"""Versioni inglese e tedesca delle schede: ricava la «forma» in un'altra lingua da quella italiana con i testi di scripts/schede/testi.json.

L'italiano non si tocca: le schede restano scritte dai moduli r1, r4, r6, r8, r10. Qui ogni frase italiana viene cercata fra le frasi fisse
(«esatte») o fra i modelli con segnaposto («modelli») e sostituita con la versione nella lingua. Una frase fissa vale `"it": "inglese"` oppure
`"it": {"en": ..., "de": ...}`; un modello e' `{"it": ..., "en": ..., "de": ...}`. Il tedesco e' facoltativo: se una frase non ha la versione tedesca
resta in inglese (con i numeri in formato inglese) e si elenca fra quelle da tradurre. In inglese i numeri passano al formato inglese
(1.234,5 -> 1,234.5); in tedesco restano nel formato italiano. Un nome proprio (zona, linea, fermata) resta com'e'.
Le frasi senza traduzione si elencano (e restano in italiano)."""
import json
import re
from pathlib import Path

FILE = Path(__file__).resolve().parent / "testi.json"
NUM = r"\d+(?:[.,]\d+)*"
TIPI = {"n": NUM, "p": r"[+\-−]?" + NUM, "s": r".+?", "t": r".+?", "w": r".+?", "a": r"(?:il |l')"}
PAROLE = {
    "en": [("minuti", "minutes"), ("nessuno", "none"), (" contro ", " versus "), ("stima Google", "Google estimate"), ("stima sensori", "sensor estimate"), (" o ", " or "), (" e altre", " and others"), (" e ", " and ")],
    "de": [("minuti", "Minuten"), ("nessuno", "keine"), (" contro ", " gegen "), ("stima Google", "Google-Schätzung"), ("stima sensori", "Sensorschätzung"), (" o ", " oder "), (" e altre", " und andere"), (" e ", " und ")],
}
CONNETTORI = {"di", "del", "della", "dei", "da", "d'", "de", "al", "e", "→", "-", "–", "+", "(", ")", "/", "Da", "Del", "Di"}


def numero_en(s):
    """'1.234,5' -> '1,234.5'; '0,4' -> '0.4'; '4.044' -> '4,044' (il punto italiano separa le migliaia)."""
    segno = ""
    if s and s[0] in "+-−":
        segno, s = s[0], s[1:]
    intero, _, dec = s.partition(",")
    intero = intero.replace(".", "")
    if len(intero) > 3:
        intero = f"{int(intero):,}"
    return segno + intero + ("." + dec if dec else "")


def _carica():
    d = json.loads(FILE.read_text(encoding="utf-8"))
    modelli = []
    for mod in d["modelli"]:
        rx, pos = "", 0
        for mt in re.finditer(r"\{([nspwta])(\d)\}", mod["it"]):
            rx += re.escape(mod["it"][pos:mt.start()]) + f"(?P<{mt.group(1)}{mt.group(2)}>{TIPI[mt.group(1)]})"
            pos = mt.end()
        rx += re.escape(mod["it"][pos:])
        letterali = len(re.sub(r"\{[nspwta]\d\}", "", mod["it"]))
        modelli.append((letterali, re.compile(rx), mod["en"], mod.get("de")))
    modelli.sort(key=lambda x: -x[0])      # prima i modelli piu' specifici
    return d["esatte"], modelli


ESATTE, MODELLI = _carica()


def sembra_nome(t):
    """Nome proprio (zona, linea, fermata, intervallo di numeri): parole con la maiuscola, cifre, connettori e punteggiatura."""
    if not t.strip():
        return True
    for tok in re.split(r"[\s,]+", t):
        if not tok:
            continue
        if tok in CONNETTORI or re.fullmatch(r"[~\d.,:+\-–/→×%()±€]+", tok) or re.fullmatch(r"\(?[A-Z0-9À-Ý][^\s]*", tok):
            continue
        return False
    return True


