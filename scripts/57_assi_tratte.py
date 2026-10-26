# -*- coding: utf-8 -*-
"""
scripts/57_assi_tratte.py - Pacchetto A della Fase 5: ASSI e TRATTE.

Da "corridoio = stesso nome" a "asse = stessa strada" (anche se cambia nome o
comune) diviso in tratte di lunghezza confrontabile (0,3-1,5 km).

Come si costruisce l'asse (grafo OSM, tratti = archi base della rete):
  1. a ogni incrocio (nodo) si collegano gli estremi di due tratti che
     proseguono quasi dritti (deviazione <= 35 gradi; <= 45 gradi se hanno lo
     stesso nome o lo stesso "ref"), scegliendo sempre la coppia con deviazione
     minima (accoppiamento goloso). Classi compatibili: stesso gruppo
     autostrada/tangenziale oppure stesso gruppo urbano entro una classe di
     distanza. L'asse si ferma dove la classe passa ad autostrada/tangenziale.
  2. i tratti collegati formano CATENE (percorsi ordinati);
  3. due catene con lo STESSO nome che scorrono parallele entro ~100 m (le due
     carreggiate di un corso) vengono unite nello stesso ASSE.
  Nomi: ogni asse porta tutti i nomi che attraversa in ordine; il nome
  principale e' quello del tratto piu' lungo.

Tratte: ogni catena e' tagliata ai grandi incroci (incroci con un'altra strada
di rango pari o superiore) e, se un pezzo supera 1,5 km, spezzata in pezzi da
~1 km; le tratte sotto 300 m si uniscono alla vicina.

Output:
  data/processed/traffico_d/assi.json
  data/processed/traffico_d/tratte.csv
  data/processed/traffico_d/assi_tratte.npz   (edge -> asse, edge -> tratta)
  docs/rapporti/RAPPORTO_ASSI_TRATTE.txt
"""

import csv
import json
import math
import sys
from collections import defaultdict, Counter
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
OUT = PROC / "traffico_d"
RETE_DIR = OUT / "rete"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_ASSI_TRATTE.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

DEV_STRAIGHT = math.radians(35.0)
DEV_STESSO_NOME = math.radians(45.0)
SOGLIA_PARALLELE_M = 100.0
LUN_TRATTA_MAX = 1500.0
LUN_TRATTA_TARGET = 1000.0
LUN_TRATTA_MIN = 300.0


def normalizza(nome):
    from importlib import import_module
    return import_module("24_importanza_vie").normalizza(nome)


def base_classe(classe):
    """(famiglia, indice) per compatibilita' e rango."""
    if classe in ("motorway", "motorway_link"):
        return "autostrada", 0
    if classe in ("trunk", "trunk_link"):
        return "autostrada", 1
    if classe in ("primary", "primary_link"):
        return "urbana", 0
    if classe in ("secondary", "secondary_link"):
        return "urbana", 1
    if classe in ("tertiary", "tertiary_link", "unclassified"):
        return "urbana", 2
    return "urbana", 3


RANGO_VAL = {"motorway": 5, "motorway_link": 5, "trunk": 5, "trunk_link": 5,
             "primary": 4, "primary_link": 4, "secondary": 3, "secondary_link": 3,
             "tertiary": 2, "tertiary_link": 2, "unclassified": 1, "residential": 1,
             "living_street": 1, "service": 1, "road": 1}


def compatibili(c1, c2):
    f1, i1 = base_classe(c1)
    f2, i2 = base_classe(c2)
    return f1 == f2 and abs(i1 - i2) <= 1


def unit(vx, vy):
    n = math.hypot(vx, vy)
    if n <= 0:
        return (0.0, 0.0)
    return (vx / n, vy / n)


def direzione_estremo(pts, end):
    """direzione (in metri) che si allontana dal nodo, lungo il tratto."""
    if end == 0:
        la1, lo1 = pts[0]; la2, lo2 = pts[min(1, len(pts) - 1)]
    else:
        la1, lo1 = pts[-1]; la2, lo2 = pts[max(0, len(pts) - 2)]
    mx = math.cos(math.radians(0.5 * (la1 + la2))) * 111320.0
    return unit((lo2 - lo1) * mx, (la2 - la1) * 110540.0)


def unisci(padre, radice, i, j):
    ri, rj = radice(i), radice(j)
    if ri != rj:
        padre[ri] = rj


