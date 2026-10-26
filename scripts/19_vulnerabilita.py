# -*- coding: utf-8 -*-
"""
scripts/19_vulnerabilita.py - Indice di vulnerabilita' per sezione di censimento

Componenti (piu' alti = piu' vulnerabile), dal censimento ISTAT 2021:
  occ   = quota di residenti 15-64 NON occupati (1 - occ/p1564)
  ist   = quota pop 9+ senza titolo di studio o con solo la elementare
  aff   = affollamento: residenti per abitazione occupata (p/ab)
  anz   = quota di residenti 65 anni e piu'

Dal giro F3 l'indice usa SOLO queste quattro componenti di censimento (bollino CENSIMENTO): servizi e verde a piedi (isocrone, script 18)
non entrano piu', cosi' la lettura «fragili senza servizi» di scheda 3 non e' circolare (controllo dello script 95).

Ogni componente e' trasformata in percentile sull'area (0 = il meno
vulnerabile, 1 = il piu' vulnerabile). L'indice e' la media pesata dei
percentili disponibili (pesi con --pesi, default tutti a 1). Le sezioni a cui
manca una componente (es. nessun residente 15-64) la escludono e i pesi si
rinormalizzano.

Uscite:
  data/processed/vulnerabilita.json   (indice + componenti per sezione)
  docs/rapporti/RAPPORTO_VULNERABILITA.txt     (sintesi e top 10)

Usage:
    python 19_vulnerabilita.py [--pesi occ=1,ist=1,aff=1,anz=1]
"""

import argparse
import datetime as dt
import json
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SEZIONI = RADICE / "data/processed/sezioni_torino.json"
ACCESS = RADICE / "data/processed/accessibilita.json"
OUT = RADICE / "data/processed/vulnerabilita.json"
RAPPORTO = RADICE / "docs/rapporti/RAPPORTO_VULNERABILITA.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

PRO_COM_TORINO = 30001  # non usato: il comune resta il campo "c" del json

# Nota: in 05 il comune di Torino e' identificato dal codice PRO_COM del file ISTAT.

NOMI = {"occ": "non occupati 15-64", "ist": "bassa istruzione 9+",
        "aff": "affollamento abitazioni", "anz": "quota 65+",
        "serv": "servizi a piedi (inverso)", "verde": "verde a piedi (inverso)"}
INVERSI = {"serv", "verde"}  # componenti dove valore basso = vulnerabile