def traduci(testo, lingua="en", mancanti=None):
    """Traduce una frase italiana in `lingua` ("en" o "de"). Se non la conosce la lascia com'e' e la registra in `mancanti`;
    in tedesco una frase che ha solo l'inglese resta inglese e si registra anch'essa."""
    if not isinstance(testo, str):
        return testo
    if testo in ESATTE:
        v = ESATTE[testo]
        if isinstance(v, str):
            v = {"en": v}
        if lingua == "de":
            if v.get("de") is not None:
                return v["de"]
            if mancanti is not None and v["en"] != testo:
                mancanti.append(testo)
        return v["en"]
    for _lett, rx, en, de in MODELLI:
        mt = rx.fullmatch(testo)
        if not mt:
            continue
        usa_de = lingua == "de" and de is not None
        if lingua == "de" and de is None and mancanti is not None:
            mancanti.append(testo)
        modello = de if usa_de else en
        parole = PAROLE["de" if usa_de else "en"]
        valori = {}
        for nome, v in mt.groupdict().items():
            tipo = nome[0]
            if tipo in "np":
                valori[nome] = v if usa_de else numero_en(v)       # in tedesco i numeri restano nel formato italiano
            elif tipo == "t":
                valori[nome] = traduci(v, "de" if usa_de else "en", mancanti)
            elif tipo == "w":
                for it, altra in parole:
                    v = v.replace(it, altra)
                valori[nome] = v
            elif tipo == "a":
                valori[nome] = ""
            else:
                valori[nome] = v
        return re.sub(r"\{([nspwta]\d)\}", lambda x: valori[x.group(1)], modello)
    if re.fullmatch(r"[~\d.,:\s\-–+]+", testo):     # solo cifre e punteggiatura (es. «1,5-2», «21–28»): in inglese i decimali passano al formato inglese
        if lingua == "de":
            return testo
        return re.sub(NUM, lambda x: numero_en(x.group()) if re.search(r"[.,]", x.group()) else x.group(), testo)
    if sembra_nome(testo):
        return testo
    if mancanti is not None:
        mancanti.append(testo)
    return testo


ETICHETTE = {
    "en": {"STIMATO": "ESTIMATED", "MISURATO": "MEASURED", "PROGRAMMATO": "SCHEDULED", "CENSIMENTO": "CENSUS", "dati scarsi": "little data"},
    "de": {"STIMATO": "GESCHÄTZT", "MISURATO": "GEMESSEN", "PROGRAMMATO": "GEPLANT", "CENSIMENTO": "ZENSUS", "dati scarsi": "wenig Daten"},
}
SALTA = {"tipo", "tono", "link", "id", "vista", "xnome", "ynome", "mappa", "contorno"}


def _grafico_o_valore(o, lingua, mancanti):
    if isinstance(o, str):
        return traduci(o, lingua, mancanti)
    if isinstance(o, list):
        return [_grafico_o_valore(x, lingua, mancanti) for x in o]
    if isinstance(o, dict):
        return {k: (v if k in SALTA else _grafico_o_valore(v, lingua, mancanti)) for k, v in o.items()}
    return o


def traduci_forma(f, lingua="en", mancanti=None):
    """La forma di una scheda in `lingua` ("en" o "de"): stessa struttura di quella italiana, senza il vecchio riquadro «english».
    `mancanti` raccoglie le frasi italiane senza traduzione (in tedesco anche quelle che hanno solo l'inglese)."""
    out = {}
    for k, v in f.items():
        if k == "english":
            continue
        if k == "etichetta":
            e = v
            for it, altra in ETICHETTE[lingua].items():
                e = e.replace(it, altra)
            out[k] = e
        elif k == "principale" and isinstance(v, dict) and v.get("tipo") == "dispersione":
            out[k] = {kk: (vv if kk in SALTA or kk == "punti" else _grafico_o_valore(vv, lingua, mancanti)) for kk, vv in v.items()}   # i nomi delle zone restano com'e'
        elif k in SALTA:
            out[k] = v
        else:
            out[k] = _grafico_o_valore(v, lingua, mancanti)
    return out
