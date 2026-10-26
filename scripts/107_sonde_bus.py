# -*- coding: utf-8 -*-
"""
scripts/107_sonde_bus.py - i bus come sonde del traffico: k(zona, ora) per la stima aperta dell'auto (F3, regole §6.1 del piano).

k(zona, h) = velocita' mediana dei BUS IN MOVIMENTO all'ora h / velocita' mediana alle 5-6 del mattino, nella zona IMQ.
  - dati: le posizioni GPS dei mezzi (tabella mezzi_gtt dello storico), giorni feriali del PERIODO «gps» (comuni.PERIODO), ora locale;
  - una coppia = due posizioni consecutive dello stesso mezzo e della stessa linea, a 30-120 secondi l'una dall'altra;
    velocita' = distanza in linea d'aria / secondi;
  - si escludono le coppie con una posizione a meno di 60 m da una fermata della linea (il bus li' si ferma per servizio, non per il traffico),
    le coppie quasi ferme (sotto 2 km/h: capolinea, rimessa) e le velocita' impossibili (oltre 90 km/h: salto del GPS);
  - solo bus (route_type 3 del GTFS), non tram ne' metro;
  - una cella (zona, ora) vale solo con almeno 300 coppie, e la zona deve avere 300 coppie anche alle 5-6; altrimenti si usa il k di tutta la citta'
    a quell'ora; dove neanche la citta' ha 300 coppie (ore della notte) k = 1 (strada libera);
  - k sta fra 0,3 e 1.

Come si lancia
--------------
  python scripts\\107_sonde_bus.py            (tutto il PERIODO)
  python scripts\\107_sonde_bus.py --prova    (due giorni, scrive in una cartella temporanea)

Uscite: data/processed/sonde_bus.json, docs/rapporti/RAPPORTO_SONDE_BUS.txt
Sola lettura sullo storico.
"""
import argparse
import csv
import datetime as dt
import io
import json
import sqlite3
import sys
import tempfile
import time
import zipfile
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
PROC = RADICE / "data" / "processed"
DB = RADICE / "data" / "storico_backup.sqlite"
GTFS = RADICE / "data" / "raw" / "gtt_gtfs_20261003_224530.zip"
ZONE_GEO = PROC / "imq_zone_geo.json"
OUT_JSON = PROC / "sonde_bus.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_SONDE_BUS.txt"

DT_MIN_S, DT_MAX_S = 30, 120
DIST_FERMATA_M = 60.0
VEL_MIN_KMH, VEL_MAX_KMH = 2.0, 90.0
MIN_COPPIE = 300
ORE_BASE = (5, 6)
K_MIN, K_MAX = 0.3, 1.0
FUSO = ZoneInfo("Europe/Rome")


def proietta(lat, lon, lat0=45.07):
    return np.column_stack([np.asarray(lon) * np.cos(np.radians(lat0)) * 111320.0, np.asarray(lat) * 110540.0])


