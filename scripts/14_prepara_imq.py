#!/usr/bin/env python3
"""14_prepara_imq.py - Fase 2 del piano IMQ 2022: aggrega i CSV esportati.

Legge data/processed/imq/*.csv (prodotti da scripts/13_esporta_imq.ps1) e scrive:
- data/processed/imq_zone.json      le 212 zone con macroarea e comuni ISTAT
- data/processed/imq_od.json        matrici origine->destinazione (totale/pubblico/
                                    privato/altro), intera giornata
- data/processed/imq_aggregati.json per zona di origine -> scopo, ora, modo
- data/processed/imq_residenti.json per zona di residenza -> sesso x classe di eta'

Ogni valore e' PESATO (somma di PESO); ogni cella porta anche n (righe intervistate)
e "affidabile" (n >= SOGLIA_N). Non entrano mai dati personali.

Costanti (da sviluppo/MEMORIA_PROGETTO.md / piano del 9/10/2026):
- SOGLIA_N = 30; classi di eta' 1=11-19, 2=20-49, 3=50-64, 4=65-84;
- scopi 12-16 -> "altro" (accorpati nella categoria 10 "Altro");
- ora = ora (0-23) di ORA_PAR;
- modo, gerarchia pubblico > privato > altro:
  pubblico = bus/tram/metro/treno/pullman extraurbano/scuolabus/bus aziendale;
  privato  = auto conducente, auto passeggero, moto/motorino, taxi/NCC;
  altro    = piedi, bicicletta, monopattino e tutto il resto.

Solo libreria standard. Uso: python scripts/14_prepara_imq.py
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def trova_radice():
    for c in [AQUI, *AQUI.parents]:
        if c.name.lower() == "gtt":
            return c
    d = Path.home() / "Desktop" / "GTT"
    return d if d.is_dir() else AQUI.parent


RADICE = trova_radice()
IN = RADICE / "data" / "processed" / "imq"
OUT = RADICE / "data" / "processed"

SOGLIA_N = 30
CLASSI_ETA = {1: "11-19", 2: "20-49", 3: "50-64", 4: "65-84"}
SESSI = {1: "M", 2: "F"}

# Riferimenti dal report IMQ 2022 (data/raw/IMQ-2022_EP_REPORT-COMPLETO-2.1.pdf):
# - §9.2 "SCOPI DEGLI SPOSTAMENTI", colonna TOTALE, riga "Totale con ritorno a casa";
# - §9.3 "DISTRIBUZIONE ORARIA DELLA MOBILITA'", riga TOTALE (Pubblico / Privato).
RIF_TOTALE = 8_217_863
RIF_QUOTA_PUB = 464_337 / 8_217_868.0
RIF_QUOTA_PRI = 4_911_434 / 8_217_868.0
TOLL_TOTALE = 0.02      # ±2%
TOLL_QUOTA = 0.03       # ±3 punti

# Classificazione dei mezzi (tab_mezzi). cod_tipo_mezzo MBT/BXU/TR = pubblico;
# gli altri mezzi pubblici sono indicati esplicitamente.
PUBBLICO_TIPI = {"MBT", "BXU", "TR"}
PUBBLICO_COD = {"08", "10", "11", "23", "24"}   # altro urbano, bus aziendale, scuolabus, funicolare, battello
PRIVATO_COD = {"02", "03", "04", "05"}          # moto, auto conducente, auto passeggero, taxi/NCC


def classe_mezzo(cod, tipo):
    tipo = (tipo or "").strip().upper()
    if tipo in PUBBLICO_TIPI:
        return "pubblico"
    if cod in PUBBLICO_COD:
        return "pubblico"
    if cod in PRIVATO_COD:
        return "privato"
    return "altro"


def norm_zona(c):
    """QC01 -> Q001 (solo Torino: la residenza usa QCxx, il resto Q0xx)."""
    c = (c or "").strip()
    if len(c) == 4 and c[0].upper() == "Q" and c[1].upper() == "C":
        return "Q0" + c[2:]
    return c


def leggi(nome):
    p = IN / nome
    if not p.is_file():
        sys.exit(f"CSV mancante: {p} (esegui prima 13_esporta_imq.ps1)")
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def cella(d):
    """d = {'v': peso, 'n': righe} -> [peso_arrotondato, n, affidabile]."""
    return [round(d["v"], 3), d["n"], d["n"] >= SOGLIA_N]


def main():
    zone_camp = leggi("zone_camp.csv")
    comuni = leggi("comuni.csv")
    mezzi = leggi("mezzi.csv")
    spostamenti = leggi("spostamenti.csv")
    interviste = leggi("interviste.csv")

    zone = [norm_zona(r["COD2"]) for r in zone_camp]
    if len(zone) != 212 or len(set(zone)) != 212:
        sys.exit(f"STOP: zone_camp.csv non ha 212 codici distinti ({len(zone)}/{len(set(zone))})")
    zone_ok = set(zone)

    # --- tabella di corrispondenza dei mezzi (per il rapporto) ---
    tab_mezzi = []
    cls_mezzo = {}
    for r in mezzi:
        cod = (r["Cod_Mezzo"] or "").strip()
        cls = classe_mezzo(cod, r.get("cod_tipo_mezzo"))
        cls_mezzo[cod] = cls
        tab_mezzi.append({"cod": cod, "label": (r["Label"] or "").strip(),
                          "tipo": (r.get("cod_tipo_mezzo") or "").strip(), "classe": cls})

    # --- comuni per zona (codici ISTAT) ---
    istat_per_zona = defaultdict(list)
    comuni_non_agganciati = 0
    for r in comuni:
        cod = norm_zona(r["COD2"])
        if cod not in zone_ok:
            comuni_non_agganciati += 1
            continue
        istat_per_zona[cod].append((r["COD1"] or "").strip())
    for z in istat_per_zona:
        istat_per_zona[z] = sorted(set(istat_per_zona[z]))

    # --- spostamenti: OD, scopo, ora, modo ---
    modi = ("tot", "pub", "pri", "alt")
    od = {m: defaultdict(lambda: {"v": 0.0, "n": 0}) for m in modi}
    agg_scopo = defaultdict(lambda: defaultdict(lambda: {"v": 0.0, "n": 0}))
    agg_ora = defaultdict(lambda: defaultdict(lambda: {"v": 0.0, "n": 0}))
    agg_modo = defaultdict(lambda: defaultdict(lambda: {"v": 0.0, "n": 0}))
    tot_scopo = defaultdict(lambda: {"v": 0.0, "n": 0})
    tot_ora = defaultdict(lambda: {"v": 0.0, "n": 0})
    tot_modo = defaultdict(lambda: {"v": 0.0, "n": 0})
    somma_totale = 0.0
    somma_od = 0.0
    par_fuori = arr_fuori = 0

    for r in spostamenti:
        peso = float(r["PESO"] or 0)
        somma_totale += peso
        par = (r["COD_PAR"] or "").strip()
        arr = (r["COD_ARR"] or "").strip()
        scopo = (r["SCOPO"] or "").strip()
        if scopo in {"12", "13", "14", "15", "16"}:
            scopo = "10"   # non documentati -> Altro
        ora_s = (r["ORA_PAR"] or "").strip()
        ora = int(ora_s.split(":")[0]) if ora_s else None

        # modo (gerarchia pubblico > privato > altro)
        classi = {cls_mezzo.get((r[f"MEZZO{i}"] or "").strip()) for i in range(1, 4)}
        classi.discard(None)
        if "pubblico" in classi:
            modo = "pub"
        elif "privato" in classi:
            modo = "pri"
        else:
            modo = "alt"

        for key in ("tot", modo):
            od[key][(par, arr)]["v"] += peso
            od[key][(par, arr)]["n"] += 1
        if par in zone_ok and arr in zone_ok:
            somma_od += peso
        else:
            if par not in zone_ok:
                par_fuori += 1
            if arr not in zone_ok:
                arr_fuori += 1

        agg_scopo[par][scopo]["v"] += peso
        agg_scopo[par][scopo]["n"] += 1
        tot_scopo[scopo]["v"] += peso
        tot_scopo[scopo]["n"] += 1
        if ora is not None:
            agg_ora[par][ora]["v"] += peso
            agg_ora[par][ora]["n"] += 1
            tot_ora[ora]["v"] += peso
            tot_ora[ora]["n"] += 1
        agg_modo[par][modo]["v"] += peso
        agg_modo[par][modo]["n"] += 1
        tot_modo[modo]["v"] += peso
        tot_modo[modo]["n"] += 1

    # --- residenti: zona di residenza -> sesso x classe di eta' ---
    res = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"v": 0.0, "n": 0})))
    tot_res = {"v": 0.0, "n": 0}
    res_non_agganciati = 0
    for r in interviste:
        peso = float(r["PESO"] or 0)
        tot_res["v"] += peso
        tot_res["n"] += 1
        z = norm_zona(r["COD_CAMP"])
        sesso = SESSI.get(int(r["SESSO"])) if (r["SESSO"] or "").strip() else None
        eta = CLASSI_ETA.get(int(r["FASCIA_ETA"])) if (r["FASCIA_ETA"] or "").strip() else None
        if z not in zone_ok or sesso is None or eta is None:
            res_non_agganciati += 1
            continue
        res[z][sesso][eta]["v"] += peso
        res[z][sesso][eta]["n"] += 1

    # ------------------------------------------------------------ verifiche
    esiti = []

    def check(nome, ok, dettaglio):
        esiti.append((nome, bool(ok), dettaglio))
        print(f"[{'OK ' if ok else 'STOP'}] {nome}: {dettaglio}")

    check("righe spostamenti", len(spostamenti) == 95608, f"{len(spostamenti)} (atteso 95608)")
    check("righe interviste", len(interviste) == 41933, f"{len(interviste)} (atteso 41933)")
    check("212 zone presenti", len(zone_ok) == 212, f"{len(zone_ok)}")
    check("somma PESO spostamenti = fase 1", abs(somma_totale - 8217862.72272161) <= 1,
          f"{somma_totale:.3f}")
    check("somma PESO residenti = fase 1", abs(tot_res["v"] - 3629394.31707437) <= 1,
          f"{tot_res['v']:.3f}")
    check("totale spostamenti = report §9.2 (±2%)",
          abs(somma_totale - RIF_TOTALE) / RIF_TOTALE <= TOLL_TOTALE,
          f"{somma_totale:.1f} vs {RIF_TOTALE} ({100*(somma_totale-RIF_TOTALE)/RIF_TOTALE:+.3f}%)")

    q_pub = tot_modo["pub"]["v"] / somma_totale
    q_pri = tot_modo["pri"]["v"] / somma_totale
    check("quota pubblico = report §9.3 (±3 punti)", abs(q_pub - RIF_QUOTA_PUB) <= TOLL_QUOTA,
          f"{100*q_pub:.2f}% vs {100*RIF_QUOTA_PUB:.2f}%")
    check("quota privato = report §9.3 (±3 punti)", abs(q_pri - RIF_QUOTA_PRI) <= TOLL_QUOTA,
          f"{100*q_pri:.2f}% vs {100*RIF_QUOTA_PRI:.2f}%")

    # ------------------------------------------------------------ scrittura
    OUT.mkdir(parents=True, exist_ok=True)

    zone_json = [{"cod": norm_zona(r["COD2"]), "denom": r["DENOMINAZIONE"].strip(),
                  "macro": r["MACRO_CAMP"].strip(), "prov": r["PROVINCIA"].strip(),
                  "istat": istat_per_zona.get(norm_zona(r["COD2"]), [])}
                 for r in zone_camp]
    (OUT / "imq_zone.json").write_text(
        json.dumps(zone_json, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    od_json = {
        "zone": zone,
        "modi": list(modi),
        "od": {m: [[a, b, round(d["v"], 3), d["n"], d["n"] >= SOGLIA_N]
                   for (a, b), d in sorted(od[m].items())] for m in modi},
    }
    (OUT / "imq_od.json").write_text(
        json.dumps(od_json, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    agg_json = {
        "zone": zone,
        "per_zona": {par: {"scopo": {k: cella(v) for k, v in agg_scopo[par].items()},
                           "ora": {str(k): cella(v) for k, v in agg_ora[par].items()},
                           "modo": {k: cella(v) for k, v in agg_modo[par].items()}}
                     for par in zone},
        "totale": {"scopo": {k: cella(v) for k, v in tot_scopo.items()},
                   "ora": {str(k): cella(v) for k, v in tot_ora.items()},
                   "modo": {k: cella(v) for k, v in tot_modo.items()}},
    }
    (OUT / "imq_aggregati.json").write_text(
        json.dumps(agg_json, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    res_json = {
        "zone": zone,
        "per_zona": {z: {s: {e: {"v": round(res[z][s][e]["v"], 3), "n": res[z][s][e]["n"]}
                            for e in CLASSI_ETA.values() if res[z][s][e]["n"]}
                        for s in SESSI.values() if any(res[z][s][e]["n"] for e in CLASSI_ETA.values())}
                     for z in zone},
        "totale": {"v": round(tot_res["v"], 3), "n": tot_res["n"]},
    }
    (OUT / "imq_residenti.json").write_text(
        json.dumps(res_json, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # ------------------------------------------------------------ riepilogo
    print("\n--- mezzi ---")
    for t in tab_mezzi:
        print(f"  {t['cod']} {t['tipo']:>4} {t['classe']:<8} {t['label']}")

    print("\n--- quote modali (intera giornata) ---")
    for k, nome in (("pub", "pubblico"), ("pri", "privato"), ("alt", "altro")):
        print(f"  {nome:<9} {tot_modo[k]['v']:>12.0f}  {100*tot_modo[k]['v']/somma_totale:5.2f}%  "
              f"n={tot_modo[k]['n']}")

    print("\n--- affidabilita' celle OD (n >= 30) ---")
    for m in modi:
        tot_c = len(od[m])
        aff = sum(1 for d in od[m].values() if d["n"] >= SOGLIA_N)
        print(f"  {m}: {aff}/{tot_c} celle affidabili ({100*aff/max(tot_c,1):.1f}%)")

    print("\n--- controlli ---")
    print(f"  somma OD (zone valide) = {somma_od:.1f} su totale {somma_totale:.1f} "
          f"(scarto {100*(somma_totale-somma_od)/somma_totale:.4f}%)")
    print(f"  spostamenti con origine fuori dalle 212 zone: {par_fuori}; destinazione: {arr_fuori}")
    print(f"  comuni non agganciati a una zona: {comuni_non_agganciati}/{len(comuni)}")
    print(f"  interviste non agganciate a zona/sesso/eta': {res_non_agganciati}")

    print("\n--- scopi (pesati, ordine codice) ---")
    tot_scope_rif = {"01": 1405970, "02": None, "03": 115884, "04": 1321351, "05": 387406,
                     "06": 213241, "07": 628517, "08": 3714050, "09": 361907, "10": 69536}
    for k in sorted(tot_scopo):
        v = tot_scopo[k]["v"]
        rif = tot_scope_rif.get(k)
        extra = f"  (report §9.2: {rif})" if rif else ""
        print(f"  scopo {k}: {v:>12.0f}  n={tot_scopo[k]['n']}{extra}")

    print("\n--- file scritti ---")
    for f in ("imq_zone.json", "imq_od.json", "imq_aggregati.json", "imq_residenti.json"):
        print(f"  {OUT / f} ({(OUT / f).stat().st_size/1e6:.2f} MB)")

    fallite = [n for n, ok, _ in esiti if not ok]
    if fallite:
        sys.exit("\nSTOP: verifiche fallite: " + ", ".join(fallite))
    print("\nTutte le verifiche di fase 2 superate.")


if __name__ == "__main__":
    main()
