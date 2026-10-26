# -*- coding: utf-8 -*-
"""
scripts/52_tp_corridoi.py - Pacchetto B (seconda parte): dai tratti ai corridoi.

Aggrega i passaggi bus/tram per tratto (tp_conteggi.npz, scritto da 51) ai
CORRIDOI di importanza_vie.json (la stessa suddivisione usata dal traffico:
l'assegnazione tratto -> corridoio e' identica a quella dello script 43).

Per ogni corridoio:
 - passaggi/ora in punta mattina (7-9) e sera (17-19), media pesata per lunghezza
   dei tratti del corridoio (come per il traffico), piu' il massimo;
 - passaggi giorno 6-21;
 - linee diverse;
 - lunghezza coperta (km di tratto con almeno un passaggio);
 - metro_vicina / ferrovia_vicina: fermata metro o linea/stazione ferroviaria
   entro 300 m dal corridoio.

Controlli (piano, sezione 4): (1) corse totali ricalcolate in un altro modo
(tolleranza 0); (3) tre fermate ricalcolate dal GTFS grezzo; (4) buon senso su
strade note e strade residenziali.

Input:  tp_conteggi.npz, tp_tratti.csv, segmenti.csv, importanza_vie.json,
        data/raw/gtt_gtfs_20261003_224530.zip, rete
Output: data/processed/tp_corridoi.json, parte 2 di docs/rapporti/RAPPORTO_TP_PER_STRADA.txt
"""

import csv
import io
import json
import math
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rete_osm  # noqa: E402

VICINANZA_M = 25.0
CELLA_LAT, CELLA_LON = 0.0009, 0.0013
SOGLIA_METRO_M = 300.0
GTFS = None


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
PROC = RADICE / "data" / "processed"
OUT_DIR = PROC / "traffico_c"
RETE_DIR = OUT_DIR / "rete"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_TP_PER_STRADA.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
GTFS = RADICE / "data" / "raw" / "gtt_gtfs_20261003_224530.zip"


def normalizza(nome):
    from importlib import import_module
    return import_module("24_importanza_vie").normalizza(nome)


def leggi_csv_zip(z, nome):
    with z.open(nome) as fh:
        return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig")))


def carica_corridoi():
    dati = json.loads((PROC / "importanza_vie.json").read_text(encoding="utf-8"))
    corridoi = dati["corridoi"]
    per_chiave = defaultdict(list)
    griglia = defaultdict(set)
    for i, c in enumerate(corridoi):
        per_chiave[c["chiave_normalizzata"]].append(i)
        for tratto in c["geometria"]:
            for k in range(len(tratto) - 1):
                (la0, lo0), (la1, lo1) = tratto[k], tratto[k + 1]
                passi = max(1, int(max(abs(la1 - la0) / CELLA_LAT, abs(lo1 - lo0) / CELLA_LON) * 4))
                for t in range(passi + 1):
                    la = la0 + (la1 - la0) * t / passi
                    lo = lo0 + (lo1 - lo0) * t / passi
                    griglia[(math.floor(la / CELLA_LAT), math.floor(lo / CELLA_LON))].add(i)
    return corridoi, per_chiave, griglia


def distanza_a_corridoio(corridoio, la, lo):
    best = 1e18
    for tratto in corridoio["geometria"]:
        for k in range(len(tratto) - 1):
            la1, lo1 = tratto[k]
            la2, lo2 = tratto[k + 1]
            mx = math.cos(math.radians(la)) * 111320.0
            my = 110540.0
            px, py = (lo - lo1) * mx, (la - la1) * my
            dx, dy = (lo2 - lo1) * mx, (la2 - la1) * my
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 <= 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
            d = math.hypot(px - t * dx, py - t * dy)
            if d < best:
                best = d
    return best


