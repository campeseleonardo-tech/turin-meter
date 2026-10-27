#!/usr/bin/env python3
"""
rifai_mappa_da_html.py  -  rifà la mappa col modello nuovo, senza i dati grezzi

Prende i dati (la riga «const DATI = ...») dalla mappa attuale, di solito mappa_torino.html, e li mette nel modello
scripts/mappa_template.html: così si prova il modello nuovo (lingue, temi, sfondi) anche dove non ci sono i dati
grezzi dello script 04, per esempio nel cloud. Le chiavi degli sfondi si leggono da config_locale.json, se c'è
(senza, gli sfondi con chiave non compaiono). La mappa vera si rifà con lo script 04.

Uso:
    python scripts/rifai_mappa_da_html.py                        # rifà mappa_torino.html sul posto
    python scripts/rifai_mappa_da_html.py --da vecchia.html --a nuova.html
"""
import argparse
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RADICE = AQUI.parent
sys.path.insert(0, str(AQUI))
import config_locale  # noqa: E402
from schede.r6 import fattori_auto_mappa  # noqa: E402

INIZIO = "const DATI = "


def leggi_dati(percorso):
    """Il dizionario scritto nella riga «const DATI = {...};» della mappa."""
    for riga in percorso.read_text(encoding="utf-8").split("\n"):
        if riga.startswith(INIZIO):
            return json.loads(riga[len(INIZIO):].rstrip().rstrip(";"))
    sys.exit(f"ERRORE: in {percorso} non c'è la riga «{INIZIO}…»: non è una mappa di Turin Meter.")


def rifai(da, a, modello):
    dati = leggi_dati(da)
    if dati.get("r6"):
        dati["r6"].update(fattori_auto_mappa())      # tempi in auto: una sola stima, la corretta col controllo (decisione 16 di §2)
    testo = json.dumps(dati, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html = modello.read_text(encoding="utf-8").replace('"__DATI__"', testo)
    html = config_locale.metti_chiavi_mappa(html)
    a.write_text(html, encoding="utf-8")
    return dati


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--da", type=Path, default=RADICE / "mappa_torino.html", help="mappa da cui leggere i dati")
    ap.add_argument("--a", type=Path, default=None, help="file da scrivere (predefinito: lo stesso di --da)")
    ap.add_argument("--modello", type=Path, default=AQUI / "mappa_template.html")
    arg = ap.parse_args()
    uscita = arg.a or arg.da
    dati = rifai(arg.da, uscita, arg.modello)
    print(f"Mappa rifatta: {uscita}  ({uscita.stat().st_size / 1e6:.1f} MB, {len(dati)} gruppi di dati)")
    if "ritardi_tratti" not in dati:
        print("  Nota: nei dati non ci sono i tratti dove i bus perdono tempo (script 106 e 04): quel tema non compare.")


if __name__ == "__main__":
    main()
