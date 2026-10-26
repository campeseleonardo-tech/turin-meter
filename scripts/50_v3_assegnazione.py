# -*- coding: utf-8 -*-
"""
scripts/50_v3_assegnazione.py - Pacchetto A (Fase 3-bis), parte 2: assegnazione V3.

Modello V3 (fissato nel piano, sezione 3):
  1. destinazioni per attrattori (punti_v3.json, script 49) e origine da casa o
     dal posto del viaggio precedente;
  2. CONGESTIONE: assegnazione ripetuta (metodo delle medie successive, MSA) con
     funzione di ritardo BPR  t = t0 * (1 + 0,15 * (v/c)^4); capacita' per classe
     di strada (valori standard perche' la rete non conserva il numero di corsie);
     caso principale = ora di punta del mattino (media delle ore 7 e 8);
  3. PORTE solo di rango >= 3 (porte_v3.json).

Il giorno intero (6-21, due versi) si ottiene assegnando la domanda giornaliera
sulla rete con i tempi di punta congestionati.

Ripartibile: salva lo stato MSA a ogni iterazione (v3/msa_stato.npz).

Opzioni:  --abl 1|2|3  (ablazione diagnostica: 1 = senza attrattori,
          2 = senza congestione, 3 = senza restrizione delle porte)
          --iter N      numero di iterazioni MSA (default 12)
          --outdir      sottocartella (default v3)

Output (in v3/): archi_flusso_v3.npz, corridoi_v3.json, riepilogo.json
"""

import argparse
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rete_osm  # noqa: E402

PROC = AQUI.parent / "data" / "processed"
OUT_DIR = PROC / "traffico_c"
RETE_DIR = OUT_DIR / "rete"
VICINANZA_M = 25.0
CELLA_LAT, CELLA_LON = 0.0009, 0.0013

CAPACITA = {
    "motorway": 8000, "motorway_link": 4000, "trunk": 6000, "trunk_link": 3000,
    "primary": 3600, "primary_link": 2400, "secondary": 2600, "secondary_link": 1600,
    "tertiary": 1800, "tertiary_link": 1200, "unclassified": 1200, "residential": 900,
    "living_street": 400, "service": 600, "road": 1000,
}
ALPHA, BETA = 0.15, 4.0


def normalizza(nome):
    from importlib import import_module
    return import_module("24_importanza_vie").normalizza(nome)


def carica_corridoi():
    corridoi = json.loads((PROC / "importanza_vie.json").read_text(encoding="utf-8"))["corridoi"]
    per_chiave = defaultdict(list)
    griglia = defaultdict(set)
    for i, c in enumerate(corridoi):
        per_chiave[c["chiave_normalizzata"]].append(i)
        for tratto in c["geometria"]:
            for k in range(len(tratto) - 1):
                (la0, lo0), (la1, lo1) = tratto[k], tratto[k + 1]
                passi = max(1, int(max(abs(la1 - la0) / CELLA_LAT, abs(lo1 - lo0) / CELLA_LON) * 4))
                for t in range(passi + 1):
                    griglia[(math.floor((la0 + (la1 - la0) * t / passi) / CELLA_LAT),
                             math.floor((lo0 + (lo1 - lo0) * t / passi) / CELLA_LON))].add(i)
    return corridoi, per_chiave, griglia


def distanza_a_corridoio(corridoio, la, lo):
    best = 1e18
    for tratto in corridoio["geometria"]:
        for k in range(len(tratto) - 1):
            la1, lo1 = tratto[k]; la2, lo2 = tratto[k + 1]
            mx = math.cos(math.radians(la)) * 111320.0
            my = 110540.0
            px, py = (lo - lo1) * mx, (la - la1) * my
            dx, dy = (lo2 - lo1) * mx, (la2 - la1) * my
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 <= 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
            d = math.hypot(px - t * dx, py - t * dy)
            if d < best:
                best = d
    return best


