#!/usr/bin/env python3
"""
96_inventario_dati.py  -  inventario dei dati: ogni file di data/, chi lo legge, chi lo scrive, dove dovrebbe stare.

SOLA LETTURA: non modifica, non sposta e non cancella nessun dato. Scrive solo sviluppo/note_tecniche/DATI.md (la parte fra i due
segnaposto <!-- INVENTARIO:INIZIO --> e <!-- INVENTARIO:FINE -->; il resto del file, per esempio le decisioni di Leo, resta com'e').

Cosa fa
-------
  1. Elenca ogni file sotto data/ con il peso.
  2. Cerca il nome del file (e, se non basta, il nome delle cartelle che lo contengono e il nome senza estensione)
     nel codice: scripts/*.py, .bat, .ps1, .sh, scripts/prove, scripts/mappa_template.html e le pagine
     (index.html, mappa_torino.html). Dice quali script lo LEGGONO e quali lo SCRIVONO
     (euristica sulle righe vicine: write_text, open(...,"w"), to_csv, dump, savefig, scp, copy, >).
     Una cartella citata dallo script (per es. un glob) vale per tutti i file che contiene: «via cartella».
  3. Propone un posto (e' solo una PROPOSTA: decide Leo, piano 2 passo 3):
       riassunto  lo storico (SQLite della raccolta): si tengono solo i riassunti (script 97); i riassunti stessi
                  (data/storico_riassunti/) vanno sempre in git
       Release    data/raw/ e, fuori da raw, i file da 5 MB in su che qualcuno legge (zip nella Release di GitHub)
       git        file sotto 5 MB letti da una pagina o da uno script, o scritti da uno script dei risultati
                  (sopra 5 MB solo se una pagina li carica; sopra 50 MB sempre Release: AVVISO)
       fonte      IMQ 2022 e OMI grezzi (decisione di Leo 22/10) e i file derivati che ne ricopiano le celle o le quotazioni (L12, 24/10):
                  licenza non chiara, non si pubblicano, si riscaricano dalla fonte
       fuori      nessuno script e nessuna pagina lo cita: probabilmente avanzo (non si pubblica)
     «fuori» anche: strumenti (cartelle jdk/jre), copie di sicurezza (backup, «prima_correzioni»), cache e prove (_parziale, _test).
     Zip, pdf, pbf e simili letti solo dagli script vanno in Release anche se piccoli.
     «Script dei risultati» = numeri 21-29 e 33-95 piu' schede_risultati.py; «script dei dati» = 01-20 e 30-32.
  4. Scrive sviluppo/note_tecniche/DATI.md: totali per posto, tabella per cartella, tabella per file (le cartelle con piu' di 30
     file, come data/raw/, sono raccolte in una riga) e stampa i totali.

Come si lancia
--------------
  python scripts/96_inventario_dati.py                  sui dati veri (serve data/)
  python scripts/96_inventario_dati.py --prova          cartella data/ finta (file vuoti con i pesi veri): per provarlo nel cloud;
                                                        scrive DATI_prova.md nella cartella finta, non sviluppo/note_tecniche/DATI.md
  python scripts/96_inventario_dati.py --gitignore      oltre al resto, riscrive le esclusioni di data/ nel .gitignore (fra i segnaposto
                                                        «# >>> data» e «# <<< data»): tutto cio' che l'inventario non mette in «git»
  opzioni: --data CARTELLA  --uscita FILE  --gitignore [FILE]
"""
import argparse
import os
import re
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402

RADICE = comuni.RADICE
SOGLIA_GIT = 5 * 1024 * 1024
SOGLIA_MAX = 50 * 1024 * 1024
ESTENSIONI_GREZZE = (".zip", ".pdf", ".pbf", ".gz", ".accdb", ".7z", ".xlsx")
FUORI_SE = re.compile(r"(^|/)(jdk|jre)[^/]*/|(^|/)backup[^/]*/|_prima_|prima_correzioni|_parziale|_test(/|\.|$)|(^|/)STOP_RACCOLTA|"
                      r"^(live\.js|stat\.js|agg_cache\.json|get_[a-z]+\.xml|replay_[^/]*\.js)$", re.I)
