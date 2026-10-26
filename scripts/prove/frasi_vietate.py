"""Formule da evitare in ogni testo del sito e dei README (§5.0 del piano, regole 2 e 4): tono umano, niente frasi da AI, niente etichette del tipo di dato.
Usato da prova_contenuto.py (testi statici) e da prova_pagine.py (testi delle pagine nel browser)."""
import re

FRASI = {
    "it": ["il punto è", "io decido", "non solo", "davvero", "in breve", "senza fronzoli", "ho fatto tutto il percorso", "le macchine eseguono", "moltiplica quello che sai"],
    "en": ["the point is", "not just", "i decide", "really", "in short", "in a nutshell", "no frills", "the machines"],
    "de": ["der punkt ist", "nicht nur", "ich entscheide", "wirklich", "kurz gesagt", "die maschinen"],
}
VIETATE = {lg: re.compile(r"(?<![\wàèéìòù])(?:" + "|".join(re.escape(f) for f in fr) + r")(?![\wàèéìòù])", re.I) for lg, fr in FRASI.items()}
# etichette del tipo di dato: mai da sole, mai fra parentesi quadre (§5.0, regola 4)
ETICHETTA_TIPO = re.compile(r"\[(?:MISURATO|STIMATO|CALCOLATO|CENSIMENTO|PROGRAMMATO|DATI SCARSI|MEASURED|ESTIMATED|CALCULATED|FEW DATA|GEMESSEN|GESCHÄTZT|BERECHNET|WENIGE DATEN)[^\]]*\]|\b(MISURATO|STIMATO|CALCOLATO|DATI SCARSI|MEASURED|ESTIMATED|CALCULATED|GEMESSEN|GESCHÄTZT|BERECHNET)\b")


def trova(testo, lingua):
    """Le formule vietate trovate in `testo` (lista di stringhe, vuota se va bene)."""
    return sorted({m.group(0).lower() for m in VIETATE[lingua].finditer(testo)}) + [m.group(0) for m in ETICHETTA_TIPO.finditer(testo)]
