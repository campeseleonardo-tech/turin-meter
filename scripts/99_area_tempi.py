# -*- coding: utf-8 -*-
"""
scripts/99_area_tempi.py - «Area che si espande» (scheda 4): dove si arriva in N minuti, coi mezzi e in auto, partendo da Piazza Castello
o da una zona di Torino.

Sola lettura sui dati. Due parti:

1. Piazza Castello -> ogni sezione di censimento abitata del Comune di Torino (4.044, centroidi da accessibilita_piedi5.json):
   - mezzi pubblici: r5py come lo script 18 e il 93 (stesso GTFS, stessa rete OSM, cammino a 4,8 km/h), giorno 2026-10-12, partenza 7:45,
     finestra di 30 minuti, mediana, al massimo 120 minuti; chi non e' raggiunto resta null;
   - auto: rete del modello del traffico (rete_osm), cammino minimo a flusso libero come nel 93; di punta = tempo x fattore + 5 minuti
     di parcheggio. Dal giro F3 (25/10/2026) la stima principale e' quella aperta (comuni.TempiAutoAperti, alle 8): percorso piu' veloce da Piazza Castello
     a ogni sezione con le velocita' dei sensori 5T e delle sonde bus e 20 secondi per semaforo + 5 minuti. Campi: auto_stima_min e auto_favorevole_min.
     La stima dei sensori 5T (fattore unico di tp_contro_auto.json) resta come «stima piu' favorevole all'auto».
2. Zona di Torino -> zona di Torino: tabella gia' calcolata dal 93 (data/processed/tp_contro_auto.json, gruppo «a»: contiene TUTTE le
   coppie, 23 x 22); lo script la ricopia in minuti interi e assegna ogni sezione alla sua zona (punto nel poligono, imq_zone_geo.json).

Tempi in minuti interi. Uscita compatta: data/processed/area_tempi.json (la scheda ne ricava data/area_tempi.js, letto da assets/area.js).

Come si lancia
--------------
  python scripts\\99_area_tempi.py --prova 200      (200 sezioni; scrive area_tempi_prova.json)
  python scripts\\99_area_tempi.py                  (tutte le sezioni di Torino; pochi minuti, quasi tutto per avviare r5py)
  python scripts\\99_area_tempi.py --finto          (tempi finti calcolati dalla distanza, SOLO per provare pagina e formato nel cloud: scrive
                                                   area_tempi_finto.json con «finto: true»; non servono ne' r5py ne' la rete stradale)
"""
import argparse
import datetime as dt
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
PROC = RADICE / "data" / "processed"
TRAFFICO = PROC / "traffico_c"
SEZIONI = PROC / "accessibilita_piedi5.json"
TP_AUTO = PROC / "tp_contro_auto.json"
ZONE_GEO = PROC / "imq_zone_geo.json"
OUT = PROC / "area_tempi.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_AREA_TEMPI.txt"

