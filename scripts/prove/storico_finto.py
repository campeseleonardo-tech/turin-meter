#!/usr/bin/env python3
"""
storico_finto.py  -  uno storico SQLite e un GTFS FINTI, piccoli, per provare gli script 97, 27, 70, 26 e 71 nel cloud (dove non c'e' data/).

I dati sono inventati (numeri casuali con seme fisso): servono solo a far girare il codice e a confrontare le due strade
(storico contro riassunti), non hanno nessun significato per Torino.

Uso (da un'altra prova):  import storico_finto; finto = storico_finto.crea(cartella)
Ritorna: {"db": percorso dello storico, "gtfs": percorso dello zip, "giorno_controllo": giorno per il controllo GPS dello script 70}.

Cosa c'e'
---------
GTFS: 4 linee (tram 4, bus 15, 68, 9), 2 versi, corse ogni 6 minuti dalle 6:30 alle 9:30 (ogni 12 nel sabato), 8 fermate, 2 minuti fra una fermata e l'altra.
Giorni: feriali 12-16/10/2026, sabato 17/10 (completo) e sabato 24/10 (con pochissimo GPS: da escludere).
Tabelle: trip_update_gtt (feed dei ritardi), mezzi_gtt (GPS), sensori_5t, flussi_5t, accuratezza_5t, parcheggi_5t, occupazione_pk.
"""
import csv
import io
import json
import random
import sqlite3
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

GIORNI = ["20261012", "20261013", "20261014", "20261015", "20261016", "20261017", "20261024"]
POCO_GPS = {"20261024"}
GIORNI_5T = [date(2026, 10, 12) + timedelta(days=i) for i in range(6)]     # 12-17 ottobre, giorni interi
OFFSET = 2                                                                  # ora legale (fine il 25/10/2026)
LINEE = [("R4", "4", 0, 7.64), ("R15", "15", 3, 7.65), ("R68", "68", 3, 7.66), ("R9", "9", 3, 7.67)]
N_FERMATE = 8


def _base(giorno):
    d = datetime.strptime(giorno, "%Y%m%d")
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc) - timedelta(hours=OFFSET)


def _iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def crea_gtfs(percorso):
    routes = [["route_id", "route_short_name", "route_type"]] + [[r, n, t] for r, n, t, _ in LINEE]
    stops = [["stop_id", "stop_name", "stop_lat", "stop_lon"]]
    trips = [["route_id", "service_id", "trip_id", "direction_id"]]
    times = [["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"]]
    corse = []     # (trip_id, route_id, direzione, secondi di partenza, [stop_id])
    for r, nome, _t, lon in LINEE:
        ids = [f"{r}_S{i}" for i in range(N_FERMATE)]
        for i, sid in enumerate(ids):
            stops.append([sid, f"Fermata {nome}-{i}", round(45.04 + 0.004 * i, 6), lon])
        for d in (0, 1):
            ordine = ids if d == 0 else ids[::-1]
            for k in range(30):
                partenza = 6 * 3600 + 1800 + k * 360 + d * 90
                tid = f"{r}_{d}_{k:02d}"
                trips.append([r, "FERIALE", tid, d])
                corse.append((tid, r, d, partenza, ordine))
                for seq, sid in enumerate(ordine, 1):
                    s = partenza + (seq - 1) * 120
                    hms = f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"
                    times.append([tid, hms, hms, sid, seq])
    cal = [["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"],
           ["FERIALE", 1, 1, 1, 1, 1, 1, 1, "20261001", "20261231"]]
    cald = [["service_id", "date", "exception_type"]]

    def csvtxt(righe):
        b = io.StringIO()
        csv.writer(b, lineterminator="\n").writerows(righe)
        return b.getvalue()

    with zipfile.ZipFile(percorso, "w", zipfile.ZIP_DEFLATED) as z:
        for nome, righe in (("routes.txt", routes), ("stops.txt", stops), ("trips.txt", trips), ("stop_times.txt", times),
                            ("calendar.txt", cal), ("calendar_dates.txt", cald)):
            z.writestr(nome, csvtxt(righe))
    return corse


