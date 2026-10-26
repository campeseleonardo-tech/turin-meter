#!/usr/bin/env python3
"""Prova delle versioni inglese e tedesca delle schede: ogni frase di data/schede_risultati.js (forma) ha la sua traduzione inglese in scripts/schede/testi.json,
nessuna frase inglese ha segnaposto rimasti, nessun numero inglese resta nel formato italiano (1.234,5) e ogni scheda ha forma_en e forma_de con la stessa struttura.
Il tedesco puo' restare in inglese dove manca la frase tedesca (le aggiunge F4), ma non deve avere segnaposto rimasti e deve coincidere con quello rifatto.
Uso: python scripts/prove/prova_traduzione.py        Codice di uscita 0 = tutto a posto."""
import json
import re
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RADICE / "scripts"))
from schede.traduci import traduci_forma  # noqa: E402


def stringhe(o, out):
    if isinstance(o, str):
        out.append(o)
    elif isinstance(o, list):
        [stringhe(x, out) for x in o]
    elif isinstance(o, dict):
        [stringhe(v, out) for k, v in o.items() if k not in ("mappa", "tipo", "tono", "link", "id", "vista")]


def struttura(o):
    if isinstance(o, dict):
        return {k: struttura(v) for k, v in o.items()}
    if isinstance(o, list):
        return [struttura(x) for x in o]
    return type(o).__name__ if not isinstance(o, str) else "s"


def main():
    t = (RADICE / "data" / "schede_risultati.js").read_text(encoding="utf-8")
    schede = json.loads(t[t.index("["):t.rindex("]") + 1])
    problemi = []
    for s in schede:
        if "forma" not in s:
            continue
        nome = "R" + s["risultato"]
        if "forma_en" not in s:
            problemi.append(f"{nome}: manca forma_en")
            continue
        man = []
        rifatta = traduci_forma(s["forma"], "en", man)
        if man:
            problemi.append(f"{nome}: frasi senza traduzione: {man[:3]}")
        if rifatta != s["forma_en"]:
            problemi.append(f"{nome}: forma_en nel file diversa da quella rifatta: rilancia scripts/schede_risultati.py")
        if "forma_de" not in s:
            problemi.append(f"{nome}: manca forma_de")
        else:
            if traduci_forma(s["forma"], "de", []) != s["forma_de"]:
                problemi.append(f"{nome}: forma_de nel file diversa da quella rifatta: rilancia scripts/schede_risultati.py")
            if struttura(s["forma"]) != struttura(s["forma_de"]) and {k: v for k, v in struttura(s["forma"]).items() if k != "english"} != struttura(s["forma_de"]):
                problemi.append(f"{nome}: la forma tedesca ha una struttura diversa")
            tedeschi = []
            stringhe(s["forma_de"], tedeschi)
            for x in tedeschi:
                if re.search(r"\{[nspwta]\d\}", x):
                    problemi.append(f"{nome}: segnaposto rimasto in «{x[:60]}» (tedesco)")
        fi, fe = s["forma"], s["forma_en"]
        if {k: v for k, v in struttura(fi).items() if k != "english"} != struttura(fe):
            problemi.append(f"{nome}: la forma inglese ha una struttura diversa")
        testi = []
        stringhe(fe, testi)
        for x in testi:
            if re.search(r"\{[nspwta]\d\}", x):
                problemi.append(f"{nome}: segnaposto rimasto in «{x[:60]}»")
            if re.search(r"\d\.\d{3}(?!\d)|\d+,\d(?!\d)", x) and not re.search(r"\d,\d{3}", x) and not re.search(r"per litre|per km", x):   # i prezzi dei carburanti hanno tre decimali anche in inglese
                problemi.append(f"{nome}: numero in formato italiano in «{x[:60]}»")
    for x in problemi:
        print("PROBLEMA:", x)
    print(f"{len([s for s in schede if 'forma' in s])} schede controllate:", "OK" if not problemi else "CI SONO PROBLEMI")
    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())
