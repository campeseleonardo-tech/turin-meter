#!/usr/bin/env python3
"""
confronta_riassunti.py  -  sul PC di Leo: i riassunti dello storico danno gli stessi numeri dello storico vero?

Lancia gli script 27, 70, 26 e 71 due volte: la prima dallo storico SQLite, la seconda con --riassunti (dai riassunti dello script 97), copia ogni volta
i loro JSON e rapporti, e li confronta (tolleranza 0,011 sui numeri; le righe che nominano la sorgente e i campi «generato» si ignorano).
Alla fine i file in data/processed e docs/rapporti sono quelli della seconda esecuzione (uguali ai primi, se il confronto e' OK).
Ci vogliono alcuni minuti (il 27 e il 70 sono lenti). Prima serve lo script 97.

Uso: python scripts/confronta_riassunti.py [--senza-70]      Codice di uscita 0 = tutto uguale.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RADICE = AQUI.parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI / "prove"))
import comuni  # noqa: E402
import prova_riassunti as pr  # noqa: E402  (funzioni di confronto)

PROCESSED = RADICE / "data" / "processed"
RAPPORTI = RADICE / "docs" / "rapporti"
SCRIPT = [
    ("27_risultato4_regolarita.py", [PROCESSED / "risultato4_regolarita.json", RAPPORTI / "RAPPORTO_RISULTATO4.txt"]),
    ("70_risultato9_attesa.py", [PROCESSED / "risultato9_attesa.json", RAPPORTI / "RAPPORTO_RISULTATO9_ATTESA.txt"]),
    ("26_velocita_5t.py", [PROCESSED / "velocita_5t.json", RAPPORTI / "RAPPORTO_VELOCITA_5T.txt"]),
    ("71_parcheggi_riempimento.py", [PROCESSED / "risultato6_v2" / "riempimento.json", RAPPORTI / "RAPPORTO_R6V2_RIEMPIMENTO.txt"]),
]


def lancia(nome, extra, copia_in):
    print(f"  python scripts/{nome} {' '.join(extra)}", flush=True)
    r = subprocess.run([sys.executable, str(AQUI / nome), *extra], cwd=str(RADICE), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stdout[-1500:], r.stderr[-1500:])
        sys.exit(f"ERRORE: {nome} si e' fermato")
    for p in dict(SCRIPT)[nome]:
        shutil.copy2(p, copia_in / p.name)
    return r.stderr


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    senza_70 = "--senza-70" in sys.argv[1:]
    c = comuni.Controlli()
    if not (RADICE / "data" / "storico_backup.sqlite").exists():
        sys.exit("ERRORE: manca data/storico_backup.sqlite: questo confronto serve sul PC con lo storico vero.")
    if not (RADICE / "data" / "storico_riassunti").exists():
        sys.exit("ERRORE: mancano i riassunti: lancia prima scripts/97_riassunti_storico.py")
    tmp = Path(tempfile.mkdtemp(prefix="confronto_riassunti_"))
    cartelle = {"A": tmp / "storico", "B": tmp / "riassunti"}
    for p in cartelle.values():
        p.mkdir()
    script = [s for s in SCRIPT if not (senza_70 and s[0].startswith("70_"))]
    for etichetta, extra in (("A", []), ("B", ["--riassunti"])):
        print(f"\n[{etichetta}] {'dallo storico' if etichetta == 'A' else 'dai riassunti'}")
        for nome, _ in script:
            err = lancia(nome, extra, cartelle[etichetta])
            if etichetta == "B":
                c(f"{nome}: ha letto i riassunti", "riassunti" in err or nome.startswith(("26", "71")))
    for nome, files in script:
        for p in files:
            a, b = cartelle["A"] / p.name, cartelle["B"] / p.name
            if p.suffix == ".json":
                ja, jb = pr.senza_generato(json.loads(a.read_text(encoding="utf-8"))), pr.senza_generato(json.loads(b.read_text(encoding="utf-8")))
                diff, massimo = [], [0.0]
                pr.confronta(ja, jb, "", diff, massimo)
                c(f"{p.name}: storico = riassunti (differenza massima {massimo[0]:.6f})", not diff, dettaglio="; ".join(diff[:4]))
            else:
                la, lb = pr.righe_rapporto(a.read_text(encoding="utf-8")), pr.righe_rapporto(b.read_text(encoding="utf-8"))
                diffs = [(x, y) for x, y in zip(la, lb) if x != y]
                c(f"{p.name}: stesse righe ({len(la)} contro {len(lb)})", len(la) == len(lb) and not diffs,
                  dettaglio=" | ".join(f"«{x[:60]}» ≠ «{y[:60]}»" for x, y in diffs[:3]))
    print(f"\nCopie dei due giri in {tmp}\navvisi: {len(c.avvisi())}")
    return 0 if not c.avvisi() else 1


if __name__ == "__main__":
    sys.exit(main())
