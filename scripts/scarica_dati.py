#!/usr/bin/env python3
"""
scarica_dati.py  -  mette sul PC i dati grandi che non stanno in git, scaricandoli dalla Release di GitHub.

Cosa fa
-------
  1. Scarica SHA256SUMS.txt dall'ultima Release (hash di ogni zip) e poi ogni zip (dati-grezzi-*.zip, dati-calcolati-*.zip, scritti dallo script 98).
  2. Controlla l'hash dello zip; se non torna, lo scarta e si ferma con un messaggio.
  3. Dentro ogni zip legge SHA256SUMS e mette i file in data/ (stessi percorsi). Un file gia' presente e uguale (stesso hash) si salta;
     un file presente ma DIVERSO non si sovrascrive (AVVISO) a meno di --sovrascrivi. Non scrive mai fuori da data/.
  4. Stampa cosa resta da fare a mano: IMQ 2022 e OMI NON sono nella Release (licenza non chiara, sviluppo/note_tecniche/DATI.md): indirizzi e procedura
     in docs/en/METHODS.md. Con --fonti scarica anche le fonti pubbliche stabili (zone statistiche del Comune di Torino).
Lo storico della raccolta NON si scarica: ci sono i riassunti in git (data/storico_riassunti/).

Come si lancia
--------------
  python scripts/scarica_dati.py                  tutto (ultima Release)
  python scripts/scarica_dati.py --solo calcolati solo gli zip il cui nome contiene «calcolati»
  python scripts/scarica_dati.py --prova          dice cosa farebbe, non scarica
  opzioni: --url BASE (default l'ultima Release; anche file:///cartella/ per le prove)  --radice CARTELLA  --fonti  --sovrascrivi
"""
import argparse
import hashlib
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comuni import REPO_URL  # noqa: E402

RADICE = Path(__file__).resolve().parent.parent
BASE = REPO_URL + "/releases/latest/download/"
UA = "GTT-progetto-personale/0.1 (studio personale)"
FONTI_PUBBLICHE = [
    ("zone_statistiche_csv.zip", "http://geoportale.comune.torino.it/geodati/zip/zone_statistiche_csv.zip"),
    ("zone_statistiche_geo.zip", "http://geoportale.comune.torino.it/geodati/zip/zone_statistiche_geo.zip"),
]
A_MANO = [
    ("IMQ 2022 (Agenzia della mobilita' piemontese)", "https://mtm.torino.it/it/dati-statistiche/indagini-old/indagine-imq-2021/open-data-imq-2022/",
     "scarica IMQ2022_opendata_web.zip e le zone di campionamento in data/raw/IMQ2022_opendata_web/ (licenza non chiara)"),
    ("OMI (Agenzia delle Entrate)", "https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari",
     "servizio Forniture dati OMI: semestre 2025/2, provincia di Torino, in data/raw/omi_2025_2/ (licenza non chiara)"),
    ("Rete stradale (OpenStreetMap)", "https://download.geofabrik.de/europe/italy/nord-ovest.html",
     "gia' nella Release come estratto tagliato (data/otp/rete/torino_cintura.osm.pbf); l'intero Nord-Ovest serve solo per rifarlo con lo script 17"),
]
BLOCCO = 1024 * 1024


def sha256_file(percorso):
    h = hashlib.sha256()
    with open(percorso, "rb") as f:
        while True:
            b = f.read(BLOCCO)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def scarica(url, dest, etichetta=""):
    """Scarica in dest (a blocchi, con avanzamento). Ritorna True/False e stampa l'errore."""
    richiesta = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(richiesta, timeout=120) as r, open(dest, "wb") as f:
            totale = int(r.headers.get("Content-Length") or 0)
            letti, ultimo = 0, 0
            while True:
                b = r.read(BLOCCO)
                if not b:
                    break
                f.write(b)
                letti += len(b)
                if totale and letti - ultimo >= 50 * BLOCCO:
                    print(f"    {etichetta} {letti / 1e6:.0f}/{totale / 1e6:.0f} MB", flush=True)
                    ultimo = letti
        return True
    except urllib.error.HTTPError as e:
        print(f"  [ERRORE] {url}: il server risponde {e.code} ({e.reason})")
    except Exception as e:
        print(f"  [ERRORE] {url}: {e}")
    return False


def leggi_somme(testo):
    """Righe «hash  nome» -> {nome: hash}"""
    out = {}
    for riga in testo.splitlines():
        parti = riga.strip().split(None, 1)
        if len(parti) == 2 and len(parti[0]) == 64:
            out[parti[1].strip().lstrip("*")] = parti[0].lower()
    return out