# decisioni di Leo (22/10/2026): licenza non chiara -> il file non si pubblica, si riscarica dalla fonte (docs/en/METHODS.md)
# giro L12 (24/10/2026): anche i file derivati che ricopiano la fonte (celle IMQ, quotazioni OMI) restano fuori da git: processed/imq_*.json, omi_zone.json
# e le matrici di domanda per coppia di zone (traffico_c/domanda_*, v3/domanda_v3.json). I risultati riassunti (schede, mappa) restano.
FONTE_SE = re.compile(r"(^|/)imq[^/]*/|(^|/)imq2022|^raw/omi|^processed/(imq_[^/]*\.json|omi_zone\.json|traffico_c/domanda_[^/]*|traffico_c/v3/domanda_v3\.json|rapporto_gtt/(blocchi/|pagine\.json))", re.I)
RAGGRUPPA_SOPRA = 30          # cartelle con piu' file di cosi' = una riga sola
CARTELLE_GENERICHE = {"data", "raw", "processed"}
INIZIO, FINE = "<!-- INVENTARIO:INIZIO -->", "<!-- INVENTARIO:FINE -->"
PAGINE = ["index.html", "mappa_torino.html"]
EST_CODICE = {".py", ".bat", ".ps1", ".sh"}
SCRIVE_PY = re.compile(r"write_text|write_bytes|\.write\(|open\([^)]*[\"'][wax]b?\+?[\"']|to_csv|to_json|to_excel|json\.dump\(|"
                       r"pickle\.dump|savefig|\.save\(|shutil\.(copy|move)|np\.save|writelines|urlretrieve|extractall|"
                       r"\.to_parquet|rename\(")
SCRIVE_BAT = re.compile(r">|\bcopy\b|\bmove\b|\bscp\b|\bxcopy\b|Out-File|Set-Content|curl|Invoke-WebRequest|wget", re.I)


def numero_script(nome):
    m = re.match(r"(\d+)", nome)
    return int(m.group(1)) if m else None


def tipo_script(nome):
    """'risultati', 'dati' o 'altro' (strumenti, comuni, supervisore, pagine...)."""
    n = numero_script(nome)
    if nome == "schede_risultati.py" or (n is not None and (21 <= n <= 29 or 33 <= n <= 95)):
        return "risultati"
    if n is not None and (1 <= n <= 20 or 30 <= n <= 32):
        return "dati"
    return "altro"


def carica_codice(radice, escludi):
    """{percorso relativo: righe} per scripts/ (anche prove/) e le pagine."""
    corpus = {}
    cartelle = [radice / "scripts", radice / "scripts" / "prove"]
    for c in cartelle:
        if not c.is_dir():
            continue
        for p in sorted(c.iterdir()):
            if p.is_file() and (p.suffix in EST_CODICE or p.name == "mappa_template.html") and p.name != escludi:
                corpus[p.relative_to(radice).as_posix()] = p.read_text(encoding="utf-8", errors="replace").splitlines()
    for nome in PAGINE:
        p = radice / nome
        if p.exists():   # la riga «const DATI = ...» della mappa e' dato incorporato (nomi di file nei metadati): non conta come lettura
            corpus[nome] = [x for x in p.read_text(encoding="utf-8", errors="replace").splitlines() if not x.startswith("const DATI = ")]
    return corpus


def e_scrittura(percorso, righe, indici):
    """True se nelle righe dove compare il nome (o nella variabile a cui e' assegnato) si scrive."""
    scrive = SCRIVE_BAT if Path(percorso).suffix in (".bat", ".ps1", ".sh") else SCRIVE_PY
    for i in indici:
        riga = righe[i]
        if scrive.search(riga):
            return True
        m = re.match(r"\s*([A-Za-z_]\w*)\s*=", riga)
        if m and Path(percorso).suffix == ".py":
            var = re.escape(m.group(1))
            rx_var = re.compile(rf"\b{var}\b")
            for j, r in enumerate(righe):
                if j != i and rx_var.search(r) and scrive.search(r):
                    return True
    return False


