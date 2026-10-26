#!/usr/bin/env python3
"""Copia ogni giorno lo storico SQLite dal Pi al PC in modo consistente.

Regola (L4, 23/10/2026): la copia nuova sostituisce quella vecchia solo se non ha perso dati. Il solo
controllo di integrita' non basta: se sul Pi il file si azzera, la copia e' vuota ma "integra" e il PC
butterebbe l'unica copia buona. Quindi, per ogni tabella gia' presente nella copia vecchia: righe nuove >=
righe vecchie; per mezzi_gtt e flussi_5t anche primo istante uguale e ultimo istante >= quello vecchio.
Se la regola non e' rispettata la vecchia resta, la nuova va in data/storico_backup_SOSPETTO.sqlite e
l'uscita e' il codice 3 (ALLARME nel .bat). Se e' rispettata, la vecchia diventa storico_backup_ieri.sqlite.
Prova senza Pi: python scripts/backup_da_leopi.py --prova
"""
import base64
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config_locale  # noqa: E402


def trova_radice():
    qui = Path(__file__).resolve().parent
    return next((p for p in [qui, *qui.parents] if p.name.lower() == "gtt"), qui.parent)


RAD = trova_radice()
DATA = RAD / "data"
# config_locale.json nella radice (non in git); con --prova (anche sul controllo automatico di GitHub) non serve
CFG = config_locale.carica() if "--prova" not in sys.argv else {"pi": "prova@prova", "dir_remota": "/prova", "chiave": "prova"}
PI = CFG["pi"]
REMOTE_DB = CFG["dir_remota"] + "/data/storico.sqlite"
# L4b (23/10/2026): lo snapshot sul Pi sta su disco, non in /tmp (sul Pi /tmp e' in memoria: 3,9 GB, non bastano piu')
REMOTE_TMP_DIR = CFG["dir_remota"] + "/data/tmp_copia"
SPAZIO_SNAPSHOT_VOLTE = 1.5  # spazio libero richiesto sul Pi: 1,5 volte lo storico, prima di fare lo snapshot
RESTI_ORE = 24  # si cancellano solo gtt_storico_*.sqlite di quella cartella piu' vecchi di cosi' (copie interrotte)
SSH_KEY = Path(CFG["chiave"])
DEST = DATA / "storico_backup.sqlite"
TABELLE = ("sensori_5t", "flussi_5t", "accuratezza_5t", "mezzi_gtt", "errori",
           "trip_update_gtt", "avvisi_gtt",
           "parcheggi_5t", "occupazione_pk", "ztl_5t",
           "gtfs_versioni")  # parcheggi/ZTL raccolti dal 14/10; gtfs_versioni dall'archivio GTFS (L4)
TABELLE_CON_ISTANTI = ("mezzi_gtt", "flussi_5t")  # qui anche il primo istante deve restare uguale
CODICE_SOSPETTO = 3
SPAZIO_PER_IERI = 1.2  # copia "ieri" solo se il disco del PC ha almeno 1,2 volte la copia nuova