def fermate_per_linea():
    """route_id dei bus -> coordinate (lat, lon) delle fermate servite (da trips.txt e stop_times.txt)."""
    with zipfile.ZipFile(GTFS) as z:
        bus = set()
        with z.open("routes.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                if r["route_type"] == "3":
                    bus.add(r["route_id"])
        corsa_linea = {}
        with z.open("trips.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                if r["route_id"] in bus:
                    corsa_linea[r["trip_id"]] = r["route_id"]
        coppie = set()
        with z.open("stop_times.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                linea = corsa_linea.get(r["trip_id"])
                if linea:
                    coppie.add((linea, r["stop_id"]))
        pos = {}
        with z.open("stops.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                try:
                    pos[r["stop_id"]] = (float(r["stop_lat"]), float(r["stop_lon"]))
                except (ValueError, KeyError):
                    continue
    per = defaultdict(list)
    for linea, s in coppie:
        if s in pos:
            per[linea].append(pos[s])
    return bus, {k: np.array(v) for k, v in per.items()}


def zone_poligoni():
    """STRtree dei poligoni delle zone IMQ (coordinate lat, lon come nello script 41) e i loro codici."""
    from shapely.geometry import MultiPolygon, Polygon
    from shapely.strtree import STRtree
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

    poligoni, codici = [], []
    for zg in json.loads(ZONE_GEO.read_text(encoding="utf-8")):
        polys = []
        for an in anelli_di(zg["g"]):
            if len(an) >= 4:
                p = Polygon(an)
                if not p.is_valid:
                    p = p.buffer(0)
                if p.area > 0:
                    polys.append(p)
        if polys:
            poligoni.append(MultiPolygon(polys) if len(polys) > 1 else polys[0])
            codici.append(zg["cod"])
    return STRtree(poligoni), poligoni, codici


def zona_dei_punti(albero, poligoni, codici, lat, lon):
    """Codice della zona di ogni punto (None se fuori da ogni poligono)."""
    import shapely
    punti = shapely.points(lat, lon)
    ip, ig = albero.query(punti, predicate="within")
    out = np.full(len(lat), None, dtype=object)
    for i, g in zip(ip, ig):
        if out[i] is None:
            out[i] = codici[g]
    return out


def leggi_posizioni(giorni_locali):
    """DataFrame (veicolo, linea, t [s epoca], lat, lon) delle posizioni dei giorni locali chiesti, senza ripetizioni."""
    primo = dt.datetime.fromisoformat(min(giorni_locali) + "T00:00:00").replace(tzinfo=FUSO).astimezone(dt.timezone.utc)
    ultimo = (dt.datetime.fromisoformat(max(giorni_locali) + "T00:00:00") + dt.timedelta(days=1)).replace(tzinfo=FUSO).astimezone(dt.timezone.utc)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    df = pd.read_sql_query(
        "SELECT veicolo, linea, ts_feed AS t, lat, lng AS lon FROM mezzi_gtt WHERE letto_utc >= ? AND letto_utc < ? AND ts_feed IS NOT NULL",
        con, params=(primo.isoformat(timespec="seconds"), ultimo.isoformat(timespec="seconds")))
    con.close()
    df = df.drop_duplicates(["veicolo", "t"]).sort_values(["veicolo", "t"], kind="stable").reset_index(drop=True)
    return df


def coppie_di_velocita(df, bus, fermate, log):
    """Per ogni coppia valida: ora locale, giorno, velocita' (km/h) e punto medio."""
    from scipy.spatial import cKDTree
    df = df[df["linea"].isin(bus)].reset_index(drop=True)
    stesso = (df["veicolo"].values[1:] == df["veicolo"].values[:-1]) & (df["linea"].values[1:] == df["linea"].values[:-1])
    dt_s = df["t"].values[1:] - df["t"].values[:-1]
    ok = stesso & (dt_s >= DT_MIN_S) & (dt_s <= DT_MAX_S)
    i = np.nonzero(ok)[0]
    a, b = df.iloc[i].reset_index(drop=True), df.iloc[i + 1].reset_index(drop=True)
    xa, xb = proietta(a["lat"], a["lon"]), proietta(b["lat"], b["lon"])
    dist = np.hypot(*(xb - xa).T)
    vel = dist / dt_s[i] * 3.6
    lontano = np.ones(len(a), dtype=bool)
    for linea, idx in a.groupby("linea").indices.items():
        f = fermate.get(linea)
        if f is None or not len(f):
            continue
        albero = cKDTree(proietta(f[:, 0], f[:, 1]))
        da, _ = albero.query(xa[idx])
        db, _ = albero.query(xb[idx])
        lontano[idx] = (da >= DIST_FERMATA_M) & (db >= DIST_FERMATA_M)
    valido = lontano & (vel >= VEL_MIN_KMH) & (vel <= VEL_MAX_KMH)
    log(f"  coppie di posizioni a 30-120 s: {len(a):,}; lontane dalle fermate: {int(lontano.sum()):,}; in movimento e plausibili: {int(valido.sum()):,}")
    a, b, vel = a[valido].reset_index(drop=True), b[valido].reset_index(drop=True), vel[valido]
    istante = pd.to_datetime(a["t"], unit="s", utc=True).dt.tz_convert(FUSO)
    return pd.DataFrame({"giorno": istante.dt.strftime("%Y-%m-%d"), "ora": istante.dt.hour, "dow": istante.dt.dayofweek, "v": vel,
                         "lat": (a["lat"] + b["lat"]) / 2, "lon": (a["lon"] + b["lon"]) / 2}), {"coppie_30_120": int(len(lontano)), "lontane": int(lontano.sum())}


def calcola_k(c, zone):
    """k per citta' e per zona. c: DataFrame delle coppie con la colonna zona."""
    def mediane(sub):
        g = sub.groupby("ora")["v"]
        return {int(h): (float(m), int(n)) for h, m, n in zip(g.median().index, g.median().values, g.size().values)}

    def k_di(med, base):
        out = {}
        for h in range(24):
            v, n = med.get(h, (None, 0))
            out[h] = (None if (base is None or n < MIN_COPPIE) else min(K_MAX, max(K_MIN, v / base)), n)
        return out

    citta_med = mediane(c)
    base_c = _base(citta_med)
    citta = k_di(citta_med, base_c)
    k_citta = {h: (citta[h][0] if citta[h][0] is not None else K_MAX) for h in range(24)}
    zone_out = {}
    for cod, sub in c.dropna(subset=["zona"]).groupby("zona"):
        med = mediane(sub)
        base = _base(med)
        if base is None:
            continue
        kz = k_di(med, base)
        validi = {h: {"k": round(kz[h][0], 3), "n": kz[h][1]} for h in range(24) if kz[h][0] is not None}
        if validi:
            zone_out[cod] = {"base_kmh": round(base, 2), "ore": validi}
    return base_c, citta, k_citta, zone_out


def _base(med):
    """Mediana (pesata dalle coppie) delle ore 5-6; None se in tutto sono meno di MIN_COPPIE."""
    n = sum(med.get(h, (0, 0))[1] for h in ORE_BASE)
    if n < MIN_COPPIE:
        return None
    return float(sum(med[h][0] * med[h][1] for h in ORE_BASE if h in med) / n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true", help="solo due giorni feriali; uscite in una cartella temporanea")
    args = ap.parse_args()
    t0 = time.time()
    comuni.richiedi_fonte(ZONE_GEO)
    c = comuni.Controlli()

    def log(m):
        print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

    da, a = comuni.PERIODO["gps"]
    giorni = [str(g.date()) for g in pd.date_range(da, a) if g.dayofweek < 5]
    if args.prova:
        giorni = giorni[:2]
        cartella = Path(tempfile.mkdtemp(prefix="sonde_bus_prova_"))
        out_json, rapporto = cartella / OUT_JSON.name, cartella / RAPPORTO.name
        log(f"PROVA: giorni {giorni}; uscite in {cartella}")
    else:
        out_json, rapporto = OUT_JSON, RAPPORTO
    log(f"giorni feriali del periodo GPS ({da} - {a}): {len(giorni)}")
    comuni.richiedi_fonte(DB)
    log("posizioni dei mezzi dallo storico ...")
    df = leggi_posizioni(giorni)
    log(f"  posizioni: {len(df):,}")
    bus, fermate = fermate_per_linea()
    log(f"linee bus nel GTFS: {len(bus)}; con fermate: {len(fermate)}")
    cop, conteggi = coppie_di_velocita(df, bus, fermate, log)
    cop = cop[cop["giorno"].isin(giorni)].reset_index(drop=True)
    albero, poligoni, codici = zone_poligoni()
    cop["zona"] = zona_dei_punti(albero, poligoni, codici, cop["lat"].values, cop["lon"].values)
    log(f"  coppie nei giorni feriali: {len(cop):,}; dentro una zona IMQ: {int(cop['zona'].notna().sum()):,}")

    base_c, citta, k_citta, zone = calcola_k(cop, codici)
    c("la citta' ha le coppie per la base delle 5-6", base_c is not None, bloccante=True, dettaglio=f"velocita' di base {base_c or 0:.1f} km/h")
    c("k di punta (8) minore di k delle 5-6 (che e' 1)", k_citta[8] < 0.999, dettaglio=f"k(8) = {k_citta[8]:.2f}")
    c("k stretto fra 0,3 e 1", all(K_MIN <= v <= K_MAX for v in k_citta.values()), bloccante=True)
    n_zone_ok = len(zone)
    log(f"zone con almeno una cella valida: {n_zone_ok} su {len(codici)}")
    celle = sum(len(z["ore"]) for z in zone.values())
    out = {"stimato": True, "prova": bool(args.prova),
           "parametri": {"periodo": {"da": da, "a": a}, "giorni_feriali": giorni, "coppie_secondi": [DT_MIN_S, DT_MAX_S], "distanza_fermata_m": DIST_FERMATA_M,
                         "velocita_valida_kmh": [VEL_MIN_KMH, VEL_MAX_KMH], "minimo_coppie_per_cella": MIN_COPPIE, "ore_base": list(ORE_BASE), "k_limiti": [K_MIN, K_MAX],
                         "solo": "bus (route_type 3 del GTFS)"},
           "coppie_usate": int(len(cop)), "base_citta_kmh": round(base_c, 2),
           "citta": {str(h): {"k": round(k_citta[h], 3), "n": citta[h][1], "misurato": citta[h][0] is not None} for h in range(24)},
           "zone": zone, "controlli": list(c.righe)}
    out_json.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    r = ["RAPPORTO SONDE BUS: k(zona, ora) per la stima aperta dell'auto" + (" - PROVA" if args.prova else ""),
         f"generato: {dt.datetime.now().isoformat(timespec='seconds')}", "",
         f"Periodo GPS {da} - {a}, giorni feriali: {len(giorni)}. Coppie di posizioni usate: {len(cop):,}. Velocita' di base (5-6 del mattino, tutta la citta'): {base_c:.1f} km/h.",
         f"Regole: coppie a {DT_MIN_S}-{DT_MAX_S} s, lontane {DIST_FERMATA_M:g} m dalle fermate della linea, fra {VEL_MIN_KMH:g} e {VEL_MAX_KMH:g} km/h, solo bus; "
         f"cella valida con almeno {MIN_COPPIE} coppie; k fra {K_MIN} e {K_MAX}.", "",
         "K DI TUTTA LA CITTA' PER ORA (n = coppie; «no» = poche coppie, k = 1)", "  ora | k | coppie | misurato"]
    for h in range(24):
        r.append(f"  {h:02d} | {k_citta[h]:.2f} | {citta[h][1]:,} | {'si' if citta[h][0] is not None else 'no'}")
    r += ["", f"Zone con celle proprie: {n_zone_ok} su {len(codici)}; celle (zona, ora) valide: {celle}.", "", "Controlli:"] + [f"  {x}" for x in c.righe]
    rapporto.write_text("\n".join(r) + "\n", encoding="utf-8")
    log(f"scritto {out_json.name} e {rapporto.name} ({time.time() - t0:.0f} s)")
    print("\n".join(r))
    if c.avvisi():
        print("AVVISI presenti: leggi le righe sopra")


if __name__ == "__main__":
    main()
