# -*- coding: utf-8 -*-
"""
scripts/41_zone_punti.py - Pacchetto C del piano Fase 3.

Trasforma le 212 zone IMQ in PUNTI pesati sulla rete stradale:
 - le zone con popolazione censita dentro il taglio OSM (quartieri di Torino e
   comuni della cintura) sono rappresentate da piu' punti, scelti a caso con
   probabilita' proporzionale alla popolazione delle sezioni di censimento
   (campionamento PPS senza ripetizione), agganciati al nodo stradale piu'
   vicino;
 - le zone il cui centroide cade fuori dal taglio OSM entrano/escono dall'area
   attraverso una PORTA (il punto in cui una strada di rango >= secondary e'
   tagliata dal bordo del ritaglio). La porta si sceglie con l'azimut dalla
   zona verso Torino e il rango della strada (preferenza alle autostrade per
   le distanze lunghe).

V0 (variante di base): i punti rappresentano la POPOLAZIONE, e valgono sia per
l'origine sia per la destinazione dei viaggi. La raffinatezza "attrattori per
le destinazioni non domestiche" e' la variante V3.

Output:
  data/processed/traffico_c/punti.json    (zona -> punti: lat, lon, nodo, peso, tipo)
  data/processed/traffico_c/porte.json    (elenco delle porte)
  docs/rapporti/RAPPORTO_TRAFFICO_C_PUNTI.txt
"""

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rete_osm  # noqa: E402


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
PROC = RADICE / "data" / "processed"
OUT_DIR = PROC / "traffico_c"
RETE_DIR = OUT_DIR / "rete"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_TRAFFICO_C_PUNTI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

# riquadro del taglio OSM (script 17)
LON_MIN, LAT_MIN, LON_MAX, LAT_MAX = 7.45, 44.90, 7.93, 45.24
CENTRO = (45.0703, 7.6869)   # piazza Castello

RANGO = {"motorway": 5, "motorway_link": 5, "trunk": 5, "trunk_link": 5,
         "primary": 4, "primary_link": 4, "secondary": 3, "secondary_link": 3}
ALTO_RANGO = set(RANGO)

K_PUNTI = {"quartiere": 20, "cintura": 8, "altro": 5}
SEED = 20261017


def anelli_di(g):
    if isinstance(g, str):
        g = json.loads(g)
    if not g:
        return []
    if isinstance(g[0][0], (int, float)):
        return [g]
    if isinstance(g[0][0][0], (int, float)):
        return g
    return [a for p in g for a in p]


def centroide(anelli):
    pts = [p for a in anelli for p in a]
    las = [p[0] for p in pts]
    los = [p[1] for p in pts]
    return (min(las) + max(las)) / 2, (min(los) + max(los)) / 2