class Indice:
    """Cerca le chiavi (nomi) nel codice una volta sola, con cache."""

    def __init__(self, corpus):
        self.corpus = corpus
        self.testi = {p: "\n".join(r) for p, r in corpus.items()}
        self.cache = {}

    def cerca(self, chiave):
        if chiave in self.cache:
            return self.cache[chiave]
        legge, scrive = set(), set()
        for p, testo in self.testi.items():
            if chiave not in testo:
                continue
            righe = self.corpus[p]
            indici = [i for i, r in enumerate(righe) if chiave in r]
            if p in PAGINE or p.endswith("mappa_template.html"):
                legge.add(p)
            elif e_scrittura(p, righe, indici):
                scrive.add(p)
                # uno script che scrive un file puo' anche rileggerlo: lo diciamo solo se ci sono righe senza scrittura
                if any(not e_scrittura(p, righe, [i]) and not re.match(r"\s*([A-Za-z_]\w*)\s*=", righe[i]) for i in indici):
                    legge.add(p)
            else:
                legge.add(p)
        self.cache[chiave] = (legge, scrive)
        return self.cache[chiave]

    def usi_file(self, rel_data):
        """(legge, scrive, come) per un file con percorso relativo a data/."""
        parti = Path(rel_data).parts
        nome = parti[-1]
        legge, scrive = self.cerca(nome)
        if legge or scrive:
            return legge, scrive, "nome"
        chiavi = [d for d in parti[:-1] if d not in CARTELLE_GENERICHE and len(d) >= 4]
        stem = Path(nome).stem
        if len(stem) >= 8:
            chiavi.append(stem)
        for k in reversed(chiavi):     # la cartella piu' interna prima
            legge, scrive = self.cerca(k)
            if legge or scrive:
                return legge, scrive, "via " + ("cartella" if k in parti[:-1] else "nome senza estensione")
        return set(), set(), ""


def posto(rel_data, peso, legge, scrive):
    """(posto, nota) secondo le regole in testa al file."""
    nome = rel_data.lower()
    parti = Path(rel_data).parts
    if FUORI_SE.search(rel_data):
        return "fuori", "strumento (Java), copia di sicurezza, prova o cache: non e' un dato del progetto"
    if nome.endswith((".sqlite", ".sqlite3", ".db", "-wal", "-shm")):
        return "riassunto", "storico della raccolta: si tengono i riassunti (script 97)"
    if parti[0] == "catalogo" and nome.endswith(".js"):
        return "git", "la mappa lo carica quando si apre «Luoghi della città»"
    if parti[0] == "storico_riassunti":
        return "git", "riassunti dello storico (script 97): vanno in git"
    if FONTE_SE.search(rel_data):
        return "fonte", "IMQ 2022 e OMI: licenza non chiara, non si pubblica; si riscarica dalla fonte (decisione di Leo)"
    if parti[0] == "raw":
        return "Release", "dato grezzo (controllare la licenza in docs/en/METHODS.md)"
    da_pagine = any(p in PAGINE or p.endswith("mappa_template.html") for p in legge)
    da_script = any(not (p in PAGINE or p.endswith("mappa_template.html")) for p in legge)
    da_risultati = any(tipo_script(Path(p).name) == "risultati" for p in scrive)
    if nome.endswith(ESTENSIONI_GREZZE) and not da_pagine and (legge or scrive):
        return "Release", "archivio o documento grezzo (zip, pdf, pbf...): non va in git"
    if peso >= SOGLIA_MAX:
        return "Release", "oltre 50 MB: troppo grande per git" if (legge or scrive) else "oltre 50 MB e nessuno lo cita"
    if not legge and not scrive:
        return "fuori", "nessuno script e nessuna pagina lo cita: avanzo?"
    if peso < SOGLIA_GIT and (da_pagine or da_script or da_risultati):
        return "git", ""
    if da_pagine:
        return "git", "sopra 5 MB ma caricato da una pagina"
    if da_risultati and not da_script:
        return "git", "sopra 5 MB, scritto da uno script dei risultati"
    return "Release", "sopra 5 MB, letto solo dagli script"


def mb(x):
    return f"{x / 1048576:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def breve(insieme, n=4):
    nomi = sorted(Path(p).name for p in insieme)
    return ", ".join(nomi[:n]) + (f" (+{len(nomi) - n})" if len(nomi) > n else "") if nomi else "—"


def scansiona(data):
    out = []
    for dirpath, _, files in os.walk(data):
        for f in files:
            p = Path(dirpath) / f
            try:
                out.append((p.relative_to(data).as_posix(), p.stat().st_size))
            except OSError:
                pass
    return sorted(out)


def inventario(data, corpus):
    idx = Indice(corpus)
    righe = []
    for rel, peso in scansiona(data):
        legge, scrive, come = idx.usi_file(rel)
        pz, nota = posto(rel, peso, legge, scrive)
        righe.append({"rel": rel, "peso": peso, "legge": legge, "scrive": scrive, "come": come, "posto": pz, "nota": nota})
    return righe


