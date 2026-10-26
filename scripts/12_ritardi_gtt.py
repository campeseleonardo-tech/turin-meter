#!/usr/bin/env python3
"""12_ritardi_gtt.py — corse GTT (trip_update) e avvisi: raccolta una tantum + analisi.

Sottocomandi:
  raccogli   scarica trip_update e alerts a intervalli regolari (una tantum) e salva
              le righe decodificate in data/processed/ritardi_<AAAAMMGG>.csv e
              data/processed/avvisi_<AAAAMMGG>.json. Solo libreria standard.
  raccogli-db legge gli stessi feed senza interruzione e salva osservazioni deduplicate
              nelle tabelle trip_update_gtt e avvisi_gtt di storico.sqlite.
  analizza   legge i file raccolti (+ i .pb alerts già in data/raw), li unisce con il
              GTFS statico (trips.txt) e produce: corse distinte attive e soppresse per
              linea e ora, match trip_id<->GTFS, sintesi degli avvisi.
              Con --db include il riepilogo recente SQLite. Scrive il rapporto e gli aggregati.

Cosa c'e' nel feed (verificato il 14/10/2026 su 324.660 righe di storico, 10-11/10): il
campo delay a livello di corsa NON c'e' mai; stop_time_update invece c'e' nel 99,9% delle
righe e per ogni fermata (seq) contiene in arr il ritardo in secondi (arr.delay, ~70% dei
casi) oppure l'orario previsto di arrivo (arr.time, epoch, ~30%). Una lettura al minuto
segue la corsa fermata per fermata. Con arr.time il ritardo si ricava dall'orario GTFS
della stessa corsa e stop_sequence (campione: mediana 0, p25/p75 -1,2/+1,2, p95 +5,1 min).
Questo strumento oggi conta corse attive/soppresse; il calcolo dei ritardi in minuti
non e' ancora implementato (serve al Risultato 4).

Ore locali Europe/Rome calcolate a mano (regola UE), come in comuni.py.
Solo raccogli-db scrive nelle sue due tabelle SQLite; nessun sottocomando modifica i grezzi.
"""
import argparse
import csv
import hashlib
import io
import json
import sqlite3
import sys
import time
import urllib.request
import zipfile
from calendar import monthrange
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def trova_radice():
    for c in [AQUI, *AQUI.parents]:
        if c.name.lower() == "gtt":
            return c
    return AQUI.parent


RAD = trova_radice()
ELAB = RAD / "data" / "processed"
RAW = RAD / "data" / "raw"
DOCS = RAD / "docs"
UA = "GTT-progetto-personale/0.1 (studio personale)"
URL_TU = "https://percorsieorari.gtt.to.it/das_gtfsrt/trip_update.aspx"
URL_AL = "https://percorsieorari.gtt.to.it/das_gtfsrt/alerts.aspx"

RELAZIONE = {0: "PROGRAMMATA", 1: "AGGIUNTA", 2: "NON_IN_PROGRAMMA", 3: "SOPPRESSA"}
CAUSA = {0: "IGNOTA", 1: "ALTRA", 2: "PROBLEMA_TECNICO", 3: "SCIOPERO",
         4: "MANIFESTAZIONE", 5: "INCIDENTE", 6: "FESTIVITA", 7: "METEO",
         8: "MANUTENZIONE", 9: "LAVORI", 10: "ATTIVITA_POLIZIA", 11: "EMERGENZA_MEDICA"}
EFFETTO = {0: "IGNOTO", 1: "SERVIZIO_NON_ATTIVO", 2: "SERVIZIO_RIDOTTO",
           3: "RITARDI_SIGNIFICATIVI", 4: "DEVIAZIONE", 5: "SERVIZIO_AGG",
           6: "SERVIZIO_MODIFICATO", 7: "ALTRO", 8: "FERMATA_SPOSTATA",
           9: "NESSUNA_EFFETTO", 10: "ACCESSIBILITA"}
