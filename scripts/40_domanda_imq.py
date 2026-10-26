# -*- coding: utf-8 -*-
"""
scripts/40_domanda_imq.py - Pacchetto B del piano traffico Fase 3.

Costruisce la domanda di viaggi in AUTO CONDUCENTE dall'indagine IMQ 2022
(data/processed/imq/spostamenti.csv), pesata con PESO, per coppia di zone
(origine, destinazione) e ora di partenza (giorno feriale medio).

Regole (dal piano, sezione 4):
 - viaggio "auto conducente" = il campo MEZZO1-3 contiene il codice 03;
 - viaggi misti (auto + un altro mezzo motorizzato, es. auto+treno): di
   default si tengono solo quelli in cui 03 e' l'unico mezzo motorizzato;
   gli altri si contano e si scrivono a parte (se > 8% si valuta diversamente);
 - peso = colonna PESO (la somma su tutte le righe = 8.217.863 spostamenti/giorno);
 - ora = ora di partenza ORA_PAR, fascia locale;
 - origine/destinazione = COD_PAR/COD_ARR fra le 212 zone; un estremo vuoto
   significa "fuori dalle 212 zone" (esterno non localizzato) e viene contato.

Controlli (tolleranza 5%): totale auto-conducente ~4,18 milioni/giorno e
~0,97 milioni con almeno un estremo in un quartiere di Torino; picchi 7-8 e 16-18.

Output:
  data/processed/traffico_c/domanda_auto.json
  docs/rapporti/RAPPORTO_TRAFFICO_C_DOMANDA.txt
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
SPOSTAMENTI = RADICE / "data" / "processed" / "imq" / "spostamenti.csv"
ZONE_JSON = RADICE / "data" / "processed" / "imq_zone.json"
OUT_DIR = RADICE / "data" / "processed" / "traffico_c"
OUT = OUT_DIR / "domanda_auto.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_TRAFFICO_C_DOMANDA.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

MEZZI_NON_MOTORIZZATI = {"", "01", "16", "20", "26"}  # piedi, bici, bike sharing, monopattino
TOTALE_RIFERIMENTO = 8217863.0


def main():
    if not SPOSTAMENTI.is_file():
        sys.exit(f"ERRORE: non trovo {SPOSTAMENTI}. I dati IMQ 2022 non stanno in git (licenza non chiara): scaricali dalla fonte "
                 "(indirizzi in docs/en/METHODS.md), poi python scripts/14_prepara_imq.py.")

    zone_ok = {z["cod"] for z in json.loads(ZONE_JSON.read_text(encoding="utf-8"))}
    quartieri_torino = {c for c in zone_ok if c.startswith("Q")}

    celle = defaultdict(lambda: [0.0, 0])        # (par, arr, ora) -> [peso, n]
    quote_ora = defaultdict(float)               # ora -> peso
    tot = {"peso": 0.0, "n": 0}
    tot_torino = 0.0          # almeno un estremo in un quartiere di Torino
    fuori = {"peso": 0.0, "n": 0}                # un estremo vuoto/non localizzato
    misti = {"peso": 0.0, "n": 0}                # auto + altro mezzo motorizzato (esclusi)
    misti_tenuti = {"peso": 0.0, "n": 0}
    ore_strane = 0
    senza_ora = 0
    problemi_ora = defaultdict(int)
    celle_sotto30 = {"n_celle": 0, "peso": 0.0}
    celle_per_interviste = defaultdict(lambda: [0, 0.0])

    with SPOSTAMENTI.open(encoding="utf-8-sig", newline="") as fh:
        lettore = csv.DictReader(fh, delimiter=";")
        for r in lettore:
            mezzi = [(r.get(f"MEZZO{i}") or "").strip() for i in (1, 2, 3)]
            if "03" not in mezzi:
                continue
            peso = float((r.get("PESO") or "0").replace(",", ".") or 0)
            altri_motorizzati = [m for m in mezzi if m and m != "03" and m not in MEZZI_NON_MOTORIZZATI]
            if altri_motorizzati:
                misti["peso"] += peso
                misti["n"] += 1
                continue
            misti_tenuti["peso"] += peso
            misti_tenuti["n"] += 1

            par = (r.get("COD_PAR") or "").strip()
            arr = (r.get("COD_ARR") or "").strip()
            ora_s = (r.get("ORA_PAR") or "").strip()
            if not ora_s:
                senza_ora += 1
                continue
            hh = ora_s.split(":")[0]
            try:
                ora = int(hh)
            except ValueError:
                problemi_ora[ora_s] += 1
                continue
            if ora == 24:
                ora = 0
            if not (0 <= ora <= 23):
                ore_strane += 1
                continue

            tot["peso"] += peso
            tot["n"] += 1
            quote_ora[ora] += peso
            if par in quartieri_torino or arr in quartieri_torino:
                tot_torino += peso
            if par not in zone_ok or arr not in zone_ok:
                fuori["peso"] += peso
                fuori["n"] += 1
            celle[(par, arr, ora)][0] += peso
            celle[(par, arr, ora)][1] += 1

    # quanti viaggi (peso) stanno in celle OD con meno di 30 interviste
    for (par, arr, ora), (peso, n) in celle.items():
        celle_per_interviste[n][0] += 1
        celle_per_interviste[n][1] += peso
        if n < 30:
            celle_sotto30["n_celle"] += 1
            celle_sotto30["peso"] += peso

    quote = {str(h): (quote_ora.get(h, 0.0) / tot["peso"] if tot["peso"] else 0.0) for h in range(24)}

    celle_out = [[par, arr, ora, round(peso, 4), n]
                 for (par, arr, ora), (peso, n) in sorted(celle.items())]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = {
        "stimato": False,
        "fonte": "IMQ 2022 (indagine telefonica, campione) - spostamenti.csv",
        "grandezza": "viaggi in auto come conducente, giorno feriale medio, pesati",
        "criterio_misti": ("tenuti solo i viaggi in cui 03 (auto conducente) e' l'unico mezzo "
                           "motorizzato; esclusi quelli con un altro mezzo motorizzato"),
        "totali": {
            "peso_auto_conducente": round(tot["peso"], 4),
            "n_righe_intervistate": tot["n"],
            "frazione_del_totale_giornaliero": round(tot["peso"] / TOTALE_RIFERIMENTO, 5),
            "riferimento_totale_giornaliero": TOTALE_RIFERIMENTO,
            "con_almeno_un_estremo_in_quartiere_torino": round(tot_torino, 4),
            "un_estremo_fuori_dalle_212_zone": {"peso": round(fuori["peso"], 4), "n": fuori["n"]},
            "esclusi_misti": {"peso": round(misti["peso"], 4), "n": misti["n"]},
            "misti_tenuti": {"peso": round(misti_tenuti["peso"], 4), "n": misti_tenuti["n"]},
            "senza_ora": senza_ora,
            "ora_fuori_range": ore_strane,
        },
        "quote_orarie": quote,
        "peso_per_ora": {str(h): round(quote_ora.get(h, 0.0), 4) for h in range(24)},
        "celle_sotto_30_interviste": {
            "n_celle": celle_sotto30["n_celle"],
            "peso": round(celle_sotto30["peso"], 4),
            "quota_peso": round(celle_sotto30["peso"] / tot["peso"], 5) if tot["peso"] else None,
        },
        "celle": celle_out,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    righe = []
    a = righe.append
    a("RAPPORTO DOMANDA AUTO IMQ 2022 (pacchetto B, metodo C)")
    a("=" * 70)
    a(f"righe di spostamenti.csv lette: {tot['n'] + misti['n'] + senza_ora + ore_strane + sum(problemi_ora.values()):,}")
    a("")
    a("== Totali (controlli, tolleranza 5%) ==")
    a(f"  auto conducente (solo 03 unico motorizzato) : {tot['peso']:>14,.0f} viaggi/giorno   (riferimento ~4.180.000)")
    a(f"     = {100*tot['peso']/TOTALE_RIFERIMENTO:.1f}% del totale spostamenti/giorno ({TOTALE_RIFERIMENTO:,.0f})")
    a(f"  con almeno un estremo in quartiere Torino  : {tot_torino:>14,.0f} viaggi/giorno   (riferimento ~970.000)")
    a(f"  un estremo fuori dalle 212 zone            : {fuori['peso']:>14,.0f} viaggi/giorno  ({fuori['n']} interviste)")
    a(f"  esclusi perche' misti (auto + altro mezzo) : {misti['peso']:>14,.0f} viaggi/giorno  ({misti['n']} interviste)")
    a(f"     = {100*misti['peso']/(tot['peso']+misti['peso']):.2f}% del peso auto (soglia di attenzione 8%)")
    a(f"  celle OD x ora distinte                    : {len(celle):,}")
    a("")
    a("== Profilo orario (quota del peso per ora di partenza) ==")
    for h in range(24):
        q = quote[str(h)] * 100
        a(f"  {h:02d}:00  {q:5.2f}%  {'#' * int(round(q))}")
    a(f"  picco 7-8-9: {100*sum(quote_ora.get(h,0) for h in (7,8,9))/tot['peso']:.2f}%   "
      f"picco 16-17-18: {100*sum(quote_ora.get(h,0) for h in (16,17,18))/tot['peso']:.2f}%")
    a("")
    a("== Celle OD con meno di 30 interviste (campione debole) ==")
    a(f"  celle: {celle_sotto30['n_celle']:,} su {len(celle):,} ({100*celle_sotto30['n_celle']/len(celle):.1f}%)")
    a(f"  peso in quelle celle: {celle_sotto30['peso']:,.0f} = {100*celle_sotto30['peso']/tot['peso']:.1f}% del peso")
    a("")
    a(f"Output: {OUT}")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")

    print("\n".join(righe))
    print(f"\nScritto {OUT}")
    if problemi_ora:
        print("ATTENZIONE formati ORA_PAR strani:", dict(problemi_ora))


if __name__ == "__main__":
    main()
