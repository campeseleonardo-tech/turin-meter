# -*- coding: utf-8 -*-
"""
scripts/51_tp_gtfs_tratti.py - Pacchetto B del piano Fase 4 (offerta di bus/tram).

Per ogni TRATTO della rete stradale (gli stessi 105.890 della Fase 3) conta
quanti passaggi di bus e tram ci sono in un giorno feriale tipico, e in che
fascia (mattina 7-9, sera 17-19, giorno 6-21).

Metodo (map matching delle forme GTFS sui tratti OSM):
 - si scelgono le corse dei bus (route_type 3) e dei tram (route_type 0) attive
   nel giorno scelto (calendar + calendar_dates);
 - per ogni corsa si prende la sua forma (shape_id); la polilinea della forma
   viene ricampionata ogni ~25 m e ogni punto si aggancia al tratto stradale
   piu' vicino se entro 25 m (i tram, che possono stare su binari non presenti
   nella rete auto, si agganciano alla strada piu' vicina);
 - una corsa e' "agganciata" se almeno il 60% dei punti ricadenti nel riquadro
   del taglio OSM si aggancia e almeno 5 tratti distinti risultano coperti;
 - i conteggi si fanno per forma (una volta), poi moltiplicati per il numero di
   corse che usano quella forma.

Il conteggio per tratto e' "quante corse passano da quel tratto" (presenza), non
il numero di volte: una corsa conta 1 su ogni tratto che tocca.

La metropolitana (route_type 1) e la funicolare (7) NON scorrono sulle strade e
non entrano nei passaggi: vengono registrate a parte (pacchetto 52) come
metro_vicina / ferrovia_vicina.

Input:  data/raw/gtt_gtfs_20261003_224530.zip
        data/processed/traffico_c/rete/rete_auto.npz
        data/processed/traffico_c/segmenti.csv   (id_tratto -> corridoio)
Output: data/processed/traffico_c/tp_conteggi.npz  (conteggi per tratto)
        data/processed/traffico_c/tp_tratti.csv
        docs/rapporti/RAPPORTO_TP_PER_STRADA.txt (parte 1: tratti + controlli)
"""

import argparse
import csv
import io
import math
import sys
import time
import zipfile
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
RAW = RADICE / "data" / "raw"
OUT_DIR = RADICE / "data" / "processed" / "traffico_c"
RETE_DIR = OUT_DIR / "rete"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_TP_PER_STRADA.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
GTFS = RAW / "gtt_gtfs_20261003_224530.zip"

SOGLIA_AGGANCIO_M = 25.0
FRAZIONE_AGGANCIA = 0.60
MIN_TRATTI_AGGANCIA = 5
CELLA = 0.0015          # ~165 m in latitudine


# ------------------------------------------------------------------ geometria
def costruisci_griglia(rete):
    """Griglia cella -> lista di indici di tratti che hanno un vertice nella cella."""
    pts = rete["edge_pts"]
    off = rete["edge_off"]
    griglia = defaultdict(list)
    for e in range(len(off) - 1):
        visti = set()
        for k in range(int(off[e]), int(off[e + 1])):
            la, lo = float(pts[k, 0]), float(pts[k, 1])
            c = (math.floor(la / CELLA), math.floor(lo / CELLA))
            # inserisco sia la cella sia i vicini immediati per robustezza
            if c not in visti:
                visti.add(c)
                griglia[c].append(e)
    return griglia


def distanza_min_m(lat, lon, pts):
    best = 1e18
    mx = math.cos(math.radians(lat)) * 111320.0
    my = 110540.0
    for k in range(len(pts) - 1):
        la1, lo1 = float(pts[k, 0]), float(pts[k, 1])
        la2, lo2 = float(pts[k + 1, 0]), float(pts[k + 1, 1])
        px, py = (lon - lo1) * mx, (lat - la1) * my
        dx, dy = (lo2 - lo1) * mx, (la2 - la1) * my
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 <= 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
        d = math.hypot(px - t * dx, py - t * dy)
        if d < best:
            best = d
    return best


def aggancia(lat, lon, rete, griglia, cache_geom):
    ci, cj = math.floor(lat / CELLA), math.floor(lon / CELLA)
    cand = set()
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            cand.update(griglia.get((ci + di, cj + dj), ()))
    best = (1e18, None)
    for e in cand:
        g = cache_geom.get(e)
        if g is None:
            g = rete_osm.geometria_arco(rete, e)
            cache_geom[e] = g
        d = distanza_min_m(lat, lon, g)
        if d < best[0]:
            best = (d, e)
    return best


def ricampiona(pts, passo_m):
    """Punti della polilinea ogni ~passo_m (i punti originali sono sempre inclusi)."""
    out = [pts[0]]
    acc = 0.0
    for k in range(len(pts) - 1):
        la1, lo1 = pts[k]
        la2, lo2 = pts[k + 1]
        d = rete_osm.haversine_m(la1, lo1, la2, lo2)
        if d <= 0:
            continue
        acc += d
        if acc >= passo_m:
            out.append(pts[k + 1])
            acc = 0.0
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out


