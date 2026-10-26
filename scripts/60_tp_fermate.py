# -*- coding: utf-8 -*-
"""
scripts/60_tp_fermate.py - Pacchetto D (Fase 5), parte 1: frequenza per FERMATA.

Principio: si usano SOLO le COORDINATE delle fermate (stops.txt lat/lon), mai i
nomi. Per il giorno feriale tipico (mercoledi' 14/10/2026, ricontrollato sul
calendario GTFS) si contano le partenze per fermata:
  - ora di punta mattina (7-9) e sera (17-19): partenze/ora;
  - giorno 6-21;
  - numero di linee;
  - bus/tram (route_type 0 e 3) separati da metropolitana (1) e ferrovia (2).
Le fermate con parent_station si contano UNA volta (aggregate sulla stazione).

Controllo indipendente: le partenze totali bus/tram sono ricalcolate con un
secondo metodo (espansione dei servizi giorno per giorno).

Output: data/processed/traffico_d/tp_fermate.csv
        data/processed/traffico_d/tp_fermate_meta.json
"""

import csv
import io
import json
import math
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

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
OUT = RADICE / "data" / "processed" / "traffico_d"
GTFS = RAW / "gtt_gtfs_20261003_224530.zip"


def leggi_csv_zip(z, nome):
    with z.open(nome) as fh:
        return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig")))


def attive_al(z, data):
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
    return (s | add) - rem, d, wd