def percentile_pesata(coppie):
    """Percentile PESATO per residenti. coppie = [(valore, residenti)].
    Un livello conta quante persone lo vivono, non quante sezioni lo hanno:
    evita che sezioni da 2 residenti finiano in cima alla lista."""
    coppie = sorted((v, w) for v, w in coppie if w is not None)
    tot = sum(w for _, w in coppie)
    if tot <= 0:
        return {}
    ranghi = {}
    cum = 0.0
    for v, w in coppie:
        cum += w
        ranghi[v] = cum / tot
    return ranghi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pesi", default="occ=1,ist=1,aff=1,anz=1")
    args = ap.parse_args()

    pesi = {}
    for pezzo in args.pesi.split(","):
        k, v = pezzo.split("=")
        pesi[k.strip()] = float(v)

    sezioni = json.loads(SEZIONI.read_text(encoding="utf-8"))
    sezioni = [s for s in sezioni if s.get("p", 0) > 0]
    print(f"Sezioni con residenti: {len(sezioni)}")

    # Sezioni "istituzionali": RSA, case di riposo e simili censite come sezione
    # a sé (molti anziani, nessuna abitazione occupata, poche o nessuna famiglia).
    # La vulnerabilita' del quartiere non deve fare i conti col loro interno.
    def e_istituzionale(s):
        return s.get("ab", 0) == 0 and s["p"] >= 20 and s.get("sen", 0) / s["p"] > 0.8

    istituto = {s["id"] for s in sezioni if e_istituzionale(s)}
    sezioni_tutte = sezioni
    sezioni = [s for s in sezioni if s["id"] not in istituto]
    print(f"Sezioni escluse come istituzionali (RSA e simili): {len(istituto)}")

    usa_access = False   # F3 (§3.7): indice solo da dati di CENSIMENTO; servizi e verde (isocrone) non entrano piu'
    access = json.loads(ACCESS.read_text(encoding="utf-8")) if usa_access else None
    taglio_piedi = str(access["parametri"]["cutoff_piedi_min"]) if usa_access else None

    # ---- componenti grezze, attutite verso la media dell'area:
    #      v = (k + m*lambda) / (d + lambda), con lambda in "persone".
    #      Le sezioni grandi restano se stesse; le micro-sezioni (es. 20-40
    #      residenti) non fanno piu' gli estremi per puro campionamento.
    LAMBDA_PERS = 100.0
    LAMBDA_AB = 20.0
    comp = {k: {} for k in NOMI}
    tot = {"occ": [0, 0], "ist": [0, 0], "aff": [0, 0], "anz": [0, 0]}
    for s in sezioni:
        sid = s["id"]
        if s.get("p1564", 0) > 0:
            tot["occ"][0] += s["p1564"] - s["occ"]; tot["occ"][1] += s["p1564"]
        if s.get("ist9", 0) > 0:
            tot["ist"][0] += s["i0"] + s["iel"]; tot["ist"][1] += s["ist9"]
        if s.get("ab", 0) > 0:
            tot["aff"][0] += s["p"]; tot["aff"][1] += s["ab"]
        if s.get("p", 0) > 0:
            tot["anz"][0] += s["sen"]; tot["anz"][1] += s["p"]
    media = {k: (v[0] / v[1]) if v[1] else 0.0 for k, v in tot.items()}
    attutisci = {
        "occ": (lambda s: (s["p1564"] - s["occ"], s["p1564"]), LAMBDA_PERS),
        "ist": (lambda s: (s["i0"] + s["iel"], s["ist9"]), LAMBDA_PERS),
        "aff": (lambda s: (s["p"], s["ab"]), LAMBDA_AB),
        "anz": (lambda s: (s["sen"], s["p"]), LAMBDA_PERS),
    }
    for k, (prendi, lam) in attutisci.items():
        m = media[k]
        for s in sezioni:
            if prendi(s)[1] > 0:
                k_num, d = prendi(s)
                comp[k][s["id"]] = (k_num + m * lam) / (d + lam)
        # riporto il valore grezzo nel rapporto? no: l'attutito e' la misura; m e' dichiarata
    if usa_access:
            rec = next((r for r in access["sezioni"] if r["id"] == sid), None)
            if rec:
                tot = sum(rec["piedi"].get(taglio_piedi, {}).values())
                comp["serv"][sid] = tot
                comp["verde"][sid] = rec["piedi"].get(taglio_piedi, {}).get("verde", 0)

    attivi = [k for k in NOMI if comp[k] and pesi.get(k, 0) > 0]
    print("Componenti usate:", ", ".join(f"{k} ({NOMI[k]}, peso {pesi.get(k,0)})" for k in attivi))
    if usa_access:
        print("Attenzione: servizi e verde vengono dalle isocrone 18 -> bollino CENSIMENTO+STIMATO")

    # ---- percentili pesati per residenti (i componenti inversi sono girati)
    peso_sezione = {s["id"]: s["p"] for s in sezioni}
    pct = {}
    for k in attivi:
        ranghi = percentile_pesata([(v, peso_sezione[sid]) for sid, v in comp[k].items()])
        for sid, v in comp[k].items():
            p = ranghi.get(v)
            if p is not None:
                pct.setdefault(k, {})[sid] = (1.0 - p) if k in INVERSI else p

    # ---- indice (le istituzionali entrano nel JSON solo come flag, senza indice)
    risultati = []
    for s in sezioni_tutte:
        sid = s["id"]
        if sid in istituto:
            risultati.append({"id": sid, "comune": s["c"], "res": s["p"],
                              "v": None, "c": {}, "tipo": "istituzionale"})
            continue
        num = 0.0
        den = 0.0
        dettaglio = {}
        for k in attivi:
            p = pct[k].get(sid)
            if p is None:
                continue
            w = pesi[k]
            num += w * p
            den += w
            dettaglio[k] = round(p, 3)
        if den == 0:
            continue
        risultati.append({
            "id": sid, "comune": s["c"], "res": s["p"],
            "v": round(100.0 * num / den, 1),
            "c": dettaglio,
            "tipo": "residenziale",
        })

    risultati.sort(key=lambda r: (r["v"] is None, -(r["v"] or 0)))
    origine = "CENSIMENTO+STIMATO" if usa_access else "CENSIMENTO"
    esito = {
        "generato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "origine": origine,
        "componenti": {k: {"nome": NOMI[k], "peso": pesi.get(k, 0)} for k in attivi},
        "nota": ("Indice di vuln. = media pesata dei percentili delle componenti. "
                 "Percentili pesati per residenti; rapporti attutiti verso la media "
                 "dell'area (peso a priori 100 persone, 20 abitazioni) per evitare "
                 "che micro-sezioni facciano estremi per campionamento. "
                 "0 = meno vulnerabile, 100 = piu' vulnerabile. "
                 "Non e' una misura di reddito: il reddito per sezione non esiste."),
        "sezioni": risultati,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(esito, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Scritto {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")

    # ---- rapporto
    vals = sorted(r["v"] for r in risultati if r["v"] is not None)
    med = vals[len(vals) // 2]
    righe = [
        "RAPPORTO VULNERABILITA' PER SEZIONE",
        f"generato: {esito['generato']}  origine: {origine}",
        "componenti e pesi: " + ", ".join(f"{k}={pesi.get(k,0)}" for k in attivi),
        f"sezioni: {len(risultati)}  indice mediano: {med}",
        "",
        "Top 10 sezioni per indice (id, comune, residenti, indice, percentili):",
    ]
    for r in risultati[:10]:
        righe.append(f"  {r['id']}  comune {r['comune']}  res {r['res']}  v {r['v']}  {r['c']}")
    if usa_access:
        righe += ["", "Componenti serv/verde da isocrone (script 18): bollino CENSIMENTO+STIMATO."]
    righe += ["", f"Sezioni istituzionali escluse dal rango (RSA e simili): {len(istituto)}",
              "", "Rapporti attutiti verso la media dell'area (lambda 100 persone / 20 abitazioni).",
              "Il reddito non entra: non esiste a livello di sezione (solo MEF per comune)."]
    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(righe), encoding="utf-8")
    print(f"Scritto {RAPPORTO}")


if __name__ == "__main__":
    main()
