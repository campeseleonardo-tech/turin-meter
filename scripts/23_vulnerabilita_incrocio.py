# -*- coding: utf-8 -*-
"""
scripts/23_vulnerabilita_incrocio.py - Vulnerabilità x vuoto di servizio (Risultato 1)

Incrocia due file già prodotti:
  - data/processed/vulnerabilita.json  (indice composito v 0-100 + componenti c)
  - data/processed/risultato1_vuoti.json (flag "manca": gruppo = zero/pochissimo per sezione)

Per ogni sezione residenziale produce:
  - v: indice composito
  - comp: componenti grezze (percentili 0-1)
  - manca: dizionario gruppi -> "zero"|"pochissimo"
  - gruppi: per gruppo e per livello ("zero","pochissimo"),
            "debole_senza" / "debole_servito" / "ok"

Soglia di vulnerabilità: v >= soglia (default 90).
Uscita: data/processed/vulnerabilita_mappa.json (per la mappa interattiva).

Usage:
    python 23_vulnerabilita_incrocio.py [--soglia 90]
"""

import argparse
import datetime as dt
import json
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
VULN = RADICE / "data/processed/vulnerabilita.json"
VUOTI = RADICE / "data/processed/risultato1_vuoti.json"
OUT = RADICE / "data/processed/vulnerabilita_mappa.json"
GRUPPI = ["scuole", "salute", "cibo", "fermate", "verde"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--soglia", type=float, default=90.0,
                    help="soglia sopra la quale una sezione è considerata vulnerabile (default 90)")
    args = ap.parse_args()
    soglia = args.soglia

    vuln = json.loads(VULN.read_text(encoding="utf-8"))
    vuoti = json.loads(VUOTI.read_text(encoding="utf-8"))

    # {id: {gruppo: "zero"|"pochissimo"}}
    manca = {r["id"]: r["manca"] for r in vuoti["sezioni_manca"]}

    print(f"Sezioni vulnerabilità da processare: {len(vuln['sezioni'])}")
    print(f"Sezioni con almeno un gruppo mancante (su {len(manca)} note): {len(manca)}")

    res = []
    n_debole = n_debole_con_manca = 0
    for r in vuln["sezioni"]:
        sid = r["id"]
        if r.get("tipo") != "residenziale":
            continue
        v = r["v"]
        if v >= soglia:
            n_debole += 1
        # combina i due livelli di vuoto: per ogni gruppo calcoliamo
        # il flag a livello "zero" e a livello "pochissimo".
        # A "pochissimo" conta anche chi è a zero.
        gruppi = {}
        for g in GRUPPI:
            debole = v >= soglia
            senza_0 = (manca.get(sid, {}).get(g) == "zero")
            senza_poch = g in manca.get(sid, {})
            if debole and senza_0:
                c0 = "debole_senza"
            elif debole:
                c0 = "debole_servito"
            else:
                c0 = "ok"
            if debole and senza_poch:
                cp = "debole_senza"
            elif debole:
                cp = "debole_servito"
            else:
                cp = "ok"
            gruppi[g] = {"zero": c0, "pochissimo": cp}

        res.append({
            "id": sid,
            "comune": r["comune"],
            "res": r["res"],
            "v": v,
            "comp": r.get("c", {}),
            "manca": manca.get(sid, {}),
            "gruppi": gruppi,
        })
        if v >= soglia and manca.get(sid, {}):
            n_debole_con_manca += 1

    print(f"Sezioni vulnerabili (v >= {soglia}): {n_debole} "
          f"({n_debole_con_manca} hanno almeno un gruppo a zero/pochissimo)")

    esito = {
        "generato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "fonte_vulnerabilita": VULN.name,
        "fonte_vuoti": VUOTI.name,
        "soglia_vulnerabilita": soglia,
        "gruppi": GRUPPI,
        "sezioni": res,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(esito, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Scritto {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
