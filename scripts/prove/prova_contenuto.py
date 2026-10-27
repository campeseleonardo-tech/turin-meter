#!/usr/bin/env python3
"""Prova del contenuto delle schede (passo 4.9 del piano), in italiano, inglese e tedesco, senza browser:
  - il numero grande e' quello dei file dei dati (schede 1, 3, 4) o la media delle 4 ore del giorno (scheda 2, decisione 16), e uguale nelle tre lingue;
  - 2 o 3 punti di al massimo 25 parole;
  - nessuna stima aperta o forbice dei tempi in auto, nessuna tariffa agevolata, fuori da calcolo, criteri e limiti (decisione 16);
  - una sola parte chiusa nella finestra delle schede, con le fonti come ultima riga;
  - nessuna etichetta del tipo di dato (§5.0 del piano: via badge, MISURATO/STIMATO/CALCOLATO e simili come etichette);
  - 4 schede in 2 gruppi (3 in vetrina + 1 approfondimento);
  - nessuna frase italiana in inglese e in tedesco;
  - TomTom si nomina solo come fonte del controllo (calcolo, criteri, limiti, fonti, confronto), mai nel titolo, nel numero grande o nei punti; mai «permesso» / «uso autorizzato».
Uso: python scripts/prove/prova_contenuto.py        Codice di uscita 0 = tutto a posto."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import frasi_vietate  # noqa: E402

RADICE = Path(__file__).resolve().parent.parent.parent
PROC = RADICE / "data" / "processed"
ITALIANO = re.compile(r"\b(sono|ogni|più|anche|quanto|mezzi|dati|risultati|fermate|ritardo|torinesi|persone|giorni|dalla|alla|tutti|perché|nella|delle|degli|coi|dove|che|non)\b", re.I)
LINGUE = {"it": "forma", "en": "forma_en", "de": "forma_de"}
VIETATE_AUTO = re.compile(r"stima aperta|stima corretta|forbice|open estimate|corrected estimate|offene Schätzung|korrigierte Schätzung|Spanne|tariffe agevolate|concession fare|ermäßigte Tarife", re.I)


def frasi(o, chiave=""):
    """Le stringhe di testo di una forma (senza i dati dei disegni)."""
    if isinstance(o, str):
        return [o]
    if isinstance(o, list):
        return [t for x in o for t in frasi(x, chiave)]
    if isinstance(o, dict):
        return [t for k, v in o.items() if k not in ("anima", "contorno", "d", "tipo", "tono", "id", "link", "vista") for t in frasi(v, k)]
    return []


def cifre(v):
    return re.findall(r"\d+", str(v))


def main():
    t = (RADICE / "data" / "schede_risultati.js").read_text(encoding="utf-8")
    schede = json.loads(t[t.index("["):t.index("];\nwindow.SCHEDE_PERIODO") + 1])
    vis = [s for s in schede if s.get("numero_pubblico") is not None and s.get("forma")]
    err = []
    if len(vis) != 4:
        err.append(f"le schede in pagina sono {len(vis)}, non 4")
    gruppi = {}
    for s in vis:
        gruppi.setdefault(s.get("gruppo"), []).append(s["risultato"])
    if sorted(len(v) for v in gruppi.values()) != [1, 3]:
        err.append(f"i gruppi non sono 3 + 1: {gruppi}")
    r4 = json.loads((PROC / "risultato4_regolarita.json").read_text(encoding="utf-8"))
    attesi = {
        "4": r4["confronto_gtt"]["definizioni"]["a"]["per_tipo"]["0"]["ritardo10_pct"],
        "6": json.loads((PROC / "risultato6_v2" / "mappa_r6.json").read_text(encoding="utf-8"))["riepilogo"]["fermate_senza_posti_bastanti"],
        "10": json.loads((PROC / "case_fragilita_servizi.json").read_text(encoding="utf-8"))["e2_doppio_svantaggio"]["sezioni"]["residenti_doppio_svantaggio"],
    }
    for s in vis:
        r = s["risultato"]
        f_it = s["forma"]
        v = f_it["numero"]["valore"]
        if r in attesi:
            if v != attesi[r]:
                err.append(f"scheda {r}: numero grande {v} diverso dai dati {attesi[r]}")
        else:
            ore = json.loads((PROC / "ore_del_giorno.json").read_text(encoding="utf-8"))["ore"]
            medio = round(sum(o["ab"]["limite_corretto"]["mediano"] for o in ore) / len(ore), 1)
            if v != medio:
                err.append(f"scheda {r}: numero grande {v} diverso dalla media delle {len(ore)} ore del giorno {medio}")
        for lg, k in LINGUE.items():
            f = s.get(k)
            if not f:
                err.append(f"scheda {r}: manca {k}")
                continue
            if cifre(f["numero"]["valore"]) != cifre(v):
                err.append(f"scheda {r} {lg}: numero grande diverso dall'italiano ({f['numero']['valore']} contro {v})")
            if not 2 <= len(f["punti"]) <= 3:
                err.append(f"scheda {r} {lg}: {len(f['punti'])} punti, non 2 o 3")
            for p in f["punti"]:
                if len(p.split()) > 25:
                    err.append(f"scheda {r} {lg}: punto di {len(p.split())} parole: {p[:60]}…")
            if "tipo_badge" in f:
                err.append(f"scheda {r} {lg}: c'è ancora un'etichetta del tipo di dato (tipo_badge)")
            visibili = " . ".join(frasi({k: x for k, x in f.items() if k not in ("calcolo", "criteri", "limiti", "fonti")}))
            for t in VIETATE_AUTO.findall(visibili):
                err.append(f"scheda {r} {lg}: «{t}» fuori da calcolo e limiti (decisione 16)")
            tutto_testo = " . ".join(frasi(f))
            for t in frasi_vietate.trova(tutto_testo, lg):
                err.append(f"scheda {r} {lg}: formula vietata o etichetta del tipo di dato: «{t}»")
            for fr in re.split(r"(?<=[.;!?])\s+", tutto_testo):
                if len(fr.split()) > 35:
                    err.append(f"scheda {r} {lg}: frase di {len(fr.split())} parole: {fr[:60]}…")
            if not f.get("fonti"):
                err.append(f"scheda {r} {lg}: niente fonti")
            visibile = " ".join([f["titolo"], f["domanda"], f["numero"]["testo"], str(f["numero"].get("breve", ""))] + list(f["punti"]))
            if lg != "it" and ITALIANO.search(visibile):
                err.append(f"scheda {r} {lg}: parole italiane in titolo, numero o punti: {sorted(set(m.lower() for m in ITALIANO.findall(visibile)))}")
            if re.search(r"tomtom", visibile, re.I):
                err.append(f"scheda {r} {lg}: TomTom nominato fuori dal calcolo e dalle fonti")
            tutto = json.dumps(f, ensure_ascii=False)
            if re.search(r"uso autorizzato|used with permission|mit Erlaubnis|con permesso|with permission", tutto, re.I):
                err.append(f"scheda {r} {lg}: dichiara un permesso di TomTom")
    # formule vietate nei README e nel metodo, per lingua del file
    for nome, lg in (("README.md", "en"), ("README.it.md", "it"), ("README.de.md", "de"), ("docs/en/METHODS.md", "en"), ("DATA_LICENSES.md", "en")):
        testo = (RADICE / nome).read_text(encoding="utf-8")
        testo = re.sub(r"\]\([^)]*\)", "]", testo)   # via gli indirizzi dei link
        for t in frasi_vietate.trova(testo, lg):
            err.append(f"{nome}: formula vietata o etichetta del tipo di dato: «{t}»")
    # una sola parte chiusa, con le fonti come ultima riga
    pag = (RADICE / "assets" / "schede.js").read_text(encoding="utf-8")
    a = pag.index("$(\"finCorpo\").innerHTML")
    corpo = pag[a:pag.index("showModal", a)]
    if corpo.count("parte(") != 1:
        err.append(f"assets/schede.js: {corpo.count('parte(')} parti chiuse nella scheda, non 1")
    if "fonti" not in corpo.split("elenco(f.limiti")[-1]:
        err.append("assets/schede.js: le fonti non sono l'ultima riga della parte chiusa")
    for e in err:
        print("ERRORE", e)
    print(f"prova del contenuto: {len(vis)} schede × 3 lingue, " + ("TUTTO A POSTO" if not err else f"{len(err)} ERRORI"))
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
