# -*- coding: utf-8 -*-
"""
scripts/rete_osm.py - rete stradale percorribile in auto ricavata dal taglio OSM
(data/otp/rete/torino_cintura.osm.pbf), per il metodo C del Risultato 8.

Perche' un grafo nostro e non r5py: il metodo C deve far passare ~milioni di
viaggi su TUTTA la rete e sommare i passaggi su ogni tratto. r5py serve a
calcolare percorsi puntuali (o matrici di tempi), non a fare un'assegnazione
di flusso su centinaia di origini: 500+ punti di partenza x 500+ di arrivo
sono centinaia di migliaia di percorsi da ricostruire, impraticabile.
Con un grafo in memoria + scipy.sparse.csgraph.dijkstra si calcola l'albero
dei cammini minimi una volta per ogni NODO di origine e i flussi si sommano
sull'albero con una somma di sottoalbero (vedi scripts/42_instradamento.py).

Cosa costruisce:
  - nodi = soli nodi "di giunzione" (fine di una strada o punto in comune fra
    due strade) piu' le estremita' di ogni way;
  - archi = tratti di way fra due nodi di giunzione, con lunghezza, tempo di
    percorrenza (da maxspeed OSM o da velocita' tipica per classe) e geometria
    completa (per abbinare i tratti ai corridoi e ai sensori);
  - ogni tratto e' un arco non orientato ("arco base") con 1 o 2 archi orientati
    (verso unico o doppio senso).

Non modifica nessun file del progetto se non quelli indicati in SALVA().
"""

import json
import math
import re
import time
from collections import Counter
from pathlib import Path

import numpy as np

# --- classi di strada percorribili in auto e velocita' tipica (km/h) -------------
VELOCITA_DEFAULT = {
    "motorway": 120.0, "motorway_link": 60.0,
    "trunk": 100.0, "trunk_link": 60.0,
    "primary": 70.0, "primary_link": 50.0,
    "secondary": 60.0, "secondary_link": 40.0,
    "tertiary": 50.0, "tertiary_link": 35.0,
    "unclassified": 40.0, "residential": 30.0, "living_street": 15.0,
    "service": 20.0, "road": 30.0,
}
DRIVABILI = set(VELOCITA_DEFAULT)
# classi in cui, se manca il tag oneway, si assume senso unico (autostrade)
SENSO_UNICO_DEFAULT = {"motorway", "motorway_link", "trunk", "trunk_link"}

# --- Pacchetto B (Fase 5): corsie e capacita' ------------------------------------
# ordine di rango delle classi (per "classi adiacenti" negli assi e nelle tratte)
RANGO_CLASSE = {
    "motorway": 8, "motorway_link": 7,
    "trunk": 6, "trunk_link": 5,
    "primary": 4, "primary_link": 3,
    "secondary": 2, "secondary_link": 1,
    "tertiary": 1, "tertiary_link": 1,
    "unclassified": 0, "residential": 0, "living_street": 0,
    "service": 0, "road": 0,
}
# famiglie: autostrada/tangenziale e' una classe a parte, l'asse si ferma li'
FAMIGLIA = {}
for _c in VELOCITA_DEFAULT:
    FAMIGLIA[_c] = "autostrada" if _c.startswith(("motorway", "trunk")) else "urbana"

# corsie per verso quando il tag "lanes" manca (valori standard DICHIARATI)
CORSIE_DEFAULT_VERSO = {
    "motorway": 2, "motorway_link": 1, "trunk": 2, "trunk_link": 1,
    "primary": 1, "primary_link": 1, "secondary": 1, "secondary_link": 1,
    "tertiary": 1, "tertiary_link": 1, "unclassified": 1, "residential": 1,
    "living_street": 1, "service": 1, "road": 1,
}

# capacita' veicoli/ora PER CORSIA (valori standard, fonte: Highway Capacity Manual,
# capacita' pratica urbana con incroci semaforizzati; arrotondati e dichiarati)
CAPACITA_CORSIA = {
    "motorway": 1800, "motorway_link": 1200, "trunk": 1400, "trunk_link": 1000,
    "primary": 1000, "primary_link": 800, "secondary": 800, "secondary_link": 700,
    "tertiary": 700, "tertiary_link": 600, "unclassified": 600, "residential": 500,
    "living_street": 300, "service": 300, "road": 500,
}

