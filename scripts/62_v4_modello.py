# -*- coding: utf-8 -*-
"""
scripts/62_v4_modello.py - Pacchetto E (Fase 5): modello del traffico V4.

Cosa cambia rispetto a V0 (Fase 3): destinazioni per attrattori (punti_v3),
CONGESTIONE con capacita' per CORSIA (pacchetto B) e domanda di punta, ZTL e
aree pedonali (pacchetto C), porte di rango >= 3.

  - capacita' di un arco = corsie del verso x capacita' per corsia (rete_osm);
  - funzione di ritardo BPR t = t0 * (1 + 0,15 * (v/c)^4), metodo delle medie
    successive (MSA), caso principale = punta del mattino (7-9);
  - durante le ore ZTL (7-9 per la ZTL centrale) i tratti in ZTL sono chiusi al
    traffico di attraversamento (tempo x100); i tratti pedonali sono tolti
    (tempo x1e6);
  - il giorno (6-21) si assegna sulla rete con i tempi di punta congestionati.

Varianti (--variante): v0 (popolazione, niente congestione/ZTL, tutte le porte),
v4 (tutto), abl1 (v4 senza attrattori), abl2 (v4 senza congestione),
abl3 (v4 senza porte ristrette).

Output in data/processed/traffico_d/<outdir>/:
  archi_flusso.npz, tratte_flusso.json, riepilogo.json
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rete_osm  # noqa: E402
import importlib
v3 = importlib.import_module("50_v3_assegnazione")

PROC = AQUI.parent / "data" / "processed"
OUT = PROC / "traffico_d"
RETE_DIR = OUT / "rete"
ALPHA, BETA = 0.15, 4.0
PENALITA_ZTL = 100.0
PENALITA_PED = 1e6


def carica_ztl_edges(n_edge, edge_tratta, ore_punta=(7, 8)):
    """Sete di archi (tratti) in ZTL durante le ore di punta e pedonali."""
    ztl_per_tratta = {}
    ped_per_tratta = {}
    p = OUT / "tratte_ztl.csv"
    if p.is_file():
        import csv
        with p.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter=";"):
                ore = [int(x) for x in r["ztl_ore"].split("|") if x]
                ztl_per_tratta[int(r["id_tratta"])] = (float(r["ztl_frazione"]), ore)
                ped_per_tratta[int(r["id_tratta"])] = float(r["pedonale_frazione"])
    et = edge_tratta
    ztl_punta = np.zeros(n_edge, bool)
    ped = np.zeros(n_edge, bool)
    for e in range(n_edge):
        t = int(et[e])
        if t < 0:
            continue
        fr, ore = ztl_per_tratta.get(t, (0.0, []))
        if fr >= 0.5 and any(h in ore for h in ore_punta):
            ztl_punta[e] = True
        if ped_per_tratta.get(t, 0.0) >= 0.5:
            ped[e] = True
    return ztl_punta, ped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variante", default="v4", choices=["v0", "v4", "abl1", "abl2", "abl3"])
    ap.add_argument("--iter", type=int, default=8)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--prova", type=int, default=0, help="usa solo N origini (prova rapida)")
    args = ap.parse_args()
    outdir = OUT / (args.outdir or args.variante)
    outdir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    rete = rete_osm.carica(RETE_DIR)
    xy = rete["nodi_xy"]; meta = rete["meta"]; N = len(xy)
    archi = rete["archi"]
    src = archi[:, 0].astype(np.int64); dst = archi[:, 1].astype(np.int64)
    t_arc0 = archi[:, 2].astype(np.float64)
    ind_edge = archi[:, 3].astype(np.int64)
    dir_arc = archi[:, 4].astype(np.int64)
    n_archi = len(archi); n_edge = len(rete["edge_a"])

    corsie_av = np.array(meta["corsie_avanti"] if "corsie_avanti" in meta
                         else [1] * n_edge, dtype=np.float64)
    corsie_in = np.array(meta["corsie_indietro"] if "corsie_indietro" in meta
                         else [1] * n_edge, dtype=np.float64)
    hw = meta["highway"]
    cap_per_corsia = np.array([rete_osm.CAPACITA_CORSIA.get(hw[e], 500) for e in range(n_edge)],
                              dtype=np.float64)
    cap_arc = np.where(dir_arc == 0, np.maximum(corsie_av[ind_edge], 1) * cap_per_corsia[ind_edge],
                       np.maximum(corsie_in[ind_edge], 1) * cap_per_corsia[ind_edge])

    # --- domanda ---
    TC = OUT.parent / "traffico_c"
    if args.variante in ("v0", "abl1"):
        punti = json.loads((TC / "punti.json").read_text(encoding="utf-8"))["zone"]
        punti = {cod: {"casa": elenco} for cod, elenco in punti.items()}
    else:
        punti = json.loads((TC / "v3" / "punti_v3.json").read_text(encoding="utf-8"))["zone"]
    if args.variante == "v0":
        domanda = json.loads((TC / "domanda_auto.json").read_text(encoding="utf-8"))
    else:
        domanda = json.loads((TC / "v3" / "domanda_v3.json").read_text(encoding="utf-8"))
    if args.variante in ("v0", "abl3"):
        porte = json.loads((TC / "porte.json").read_text(encoding="utf-8"))["porte"]
    else:
        porte = json.loads((TC / "v3" / "porte_v3.json").read_text(encoding="utf-8"))["porte"]

    # le celle di domanda_auto (V0) hanno 5 campi: aggiungi i gruppi "casa"
    domanda["celle"] = [(list(c) + ["casa", "casa"])[:7] for c in domanda["celle"]]
    origini, peso_tot, perso_self, perso_zone, dett = v3.costruisci_domanda_nodi(punti, domanda, porte, N)
    lista_origini = sorted(origini)
    if args.prova:
        lista_origini = lista_origini[:args.prova]
    peso_conv = sum(float(v[1].sum()) for v in origini.values())
    share_diurno = sum(domanda["quote_orarie"][str(h)] for h in range(6, 22))
    peak_share = (domanda["quote_orarie"]["7"] + domanda["quote_orarie"]["8"]) / 2.0
    print(f"[{args.variante}] origini {len(lista_origini):,}  peso {peso_tot:,.0f}  "
          f"flusso {peso_conv:,.0f} ({100*peso_conv/peso_tot:.1f}%)  share diurno {share_diurno:.3f}  "
          f"punta {peak_share:.4f}")

    # --- ZTL / pedonali ---
    et = np.load(OUT / "assi_tratte.npz")["edge_tratta"]
    ztl_punta, ped = carica_ztl_edges(n_edge, et)
    print(f"[{args.variante}] tratti in ZTL in punta: {int(ztl_punta.sum()):,}   "
          f"pedonali: {int(ped.sum()):,}")

    def matrice_da(t_arc):
        return v3.matrice(src, dst, t_arc, N)

    congestione = args.variante in ("v4", "abl1", "abl3")

    if not congestione:
        t_arc = t_arc0.copy()
        if args.variante == "v4" or args.variante == "abl1" or args.variante == "abl3":
            pass
        M, chiavi, idx = matrice_da(t_arc)
        flusso_day = v3.assegna(M, chiavi, idx, origini, lista_origini, N, n_archi)
        t_arc_fin = t_arc
        vc = np.zeros(n_archi)
    else:
        F = np.zeros(n_archi)
        t_arc = t_arc0.copy()
        for it in range(1, args.iter + 1):
            t_arc_it = t_arc.copy()
            if args.variante in ("v4", "abl1", "abl3"):
                t_arc_it = t_arc_it * np.where(ztl_punta[ind_edge], PENALITA_ZTL, 1.0)
                t_arc_it = t_arc_it * np.where(ped[ind_edge], PENALITA_PED, 1.0)
            M, chiavi, idx = matrice_da(t_arc_it)
            x = v3.assegna(M, chiavi, idx, origini, lista_origini, N, n_archi, scala=peak_share)
            F += (x - F) / it
            ratio = np.clip(F / cap_arc, 0.0, 6.0)
            t_arc = t_arc0 * (1.0 + ALPHA * ratio ** BETA)
            print(f"  [{args.variante}] MSA {it}/{args.iter}  ({time.time()-t0:.0f} s)  "
                  f"v/c medio {float(np.average(ratio, weights=F+1)):.3f}")
            np.savez_compressed(outdir / "msa_stato.npz", F=F, t_arc=t_arc, it=it)
        # giorno sulla rete congestionata (con ZTL in punta applicata)
        t_arc_day = t_arc * np.where(ztl_punta[ind_edge], PENALITA_ZTL, 1.0) \
            * np.where(ped[ind_edge], PENALITA_PED, 1.0)
        M, chiavi, idx = matrice_da(t_arc_day)
        flusso_day = v3.assegna(M, chiavi, idx, origini, lista_origini, N, n_archi)
        t_arc_fin = t_arc
        vc = F / cap_arc

    flusso_diurno = flusso_day * share_diurno
    np.savez_compressed(outdir / "archi_flusso.npz",
                        flusso_dir=flusso_day, flusso_diurno_dir=flusso_diurno,
                        t_arc=t_arc_fin, cap_arc=cap_arc,
                        share_diurno=share_diurno, peak_share=peak_share)

    # --- per tratto (2 versi) e per tratta ---
    f_ab = np.zeros(n_edge); f_ba = np.zeros(n_edge)
    np.add.at(f_ab, ind_edge[dir_arc == 0], flusso_diurno[dir_arc == 0])
    np.add.at(f_ba, ind_edge[dir_arc == 1], flusso_diurno[dir_arc == 1])
    oneway_edge = np.array([v in ("avanti", "indietro") for v in meta["verso"]])
    f_2v = (f_ab + f_ba) * np.where(oneway_edge, 2.0, 1.0)
    edge_len = rete["edge_len"]

    # aggregazione per tratta (media pesata per lunghezza)
    tratte = json.loads((OUT / "tratte.json").read_text(encoding="utf-8"))["tratte"]
    somma = defaultdict(float); pesi = defaultdict(float)
    for e in range(n_edge):
        t = int(et[e])
        if t < 0:
            continue
        somma[t] += f_2v[e] * float(edge_len[e])
        pesi[t] += float(edge_len[e])
    tratte_out = []
    for t in tratte:
        tid = t["id"]
        fl = somma.get(tid, 0.0) / pesi.get(tid, 1.0) if pesi.get(tid) else 0.0
        tratte_out.append({"id": tid, "asse": t["asse"], "nome": t["nome_principale"],
                           "comune": t["comune"], "quartiere": t["quartiere"],
                           "lunghezza_m": t["lunghezza_m"], "classe": t["classe"],
                           "rango": t["rango"], "corsie_totali": t["corsie_totali"],
                           "veic_giorno_2v": round(fl, 1), "stimato": True})
    (outdir / "tratte_flusso.json").write_text(json.dumps({
        "stimato": True, "variante": args.variante,
        "nota": "Flusso diurno 6-21 a DUE VERSI, media pesata per lunghezza delle tratte. "
                "Dove il tratto e' a senso unico il valore e' x2 (come i sensori 5T).",
        "tratte": tratte_out,
    }, ensure_ascii=False), encoding="utf-8")

    # sensori: tratto piu' vicino (per la valutazione)
    sensori_v2 = json.loads((PROC / "sensori_corridoi_v2.json").read_text(encoding="utf-8"))["sensori"]
    ab = json.loads((PROC / "traffico_stimato_AB.json").read_text(encoding="utf-8"))
    medi = rete_osm.punti_medi(rete)
    info = []
    for u in ab["unita"]:
        lcd = u["lcd1"][0]
        pos = sensori_v2.get(lcd)
        if not pos:
            continue
        d, e = rete_osm.tratto_piu_vicino(rete, pos["lat"], pos["lon"], medi)
        fl = float(f_2v[e]) if e is not None else None
        info.append({"lcd1": u["lcd1"], "via": pos["via"], "corridoio": u["corridoio"]["nome"],
                     "dist_m": None if e is None else round(d, 1),
                     "modello_2v": None if fl is None else round(fl, 1),
                     "misurato": u["f_diurno_totale"],
                     "classe": u["corridoio"]["punteggio"]})
    (outdir / "sensori.json").write_text(json.dumps({
        "variante": args.variante, "sensori": info}, ensure_ascii=False), encoding="utf-8")

    vc_medio = float(np.average(vc, weights=F + 1)) if congestione else 0.0
    riepilogo = {
        "stimato": True, "variante": args.variante, "iterazioni": args.iter if congestione else 0,
        "origini": len(lista_origini), "peso_totale": round(peso_tot, 1),
        "peso_flusso": round(peso_conv, 1), "share_diurno": round(share_diurno, 5),
        "peak_share": round(peak_share, 5), "vc_medio": round(vc_medio, 3),
        "tratti_ztl_punta": int(ztl_punta.sum()), "tratti_pedonali": int(ped.sum()),
        "veicoli_km_day": round(float((flusso_day * edge_len[ind_edge]).sum() / 1000), 0),
        "durata_s": round(time.time() - t0, 1), "data": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (outdir / "riepilogo.json").write_text(json.dumps(riepilogo, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    print(json.dumps(riepilogo, ensure_ascii=False, indent=1))
    print(f"[{args.variante}] fatto in {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