def esegui(comando):
    r = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode:
        raise RuntimeError(f"Comando fallito ({r.returncode}): {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout.strip()


def comando_ssh(testo):
    codice = base64.b64encode(testo.encode("utf-8")).decode("ascii")
    remoto = f"python3 -c \"import base64;exec(base64.b64decode('{codice}').decode())\""
    return [shutil.which("ssh") or "ssh", "-i", str(SSH_KEY), "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=30", PI, remoto]


def codice_remoto(db, cartella, snapshot, volte=SPAZIO_SNAPSHOT_VOLTE, resti_ore=RESTI_ORE):
    """Codice Python eseguito sul Pi (e provato in locale da --prova): spazio, resti vecchi, snapshot, riepilogo."""
    return f'''import json, sqlite3, os, time, glob, shutil
db={db!r}; cartella={cartella!r}; snap={snapshot!r}
os.makedirs(cartella, exist_ok=True)
peso=os.path.getsize(db)
libero=shutil.disk_usage(cartella).free
serve=int({volte}*peso)
if libero<serve:
    print(json.dumps({{"spazio_insufficiente":{{"libero":libero,"serve":serve}}}}))
    raise SystemExit(0)
for f in glob.glob(os.path.join(cartella,"gtt_storico_*.sqlite")):
    if f!=snap and time.time()-os.path.getmtime(f)>{resti_ore}*3600:
        os.unlink(f)
src=sqlite3.connect("file:"+db+"?mode=ro", uri=True, timeout=60)
dst=sqlite3.connect(snap, timeout=60)
src.backup(dst, pages=256, sleep=0.1)
check=dst.execute("PRAGMA integrity_check").fetchone()[0]
tables={{r[0] for r in dst.execute("SELECT name FROM sqlite_master WHERE type='table'")}}
names={TABELLE!r}
counts={{t: dst.execute('SELECT COUNT(*) FROM "'+t+'"').fetchone()[0] for t in names if t in tables}}
ranges={{}}
for t,col in (("mezzi_gtt","letto_utc"),("flussi_5t","generato_utc"),("trip_update_gtt","letto_utc"),("occupazione_pk","generato_utc")):
    if t in tables: ranges[t]=dst.execute('SELECT MIN("'+col+'"),MAX("'+col+'") FROM "'+t+'"').fetchone()
dst.close(); src.close()
print(json.dumps({{"integrity_check":check,"conteggi":counts,"intervalli":ranges}}))
'''


def riepilogo_locale(percorso, controlla=True):
    uri = percorso.resolve().as_uri() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True, timeout=30)
    integro = "non controllato"
    if controlla:
        integro = con.execute("PRAGMA integrity_check").fetchone()[0]
    if controlla and integro != "ok":
        con.close()
        raise RuntimeError(f"integrity_check locale: {integro}")
    presenti = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conteggi = {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                for t in TABELLE if t in presenti}
    ultimi = {}
    for tabella, colonna in (("mezzi_gtt", "letto_utc"), ("flussi_5t", "generato_utc"),
                             ("trip_update_gtt", "letto_utc"),
                             ("occupazione_pk", "generato_utc")):
        if tabella in presenti:
            ultimi[tabella] = con.execute(
                f'SELECT MIN("{colonna}"),MAX("{colonna}") FROM "{tabella}"').fetchone()
    con.close()
    return {"integrity_check": integro, "conteggi": conteggi, "intervalli": ultimi}


def decidi(riepilogo_vecchio, riepilogo_nuovo):
    """Funzione pura: (accetta, motivi). Riepiloghi come quelli di riepilogo_locale()."""
    motivi = []
    nuovi = riepilogo_nuovo["conteggi"]
    for tabella, vecchie in riepilogo_vecchio["conteggi"].items():
        if tabella not in nuovi:
            motivi.append(f"{tabella}: nella copia nuova manca (vecchia {vecchie:,} righe)")
        elif nuovi[tabella] < vecchie:
            motivi.append(f"{tabella}: {nuovi[tabella]:,} righe nuove contro {vecchie:,} vecchie")
    for tabella in TABELLE_CON_ISTANTI:
        v = riepilogo_vecchio["intervalli"].get(tabella)
        n = riepilogo_nuovo["intervalli"].get(tabella)
        if not v or v[0] is None:
            continue
        if not n or n[0] is None:
            motivi.append(f"{tabella}: nessun istante nella copia nuova (vecchia {v[0]} - {v[1]})")
        elif n[0] != v[0]:
            motivi.append(f"{tabella}: primo istante {n[0]} contro {v[0]}")
        elif n[1] < v[1]:
            motivi.append(f"{tabella}: ultimo istante {n[1]} prima di {v[1]}")
    return not motivi, motivi


def sostituisci(nuova, dest, avviso=print):
    """Applica la regola: ritorna 0 se la copia nuova e' stata accettata, CODICE_SOSPETTO se no."""
    sospetto = dest.with_name(dest.stem + "_SOSPETTO.sqlite")
    ieri = dest.with_name(dest.stem + "_ieri.sqlite")
    if dest.exists():
        accetta, motivi = decidi(riepilogo_locale(dest, controlla=False),
                                 riepilogo_locale(nuova, controlla=False))
        if not accetta:
            os.replace(nuova, sospetto)
            print("ALLARME: la copia nuova ha meno dati di quella di prima, tenuta la vecchia.")
            for m in motivi:
                print(f"  - {m}")
            print(f"La nuova e' in {sospetto}")
            return CODICE_SOSPETTO
        libero = shutil.disk_usage(dest.parent).free
        if libero < SPAZIO_PER_IERI * nuova.stat().st_size:
            avviso(f"AVVISO: poco spazio sul PC ({libero / 1e9:.1f} GB liberi): non tengo la copia 'ieri'")
        else:
            os.replace(dest, ieri)
    os.replace(nuova, dest)
    return 0