R_TERRA = 6371000.0


def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R_TERRA * math.asin(math.sqrt(a))


def parse_maxspeed(valore, default):
    """'50' -> 50; '30 mph' -> 48,3; 'IT:urban' -> default; 'walk' -> 7."""
    if valore is None:
        return default
    s = str(valore).strip().lower()
    if not s:
        return default
    if s in ("walk", "walking"):
        return 7.0
    if s in ("none", "signals", "variable"):
        return default
    m = re.search(r"\d+(?:[.,]\d+)?", s)
    if not m:
        return default
    v = float(m.group().replace(",", "."))
    if "mph" in s:
        v *= 1.60934
    if v <= 0:
        return default
    return v


def _oneway(tags, highway):
    """Ritorna 'avanti', 'indietro' o 'doppio' (verso lungo l'ordine dei nodi del way)."""
    v = (tags.get("oneway") or "").strip().lower()
    if v in ("yes", "true", "1"):
        return "avanti"
    if v in ("-1", "reverse"):
        return "indietro"
    if v in ("no", "false", "0"):
        return "doppio"
    if (tags.get("junction") or "").strip().lower() in ("roundabout", "circular"):
        return "avanti"
    if highway in SENSO_UNICO_DEFAULT:
        return "avanti"
    return "doppio"


def _intero(valore):
    if valore is None:
        return None
    m = re.search(r"\d+", str(valore))
    return int(m.group()) if m else None


def corsie_per_verso(tags, highway, verso):
    """Ritorna (corsie_avanti, corsie_indietro, stimate).

    Regole (dichiarate nel pacchetto B):
      - lanes:forward / lanes:backward hanno la precedenza;
      - altrimenti, se la strada e' a senso unico, "lanes" e' il numero di corsie
        di quell'unico verso;
      - altrimenti (doppio senso) "lanes" e' il totale: meta' per verso (arrotondata);
      - se manca tutto, valore standard per classe e per verso (CORSIE_DEFAULT_VERSO);
      - "stimate" = True se NON c'era un tag lanes/lanes:* esplicito.
    """
    def default():
        return CORSIE_DEFAULT_VERSO.get(highway, 1)

    lf = _intero(tags.get("lanes:forward"))
    lb = _intero(tags.get("lanes:backward"))
    lt = _intero(tags.get("lanes"))
    if lf is not None or lb is not None:
        fa = lf if lf is not None else 0
        ba = lb if lb is not None else 0
        stimate = False
    elif verso in ("avanti", "indietro"):
        fa = ba = 0
        if lt is not None:
            if verso == "avanti":
                fa = lt
            else:
                ba = lt
            stimate = False
        else:
            if verso == "avanti":
                fa = default()
            else:
                ba = default()
            stimate = True
    else:  # doppio senso
        if lt is not None:
            fa = (lt + 1) // 2
            ba = lt // 2
            stimate = False
        else:
            fa = ba = default()
            stimate = True
    # mai zero corsie per un verso percorribile
    if verso in ("avanti", "doppio") and fa < 1:
        fa = 1
    if verso in ("indietro", "doppio") and ba < 1:
        ba = 1
    if verso == "avanti":
        ba = 0
    if verso == "indietro":
        fa = 0
    return fa, ba, stimate


def capacita_tratto(highway, corsie_verso):
    """Capacita' veicoli/ora di un tratto in UN verso (corsie x capacita' per corsia)."""
    return float(corsie_verso) * float(CAPACITA_CORSIA.get(highway, 500))


def _accessibile(tags):
    for k in ("access", "motor_vehicle", "motorcar", "vehicle"):
        v = (tags.get(k) or "").strip().lower()
        if v in ("no", "private"):
            return False
    if (tags.get("highway") or "") in ("construction", "proposed", "abandoned"):
        return False
    return True


# --- costruzione -----------------------------------------------------------------