def crea_db(percorso, corse):
    rng = random.Random(2026)
    con = sqlite3.connect(percorso)
    con.executescript("""
    CREATE TABLE trip_update_gtt (letto_utc TEXT NOT NULL, entity_id TEXT NOT NULL, trip_id TEXT, start_date TEXT, start_time TEXT,
        rel TEXT, delay INTEGER, stop_time_update INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY (letto_utc, entity_id));
    CREATE TABLE mezzi_gtt (letto_utc TEXT, ts_feed INTEGER, veicolo TEXT, linea TEXT, corsa TEXT, lat REAL, lng REAL, velocita REAL, direzione INTEGER);
    CREATE INDEX ix_mezzi_tempo ON mezzi_gtt (letto_utc);
    CREATE TABLE sensori_5t (lcd1 TEXT PRIMARY KEY, road_lcd TEXT, nome_strada TEXT, offset_m REAL, direzione TEXT, lat REAL, lng REAL, accuratezza REAL);
    CREATE TABLE flussi_5t (generato_utc TEXT, lcd1 TEXT, flusso REAL, velocita REAL, periodo_min INTEGER, PRIMARY KEY (generato_utc, lcd1));
    CREATE TABLE accuratezza_5t (generato_utc TEXT, lcd1 TEXT, accuratezza REAL, PRIMARY KEY (generato_utc, lcd1));
    CREATE TABLE parcheggi_5t (id TEXT PRIMARY KEY, nome TEXT, lat REAL, lng REAL, totale INTEGER);
    CREATE TABLE occupazione_pk (generato_utc TEXT, id TEXT, stato INTEGER, totale INTEGER, liberi INTEGER, tendenza INTEGER,
        PRIMARY KEY (generato_utc, id));
    """)
    linea_di = {r: n for r, n, _t, _l in LINEE}
    coord = {}
    for r, nome, _t, lon in LINEE:
        for i in range(N_FERMATE):
            coord[f"{r}_S{i}"] = (45.04 + 0.004 * i, lon)

    for giorno in GIORNI:
        base = _base(giorno).timestamp()
        sabato = datetime.strptime(giorno, "%Y%m%d").weekday() == 5
        tu, gps = [], []
        # il feed dei ritardi: una lettura al minuto per tutto il giorno (serve alle ore attive)
        for m in range(4 * 60, 12 * 60):
            t = base + m * 60
            tu.append((_iso(t), f"HB{m}", "HB", giorno, "", "SCHEDULED", None, 0, json.dumps({"trip": {"trip_id": "HB"}, "stu": []})))
        for n, (tid, r, d, partenza, ordine) in enumerate(corse):
            if sabato and (n % 2):
                continue
            dly = [max(-120, min(900, rng.expovariate(1 / 150) - 50)) for _ in ordine]
            for i in range(1, len(dly)):
                dly[i] = 0.7 * dly[i - 1] + 0.3 * dly[i]
            arr = [base + partenza + i * 120 + dly[i] for i in range(len(ordine))]
            # feed: per ogni fermata una lettura 60 s prima, con le fermate successive; il feed sottostima il ritardo (x0,6)
            for i in range(len(ordine)):
                letto = _iso(arr[i] - 60)
                stu = []
                for j in range(i, min(i + 3, len(ordine))):
                    dj = dly[j] * 0.6
                    if (n + j) % 5 == 0:
                        stu.append({"seq": j + 1, "arr": {"time": int(base + partenza + j * 120 + dj)}})
                    else:
                        stu.append({"seq": j + 1, "arr": {"delay": int(dj)}})
                payload = json.dumps({"trip": {"trip_id": tid, "start_date": giorno}, "stu": stu})
                tu.append((letto, f"{tid}_{i}", tid, giorno, "", "SCHEDULED", int(dly[i] * 0.6), len(stu), payload))
            # GPS: un campione ogni 30 s lungo la corsa; il 10% delle corse non ha GPS, il 15% dei campioni manca
            if giorno in POCO_GPS and n % 10:
                continue
            if rng.random() < 0.10:
                continue
            ts0, ts1 = arr[0] - 60, arr[-1] + 60
            t = ts0
            while t <= ts1:
                if rng.random() > 0.15:
                    # posizione: fra le fermate in base al tempo di arrivo stimato
                    if t <= arr[0]:
                        lat, lon = coord[ordine[0]]
                    elif t >= arr[-1]:
                        lat, lon = coord[ordine[-1]]
                    else:
                        i = max(k for k in range(len(arr) - 1) if arr[k] <= t)
                        f = (t - arr[i]) / (arr[i + 1] - arr[i])
                        (la0, lo0), (la1, lo1) = coord[ordine[i]], coord[ordine[i + 1]]
                        lat, lon = la0 + f * (la1 - la0), lo0 + f * (lo1 - lo0)
                    gps.append((_iso(t + 2), int(t), f"V{n}", linea_di[r], tid, round(lat, 6), round(lon, 6), 10.0, d))
                t += 30
        # un po' di sporcizia: corsa fuori dal GTFS e righe senza corsa
        for k in range(40):
            t = base + 8 * 3600 + k * 30
            gps.append((_iso(t + 2), int(t), "VX", "99", "XXX_0_00", 45.06 + k * 1e-4, 7.60, 5.0, 0))
            gps.append((_iso(t + 2), int(t), "VY", "99", "", 45.06, 7.61, 5.0, 0))
        con.executemany("INSERT OR IGNORE INTO trip_update_gtt VALUES (?,?,?,?,?,?,?,?,?)", tu)
        con.executemany("INSERT INTO mezzi_gtt VALUES (?,?,?,?,?,?,?,?,?)", gps)

    # sensori 5T: 6 sensori, uno ogni 5 minuti, giorni interi dal 12 al 17 ottobre (ora locale)
    sensori = [(f"S{i}", f"R{i}", f"Corso {i} (TO)" if i < 5 else f"Strada provinciale {i}", 0.0, "N" if i % 2 else "S",
                45.05 + 0.005 * i, 7.65 + 0.004 * i, 1.0) for i in range(6)]
    con.executemany("INSERT INTO sensori_5t VALUES (?,?,?,?,?,?,?,?)", sensori)
    flussi, accur = [], []
    for d in GIORNI_5T:
        inizio = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) - timedelta(hours=OFFSET)
        for k in range(288):
            t = inizio + timedelta(minutes=5 * k)
            h = (k * 5) // 60
            g = t.isoformat()
            for s in sensori:
                base_f = 40 + 300 * max(0.0, 1 - abs(h - 8) / 6) + 250 * max(0.0, 1 - abs(h - 18) / 6)
                if rng.random() < 0.03:
                    f, v = None, None
                else:
                    f = float(int(rng.gauss(base_f, 25))) if rng.random() > 0.02 else 0.0
                    f = max(f, 0.0)
                    v = None if rng.random() < 0.02 else round(max(5.0, rng.gauss(32 - 0.03 * base_f, 3)), 1)
                flussi.append((g, s[0], f, v, 5))
                r_ = rng.random()
                if r_ < 0.02:
                    pass                       # nessuna riga di accuratezza
                else:
                    accur.append((g, s[0], 0.0 if r_ < 0.05 else 1.0))
    con.executemany("INSERT INTO flussi_5t VALUES (?,?,?,?,?)", flussi)
    con.executemany("INSERT INTO accuratezza_5t VALUES (?,?,?)", accur)

    # parcheggi: 4 parcheggi, una lettura ogni 5 minuti; il 12/10 la raccolta parte a mezzogiorno (giorno incompleto)
    park = [("P1", "PARCHEGGIO UNO", 45.06, 7.66, 400), ("P2", "PARCHEGGIO DUE", 45.07, 7.67, 250),
            ("P3", "PARCHEGGIO TRE", 45.08, 7.68, 0), ("P4", "PARCHEGGIO FERMO", 45.09, 7.69, 100)]
    con.executemany("INSERT INTO parcheggi_5t VALUES (?,?,?,?,?)", park)
    occ = []
    for d in GIORNI_5T:
        inizio = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) - timedelta(hours=OFFSET)
        for k in range(288):
            if d == GIORNI_5T[0] and k < 144:
                continue
            t = inizio + timedelta(minutes=5 * k)
            h = (k * 5) / 60
            g = t.isoformat()
            for pid, _n, _la, _lo, tot in park:
                if pid == "P4":
                    o = 0.51
                elif pid == "P2":
                    o = 0.2 + 0.1 * max(0.0, 1 - abs(h - 3) / 4)         # residenziale: piu' pieno di notte
                else:
                    o = 0.15 + 0.7 * max(0.0, 1 - abs(h - 12) / 6)       # pendolare: pieno di giorno
                o = min(1.0, max(0.0, o + rng.gauss(0, 0.02)))
                stato = 0 if rng.random() < 0.01 else 1
                totale = tot if tot else None
                liberi = None if rng.random() < 0.01 else int(round((1 - o) * (tot or 120)))
                occ.append((g, pid, stato, totale, liberi, 0))
    con.executemany("INSERT INTO occupazione_pk VALUES (?,?,?,?,?,?)", occ)
    con.commit()
    con.close()


def crea(cartella):
    cartella = Path(cartella)
    (cartella / "data").mkdir(parents=True, exist_ok=True)
    gtfs = cartella / "data" / "gtt_gtfs_finto.zip"
    db = cartella / "data" / "storico_backup.sqlite"
    corse = crea_gtfs(gtfs)
    crea_db(db, corse)
    return {"db": db, "gtfs": gtfs, "giorno_controllo": "20261015"}


if __name__ == "__main__":
    import sys
    out = crea(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(out)
