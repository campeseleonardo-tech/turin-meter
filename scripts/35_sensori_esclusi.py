#!/usr/bin/env python3
"""35_sensori_esclusi.py

Elenco dei sensori 5T da NON usare per misurare il traffico, con il motivo.
Vedi sviluppo/note_tecniche/R8_traffico.md.

Regole (periodo = giorni locali 2026-10-09 -> 2026-10-16, UTC+2):
- "morto"      : ha letture nel periodo ma TUTTE con accuratezza = 0;
- "bloccato"   : fra le letture con accuratezza > 0 ha meno di 20 coppie distinte
                 (flusso, velocita') e almeno 500 letture (ripete sempre gli stessi numeri);
- "pochi dati": ha letture con accuratezza > 0 ma nessuna cella "ok" in velocita_5t.json.
L'ordine di controllo e' morto -> bloccato -> pochi dati: ogni sensore ha UN solo motivo.

Output:
- data/processed/sensori_esclusi.json  (lista di {lcd1, nome, motivo})
- docs/rapporti/RAPPORTO_SENSORI_ESCLUSI.txt

Solo libreria standard. Database in sola lettura.
"""

import json
import sqlite3
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
DB = RADICE / "data" / "storico_backup.sqlite"
VELOCITA = RADICE / "data" / "processed" / "velocita_5t.json"
OUT = RADICE / "data" / "processed" / "sensori_esclusi.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_SENSORI_ESCLUSI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

DA, A = "2026-10-09", "2026-10-16"   # giorni locali (UTC+2)
MIN_COPPIE = 20                       # sotto questo numero di coppie distinte: "bloccato"
MIN_LETTURE_BLOCCATO = 500            # ...ma solo con almeno tante letture

RIGHE = []


def scrivi(msg=""):
    RIGHE.append(str(msg))


def apri_db(percorso):
    if not percorso.is_file():
        raise SystemExit(f"DB non trovato: {percorso}")
    con = sqlite3.connect(f"file:{percorso}?mode=ro", uri=True, timeout=60)
    con.execute("PRAGMA busy_timeout=60000")
    return con


def main():
    con = apri_db(DB)
    cur = con.cursor()

    anagrafica = {}
    for lcd1, nome, direzione, lat, lng in cur.execute(
            "SELECT lcd1, nome_strada, direzione, lat, lng FROM sensori_5t"):
        anagrafica[str(lcd1)] = dict(nome=nome or "", dir=direzione or "?",
                                     lat=lat, lon=lng, urbano="(TO)" in (nome or ""))

    righe = cur.execute("""
        SELECT CAST(f.lcd1 AS TEXT), f.flusso, f.velocita, a.accuratezza
        FROM flussi_5t f
        LEFT JOIN accuratezza_5t a
               ON a.generato_utc = f.generato_utc AND a.lcd1 = f.lcd1
        WHERE date(datetime(substr(f.generato_utc,1,19), '+2 hours')) BETWEEN ? AND ?
    """, (DA, A)).fetchall()
    con.close()

    letture = {}
    coppie = {}
    for lcd1, flusso, vel, acc in righe:
        d = letture.setdefault(lcd1, dict(tot=0, pos=0))
        d["tot"] += 1
        if acc is not None and acc > 0:
            d["pos"] += 1
            coppie.setdefault(lcd1, set()).add((flusso, vel))

    dati_vel = json.loads(VELOCITA.read_text(encoding="utf-8"))["sensori"]
    con_cella_ok = {str(k) for k, s in dati_vel.items()
                    if any(c.get("ok") for ct in s["celle"].values() for c in ct.values())}

    esclusi = []
    dettagli = []
    for lcd1 in sorted(anagrafica):
        info = anagrafica[lcd1]
        l = letture.get(lcd1, dict(tot=0, pos=0))
        nc = len(coppie.get(lcd1, ()))
        motivo = None
        if l["tot"] > 0 and l["pos"] == 0:
            motivo = "morto"
        elif l["pos"] >= MIN_LETTURE_BLOCCATO and nc < MIN_COPPIE:
            motivo = "bloccato"
        elif l["pos"] > 0 and lcd1 not in con_cella_ok:
            motivo = "pochi dati"
        if motivo:
            esclusi.append(dict(lcd1=lcd1, nome=info["nome"], motivo=motivo))
            dettagli.append((lcd1, info, motivo, l["tot"], l["pos"], nc))

    usabili = [k for k in anagrafica if k not in {e["lcd1"] for e in esclusi}]
    per_motivo = {}
    for e in esclusi:
        per_motivo.setdefault(e["motivo"], []).append(e["lcd1"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(esclusi, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------- rapporto ----------
    scrivi("SENSORI 5T ESCLUSI DALLA MISURA DEL TRAFFICO")
    scrivi("=" * 78)
    scrivi(f"periodo: giorni locali {DA} -> {A} (UTC+2)")
    scrivi(f"database (sola lettura): {DB}")
    scrivi("regole: morto = nel periodo ha letture ma tutte con accuratezza 0;")
    scrivi(f"        bloccato = almeno {MIN_LETTURE_BLOCCATO} letture con accuratezza > 0 ma meno di "
           f"{MIN_COPPIE} coppie distinte (flusso, velocita');")
    scrivi("        pochi dati = ha letture con accuratezza > 0 ma nessuna cella ok in velocita_5t.json.")
    scrivi("")
    scrivi("(1) Conteggi")
    scrivi(f"  sensori in tutto: {len(anagrafica)}")
    for m in ("morto", "bloccato", "pochi dati"):
        l = per_motivo.get(m, [])
        urb = sum(1 for x in l if anagrafica[x]["urbano"])
        scrivi(f"  {m:11s}: {len(l):>3}  (di cui urbani {urb})   [attesi: "
               f"{'11 (3)' if m == 'morto' else '5' if m == 'bloccato' else '1 (11421)'}]")
    scrivi(f"  esclusi in tutto: {len(esclusi)}   [attesi 17]")
    scrivi(f"  sensori usabili: {len(usabili)}   [attesi 109 - 17 = 92]")
    scrivi("")
    scrivi("(2) Elenco degli esclusi")
    scrivi(f"  {'lcd1':>6}  {'nome':34s} {'dir':9s} {'urb':>4} {'motivo':10s} "
           f"{'letture':>8} {'acc>0':>7} {'coppie':>7}")
    for lcd1, info, motivo, tot, pos, nc in sorted(dettagli, key=lambda x: (x[2], x[0])):
        scrivi(f"  {lcd1:>6}  {info['nome'][:34]:34s} {info['dir'][:9]:9s} "
               f"{'si' if info['urbano'] else 'no':>4} {motivo:10s} "
               f"{tot:>8} {pos:>7} {nc:>7}")

    testo = "\n".join(RIGHE)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.write(testo + "\n")
    RAPPORTO.write_text(testo + "\n", encoding="utf-8")
    print(f"\nRapporto salvato: {RAPPORTO}")
    print(f"JSON salvato: {OUT}")

    # esito dei controlli a console
    atteso = {"morto": 11, "bloccato": 5, "pochi dati": 1}
    tutti_ok = all(len(per_motivo.get(m, [])) == n for m, n in atteso.items()) \
        and len(esclusi) == 17 and len(usabili) == 92
    print("CONTROLLI:", "OK" if tutti_ok else "NON TORNANO")
    for m, n in atteso.items():
        print(f"  {m}: atteso {n}, trovato {len(per_motivo.get(m, []))}")
    print(f"  totale esclusi: atteso 17, trovato {len(esclusi)}")
    print(f"  usabili: atteso 92, trovato {len(usabili)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