def costruisci(pbf, log=print, prova_bbox=None):
    """Legge il PBF e ritorna (nodi, archi_base, archi_orientati) come liste di dict.

    prova_bbox: (lat_min, lon_min, lat_max, lon_max) per limitare a un riquadro
    (solo per la prova rapida: taglia i way, non e' il giro vero).
    """
    import osmium

    t0 = time.time()
    modi = []          # un record per way percorribile
    conta_nodo = Counter()

    class Lettore(osmium.SimpleHandler):
        def way(self, w):
            hw = w.tags.get("highway")
            if hw not in DRIVABILI or not _accessibile(w.tags):
                return
            try:
                refs = [n.ref for n in w.nodes]
                pts = [(n.location.lat, n.location.lon) for n in w.nodes]
            except Exception:
                return
            if len(refs) < 2:
                return
            if prova_bbox:
                la0, lo0, la1, lo1 = prova_bbox
                if not any(la0 <= la <= la1 and lo0 <= lo <= lo1 for la, lo in pts):
                    return
            conta_nodo.update(refs)
            modi.append({
                "refs": refs, "pts": pts, "highway": hw,
                "nome": (w.tags.get("name") or "").strip() or None,
                "ref": (w.tags.get("ref") or "").strip() or None,
                "maxspeed": w.tags.get("maxspeed"),
                "verso": _oneway(w.tags, hw),
                "tags": {k: w.tags.get(k) for k in (
                    "lanes", "lanes:forward", "lanes:backward", "oneway", "maxspeed",
                    "width", "cycleway", "cycleway:left", "cycleway:right", "busway",
                    "bus", "bridge", "tunnel", "junction", "access", "motor_vehicle")},
            })

    log(f"  lettura OSM ({Path(pbf).name}) ...")
    Lettore().apply_file(str(pbf), locations=True)
    log(f"  way percorribili: {len(modi):,}")

    # nodi di giunzione: usati da piu' di un way oppure estremi di un way
    giunzione = {n for n, c in conta_nodo.items() if c >= 2}
    for m in modi:
        giunzione.add(m["refs"][0])
        giunzione.add(m["refs"][-1])

    # id nodo -> indice compatto
    id_nodo = {}
    nodi = []

    def indice(nid, lat, lon):
        i = id_nodo.get(nid)
        if i is None:
            i = len(nodi)
            id_nodo[nid] = i
            nodi.append((lat, lon))
        return i

    archi_base = []   # {a,b,pts,len_m,t_s,highway,nome,ref,verso,ind_a,ind_b}
    for m in modi:
        refs, pts, hw = m["refs"], m["pts"], m["highway"]
        vel_default = VELOCITA_DEFAULT.get(hw, 30.0)
        vel = parse_maxspeed(m["maxspeed"], vel_default)
        vel_ms = max(vel, 5.0) / 3.6
        inizio = 0
        for i in range(1, len(refs)):
            if refs[i] not in giunzione and i != len(refs) - 1:
                continue
            if i == inizio:
                continue
            seg_pts = pts[inizio:i + 1]
            seg_refs = refs[inizio:i + 1]
            if len(seg_pts) >= 2:
                lung = 0.0
                for k in range(len(seg_pts) - 1):
                    lung += haversine_m(*seg_pts[k], *seg_pts[k + 1])
                if lung > 0.1:
                    fa, ba, stimate = corsie_per_verso(m["tags"], hw, m["verso"])
                    archi_base.append({
                        "a": indice(seg_refs[0], *seg_pts[0]),
                        "b": indice(seg_refs[-1], *seg_pts[-1]),
                        "pts": seg_pts,
                        "len_m": lung,
                        "t_s": lung / vel_ms,
                        "highway": hw,
                        "nome": m["nome"],
                        "ref": m["ref"],
                        "verso": m["verso"],
                        "vel_kmh": vel,
                        "corsie_avanti": fa,
                        "corsie_indietro": ba,
                        "corsie_stimate": stimate,
                        "bridge": bool((m["tags"].get("bridge") or "").lower() in ("yes", "viaduct", "boardwalk", "1")),
                        "tunnel": bool((m["tags"].get("tunnel") or "").lower() in ("yes", "building_passage", "1")),
                        "junction": (m["tags"].get("junction") or "").strip().lower() or None,
                        "maxspeed_raw": m["tags"].get("maxspeed"),
                        "width_raw": m["tags"].get("width"),
                    })
            inizio = i

    log(f"  nodi di giunzione: {len(nodi):,}   tratti (archi base): {len(archi_base):,}   "
        f"({time.time()-t0:.1f} s)")

    # archi orientati (per il routing e per sommare i flussi nei due versi)
    archi = []   # (src, dst, peso_s, indice_arco_base, verso 0=avanti 1=indietro)
    for e, arco in enumerate(archi_base):
        if arco["verso"] in ("avanti", "doppio"):
            archi.append((arco["a"], arco["b"], arco["t_s"], e, 0))
        if arco["verso"] in ("indietro", "doppio"):
            archi.append((arco["b"], arco["a"], arco["t_s"], e, 1))

    nodi_xy = np.array(nodi, dtype=np.float64)
    return nodi, nodi_xy, archi_base, archi