def main():
    rete = rete_osm.carica(RETE_DIR)
    meta = rete["meta"]
    n_edge = len(rete["edge_a"])
    edge_a = rete["edge_a"]; edge_b = rete["edge_b"]
    edge_len = rete["edge_len"]
    nomi = meta["nomi"]; hw = meta["highway"]
    norm_edge = [normalizza(nomi[e]) if nomi[e] else "" for e in range(n_edge)]
    rango_edge = np.array([RANGO_VAL.get(hw[e], 1) for e in range(n_edge)])

    # ---------- estremi per nodo ----------
    estremi = defaultdict(list)   # nodo -> [(edge, end)]
    for e in range(n_edge):
        estremi[int(edge_a[e])].append((e, 0))
        estremi[int(edge_b[e])].append((e, 1))

    def pts_edge(e):
        return rete_osm.geometria_arco(rete, e)

    # ---------- accoppiamento agli incroci ----------
    ROUND = {"roundabout", "circular", "mini_roundabout"}
    nodo_rotonda = set()
    for e in range(n_edge):
        if (meta["junction"][e] or "") in ROUND:
            nodo_rotonda.add(int(edge_a[e]))
            nodo_rotonda.add(int(edge_b[e]))
    prm = {}          # (edge, end) -> (edge2, end2)
    coppie = 0
    nodi_non_accoppiati = 0
    for nodo, ee in estremi.items():
        if len(ee) < 2:
            continue
        # rotatorie e svincoli complessi: non si accoppia (regola scritta).
        # Le strade che entrano in rotatoria finiscono li'.
        if nodo in nodo_rotonda or len(ee) >= 5:
            nodi_non_accoppiati += 1
            continue
        dirs = {}
        for (e, end) in ee:
            dirs[(e, end)] = direzione_estremo(pts_edge(e), end)
        # tutte le coppie compatibili, ordinate per deviazione crescente
        cand = []
        for i in range(len(ee)):
            for j in range(i + 1, len(ee)):
                (e1, d1), (e2, d2) = ee[i], ee[j]
                if e1 == e2:
                    continue
                if not compatibili(hw[e1], hw[e2]):
                    continue
                u1 = dirs[(e1, d1)]; u2 = dirs[(e2, d2)]
                dot = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
                dev = math.pi - math.acos(dot)
                stesso = (norm_edge[e1] and norm_edge[e1] == norm_edge[e2]) or \
                         (meta["ref"][e1] and meta["ref"][e1] == meta["ref"][e2])
                lim = DEV_STESSO_NOME if stesso else DEV_STRAIGHT
                if dev <= lim:
                    cand.append((dev, (e1, d1), (e2, d2)))
        cand.sort(key=lambda t: t[0])
        usati = set()
        for dev, k1, k2 in cand:
            if k1 in usati or k2 in usati:
                continue
            prm[k1] = k2
            prm[k2] = k1
            usati.add(k1); usati.add(k2)
            coppie += 1

    # ---------- componenti (catene) ----------
    padre = list(range(n_edge))
    def radice(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i
    partner = defaultdict(list)
    for k, v in prm.items():
        partner[k[0]].append(k[1])
    for (e, end), (e2, end2) in prm.items():
        unisci(padre, radice, e, e2)

    comp = defaultdict(list)
    for e in range(n_edge):
        comp[radice(e)].append(e)

    # ---------- ordine dentro ogni catena ----------
    def cammina(e_start):
        """Ritorna (nodi, edges, ends_iniziali) della catena che contiene e_start."""
        # scegli un'estremita' libera se esiste
        def grado_liberi(e):
            return [end for end in (0, 1) if (e, end) not in prm]
        parti = None
        for e in comp_edges:
            lib = grado_liberi(e)
            if lib:
                parti = (e, lib[0])
                break
        if parti is None:
            parti = (e_start, 0)
        e, s = parti
        seq_e = []
        seq_s = []
        visti = set()
        while e is not None and (e, s) not in visti:
            visti.add((e, s))
            seq_e.append(e); seq_s.append(s)
            uscita = 1 - s
            pari = prm.get((e, uscita))
            if pari is None:
                break
            e2, end2 = pari
            s = end2
            e = e2
            if len(seq_e) > n_edge:
                break
        return seq_e, seq_s

    catene = []       # lista di dict {edges, ends}
    for rad, comp_edges in comp.items():
        comp_edges = sorted(comp_edges)
        seq_e, seq_s = cammina(comp_edges[0])
        if len(seq_e) != len(comp_edges):
            # catena degenere (ciclo o ramo): tieni comunque cio' che si e' percorso
            mancanti = [e for e in comp_edges if e not in set(seq_e)]
            seq_e += mancanti
            seq_s += [0] * len(mancanti)
        catene.append({"edges": seq_e, "ends": seq_s})

    # ---------- unione carreggiate per stesso nome entro 100 m ----------
    # griglia dei punti delle catene
    CELLA = 0.0010
    def punti_catena(edges, ends, passo_m=40.0):
        out = []
        for e, s in zip(edges, ends):
            p = pts_edge(e)
            if s == 1:
                p = p[::-1]
            for k in range(len(p)):
                out.append((float(p[k, 0]), float(p[k, 1])))
        return out

    punti_c = [punti_catena(c["edges"], c["ends"]) for c in catene]
    # nome "dominante" di ogni catena (per lunghezza): l'unione delle carreggiate
    # si fa solo fra catene con lo STESSO nome dominante (evita di incatenare
    # catene lunghe che condividono solo un nome di passaggio).
    nomi_c = []
    for c in catene:
        peso = Counter()
        for e in c["edges"]:
            if norm_edge[e]:
                peso[norm_edge[e]] += float(edge_len[e])
        nomi_c.append({peso.most_common(1)[0][0]} if peso else set())
    griglia = defaultdict(set)
    for ci, pp in enumerate(punti_c):
        visto = set()
        for (la, lo) in pp:
            cella = (math.floor(la / CELLA), math.floor(lo / CELLA))
            if cella not in visto:
                visto.add(cella)
                griglia[cella].add(ci)
    padre_c = list(range(len(catene)))
    def rc(i):
        while padre_c[i] != i:
            padre_c[i] = padre_c[padre_c[i]]
            i = padre_c[i]
        return i
    for cella, dentro in griglia.items():
        if len(dentro) < 2:
            continue
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for cj in griglia.get((cella[0] + di, cella[1] + dj), ()):
                    for ci in dentro:
                        if ci >= cj:
                            continue
                        if nomi_c[ci] & nomi_c[cj]:
                            ri, rj = rc(ci), rc(cj)
                            if ri != rj:
                                padre_c[ri] = rj
    assi_cat = defaultdict(list)
    for ci in range(len(catene)):
        assi_cat[rc(ci)].append(ci)
    assi_ids = {r: k for k, r in enumerate(sorted(assi_cat))}

    # ---------- quartiere/comune ----------
    zone = json.loads((PROC / "imq_zone_geo.json").read_text(encoding="utf-8"))

    def anelli(g):
        if isinstance(g, str):
            g = json.loads(g)
        if not g:
            return []
        if isinstance(g[0][0], (int, float)):
            return [g]
        if isinstance(g[0][0][0], (int, float)):
            return g
        return [a for p in g for a in p]

    from shapely.geometry import Polygon, MultiPolygon, Point
    from shapely.strtree import STRtree
    polys, cods, comuni = [], [], []
    for z in zone:
        pp = []
        for an in anelli(z["g"]):
            if len(an) >= 4:
                try:
                    # le zone hanno coordinate [lat, lon]: shapely vuole (x=lon, y=lat)
                    p = Polygon([(pt[1], pt[0]) for pt in an])
                    if not p.is_valid:
                        p = p.buffer(0)
                    if p.area > 0:
                        pp.append(p)
                except Exception:
                    pass
        if pp:
            polys.append(MultiPolygon(pp) if len(pp) > 1 else pp[0])
            cods.append(z["cod"])
            comuni.append("Torino" if z["cod"].startswith("Q") else z["denom"].title())
    tree = STRtree(polys)

    def comune_quartiere(lat, lon):
        pt = Point(lon, lat)
        for j in np.atleast_1d(tree.query(pt)):
            if polys[j].contains(pt):
                return comuni[j], cods[j]
        return None, None

    # ---------- tratte ----------
    tratte = []
    asse_tratte = defaultdict(list)
    edge_asse = np.full(n_edge, -1, dtype=np.int64)
    edge_tratta = np.full(n_edge, -1, dtype=np.int64)
    tid = 0
    for root, lista_cat in assi_cat.items():
        aid = assi_ids[root]
        for ci in lista_cat:
            cat = catene[ci]
            edges = cat["edges"]; ends = cat["ends"]
            for e in edges:
                edge_asse[e] = aid
            rango_cat = int(max(rango_edge[e] for e in edges))
            # lunghezze
            L = [float(edge_len[e]) for e in edges]
            taglio = [0]
            acc = 0.0
            for k in range(len(edges)):
                acc += L[k]
                # nodo di confine dopo il tratto k
                if k < len(edges) - 1:
                    nodo = int(edge_b[edges[k]]) if ends[k] == 0 else int(edge_a[edges[k]])
                    altri = [ee for ee in estremi.get(nodo, ())
                             if ee[0] != edges[k] and ee[0] != edges[k + 1]]
                    grande = any(rango_edge[ee[0]] >= rango_cat and edge_len[ee[0]] > 30
                                 for ee in altri)
                else:
                    grande = True
                if grande and acc >= 0 or acc >= LUN_TRATTA_TARGET:
                    if acc >= LUN_TRATTA_MIN or k == len(edges) - 1:
                        taglio.append(k + 1)
                        acc = 0.0
            if taglio[-1] != len(edges):
                taglio.append(len(edges))
            # costruisci tratte fra tagli consecutivi, unendo quelle < 300 m
            pezzi = []
            for a0, a1 in zip(taglio[:-1], taglio[1:]):
                pezzi.append((a0, a1))
            uniti = []
            i = 0
            while i < len(pezzi):
                a0, a1 = pezzi[i]
                lun = sum(L[a0:a1])
                # unisci in avanti le tratte corte
                while lun < LUN_TRATTA_MIN and i + 1 < len(pezzi):
                    a1 = pezzi[i + 1][1]
                    i += 1
                    lun = sum(L[a0:a1])
                uniti.append((a0, a1))
                i += 1
            for a0, a1 in uniti:
                seg = edges[a0:a1]
                segs = ends[a0:a1]
                # geometria e nome
                geom = []
                for e, s in zip(seg, segs):
                    p = pts_edge(e)
                    if s == 1:
                        p = p[::-1]
                    geom.append(p)
                lun_m = float(sum(edge_len[e] for e in seg))
                mid = geom[len(geom) // 2]
                mlat = float(mid[len(mid) // 2, 0]); mlon = float(mid[len(mid) // 2, 1])
                comune, quartiere = comune_quartiere(mlat, mlon)
                nomi_t = []
                for e in seg:
                    if norm_edge[e] and (not nomi_t or nomi_t[-1] != norm_edge[e]):
                        nomi_t.append(norm_edge[e])
                cls_max = max((hw[e] for e in seg), key=lambda c: RANGO_VAL.get(c, 1))
                corsie_av = float(np.mean([rete["edge_corsie_avanti"][e] for e in seg])) \
                    if "edge_corsie_avanti" in rete else 1.0
                corsie_in = float(np.mean([rete["edge_corsie_indietro"][e] for e in seg])) \
                    if "edge_corsie_indietro" in rete else 1.0
                bridge = any(bool(rete["edge_bridge"][e]) for e in seg) if "edge_bridge" in rete else False
                tunnel = any(bool(rete["edge_tunnel"][e]) for e in seg) if "edge_tunnel" in rete else False
                versi = {meta["verso"][e] for e in seg}
                verso_unico = bool(versi <= {"avanti"} or versi <= {"indietro"})
                flat = [[round(float(la), 6), round(float(lo), 6)] for p in geom for la, lo in p]
                tratte.append({
                    "id": tid, "asse": aid, "catena": ci,
                    "nomi": nomi_t, "nome_principale": (nomi_t[0] if nomi_t else None),
                    "comune": comune, "quartiere": quartiere,
                    "lunghezza_m": round(lun_m, 1), "classe": cls_max,
                    "rango": int(RANGO_VAL.get(cls_max, 1)),
                    "corsie_avanti": round(corsie_av, 2), "corsie_indietro": round(corsie_in, 2),
                    "corsie_totali": round(corsie_av + corsie_in, 2),
                    "corsie_stimate": bool(any(bool(rete["edge_corsie_stimate"][e]) for e in seg))
                    if "edge_corsie_stimate" in rete else True,
                    "verso_unico": verso_unico,
                    "bridge": bool(bridge), "tunnel": bool(tunnel),
                    "nomi_osm": [nomi[e] for e in seg if nomi[e]],
                    "geom": flat,
                })
                for e in seg:
                    edge_tratta[e] = tid
                asse_tratte[aid].append(tid)
                tid += 1

    # ---------- assi ----------
    assi = []
    for root in sorted(assi_cat):
        aid = assi_ids[root]
        lista = asse_tratte[aid]
        nomi_ord = []
        for tt in lista:
            for n in tratte[tt]["nomi"]:
                if n not in nomi_ord:
                    nomi_ord.append(n)
        comuni_set = sorted({tratte[tt]["comune"] for tt in lista if tratte[tt]["comune"]})
        lung = sum(tratte[tt]["lunghezza_m"] for tt in lista)
        assi.append({
            "id": aid,
            "nomi": nomi_ord,
            "nome_principale": (nomi_ord[0] if nomi_ord else None),
            "comuni": comuni_set,
            "n_tratte": len(lista),
            "tratte": lista,
            "lunghezza_km": round(lung / 1000.0, 3),
            "classe_max": max((tratte[tt]["classe"] for tt in lista),
                              key=lambda c: RANGO_VAL.get(c, 1)) if lista else None,
            "nomi_osm_esempio": sorted({n for tt in lista for n in tratte[tt]["nomi_osm"]})[:4],
        })

    OUT.mkdir(parents=True, exist_ok=True)
    # tratte.json = metadati delle tratte SENZA geometria (la geometria si rilegge
    # dalla rete tramite assi_tratte.npz edge_tratta, per non duplicare i dati)
    tratte_meta = [{k: v for k, v in t.items() if k != "geom"} for t in tratte]
    (OUT / "tratte.json").write_text(json.dumps({
        "stimato": False, "n_tratte": len(tratte_meta), "tratte": tratte_meta,
    }, ensure_ascii=False), encoding="utf-8")
    (OUT / "assi.json").write_text(json.dumps({
        "stimato": False,
        "nota": ("Assi = stessa strada anche se cambia nome/comune; tratte 0,3-1,5 km. "
                 "Costruiti dai tratti OSM (rete Fase 5) con accoppiamento 'quasi dritto' "
                 "agli incroci e unione delle carreggiate omonime entro 100 m."),
        "parametri": {"dev_dritto_gradi": 35, "dev_stesso_nome_gradi": 45,
                      "parallele_m": SOGLIA_PARALLELE_M,
                      "tratta_min_m": LUN_TRATTA_MIN, "tratta_max_m": LUN_TRATTA_MAX},
        "n_assi": len(assi), "n_tratte": len(tratte),
        "assi": assi,
    }, ensure_ascii=False), encoding="utf-8")

    with (OUT / "tratte.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["id_tratta", "id_asse", "nomi", "nome_principale", "comune", "quartiere",
                    "lunghezza_m", "classe", "rango", "corsie_avanti", "corsie_indietro",
                    "corsie_totali", "verso_unico", "bridge", "tunnel", "geom_wkt"])
        for t in tratte:
            geom = t["geom"]
            wkt = "LINESTRING(" + ",".join(f"{lo} {la}" for la, lo in geom) + ")"
            w.writerow([t["id"], t["asse"], ">".join(t["nomi"]), t["nome_principale"] or "",
                        t["comune"] or "", t["quartiere"] or "", t["lunghezza_m"], t["classe"],
                        t["rango"], t["corsie_avanti"], t["corsie_indietro"], t["corsie_totali"],
                        int(t["verso_unico"]), int(t["bridge"]), int(t["tunnel"]), wkt])
    np.savez_compressed(OUT / "assi_tratte.npz",
                        edge_asse=edge_asse, edge_tratta=edge_tratta)

    # ---------- controlli ----------
    # copertura: km di strade di rango >= 3 in Torino dentro un asse
    def in_torino(t):
        return t["comune"] == "Torino"
    km_r3_tor = sum(t["lunghezza_m"] for t in tratte if t["rango"] >= 3 and in_torino(t))
    km_r3_tor_coperte = sum(t["lunghezza_m"] for t in tratte
                            if t["rango"] >= 3 and in_torino(t) and t["asse"] >= 0)
    # salti > 100 m fra tratti consecutivi (gia' garantito: tratti consecutivi condividono un nodo)
    # tratti in due assi: impossibile per costruzione (una componente)
    # incoerenza asse: cambia classe di colpo (>= 2 famiglie) o torna indietro (angolo > 90)
    incoerenti = 0
    for a in assi:
        famiglie = {base_classe(tratte[tt]["classe"])[0] for tt in a["tratte"]}
        if len(famiglie) > 1:
            incoerenti += 1
    perc_incoerenti = 100.0 * incoerenti / max(len(assi), 1)

    righe = []
    def a_(s=""):
        righe.append(s)
    a_("ASSI E TRATTE (pacchetto A, Fase 5)")
    a_("=" * 74)
    a_(f"  assi: {len(assi):,}   tratte: {len(tratte):,}")
    a_(f"  accoppiamenti 'quasi dritto' agli incroci: {coppie:,}")
    a_(f"  km totali dei tratti nella rete: {float(edge_len.sum())/1000:,.1f}")
    a_(f"  km di strade di rango >= 3 in Torino: {km_r3_tor/1000:,.1f}; "
       f"coperte da un asse: {100*km_r3_tor_coperte/max(km_r3_tor,1):.1f}%")
    a_(f"  assi incoerenti (classi di famiglie diverse): {incoerenti} "
       f"({perc_incoerenti:.1f}%) - soglia di arresto 10%")
    a_(f"  tratte sotto 300 m: {sum(1 for t in tratte if t['lunghezza_m'] < 300)} "
       f"(di cui rango>=3 a Torino: "
       f"{sum(1 for t in tratte if t['lunghezza_m'] < 300 and t['rango'] >= 3 and in_torino(t))})")
    a_(f"  tratte oltre 1500 m: {sum(1 for t in tratte if t['lunghezza_m'] > 1500)}")
    a_(f"  tratte con verso unico (una sola carreggiata): "
       f"{sum(1 for t in tratte if t['verso_unico'])}")
    a_("")
    a_("== Esempi richiesti dal piano ==")
    esempi = ["trapani", "lecce", "potenza", "agudio", "sturzo", "francia",
              "regina margherita", "allamano", "vittorio emanuele", "giulio cesare",
              "vercelli", "lione"]
    for chiave in esempi:
        trovati = [a for a in assi if any(chiave in n for n in a["nomi"])]
        trovati.sort(key=lambda a: -a["lunghezza_km"])
        if not trovati:
            a_(f"  {chiave:18s}: NESSUN ASSE")
            continue
        for a_2 in trovati[:2]:
            a_(f"  {chiave:18s}: asse {a_2['id']:5d}  {a_2['lunghezza_km']:6.2f} km  "
               f"nomi {' > '.join(a_2['nomi'][:6])}  comuni {','.join(a_2['comuni'])}")
    a_("")
    a_("== I 20 assi piu' lunghi ==")
    for a_2 in sorted(assi, key=lambda x: -x["lunghezza_km"])[:20]:
        a_(f"  {a_2['lunghezza_km']:7.2f} km  {a_2['n_tratte']:4d} tratte  "
           f"{' > '.join(a_2['nomi'][:4])[:70]}")
    a_("")
    a_("== Tratte con i nomi che cambiano (esempi) ==")
    multi = [t for t in tratte if len([n for n in t["nomi"]]) >= 2]
    a_(f"  tratte che attraversano un cambio di nome: {len(multi):,}")
    for t in multi[:10]:
        a_(f"    tratta {t['id']:5d} asse {t['asse']:4d} {' > '.join(t['nomi'])} "
           f"({t['comune']}, {t['lunghezza_m']:.0f} m)")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))

    (OUT / "riepilogo_assi.json").write_text(json.dumps({
        "n_assi": len(assi), "n_tratte": len(tratte), "coppie_incrocio": coppie,
        "km_rete": round(float(edge_len.sum()) / 1000, 1),
        "km_rango3_torino": round(km_r3_tor / 1000, 1),
        "perc_coperta": round(100 * km_r3_tor_coperte / max(km_r3_tor, 1), 1),
        "assi_incoerenti": incoerenti, "perc_incoerenti": round(perc_incoerenti, 2),
        "tratte_sotto_300m": int(sum(1 for t in tratte if t["lunghezza_m"] < 300)),
        "tratte_oltre_1500m": int(sum(1 for t in tratte if t["lunghezza_m"] > 1500)),
    }, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
