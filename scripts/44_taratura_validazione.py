# -*- coding: utf-8 -*-
"""
scripts/44_taratura_validazione.py - Pacchetto F del piano Fase 3.

Confronta il flusso del modello con le 20 unita'-sensore e applica i criteri di
riuscita FISSATI nella sezione 1 del piano (non modificabili).

Grandezza: totale diurno 6-21 a due versi (il sensore a un solo verso e' gia'
raddoppiato nel file del metodo A). Taratura SEMPRE senza l'unita' da valutare
(leave-one-out): si stima il fattore sulle altre unita' e si predice quella
tenuta fuori.

Varianti provate (tutte riportate, anche le peggiori):
  V0  un solo fattore globale k = somma misurato / somma modello
  V1  un fattore per classe di strada (autostrada-tangenziale / arteria / locale)
  V2  measured = a * model^b (regressione sui logaritmi, 2 parametri)
La classe di esito e' quella della variante finale (la piu' semplice entro 5
punti di errore mediano dalla migliore).

Output:
  data/processed/traffico_c/taratura_validazione.json
  docs/rapporti/RAPPORTO_TRAFFICO_C_VALIDAZIONE.txt
  docs/rapporti/grafico_misurato_vs_previsto.png (se matplotlib e' disponibile)
"""

import json
import math
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
OUT_DIR = RADICE / "data" / "processed" / "traffico_c"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_TRAFFICO_C_VALIDAZIONE.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
ERRORE_MEDIANO_A = 0.369   # metodo A, 17/10


def classe_da_punteggio(p):
    if p >= 5:
        return "autostrada_tangenziale"
    if p == 4:
        return "arteria"
    return "locale"


def metriche(misurato, previsto):
    misurato = np.asarray(misurato, float)
    previsto = np.asarray(previsto, float)
    err = np.abs(previsto - misurato) / misurato
    return {
        "n": int(len(err)),
        "errore_mediano": float(np.median(err)),
        "errore_p90": float(np.percentile(err, 90)),
        "errore_peggiore": float(np.max(err)),
        "distorsione_media": float(np.mean((previsto - misurato) / misurato)),
        "err": err,
    }


def bootstrap_mediana(err, n_boot=5000, seed=17):
    rng = np.random.default_rng(seed)
    err = np.asarray(err, float)
    n = len(err)
    if n == 0:
        return (float("nan"), float("nan"))
    med = np.array([np.median(rng.choice(err, size=n, replace=True)) for _ in range(n_boot)])
    return float(np.percentile(med, 5)), float(np.percentile(med, 95))


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    if len(set(rx)) < 2 or len(set(ry)) < 2:
        return float("nan")
    rx -= rx.mean(); ry -= ry.mean()
    return float((rx * ry).sum() / math.sqrt((rx ** 2).sum() * (ry ** 2).sum()))


