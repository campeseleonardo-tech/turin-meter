# -*- coding: utf-8 -*-
"""
scripts/102_scelta_del_mezzo.py - Risultato 8, parte E (giro L13): dove i mezzi pubblici sono lenti, chi puo' prende l'auto?

Domanda: nelle coppie di zone dove i mezzi impiegano molto piu' dell'auto, una quota minore di persone usa i mezzi?

Regole (fissate il 24/10/2026 PRIMA di vedere i numeri, `sviluppo/piani/PROMPT_LAVORI.md` blocco L13):
- viaggi dell'indagine IMQ 2022 (spostamenti.csv, dal disco: i file IMQ non stanno in git) che partono fra le 6 e le 10 (ore 6-9) di un feriale;
- quota dei mezzi di una coppia di zone = viaggi coi mezzi pubblici / (mezzi pubblici + auto come conducente + auto come passeggero), con i pesi dell'indagine;
  un viaggio e' «coi mezzi» se almeno uno dei suoi tre mezzi e' pubblico (stessa gerarchia dello script 14), altrimenti e' «in auto» se ha un'auto
  (03 conducente o 04 passeggero); piedi, bici, moto, taxi e il resto non entrano;
- una coppia conta solo con almeno 30 interviste (SOGLIA_N dello script 14), cioe' 30 viaggi nella fascia che entrano nella quota (mezzi o auto);
- rapporto dei tempi = quello della stima aperta dell'auto alle 8 (tp_contro_auto.json: «rapporto_basso», script 93 con comuni.TempiAutoAperti, giro F3);
- tre gruppi separati: Torino-Torino, Torino-cintura (nei due sensi), cintura-cintura (solo se ci sono almeno 10 coppie); AVVISO sotto 20 coppie in un gruppo;
- Spearman fra rapporto e quota dei mezzi, con intervallo al 95% da 2.000 ricampionamenti delle coppie (seme fisso 20261024);
  «regge» solo se l'intervallo non contiene lo 0;
- fasce del rapporto: sotto 1,5; 1,5-2; 2-3; oltre 3. Per ogni fascia di ogni gruppo: quota dei mezzi, coppie, interviste.
Frase obbligatoria nelle pagine: «È una relazione, non una causa: chi abita lontano ha anche più spesso l'auto.»

In git va solo il JSON del risultato (riassunti per gruppo e fascia, nessuna cella della fonte).

Come si lancia
--------------
  python scripts\\102_scelta_del_mezzo.py            (serve data/processed/imq/spostamenti.csv e mezzi.csv: derivati dall'IMQ, fuori da git)
  python scripts\\102_scelta_del_mezzo.py --prova    (dati finti, scrive file con suffisso _prova)
Uscite: data/processed/scelta_del_mezzo.json, docs/rapporti/RAPPORTO_SCELTA_DEL_MEZZO.txt
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
PROC = RADICE / "data" / "processed"
IMQ = PROC / "imq"
OUT_JSON = PROC / "scelta_del_mezzo.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_SCELTA_DEL_MEZZO.txt"

ORE = (6, 7, 8, 9)                       # partenza dalle 6 alle 10
SOGLIA_N = 30                            # come SOGLIA_N dello script 14
MIN_COPPIE_CINTURA = 10                  # cintura-cintura solo con almeno 10 coppie
AVVISO_COPPIE = 20
RICAMPIONAMENTI = 2000
SEME = 20261024
FASCE = [(0.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 99.0)]
GRUPPI = {"a": "Torino-Torino", "b": "Torino-cintura (e cintura-Torino)", "c": "cintura-cintura"}
FRASE = "È una relazione, non una causa: chi abita lontano ha anche più spesso l'auto."

PUBBLICO_TIPI = {"MBT", "BXU", "TR"}
PUBBLICO_COD = {"08", "10", "11", "23", "24"}      # come lo script 14
AUTO_COD = {"03", "04"}                            # auto come conducente, auto come passeggero


def leggi_csv(p):
    if not p.is_file():
        comuni.richiedi_fonte(p)
        sys.exit(f"ERRORE: manca {p}")
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def mezzi_pubblici(righe_mezzi):
    pub = set()
    for r in righe_mezzi:
        cod = (r["Cod_Mezzo"] or "").strip()
        tipo = (r.get("cod_tipo_mezzo") or "").strip().upper()
        if tipo in PUBBLICO_TIPI or cod in PUBBLICO_COD:
            pub.add(cod)
    return pub


def quote_per_coppia(spostamenti, pub, ore=ORE):
    """{(da, a): {"pub": peso, "auto": peso, "n": viaggi}} per i viaggi delle ore indicate (predefinito 6-9) che sono «coi mezzi» o «in auto»."""
    q = defaultdict(lambda: {"pub": 0.0, "auto": 0.0, "n": 0})
    for r in spostamenti:
        ora_s = (r["ORA_PAR"] or "").strip()
        if not ora_s:
            continue
        if int(ora_s.split(":")[0]) not in ore:
            continue
        cod = {(r[f"MEZZO{i}"] or "").strip() for i in (1, 2, 3)}
        cod.discard("")
        if cod & pub:
            modo = "pub"
        elif cod & AUTO_COD:
            modo = "auto"
        else:
            continue
        coppia = ((r["COD_PAR"] or "").strip(), (r["COD_ARR"] or "").strip())
        q[coppia][modo] += float(r["PESO"] or 0)
        q[coppia]["n"] += 1
    return q


def ranghi(v):
    """Ranghi con media sui pari (come scipy.stats.rankdata)."""
    v = np.asarray(v, dtype=float)
    ordine = np.argsort(v, kind="mergesort")
    r = np.empty(len(v))
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[ordine[j + 1]] == v[ordine[i]]:
            j += 1
        r[ordine[i:j + 1]] = (i + j) / 2.0 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = ranghi(x), ranghi(y)
    if rx.std() == 0 or ry.std() == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def spearman_con_intervallo(x, y):
    """(rho, basso, alto): intervallo al 95% da RICAMPIONAMENTI ricampionamenti delle coppie con reinserimento, seme fisso."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    rho = spearman(x, y)
    if rho is None or len(x) < 5:
        return rho, None, None
    rng = np.random.default_rng(SEME)
    vals = []
    for _ in range(RICAMPIONAMENTI):
        i = rng.integers(0, len(x), len(x))
        r = spearman(x[i], y[i])
        if r is not None:
            vals.append(r)
    if len(vals) < RICAMPIONAMENTI // 2:
        return rho, None, None
    return rho, float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def analizza_gruppo(coppie):
    """coppie: [{rapporto, quota, pub, auto, n}] -> dizionario del gruppo."""
    if not coppie:
        return {"coppie": 0, "interviste": 0}
    rapp = [c["rapporto"] for c in coppie]
    quota = [c["quota"] for c in coppie]
    rho, lo, hi = spearman_con_intervallo(rapp, quota)
    fasce = []
    for da, a in FASCE:
        s = [c for c in coppie if da <= c["rapporto"] < a]
        tot = sum(c["pub"] + c["auto"] for c in s)
        fasce.append({"da": da, "a": None if a > 50 else a, "coppie": len(s), "interviste": sum(c["n"] for c in s),
                      "quota_mezzi": round(sum(c["pub"] for c in s) / tot, 4) if tot > 0 else None})
    return {"coppie": len(coppie), "interviste": sum(c["n"] for c in coppie),
            "rapporto_mediano": round(float(np.median(rapp)), 2),
            "quota_mezzi_totale": round(sum(c["pub"] for c in coppie) / sum(c["pub"] + c["auto"] for c in coppie), 4),
            "spearman": None if rho is None else round(rho, 3),
            "intervallo95": None if lo is None else [round(lo, 3), round(hi, 3)],
            "regge": bool(lo is not None and (hi < 0 or lo > 0)),
            "fasce": fasce}