def salva(cartella, nodi_xy, archi_base, archi):
    """Salva la rete in un .npz compatto (array) piu' un .json (nomi)."""
    cartella = Path(cartella)
    cartella.mkdir(parents=True, exist_ok=True)
    E = len(archi_base)
    # geometria dei tratti appiattita
    off = np.zeros(E + 1, dtype=np.int64)
    for e, arco in enumerate(archi_base):
        off[e + 1] = off[e] + len(arco["pts"])
    pts = np.empty((int(off[-1]), 2), dtype=np.float64)
    for e, arco in enumerate(archi_base):
        for k, (la, lo) in enumerate(arco["pts"]):
            pts[int(off[e]) + k] = (la, lo)
    # ATTENZIONE: i pesi (tempi) devono restare in virgola mobile. Se si
    # arrotondano a interi, molti tratti corti hanno tempo 0 e l'albero dei
    # cammini minimi si rompe (verificato il 17/10). Gli indici dei nodi
    # (fino a ~82.000) sono rappresentabili esattamente in float64.
    archi = np.array(archi, dtype=np.float64) if archi else np.zeros((0, 5), dtype=np.float64)
    np.savez_compressed(
        cartella / "rete_auto.npz",
        nodi_xy=nodi_xy,
        edge_a=np.array([a["a"] for a in archi_base], dtype=np.int64),
        edge_b=np.array([a["b"] for a in archi_base], dtype=np.int64),
        edge_len=np.array([a["len_m"] for a in archi_base], dtype=np.float64),
        edge_t=np.array([a["t_s"] for a in archi_base], dtype=np.float64),
        edge_off=off, edge_pts=pts,
        archi=archi,
        edge_corsie_avanti=np.array([a.get("corsie_avanti", 1) for a in archi_base], dtype=np.int64),
        edge_corsie_indietro=np.array([a.get("corsie_indietro", 1) for a in archi_base], dtype=np.int64),
        edge_corsie_stimate=np.array([bool(a.get("corsie_stimate", True)) for a in archi_base], dtype=bool),
        edge_bridge=np.array([bool(a.get("bridge", False)) for a in archi_base], dtype=bool),
        edge_tunnel=np.array([bool(a.get("tunnel", False)) for a in archi_base], dtype=bool),
    )
    (cartella / "rete_auto_metadati.json").write_text(json.dumps({
        "n_nodi": int(len(nodi_xy)), "n_archi_base": E, "n_archi_orientati": int(len(archi)),
        "nomi": [a["nome"] for a in archi_base],
        "highway": [a["highway"] for a in archi_base],
        "ref": [a["ref"] for a in archi_base],
        "verso": [a["verso"] for a in archi_base],
        "vel_kmh": [a["vel_kmh"] for a in archi_base],
        "corsie_avanti": [int(a.get("corsie_avanti", 1)) for a in archi_base],
        "corsie_indietro": [int(a.get("corsie_indietro", 1)) for a in archi_base],
        "corsie_stimate": [bool(a.get("corsie_stimate", True)) for a in archi_base],
        "bridge": [bool(a.get("bridge", False)) for a in archi_base],
        "tunnel": [bool(a.get("tunnel", False)) for a in archi_base],
        "junction": [a.get("junction") for a in archi_base],
        "maxspeed_raw": [a.get("maxspeed_raw") for a in archi_base],
        "width_raw": [a.get("width_raw") for a in archi_base],
        "stimato": False,
    }, ensure_ascii=False), encoding="utf-8")