GIORNO = dt.date(2026, 10, 12)
PARTENZA = dt.time(7, 45)
FINESTRA_MIN = 30
TEMPO_MAX_MIN = 120
VEL_PIEDI_KMH = 4.8
MIN_PARCHEGGIO = 5.0
CASTELLO = (45.0703, 7.6869)
PORTA_NUOVA = (45.0618, 7.6783)
COMUNE_TORINO = "1272"
SCALA = 10_000                       # coordinate intere: decimillesimi di grado (circa 8-11 m)


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def carica_sezioni(prova):
    d = json.loads(SEZIONI.read_text(encoding="utf-8"))
    s = [x for x in d["sezioni"] if x["id"].startswith(COMUNE_TORINO) and x.get("res", 0) > 0]
    s.sort(key=lambda x: x["id"])
    if prova:
        passo = max(1, len(s) // prova)
        s = s[::passo][:prova]
    return s


def zone_finte(sezioni, codici):
    """Solo per --finto senza imq_zone_geo.json (derivato da IMQ, fuori da git, non c'e' nel controllo di GitHub): le sezioni, ordinate per latitudine,
    si dividono in tante fasce uguali quante sono le zone. Serve solo a provare formato e pagina."""
    ordine = sorted(codici)
    per_lat = np.argsort([s["lat"] for s in sezioni], kind="stable")
    zona = np.zeros(len(sezioni), dtype=int)
    for rango, i in enumerate(per_lat):
        zona[i] = rango * len(ordine) // max(1, len(sezioni))
    return zona, 0


def zona_di_ogni_sezione(sezioni, codici):
    """Codice della zona Q... che contiene il centroide di ogni sezione (ray casting). Chi non e' in nessun poligono va alla zona piu' vicina (contato)."""
    geo = {z["cod"]: z["g"] for z in json.loads(ZONE_GEO.read_text(encoding="utf-8")) if z["cod"] in codici}
    lat = np.array([s["lat"] for s in sezioni])
    lon = np.array([s["lon"] for s in sezioni])
    zona = np.full(len(sezioni), -1, dtype=int)
    ordine = sorted(codici)
    for k, cod in enumerate(ordine):
        for anello in geo[cod]:
            a = np.asarray(anello, dtype=float)                       # righe [lat, lon]
            dentro = np.zeros(len(sezioni), dtype=bool)
            x, y = a[:, 1], a[:, 0]
            for i in range(len(a)):
                j = i - 1
                incrocia = ((y[i] > lat) != (y[j] > lat)) & (lon < (x[j] - x[i]) * (lat - y[i]) / (y[j] - y[i] + 1e-18) + x[i])
                dentro ^= incrocia
            zona[dentro & (zona < 0)] = k
    fuori = int((zona < 0).sum())
    if fuori:
        centri = np.array([np.mean(np.concatenate([np.asarray(r, float) for r in geo[c]]), axis=0) for c in ordine])
        for i in np.nonzero(zona < 0)[0]:
            zona[i] = int(np.argmin((centri[:, 0] - lat[i]) ** 2 + (centri[:, 1] - lon[i]) ** 2))
    return zona, fuori


def tempi_tp(sezioni):
    """Minuti coi mezzi da Piazza Castello a ogni sezione (nan = non raggiunta entro 120 minuti)."""
    import pandas as pd
    spec = importlib.util.spec_from_file_location("acc18", AQUI / "18_accessibilita.py")
    m18 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m18)
    rete, gpd = m18.avvia_rete()
    from r5py import TransportMode as TM
    from r5py import TravelTimeMatrix
    dest = pd.DataFrame({"id": [s["id"] for s in sezioni], "lat": [s["lat"] for s in sezioni], "lon": [s["lon"] for s in sezioni]})
    dest = gpd.GeoDataFrame(dest, geometry=gpd.points_from_xy(dest["lon"], dest["lat"]), crs="EPSG:4326")
    orig = pd.DataFrame({"id": ["CASTELLO"], "lat": [CASTELLO[0]], "lon": [CASTELLO[1]]})
    orig = gpd.GeoDataFrame(orig, geometry=gpd.points_from_xy(orig["lon"], orig["lat"]), crs="EPSG:4326")
    mat = TravelTimeMatrix(rete, origins=orig, destinations=dest, departure=dt.datetime.combine(GIORNO, PARTENZA),
                           departure_time_window=dt.timedelta(minutes=FINESTRA_MIN), transport_modes=[TM.TRANSIT, TM.WALK],
                           speed_walking=VEL_PIEDI_KMH, max_time=dt.timedelta(minutes=TEMPO_MAX_MIN))
    mat = pd.DataFrame(mat)
    col = "travel_time" if "travel_time" in mat.columns else "travel_time_p50"
    v = mat[col]
    if str(v.dtype).startswith("timedelta"):
        v = v.dt.total_seconds() / 60.0
    per_id = {str(a): (float(x) if x == x else np.nan) for a, x in zip(mat["to_id"], v)}
    return np.array([per_id.get(str(s["id"]), np.nan) for s in sezioni])