def estrai_zip(percorso_zip, radice, sovrascrivi, prova):
    """Mette i file dello zip in radice/data. Ritorna (scritti, uguali, diversi_saltati, rifiutati)."""
    scritti = uguali = saltati = rifiutati = 0
    data = (radice / "data").resolve()
    with zipfile.ZipFile(percorso_zip) as z:
        somme = leggi_somme(z.read("SHA256SUMS").decode("utf-8")) if "SHA256SUMS" in z.namelist() else {}
        if not somme:
            print("  [ERRORE] lo zip non ha SHA256SUMS: non lo uso")
            return 0, 0, 0, 1
        for nome, hash_atteso in somme.items():
            destinazione = (radice / nome).resolve()
            if not nome.startswith("data/") or ".." in Path(nome).parts or data not in destinazione.parents:
                print(f"  [RIFIUTATO] percorso fuori da data/: {nome}")
                rifiutati += 1
                continue
            if destinazione.exists():
                if sha256_file(destinazione) == hash_atteso:
                    uguali += 1
                    continue
                if not sovrascrivi:
                    print(f"  AVVISO {nome}: esiste ed e' diverso, non lo sovrascrivo (usa --sovrascrivi)")
                    saltati += 1
                    continue
            if prova:
                scritti += 1
                continue
            destinazione.parent.mkdir(parents=True, exist_ok=True)
            tmp = destinazione.with_name(destinazione.name + ".part")
            h = hashlib.sha256()
            with z.open(nome) as src, open(tmp, "wb") as dst:
                while True:
                    b = src.read(BLOCCO)
                    if not b:
                        break
                    h.update(b)
                    dst.write(b)
            if h.hexdigest() != hash_atteso:
                tmp.unlink()
                print(f"  [ERRORE] {nome}: l'hash non torna, file scartato")
                rifiutati += 1
                continue
            tmp.replace(destinazione)
            scritti += 1
    return scritti, uguali, saltati, rifiutati


def main():
    ap = argparse.ArgumentParser(description="Scarica i dati grandi dalla Release di GitHub e li mette in data/")
    ap.add_argument("--url", default=BASE, help="base degli indirizzi (default: ultima Release; file:///cartella/ per le prove)")
    ap.add_argument("--radice", default=str(RADICE), help="cartella del progetto (default: questa)")
    ap.add_argument("--solo", help="solo gli zip il cui nome contiene questa parola")
    ap.add_argument("--fonti", action="store_true", help="scarica anche le fonti pubbliche stabili")
    ap.add_argument("--sovrascrivi", action="store_true", help="sovrascrive i file diversi gia' presenti")
    ap.add_argument("--prova", action="store_true", help="non scarica ne' scrive: dice cosa farebbe (scarica solo SHA256SUMS.txt)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    radice = Path(args.radice)
    base = args.url if args.url.endswith("/") else args.url + "/"
    tmp = Path(tempfile.mkdtemp(prefix="scarica_dati_"))
    errori = 0
    try:
        print(f"Release: {base}")
        somme_file = tmp / "SHA256SUMS.txt"
        if not scarica(base + "SHA256SUMS.txt", somme_file, "SHA256SUMS.txt"):
            print("Non riesco a leggere SHA256SUMS.txt: la Release non esiste ancora o manca la rete. Se la Release non e' stata creata, "
                  "il giro P3 (script 98) non e' ancora fatto.")
            return 1
        zips = leggi_somme(somme_file.read_text(encoding="utf-8"))
        if args.solo:
            zips = {n: h for n, h in zips.items() if args.solo in n}
        if not zips:
            print("Nessuno zip nell'elenco.")
            return 1
        tot = [0, 0, 0, 0]
        for nome, hash_atteso in zips.items():
            print(f"\n{nome}")
            if args.prova:
                print("  (prova: non scarico)")
                continue
            dest = tmp / nome
            if not scarica(base + nome, dest, nome):
                errori += 1
                continue
            if sha256_file(dest) != hash_atteso:
                print(f"  [ERRORE] hash dello zip diverso da SHA256SUMS.txt: scarto {nome}")
                dest.unlink()
                errori += 1
                continue
            print("  hash dello zip OK")
            r = estrai_zip(dest, radice, args.sovrascrivi, False)
            tot = [a + b for a, b in zip(tot, r)]
            print(f"  file scritti {r[0]}, gia' uguali {r[1]}, diversi non sovrascritti {r[2]}, rifiutati {r[3]}")
            errori += r[3]
            dest.unlink()
        if not args.prova:
            print(f"\nTotale: scritti {tot[0]}, gia' uguali {tot[1]}, diversi non sovrascritti {tot[2]}, rifiutati {tot[3]}")
        if args.fonti and not args.prova:
            raw = radice / "data" / "raw"
            raw.mkdir(parents=True, exist_ok=True)
            for nome, url in FONTI_PUBBLICHE:
                if any(raw.glob(nome.replace(".zip", "") + "*.zip")):
                    print(f"fonte {nome}: gia' presente")
                    continue
                if scarica(url, raw / nome, nome):
                    print(f"fonte {nome}: scaricata in data/raw/")
                else:
                    errori += 1
        print("\nDa fare a mano (licenza non chiara, non sono nella Release):")
        for nome, url, cosa in A_MANO:
            print(f"  - {nome}: {url}\n    {cosa}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