def main():
    t0 = time.time()
    data = "20261014"
    z = zipfile.ZipFile(GTFS)
    servizi, d, wd = attive_al(z, data)
    print(f"giorno tipico {data} ({wd})  servizi attivi: {len(servizi):,}")

    routes = {r["route_id"]: r for r in leggi_csv_zip(z, "routes.txt")}
    stops = {s["stop_id"]: s for s in leggi_csv_zip(z, "stops.txt")}
    trips = {t["trip_id"]: t for t in leggi_csv_zip(z, "trips.txt") if t["service_id"] in servizi}
    print(f"corse attive: {len(trips):,}")

    # partenze per (stop_id, ora) per tipo
    with z.open("stop_times.txt") as fh:
        st = pd.read_csv(fh, dtype=str, usecols=["trip_id", "stop_id", "departure_time"])
    st = st[st["trip_id"].isin(trips.keys())].copy()
    st["ora"] = st["departure_time"].str.slice(0, 2)
    st["ora"] = pd.to_numeric(st["ora"], errors="coerce")
    st = st.dropna(subset=["ora"])
    st["ora"] = st["ora"].astype(int) % 24
    st["route_type"] = st["trip_id"].map(lambda t: routes.get(trips[t]["route_id"], {}).get("route_type"))
    st["linea"] = st["trip_id"].map(
        lambda t: (routes.get(trips[t]["route_id"], {}).get("route_short_name") or "").strip())
    print(f"stop_times attivi: {len(st):,}  ({time.time()-t0:.0f} s)")

    # mappa fermata -> stazione (parent) e coordinate
    def _coord(sid):
        s = stops.get(sid)
        if not s:
            return (None, None)
        return (float(s["stop_lat"]), float(s["stop_lon"]))

    parent = {}
    for sid, s in stops.items():
        if s.get("parent_station"):
            parent[sid] = s["parent_station"]

    def chiave(sid):
        return parent.get(sid, sid)

    st["fermata"] = st["stop_id"].map(chiave)

    def coord_di(fid):
        s = stops.get(fid)
        if s and s.get("stop_lat"):
            return float(s["stop_lat"]), float(s["stop_lon"])
        # stazione senza coordinate proprie: prendi un figlio
        for sid, p in parent.items():
            if p == fid:
                return _coord(sid)
        return (None, None)

    urbano = {"0", "3"}  # tram e bus
    out = []
    grp = st.groupby("fermata")
    for fid, g in grp:
        lat, lon = coord_di(fid)
        if lat is None:
            continue
        ora = g["ora"].values
        tipo = g["route_type"].values
        linee = set(x for x in g["linea"].values if x)
        bus = np.isin(tipo, list(urbano))
        am = int(np.sum(bus & ((ora == 7) | (ora == 8))))
        pm = int(np.sum(bus & ((ora == 17) | (ora == 18))))
        giorno = int(np.sum(bus & (ora >= 6) & (ora <= 21)))
        metro = int(np.sum(np.isin(tipo, ["1"])))
        ferro = int(np.sum(np.isin(tipo, ["2"])))
        if am == 0 and pm == 0 and giorno == 0 and metro == 0 and ferro == 0:
            continue
        out.append({
            "fermata": fid, "lat": lat, "lon": lon,
            "partenze_ora_am": round(am / 2.0, 2), "partenze_ora_pm": round(pm / 2.0, 2),
            "partenze_giorno_6_21": giorno, "n_linee": len(linee),
            "linee": "|".join(sorted(linee)),
            "n_metro": metro, "n_ferrovia": ferro,
            "tipo": "metro" if metro else ("ferrovia" if ferro else "bus_tram"),
        })

    # --- controllo indipendente: espansione servizi giorno per giorno ---
    import datetime
    attivi2 = set()
    for c in leggi_csv_zip(z, "calendar.txt"):
        if c[wd] == "1":
            ini = datetime.datetime.strptime(c["start_date"], "%Y%m%d").date()
            fin = datetime.datetime.strptime(c["end_date"], "%Y%m%d").date()
            if ini <= d <= fin:
                attivi2.add(c["service_id"])
    for e in leggi_csv_zip(z, "calendar_dates.txt"):
        if e["date"] == data:
            (attivi2.add if e["exception_type"] == "1" else attivi2.discard)(e["service_id"])
    tot2 = sum(1 for t in leggi_csv_zip(z, "trips.txt")
               if t["service_id"] in attivi2 and routes.get(t["route_id"], {}).get("route_type") in urbano)
    tot1 = sum(1 for t in trips.values() if routes.get(t["route_id"], {}).get("route_type") in urbano)

    # --- raggruppa le fermate della stessa POSIZIONE (i due versi sono fermate
    # distinte nello stesso punto): entro 40 m si contano come una sola, cosi'
    # "partenze/ora" = somma dei due versi (come chiede il piano). ---
    CELLA = 0.0006  # ~65 m
    griglia = defaultdict(list)
    for i, o in enumerate(out):
        griglia[(math.floor(o["lat"] / CELLA), math.floor(o["lon"] / CELLA))].append(i)
    padre = list(range(len(out)))

    def rad(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    def unisci(i, j):
        ri, rj = rad(i), rad(j)
        if ri != rj:
            padre[ri] = rj

    for (ci, cj), dentro in griglia.items():
        vic = set(dentro)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                vic |= set(griglia.get((ci + di, cj + dj), ()))
        for i in dentro:
            for j in vic:
                if i < j and rete_osm.haversine_m(out[i]["lat"], out[i]["lon"],
                                                  out[j]["lat"], out[j]["lon"]) <= 40.0:
                    unisci(i, j)
    gruppi = defaultdict(list)
    for i in range(len(out)):
        gruppi[rad(i)].append(i)
    nodi = []
    for root, idx in gruppi.items():
        la = sum(out[i]["lat"] for i in idx) / len(idx)
        lo = sum(out[i]["lon"] for i in idx) / len(idx)
        am = sum(out[i]["partenze_ora_am"] for i in idx)
        pm = sum(out[i]["partenze_ora_pm"] for i in idx)
        gg = sum(out[i]["partenze_giorno_6_21"] for i in idx)
        linee = set()
        for i in idx:
            linee |= set(x for x in out[i]["linee"].split("|") if x)
        tipi = {out[i]["tipo"] for i in idx}
        nodi.append({
            "fermata": f"N{root}", "lat": la, "lon": lo,
            "partenze_ora_am": round(am, 2), "partenze_ora_pm": round(pm, 2),
            "partenze_giorno_6_21": gg, "n_linee": len(linee),
            "linee": "|".join(sorted(linee)),
            "tipo": "metro" if "metro" in tipi else ("ferrovia" if "ferrovia" in tipi else "bus_tram"),
            "n_stop_gtfs": len(idx),
        })
    out_nodi = nodi

    with (OUT / "tp_fermate.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["fermata", "lat", "lon", "partenze_ora_am", "partenze_ora_pm",
                    "partenze_giorno_6_21", "n_linee", "linee", "tipo", "n_stop_gtfs"])
        for o in out_nodi:
            w.writerow([o["fermata"], round(o["lat"], 6), round(o["lon"], 6),
                        o["partenze_ora_am"], o["partenze_ora_pm"], o["partenze_giorno_6_21"],
                        o["n_linee"], o["linee"], o["tipo"], o["n_stop_gtfs"]])

    am_tot = sum(o["partenze_ora_am"] for o in out_nodi)
    meta = {
        "giorno_tipico": data, "giorno_settimana": wd, "servizi_attivi": len(servizi),
        "corse_attive": len(trips), "corse_bus_tram": int(tot1),
        "corse_bus_tram_controllo": int(tot2),
        "controllo_uguale": bool(tot1 == tot2),
        "stop_gtfs_usati": len(out), "fermate_raggruppate": len(out_nodi),
        "fermate_bus_tram": sum(1 for o in out_nodi if o["tipo"] == "bus_tram"),
        "fermate_metro": sum(1 for o in out_nodi if o["tipo"] == "metro"),
        "partenze_ora_am_totali": round(am_tot, 1),
        "durata_s": round(time.time() - t0, 1),
        "fonte": "GTFS GTT 20261003, orario programmato; fermate entro 40 m raggruppate",
    }
    (OUT / "tp_fermate_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"Scritto {OUT/'tp_fermate.csv'}")


if __name__ == "__main__":
    main()
