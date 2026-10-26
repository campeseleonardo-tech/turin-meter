#!/usr/bin/env python3
"""
98_prepara_release.py  -  prepara gli zip per la Release di GitHub (i dati grandi che non stanno in git).

Sola lettura su data/. Usa le stesse regole dell'inventario (script 96, decisioni in sviluppo/note_tecniche/DATI.md): entrano negli zip i file con posto «Release»
(data/raw/ tranne IMQ e OMI, file calcolati sopra 5 MB, ecc.); NON entrano i file «git», «riassunto», «fonte» (IMQ, OMI) e «fuori».

Cosa scrive (in una cartella FUORI da git, default <cartella del progetto>_release accanto al progetto):
  dati-grezzi-istat-AAAA-MM.zip, dati-grezzi-altri-AAAA-MM.zip, dati-calcolati-AAAA-MM.zip   (se un gruppo supera 1,9 GB si divide: -1, -2)
    dentro: i file con il loro percorso (data/...), ELENCO.txt (nome, peso, hash) e SHA256SUMS (formato «hash  percorso»)
  SHA256SUMS.txt       hash di ogni zip: lo legge scripts/scarica_dati.py per controllare gli zip scaricati
  LEGGIMI_RELEASE.txt  cosa caricare e come

Come si lancia
--------------
  python scripts/98_prepara_release.py                  sui dati veri
  python scripts/98_prepara_release.py --prova          dati finti (cartella temporanea)
  opzioni: --data CARTELLA  --out CARTELLA  --tag AAAA-MM  --solo GRUPPO (istat, altri, calcolati)

Poi, a mano: GitHub -> Releases -> Draft a new release -> tag dati-AAAA-MM -> trascina gli zip E SHA256SUMS.txt -> Publish.
"""
import argparse
import hashlib
import re
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402

RADICE = comuni.RADICE
MAX_ZIP = int(1.9 * 1024 ** 3)       # GitHub: file di una Release fino a 2 GB
BLOCCO = 1024 * 1024
# PDF e pagine salvate non sono dati aperti (rapporti di GTT, report IMQ): si citano, non si ridistribuiscono (decisione di Leo 26/10)
NON_DATI_APERTI = re.compile(r"\.(pdf|html?)$", re.I)


def gruppo_di(rel):
    parti = Path(rel).parts
    if parti[0] == "raw":
        return "istat" if len(parti) > 2 and parti[1].lower() == "istat" else "altri"
    return "calcolati"


NOMI = {"istat": "dati-grezzi-istat", "altri": "dati-grezzi-altri", "calcolati": "dati-calcolati"}


def dividi(file_peso, limite):
    """Divide [(rel, peso)] in parti, ciascuna sotto il limite (peso non compresso: prudente)."""
    parti, corrente, tot = [], [], 0
    for rel, peso in sorted(file_peso):
        if corrente and tot + peso > limite:
            parti.append(corrente)
            corrente, tot = [], 0
        corrente.append((rel, peso))
        tot += peso
    if corrente:
        parti.append(corrente)
    return parti


