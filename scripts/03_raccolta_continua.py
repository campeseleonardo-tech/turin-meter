#!/usr/bin/env python3
"""
03_raccolta_continua.py  -  raccoglie nel tempo i dati reali di Torino (PC ora, Raspberry Pi in futuro).

Ogni 5 minuti salva i flussi di traffico 5T (91 sensori) e i posti liberi nei
parcheggi in struttura 5T (~41 parcheggi, compresi gli interscambi Stura/Caio Mario/
Sofia/Venchi Unica/Fermi).
Una volta al giorno salva perimetro/varchi/orari ZTL 5T, solo se diversi dall'ultima copia.
Una volta al giorno scarica il GTFS di GTT: se e' cambiato, lo tiene in data/gtfs/gtt_gtfs_AAAAMMGG.zip
e scrive una riga nella tabella gtfs_versioni (il file non va dentro SQLite: lo storico crescerebbe).
Ogni N secondi (default 60) salva le posizioni dei mezzi GTT.
Tutto finisce in un unico file locale: data/storico.sqlite  (nessun cloud).

Non serve installare nulla (solo Python).
Avvio di prova (si ferma con Ctrl+C):
    python3 03_raccolta_continua.py
Solo traffico, senza mezzi GTT:
    python3 03_raccolta_continua.py --no-gtt
Una sola lettura e poi esce (per provare che funziona):
    python3 03_raccolta_continua.py --una-volta

Peso indicativo (stima mia, NON misurata): i flussi 5T sono ~26.000 righe/giorno,
poche MB al mese. Le posizioni GTT a 60 s possono arrivare a decine di MB al giorno:
controlla la dimensione di storico.sqlite dopo un giorno e, se serve, alza --gtt-secondi.
Se un feed risponde con errore, lo script scrive l'errore e riprova al giro dopo,
senza fermarsi.
"""
import argparse
import csv
import hashlib
import io
import sqlite3
import struct
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent

def trova_radice():
    """La cartella del progetto e' quella chiamata GTT, ovunque venga lanciato lo script."""
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    candidata = Path.home() / "Desktop" / "GTT"
    if candidata.is_dir():
        return candidata
    return AQUI.parent


RADICE = trova_radice()
DB = RADICE / "data" / "storico.sqlite"
UA = "GTT-progetto-personale/0.1 (studio personale)"
URL_5T = "https://opendata.5t.torino.it/get_fdt"
URL_PK = "https://opendata.5t.torino.it/get_pk"
URL_ZTL = "https://opendata.5t.torino.it/get_access_control"
SECONDI_ZTL = 86400  # dato quasi fisso: basta un controllo al giorno
URL_GTFS = "https://www.gtt.to.it/open_data/gtt_gtfs.zip"  # stesso indirizzo dello script 01
SECONDI_GTFS = 86400  # GTT lo cambia poche volte l'anno: basta un controllo al giorno
CARTELLA_GTFS = RADICE / "data" / "gtfs"
FILE_GTFS_OBBLIGATORI = ("stops.txt", "trips.txt", "stop_times.txt")
URL_VP = "https://percorsieorari.gtt.to.it/das_gtfsrt/vehicle_position.aspx"
SECONDI_5T = 300  # il feed 5T e' aggiornato ogni 5 minuti: non ha senso chiedere piu' spesso

# --- codici lcd1 condivisi da due sensori fisici (pacchetto H, 17/10/2026) --------
# Tre codici sono usati da due sensori diversi. La PRIMA voce del documento (in
# ordine di apparizione) tiene il codice invariato, cosi' i dati storici restano
# validi; la seconda e le successive diventano '<codice>~2', '<codice>~3'...
# Qui l'offset atteso della prima voce, che serve da ancora: se il feed cambia
# ordine, lo script lo segnala nel log invece di scambiare i due sensori.
CODICI_CONDIVISI_ANCORA = {"40189": 160.0, "40123": 1555.0, "13077": 4960.0}


def adesso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(msg):
    print(f"{adesso()}  {msg}", flush=True)