class GrigliaPunti:
    """Indice spaziale semplice per un elenco di punti (lat, lon, etichetta)."""

    def __init__(self, punti, cella=0.002):
        self.cella = cella
        self.g = defaultdict(list)
        self.punti = punti
        for i, (la, lo, _) in enumerate(punti):
            self.g[(math.floor(la / cella), math.floor(lo / cella))].append(i)

    def vicino_entro(self, la, lo, raggio_m):
        c = self.cella
        ci, cj = math.floor(la / c), math.floor(lo / c)
        n = max(1, int(raggio_m / (c * 110540.0)) + 1)
        for di in range(-n, n + 1):
            for dj in range(-n, n + 1):
                for i in self.g.get((ci + di, cj + dj), ()):
                    pla, plo, lab = self.punti[i]
                    if rete_osm.haversine_m(la, lo, pla, plo) <= raggio_m:
                        return lab
        return None


def punti_metro(z):
    """Fermate della metropolitana (route_type 1) dal GTFS: [(lat,lon,'linea')]."""
    routes = {r["route_id"]: r for r in leggi_csv_zip(z, "routes.txt")}
    metro_routes = {rid for rid, r in routes.items() if r["route_type"] == "1"}
    import pandas as pd
    with z.open("trips.txt") as fh:
        trips = pd.read_csv(fh, dtype=str, usecols=["trip_id", "route_id"])
    metro_trips = set(trips[trips["route_id"].isin(metro_routes)]["trip_id"])
    with z.open("stop_times.txt") as fh:
        st = pd.read_csv(fh, dtype=str, usecols=["trip_id", "stop_id"])
    metro_stops = set(st[st["trip_id"].isin(metro_trips)]["stop_id"])
    linea_nome = "|".join(sorted((routes[r].get("route_short_name") or r) for r in metro_routes))
    stops = leggi_csv_zip(z, "stops.txt")
    out = []
    for s in stops:
        if s["stop_id"] in metro_stops:
            out.append((float(s["stop_lat"]), float(s["stop_lon"]), linea_nome))
    return out


def punti_ferrovia(pbf):
    """Punti (lat,lon,'ferrovia') delle linee railway=rail/light_rail e delle
    stazioni, dal taglio OSM. Serve solo per la distanza (flag vicino/lontano)."""
    import osmium
    pts = []

    class H(osmium.SimpleHandler):
        def node(self, n):
            if (n.tags.get("railway") or "") in ("station", "halt"):
                pts.append((n.location.lat, n.location.lon, n.tags.get("name") or "ferrovia"))

        def way(self, w):
            if (w.tags.get("railway") or "") in ("rail", "light_rail", "narrow_gauge"):
                # le linee in galleria (passante ferroviario) non contano: non sono
                # "di fianco" alla strada in superficie
                if (w.tags.get("tunnel") or "").lower() in ("yes", "building_passage"):
                    return
                for nd in w.nodes:
                    try:
                        pts.append((nd.location.lat, nd.location.lon, w.tags.get("name") or "ferrovia"))
                    except Exception:
                        pass

    H().apply_file(str(pbf), locations=True)
    return pts


def indipendente_corse(z, data):
    """Ricalcola le corse bus/tram del giorno con un metodo diverso da 51
    (espande i servizi giorno per giorno invece di usare direttamente calendar)."""
    import datetime
    d = datetime.datetime.strptime(data, "%Y%m%d").date()
    # espansione: per ogni servizio, intervallo di date + eccezioni
    attivi = []
    for c in leggi_csv_zip(z, "calendar.txt"):
        wd = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][d.weekday()]
        if c[wd] != "1":
            continue
        ini = datetime.datetime.strptime(c["start_date"], "%Y%m%d").date()
        fin = datetime.datetime.strptime(c["end_date"], "%Y%m%d").date()
        if ini <= d <= fin:
            attivi.append(c["service_id"])
    attivi = set(attivi)
    for e in leggi_csv_zip(z, "calendar_dates.txt"):
        if e["date"] == data:
            if e["exception_type"] == "1":
                attivi.add(e["service_id"])
            else:
                attivi.discard(e["service_id"])
    routes = {r["route_id"]: r["route_type"] for r in leggi_csv_zip(z, "routes.txt")}
    n = 0
    for t in leggi_csv_zip(z, "trips.txt"):
        if t["service_id"] in attivi and routes.get(t["route_id"]) in ("0", "3"):
            n += 1
    return n, len(attivi)