def tempi_auto_liberi(sezioni, punti_extra):
    """Minuti in auto da Piazza Castello a ogni sezione e ai punti extra (rete del modello del traffico, come il 93):
    (libero, libero_extra, aperto_alle_8, aperto_extra), con «aperto» = stima aperta alle 8 senza i minuti di parcheggio (comuni.TempiAutoAperti)."""
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components, dijkstra
    from scipy.spatial import cKDTree
    import rete_osm
    rete = rete_osm.carica(TRAFFICO / "rete")
    xy, archi = rete["nodi_xy"], rete["archi"]
    N = len(xy)
    src, dst, w = archi[:, 0].astype(np.int64), archi[:, 1].astype(np.int64), archi[:, 2].astype(np.float64)
    chiave = src * N + dst
    ordine = np.lexsort((w, chiave))
    ks = chiave[ordine]
    primo = np.concatenate(([True], ks[1:] != ks[:-1]))
    sel = ordine[primo]
    tieni = src[sel] != dst[sel]
    M = csr_matrix((w[sel][tieni], (src[sel][tieni], dst[sel][tieni])), shape=(N, N))
    _, et = connected_components(M, directed=True, connection="strong")
    nodi_princ = np.nonzero(et == np.argmax(np.bincount(et)))[0]
    k = np.cos(np.radians(45.07))
    albero = cKDTree(np.column_stack([xy[nodi_princ, 0], xy[nodi_princ, 1] * k]))

    def nodo(lat, lon):
        return int(nodi_princ[albero.query([lat, lon * k])[1]])

    n0 = nodo(*CASTELLO)
    nodi = [nodo(s["lat"], s["lon"]) for s in sezioni]
    nodi_extra = [nodo(*p) for p in punti_extra]
    dist = dijkstra(M, indices=[n0])[0]
    dist_ap = dijkstra(comuni.TempiAutoAperti().matrice_pesi(8)[0], indices=[n0])[0]
    return (np.array([dist[n] for n in nodi]) / 60.0, np.array([dist[n] for n in nodi_extra]) / 60.0,
            np.array([dist_ap[n] for n in nodi]) / 60.0, np.array([dist_ap[n] for n in nodi_extra]) / 60.0)


def tempi_finti(sezioni, punti_extra):
    """Solo per provare: distanza in linea d'aria da Piazza Castello, mezzi 3 minuti ogni km piu' 6; auto 1,6 minuti ogni km piu' 1."""
    def km(lat, lon):
        return comuni.haversine_m(CASTELLO[0], CASTELLO[1], lat, lon) / 1000.0
    d = np.array([km(s["lat"], s["lon"]) for s in sezioni])
    rng = np.random.default_rng(7)
    tp = 6 + 3.0 * d * (1 + 0.25 * rng.random(len(d)))
    tp[d > 8.5] = np.nan
    libero, libero_pn = 1.0 + 1.6 * d, np.array([1.0 + 1.6 * km(*p) for p in punti_extra])
    return tp, libero, libero_pn, np.array([6 + 3.0 * km(*p) for p in punti_extra]), 1.8 * libero, 1.8 * libero_pn