def azimut(lat1, lon1, lat2, lon2):
    """Angolo (gradi) dal punto 1 verso il punto 2, 0 = nord."""
    dlon = math.radians(lon2 - lon1)
    la1, la2 = math.radians(lat1), math.radians(lat2)
    y = math.sin(dlon) * math.cos(la2)
    x = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def diff_ang(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def main():
    rete = rete_osm.carica(RETE_DIR)
    xy = rete["nodi_xy"]
    meta = rete["meta"]
    N = len(xy)

    # --- gradi dei nodi e porte -------------------------------------------------
    edge_a = rete["edge_a"]
    edge_b = rete["edge_b"]
    grado = np.zeros(N, dtype=np.int32)
    for i in range(len(edge_a)):
        grado[edge_a[i]] += 1
        grado[edge_b[i]] += 1

    # nodi "utili": hanno almeno un arco entrante e uno uscente. Le estremita'
    # troncate di un'autostrada sono nodi di grado 1: se sono "di uscita" non
    # hanno archi uscenti e un viaggio che parte da li' non potrebbe muoversi.
    archi = rete["archi"]
    archi_int = archi[:, :2].astype(np.int64)
    entrata = np.zeros(N, dtype=np.int64)
    uscita = np.zeros(N, dtype=np.int64)
    np.add.at(uscita, archi_int[:, 0], 1)
    np.add.at(entrata, archi_int[:, 1], 1)
    utili = (entrata > 0) & (uscita > 0)
    # tengo solo i nodi della componente FORTEMENTE connessa piu' grande (il
    # "nocciolo" della rete, 97-98% dei nodi): da un nodo fuori dal nocciolo si
    # puo' non riuscire a raggiungere il resto della citta' (es. fondo di una
    # strada a senso unico, estremita' troncata di un'autostrada).
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    G = sp.csr_matrix((np.ones(len(archi)), (archi_int[:, 0], archi_int[:, 1])), shape=(N, N))
    _n, lab = connected_components(G, directed=True, connection="strong")
    grande = int(np.argmax(np.bincount(lab)))
    utili = utili & (lab == grande)
    indici_utili = np.nonzero(utili)[0]
    xy_utili = xy[utili]
    print(f"nodi utili (nocciolo della rete, componenti forti): {int(utili.sum()):,} su {N:,}")

    # --- porte = tratti che ATTRAVERSANO il bordo del taglio OSM ---------------
    # Una porta e' un tratto con un estremo dentro il riquadro e l'altro fuori:
    # e' il punto in cui una strada esterna entra nell'area studiata. Il "nodo
    # di ingresso" e' l'estremo interno (da li' si entra in rete).
    RANGO_ALL = dict(RANGO)
    for k, v in {"tertiary": 2, "tertiary_link": 2, "unclassified": 1,
                 "residential": 1, "service": 1, "road": 1, "living_street": 1}.items():
        RANGO_ALL.setdefault(k, v)

    def dentro(la, lo):
        return LON_MIN <= lo <= LON_MAX and LAT_MIN <= la <= LAT_MAX

    porte = {}
    n_crossing = 0
    for e in range(len(edge_a)):
        hw = meta["highway"][e]
        if hw not in RANGO_ALL:
            continue
        na, nb = int(edge_a[e]), int(edge_b[e])
        la, lo = xy[na]
        lb, lob = xy[nb]
        dentro_a, dentro_b = dentro(la, lo), dentro(lb, lob)
        if dentro_a == dentro_b:
            continue
        n_crossing += 1
        nid_in = na if dentro_a else nb
        if not utili[nid_in]:
            continue
        r = RANGO_ALL[hw]
        if nid_in not in porte or r > porte[nid_in]["rango"]:
            porte[nid_in] = {"nodo": nid_in, "lat": round(float(xy[nid_in, 0]), 6),
                             "lon": round(float(xy[nid_in, 1]), 6), "rango": r,
                             "highway": hw, "nome": meta["nomi"][e]}

    # Le autostrade hanno tratti lunghi fra due svincoli: capita che il tratto
    # che attraversa il bordo abbia TUTTI E DUE gli estremi fuori dal riquadro.
    # In quel caso si aggiungono le estremita' troncate di grado 1 (come
    # all'inizio), prendendo come ingresso il nodo utile piu' vicino.
    for e in range(len(edge_a)):
        hw = meta["highway"][e]
        if hw not in ALTO_RANGO:
            continue
        for nid in (int(edge_a[e]), int(edge_b[e])):
            if grado[nid] != 1 or utili[nid]:
                continue
            la, lo = float(xy[nid, 0]), float(xy[nid, 1])
            if dentro(la, lo):
                continue
            j = int(np.argmin((xy_utili[:, 0] - la) ** 2 + (xy_utili[:, 1] - lo) ** 2))
            nid_in = int(indici_utili[j])
            r = RANGO_ALL[hw]
            if nid_in not in porte or r > porte[nid_in]["rango"]:
                porte[nid_in] = {"nodo": nid_in, "lat": round(float(xy[nid_in, 0]), 6),
                                 "lon": round(float(xy[nid_in, 1]), 6), "rango": r,
                                 "highway": hw, "nome": meta["nomi"][e]}

    # --- tempo di percorrenza da ogni porta verso Torino (per scegliere la porta) ---
    centro_node = int(indici_utili[int(np.argmin(
        (xy_utili[:, 0] - CENTRO[0]) ** 2 + (xy_utili[:, 1] - CENTRO[1]) ** 2))])
    M = sp.csr_matrix((archi[:, 2].astype(float), (archi_int[:, 0], archi_int[:, 1])), shape=(N, N))
    from scipy.sparse.csgraph import dijkstra as _dij
    nodi_porta = sorted(porte)
    dist_pc = _dij(M, indices=nodi_porta, return_predecessors=False)
    for k, nid in enumerate(nodi_porta):
        t = float(dist_pc[k, centro_node])
        porte[nid]["nodo_utile"] = nid
        porte[nid]["tempo_a_centro_min"] = None if not np.isfinite(t) else round(t / 60, 1)
    zone_geo = json.loads((PROC / "imq_zone_geo.json").read_text(encoding="utf-8"))
    zone_istat = json.loads((PROC / "imq_zone.json").read_text(encoding="utf-8"))
    sezioni = json.loads((PROC / "sezioni_torino.json").read_text(encoding="utf-8"))

    # comune -> zone (dall'elenco istat)
    comune_zone = defaultdict(list)
    for z in zone_istat:
        for ist in z.get("istat") or []:
            comune_zone[int(ist)].append(z["cod"])

    # quartieri di Torino: associazione sezione -> quartiere con shapely
    quartieri = {}
    for zg in zone_geo:
        if zg["cod"].startswith("Q"):
            quartieri[zg["cod"]] = anelli_di(zg["g"])
    try:
        from shapely.geometry import Polygon, MultiPolygon, Point
        from shapely.strtree import STRtree
        poligoni = []
        chiavi = []
        for cod, anelli in quartieri.items():
            polys = []
            for an in anelli:
                if len(an) >= 4:
                    p = Polygon(an)
                    if not p.is_valid:
                        p = p.buffer(0)
                    if p.area > 0:
                        polys.append(p)
            if polys:
                poligoni.append(MultiPolygon(polys) if len(polys) > 1 else polys[0])
                chiavi.append(cod)
        albero = STRtree(poligoni)
        ha_shapely = True
    except Exception as err:
        print("ATTENZIONE: shapely non disponibile, quartieri non assegnati:", err)
        ha_shapely = False

    sez_per_zona = defaultdict(list)
    non_assegnate = 0
    for s in sezioni:
        pop = float(s.get("p") or 0)
        if pop <= 0 or not s.get("g"):
            continue
        comune = int(s["c"])
        an = s["g"]
        pts = an[0]
        la = sum(p[0] for p in pts) / len(pts)
        lo = sum(p[1] for p in pts) / len(pts)
        if comune == 1272 and ha_shapely:
            # i poligoni sono costruiti in coordinate (lat, lon): uso Point(la, lo)
            pt = Point(la, lo)
            cod = None
            for j in np.atleast_1d(albero.query(pt)):
                if poligoni[j].contains(pt):
                    cod = chiavi[j]
                    break
            if cod is None:
                non_assegnate += 1
                continue
        else:
            zs = comune_zone.get(comune)
            if not zs or len(zs) != 1:
                non_assegnate += 1
                continue
            cod = zs[0]
        sez_per_zona[cod].append((la, lo, pop))

    # --- punti per zona ---------------------------------------------------------
    rng = np.random.default_rng(SEED)
    punti = {}
    tipo_zona = {}
    conteggi = defaultdict(int)
    nodi_usati = set()
    zone_senza_punti = []
    for zg in zone_geo:
        cod = zg["cod"]
        anelli = anelli_di(zg["g"])
        clat, clon = centroide(anelli) if anelli else CENTRO
        dentro = (LON_MIN <= clon <= LON_MAX and LAT_MIN <= clat <= LAT_MAX)
        sez = sez_per_zona.get(cod, [])
        if cod.startswith("Q"):
            k, tipo = K_PUNTI["quartiere"], "quartiere"
        elif sez:
            k, tipo = (K_PUNTI["cintura"] if dentro else K_PUNTI["altro"]), "con_sezioni"
        else:
            k, tipo = 0, "porta"

        elenco = []
        if sez and k > 0:
            pesi = np.array([p[2] for p in sez], dtype=float)
            pesi /= pesi.sum()
            n = min(k, len(sez))
            scelti = rng.choice(len(sez), size=n, replace=False, p=pesi)
            for i in scelti:
                la, lo, pop = sez[i]
                elenco.append({"lat": round(la, 6), "lon": round(lo, 6)})
            tipo_zona[cod] = tipo
        else:
            # porta: la piu' coerente con la direzione della zona rispetto a Torino
            az = azimut(*CENTRO, clat, clon)
            cand = []
            # a distanze grandi si entra da strade di rango alto, non da una
            # strada di campagna: il rango minimo sale con la distanza della zona
            for p in porte.values():
                if diff_ang(az, azimut(*CENTRO, p["lat"], p["lon"])) > 40:
                    continue
                dist = rete_osm.haversine_m(clat, clon, p["lat"], p["lon"])
                km_d = dist / 1000.0
                min_r = 4 if km_d > 60 else (3 if km_d > 30 else (2 if km_d > 12 else 1))
                if p["rango"] < min_r:
                    continue
                vel = {5: 100.0, 4: 60.0, 3: 45.0, 2: 40.0, 1: 35.0}[p["rango"]]
                t_zona = dist / (vel / 3.6)
                t_centro = (p.get("tempo_a_centro_min") or 999) * 60
                cand.append((t_zona + t_centro, dist, p))
            if not cand:
                # nessuna porta nella direzione della zona: allargo il cono
                for p in porte.values():
                    dist = rete_osm.haversine_m(clat, clon, p["lat"], p["lon"])
                    cand.append((dist, dist, p))
            cand.sort(key=lambda t: t[0])
            if cand:
                # fino a 3 porte (le migliori entro 1,35 volte il costo minimo),
                # con peso inversamente proporzionale al costo: una zona esterna
                # grande entra da piu' strade, non da una sola. I viaggi INTERNI
                # a una zona esterna restano fuori rete (li scarta il pacchetto D).
                presi = [cand[0]]
                for t in cand[1:3]:
                    if t[0] <= 1.35 * cand[0][0]:
                        presi.append(t)
                for t in presi:
                    elenco.append({"lat": t[2]["lat"], "lon": t[2]["lon"],
                                   "porta": t[2]["nodo"], "peso_rel": 1.0})
            tipo_zona[cod] = "porta"

        # aggancio al nodo stradale piu' vicino
        out = []
        n_nodi_zona = set()
        for el in elenco:
            la, lo = el["lat"], el["lon"]
            d2 = (xy_utili[:, 0] - la) ** 2 + (xy_utili[:, 1] - lo) ** 2
            nid = int(indici_utili[int(np.argmin(d2))])
            d = float(rete_osm.haversine_m(la, lo, *xy[nid]))
            out.append({"lat": round(float(xy[nid, 0]), 6), "lon": round(float(xy[nid, 1]), 6),
                        "nodo": nid, "dist_nodo_m": round(d, 1),
                        "tipo": "porta" if "porta" in el else "sezione",
                        "_peso_rel": el.get("peso_rel", 1.0)})
            n_nodi_zona.add(nid)
            nodi_usati.add(nid)
        if not out:
            zone_senza_punti.append(cod)
        tot_rel = sum(o["_peso_rel"] for o in out) or 1.0
        for o in out:
            o["peso"] = round(o.pop("_peso_rel") / tot_rel, 8)
        punti[cod] = out
        conteggi[tipo_zona.get(cod, tipo)] += 1

    # --- scrittura --------------------------------------------------------------
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "punti.json").write_text(json.dumps({
        "stimato": True,
        "nota": ("Punti pesati per zona, V0 = popolazione (sezioni di censimento). "
                 "Zone fuori dal taglio OSM: ingresso da una porta."),
        "seed": SEED, "k_punti": K_PUNTI,
        "zone": punti,
    }, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "porte.json").write_text(json.dumps({
        "stimato": False,
        "nota": "Nodi di bordo del taglio OSM su strade di rango >= secondary (degrado 1).",
        "porte": sorted(porte.values(), key=lambda p: p["nodo"]),
    }, ensure_ascii=False), encoding="utf-8")

    # --- rapporto ---------------------------------------------------------------
    righe = []
    a = righe.append
    a("RAPPORTO PUNTI E PORTE (pacchetto C, metodo C)")
    a("=" * 70)
    a(f"  zone totali: {len(zone_geo)}")
    a(f"  punti di origine/destinazione: {sum(len(v) for v in punti.values()):,}")
    a(f"  nodi stradali distinti usati dai punti: {len(nodi_usati):,} su {N:,}")
    a(f"  porte trovate sul bordo del taglio: {len(porte):,}")
    a(f"  sezioni di censimento assegnate a una zona: {sum(len(v) for v in sez_per_zona.values()):,} "
      f"(non assegnate: {non_assegnate:,})")
    a("")
    a("  zone per tipo: " + ", ".join(f"{k}={v}" for k, v in sorted(conteggi.items())))
    a(f"  zone senza alcun punto: {len(zone_senza_punti)} {zone_senza_punti}")
    senza2 = [c for c, v in punti.items() if len({p['nodo'] for p in v}) < 2 and len(v) > 1]
    a(f"  zone con punti tutti sullo stesso nodo stradale: {len(senza2)} {senza2[:10]}")
    a("")
    a("  distribuzione dei punti per numero di punti-zona:")
    for k in sorted({len(v) for v in punti.values()}):
        a(f"    {k} punti: {sum(1 for v in punti.values() if len(v) == k)} zone")
    a("")
    a("  porte per rango: " + ", ".join(
        f"rango{r}={sum(1 for p in porte.values() if p['rango']==r)}" for r in (5, 4, 3, 2, 1)))
    a("")
    a("  esempi di punti (prime zone):")
    for cod in list(punti)[:5]:
        a(f"    {cod}: " + ", ".join(f"nodo {p['nodo']} ({p['dist_nodo_m']}m){'(porta)' if p['tipo']=='porta' else ''}"
                                     for p in punti[cod][:8]))
    a("")
    a(f"Output: {OUT_DIR/'punti.json'}")
    a(f"Output: {OUT_DIR/'porte.json'}")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