def main():
    dati = np.load(OUT_DIR / "tp_conteggi.npz")
    giorno, am, pm = dati["giorno"], dati["am"], dati["pm"]

    rete = rete_osm.carica(RETE_DIR)
    meta = rete["meta"]
    edge_a, edge_len = rete["edge_a"], rete["edge_len"]
    n_edge = len(edge_a)

    corridoi, per_chiave, griglia = carica_corridoi()
    nome_edge = [normalizza(meta["nomi"][e]) if meta["nomi"][e] else "" for e in range(n_edge)]
    medi = np.array([rete_osm.punto_medio(rete, e) for e in range(n_edge)])

    # assegnazione tratto -> corridoio (identica allo script 43)
    assegna = [None] * n_edge
    for e in range(n_edge):
        la, lo = medi[e]
        chiave = nome_edge[e]
        scelto = None
        if chiave and chiave in per_chiave:
            cands = per_chiave[chiave]
            if len(cands) == 1:
                scelto = cands[0]
            else:
                best = (1e18, None)
                for i in cands:
                    d = distanza_a_corridoio(corridoi[i], la, lo)
                    if d < best[0]:
                        best = (d, i)
                if best[0] <= 200:
                    scelto = best[1]
        if scelto is None:
            ci, cj = math.floor(la / CELLA_LAT), math.floor(lo / CELLA_LON)
            vicini = set()
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    vicini |= griglia.get((ci + di, cj + dj), set())
            best = (1e18, None)
            for i in vicini:
                d = distanza_a_corridoio(corridoi[i], la, lo)
                if d < best[0]:
                    best = (d, i)
            if best[1] is not None and best[0] <= VICINANZA_M:
                scelto = best[1]
        assegna[e] = scelto

    # --- metropolitana e ferrovia ---
    z = zipfile.ZipFile(GTFS)
    metro = punti_metro(z)
    print(f"fermate metro (GTFS route_type 1): {len(metro)}")
    ferrovia = punti_ferrovia(RADICE / "data" / "otp" / "rete" / "torino_cintura.osm.pbf")
    print(f"punti ferroviari (OSM): {len(ferrovia)}")
    g_metro = GrigliaPunti(metro)
    g_ferro = GrigliaPunti(ferrovia)

    # --- aggregazione per corridoio ---
    per_cor = defaultdict(list)
    for e in range(n_edge):
        if assegna[e] is not None:
            per_cor[assegna[e]].append(e)

    out = []
    for i, c in enumerate(corridoi):
        elenco = per_cor.get(i, [])
        tot_lung = sum(float(edge_len[e]) for e in elenco)
        if not elenco or tot_lung <= 0:
            out.append({"nome": c["nome"], "chiave": c["chiave_normalizzata"],
                        "comune": c.get("comune"), "lunghezza_km": c["lunghezza_km"],
                        "n_tratti": len(elenco), "passaggi_giorno_6_21": 0.0,
                        "passaggi_giorno_6_21_max": 0.0, "passaggi_ora_punta_am": 0.0,
                        "passaggi_ora_punta_am_max": 0.0, "passaggi_ora_punta_pm": 0.0,
                        "passaggi_ora_punta_pm_max": 0.0, "passaggi_max_tratto_giorno": 0.0,
                        "linee": [], "metro_vicina": False, "ferrovia_vicina": False,
                        "stimato": False})
            continue
        lung = np.array([float(edge_len[e]) for e in elenco])
        g = giorno[elenco]
        a_ = am[elenco]
        p_ = pm[elenco]
        # media pesata per lunghezza (coerente col traffico) e massimo (tratto piu' servito)
        pg = float((g * lung).sum() / lung.sum())
        pa = float((a_ * lung).sum() / lung.sum()) / 2.0
        pp = float((p_ * lung).sum() / lung.sum()) / 2.0
        lung_coperta = float(lung[g > 0].sum() / 1000.0)
        # metro/ferrovia: vicinanza da QUALSIASI tratto del corridoio (non dal baricentro)
        m = None
        f_ = None
        for e in elenco:
            la_e, lo_e = medi[e]
            if m is None:
                m = g_metro.vicino_entro(la_e, lo_e, SOGLIA_METRO_M)
            if f_ is None:
                f_ = g_ferro.vicino_entro(la_e, lo_e, SOGLIA_METRO_M)
            if m is not None and f_ is not None:
                break
        out.append({"nome": c["nome"], "chiave": c["chiave_normalizzata"],
                    "comune": c.get("comune"), "lunghezza_km": c["lunghezza_km"],
                    "n_tratti": len(elenco), "km_tratti": round(tot_lung / 1000.0, 3),
                    "passaggi_giorno_6_21": round(pg, 1),
                    "passaggi_giorno_6_21_max": round(float(g.max()), 1),
                    "passaggi_ora_punta_am": round(pa, 2),
                    "passaggi_ora_punta_am_max": round(float(a_.max()) / 2.0, 2),
                    "passaggi_ora_punta_pm": round(pp, 2),
                    "passaggi_ora_punta_pm_max": round(float(p_.max()) / 2.0, 2),
                    "passaggi_max_tratto_giorno": round(float(g.max()), 1),
                    "km_coperti": round(lung_coperta, 3),
                    "linee": [],
                    "metro_vicina": bool(m), "metro_linea": m,
                    "ferrovia_vicina": bool(f_), "ferrovia_nome": f_,
                    "stimato": False})

    # linee per corridoio dal tp_tratti.csv (nomi uniti)
    linee_cor = defaultdict(set)
    with (OUT_DIR / "tp_tratti.csv").open(encoding="utf-8", newline="") as fh:
        for e, r in enumerate(csv.DictReader(fh, delimiter=";")):
            if r["linee"] and assegna[int(r["id_tratto"])] is not None:
                linee_cor[assegna[int(r["id_tratto"])]].update(r["linee"].split("|"))
    for i, o in enumerate(out):
        o["linee"] = sorted(x for x in linee_cor.get(i, set()) if x)
        o["n_linee"] = len(o["linee"])

    (RADICE / "data" / "processed" / "tp_corridoi.json").write_text(json.dumps({
        "stimato": False,
        "fonte": "GTFS GTT 20261003 (orario programmato), giorno feriale tipico 2026-10-14",
        "nota": ("Passaggi di bus e tram per corridoio. Passaggi/ora = corse nella fascia / 2 h. "
                 "Valori pesati per lunghezza dei tratti del corridoio. Solo corse bus/tram "
                 "agganciate alla rete stradale (93,1%). La metropolitana non passa sulle strade: "
                 "solo flag metro_vicina entro 300 m."),
        "giorno_tipico": "20261014",
        "corridoi": out,
    }, ensure_ascii=False), encoding="utf-8")

    # --- controlli ---
    righe = []
    a = righe.append
    a("")
    a("=" * 74)
    a("PARTE 2 - AGGREGAZIONE PER CORRIDOIO E CONTROLLI")
    a("=" * 74)
    # controllo 1: corse ricalcolate con un altro metodo
    n_ind, n_serv = indipendente_corse(z, "20261014")
    a(f"(1) corse bus/tram del giorno: 51 = 13.158 ; ricalcolo indipendente = {n_ind:,} "
      f"(servizi attivi {n_serv}) -> {'UGUALE (0)' if n_ind == 13158 else 'DIVERSO'}")
    # controllo 3: tre fermate a caso dal GTFS grezzo
    import pandas as pd
    with z.open("stop_times.txt") as fh:
        st = pd.read_csv(fh, dtype=str, usecols=["trip_id", "stop_id"])
    routes = {r["route_id"]: r for r in leggi_csv_zip(z, "routes.txt")}
    with z.open("trips.txt") as fh:
        tr = pd.read_csv(fh, dtype=str, usecols=["trip_id", "service_id", "route_id"])
    servizi = set()
    import datetime as _dt
    d = _dt.date(2026, 10, 14)
    for c in leggi_csv_zip(z, "calendar.txt"):
        wd = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][d.weekday()]
        if c[wd] == "1" and c["start_date"] <= "20261014" <= c["end_date"]:
            servizi.add(c["service_id"])
    for e2 in leggi_csv_zip(z, "calendar_dates.txt"):
        if e2["date"] == "20261014":
            (servizi.add if e2["exception_type"] == "1" else servizi.discard)(e2["service_id"])
    tr_ok = tr[tr["service_id"].isin(servizi)]
    tr_ok = tr_ok[tr_ok["route_id"].isin([r for r, x in routes.items() if x["route_type"] in ("0", "3")])]
    conteggio_fermate = st[st["trip_id"].isin(set(tr_ok["trip_id"]))].groupby("stop_id")["trip_id"].nunique()
    stops = {s["stop_id"]: s for s in leggi_csv_zip(z, "stops.txt")}
    campione = list(conteggio_fermate.sort_values(ascending=False).index[:3])
    a("(3) tre fermate piu' servite, corse del giorno ricalcolate dal GTFS grezzo (In [stop_times]):")
    for sid in campione:
        s = stops[sid]
        a(f"      {sid} {(s['stop_name'] or '')[:34]:34s} {int(conteggio_fermate[sid]):5d} corse/giorno")
    # controllo 4: strade note vs residenziali
    idx_nome = {o["nome"]: o for o in out}
    a("(4) buon senso (passaggi/ora in punta mattina, valore sul tratto piu' servito):")
    for nome in ["Corso Francia (Collegno)", "Corso Vittorio Emanuele II (Torino)",
                 "Via Nizza (Torino)", "Corso Giulio Cesare (Torino)"]:
        o = idx_nome.get(nome)
        if o:
            a(f"      {nome:38s} {o['passaggi_ora_punta_am_max']:6.1f} pass/h am (max)  "
              f"{o['passaggi_ora_punta_am']:5.1f} (media)  giorno max {o['passaggi_giorno_6_21_max']:6.0f}  "
              f"linee {o['n_linee']}")
        else:
            a(f"      {nome:38s} non trovato")
    torino = [o for o in out if (o.get("comune") == "Torino") and o.get("n_tratti")]
    via = sorted(torino, key=lambda o: -o["passaggi_giorno_6_21"])
    a("      corridoi di Torino con piu' passaggi diurni:")
    for o in via[:12]:
        a(f"      {o['passaggi_giorno_6_21']:6.0f} pass/g  {o['passaggi_ora_punta_am']:5.1f}/h am  "
          f"{o['nome'][:40]:40s} linee {o['n_linee']}")
    a(f"      corridoi di Torino con ZERO passaggi: "
      f"{sum(1 for o in torino if o['passaggi_giorno_6_21'] == 0)} su {len(torino)}")
    a(f"      corridoi con metro_vicina: {sum(1 for o in out if o['metro_vicina'])}; "
      f"ferrovia_vicina: {sum(1 for o in out if o['ferrovia_vicina'])}")
    # controllo 5: corridoi con passaggi ma nessuna fermata vicina
    a("(5) controllo fermate: non implementato come elenco separato (le fermate GTFS "
      "non sono usate per il conteggio, che nasce dalle forme). Elenco corridoi senza "
      "passaggi in Torino per confronto col traffico (pacchetto D).")
    base = RAPPORTO.read_text(encoding="utf-8") if RAPPORTO.is_file() else ""
    taglio = base.find("PARTE 2")
    if taglio > 0:
        base = base[:taglio].rstrip() + "\n"
    RAPPORTO.write_text(base + "\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))
    print("Scritto data/processed/tp_corridoi.json")


if __name__ == "__main__":
    main()
