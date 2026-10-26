# -*- coding: utf-8 -*-
"""
scripts/53_pubblicazione_traffico.py - Pacchetto C del piano Fase 4.

Pubblica il traffico per corridoio con NUMERI ASSOLUTI (con fascia di errore),
VALORI RELATIVI (quintili, rapporto sulla mediana di Torino) e GRADUATORIA,
usando la variante finale scelta (V0 o V3, da v3/valutazione_v3.json).

Non sovrascrive il file della Fase 3 (data/processed/traffico_stimato_finale.json):
scrive data/processed/traffico_stimato_finale_v2.json.

Universo di Torino: corridoi con "(Torino)" nel nome, lunghezza >= 300 m,
escluse autostrade/tangenziali/raccordi (punteggio >= 5 o nome), corridoi a
flusso nullo e quelli affidabile=false (valori di bordo assurdi). Prima cintura:
i comuni confinanti con la stessa regola.
"""

import json
import re
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
PROC = AQUI.parent / "data" / "processed"
OUT_DIR = PROC / "traffico_c"
RAPPORTO = AQUI.parent / "docs" / "rapporti" / "RAPPORTO_TRAFFICO_C_V2.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
SENS_AB = PROC / "traffico_stimato_AB.json"

CINTURA = {"Beinasco", "Borgaro Torinese", "Collegno", "Druento", "Grugliasco", "Moncalieri",
           "Nichelino", "Orbassano", "Pecetto Torinese", "Pino Torinese", "San Mauro Torinese",
           "Settimo Torinese", "Venaria Reale"}
AUTOSTRADA = re.compile(r"autostrada|tangenziale|raccordo", re.I)
SOGLIA_ASSURDO = 80000.0
MIN_LUNG = 0.3     # km


def quantile_rank(v, v_all):
    return 1.0 * np.searchsorted(np.sort(v_all), v, side="left") / max(len(v_all), 1)