def costruisci_domanda_nodi(punti, domanda, porte, N):
    """Ritorna origini {nodo: (dest[], val[])}, peso_tot e dettaglio perdite."""
    def punti_zona(cod, gruppo):
        z = punti.get(cod)
        if not z:
            return None
        e = z.get(gruppo) or z.get("casa")
        return e or z.get("casa")

    # zona fittizia FUORI: porte di rango >= 3, peso proporzionale alla capacita'
    cap_rango = {5: 8000, 4: 4000, 3: 2500, 2: 1500, 1: 800}
    pesi_porta = defaultdict(float)
    for p in porte:
        pesi_porta[p["nodo"]] += cap_rango.get(p["rango"], 1000.0)
    tp = sum(pesi_porta.values()) or 1.0
    fuori = [(n, v / tp) for n, v in pesi_porta.items()]

    zona_porta = {cod for cod, z in punti.items()
                  if z.get("casa") and all(p.get("tipo", "sezione") == "porta" for p in z["casa"])}

    def punti_o_fuori(cod, gruppo):
        if cod is None:
            return fuori
        e = punti_zona(cod, gruppo)
        if not e:
            return fuori
        # zona esterna (solo porte): usa le porte "fuori" del modello V3, non quelle del V0
        if cod in zona_porta:
            return fuori
        return [(p["nodo"], p["peso"]) for p in e]

    dem = defaultdict(float)
    peso_tot = 0.0
    perso_self = 0.0
    perso_zone = 0.0
    dett = defaultdict(lambda: [0.0, 0.0])
    for par, arr, ora, peso, n, og, dg in domanda["celle"]:
        peso_tot += peso
        op = punti_o_fuori(par, og)
        dp = punti_o_fuori(arr, dg)
        esterna_par = par in zona_porta or par not in punti
        esterna_arr = arr in zona_porta or arr not in punti
        if par == arr and esterna_par:
            dett["intra_porta_fuori_rete"][0] += peso
            dett["intra_porta_fuori_rete"][1] += peso
            continue
        # un viaggio fra due zone ESTERNE diverse avviene fuori dall'area studiata:
        # instradarlo fra due porte diverse creerebbe traffico finto sui corsi di Torino
        if esterna_par and esterna_arr:
            dett["inter_porta_porta"][0] += peso
            dett["inter_porta_porta"][1] += peso
            continue
        if not op or not dp:
            perso_zone += peso
            continue
        fraz_self = 0.0
        for (no, wo) in op:
            for (nd, wd) in dp:
                if no == nd:
                    fraz_self += wo * wd
                else:
                    dem[(no, nd)] += peso * wo * wd
        perso_self += peso * fraz_self
        if par == arr:
            cat = "intra_esterna" if esterna_par else "intra_interna"
        elif esterna_par and esterna_arr:
            cat = "inter_porta_porta"
        elif esterna_par or esterna_arr:
            cat = "inter_porta_interna"
        else:
            cat = "inter_interna"
        dett[cat][0] += peso * fraz_self
        dett[cat][1] += peso

    per_origine = defaultdict(lambda: ([], []))
    for (no, nd), v in dem.items():
        per_origine[no][0].append(nd)
        per_origine[no][1].append(v)
    origini = {no: (np.array(d, np.int64), np.array(v, np.float64))
               for no, (d, v) in per_origine.items()}
    return origini, peso_tot, perso_self, perso_zone, dett