def cartella_di(rel, profondita=2):
    parti = Path(rel).parts[:-1]
    return "/".join(parti[:profondita]) if parti else "(radice di data)"


def testo_md(righe, data_txt):
    tot = {}
    for r in righe:
        t = tot.setdefault(r["posto"], [0, 0])
        t[0] += 1
        t[1] += r["peso"]
    ordine = ["git", "Release", "riassunto", "fonte", "fuori"]
    L = [INIZIO, "",
         f"*Inventario scritto da `scripts/96_inventario_dati.py` il {datetime.now():%d/%m/%Y} sulla cartella {data_txt}. Le proposte sono automatiche (regole in testa allo script): "
         "decide Leo, fonte per fonte (piano 2, passo 3).*", "",
         "### Totali per posto", "", "| Posto | File | Peso (MB) | Cosa vuol dire |", "|---|---|---|---|"]
    spiegazione = {"git": "dentro il repository", "Release": "zip nella Release di GitHub", "riassunto": "dello storico si tengono solo i riassunti (script 97)",
                   "fonte": "non si pubblica: si riscarica dalla fonte (IMQ, OMI)", "fuori": "nessuno lo cita: non si pubblica"}
    for p in ordine:
        n, s = tot.get(p, [0, 0])
        L.append(f"| {p} | {n} | {mb(s)} | {spiegazione[p]} |")
    L.append(f"| **tutto** | {len(righe)} | {mb(sum(r['peso'] for r in righe))} | |")
    grossi = [r for r in righe if r["posto"] == "git" and r["peso"] >= SOGLIA_MAX]
    L += ["", f"Avvisi: file in «git» sopra 50 MB: {len(grossi)}.", ""]

    gruppi = {}
    for r in righe:
        gruppi.setdefault(cartella_di(r["rel"]), []).append(r)
    L += ["### Per cartella", "", "| Cartella | File | Peso (MB) | git | Release | riassunto | fonte | fuori |", "|---|---|---|---|---|---|---|---|"]
    for c, rs in sorted(gruppi.items()):
        per = {p: sum(1 for r in rs if r["posto"] == p) for p in ordine}
        L.append(f"| `data/{c}` | {len(rs)} | {mb(sum(r['peso'] for r in rs))} | {per['git']} | {per['Release']} | {per['riassunto']} | {per['fonte']} | {per['fuori']} |")
    L += ["", "### Per file", "",
          f"Le cartelle con più di {RAGGRUPPA_SOPRA} file sono in una riga sola (elenco completo: rilanciare lo script e guardare `--data`).", ""]
    for c, rs in sorted(gruppi.items()):
        L += [f"#### `data/{c}`", ""]
        if len(rs) > RAGGRUPPA_SOPRA:
            leg = set().union(*[r["legge"] for r in rs])
            scr = set().union(*[r["scrive"] for r in rs])
            posti = ", ".join(f"{p}: {sum(1 for r in rs if r['posto'] == p)}" for p in ordine if any(r["posto"] == p for r in rs))
            L += [f"{len(rs)} file, {mb(sum(r['peso'] for r in rs))} MB ({posti}). Letti da: {breve(leg, 6)}. Scritti da: {breve(scr, 6)}.", ""]
            continue
        L += ["| File | MB | Legge | Scrive | Posto | Nota |", "|---|---|---|---|---|---|"]
        for r in rs:
            nota = "; ".join(x for x in [r["nota"], r["come"]] if x)
            L.append(f"| `{Path(r['rel']).name}` | {mb(r['peso'])} | {breve(r['legge'])} | {breve(r['scrive'])} | {r['posto']} | {nota} |")
        L.append("")
    L.append(FINE)
    return "\n".join(L) + "\n", tot


GI_INIZIO = "# >>> data: esclusioni scritte da scripts/96_inventario_dati.py --gitignore (decisioni in sviluppo/note_tecniche/DATI.md)"
GI_FINE = "# <<< data"
CARTELLE_IN_GIT = ("catalogo", "processed", "ref", "scenari", "storico_riassunti")    # whitelist del .gitignore (sopra i segnaposto)


def _gi(p):
    """Percorso nel formato del .gitignore (caratteri speciali con la barra)."""
    for ch in ("\\", "[", "]", "*", "?", "#", "!"):
        p = p.replace(ch, "\\" + ch)
    return "/" + p if not p.startswith("/") else p


