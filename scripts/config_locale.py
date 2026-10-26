"""Legge config_locale.json (nella radice del progetto, NON in git): dati di accesso al Raspberry Pi.

Si crea copiando scripts/config_locale.esempio.json in config_locale.json e mettendo i valori veri.
Dai .bat:  for /f "delims=" %%a in ('python scripts\\config_locale.py pi') do set "PI=%%a"
Chiavi che stampa: pi (utente@indirizzo), utente, indirizzo, chiave (percorso completo), dir_remota (/home/<utente>/GTT).
"""
import json
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
FILE = RADICE / "config_locale.json"
CAMPI = ("pi_utente", "pi_indirizzo", "chiave_ssh")


def messaggio_mancante(dettaglio):
    return (f"{dettaglio}\n"
            f"Crea il file {FILE.name} nella cartella del progetto: copia scripts/config_locale.esempio.json "
            f"in {FILE.name} e scrivi i valori veri (utente e indirizzo del Raspberry Pi di casa, percorso "
            f"della chiave SSH). Il file non va in git.")


def carica():
    """Restituisce un dizionario con utente, indirizzo, pi, chiave, dir_remota; si ferma con un messaggio chiaro."""
    if not FILE.exists():
        sys.exit(messaggio_mancante(f"ERRORE: manca {FILE}."))
    try:
        c = json.loads(FILE.read_text(encoding="utf-8"))
    except ValueError as e:
        sys.exit(messaggio_mancante(f"ERRORE: {FILE.name} non e' un JSON valido ({e})."))
    mancanti = [k for k in CAMPI if not str(c.get(k, "")).strip()]
    if mancanti:
        sys.exit(messaggio_mancante(f"ERRORE: in {FILE.name} mancano i campi: {', '.join(mancanti)}."))
    utente, indirizzo = c["pi_utente"].strip(), c["pi_indirizzo"].strip()
    return {
        "utente": utente,
        "indirizzo": indirizzo,
        "pi": f"{utente}@{indirizzo}",
        "chiave": str(Path(c["chiave_ssh"]).expanduser()),
        "dir_remota": f"/home/{utente}/GTT",
    }


def metti_chiavi_mappa(html):
    """Scrive nella pagina della mappa le chiavi da browser degli sfondi (carto_chiave, arcgis_chiave di config_locale.json).
    Sono chiavi limitate al dominio del sito. Se il file o il campo manca, la chiave resta vuota e quello sfondo non compare.
    Non stampa mai le chiavi."""
    try:
        c = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        c = {}
    for segnaposto, campo in (("__CARTO_CHIAVE__", "carto_chiave"), ("__ARCGIS_CHIAVE__", "arcgis_chiave")):
        valore = str(c.get(campo, "")).strip()
        html = html.replace(f'"{segnaposto}"', json.dumps(valore))
    return html


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("uso: python scripts/config_locale.py pi|utente|indirizzo|chiave|dir_remota")
    cfg = carica()
    if sys.argv[1] not in cfg:
        sys.exit(f"chiave sconosciuta: {sys.argv[1]}")
    print(cfg[sys.argv[1]])