def prova():
    """Cinque casi su due SQLite finti, in una cartella temporanea."""
    def crea(percorso, mezzi, flussi, primo="2026-10-01", ultimo="2026-10-02"):
        con = sqlite3.connect(percorso)
        con.execute("CREATE TABLE mezzi_gtt (letto_utc TEXT)")
        con.execute("CREATE TABLE flussi_5t (generato_utc TEXT)")
        con.executemany("INSERT INTO mezzi_gtt VALUES (?)",
                        [(primo if i == 0 else ultimo,) for i in range(mezzi)])
        con.executemany("INSERT INTO flussi_5t VALUES (?)",
                        [(primo if i == 0 else ultimo,) for i in range(flussi)])
        con.commit()
        con.close()

    casi = [
        ("nuova piu' grande: sostituita, c'e' 'ieri'", True, dict(m=20, f=20), 0, True, False),
        ("nuova con meno righe: tenuta la vecchia, SOSPETTO", True, dict(m=5, f=20), 3, False, True),
        ("nuova vuota: come sopra", True, dict(m=0, f=0), 3, False, True),
        ("primo istante diverso: come sopra", True, dict(m=20, f=20, primo="2026-10-05"), 3, False, True),
        ("nessuna copia vecchia: sostituita", False, dict(m=20, f=20), 0, True, False),
    ]
    errori = 0
    for nome, con_vecchia, k, codice_atteso, nuova_vince, sospetto_atteso in casi:
        with tempfile.TemporaryDirectory() as cartella:
            cartella = Path(cartella)
            dest = cartella / "storico_backup.sqlite"
            nuova = cartella / "nuova.part"
            if con_vecchia:
                crea(dest, 10, 10)
            crea(nuova, k["m"], k["f"], k.get("primo", "2026-10-01"))
            codice = sostituisci(nuova, dest, avviso=lambda t: None)
            righe_dest = riepilogo_locale(dest, controlla=False)["conteggi"]["mezzi_gtt"]
            ok = (codice == codice_atteso
                  and righe_dest == (k["m"] if nuova_vince else 10)
                  and (cartella / "storico_backup_SOSPETTO.sqlite").exists() == sospetto_atteso
                  and (cartella / "storico_backup_ieri.sqlite").exists() == (con_vecchia and nuova_vince))
        print(("OK     " if ok else "ERRORE ") + nome)
        errori += 0 if ok else 1
    return 1 if errori else 0


def prova_remoto():
    """Parte remota su un SQLite finto in una cartella temporanea: copia, spazio insufficiente, pulizia dei soli resti vecchi."""
    errori = 0

    def esito(nome, ok):
        nonlocal errori
        print(("OK     " if ok else "ERRORE ") + nome)
        errori += 0 if ok else 1

    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        db = t / "storico.sqlite"
        con = sqlite3.connect(db)
        con.execute("CREATE TABLE mezzi_gtt (letto_utc TEXT)")
        con.executemany("INSERT INTO mezzi_gtt VALUES (?)", [("2026-10-01",), ("2026-10-02",)])
        con.commit()
        con.close()
        cartella = t / "tmp_copia"
        snap = cartella / "gtt_storico_nuovo.sqlite"
        cartella.mkdir()
        vecchio = cartella / "gtt_storico_vecchio.sqlite"
        recente = cartella / "gtt_storico_recente.sqlite"
        altro = cartella / "altro.sqlite"
        for f in (vecchio, recente, altro):
            f.write_bytes(b"x")
        passato = time.time() - (RESTI_ORE + 1) * 3600
        os.utime(vecchio, (passato, passato))
        os.utime(altro, (passato, passato))

        def lancia(volte):
            r = subprocess.run([sys.executable, "-I", "-c", codice_remoto(str(db), str(cartella), str(snap), volte)],
                               capture_output=True, text=True)
            return json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 and r.stdout.strip() else None

        r = lancia(1e12)  # soglia finta enorme: spazio insufficiente, niente snapshot, niente pulizia
        esito("spazio insufficiente: riportato, nessuno snapshot, nessuna pulizia",
              bool(r) and "spazio_insufficiente" in r and not snap.exists() and vecchio.exists())
        r = lancia(SPAZIO_SNAPSHOT_VOLTE)
        esito("snapshot fatto, integro, 2 righe", bool(r) and r.get("integrity_check") == "ok"
              and r["conteggi"].get("mezzi_gtt") == 2 and snap.exists())
        esito("cancellato solo il resto vecchio gtt_storico_*", not vecchio.exists() and recente.exists() and altro.exists() and snap.exists())
    return 1 if errori else 0