def matrice(M_src, M_dst, M_w, N):
    """csr con il tempo minimo per ogni coppia (src,dst) unica."""
    import scipy.sparse as sp
    chiave = M_src * N + M_dst
    order = np.argsort(chiave, kind="stable")
    chiave_s = chiave[order]
    primo = np.concatenate(([True], chiave_s[1:] != chiave_s[:-1]))
    pos = np.nonzero(primo)[0]
    idx = order[pos].copy()
    fine = np.append(pos[1:], len(chiave_s))
    for u, (a0, a1) in enumerate(zip(pos, fine)):
        if a1 - a0 > 1:
            sotto = order[a0:a1]
            idx[u] = sotto[np.argmin(M_w[sotto])]
    chiavi = chiave_s[primo]
    src_u = (chiavi // N).astype(np.int64)
    dst_u = (chiavi % N).astype(np.int64)
    w_u = M_w[idx]
    tieni = src_u != dst_u
    return (sp.csr_matrix((w_u[tieni], (src_u[tieni], dst_u[tieni])), shape=(N, N)),
            chiavi[tieni], idx[tieni])


def assegna(M, chiavi_uni, idx_uni, origini, lista_origini, N, n_archi, scala=1.0):
    """All-or-nothing: somma dei sottoalberi dei cammini minimi."""
    from scipy.sparse.csgraph import dijkstra
    flusso = np.zeros(n_archi, dtype=np.float64)
    for i in range(0, len(lista_origini), 10):
        gruppo = lista_origini[i:i + 10]
        dist, pred = dijkstra(M, indices=gruppo, return_predecessors=True)
        for k, o in enumerate(gruppo):
            di = dist[k]; pr = pred[k]
            dest, val = origini[o]
            finiti = np.isfinite(di[dest])
            dd = dest[finiti]; vv = val[finiti] * scala
            q = np.zeros(N)
            np.add.at(q, dd, vv)
            ok = np.nonzero(np.isfinite(di))[0]
            ord_ = ok[np.argsort(-di[ok])].tolist()
            ql = q.tolist(); prl = pr.tolist()
            for n in ord_:
                p = prl[n]
                if p >= 0:
                    ql[p] += ql[n]
            s = np.asarray(ql)
            nz = np.nonzero(s)[0]
            if len(nz):
                prn = pr[nz]
                buoni = prn >= 0
                nz = nz[buoni]; prn = prn[buoni]
                ch = prn.astype(np.int64) * N + nz
                pos = np.searchsorted(chiavi_uni, ch)
                pos = np.clip(pos, 0, len(chiavi_uni) - 1)
                okk = chiavi_uni[pos] == ch
                ar = idx_uni[pos[okk]]
                flusso += np.bincount(ar, weights=s[nz[okk]], minlength=n_archi)
    return flusso


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--abl", type=int, default=0, help="1=no attrattori, 2=no congestione, 3=no porte ristrette")
    ap.add_argument("--iter", type=int, default=12)
    ap.add_argument("--outdir", default="v3")
    ap.add_argument("--solo-domanda", action="store_true")
    args = ap.parse_args()
    outdir = OUT_DIR / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    rete = rete_osm.carica(RETE_DIR)
    xy = rete["nodi_xy"]; meta = rete["meta"]; N = len(xy)
    archi = rete["archi"]; ind_edge = archi[:, 3].astype(np.int64)
    n_archi = len(archi); n_edge = len(rete["edge_a"])

    punti = json.loads((OUT_DIR / "punti.json").read_text(encoding="utf-8"))["zone"]
    if args.abl != 1:
        punti = json.loads((OUT_DIR / "v3" / "punti_v3.json").read_text(encoding="utf-8"))["zone"]
    else:
        # ablazione 1: nessun attrattore -> tutti gli estremi sulla popolazione (come V0)
        punti = {cod: {"casa": elenco} for cod, elenco in punti.items()}
    domanda = json.loads((OUT_DIR / "v3" / "domanda_v3.json").read_text(encoding="utf-8"))
    if args.abl == 3:
        porte = json.loads((OUT_DIR / "porte.json").read_text(encoding="utf-8"))["porte"]
    else:
        porte = json.loads((OUT_DIR / "v3" / "porte_v3.json").read_text(encoding="utf-8"))["porte"]

    origini, peso_tot, perso_self, perso_zone, dett = costruisci_domanda_nodi(punti, domanda, porte, N)
    lista_origini = sorted(origini)
    peso_conv = sum(float(v[1].sum()) for v in origini.values())
    print(f"origini: {len(lista_origini):,}  peso totale: {peso_tot:,.0f}  "
          f"peso che produce flusso: {peso_conv:,.0f} ({100*peso_conv/peso_tot:.1f}%)  "
          f"senza flusso (stesso nodo): {perso_self:,.0f}")
    for k in sorted(dett, key=lambda k: -dett[k][1]):
        print(f"   {k:20s} peso {dett[k][1]:11,.0f}  senza flusso {dett[k][0]:10,.0f} "
              f"({100*dett[k][0]/dett[k][1]:5.1f}%)")
    if args.solo_domanda:
        return
    share_diurno = sum(domanda["quote_orarie"][str(h)] for h in range(6, 22))
    peak_share = (domanda["quote_orarie"]["7"] + domanda["quote_orarie"]["8"]) / 2.0
    print(f"share diurno 6-21: {share_diurno:.4f}   share ora di punta AM: {peak_share:.4f}")

    cap_edge = np.array([CAPACITA.get(meta["highway"][e], 1000.0) for e in range(n_edge)])
    t0_edge = rete["edge_t"].astype(np.float64).copy()

    src = archi[:, 0].astype(np.int64); dst = archi[:, 1].astype(np.int64)
    t_arc0 = t0_edge[ind_edge]

    def flusso_edge_da(flusso_arc):
        return np.bincount(ind_edge, weights=flusso_arc, minlength=n_edge)

    t_edge = t0_edge.copy()
    if args.abl == 2:
        print("ABLAZIONE 2: nessuna congestione (tempi a flusso libero)")
        M, chiavi, idx = matrice(src, dst, t_arc0, N)
        flusso_day = assegna(M, chiavi, idx, origini, lista_origini, N, n_archi)
        it_fatte = 0
    else:
        stato = outdir / "msa_stato.npz"
        F = np.zeros(n_archi)
        it_start = 1
        if stato.is_file():
            z = np.load(stato)
            F = z["F"]; t_edge = z["t_edge"]; it_start = int(z["it"])
            it_start += 1
            print(f"ripresa MSA dall'iterazione {it_start}")
        for it in range(it_start, args.iter + 1):
            t_arc = t_edge[ind_edge]
            M, chiavi, idx = matrice(src, dst, t_arc, N)
            x = assegna(M, chiavi, idx, origini, lista_origini, N, n_archi, scala=peak_share)
            F += (x - F) / it
            v_edge = flusso_edge_da(F)
            ratio = np.clip(v_edge / cap_edge, 0.0, 4.0)
            t_edge = t0_edge * (1.0 + ALPHA * ratio ** BETA)
            np.savez_compressed(stato, F=F, t_edge=t_edge, it=it)
            print(f"  MSA iter {it}/{args.iter}  ({time.time()-t0:.0f} s)  "
                  f"v/c medio {float(np.average(ratio, weights=v_edge+1)):.3f}")
        it_fatte = args.iter
        # giorno: all-or-nothing sulla rete congestionata
        M, chiavi, idx = matrice(src, dst, t_edge[ind_edge], N)
        flusso_day = assegna(M, chiavi, idx, origini, lista_origini, N, n_archi)

    flusso_diurno = flusso_day * share_diurno
    v_edge_day = flusso_edge_da(flusso_day)
    ind = ind_edge
    verso = archi[:, 4].astype(np.int64)
    f_ab = np.zeros(n_edge); f_ba = np.zeros(n_edge)
    np.add.at(f_ab, ind[verso == 0], flusso_diurno[verso == 0])
    np.add.at(f_ba, ind[verso == 1], flusso_diurno[verso == 1])
    f_tot = f_ab + f_ba
    edge_len = rete["edge_len"]
    veicoli_km = float((flusso_day * edge_len[ind]).sum() / 1000.0)
    np.savez_compressed(outdir / "archi_flusso_v3.npz",
                        flusso_dir=flusso_day, flusso_diurno_dir=flusso_diurno,
                        flusso_edge=f_tot, share_diurno=share_diurno,
                        t_edge=t_edge, v_edge_day=v_edge_day)

    # --- corridoi (come 43) ---
    corridoi, per_chiave, griglia = carica_corridoi()
    nome_edge = [normalizza(meta["nomi"][e]) if meta["nomi"][e] else "" for e in range(n_edge)]
    medi = np.array([rete_osm.punto_medio(rete, e) for e in range(n_edge)])
    assegna_c = [None] * n_edge
    for e in range(n_edge):
        la, lo = medi[e]
        chiave = nome_edge[e]
        scelto = None
        if chiave and chiave in per_chiave:
            cands = per_chiave[chiave]
            if len(cands) == 1:
                scelto = cands[0]
            else:
                best = (1e18, None)
                for i in cands:
                    d = distanza_a_corridoio(corridoi[i], la, lo)
                    if d < best[0]:
                        best = (d, i)
                if best[0] <= 200:
                    scelto = best[1]
        if scelto is None:
            ci, cj = math.floor(la / CELLA_LAT), math.floor(lo / CELLA_LON)
            vicini = set()
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    vicini |= griglia.get((ci + di, cj + dj), set())
            best = (1e18, None)
            for i in vicini:
                d = distanza_a_corridoio(corridoi[i], la, lo)
                if d < best[0]:
                    best = (d, i)
            if best[1] is not None and best[0] <= VICINANZA_M:
                scelto = best[1]
        assegna_c[e] = scelto

    per_cor = defaultdict(list)
    for e in range(n_edge):
        if assegna_c[e] is not None:
            per_cor[assegna_c[e]].append(e)
    out = []
    for i, c in enumerate(corridoi):
        eids = per_cor.get(i, [])
        if not eids:
            out.append({"nome": c["nome"], "chiave": c["chiave_normalizzata"],
                        "comune": c.get("comune"), "punteggio": c["punteggio"],
                        "lunghezza_km": c["lunghezza_km"], "n_tratti": 0, "senza_flusso": True})
            continue
        lung = edge_len[eids]; fl = f_tot[eids]
        out.append({"nome": c["nome"], "chiave": c["chiave_normalizzata"],
                    "comune": c.get("comune"), "punteggio": c["punteggio"],
                    "lunghezza_km": c["lunghezza_km"], "n_tratti": len(eids),
                    "km_tratti_modello": round(float(lung.sum() / 1000), 3),
                    "flusso_diurno_medio": round(float((fl * lung).sum() / max(lung.sum(), 1e-9)), 1),
                    "flusso_diurno_max": round(float(fl.max()), 1)})
    # sensori
    sensori_v2 = json.loads((PROC / "sensori_corridoi_v2.json").read_text(encoding="utf-8"))["sensori"]
    ab = json.loads((PROC / "traffico_stimato_AB.json").read_text(encoding="utf-8"))
    info = []
    for u in ab["unita"]:
        lcd = u["lcd1"][0]
        pos = sensori_v2.get(lcd)
        if not pos:
            continue
        d, e = rete_osm.tratto_piu_vicino(rete, pos["lat"], pos["lon"], medi)
        fl = float(f_tot[e]) if e is not None else None
        info.append({"lcd1": u["lcd1"], "via": pos["via"], "corridoio": u["corridoio"]["nome"],
                     "dist_sensore_tratto_m": None if e is None else round(d, 1),
                     "flusso_diurno_modello_sul_tratto": None if fl is None else round(fl, 1),
                     "misurato_diurno_2versi": u["f_diurno_totale"]})
    (outdir / "corridoi_v3.json").write_text(json.dumps({
        "stimato": True, "variante": "V3" + (f" - ablazione {args.abl}" if args.abl else ""),
        "corridoi": out, "sensori": info,
    }, ensure_ascii=False), encoding="utf-8")

    riepilogo = {
        "stimato": True, "abl": args.abl, "iterazioni_msa": it_fatte,
        "origini": len(lista_origini), "peso_totale": round(peso_tot, 1),
        "perso_stesso_nodo": round(perso_self, 1), "share_diurno": round(share_diurno, 5),
        "peak_share": round(peak_share, 5), "veicoli_km_giorno": round(veicoli_km, 0),
        "durata_s": round(time.time() - t0, 1), "data": time.strftime("%Y-%m-%d %H:%M:%S"),
        "capacita": CAPACITA, "alpha": ALPHA, "beta": BETA,
    }
    (outdir / "riepilogo.json").write_text(json.dumps(riepilogo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(riepilogo, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
