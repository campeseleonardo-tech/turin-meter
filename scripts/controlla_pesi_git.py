#!/usr/bin/env python3
"""
controlla_pesi_git.py  -  i file che stanno in git (o che `git add -A` aggiungerebbe) sono abbastanza piccoli?

Regole (piano 2, passo 5): nessun file sopra 50 MB (ERRORE: GitHub rifiuta oltre 100 MB e avvisa sopra 50), peso totale sotto 300 MB
(ERRORE), file fra 5 e 50 MB = AVVISO (di solito vanno nella Release: vedi sviluppo/note_tecniche/DATI.md e scripts/96_inventario_dati.py).
Conta i file tracciati piu' quelli nuovi non ignorati; non legge .git. Non modifica niente.

Uso: python scripts/controlla_pesi_git.py        Codice di uscita 0 = nessun errore (gli AVVISO non fermano).
"""
import subprocess
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
MAX_FILE = 50 * 1024 * 1024
MAX_TOTALE = 300 * 1024 * 1024
AVVISO_FILE = 5 * 1024 * 1024


def file_in_git(radice=RADICE):
    """Percorsi (relativi) dei file tracciati piu' i nuovi non ignorati."""
    def elenco(*args):
        out = subprocess.run(["git", *args, "-z"], cwd=str(radice), capture_output=True, check=True).stdout.decode("utf-8", "replace")
        return [x for x in out.split("\0") if x]
    return sorted(set(elenco("ls-files")) | set(elenco("ls-files", "--others", "--exclude-standard")))


def controlla(radice=RADICE):
    """(errori, avvisi, totale in byte, numero di file)"""
    errori, avvisi, totale, n = [], [], 0, 0
    for rel in file_in_git(radice):
        p = Path(radice) / rel
        if not p.is_file():
            continue          # tracciato ma cancellato dal disco
        peso = p.stat().st_size
        totale += peso
        n += 1
        if peso >= MAX_FILE:
            errori.append(f"{rel}: {peso / 1e6:.1f} MB (limite 50 MB per file)")
        elif peso >= AVVISO_FILE:
            avvisi.append(f"{rel}: {peso / 1e6:.1f} MB (sopra 5 MB: Release?)")
    if totale >= MAX_TOTALE:
        errori.append(f"totale in git: {totale / 1e6:.0f} MB (limite 300 MB)")
    return errori, avvisi, totale, n


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        errori, avvisi, totale, n = controlla()
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"controllo non possibile (git non risponde): {e}")
        return 1
    print(f"file in git (tracciati + nuovi non ignorati): {n}, totale {totale / 1e6:.1f} MB")
    for a in avvisi:
        print("  AVVISO", a)
    for e in errori:
        print("  ERRORE", e)
    print("OK: pesi nei limiti" if not errori else "ERRORI: guarda sopra")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