SEVERITA = {0: "IGNOTA", 1: "INFO", 2: "AVVISO", 3: "GRAVE"}


# ---------- ora locale Europe/Rome (regola UE, niente zoneinfo su Windows) ----------

def ultima_domenica(anno, mese):
    ultimo = monthrange(anno, mese)[1]
    gw = date(anno, mese, ultimo).weekday()
    return ultimo - ((gw - 6) % 7)


def offset_roma(utc):
    y = utc.year
    ini = datetime(y, 3, ultima_domenica(y, 3), 1, tzinfo=timezone.utc)
    fin = datetime(y, 10, ultima_domenica(y, 10), 1, tzinfo=timezone.utc)
    return 2 if ini <= utc < fin else 1


def parsa_utc(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def a_roma(utc):
    return utc + timedelta(hours=offset_roma(utc))


def adesso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- protobuf GTFS-realtime, senza librerie esterne ----------

def _varint(b, i):
    r = sh = 0
    while True:
        x = b[i]
        i += 1
        r |= (x & 0x7F) << sh
        sh += 7
        if not x & 0x80:
            return r, i


def _campi(b):
    i, out = 0, []
    while i < len(b):
        k, i = _varint(b, i)
        fn, wt = k >> 3, k & 7
        if wt == 0:
            v, i = _varint(b, i)
        elif wt == 1:
            v = b[i:i + 8]
            i += 8
        elif wt == 2:
            n, i = _varint(b, i)
            v = b[i:i + n]
            i += n
        elif wt == 5:
            v = b[i:i + 4]
            i += 4
        else:
            raise ValueError(f"wire type {wt} (campo {fn})")
        out.append((fn, v))
    return out


def _txt(v):
    return v.decode("utf-8", "replace")


def _i32(v):
    if v >= 2**63:
        v -= 2**64
    if v < -2**31 or v >= 2**31:
        v &= 0xFFFFFFFF
        if v >= 2**31:
            v -= 2**32
    return v


def dec_trip(b):
    d = {}
    for fn, v in _campi(b):
        if fn == 1:
            d["trip_id"] = _txt(v)
        elif fn == 2:
            d["start_time"] = _txt(v)
        elif fn == 3:
            d["start_date"] = _txt(v)
        elif fn == 4:
            d["rel"] = v
        elif fn == 5:
            d["route_id"] = _txt(v)
        elif fn == 6:
            d["dir"] = v
    return d


def dec_evento(b):
    d = {}
    for fn, v in _campi(b):
        if fn == 1:
            d["delay"] = _i32(v)
        elif fn == 2:
            d["time"] = v
        elif fn == 3:
            d["uncertainty"] = v
    return d


def dec_stu(b):
    d = {}
    for fn, v in _campi(b):
        if fn == 1:
            d["seq"] = v
        elif fn == 2:
            d["arr"] = dec_evento(v)
        elif fn == 3:
            d["dep"] = dec_evento(v)
        elif fn == 4:
            d["stop_id"] = _txt(v)
        elif fn == 5:
            d["rel"] = v
    return d


def dec_trip_update(b):
    d = {}
    for fn, v in _campi(b):
        if fn == 1:
            d["trip"] = dec_trip(v)
        elif fn == 2:
            d.setdefault("stu", []).append(dec_stu(v))
        elif fn == 4:
            d["ts"] = v
        elif fn == 5:
            d["delay"] = _i32(v)
    return d


def _translated(b):
    frasi = []
    for fn, v in _campi(b):
        if fn == 1:
            for f2, v2 in _campi(v):
                if f2 == 1:
                    frasi.append(_txt(v2))
    return " ".join(frasi)


def dec_selector(b):
    s = {}
    for fn, v in _campi(b):
        if fn == 2:
            s["route_id"] = _txt(v)
        elif fn == 5:
            s["stop_id"] = _txt(v)
        elif fn == 4:
            s["trip"] = dec_trip(v)
    return s


def dec_periodo(b):
    d = {}
    for fn, v in _campi(b):
        if fn == 1:
            d["start"] = v
        elif fn == 2:
            d["end"] = v
    return d


def dec_alert(b):
    d = {}
    for fn, v in _campi(b):
        if fn == 1:
            d.setdefault("periodi", []).append(dec_periodo(v))
        elif fn == 5:
            d.setdefault("informato", []).append(dec_selector(v))
        elif fn == 6:
            d["causa"] = v
        elif fn == 7:
            d["effetto"] = v
        elif fn == 8:
            d["url"] = _translated(v)
        elif fn == 10:
            d["header"] = _translated(v)
        elif fn == 11:
            d["descrizione"] = _translated(v)
        elif fn == 14:
            d["severita"] = v
    return d


def dec_feed(b):
    """Decodifica un FeedMessage GTFS-realtime: elenca trip_update e alert con l'id entita'."""
    esiti = {"trip_update": [], "alert": []}
    for fn, v in _campi(b):
        if fn != 2:
            continue
        ent = dict(_campi(v))
        eid = _txt(ent[1]) if 1 in ent else ""
        if 3 in ent:
            tu = dec_trip_update(ent[3])
            tu["id"] = eid
            esiti["trip_update"].append(tu)
        if 5 in ent:
            al = dec_alert(ent[5])
            al["id"] = eid
            esiti["alert"].append(al)
    return esiti


def scarica(url):
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return resp.read()


# ---------- raccolta una tantum ----------

def aiuta_avviso_semplice(a):
    linee = sorted({s.get("route_id", "") for s in a.get("informato", []) if s.get("route_id")})
    fermate = sorted({s.get("stop_id", "") for s in a.get("informato", []) if s.get("stop_id")})
    return dict(id=a.get("id", ""),
                causa=CAUSA.get(a.get("causa"), a.get("causa")),
                effetto=EFFETTO.get(a.get("effetto"), a.get("effetto")),
                severita=SEVERITA.get(a.get("severita"), a.get("severita")),
                header=a.get("header", ""),
                descrizione=a.get("descrizione", ""),
                url=a.get("url", ""),
                linee=linee, fermate=fermate,
                periodi=a.get("periodi", []))


def raccogli(args):
    ELAB.mkdir(parents=True, exist_ok=True)
    ogni = max(10, args.ogni_secondi)
    durata = args.durata_ore
    inizio = time.time()
    unione_avvisi = {}
    ultima_scrittura = 0.0
    n_snap_tu = 0
    n_righe = 0
    print(f"Raccolta una tantum iniziata: {adesso()} (ogni {ogni} s, max {durata} h)", flush=True)
    try:
        while True:
            ora = adesso()
            # trip_update
            n_corse = 0
            try:
                tu = dec_feed(scarica(URL_TU))["trip_update"]
                giorno = a_roma(parsa_utc(ora)).strftime("%Y%m%d")
                path = ELAB / f"ritardi_{giorno}.csv"
                nuovo = not path.is_file()
                with open(path, "a", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    if nuovo:
                        w.writerow(["letto_utc", "trip_id", "start_date", "start_time",
                                    "rel", "con_delay", "con_stu"])
                    for t in tu:
                        tp = t.get("trip", {})
                        con_delay = 1 if t.get("delay") is not None else 0
                        con_stu = len(t.get("stu", []))
                        w.writerow([ora, tp.get("trip_id", ""), tp.get("start_date", ""),
                                    tp.get("start_time", ""), tp.get("rel", ""),
                                    con_delay, con_stu])
                    n_corse = len(tu)
                    n_righe += n_corse
                n_snap_tu += 1
                # diagnostica per la verifica diurna: il feed porta delay/stop_time_update?
                n_delay = sum(1 for t in tu if t.get("delay") is not None)
                n_stu = sum(len(t.get("stu", [])) for t in tu)
                if n_delay or n_stu:
                    print(f"{ora}  !!! trip_update con delay={n_delay} corsa/e, "
                          f"stop_time_update={n_stu} (al di sopra dello schema minimo)", flush=True)
                print(f"{ora}  trip_update: {n_corse} corse  (file {path.name})", flush=True)
            except Exception as e:
                print(f"{ora}  ERRORE trip_update: {e!r}", flush=True)
            # alerts: unione per id, salvata quando cambia
            try:
                al = dec_feed(scarica(URL_AL))["alert"]
                for a in al:
                    unione_avvisi[a.get("id", "")] = aiuta_avviso_semplice(a)
                if time.time() - ultima_scrittura > 900:
                    giorno = a_roma(parsa_utc(ora)).strftime("%Y%m%d")
                    salva_avvisi(giorno, unione_avvisi)
                    ultima_scrittura = time.time()
                    print(f"{ora}  alerts: {len(al)} (unione {len(unione_avvisi)})", flush=True)
            except Exception as e:
                print(f"{ora}  ERRORE alerts: {e!r}", flush=True)
            if args.una_volta:
                break
            if durata and (time.time() - inizio) >= durata * 3600:
                print(f"Durata massima raggiunta ({durata} h).", flush=True)
                break
            time.sleep(ogni)
    except KeyboardInterrupt:
        print("Raccolta fermata da tastiera.", flush=True)
    finally:
        giorno = a_roma(datetime.now(timezone.utc)).strftime("%Y%m%d")
        salva_avvisi(giorno, unione_avvisi)
        print(f"Fine: {n_snap_tu} snapshot trip_update, {n_righe} righe corse salvate.", flush=True)
    return 0


def salva_avvisi(giorno, unione):
    ELAB.mkdir(parents=True, exist_ok=True)
    (ELAB / f"avvisi_{giorno}.json").write_text(
        json.dumps({"aggiornato_utc": adesso(), "avvisi": list(unione.values())},
                   ensure_ascii=False, indent=1), encoding="utf-8")


# ---------- raccolta continua in SQLite ----------

def inizializza_tabelle_ritardi(con):
    con.executescript("""
    CREATE TABLE IF NOT EXISTS trip_update_gtt (
        letto_utc TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        trip_id TEXT,
        start_date TEXT,
        start_time TEXT,
        rel TEXT,
        delay INTEGER,
        stop_time_update INTEGER NOT NULL,
        payload TEXT NOT NULL,
        PRIMARY KEY (letto_utc, entity_id));
    CREATE INDEX IF NOT EXISTS ix_trip_update_gtt_tempo
        ON trip_update_gtt (letto_utc);
    CREATE TABLE IF NOT EXISTS avvisi_gtt (
        alert_id TEXT NOT NULL,
        fingerprint TEXT NOT NULL,
        first_seen_utc TEXT NOT NULL,
        last_seen_utc TEXT NOT NULL,
        payload TEXT NOT NULL,
        PRIMARY KEY (alert_id, fingerprint));
    CREATE INDEX IF NOT EXISTS ix_avvisi_gtt_ultimo
        ON avvisi_gtt (last_seen_utc);
    """)
    con.commit()


def salva_trip_update_sqlite(con, letto, trip_updates):
    righe = []
    n_delay = n_stu = 0
    for t in trip_updates:
        trip = t.get("trip", {})
        tid = trip.get("trip_id", "")
        start_date = trip.get("start_date", "")
        start_time = trip.get("start_time", "")
        entity_id = t.get("id") or f"{tid}|{start_date}|{start_time}"
        delay = t.get("delay")
        stu = len(t.get("stu", []))
        n_delay += delay is not None
        n_stu += stu
        payload = json.dumps(t, ensure_ascii=False, separators=(",", ":"))
        righe.append((letto, entity_id, tid, start_date, start_time,
                      str(trip.get("rel", "")), delay, stu, payload))
    with con:
        con.executemany("""
            INSERT OR IGNORE INTO trip_update_gtt
            (letto_utc, entity_id, trip_id, start_date, start_time, rel,
             delay, stop_time_update, payload)
            VALUES (?,?,?,?,?,?,?,?,?)
            """, righe)
    return len(righe), n_delay, n_stu


def salva_alert_sqlite(con, letto, alert):
    righe = []
    for a in alert:
        payload = json.dumps(a, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        alert_id = a.get("id") or fingerprint
        righe.append((alert_id, fingerprint, letto, letto, payload))
    with con:
        con.executemany("""
            INSERT INTO avvisi_gtt
            (alert_id, fingerprint, first_seen_utc, last_seen_utc, payload)
            VALUES (?,?,?,?,?)
            ON CONFLICT(alert_id, fingerprint) DO UPDATE
            SET last_seen_utc=excluded.last_seen_utc
            """, righe)
    return len(righe)


def registra_errore_sqlite(con, fonte, errore):
    testo = repr(errore)[:500]
    print(f"ERRORE {fonte}: {testo}", flush=True)
    try:
        with con:
            con.execute("INSERT INTO errori VALUES (?,?,?)", (adesso(), fonte, testo))
    except sqlite3.Error as e:
        print(f"ERRORE scrittura errori: {e!r}", flush=True)


def raccogli_sqlite(args):
    db = Path(args.db).expanduser().resolve()
    db.parent.mkdir(parents=True, exist_ok=True)
    ogni = max(10, args.ogni_secondi)
    con = sqlite3.connect(db, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    inizializza_tabelle_ritardi(con)
    print(f"Raccolta trip_update/alerts continua: {db} (ogni {ogni} s)", flush=True)
    try:
        while True:
            letto = adesso()
            try:
                trip_updates = dec_feed(scarica(URL_TU))["trip_update"]
                n, n_delay, n_stu = salva_trip_update_sqlite(con, letto, trip_updates)
                print(f"{letto}  trip_update: {n} corse, delay={n_delay}, "
                      f"stop_time_update={n_stu}", flush=True)
            except Exception as e:
                registra_errore_sqlite(con, "trip_update", e)
            try:
                alert = dec_feed(scarica(URL_AL))["alert"]
                n = salva_alert_sqlite(con, letto, alert)
                print(f"{letto}  alerts: {n} avvisi", flush=True)
            except Exception as e:
                registra_errore_sqlite(con, "alerts", e)
            time.sleep(ogni)
    except KeyboardInterrupt:
        print("Raccolta continua fermata.", flush=True)
    finally:
        con.close()
    return 0


# ---------- analisi ----------

def carica_gtfs():
    zips = sorted(RAW.glob("gtt_gtfs*.zip"))
    if not zips:
        return {}
    out = {}
    with zipfile.ZipFile(zips[-1]) as z:
        with z.open("trips.txt") as f:
            for row in csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")):
                out[row.get("trip_id", "")] = (row.get("route_id", ""),
                                               row.get("trip_headsign", ""))
    return out


def analizza(args):
    ROWS = []
    for p in sorted(ELAB.glob("ritardi_*.csv")):
        with open(p, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                ROWS.append((p.name, r))
    campione_db = None
    avvisi_db = {}
    if args.db:
        db = Path(args.db).expanduser().resolve()
        if db.is_file():
            con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=30)
            esiste = con.execute("""SELECT 1 FROM sqlite_master
                                     WHERE type='table' AND name='trip_update_gtt'""").fetchone()
            if esiste:
                if args.da_utc and args.a_utc:
                    da = parsa_utc(args.da_utc).isoformat(timespec="seconds")
                    a = parsa_utc(args.a_utc).isoformat(timespec="seconds")
                    if da >= a:
                        raise ValueError("--da-utc deve precedere --a-utc")
                    where = "letto_utc >= ? AND letto_utc <= ?"
                    parametri = (da, a)
                    etichetta_campione = f"UTC {da} -> {a}"
                elif args.da_utc or args.a_utc:
                    raise ValueError("specificare insieme --da-utc e --a-utc")
                else:
                    a = datetime.now(timezone.utc).isoformat(timespec="seconds")
                    da = (datetime.now(timezone.utc) - timedelta(hours=args.ultime_ore)).isoformat(timespec="seconds")
                    where = "letto_utc >= ? AND letto_utc <= ?"
                    parametri = (da, a)
                    etichetta_campione = f"ultime {args.ultime_ore} ore UTC"
                campione_db = con.execute("""
                    SELECT COUNT(*), MIN(letto_utc), MAX(letto_utc),
                           COUNT(DISTINCT letto_utc),
                           SUM(CASE WHEN delay IS NOT NULL THEN 1 ELSE 0 END),
                           SUM(CASE WHEN stop_time_update > 0 THEN 1 ELSE 0 END),
                           COUNT(DISTINCT trip_id)
                    FROM trip_update_gtt WHERE """ + where, parametri).fetchone()
                # Per ogni id di avviso conserva nel rapporto la versione piu' recente.
                visti_alert = set()
                for (payload,) in con.execute("""
                    SELECT payload FROM avvisi_gtt WHERE last_seen_utc >= ? AND last_seen_utc <= ?
                    ORDER BY last_seen_utc DESC
                    """, parametri):
                    try:
                        a = json.loads(payload)
                        aid = a.get("id", "")
                        if aid and aid not in visti_alert:
                            avvisi_db[aid] = a
                            visti_alert.add(aid)
                    except (TypeError, ValueError):
                        continue
            con.close()
    righe = [r for _, r in ROWS]
    out = []
    def scrivi(m=""):
        out.append(str(m))

    scrivi("=" * 70)
    scrivi("CORSE GTT (trip_update) E AVVISI — analisi")
    scrivi("=" * 70)
    scrivi(f"File raccolti: {sorted({p for p, _ in ROWS})}")

    # --- dedupe e conteggi base ---
    visti = {}
    for r in righe:
        k = (r["letto_utc"], r["trip_id"], r["start_date"], r["start_time"], r["rel"])
        visti.setdefault(k, r)
    unici = list(visti.values())
    if not unici:
        scrivi("Nessun dato raccolto (nessun file ritardi_*.csv).")
        return scrivi_esito(out, args, {})
    n_righe = len(unici)
    tu_ts = sorted(parsa_utc(r["letto_utc"]) for r in unici)
    scrivi(f"Righe (lette_utc,trip,data,ora,rel unici): {n_righe}")
    scrivi(f"Intervallo UTC: {tu_ts[0].isoformat()} -> {tu_ts[-1].isoformat()}")

    corse = {}   # (start_date, trip_id, start_time) -> rel osservata (se piu' volte, ultima)
    for r in unici:
        key = (r["start_date"], r["trip_id"], r["start_time"])
        corse[key] = r["rel"]
    scrivi(f"Corse distinte (start_date, trip_id, start_time): {len(corse)}")
    # verifica diurna: il feed porta delay/stop_time_update?
    n_delay = sum(1 for r in unici if str(r.get("con_delay", "0")) == "1")
    n_stu = sum(1 for r in unici if int(str(r.get("con_stu", "0")) or "0") > 0)
    if n_delay or n_stu:
        scrivi(f"  !! {n_delay} righe con campo delay, {n_stu} con stop_time_update: "
               f"il feed porta dati oltre lo schema minimo osservato di notte")
    scrivi(f"  Campioni con delay presente: {n_delay} righe · "
           f"con stop_time_update: {n_stu} righe")

    gtfs = carica_gtfs()
    matched = sum(1 for (_, tid, _) in corse if tid in gtfs)
    scrivi(f"Match trip_id <-> GTFS (trips.txt): {matched}/{len(corse)} "
           f"({matched / len(corse):.1%})" + ("  -> GTFS: " + str(sorted(RAW.glob('gtt_gtfs*.zip'))[-1].name) if sorted(RAW.glob('gtt_gtfs*.zip')) else ""))

    # per giorno servizio
    per_giorno = defaultdict(lambda: Counter())   # giorno -> rel -> corse
    for (g, tid, ts) in corse:
        per_giorno[g][corse[(g, tid, ts)]] += 1
    scrivi("\n-- Corse distinte per giorno di servizio (start_date) --")
    for g in sorted(per_giorno):
        c = per_giorno[g]
        tot = sum(c.values())
        supp = c.get("3", 0)
        prog = c.get("0", 0)
        scrivi(f"  {g}: {tot} corse totali, {prog} PROGRAMMATE, {supp} SOPPRESSE, "
               f"altre {tot - prog - supp}")

    # per (linea, ora, rel)
    per_lo = defaultdict(lambda: Counter())   # (linea, ora) -> rel -> corse distinte
    for r in unici:
        loc = a_roma(parsa_utc(r["letto_utc"]))
        linea = gtfs.get(r["trip_id"], ("(non in GTFS)", ""))[0]
        k = (linea, loc.hour)
        per_lo[k][r["rel"]] += 1
    # snapshot per (giorno, ora)
    snap_ho = defaultdict(lambda: set())
    for r in unici:
        loc = a_roma(parsa_utc(r["letto_utc"]))
        snap_ho[(loc.strftime("%Y%m%d"), loc.hour)].add(r["letto_utc"])

    scrivi("\n-- Corse distinte per linea e ora (snapshot = letture distinte nel periodo) --")
    top = sorted(per_lo.items(), key=lambda kv: -sum(kv[1].values()))[:20]
    for (linea, h), c in top:
        tot = sum(c.values())
        n_snap = sum(len(v) for (d, hh), v in snap_ho.items() if hh == h)
        rel_s = c.get("3", 0)
        scrivi(f"  {linea:>6} ora {h:02d}:00  corse {tot:5d}  (suppresse {rel_s:3d})  "
               f"snapshot {n_snap:3d}")
    if not top:
        scrivi("  (nessuna corsa raccolta)")

    # distribuzione per rel
    rel_c = Counter(corse.values())
    scrivi("\n-- Distribuzione per schedule_relationship --")
    for k in sorted(rel_c, key=lambda x: (x != "0", str(x))):
        scrivi(f"  {RELAZIONE.get(int(k), k)} (rel={k}): {rel_c[k]} corse distinte")

    # avvisi: raw .pb in data/raw + file raccolti
    avv = {}
    for p in sorted(RAW.glob("gtt_alerts_*.pb")):
        try:
            for a in dec_feed(p.read_bytes())["alert"]:
                avv[a.get("id", "")] = a
        except Exception as e:
            scrivi(f"  (avviso {p.name} non decodificabile: {e!r})")
    for p in sorted(ELAB.glob("avvisi_*.json")):
        try:
            for a in json.loads(p.read_text(encoding="utf-8")).get("avvisi", []):
                avv[a.get("id", "")] = a
        except Exception:
            pass
    avv.update(avvisi_db)
    linee = Counter()
    fermate = set()
    scrivi("\n-- Avvisi GTT (decodificati) --")
    if not avv:
        scrivi("  (nessun avviso)")
    else:
        scrivi(f"  Avvisi distinti (unione per id): {len(avv)}")
        c_c = Counter(CAUSA.get(a.get("causa"), a.get("causa")) for a in avv.values())
        e_c = Counter(EFFETTO.get(a.get("effetto"), a.get("effetto")) for a in avv.values())
        s_c = Counter(SEVERITA.get(a.get("severita"), a.get("severita")) for a in avv.values())
        for a in avv.values():
            for s in a.get("informato", []):
                if s.get("route_id"):
                    linee[s["route_id"]] += 1
                if s.get("stop_id"):
                    fermate.add(s["stop_id"])
        scrivi(f"  Per causa: {dict(c_c.most_common())}")
        scrivi(f"  Per effetto: {dict(e_c.most_common())}")
        scrivi(f"  Per severita': {dict(s_c.most_common())}")
        scrivi(f"  Linee toccate: {len(linee)}  (top: {linee.most_common(10)})")
        scrivi(f"  Fermate toccate (distinte): {len(fermate)}")
        esempi = [a for a in avv.values() if a.get("header") or a.get("descrizione")][:5]
        for a in esempi:
            scrivi(f"  [esempio] {a.get('header','')[:80]} | {a.get('descrizione','')[:120]}")

    if campione_db is not None:
        tot_db, da_db, a_db, snapshot_db, n_delay_db, n_stu_db, trips_db = campione_db
        scrivi(f"\n-- Raccolta continua SQLite ({etichetta_campione}) --")
        scrivi(f"  Intervallo UTC: {da_db or 'nessun dato'} -> {a_db or 'nessun dato'}")
        scrivi(f"  Osservazioni: {tot_db}; snapshot: {snapshot_db}; corse distinte: {trips_db}")
        scrivi(f"  Campioni con delay presente: {n_delay_db or 0} righe · "
               f"con stop_time_update: {n_stu_db or 0} righe")

    scrivi("\n  NOTA: delay e stop_time_update sono verificati solo nei campioni elencati sopra;")
    scrivi("  la loro assenza nel periodo osservato non prova che il feed non li pubblichi mai.")
    scrivi("  Il conteggio misura le corse che il feed comunica, non l'intera offerta.")

    testo = "\n".join(out) + "\n"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(testo)
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "rapporti").mkdir(parents=True, exist_ok=True)
    (DOCS / "rapporti" / "RAPPORTO_RITARDI_GTT.txt").write_text(testo, encoding="utf-8")
    ris = dict(righe=n_righe, corse_distinte=len(corse),
               match_gtfs=[matched, len(corse)],
               per_giorno={g: dict(c) for g, c in per_giorno.items()},
               avvisi_distinti=len(avv), linee_toccate=len(linee),
               fermate_toccate=len(fermate))
    ELAB.mkdir(parents=True, exist_ok=True)
    (ELAB / "ritardi_analisi.json").write_text(
        json.dumps(ris, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"Rapporto: {DOCS / 'rapporti' / 'RAPPORTO_RITARDI_GTT.txt'}")
    print(f"Aggregati: {ELAB / 'ritardi_analisi.json'}")
    return 0


def scrivi_esito(out, args, ris):
    testo = "\n".join(out) + "\n"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(testo)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Corse GTT (trip_update) e avvisi")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("raccogli", help="raccolta una tantum di trip_update e alerts")
    p1.add_argument("--ogni-secondi", type=int, default=60)
    p1.add_argument("--durata-ore", type=float, default=20.0,
                    help="durata massima della raccolta (default 20)")
    p1.add_argument("--una-volta", action="store_true", help="un solo ciclo e poi esce")
    p3 = sub.add_parser("raccogli-db", help="raccolta continua di trip_update e alerts in SQLite")
    p3.add_argument("--db", default=str(RAD / "data" / "storico.sqlite"))
    p3.add_argument("--ogni-secondi", type=int, default=60)
    p2 = sub.add_parser("analizza", help="analizza i file raccolti e gli avvisi")
    p2.add_argument("--db", help="database con la raccolta continua (facoltativo)")
    p2.add_argument("--ultime-ore", type=int, default=24,
                    help="finestra di riepilogo della raccolta SQLite (default 24)")
    p2.add_argument("--da-utc", help="inizio inclusivo del campione ISO-8601 UTC")
    p2.add_argument("--a-utc", help="fine inclusiva del campione ISO-8601 UTC")
    args = ap.parse_args()
    if args.cmd == "raccogli":
        return raccogli(args)
    if args.cmd == "raccogli-db":
        return raccogli_sqlite(args)
    return analizza(args)


if __name__ == "__main__":
    sys.exit(main())