def righe_gitignore(righe):
    """Esclusioni (solo dentro le cartelle tenute in git) per i file che l'inventario NON mette in «git».
    Una cartella dove nessun file va in git diventa una riga sola."""
    fuori = {r["rel"] for r in righe if r["posto"] != "git"}
    tutti = {r["rel"] for r in righe}
    figli = defaultdict(set)          # cartella -> {nome: e' una cartella?}
    for rel in tutti:
        parti = Path(rel).parts
        for i in range(len(parti)):
            figli["/".join(parti[:i])].add((parti[i], i < len(parti) - 1))

    def tutto_fuori(d):
        pre = d + "/"
        return all(f in fuori for f in tutti if f.startswith(pre))

    out = []

    def visita(d):
        for nome, e_dir in sorted(figli[d]):
            rel = f"{d}/{nome}" if d else nome
            if e_dir:
                if tutto_fuori(rel):
                    out.append(f"data/{_gi(rel)[1:]}/")
                else:
                    visita(rel)
            elif rel in fuori:
                out.append(f"data/{_gi(rel)[1:]}")

    for top in CARTELLE_IN_GIT:
        if any(n == top and e for n, e in figli[""]):
            visita(top)
    in_git_altrove = sorted({Path(r["rel"]).parts[0] for r in righe if r["posto"] == "git" and len(Path(r["rel"]).parts) > 1
                             and Path(r["rel"]).parts[0] not in CARTELLE_IN_GIT})
    return out, in_git_altrove


def scrivi_gitignore(percorso, righe):
    """Riscrive il blocco fra i segnaposto; se non ci sono, lo aggiunge in fondo."""
    esclusioni, altrove = righe_gitignore(righe)
    blocco = "\n".join([GI_INIZIO, *esclusioni, GI_FINE]) + "\n"
    t = percorso.read_text(encoding="utf-8") if percorso.exists() else ""
    if GI_INIZIO in t and GI_FINE in t:
        a, b = t.index(GI_INIZIO), t.index(GI_FINE) + len(GI_FINE)
        t = t[:a] + blocco.rstrip("\n") + t[b:]
    else:
        t = t.rstrip("\n") + "\n" + blocco
    percorso.write_text(t, encoding="utf-8")
    return len(esclusioni), altrove


def scrivi_doc(percorso, blocco):
    if percorso.exists():
        t = percorso.read_text(encoding="utf-8")
        if INIZIO in t and FINE in t:
            a, b = t.index(INIZIO), t.index(FINE) + len(FINE)
            percorso.write_text(t[:a] + blocco.rstrip("\n") + t[b:], encoding="utf-8")
            return
        sep = "\n\n"
        percorso.write_text(t.rstrip("\n") + sep + blocco, encoding="utf-8")
        return
    testa = ("# Dati del progetto\n\nDove deve stare ogni file di `data/`: in git, nella Release di GitHub, come riassunto o fuori. "
             "La parte fra i segnaposto la riscrive `scripts/96_inventario_dati.py`; sotto, nella sezione «Decisioni di Leo», si scrivono le decisioni "
             "(non viene toccata).\n\n")
    coda = "\n## Decisioni di Leo\n\n(da compilare: fonte per fonte, git / Release / fonte; piano 2, passo 3)\n"
    percorso.write_text(testa + blocco + coda, encoding="utf-8")


