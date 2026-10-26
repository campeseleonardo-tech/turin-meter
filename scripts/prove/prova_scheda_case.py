#!/usr/bin/env python3
"""Prova della scheda «Case, servizi e fragilita'» senza data/: usa un case_fragilita_servizi.json dato (reale o finto, nel formato dello
script 95) e, per i risultati 1, 4, 6 e 8 che nel cloud non hanno i dati, schede finte minime. Scrive nella cartella data/schede_risultati.js
e copia index.html e progetto.html, cosi' si aprono nel browser.
Uso: python scripts/prove/prova_scheda_case.py CASE.json CARTELLA"""
import importlib.util
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RADICE = AQUI.parent.parent
case, out = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(RADICE / "scripts"))
from schede import comune  # noqa: E402
spec = importlib.util.spec_from_file_location("schede", RADICE / "scripts" / "schede_risultati.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
(out / "data" / "processed").mkdir(parents=True, exist_ok=True)
shutil.copy(case, out / "data" / "processed" / "case_fragilita_servizi.json")
comune.PROC = out / "data" / "processed"
comune.OUT_JS = out / "data" / "schede_risultati.js"


def finta(n, titolo, tag):
    def scheda():
        return {"risultato": n, "titolo": titolo, "tag": tag, "domanda": "Domanda finta?", "scenari": [{"nome": "Oggi", "numeri": [comune.num("x", 1, "u")], "nota": ""}],
                "grafici": [], "mappa": None}
    return scheda


def forma_finta(s):
    return {"etichetta": s["tag"], "titolo": f"Titolo finto del risultato {s['risultato']}", "domanda": "Domanda finta?",
            "numero": {"valore": 12, "unita": "%", "testo": "di prova"},
            "principale": {"tipo": "barre", "titolo": "Grafico finto", "unita": "%", "voci": [comune.voce("a", 40), comune.voce("b", 20, tono="rosso")]},
            "punti": ["Uno.", "Due.", "Tre."], "altri": [], "calcolo": ["Calcolo finto."], "criteri": [["a", "b"]], "limiti": ["Limite finto."],
            "english": ["One.", "Two.", "Three."]}


m.scheda_r4, m.scheda_r6, m.scheda_r8 = (finta("4", "Puntualita'", "MISURATO"), finta("6", "Parcheggi", "STIMATO"), finta("8", "Traffico", "STIMATO"))
for k in ("risultato4", "risultato6", "risultato8"):
    m.FORME[k] = forma_finta
m.leggi = lambda nome: __import__("json").loads((comune.PROC / nome).read_text(encoding="utf-8"))
m.main()
for f in ("index.html", "progetto.html"):
    shutil.copy(RADICE / f, out / f)
shutil.copytree(RADICE / "assets", out / "assets", dirs_exist_ok=True)
print("pronto in", out)