def apri_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS sensori_5t (
        lcd1 TEXT PRIMARY KEY, road_lcd TEXT, nome_strada TEXT, offset_m REAL,
        direzione TEXT, lat REAL, lng REAL, accuratezza REAL);
    CREATE TABLE IF NOT EXISTS flussi_5t (
        generato_utc TEXT, lcd1 TEXT, flusso REAL, velocita REAL, periodo_min INTEGER,
        PRIMARY KEY (generato_utc, lcd1));
    CREATE TABLE IF NOT EXISTS accuratezza_5t (
        generato_utc TEXT, lcd1 TEXT, accuratezza REAL,
        PRIMARY KEY (generato_utc, lcd1));
    CREATE TABLE IF NOT EXISTS mezzi_gtt (
        letto_utc TEXT, ts_feed INTEGER, veicolo TEXT, linea TEXT, corsa TEXT,
        lat REAL, lng REAL, velocita REAL, direzione INTEGER);
    CREATE INDEX IF NOT EXISTS ix_mezzi_tempo ON mezzi_gtt (letto_utc);
    CREATE TABLE IF NOT EXISTS parcheggi_5t (
        id TEXT PRIMARY KEY, nome TEXT, lat REAL, lng REAL, totale INTEGER);
    CREATE TABLE IF NOT EXISTS occupazione_pk (
        generato_utc TEXT, id TEXT, stato INTEGER, totale INTEGER, liberi INTEGER,
        tendenza INTEGER, PRIMARY KEY (generato_utc, id));
    CREATE TABLE IF NOT EXISTS ztl_5t (scaricato_utc TEXT, generato TEXT, xml BLOB);
    CREATE TABLE IF NOT EXISTS gtfs_versioni (
        scaricato_utc TEXT, file TEXT, sha256 TEXT, byte INTEGER, valido_da TEXT, valido_a TEXT);
    CREATE TABLE IF NOT EXISTS errori (quando_utc TEXT, fonte TEXT, messaggio TEXT);
    """)
    return con


def scarica(url):
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(r, timeout=60) as resp:
        return resp.read()


def nome_locale(tag):
    """Toglie lo schema XML dal nome: '{https://...}FDT_data' diventa 'FDT_data'."""
    return tag.rsplit("}", 1)[-1]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def salva_5t_da_bytes(con, dati):
    """Interpreta l'XML 5T e salva sensori e misure. Restituisce il numero di misure salvate.

    Codici condivisi (pacchetto H, 17/10/2026): tre codici lcd1 sono usati da due
    sensori fisici diversi. La PRIMA voce in ordine di apparizione tiene il codice
    invariato; la seconda e le successive diventano '<codice>~2', '<codice>~3'...
    (esempio: 40189~2), cosi' i due sensori si salvano entrambi e i dati storici
    restano validi.
    """
    radice = ET.fromstring(dati)
    generato = radice.attrib.get("generation_time") or adesso()
    n = 0
    visti = {}
    for s in radice.iter():
        if nome_locale(s.tag) != "FDT_data":
            continue
        a = s.attrib
        lcd1 = a.get("lcd1")
        if not lcd1:
            continue
        # --- codici condivisi: primo = invariato, poi ~2, ~3, ... ---
        visti[lcd1] = visti.get(lcd1, 0) + 1
        if visti[lcd1] == 1:
            codice = lcd1
            atteso = CODICI_CONDIVISI_ANCORA.get(lcd1)
            if atteso is not None and _num(a.get("offset")) != atteso:
                log(f"ATTENZIONE 5T: {lcd1} ha la prima voce con offset "
                    f"{a.get('offset')} invece di {atteso}: ordine del feed cambiato?")
        else:
            codice = f"{lcd1}~{visti[lcd1]}"
            log(f"5T: il codice {lcd1} compare piu' volte nel documento: la voce "
                f"n. {visti[lcd1]} diventa {codice} (offset {a.get('offset')})")
        con.execute("INSERT OR REPLACE INTO sensori_5t VALUES (?,?,?,?,?,?,?,?)",
                    (codice, a.get("Road_LCD"), a.get("Road_name"), _num(a.get("offset")),
                     a.get("direction"), _num(a.get("lat")), _num(a.get("lng")), _num(a.get("accuracy"))))
        # L'accuratezza di questa misura si salva PERMANENTE in accuratezza_5t, nello
        # stesso ciclo/transazione dei flussi. Prima di questo cambiamento l'accuratezza
        # non era salvata per misura: il passato resta "non disponibile" (le vecchie righe
        # di flussi_5t non vengono riscritte e in accuratezza_5t non si inventa nulla).
        con.execute("INSERT OR IGNORE INTO accuratezza_5t VALUES (?,?,?)",
                    (generato, codice, _num(a.get("accuracy"))))
        sf = next((c for c in s if nome_locale(c.tag) == "speedflow"), None)
        if sf is None:
            continue
        cur = con.execute("INSERT OR IGNORE INTO flussi_5t VALUES (?,?,?,?,?)",
                          (generato, codice, _num(sf.attrib.get("flow")), _num(sf.attrib.get("speed")),
                           int(_num(a.get("period")) or 5)))
        n += cur.rowcount  # 0 se la misura era gia' presente
    con.commit()
    return n


def _int(v):
    n = _num(v)
    return None if n is None else int(n)


def salva_pk_da_bytes(con, dati):
    """Parcheggi in struttura 5T: anagrafica + posti liberi. 'liberi' manca (NULL) quando
    il parcheggio non trasmette (stato 0). Restituisce il numero di letture salvate."""
    radice = ET.fromstring(dati)
    generato = radice.attrib.get("generation_time") or adesso()
    n = 0
    for p in radice.iter():
        if nome_locale(p.tag) != "PK_data":
            continue
        a = p.attrib
        pid = a.get("ID")
        if not pid:
            continue
        con.execute("INSERT OR REPLACE INTO parcheggi_5t VALUES (?,?,?,?,?)",
                    (pid, a.get("Name"), _num(a.get("lat")), _num(a.get("lng")), _int(a.get("Total"))))
        cur = con.execute("INSERT OR IGNORE INTO occupazione_pk VALUES (?,?,?,?,?,?)",
                          (generato, pid, _int(a.get("status")), _int(a.get("Total")),
                           _int(a.get("Free")), _int(a.get("tendence"))))
        n += cur.rowcount  # 0 se la lettura era gia' presente
    con.commit()
    return n


def salva_ztl_da_bytes(con, dati):
    """Salva l'XML ZTL intero, ma solo se diverso dall'ultima copia. True se salvato."""
    ultima = con.execute("SELECT xml FROM ztl_5t ORDER BY scaricato_utc DESC LIMIT 1").fetchone()
    if ultima and ultima[0] == dati:
        return False
    generato = ET.fromstring(dati).attrib.get("generation_time")
    con.execute("INSERT INTO ztl_5t VALUES (?,?,?)", (adesso(), generato, dati))
    con.commit()
    return True


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
    """Legge i campi di un messaggio protobuf (senza librerie esterne)."""
    i, out = 0, []
    while i < len(b):
        k, i = _varint(b, i)
        fn, wt = k >> 3, k & 7
        if wt == 0:
            v, i = _varint(b, i)
        elif wt == 1:
            v = b[i:i + 8]; i += 8
        elif wt == 2:
            n, i = _varint(b, i)
            v = b[i:i + n]; i += n
        elif wt == 5:
            v = b[i:i + 4]; i += 4
        else:
            raise ValueError(f"tipo protobuf non gestito: {wt}")
        out.append((fn, v))
    return out


def _txt(v):
    return v.decode("utf-8", "replace")


def salva_vp_da_bytes(con, dati):
    """Posizioni dei mezzi GTT (GTFS-realtime). Nessuna libreria da installare."""
    top = _campi(dati)
    ts_feed = 0
    for f, v in top:
        if f == 1:
            for f2, v2 in _campi(v):
                if f2 == 3:
                    ts_feed = v2
    letto = adesso()
    righe = []
    for f, v in top:
        if f != 2:
            continue
        ent = dict(_campi(v))
        if 4 not in ent:
            continue
        veh = dict(_campi(ent[4]))
        if 2 not in veh:
            continue
        pos = dict(_campi(veh[2]))
        if 1 not in pos or 2 not in pos:
            continue
        linea = corsa = vid = ""
        if 1 in veh:
            for f1, v1 in _campi(veh[1]):
                if f1 == 5:
                    linea = _txt(v1)
                elif f1 == 1:
                    corsa = _txt(v1)
        if 8 in veh:
            for f1, v1 in _campi(veh[8]):
                if f1 == 1:
                    vid = _txt(v1)
        vel = struct.unpack("<f", pos[5])[0] if 5 in pos else None
        rot = int(struct.unpack("<f", pos[3])[0]) if 3 in pos else None
        righe.append((letto, veh.get(5, ts_feed), vid or _txt(ent.get(1, b"")), linea, corsa,
                      struct.unpack("<f", pos[1])[0], struct.unpack("<f", pos[2])[0], vel, rot))
    con.executemany("INSERT INTO mezzi_gtt VALUES (?,?,?,?,?,?,?,?,?)", righe)
    con.commit()
    return len(righe)


def registra_errore(con, fonte, e):
    log(f"ERRORE {fonte}: {e}")
    try:
        con.execute("INSERT INTO errori VALUES (?,?,?)", (adesso(), fonte, str(e)[:500]))
        con.commit()
    except Exception:
        pass


def giro_5t(con):
    try:
        n = salva_5t_da_bytes(con, scarica(URL_5T))
        log(f"5T: {n} misure salvate")
    except Exception as e:
        registra_errore(con, "5T", e)


def giro_pk(con):
    try:
        n = salva_pk_da_bytes(con, scarica(URL_PK))
        log(f"PK: {n} letture parcheggi salvate")
    except Exception as e:
        registra_errore(con, "PK", e)


def giro_ztl(con):
    try:
        nuovo = salva_ztl_da_bytes(con, scarica(URL_ZTL))
        log("ZTL: " + ("nuova versione salvata" if nuovo else "invariata"))
    except Exception as e:
        registra_errore(con, "ZTL", e)


def _csv_righe(zf, nome):
    with zf.open(nome) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))


def _data_iso(testo):
    t = (testo or "").strip()
    return f"{t[:4]}-{t[4:6]}-{t[6:8]}" if len(t) == 8 and t.isdigit() else None


def controlla_gtfs(dati):
    """Zip valido con i file che servono? Ritorna (valido_da, valido_a) in AAAA-MM-GG; eccezione se no."""
    zf = zipfile.ZipFile(io.BytesIO(dati))
    nomi = set(zf.namelist())
    mancanti = [n for n in FILE_GTFS_OBBLIGATORI if n not in nomi]
    if mancanti or not ({"calendar.txt", "calendar_dates.txt"} & nomi):
        raise ValueError(f"GTFS incompleto: mancano {mancanti or 'calendar.txt e calendar_dates.txt'}")
    if zf.testzip() is not None:
        raise ValueError("GTFS: zip danneggiato")
    da = a = None
    if "feed_info.txt" in nomi:
        for r in _csv_righe(zf, "feed_info.txt"):
            da, a = _data_iso(r.get("feed_start_date")), _data_iso(r.get("feed_end_date"))
            break
    if not (da and a):
        date = []
        if "calendar.txt" in nomi:
            for r in _csv_righe(zf, "calendar.txt"):
                date += [_data_iso(r.get("start_date")), _data_iso(r.get("end_date"))]
        if "calendar_dates.txt" in nomi:
            date += [_data_iso(r.get("date")) for r in _csv_righe(zf, "calendar_dates.txt")]
        date = [d for d in date if d]
        if not date:
            raise ValueError("GTFS: nessuna data di validita'")
        da, a = min(date), max(date)
    return da, a


def data_italiana():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Rome")).strftime("%Y%m%d")
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y%m%d")


def salva_gtfs_da_bytes(con, dati, cartella=None):
    """Salva lo zip se l'hash e' nuovo. Ritorna il nome del file salvato, o None se uguale all'ultimo."""
    cartella = Path(cartella or CARTELLA_GTFS)
    da, a = controlla_gtfs(dati)
    sha = hashlib.sha256(dati).hexdigest()
    ultimo = con.execute("SELECT sha256 FROM gtfs_versioni ORDER BY scaricato_utc DESC, rowid DESC LIMIT 1").fetchone()
    if ultimo and ultimo[0] == sha:
        return None
    cartella.mkdir(parents=True, exist_ok=True)
    nome = f"gtt_gtfs_{data_italiana()}.zip"
    if (cartella / nome).exists():
        nome = nome[:-4] + "_2.zip"
    (cartella / nome).write_bytes(dati)
    con.execute("INSERT INTO gtfs_versioni VALUES (?,?,?,?,?,?)", (adesso(), nome, sha, len(dati), da, a))
    con.commit()
    return nome