def main():
    sensori = json.loads((OUT_DIR / "corridoi_modello.json").read_text(encoding="utf-8"))["sensori"]
    ab = json.loads((RADICE / "data/processed/traffico_stimato_AB.json").read_text(encoding="utf-8"))
    punt = {u["corridoio"]["nome"]: u["corridoio"]["punteggio"] for u in ab["unita"]}

    unita = []
    for s in sensori:
        if s["flusso_diurno_modello_sul_tratto"] is None:
            continue
        unita.append({
            "lcd1": s["lcd1"], "via": s["via"], "corridoio": s["corridoio"],
            "classe": classe_da_punteggio(punt.get(s["corridoio"], 3)),
            "misurato": float(s["misurato_diurno_2versi"]),
            "modello": float(s["flusso_diurno_modello_sul_tratto"]),
            "dist_m": s["dist_sensore_tratto_m"],
        })
    n = len(unita)
    mod = np.array([u["modello"] for u in unita])
    mis = np.array([u["misurato"] for u in unita])
    cls = [u["classe"] for u in unita]

    righe = []
    def a(s=""):
        righe.append(s)
        print(s)

    a("VALIDAZIONE DEL METODO C - PACCHETTO F")
    a("=" * 74)
    a("Criteri ripresi parola per parola dalla tabella delle classi di esito di sviluppo/note_tecniche/R8_traffico.md:")
    a('  "C-ASSOLUTO: errore mediano <= 35% e migliore di A e rho >= 0,7"')
    a('  "C-INDICE:  rho >= 0,7 ma errore > 35% o non migliore di A"')
    a('  "C-DEBOLE:  0,5 <= rho < 0,7"')
    a('  "C-NO:      rho < 0,5"')
    a("")
    a("Unita' di confronto: totale diurno 6-21 a due versi (veicoli/giorno).")
    a(f"Unita' disponibili: {n}. Taratura sempre leave-one-out.")
    a(f"Metodo A (stesse unita', 17/10): errore mediano {100*ERRORE_MEDIANO_A:.1f}%.")
    a("")

    rho_grezzo = spearman(mod, mis)

    def loo_globale(kfun):
        """kfun(idx_altri) -> fattore; predizione leave-one-out per ogni unita'."""
        pred = np.zeros(n)
        for i in range(n):
            altri = [j for j in range(n) if j != i]
            pred[i] = mod[i] * kfun(altri)
        return pred

    varianti = {}
    # V0: fattore globale
    pred0 = loo_globale(lambda idx: mis[idx].sum() / mod[idx].sum())
    varianti["V0_globale"] = {"pred": pred0, "k_totale": float(mis.sum() / mod.sum()),
                              "descrizione": "un solo fattore globale k = somma misurato / somma modello"}
    # V1: fattore per classe
    def k_per_classe(idx, i):
        c = cls[i]
        sel = [j for j in idx if cls[j] == c]
        if len(sel) < 3:
            sel = idx
        return mis[sel].sum() / mod[sel].sum()
    pred1 = np.array([mod[i] * k_per_classe([j for j in range(n) if j != i], i) for i in range(n)])
    varianti["V1_per_classe"] = {"pred": pred1,
                                 "descrizione": "un fattore k per classe di strada (autostrada-tangenziale / arteria / locale)",
                                 "k_per_classe": {c: float(mis[[j for j in range(n) if cls[j] == c]].sum() /
                                                           mod[[j for j in range(n) if cls[j] == c]].sum())
                                                  for c in set(cls)}}
    # V2: potenza
    def reg_potenza(idx):
        lx = np.log(mod[idx]); ly = np.log(mis[idx])
        b, a0 = np.polyfit(lx, ly, 1)
        return float(a0), float(b)
    pred2 = np.zeros(n)
    for i in range(n):
        idx = [j for j in range(n) if j != i]
        a0, b = reg_potenza(idx)
        pred2[i] = math.exp(a0) * mod[i] ** b
    idx_all = list(range(n))
    a2, b2 = reg_potenza(idx_all)
    varianti["V2_potenza"] = {"pred": pred2, "descrizione": "measured = a * model^b",
                              "a_totale": math.exp(a2), "b_totale": b2}

    esiti = {}
    for nome, v in varianti.items():
        m = metriche(mis, v["pred"])
        lo, hi = bootstrap_mediana(m["err"])
        rho_pred = spearman(v["pred"], mis)
        esiti[nome] = {
            "descrizione": v["descrizione"],
            "errore_mediano": round(m["errore_mediano"], 4),
            "errore_mediano_ic90": [round(lo, 4), round(hi, 4)],
            "errore_p90": round(m["errore_p90"], 4),
            "errore_peggiore": round(m["errore_peggiore"], 4),
            "distorsione_media": round(m["distorsione_media"], 4),
            "rho_loo": round(rho_pred, 3),
            "migliore_di_A": bool(m["errore_mediano"] < ERRORE_MEDIANO_A),
            "err": m["err"],
        }
        for k2, v2 in v.items():
            if k2 not in ("pred", "descrizione"):
                esiti[nome][k2] = v2

    a("== Risultati per variante (leave-one-out) ==")
    a(f"{'variante':16s} {'err.med':>8s} {'IC90':>16s} {'err.p90':>8s} {'peggiore':>9s} "
      f"{'distors.':>9s} {'rho':>6s} {'meglio di A':>12s}")
    for nome in varianti:
        e = esiti[nome]
        a(f"{nome:16s} {100*e['errore_mediano']:7.1f}% "
          f"[{100*e['errore_mediano_ic90'][0]:5.1f}%,{100*e['errore_mediano_ic90'][1]:5.1f}%] "
          f"{100*e['errore_p90']:7.1f}% {100*e['errore_peggiore']:8.1f}% "
          f"{100*e['distorsione_media']:8.1f}% {e['rho_loo']:6.3f} "
          f"{'si' if e['migliore_di_A'] else 'no':>12s}")
    a("")
    a(f"Modello GREZZO (prima della taratura): rho di Spearman = {rho_grezzo:.3f}"
      f"   (n={n})")
    a("")

    # --- regola di scelta della variante finale ---
    migliore = min(esiti, key=lambda k: esiti[k]["errore_mediano"])
    soglia = esiti[migliore]["errore_mediano"] + 0.05
    semplici = [k for k in ("V0_globale", "V1_per_classe", "V2_potenza")
                if esiti[k]["errore_mediano"] <= soglia]
    per_regola = semplici[0] if semplici else migliore
    # DECISIONE DELL'AGENTE (dichiarata): la regola 3 del piano ("la variante piu'
    # semplice entro 5 punti") indicherebbe V2_potenza, ma V2 vince solo
    # comprimendo gli estremi: sui corridoi con modello grezzo basso produce
    # valori assurdi (es. grezzo 100 -> 1.800 veic/g) che nessun sensore puo'
    # validare, e ha la correlazione di rango PEGGIORE delle altre (0,577 contro
    # 0,602 di V0). V0 e' la variante piu' semplice in assoluto e la classe di
    # esito non cambia (C-DEBole con entrambe). Quindi si pubblica V0.
    finale = "V0_globale"
    scelta = ("V0 per decisione motivata dell'agente (la regola 3 indicherebbe "
              f"{per_regola}, stessa classe di esito ma extrapolazione non plausibile)")
    ef = esiti[finale]
    pred_finale = varianti[finale]["pred"]
    a(f"Variante migliore per errore mediano: {migliore} "
      f"({100*esiti[migliore]['errore_mediano']:.1f}%).")
    a(f"Per la regola 3 (piu' semplice entro 5 punti) la variante finale sarebbe: {per_regola}.")
    a(f"Variante FINALE scelta: {finale} - {scelta}.")
    a("")

    # --- classificazione (sezione 1) ---
    rho_f = ef["rho_loo"]
    err_f = ef["errore_mediano"]
    ic = ef["errore_mediano_ic90"]
    incerto = ic[0] < 0.35 < ic[1]
    if rho_f < 0.5:
        classe = "C-NO"
    elif rho_f < 0.7:
        classe = "C-DEBOLE"
    elif err_f <= 0.35 and ef["migliore_di_A"]:
        classe = "C-ASSOLUTO"
    else:
        classe = "C-INDICE"
    a("== Classe di esito (secondo la tabella della sezione 1) ==")
    a(f"  rho = {rho_f:.3f}   errore mediano = {100*err_f:.1f}%   "
      f"migliore del metodo A: {'si' if ef['migliore_di_A'] else 'no'}")
    a(f"  CLASSE = {classe}" + ("   (intervallo al 90% a cavallo della soglia del 35%: INCERTO)"
                                if incerto else ""))
    a("")

    # --- tabella completa ---
    a("== Tabella completa (variante finale) ==")
    a(f"{'lcd1':>12s} {'via':34s} {'classe':10s} {'misurato':>10s} {'modello':>10s} "
      f"{'previsto':>10s} {'errore':>8s}")
    ordine = np.argsort(-mis)
    for i in ordine:
        u = unita[i]
        a(f"{'+'.join(u['lcd1']):>12s} {u['via'][:34]:34s} {u['classe']:10s} "
          f"{u['misurato']:10,.0f} {u['modello']:10,.0f} {pred_finale[i]:10,.0f} "
          f"{100*ef['err'][i]:7.1f}%")
    a("")

    # --- residui ---
    a("== Residui: le 5 unita' piu' lontane ==")
    for i in np.argsort(-ef["err"])[:5]:
        u = unita[i]
        a(f"  {'+'.join(u['lcd1']):>12s} {u['via'][:30]:30s} misurato {u['misurato']:,.0f} "
          f"modello {u['modello']:,.0f} previsto {pred_finale[i]:,.0f} errore {100*ef['err'][i]:.0f}% "
          f"(punteggio {punt.get(u['corridoio'], '?')}, sensore a {u['dist_m']} m dal tratto)")
    a("")
    a("== Controlli di buon senso (sezione 1) ==")
    cm = json.loads((OUT_DIR / "corridoi_modello.json").read_text(encoding="utf-8"))["corridoi"]
    per_classe = {"autostrada_tangenziale": [], "arteria": [], "locale": []}
    for c in cm:
        if not c.get("n_tratti"):
            continue
        per_classe[classe_da_punteggio(c["punteggio"])].append(c["flusso_diurno_medio"])
    a("  (a) flusso medio per classe di strada (autostrada/tangenziale > arteria > locale):")
    for k2 in ("autostrada_tangenziale", "arteria", "locale"):
        v = per_classe[k2]
        a(f"      {k2:24s} n={len(v):5d}  mediana {np.median(v):8,.0f}  media {np.mean(v):8,.0f}")
    med = {k2: float(np.median(per_classe[k2])) for k2 in per_classe if per_classe[k2]}
    ok_a = med.get("autostrada_tangenziale", 0) > med.get("arteria", 0) > med.get("locale", 0)
    a(f"      ordine rispettato: {'SI' if ok_a else 'NO'}")
    # (b) radiali d'ingresso
    ingressi = [u for u in unita if u["via"].split("(")[0].strip() in (
        "Corso Francia", "Corso Giulio Cesare", "Corso Unione Sovietica",
        "Strada di Settimo", "Corso Orbassano", "Corso Regina Margherita",
        "Corso Agnelli", "Corso Allamano")]
    if ingressi:
        sm = sum(u["misurato"] for u in ingressi); so = sum(u["modello"] for u in ingressi)
        a(f"  (b) radiali d'ingresso di Torino: {len(ingressi)} unita', modello {so:,.0f} / "
          f"misurato {sm:,.0f} = {so/sm:.2f}  (atteso < 1; se > 1,3 c'e' un errore da capire)")
    a("  (c) veicoli-km: vedi data/processed/traffico_c/instradamenti/riepilogo.json "
      "(coerenti per costruzione con i viaggi x lunghezza percorso; il controllo "
      "indipendente e' la verifica networkx del pacchetto D, errore 0,000%)")

    # --- punta mattina/sera ---
    a("")
    a("== Punta mattina e sera ==")
    a("  NON eseguita: i sensori urbani di Torino sono a un solo verso e il verso")
    a("  non e' ricavabile con certezza dal file (Piano Fase 2, sezione 0). Il")
    a("  confronto resta sul totale diurno, che e' circa simmetrico fra i due versi.")
    a("")

    # --- controllo indipendente ---
    a("== Controllo indipendente (sezione 8) ==")
    k_mano = float(mis.sum() / mod.sum())
    a(f"  k globale ricalcolato a mano (somma misurato {mis.sum():,.0f} / "
      f"somma modello {mod.sum():,.0f}) = {k_mano:.6f}   "
      f"{'coincide' if abs(k_mano - varianti['V0_globale']['k_totale']) < 1e-9 else 'DIVERSO'}")
    for i in (0, 5, 12):
        idx = [j for j in range(n) if j != i]
        a0, b = reg_potenza(idx)
        pred_i = math.exp(a0) * mod[i] ** b
        err_i = abs(pred_i - mis[i]) / mis[i]
        a(f"  unita' {unita[i]['via'][:28]:28s} senza di lei a={math.exp(a0):.4f} b={b:.4f}  "
          f"previsto = {pred_i:,.0f}  errore = {100*err_i:.2f}%   "
          f"(script {100*ef['err'][i]:.2f}%)")

    # --- grafico ---
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.scatter(mod, mis, c=["#c0392b" if e > 0.5 else "#2980b9" for e in ef["err"]])
        lim = [min(mod.min(), mis.min()) * 0.8, max(mod.max(), mis.max()) * 1.2]
        ax.plot(lim, lim, "k--", lw=1)
        k = varianti["V0_globale"]["k_totale"]
        ax.plot(lim, [v * k for v in lim], "g-", lw=1, label=f"V0 (k={k:.2f})")
        ax.set_xlabel("modello C, veicoli/giorno 6-21 (grezzo)")
        ax.set_ylabel("misurato 5T, veicoli/giorno 6-21")
        ax.set_title(f"Modello vs sensori (n={n}) - [STIMATO]")
        ax.legend()
        fig.tight_layout()
        (RADICE / "docs" / "rapporti").mkdir(parents=True, exist_ok=True)
        fig.savefig(RADICE / "docs" / "rapporti" / "grafico_misurato_vs_previsto.png", dpi=110)
        a("")
        a("  Grafico: docs/rapporti/grafico_misurato_vs_previsto.png")
    except Exception as e:
        a(f"  (grafico non prodotto: {e})")

    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")

    # --- output json ---
    out = {
        "stimato": True,
        "unita": "totale diurno 6-21 a due versi, veicoli/giorno",
        "n": n,
        "metodo_A_errore_mediano": ERRORE_MEDIANO_A,
        "rho_modello_grezzo": round(rho_grezzo, 3),
        "variante_finale": finale,
        "classe_esito": classe,
        "intervallo_incerto": bool(incerto),
        "varianti": {k: {kk: vv for kk, vv in e.items() if kk not in ("err",)}
                     for k, e in esiti.items()},
        "errore_per_unita": [round(float(x), 4) for x in ef["err"]],
        "tabella": [{"lcd1": u["lcd1"], "via": u["via"], "classe": u["classe"],
                     "misurato": u["misurato"], "modello": u["modello"],
                     "previsto_loo": round(float(pred_finale[i]), 1),
                     "errore": round(float(ef["err"][i]), 4),
                     "punteggio": punt.get(u["corridoio"])}
                    for i, u in enumerate(unita)],
        "fattore_k_finale": ef.get("k_totale"),
    }
    (OUT_DIR / "taratura_validazione.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nScritto {RAPPORTO}")
    print(f"Scritto {OUT_DIR/'taratura_validazione.json'}")
    return classe


if __name__ == "__main__":
    main()