def dati_finti():
    """Prova: 3 zone Torino, 3 cintura, viaggi inventati con quota che scende col rapporto."""
    rng = np.random.default_rng(1)
    zone_t, zone_c = ["Q001", "Q002", "Q003"], ["C001", "C002", "C003"]
    coppie, spost = [], []
    for da in zone_t + zone_c:
        for a in zone_t + zone_c:
            if da == a:
                continue
            gr = "a" if da in zone_t and a in zone_t else ("c" if da in zone_c and a in zone_c else "b")
            rapp = round(float(rng.uniform(1.0, 4.0)), 2)
            coppie.append({"da": da, "a": a, "gruppo": gr, "rapporto_basso": rapp, "interviste": 50})
            pubp = max(0.05, 0.6 - 0.15 * rapp)
            for _ in range(40):
                m = "06" if rng.random() < pubp else "03"
                spost.append({"ORA_PAR": "07:30", "MEZZO1": m, "MEZZO2": "", "MEZZO3": "", "COD_PAR": da, "COD_ARR": a, "PESO": "100"})
    mezzi = [{"Cod_Mezzo": "06", "cod_tipo_mezzo": "MBT"}, {"Cod_Mezzo": "03", "cod_tipo_mezzo": ""}]
    return coppie, spost, mezzi