def carica(cartella):
    """Ricarica la rete salvata. Ritorna un dict pronto per l'instradamento."""
    cartella = Path(cartella)
    z = np.load(cartella / "rete_auto.npz")
    meta = json.loads((cartella / "rete_auto_metadati.json").read_text(encoding="utf-8"))
    out = {
        "nodi_xy": z["nodi_xy"],
        "edge_a": z["edge_a"], "edge_b": z["edge_b"],
        "edge_len": z["edge_len"], "edge_t": z["edge_t"],
        "edge_off": z["edge_off"], "edge_pts": z["edge_pts"],
        "archi": z["archi"], "meta": meta,
    }
    for k in ("edge_corsie_avanti", "edge_corsie_indietro", "edge_corsie_stimate",
              "edge_bridge", "edge_tunnel"):
        if k in z.files:
            out[k] = z[k]
    return out


def geometria_arco(rete, e):
    o0, o1 = int(rete["edge_off"][e]), int(rete["edge_off"][e + 1])
    return rete["edge_pts"][o0:o1]


def punto_medio(rete, e):
    p = geometria_arco(rete, e)
    # punto a meta' lunghezza del tracciato
    if len(p) == 1:
        return float(p[0, 0]), float(p[0, 1])
    d = np.array([haversine_m(*p[k], *p[k + 1]) for k in range(len(p) - 1)])
    tot = float(d.sum())
    if tot <= 0:
        return float(p[0, 0]), float(p[0, 1])
    meta = tot / 2
    acc = 0.0
    for k in range(len(p) - 1):
        if acc + d[k] >= meta:
            t = (meta - acc) / d[k] if d[k] > 0 else 0
            return (float(p[k, 0] + (p[k + 1, 0] - p[k, 0]) * t),
                    float(p[k, 1] + (p[k + 1, 1] - p[k, 1]) * t))
        acc += d[k]
    return float(p[-1, 0]), float(p[-1, 1])


def punti_medi(rete):
    return np.array([punto_medio(rete, e) for e in range(len(rete["edge_a"]))])


def tratto_piu_vicino(rete, lat, lon, medi=None, candidati=40):
    """(distanza_m, indice_tratto) del tratto stradale piu' vicino al punto.
    Prima filtra sui punti medi (veloce), poi misura la distanza vera sul
    tracciato dei migliori 40. Ritorna (inf, None) se non c'e' nulla."""
    if medi is None:
        medi = punti_medi(rete)
    d2 = (medi[:, 0] - lat) ** 2 + (medi[:, 1] - lon) ** 2
    ord_ = np.argsort(d2)[:candidati]
    best = (float("inf"), None)
    for e in ord_:
        d = distanza_punto_tracciato_m(lat, lon, geometria_arco(rete, int(e)))
        if d < best[0]:
            best = (d, int(e))
    return best


def distanza_punto_tracciato_m(lat, lon, pts):
    """Distanza minima (m) fra (lat,lon) e la polilinea pts (array Nx2)."""
    best = 1e18
    for k in range(len(pts) - 1):
        la1, lo1 = pts[k]
        la2, lo2 = pts[k + 1]
        # proiezione locale in metri
        mx = math.cos(math.radians(lat)) * 111320.0
        my = 110540.0
        px, py = (lon - lo1) * mx, (lat - la1) * my
        dx, dy = (lo2 - lo1) * mx, (la2 - la1) * my
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 <= 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
        cx, cy = t * dx, t * dy
        d = math.hypot(px - cx, py - cy)
        if d < best:
            best = d
    return best


# --- semafori (stima aperta dell'auto, F3) ---------------------------------------
RAGGIO_SEMAFORI_M = 50.0     # semafori a meno di 50 m l'uno dall'altro = un incrocio solo
FILE_SEMAFORI = "semafori.json"