def main():
    val = json.loads((OUT_DIR / "v3" / "valutazione_v3.json").read_text(encoding="utf-8"))
    variante = val["variante_finale"]
    classe = val["classe_esito"]
    if variante == "V3":
        cor = json.loads((OUT_DIR / "v3" / "corridoi_v3.json").read_text(encoding="utf-8"))
        corridoi = cor["corridoi"]; sensori = cor["sensori"]
        k = val["varianti"]["V3"]["k_totale"]
    else:
        corridoi = json.loads((OUT_DIR / "corridoi_modello.json").read_text(encoding="utf-8"))["corridoi"]
        sensori = json.loads((OUT_DIR / "corridoi_modello.json").read_text(encoding="utf-8"))["sensori"]
        k = json.loads((OUT_DIR / "taratura_validazione.json").read_text(encoding="utf-8"))["fattore_k_finale"]

    fascia_50 = val["errore_mediano"]
    fascia_90 = val["varianti"][variante]["errore_p90"]

    # modello sui tratti dei sensori (per definire l'intervallo "validato")
    mod_sens = [s["flusso_diurno_modello_sul_tratto"] for s in sensori
                if s.get("flusso_diurno_modello_sul_tratto") is not None]
    lim_inf, lim_sup = (min(mod_sens), max(mod_sens)) if mod_sens else (0.0, 1e9)
    mis_per_corridoio = {s["corridoio"]: s["misurato_diurno_2versi"] for s in sensori}

    # registri per corridoio
    reg = []
    for c in corridoi:
        nome = c["nome"]
        lung = c.get("lunghezza_km") or 0.0
        ptg = c.get("punteggio")
        grezzo = c.get("flusso_diurno_medio")
        misura = mis_per_corridoio.get(nome)
        if misura is not None:
            veic = float(misura); stimato = False
        elif grezzo is not None:
            veic = float(grezzo) * k; stimato = True
        else:
            veic = 0.0; stimato = True
        affidabile = not (ptg is not None and ptg <= 2 and veic > SOGLIA_ASSURDO)
        estrap = bool(stimato and grezzo is not None and not (lim_inf <= grezzo <= lim_sup))
        # fuori dall'intervallo validato la fascia si allarga a un valore dichiarato (x2)
        f50 = fascia_50 * (2.0 if estrap else 1.0)
        f90 = fascia_90 * (2.0 if estrap else 1.0)
        reg.append({
            "nome": nome, "chiave": c.get("chiave_normalizzata") or c.get("chiave"),
            "comune": c.get("comune"), "punteggio": ptg, "lunghezza_km": round(lung, 3),
            "n_tratti": c.get("n_tratti", 0),
            "veic_giorno": round(veic, 1),
            "stimato": stimato, "misurato": not stimato,
            "estrapolazione": bool(estrap),
            "fascia_50": round(f50, 3), "fascia_90": round(f90, 3),
            "fascia_50_base": round(fascia_50, 3), "fascia_90_base": round(fascia_90, 3),
            "affidabile": bool(affidabile),
            "fiducia": ("alta" if not stimato else "bassa"),
            "classe_esito": classe,
            "modello_grezzo": None if grezzo is None else round(float(grezzo), 1),
        })

    # filtro autostrade
    def e_autostrada(r):
        return (r["punteggio"] is not None and r["punteggio"] >= 5) or bool(AUTOSTRADA.search(r["nome"] or ""))

    def in_universo(r, comuni):
        if r["comune"] not in comuni:
            return False
        if r["lunghezza_km"] < MIN_LUNG:
            return False
        if e_autostrada(r):
            return False
        if r["veic_giorno"] <= 0 or not r["n_tratti"]:
            return False
        if not r["affidabile"]:
            return False
        return True

    torino = [r for r in reg if in_universo(r, {"Torino"})]
    cintura = [r for r in reg if in_universo(r, CINTURA)]

    valori_torino = np.array([r["veic_giorno"] for r in torino])
    mediana = float(np.median(valori_torino)) if len(valori_torino) else 0.0
    q20, q40, q60, q80 = (np.percentile(valori_torino, [20, 40, 60, 80]) if len(valori_torino)
                          else [0, 0, 0, 0])
    q33, q67 = (np.percentile(valori_torino, [33.3, 66.7]) if len(valori_torino) else [0, 0])

    ord_torino = sorted(torino, key=lambda r: -r["veic_giorno"])
    pos_torino = {id(r): i + 1 for i, r in enumerate(ord_torino)}
    ord_cintura = sorted(cintura, key=lambda r: -r["veic_giorno"])
    pos_cintura = {id(r): i + 1 for i, r in enumerate(ord_cintura)}

    for r in reg:
        if r in torino or r in cintura:
            v = r["veic_giorno"]
            r["indice_1_5"] = int(1 + np.searchsorted([q20, q40, q60, q80], v, side="right"))
            r["rapporto_su_mediana_torino"] = round(v / mediana, 4) if mediana else None
            r["posizione_torino"] = pos_torino.get(id(r))
            r["posizione_cintura"] = pos_cintura.get(id(r))
            r["classe3"] = "alto" if v >= q67 else ("medio" if v >= q33 else "basso")
            r["km"] = r["lunghezza_km"]
        else:
            r["nel_universo"] = False
    for r in torino + cintura:
        r["nel_universo"] = True

    doc = {
        "stimato": True,
        "variante_finale": variante,
        "classe_esito": classe,
        "nota": ("Numeri assoluti = veicoli/giorno 6-21 a due versi, con fascia di "
                 "errore. fascia_50 = errore mediano leave-one-out; fascia_90 = 90esimo "
                 "percentile. Dove il modello grezzo e' fuori dall'intervallo dei sensori "
                 "la stima e' un'estrapolazione (campo estrapolazione=true) e la fascia va "
                 "letta piu' larga. Classe di esito (Fase 3) accanto a ogni numero."),
        "taratura": {"k": k, "fascia_50": round(fascia_50, 4), "fascia_90": round(fascia_90, 4),
                     "intervallo_validato_modello_grezzo": [round(lim_inf, 1), round(lim_sup, 1)]},
        "universo_torino": {"n_corridoi": len(torino),
                            "km": round(sum(r["lunghezza_km"] for r in torino), 1),
                            "mediana_veic_giorno": round(mediana, 1),
                            "soglie_classe3": {"q33": round(float(q33), 1), "q67": round(float(q67), 1)}},
        "universo_cintura": {"n_corridoi": len(cintura),
                             "km": round(sum(r["lunghezza_km"] for r in cintura), 1)},
        "corridoi": reg,
    }
    (PROC / "traffico_stimato_finale_v2.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    righe = []
    a = righe.append
    a("PUBBLICAZIONE DEL TRAFFICO - PACCHETTO C (numeri assoluti, relativi, graduatoria)")
    a("=" * 78)
    a(f"variante finale: {variante}   classe di esito (Fase 3): {classe}")
    a(f"taratura: k = {k:.4f}")
    a(f"accuratezza dichiarata dei numeri assoluti: in meta' dei casi lo scarto e' entro "
      f"+-{100*fascia_50:.0f}%; 9 volte su 10 entro +-{100*fascia_90:.0f}%.")
    a(f"corridoi totali: {len(reg):,}   con sensore (misurato): {sum(1 for r in reg if r['misurato'])}")
    a(f"UNIVERSO DI TORINO: {len(torino):,} corridoi, {sum(r['lunghezza_km'] for r in torino):,.1f} km "
      f"(mediana {mediana:,.0f} veic/g)")
    a(f"PRIMA CINTURA: {len(cintura):,} corridoi, {sum(r['lunghezza_km'] for r in cintura):,.1f} km")
    a(f"soglie classe3 dentro l'universo di Torino: medio da {q33:,.0f}, alto da {q67:,.0f} veic/giorno")
    a(f"corridoi in estrapolazione (fuori dall'intervallo dei sensori): "
      f"{sum(1 for r in reg if r['estrapolazione'])}, di cui nell'universo di Torino: "
      f"{sum(1 for r in torino if r['estrapolazione'])}")
    a("  per questi la fascia e' allargata a x2 (valore dichiarato): "
      f"+-{100*2*fascia_50:.0f}% (50%) e +-{100*2*fascia_90:.0f}% (90%)")
    a("")
    a("== I 20 corridoi di Torino con piu' traffico (universo) ==")
    for r in ord_torino[:20]:
        a(f"  {r['veic_giorno']:9,.0f} +-{100*fascia_50:2.0f}% [{r['classe3']:5s}] "
          f"p{r['punteggio']} {r['nome'][:44]:44s} pos {r['posizione_torino']:4d} "
          f"{'MISURATO' if r['misurato'] else 'stimato'}")
    a("")
    a("== I 20 corridoi della prima cintura con piu' traffico ==")
    for r in ord_cintura[:20]:
        a(f"  {r['veic_giorno']:9,.0f}  {r['nome'][:44]:44s} ({r['comune']}) pos cintura {r['posizione_cintura']}")
    a("")
    a("File: data/processed/traffico_stimato_finale_v2.json (il file della Fase 3 resta intatto)")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
