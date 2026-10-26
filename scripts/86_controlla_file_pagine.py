#!/usr/bin/env python3
"""
86_controlla_file_pagine.py  -  ogni file caricato dalle pagine esiste ed è in git?

Legge index.html, mappa_torino.html e progetto.html e elenca tutti i file che caricano (script src, fetch,
caricamenti dinamici della mappa, gruppi di data/catalogo/, immagini, pagine collegate). Per ognuno dice se esiste sul
disco e se è salvato in git (se no, GitHub Pages non lo pubblica e la pagina funziona male). Manca o non è in git = AVVISO.
Non scrive niente e non crea cartelle: è solo un controllo.

Come si lancia:  python scripts/86_controlla_file_pagine.py          (con --ci esce con 1 se manca un file: lo usa il controllo automatico su GitHub)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402

RADICE = comuni.RADICE
PAGINE = ["index.html", "mappa_torino.html", "progetto.html"]
# file che una pagina carica da JavaScript con un indirizzo costruito (non si trovano leggendo la pagina)
CARICATI_DA_SCRIPT = {"index.html": ["data/area_tempi.js"]}   # assets/area.js, scheda 4; manca finche' non gira lo script 99
URL = re.compile(r"^(https?:)?//|^data:|^mailto:|^#|^javascript:", re.I)

RE_SRC = re.compile(r"""<(?:script|img|link)\b[^>]*?\b(?:src|href)\s*=\s*["']([^"']+)["']""", re.I)
RE_A = re.compile(r"""<a\b[^>]*?\bhref\s*=\s*["']([^"'#]+\.html)(?:#[^"']*)?["']""", re.I)
RE_FETCH = re.compile(r"""fetch\(\s*["'`]([^"'`$]+)["'`]""")
RE_RICARICA = re.compile(r"""\bricarica\(\s*["']([^"']+)["']""")      # la mappa carica data/<nome>


def pulito(rif):
    return rif.split("?")[0].split("#")[0].strip()


def file_citati(pagina, testo):
    """Elenco ordinato (senza doppioni) dei file locali che la pagina carica."""
    trovati = []

    def aggiungi(rif, prefisso=""):
        rif = pulito(prefisso + rif)
        if rif and "${" not in rif and not URL.match(rif) and rif not in trovati:   # «${...}» = indirizzo costruito dal JavaScript: non si controlla
            trovati.append(rif)

    for rx in (RE_SRC, RE_A, RE_FETCH):
        for m in rx.finditer(testo):
            aggiungi(m.group(1))
    for m in RE_RICARICA.finditer(testo):
        if m.group(1).startswith("catalogo/"):
            continue   # si espande sotto con i gruppi veri
        aggiungi(m.group(1), "data/")
    if pagina == "mappa_torino.html":
        # «Luoghi della città» carica data/catalogo/<gruppo>.js per ogni gruppo di D.catalogo
        riga = next((x for x in testo.split("\n") if x.startswith("const DATI = ")), None)
        gruppi = []
        if riga:
            try:
                gruppi = [g["id"] for g in json.loads(riga[len("const DATI = "):].rstrip(";")).get("catalogo", {}).get("gruppi", [])]
            except (ValueError, AttributeError, KeyError):
                gruppi = []
        for g in gruppi:
            aggiungi(f"catalogo/{g}.js", "data/")
    for rel in CARICATI_DA_SCRIPT.get(pagina, []):
        aggiungi(rel)
    return trovati


def in_git(rel):
    try:
        out = subprocess.run(["git", "ls-files", "--", rel], cwd=str(RADICE), capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(out.strip())


OPZIONALI = {"data/area_tempi.js"}     # con --ci non e' un errore se manca (compare dopo lo script 99)


def main():
    ci = "--ci" in sys.argv     # per il controllo automatico su GitHub: esce con 1 se manca un file o un link interno (salvo gli opzionali)
    c = comuni.Controlli()
    mancanti = 0
    gravi = []
    for pagina in PAGINE:
        p = RADICE / pagina
        c(f"esiste {pagina}", p.exists(), bloccante=True)
        print(f"\n{pagina}")
        for rel in file_citati(pagina, p.read_text(encoding="utf-8")):
            esiste = (RADICE / rel).exists()
            git = in_git(rel) if esiste else False
            if git is None:
                c(f"{pagina} -> {rel}: esiste, ma git non risponde (non so se è salvato)", esiste)
                continue
            ok = esiste and git
            mancanti += 0 if ok else 1
            if not ok and rel not in OPZIONALI:
                gravi.append(f"{pagina} -> {rel}: {'manca' if not esiste else 'non e\' in git'}")
            c(f"{pagina} -> {rel}: {'esiste' if esiste else 'MANCA'}, {'in git' if git else 'NON in git'}", ok)
    print(f"\nFile da guardare: {mancanti}; avvisi: {len(c.avvisi())}")
    if ci and gravi:
        print("ERRORI (--ci):\n  " + "\n  ".join(gravi))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