def _proietta(lat, lon, lat0=45.07):
    """Coordinate in metri (piano locale): basta per distanze di qualche centinaio di metri."""
    return np.column_stack([np.asarray(lon) * math.cos(math.radians(lat0)) * 111320.0, np.asarray(lat) * 110540.0])


def leggi_semafori(pbf):
    """Posizioni (lat, lon) dei nodi OSM highway=traffic_signals nel taglio."""
    import osmium
    punti = []

    class Lettore(osmium.SimpleHandler):
        def node(self, n):
            if n.tags.get("highway") == "traffic_signals" and n.location.valid():
                punti.append((n.location.lat, n.location.lon))

    Lettore().apply_file(str(pbf))
    return punti


def raggruppa_semafori(punti, raggio_m=RAGGIO_SEMAFORI_M):
    """Raggruppa i semafori entro raggio_m: si prende un punto non ancora assegnato e con lui tutti i non assegnati
    nel raggio (non a catena: un viale con un semaforo ogni 40 m non diventa un solo incrocio). Ritorna [(lat, lon, quanti)]."""
    from scipy.spatial import cKDTree
    if not punti:
        return []
    xy = _proietta([p[0] for p in punti], [p[1] for p in punti])
    albero = cKDTree(xy)
    preso = np.zeros(len(punti), dtype=bool)
    gruppi = []
    for i in range(len(punti)):
        if preso[i]:
            continue
        vicini = [j for j in albero.query_ball_point(xy[i], raggio_m) if not preso[j]]
        preso[vicini] = True
        gruppi.append((float(np.mean([punti[j][0] for j in vicini])), float(np.mean([punti[j][1] for j in vicini])), len(vicini)))
    return gruppi


def abbina_semafori(rete, gruppi, raggio_nodo_m=RAGGIO_SEMAFORI_M):
    """Ogni incrocio con semaforo va al nodo della rete piu' vicino (entro raggio_nodo_m), altrimenti al tratto piu' vicino.
    Ritorna ([nodi], [tratti]) senza ripetizioni: un nodo o un tratto conta un semaforo solo."""
    from scipy.spatial import cKDTree
    nodi_xy = rete["nodi_xy"]
    t_nodi = cKDTree(_proietta(nodi_xy[:, 0], nodi_xy[:, 1]))
    pts = rete["edge_pts"]
    lunghezze = np.diff(rete["edge_off"])
    tratto_di_punto = np.repeat(np.arange(len(lunghezze)), lunghezze)
    t_pts = cKDTree(_proietta(pts[:, 0], pts[:, 1]))
    nodi, tratti = set(), set()
    for lat, lon, _n in gruppi:
        q = _proietta([lat], [lon])[0]
        d, i = t_nodi.query(q)
        if d <= raggio_nodo_m:
            nodi.add(int(i))
        else:
            _d, k = t_pts.query(q)
            tratti.add(int(tratto_di_punto[int(k)]))
    return sorted(nodi), sorted(tratti)


def carica_semafori(cartella, pbf=None, log=print):
    """{'nodi': [...], 'tratti': [...], 'grezzi': n, 'incroci': n} dal file salvato con la rete; se manca lo ricava dal taglio OSM e lo salva."""
    cartella = Path(cartella)
    f = cartella / FILE_SEMAFORI
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    if pbf is None:
        pbf = Path(__file__).resolve().parent.parent / "data" / "otp" / "rete" / "torino_cintura.osm.pbf"
    log(f"  semafori: lettura di {Path(pbf).name} ...")
    punti = leggi_semafori(pbf)
    gruppi = raggruppa_semafori(punti)
    nodi, tratti = abbina_semafori(carica(cartella), gruppi)
    out = {"grezzi": len(punti), "incroci": len(gruppi), "raggio_m": RAGGIO_SEMAFORI_M, "nodi": nodi, "tratti": tratti}
    f.write_text(json.dumps(out), encoding="utf-8")
    log(f"  semafori: {len(punti)} nodi OSM -> {len(gruppi)} incroci ({len(nodi)} su nodi della rete, {len(tratti)} su tratti)")
    return out