# ------------------------------------------------------------------ GTFS
def leggi_csv_zip(z, nome):
    with z.open(nome) as fh:
        return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig")))


def attive_al(z, data):
    """Insieme dei service_id attivi in una data (YYYYMMDD) secondo calendar+exceptions."""
    import datetime
    d = datetime.datetime.strptime(data, "%Y%m%d").date()
    wd = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][d.weekday()]
    s = set()
    for c in leggi_csv_zip(z, "calendar.txt"):
        if c["start_date"] <= data <= c["end_date"] and c[wd] == "1":
            s.add(c["service_id"])
    add, rem = set(), set()
    for e in leggi_csv_zip(z, "calendar_dates.txt"):
        if e["date"] == data:
            (add if e["exception_type"] == "1" else rem).add(e["service_id"])
    return (s | add) - rem


def ora_da_stringa(s):
    """'HH:MM:SS' -> ora intera (0-47, puo' superare 24 per le corse notturne)."""
    if not s:
        return None
    try:
        return int(s.split(":")[0])
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="20261014", help="giorno feriale tipico YYYYMMDD")
    ap.add_argument("--campione", type=int, default=0, help="solo N forme (prova rapida)")
    args = ap.parse_args()

    t0 = time.time()
    rete = rete_osm.carica(RETE_DIR)
    n_edge = len(rete["edge_a"])
    print(f"rete: {n_edge:,} tratti")
    griglia = costruisci_griglia(rete)
    print(f"griglia: {len(griglia):,} celle  ({time.time()-t0:.1f} s)")
    cache_geom = {}

    # corridoio per tratto (da segmenti.csv della Fase 3)
    corr_per_tratto = [""] * n_edge
    with (OUT_DIR / "segmenti.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            corr_per_tratto[int(r["id_tratto"])] = r["corridoio"]

    z = zipfile.ZipFile(GTFS)
    servizi = attive_al(z, args.data)
    print(f"servizi attivi il {args.data}: {len(servizi):,}")

    routes = {r["route_id"]: r for r in leggi_csv_zip(z, "routes.txt")}
    tipi_ok = {"0", "3"}   # 0 = tram, 3 = bus
    trips = []
    for t in leggi_csv_zip(z, "trips.txt"):
        if t["service_id"] not in servizi:
            continue
        r = routes.get(t["route_id"])
        if r is None or r["route_type"] not in tipi_ok:
            continue
        trips.append({"trip_id": t["trip_id"], "route_id": t["route_id"],
                      "shape_id": t["shape_id"],
                      "linea": (r.get("route_short_name") or "").strip() or t["route_id"]})
    print(f"corse bus/tram il giorno tipico: {len(trips):,}")

    # ora di partenza = prima fermata di ogni corsa (stop_sequence minima)
    import pandas as pd
    with z.open("stop_times.txt") as fh:
        st = pd.read_csv(fh, usecols=["trip_id", "stop_sequence", "departure_time"], dtype=str)
    st["stop_sequence"] = st["stop_sequence"].astype(int)
    st = st.sort_values(["trip_id", "stop_sequence"])
    prime = st.drop_duplicates("trip_id", keep="first").set_index("trip_id")["departure_time"]
    trip_orari = {tid: ora_da_stringa(prime.get(tid)) for tid in set(t["trip_id"] for t in trips)}
    print(f"orari letti per {len(trip_orari):,} corse  ({time.time()-t0:.1f} s)")

    # forme usate
    forma_di = {}
    for t in trips:
        forma_di.setdefault(t["shape_id"], []).append(t)
    shape_ids = list(forma_di)
    if args.campione:
        shape_ids = shape_ids[:args.campione]
    print(f"forme distinte: {len(forma_di):,} (elaboro {len(shape_ids):,})")

    # punti delle forme
    punti_forma = defaultdict(list)
    with z.open("shapes.txt") as fh:
        for r in csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig")):
            punti_forma[r["shape_id"]].append((int(r["shape_pt_sequence"]),
                                               float(r["shape_pt_lat"]), float(r["shape_pt_lon"])))

    conta_giorno = np.zeros(n_edge, dtype=np.float64)
    conta_am = np.zeros(n_edge, dtype=np.float64)
    conta_pm = np.zeros(n_edge, dtype=np.float64)
    conta_giorno_tutte = np.zeros(n_edge, dtype=np.float64)  # include anche corse non agganciate (diagnostica)
    linee_tratto = defaultdict(set)
    corse_agganciate = 0
    corse_totali = 0
    forme_non_agganciate = []
    tot_punti = 0
    tot_agganciati = 0
    t1 = time.time()
    for i, sid in enumerate(shape_ids):
        ptraw = punti_forma.get(sid)
        corse = forma_di[sid]
        corse_totali += len(corse)
        if not ptraw:
            continue
        ptraw.sort()
        pts = [(la, lo) for _, la, lo in ptraw]
        campioni = ricampiona(pts, 25.0)
        tot_punti += len(campioni)
        # solo i campioni dentro il riquadro del taglio OSM (quelli fuori non
        # possono essere valutati: la rete caricata finisce li')
        dentro = [(la, lo) for (la, lo) in campioni
                  if 7.45 <= lo <= 7.93 and 44.90 <= la <= 45.24]
        if not dentro:
            continue
        tratti = set()
        n_ok = 0
        for (la, lo) in dentro:
            d, e = aggancia(la, lo, rete, griglia, cache_geom)
            if e is not None and d <= SOGLIA_AGGANCIO_M:
                tratti.add(e)
                n_ok += 1
        fraz = n_ok / len(dentro)
        tot_agganciati += n_ok
        agganciata = (fraz >= FRAZIONE_AGGANCIA and len(tratti) >= MIN_TRATTI_AGGANCIA)
        if not agganciata:
            forme_non_agganciate.append((sid, len(corse), round(fraz, 3), len(tratti)))
            continue
        corse_agganciate += len(corse)
        linee = {c["linea"] for c in corse}
        am = sum(1 for c in corse if trip_orari.get(c["trip_id"]) in (7, 8))
        pm = sum(1 for c in corse if trip_orari.get(c["trip_id"]) in (17, 18))
        diurno = sum(1 for c in corse if trip_orari.get(c["trip_id"]) is not None
                     and 6 <= trip_orari[c["trip_id"]] <= 21)
        arr = np.fromiter(tratti, dtype=np.int64)
        conta_giorno[arr] += diurno
        conta_am[arr] += am
        conta_pm[arr] += pm
        conta_giorno_tutte[arr] += len(corse)
        for e in arr:
            linee_tratto[int(e)] |= linee
        if (i + 1) % 100 == 0:
            print(f"  forme {i+1}/{len(shape_ids)}  ({time.time()-t1:.0f} s)")
    print(f"map matching fatto in {time.time()-t1:.0f} s")

    # --- output npz ---
    np.savez_compressed(OUT_DIR / "tp_conteggi.npz",
                        giorno=conta_giorno, am=conta_am, pm=conta_pm,
                        giorno_tutte=conta_giorno_tutte)
    n_linee = np.array([len(linee_tratto[int(e)]) if int(e) in linee_tratto else 0
                        for e in range(n_edge)], dtype=np.int64)

    # --- tp_tratti.csv ---
    with (OUT_DIR / "tp_tratti.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["id_tratto", "corridoio", "passaggi_giorno_6_21", "passaggi_punta_am_7_9",
                    "passaggi_punta_pm_17_19", "passaggi_ora_punta_am", "passaggi_ora_punta_pm",
                    "linee_diverse", "linee"])
        for e in range(n_edge):
            ln = linee_tratto.get(e, set())
            w.writerow([e, corr_per_tratto[e], round(float(conta_giorno[e]), 1),
                        round(float(conta_am[e]), 1), round(float(conta_pm[e]), 1),
                        round(float(conta_am[e]) / 2.0, 2), round(float(conta_pm[e]) / 2.0, 2),
                        len(ln), "|".join(sorted(ln))])

    # --- controlli ---
    quota = corse_agganciate / corse_totali if corse_totali else 0.0
    tratti_con_tp = int((conta_giorno > 0).sum())
    righe = []
    a = righe.append
    a("OFFERTA DI TRASPORTO PUBBLICO PER STRADA (pacchetto B, Fase 4)")
    a("=" * 74)
    a(f"giorno feriale tipico scelto: {args.data} (mercoledi')")
    a(f"servizi attivi: {len(servizi):,}   corse bus/tram: {corse_totali:,}")
    a(f"corse agganciate alla rete stradale: {corse_agganciate:,} "
      f"({100*quota:.1f}%)  - soglia di arresto 75%: {'OK' if quota >= 0.75 else 'SOTTO SOGLIA'}")
    a(f"forme distinte elaborate: {len(shape_ids):,}   forme non agganciate: {len(forme_non_agganciate):,}")
    a(f"punti di forma (ricampionati): {tot_punti:,}   agganciati entro {SOGLIA_AGGANCIO_M:.0f} m: "
      f"{tot_agganciati:,} ({100*tot_agganciati/max(tot_punti,1):.1f}%)")
    a(f"tratti con almeno un passaggio: {tratti_con_tp:,} su {n_edge:,} "
      f"({100*tratti_con_tp/n_edge:.1f}%)")
    a("")
    a("ATTENZIONE: i conteggi in tp_tratti.csv coprono SOLO le corse agganciate.")
    a("")
    a("20 tratti con piu' passaggi diurni (6-21):")
    for e in np.argsort(-conta_giorno)[:20]:
        a(f"  {int(conta_giorno[e]):5d} pass  {str(corr_per_tratto[e])[:40]:40s} "
          f"punta am {int(conta_am[e]):4d}  pm {int(conta_pm[e]):4d}  linee {n_linee[e]}")
    if forme_non_agganciate:
        a("")
        a("prime forme non agganciate (i campioni fuori dal riquadro non sono valutabili):")
        for sid, nc, fr, nt in forme_non_agganciate[:12]:
            a(f"  forma {sid}  {nc} corse  frazione agganciata {fr}  tratti {nt}")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))
    print(f"\nFatto in {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
