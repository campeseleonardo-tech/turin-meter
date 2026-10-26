#!/usr/bin/env python3
"""Controllo completo: gli stessi passi di .github/workflows/controllo.yml (il controllo di GitHub), nello stesso ordine, in locale.

Da lanciare alla fine di ogni giro, non solo prova_pagine.py: se qui e' tutto verde, lo e' anche il controllo di GitHub
(salvo i dati che sul PC ci sono e su GitHub no: per questo le prove su dati finti devono girare anche senza file derivati da IMQ).

  python scripts\\controllo_completo.py            tutti i passi, prova delle pagine compresa
  python scripts\\controllo_completo.py --veloce   senza la prova delle pagine nel browser (l'ultimo passo)

Se il file del controllo di GitHub cambia, cambiare anche l'elenco PASSI qui sotto (l'ordine e' lo stesso).
Si ferma con codice 1 se un passo fallisce, ma li esegue tutti, cosi' si vedono tutti i problemi insieme."""
import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
PY = sys.executable
S = "scripts/"
# (nome, comandi): ogni comando e' una lista di argomenti; i passi con piu' comandi si fermano al primo che fallisce
PASSI = [
    ("Gli script si compilano", [[PY, "-m", "compileall", "-q", "scripts"]]),
    ("pyflakes (nessuna segnalazione)", [[PY, "-m", "pyflakes", "scripts"]]),
    ("Prove su dati finti", [[PY, S + "prove/prova_traduzione.py"], [PY, S + "prove/prova_contenuto.py"], [PY, S + "prove/prova_funzioni_comuni.py"], [PY, S + "comuni.py"],
                            [PY, S + "prove/prova_riassunti.py"], [PY, S + "prove/prova_gtfs_archivio.py"], [PY, S + "prove/prova_gtfs_per_giorno.py"],
                            [PY, S + "prove/prova_capolinea.py"], [PY, S + "backup_da_leopi.py", "--prova"],
                            [PY, S + "99_area_tempi.py", "--finto"], [PY, S + "rifai_tutto.py", "--prova-secca"], [PY, S + "schede_risultati.py"]]),
    ("Pesi dei file in git", [[PY, S + "controlla_pesi_git.py"]]),
    ("File e link delle pagine", [[PY, S + "86_controlla_file_pagine.py", "--ci"]]),
]
PROVA_PAGINE = ("Prova delle pagine nel browser", [[PY, S + "prova_pagine.py", "--playwright", "--senza-screenshot"]])
# «Le schede in git sono quelle che escono dai dati»: dopo schede_risultati.py questi file non devono cambiare (salvo le righe «generato» e «Aggiornato al»)
FILE_SCHEDE = ["data/schede_risultati.js", "README.md"]
IGNORA = re.compile(r"generato|Aggiornato al")


def stato_schede():
    """Testo dei file delle schede, senza le righe che cambiano a ogni lancio."""
    out = {}
    percorsi = [RADICE / f for f in FILE_SCHEDE] + sorted((RADICE / "r").glob("*.html"))
    for p in percorsi:
        if p.is_file():
            out[p.name] = [r for r in p.read_text(encoding="utf-8").splitlines() if not IGNORA.search(r)]
    return out


def esegui(comandi):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for c in comandi:
        r = subprocess.run(c, cwd=RADICE, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            coda = "\n".join((r.stdout + r.stderr).strip().splitlines()[-15:])
            return False, f"{' '.join(Path(x).name if i else 'python' for i, x in enumerate(c))}: codice {r.returncode}\n{coda}"
    return True, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--veloce", action="store_true", help="senza la prova delle pagine nel browser")
    args = ap.parse_args()
    passi = PASSI + ([] if args.veloce else [PROVA_PAGINE])
    prima = stato_schede()
    esiti = []
    for nome, comandi in passi:
        t0 = time.time()
        ok, msg = esegui(comandi)
        esiti.append((nome, ok, msg))
        print(f"  {'OK    ' if ok else 'ERRORE'} {nome} ({time.time() - t0:.0f} s)", flush=True)
        if nome == "Prove su dati finti":
            dopo = stato_schede()
            diversi = [n for n in sorted(set(prima) | set(dopo)) if prima.get(n) != dopo.get(n)]
            ok2 = not diversi
            esiti.append(("Le schede in git sono quelle che escono dai dati", ok2, "cambiati dopo schede_risultati.py: " + ", ".join(diversi)))
            print(f"  {'OK    ' if ok2 else 'ERRORE'} Le schede in git sono quelle che escono dai dati", flush=True)
    guasti = [e for e in esiti if not e[1]]
    for nome, _ok, msg in guasti:
        print(f"\n--- {nome}\n{msg}")
    print("\nCONTROLLO COMPLETO: " + ("TUTTO VERDE" if not guasti else f"{len(guasti)} PASSI ROSSI"))
    return 1 if guasti else 0


if __name__ == "__main__":
    sys.exit(main())