def crea_dati_finti(cartella):
    """data/ finta: file con il peso vero (sparsi, non occupano disco) e i nomi che le pagine e gli script usano davvero."""
    voci = [
        ("storico_backup.sqlite", 2_100_000_000), ("raw/omi_2025_2/OMI_Torino_valori.csv", 18_000_000),
        ("raw/omi_2025_2/TO20252/Torino.kml", 900_000), ("raw/IMQ2022_opendata_web/spostamenti.csv", 140_000_000),
        ("raw/gtfs_gtt/gtt_gtfs.zip", 55_000_000), ("raw/istat/R01_indicatori.csv", 8_000_000), ("raw/istat/basi_territoriali.zip", 30_000_000), ("otp/rete/torino_cintura.osm.pbf", 120_000_000),
        ("processed/orari_fermate.js", 3_200_000), ("processed/accessibilita.json", 31_000_000),
        ("processed/risultato6_v2/mappa_r6.json", 1_100_000), ("processed/case_fragilita_servizi.json", 600_000),
        ("processed/avanzo_di_prova.json", 12_000), ("schede_risultati.js", 150_000), ("catalogo/istruzione.js", 800_000),
        ("catalogo/salute.js", 400_000), ("otp/jdk-25-jre/bin/java", 12_000_000), ("backup/mappa_torino_prima_correzioni.html", 22_000_000),
        ("otp/rete/gtt_gtfs_20261003_224530.zip", 11_700_000), ("processed/accessibilita_parziale/p1.json", 40_000), ("ref/parcheggi_osservazioni.json", 9_000), ("scenari/metro_notte.json", 70_000),
    ]
    for rel, peso in voci:
        p = cartella / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            f.truncate(peso)
    # una cartella con tanti file (come data/raw/omi): per provare la riga unica
    for i in range(35):
        with open(cartella / "raw" / "omi_2025_2" / "TO20252" / f"comune_{i:03d}.kml", "wb") as f:
            f.truncate(50_000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="cartella dei dati (default: data/ del progetto)")
    ap.add_argument("--uscita", default=None, help="file da scrivere (default: sviluppo/note_tecniche/DATI.md)")
    ap.add_argument("--prova", action="store_true", help="usa una cartella data/ finta in una cartella temporanea")
    ap.add_argument("--gitignore", nargs="?", const="", default=None,
                    help="riscrive le esclusioni di data/ nel .gitignore (default .gitignore del progetto; con --prova, quello della cartella finta)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    c = comuni.Controlli()
    if args.prova:
        tmp = Path(tempfile.mkdtemp(prefix="inventario_prova_"))
        data = tmp / "data"
        data.mkdir()
        crea_dati_finti(data)
        uscita = Path(args.uscita) if args.uscita else tmp / "DATI_prova.md"
        data_txt = f"FINTA ({data})"
    else:
        data = Path(args.data) if args.data else RADICE / "data"
        uscita = Path(args.uscita) if args.uscita else RADICE / "docs" / "DATI.md"
        data_txt = "`data/`"
    if not data.is_dir():
        sys.exit(f"ERRORE: non trovo la cartella dei dati {data}. Sul PC lancia lo script dalla cartella del progetto; nel cloud usa --prova.")
    corpus = carica_codice(RADICE, Path(__file__).name)
    c(f"codice letto: {len(corpus)} file (script, .bat, pagine)", len(corpus) > 20, bloccante=True)
    righe = inventario(data, corpus)
    c("trovato almeno un file in data/", len(righe) > 0, bloccante=True)
    c("nessun peso negativo", all(r["peso"] >= 0 for r in righe), bloccante=True)
    md, tot = testo_md(righe, data_txt)
    c("i posti sommano a tutti i file", sum(v[0] for v in tot.values()) == len(righe), bloccante=True)
    grossi = [r["rel"] for r in righe if r["posto"] == "git" and r["peso"] >= SOGLIA_MAX]
    c("nessun file proposto per git sopra 50 MB", not grossi, dettaglio=", ".join(grossi[:3]))
    sconosciuti = [r["rel"] for r in righe if r["posto"] == "fuori"]
    c(f"file che nessuno cita: {len(sconosciuti)} (da guardare in «fuori»)", True)
    uscita.parent.mkdir(parents=True, exist_ok=True)
    scrivi_doc(uscita, md)
    if args.gitignore is not None:
        gi = Path(args.gitignore) if args.gitignore else (uscita.parent / ".gitignore" if args.prova else RADICE / ".gitignore")
        n_gi, altrove = scrivi_gitignore(gi, righe)
        print(f"\n.gitignore: {n_gi} esclusioni scritte in {gi}")
        c("tutti i file in «git» stanno nelle cartelle tenute dal .gitignore", not altrove,
          dettaglio=f"fuori dalla whitelist: {', '.join(altrove)}" if altrove else "")
    print(f"\nScritto: {uscita}")
    print(f"\n{'posto':10s} {'file':>8s} {'MB':>12s}")
    for p in ("git", "Release", "riassunto", "fonte", "fuori"):
        n, s = tot.get(p, [0, 0])
        print(f"{p:10s} {n:8d} {mb(s):>12s}")
    print(f"{'tutto':10s} {len(righe):8d} {mb(sum(r['peso'] for r in righe)):>12s}")
    print(f"avvisi: {len(c.avvisi())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