def intero(v):
    return None if v != v else int(round(float(v)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", type=int, default=0, help="usa solo N sezioni")
    ap.add_argument("--finto", action="store_true", help="tempi finti dalla distanza (solo per provare la pagina)")
    args = ap.parse_args()
    finte = args.finto and not ZONE_GEO.exists()      # con --finto le zone possono essere finte (L23: serve al controllo di GitHub)
    if not finte:
        comuni.richiedi_fonte(ZONE_GEO)      # L12: derivato da IMQ, fuori da git
    c = comuni.Controlli()
    sezioni = carica_sezioni(args.prova)
    log(f"sezioni di Torino con residenti: {len(sezioni)} ({sum(s['res'] for s in sezioni):,} residenti)")

    t93 = json.loads(TP_AUTO.read_text(encoding="utf-8"))
    par = t93["parametri"]
    f_alto = par["fattore_punta"]
    cop = [p for p in t93["coppie"] if p["gruppo"] == "a"]
    nomi = {z["zona"]: z["nome"] for z in t93["per_zona"]}
    codici = sorted({p["da"] for p in cop} | {p["a"] for p in cop})
    log(f"sensori 5T: fattore {f_alto:g}; stima principale: stima aperta alle 8; {len(codici)} zone di Torino")

    controlli_punti = [PORTA_NUOVA]
    if args.finto:
        tp, libero, libero_pn, tp_pn, aperto, aperto_pn = tempi_finti(sezioni, controlli_punti)
        log("ATTENZIONE: tempi FINTI (--finto), non usare per le schede vere")
    else:
        log("mezzi pubblici: r5py ...")
        tp = tempi_tp(sezioni)
        log("auto: cammini minimi sulla rete del modello ...")
        libero, libero_pn, aperto, aperto_pn = tempi_auto_liberi(sezioni, controlli_punti)
    # L24: i tempi coi mezzi si correggono con le misure come negli script 93, 94 e 100 (comuni.tempo_mezzi_corretto, script 105); nan resta nan
    if not comuni.correzione_tempi_mezzi():
        log("AVVISO: manca data/processed/correzione_tempi_mezzi.json (script 105): i tempi coi mezzi restano da orario")
    tp = comuni.tempo_mezzi_corretto(tp, "punta_mattina")
    auto_favorevole_min = libero * f_alto + MIN_PARCHEGGIO

    # ---- zona -> zona (dal 93) e zona di ogni sezione
    k_zona = {z: i for i, z in enumerate(codici)}
    n = len(codici)
    z_tp = [[0] * n for _ in range(n)]
    z_a1 = [[0] * n for _ in range(n)]
    z_a2 = [[0] * n for _ in range(n)]
    z_a3 = [[0] * n for _ in range(n)]
    corr = comuni.fattore_controllo()   # B: stima aperta corretta col controllo con TomTom (§6.2)
    for p in cop:
        i, j = k_zona[p["da"]], k_zona[p["a"]]
        z_tp[i][j], z_a1[i][j], z_a2[i][j] = intero(p["tp_min"]), intero(p["auto_favorevole_min"]), intero(p["auto_stima_min"])
        z_a3[i][j] = intero((p["auto_stima_min"] - MIN_PARCHEGGIO) * corr + MIN_PARCHEGGIO)
    zona, fuori = zone_finte(sezioni, codici) if finte else zona_di_ogni_sezione(sezioni, codici)
    log(f"sezioni assegnate alle zone: {len(sezioni) - fuori} dentro un poligono, {fuori} alla zona piu' vicina")
    # stima principale: stima aperta alle 8 da Piazza Castello a ogni sezione + minuti di parcheggio
    auto_stima_min = aperto + MIN_PARCHEGGIO
    auto_corretta_min = aperto * comuni.fattore_controllo() + MIN_PARCHEGGIO
    with np.errstate(invalid="ignore", divide="ignore"):
        f_basso = round(float(np.nanmedian(aperto / libero)), 2)         # numero riassuntivo: mediana di (tempo aperto / flusso libero) sulle sezioni
    log(f"fattore della stima aperta: mediana {f_basso:g} (tempo aperto / flusso libero)")

    # ---- controlli
    c("nessun tempo negativo", bool(np.all(tp[~np.isnan(tp)] >= 0) and np.all(libero >= 0)), bloccante=True)
    c("tutte le sezioni hanno una zona", bool(np.all(zona >= 0)), bloccante=True)
    pieno = sum(1 for i in range(n) for j in range(n) if i != j and z_tp[i][j] is None)
    c("tabella zona-zona completa (nessuna coppia vuota)", pieno == 0, dettaglio=f"{n} x {n - 1} coppie", bloccante=True)
    senza_tp = int(np.isnan(tp).sum())
    c("sezioni senza collegamento coi mezzi entro 120 minuti (contate a parte)", True, dettaglio=f"{senza_tp} su {len(sezioni)}")
    if not args.finto and not args.prova:
        vicino = int(np.argmin([comuni.haversine_m(CASTELLO[0], CASTELLO[1], s["lat"], s["lon"]) for s in sezioni]))
        c("la sezione piu' vicina a Piazza Castello e' a meno di 10 minuti in auto a flusso libero", libero[vicino] < 10,
          dettaglio=f"{libero[vicino]:.1f} minuti")
        pn = libero_pn[0]
        c("Piazza Castello -> Porta Nuova: auto a flusso libero sotto 10 minuti", pn < 10, dettaglio=f"{pn:.1f} minuti")
        sez_pn = int(np.argmin([comuni.haversine_m(PORTA_NUOVA[0], PORTA_NUOVA[1], s["lat"], s["lon"]) for s in sezioni]))
        c("Piazza Castello -> sezione di Porta Nuova coi mezzi sotto 15 minuti", tp[sez_pn] < 15, dettaglio=f"{tp[sez_pn]:.1f} minuti")
    soglie = (10, 20, 30, 45)
    res = np.array([s["res"] for s in sezioni], dtype=float)
    quote = {}
    for nome, v in (("mezzi", tp), ("auto_favorevole_min", auto_favorevole_min), ("auto_stima_min", auto_stima_min), ("auto_corretta_min", auto_corretta_min)):
        quote[nome] = {str(t): round(100 * float(res[np.nan_to_num(v, nan=1e9) <= t].sum() / res.sum()), 1) for t in soglie}
    c("con piu' minuti si raggiunge sempre di piu' (tutte le soglie)", all(
        list(q.values()) == sorted(q.values()) for q in quote.values()), bloccante=True)

    la0, lo0 = min(s["lat"] for s in sezioni), min(s["lon"] for s in sezioni)
    out = {
        "generato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "finto": bool(args.finto),
        "stimato": True,
        "parametri": {"correzione_tempi_mezzi": bool(comuni.correzione_tempi_mezzi()), "giorno": str(GIORNO), "partenza": f"{PARTENZA:%H:%M}", "finestra_min": FINESTRA_MIN, "tempo_max_min": TEMPO_MAX_MIN,
                      "velocita_piedi_kmh": VEL_PIEDI_KMH, "minuti_parcheggio": MIN_PARCHEGGIO, "fattore_alto": f_alto, "fattore_basso": f_basso,
                      "fonte_basso": "stima aperta alle 8 (sensori 5T, sonde bus, 20 secondi per semaforo); fattore_basso = mediana di tempo aperto / flusso libero",
                      "punto": "Piazza Castello", "punto_coord": list(CASTELLO), "scala_coordinate": SCALA, "origine": [la0, lo0], "soglie": list(soglie),
                      "prova": bool(args.prova), "n_sezioni": len(sezioni)},
        "quote_residenti": quote,
        "sezioni": {"x": [int(round((s["lon"] - lo0) * SCALA)) for s in sezioni], "y": [int(round((s["lat"] - la0) * SCALA)) for s in sezioni],
                    "res": [int(s["res"]) for s in sezioni], "zona": [int(z) for z in zona]},
        "castello": {"mezzi": [intero(v) for v in tp], "auto_favorevole_min": [intero(v) for v in auto_favorevole_min], "auto_stima_min": [intero(v) for v in auto_stima_min], "auto_corretta_min": [intero(v) for v in auto_corretta_min]},
        "zone": {"codici": codici, "nomi": [nomi.get(z, z) for z in codici], "mezzi": z_tp, "auto_favorevole_min": z_a1, "auto_stima_min": z_a2, "auto_corretta_min": z_a3},
        "controlli": list(c.righe),
    }
    suff = "_finto" if args.finto else ("_prova" if args.prova else "")
    dest = OUT.with_name(OUT.stem + suff + ".json")
    dest.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    log(f"scritto {dest.relative_to(RADICE)} ({dest.stat().st_size / 1024:.0f} KB)")

    righe = ["RAPPORTO - Area che si espande (script 99)", f"generato {out['generato']}" + ("  *** TEMPI FINTI ***" if args.finto else ""), "",
             f"Sezioni di Torino: {len(sezioni)}; senza collegamento coi mezzi entro {TEMPO_MAX_MIN} minuti: {senza_tp}",
             f"Auto: flusso libero x fattore + {MIN_PARCHEGGIO:g} minuti di parcheggio. Stima aperta (principale): percorso alle 8 con sensori, sonde bus e semafori, fattore mediano {f_basso:g}; "
             f"stima dei sensori 5T (la piu' favorevole all'auto): fattore {f_alto:g}.", "",
             "Residenti di Torino raggiunti da Piazza Castello (%):", "  minuti      " + "".join(f"{t:>8}" for t in soglie)]
    for nome, et in (("mezzi", "coi mezzi"), ("auto_favorevole_min", f"auto sensori x{f_alto:g}"), ("auto_stima_min", "auto stima aperta"), ("auto_corretta_min", "auto corretta")):
        righe.append(f"  {et:<12}" + "".join(f"{quote[nome][str(t)]:>8.1f}" for t in soglie))
    righe += ["", "Controlli:"] + [f"  {r}" for r in c.righe]
    if not args.finto and not args.prova:
        RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
        log(f"scritto {RAPPORTO.relative_to(RADICE)}")
    print("\n".join(righe))
    if c.avvisi():
        print("AVVISI presenti: leggi le righe sopra")


if __name__ == "__main__":
    main()