def main():
    if not SSH_KEY.is_file():
        raise RuntimeError(f"Chiave SSH non trovata: {SSH_KEY}")
    if not DATA.is_dir():
        raise RuntimeError(f"Cartella dati non trovata: {DATA}")
    ssh = shutil.which("ssh")
    scp = shutil.which("scp")
    if not ssh or not scp:
        raise RuntimeError("ssh e scp devono essere disponibili nel PATH di Windows")

    identificatore = uuid.uuid4().hex
    remoto_tmp = f"{REMOTE_TMP_DIR}/gtt_storico_{identificatore}.sqlite"
    py_remoto = codice_remoto(REMOTE_DB, REMOTE_TMP_DIR, remoto_tmp)
    local_tmp = DATA / f"storico_backup_{identificatore}.part"
    try:
        print("Creo uno snapshot SQLite consistente sul Pi...")
        remoto = json.loads(esegui(comando_ssh(py_remoto)))
        if "spazio_insufficiente" in remoto:
            sp = remoto["spazio_insufficiente"]
            raise RuntimeError(f"poco spazio sul Pi in {REMOTE_TMP_DIR}: liberi {sp['libero'] / 1e9:.1f} GB, "
                               f"ne servono {sp['serve'] / 1e9:.1f} GB ({SPAZIO_SNAPSHOT_VOLTE} volte lo storico): "
                               "la copia di prima resta")
        if remoto.get("integrity_check") != "ok":
            raise RuntimeError(f"integrity_check remoto: {remoto.get('integrity_check')}")
        print("Copio lo snapshot sul PC...")
        esegui([scp, "-q", "-i", str(SSH_KEY), "-o", "BatchMode=yes",
                "-o", "ConnectTimeout=30", f"{PI}:{remoto_tmp}", str(local_tmp)])
        locale = riepilogo_locale(local_tmp)
        if locale["conteggi"] != remoto["conteggi"]:
            raise RuntimeError(f"conteggi diversi: Pi={remoto['conteggi']} PC={locale['conteggi']}")
        if locale["intervalli"] != {k: tuple(v) for k, v in remoto["intervalli"].items()}:
            raise RuntimeError("intervalli temporali diversi tra snapshot del Pi e copia PC")
        if sostituisci(local_tmp, DEST):
            return CODICE_SOSPETTO
        print(f"Backup verificato: {DEST}")
        print(f"Dimensione: {DEST.stat().st_size:,} byte")
        print(f"Tabelle: {remoto['conteggi']}")
        print(f"Intervalli: {remoto['intervalli']}")
    finally:
        if local_tmp.exists():
            local_tmp.unlink()
        # Elimina esclusivamente lo snapshot temporaneo creato in questa esecuzione.
        pulisci = f"import pathlib; p=pathlib.Path({remoto_tmp!r}); p.unlink(missing_ok=True)"
        try:
            esegui(comando_ssh(pulisci))
        except Exception as e:
            print(f"Avviso: non ho potuto rimuovere lo snapshot temporaneo sul Pi: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    if "--prova" in sys.argv:
        sys.exit(max(prova(), prova_remoto()))
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERRORE backup: {e}", file=sys.stderr)
        sys.exit(1)