def sha256_file(percorso):
    h = hashlib.sha256()
    with open(percorso, "rb") as f:
        while True:
            b = f.read(BLOCCO)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def scrivi_zip(percorso_zip, data, voci):
    """voci = [(rel, peso)] relativi a data/. Ritorna l'elenco (rel, peso, sha256)."""
    elenco = []
    with zipfile.ZipFile(percorso_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for rel, peso in voci:
            src = Path(data) / rel
            h = hashlib.sha256()
            zi = zipfile.ZipInfo("data/" + rel, date_time=datetime.fromtimestamp(src.stat().st_mtime).timetuple()[:6])
            zi.compress_type = zipfile.ZIP_DEFLATED
            with open(src, "rb") as f, z.open(zi, "w", force_zip64=True) as dest:
                while True:
                    b = f.read(BLOCCO)
                    if not b:
                        break
                    h.update(b)
                    dest.write(b)
            elenco.append((rel, peso, h.hexdigest()))
        z.writestr("ELENCO.txt", "\n".join(f"data/{r}\t{p}\t{h}" for r, p, h in elenco) + "\n")
        z.writestr("SHA256SUMS", "\n".join(f"{h}  data/{r}" for r, _p, h in elenco) + "\n")
    return elenco


def main():
    ap = argparse.ArgumentParser(description="Prepara gli zip della Release (sola lettura su data/)")
    ap.add_argument("--data")
    ap.add_argument("--out")
    ap.add_argument("--tag", default=datetime.now().strftime("%Y-%m"))
    ap.add_argument("--solo", choices=tuple(NOMI))
    ap.add_argument("--prova", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    inv = comuni.carica_script("96_inventario_dati.py")
    c = comuni.Controlli()
    if args.prova:
        tmp = Path(tempfile.mkdtemp(prefix="release_prova_"))
        data = tmp / "data"
        data.mkdir()
        inv.crea_dati_finti(data)
        out = Path(args.out) if args.out else tmp / "release"
        print(f"PROVA: dati finti in {data}")
    else:
        data = Path(args.data) if args.data else RADICE / "data"
        out = Path(args.out) if args.out else RADICE.parent / (RADICE.name + "_release")
    if not data.is_dir():
        sys.exit(f"ERRORE: non trovo {data}. Sul PC lancia lo script dal progetto; nel cloud usa --prova.")
    if out.resolve().is_relative_to(RADICE.resolve()) and not args.prova:
        sys.exit(f"ERRORE: la cartella di uscita {out} sta dentro il progetto: scegline una fuori da git (--out).")
    out.mkdir(parents=True, exist_ok=True)

    righe = inv.inventario(data, inv.carica_codice(RADICE, Path(inv.__file__).name))
    release = [(r["rel"], r["peso"]) for r in righe if r["posto"] == "Release" and (data / r["rel"]).is_file() and not NON_DATI_APERTI.search(r["rel"])]
    c("ci sono file per la Release", len(release) > 0, bloccante=True)
    tolti = [r["rel"] for r in righe if r["posto"] == "Release" and NON_DATI_APERTI.search(r["rel"])]
    print(f"PDF e pagine salvate tolti dalla Release: {len(tolti)}" + (f" ({', '.join(tolti)})" if tolti else ""))
    c("nessun PDF o pagina salvata nella Release", not any(NON_DATI_APERTI.search(r) for r, _p in release))
    esclusi = {p: sum(1 for r in righe if r["posto"] == p) for p in ("git", "riassunto", "fonte", "fuori")}
    print(f"Release: {len(release)} file, {sum(p for _r, p in release) / 1e6:.0f} MB non compressi. Non inclusi: {esclusi}")
    c("nessun file «fonte» (IMQ, OMI) nella Release", not any(r["posto"] == "fonte" and (r["rel"], r["peso"]) in release for r in righe))

    gruppi = {}
    for rel, peso in release:
        gruppi.setdefault(gruppo_di(rel), []).append((rel, peso))
    sums, tutti = [], []
    for g in NOMI:
        if g not in gruppi or (args.solo and args.solo != g):
            continue
        parti = dividi(gruppi[g], MAX_ZIP)
        for i, voci in enumerate(parti, 1):
            nome = f"{NOMI[g]}-{args.tag}" + (f"-{i}" if len(parti) > 1 else "") + ".zip"
            percorso = out / nome
            print(f"  scrivo {nome} ({len(voci)} file)...", flush=True)
            elenco = scrivi_zip(percorso, data, voci)
            peso_zip = percorso.stat().st_size
            c(f"{nome}: sotto 1,9 GB ({peso_zip / 1e6:.0f} MB)", peso_zip < MAX_ZIP)
            with zipfile.ZipFile(percorso) as z:
                c(f"{nome}: lo zip si apre e ha ELENCO.txt, SHA256SUMS e {len(elenco)} file", z.testzip() is None and "ELENCO.txt" in z.namelist()
                  and "SHA256SUMS" in z.namelist() and len(z.namelist()) == len(elenco) + 2)
            sums.append(f"{sha256_file(percorso)}  {nome}")
            tutti.append((nome, peso_zip, len(elenco)))
    (out / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    (out / "LEGGIMI_RELEASE.txt").write_text(
        f"Release dati-{args.tag}\n\nCarica su GitHub (Releases -> Draft a new release, tag dati-{args.tag}) TUTTI i file di questa cartella:\n"
        + "\n".join(f"  {n}  ({p / 1e6:.0f} MB, {k} file)" for n, p, k in tutti)
        + "\n  SHA256SUMS.txt\n\nPoi sul PC pulito: python scripts/scarica_dati.py\n", encoding="utf-8")
    print("\nCartella:", out)
    for n, p, k in tutti:
        print(f"  {n:46s} {p / 1e6:9.1f} MB  {k} file")
    print(f"  {'SHA256SUMS.txt':46s} (hash degli zip)")
    print(f"avvisi: {len(c.avvisi())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