def giro_gtfs(con):
    try:
        nome = salva_gtfs_da_bytes(con, scarica(URL_GTFS))
        log("GTFS: " + ("invariato" if nome is None else f"versione nuova salvata ({nome})"))
    except Exception as e:
        registra_errore(con, "GTFS", e)


def giro_gtt(con):
    try:
        n = salva_vp_da_bytes(con, scarica(URL_VP))
        log(f"GTT: {n} mezzi salvati")
    except Exception as e:
        registra_errore(con, "GTT", e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-gtt", action="store_true", help="non raccogliere le posizioni dei mezzi GTT")
    ap.add_argument("--gtt-secondi", type=int, default=60, help="ogni quanti secondi leggere i mezzi GTT (minimo 30)")
    ap.add_argument("--una-volta", action="store_true", help="una sola lettura e poi esce")
    args = ap.parse_args()
    gtt_sec = max(30, args.gtt_secondi)

    con = apri_db()
    log(f"Archivio: {DB}")
    prossimo_5t = prossimo_gtt = prossimo_ztl = prossimo_gtfs = 0.0
    try:
        while True:
            t = time.time()
            if t >= prossimo_5t:
                giro_5t(con)
                giro_pk(con)
                prossimo_5t = t + SECONDI_5T
            if t >= prossimo_ztl:
                giro_ztl(con)
                prossimo_ztl = t + SECONDI_ZTL
            if t >= prossimo_gtfs:
                giro_gtfs(con)
                prossimo_gtfs = t + SECONDI_GTFS
            if not args.no_gtt and t >= prossimo_gtt:
                giro_gtt(con)
                prossimo_gtt = t + gtt_sec
            if args.una_volta:
                break
            time.sleep(5)
    except KeyboardInterrupt:
        log("Fermato dall'utente.")
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