def abbina(coppie_tp, q):
    """Abbina le coppie del confronto dei tempi alle quote dei mezzi; tiene le coppie con almeno SOGLIA_N viaggi."""
    per_gruppo = {k: [] for k in GRUPPI}
    viste, doppie, scartate_poche = set(), 0, 0
    for p in coppie_tp:
        chiave = (p["da"], p["a"])
        if chiave in viste:
            doppie += 1
            continue
        viste.add(chiave)
        d = q.get(chiave)
        if not d or d["n"] < SOGLIA_N or (d["pub"] + d["auto"]) <= 0:
            scartate_poche += 1
            continue
        per_gruppo[p["gruppo"]].append({"da": p["da"], "a": p["a"], "rapporto": float(p["rapporto_basso"]), "pub": d["pub"],
                                        "auto": d["auto"], "n": d["n"], "quota": d["pub"] / (d["pub"] + d["auto"])})
    return per_gruppo, doppie, scartate_poche


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true", help="dati finti, file con suffisso _prova")
    args = ap.parse_args()
    c = comuni.Controlli()
    if args.prova:
        coppie_tp, spost, mezzi = dati_finti()
    else:
        comuni.richiedi_fonte(IMQ / "spostamenti.csv", IMQ / "mezzi.csv")
        tp = json.loads((PROC / "tp_contro_auto.json").read_text(encoding="utf-8"))
        coppie_tp = tp["coppie"]
        spost = leggi_csv(IMQ / "spostamenti.csv")
        mezzi = leggi_csv(IMQ / "mezzi.csv")
    pub = mezzi_pubblici(mezzi)
    c("mezzi pubblici riconosciuti (almeno la linea urbana GTT)", "06" in pub, bloccante=True, dettaglio=f"{len(pub)} codici")
    per_gruppo, doppie, scartate_poche = abbina(coppie_tp, quote_per_coppia(spost, pub))
    c("nessuna coppia contata due volte", doppie == 0, bloccante=True, dettaglio=f"{doppie} doppie")
    tutte = [x for v in per_gruppo.values() for x in v]
    c("quote dei mezzi fra 0 e 1", all(0.0 <= x["quota"] <= 1.0 for x in tutte), bloccante=True)
    c("rapporti dei tempi positivi", all(x["rapporto"] > 0 for x in tutte), bloccante=True)
    c("interviste totali usate (viaggi 6-10 in coppie con almeno 30)", sum(x["n"] for x in tutte) > 0, bloccante=True,
      dettaglio=f"{sum(x['n'] for x in tutte)} viaggi in {len(tutte)} coppie; {scartate_poche} coppie sotto le {SOGLIA_N} interviste o senza viaggi")

    gruppi = {}
    for k, nome in GRUPPI.items():
        n = len(per_gruppo[k])
        if k == "c" and n < MIN_COPPIE_CINTURA:
            gruppi[k] = {"nome": nome, "coppie": n, "interviste": sum(x["n"] for x in per_gruppo[k]), "non_valutato": True}
            c(f"gruppo {nome}: almeno {MIN_COPPIE_CINTURA} coppie", False, dettaglio=f"{n} coppie: gruppo non valutato")
            continue
        c(f"gruppo {nome}: almeno {AVVISO_COPPIE} coppie", n >= AVVISO_COPPIE, dettaglio=f"{n} coppie")
        gruppi[k] = {"nome": nome, **analizza_gruppo(per_gruppo[k])}
        g = gruppi[k]
        for f in g.get("fasce", []):
            if f["quota_mezzi"] is not None:
                c(f"gruppo {nome}: quota {f['da']}-{f['a']} fra 0 e 1", 0 <= f["quota_mezzi"] <= 1, bloccante=True)

    # Variante a giornata intera: NON e' la regola fissata (fascia 6-10); serve solo a dire a Leo cosa si vedrebbe, non va in pagina.
    pg_g, _, _ = abbina(coppie_tp, quote_per_coppia(spost, pub, ore=tuple(range(24))))
    variante = {"nota": "variante a giornata intera, non e' la regola fissata: solo per informare, non entra nelle schede",
                "gruppi": {k: ({"nome": GRUPPI[k], **analizza_gruppo(v)} if (k != "c" or len(v) >= MIN_COPPIE_CINTURA) else
                               {"nome": GRUPPI[k], "coppie": len(v), "non_valutato": True}) for k, v in pg_g.items()}}
    out = {"titolo": "Dove i mezzi pubblici sono lenti, si prende l'auto?", "frase": FRASE,
           "regole": {"ore_partenza": [ORE[0], ORE[-1] + 1], "soglia_interviste": SOGLIA_N, "ricampionamenti": RICAMPIONAMENTI, "seme": SEME,
                      "fasce": [[a, None if b > 50 else b] for a, b in FASCE], "rapporto": "stima aperta alle 8 (rapporto_basso di tp_contro_auto.json)",
                      "quota": "mezzi pubblici / (mezzi pubblici + auto conducente + auto passeggero)", "prova": bool(args.prova)},
           "gruppi": gruppi, "variante_giornata": variante, "controlli": c.righe}
    out_json = OUT_JSON.with_name("scelta_del_mezzo_prova.json") if args.prova else OUT_JSON
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    righe = ["SCELTA DEL MEZZO (script 102) - partenze 6-10 di un feriale, indagine IMQ 2022, tempi della stima aperta alle 8", FRASE, ""]
    for k, g in gruppi.items():
        righe.append(f"{g['nome']}: {g['coppie']} coppie, {g['interviste']} interviste" + (" (gruppo non valutato)" if g.get("non_valutato") else ""))
        if g.get("non_valutato") or not g["coppie"]:
            continue
        iv = g["intervallo95"]
        righe.append(f"  Spearman {g['spearman']}, intervallo 95% {iv}, {'REGGE' if g['regge'] else 'non regge'}; quota mezzi {100 * g['quota_mezzi_totale']:.1f}%")
        for f in g["fasce"]:
            righe.append(f"  rapporto {f['da']}-{f['a']}: quota mezzi {None if f['quota_mezzi'] is None else round(100 * f['quota_mezzi'], 1)}%, {f['coppie']} coppie, {f['interviste']} interviste")
    righe += ["", "VARIANTE a giornata intera (NON e' la regola fissata, solo per informare)"]
    for k, g in variante["gruppi"].items():
        righe.append(f"{g['nome']}: {g['coppie']} coppie" + ("" if g.get("non_valutato") else f", Spearman {g.get('spearman')}, intervallo 95% {g.get('intervallo95')}, {'regge' if g.get('regge') else 'non regge'}"))
    righe += ["", "CONTROLLI"] + c.righe
    rapporto = RAPPORTO.with_name("RAPPORTO_SCELTA_DEL_MEZZO_prova.txt") if args.prova else RAPPORTO
    rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe[:20]))
    print("avvisi:", len(c.avvisi()))


if __name__ == "__main__":
    main()
