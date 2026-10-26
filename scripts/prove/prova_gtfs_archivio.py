#!/usr/bin/env python3
"""Prova senza Pi dell'archivio GTFS del raccoglitore (script 03): database e cartella temporanei, zip finti."""
import importlib.util
import io
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

QUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("raccolta", QUI.parent / "03_raccolta_continua.py")
rac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rac)

ERRORI = 0


def esito(nome, ok):
    global ERRORI
    print(("OK     " if ok else "ERRORE ") + nome)
    ERRORI += 0 if ok else 1


def zip_finto(fine, completo=True, feed_info=False):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("stops.txt", "stop_id\n1\n")
        if completo:
            z.writestr("trips.txt", "trip_id\n1\n")
            z.writestr("stop_times.txt", "trip_id\n1\n")
        z.writestr("calendar.txt", f"service_id,start_date,end_date\ns,20260901,{fine}\n")
        z.writestr("calendar_dates.txt", "service_id,date\ns,20260825\n")
        if feed_info:
            z.writestr("feed_info.txt", "feed_start_date,feed_end_date\n20260801,20270131\n")
    return buf.getvalue()


with tempfile.TemporaryDirectory() as t:
    cartella = Path(t) / "gtfs"
    rac.CARTELLA_GTFS = cartella
    con = sqlite3.connect(":memory:")
    con.executescript("""CREATE TABLE gtfs_versioni (scaricato_utc TEXT, file TEXT, sha256 TEXT, byte INTEGER,
        valido_da TEXT, valido_a TEXT);
        CREATE TABLE errori (quando_utc TEXT, fonte TEXT, messaggio TEXT);""")
    a = zip_finto("20270131")
    n1 = rac.salva_gtfs_da_bytes(con, a, cartella)
    esito("prima versione salvata", bool(n1) and (cartella / n1).read_bytes() == a)
    v = con.execute("SELECT valido_da, valido_a FROM gtfs_versioni").fetchone()
    esito("validita' da calendar e calendar_dates (2026-08-25 / 2027-01-31)", v == ("2026-08-25", "2027-01-31"))
    esito("stessa versione ignorata", rac.salva_gtfs_da_bytes(con, a, cartella) is None
          and con.execute("SELECT COUNT(*) FROM gtfs_versioni").fetchone()[0] == 1)
    b = zip_finto("20270630", feed_info=True)
    n2 = rac.salva_gtfs_da_bytes(con, b, cartella)
    esito("versione nuova salvata (stesso giorno: _2)", bool(n2) and n2 != n1 and n2.endswith("_2.zip"))
    esito("validita' da feed_info", con.execute("SELECT valido_a FROM gtfs_versioni ORDER BY rowid DESC").fetchone()[0] == "2027-01-31")
    esito("due file in cartella", len(list(cartella.glob("*.zip"))) == 2)
    # zip rotto e zip incompleto: errore registrato dal giro, nessuna eccezione, nessun file in piu'
    for nome, dati in (("zip rotto", b"non e' uno zip"), ("zip incompleto", zip_finto("20270131", completo=False))):
        rac.scarica = lambda url, d=dati: d
        try:
            rac.giro_gtfs(con)
            eccezione = False
        except Exception:
            eccezione = True
        esito(f"{nome}: errore registrato, nessuna eccezione",
              not eccezione and con.execute("SELECT COUNT(*) FROM errori WHERE fonte='GTFS'").fetchone()[0] >= 1
              and len(list(cartella.glob("*.zip"))) == 2)
    con.close()
sys.exit(1 if ERRORI else 0)
