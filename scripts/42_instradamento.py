# -*- coding: utf-8 -*-
"""
scripts/42_instradamento.py - Pacchetto D del piano Fase 3.

Prende la domanda auto (coppie di zone x ora) e i punti pesati per zona, e fa
"guidare" ogni viaggio sul percorso piu' veloce della rete stradale. Poi somma
i viaggi su ogni tratto.

Metodo (V0 - variante di base):
  - percorso piu' veloce (tempo da maxspeed OSM / classe di strada), tutto o
    niente: un solo percorso per coppia di punti;
  - nessun rallentamento da traffico; uno schema unico per tutte le ore (le
    ore si ottengono dopo con le quote orarie della domanda);
  - i viaggi interni a una zona passano fra punti diversi della stessa zona.

Come si calcola in fretta: per ogni NODO di origine si calcola l'albero dei
cammini minimi (scipy.sparse.csgraph.dijkstra) e poi si somma la domanda dei
sottoalberi (una passata sui nodi in ordine di distanza decrescente). Cosi' non
si ricostruisce un percorso per ogni coppia.

Ripartibile: salva lo stato ogni CHECKPOINT origini in
data/processed/traffico_c/instradamenti/ e al rilancio riparte da li'.

Output:
  data/processed/traffico_c/domanda_nodi.npz      (domanda fra nodi, per il ricalcolo)
  data/processed/traffico_c/archi_flusso.npz      (flusso per arco orientato, giorno)
  data/processed/traffico_c/instradamenti/riepilogo.json
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


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
OUT_DIR = RADICE / "data" / "processed" / "traffico_c"
RETE_DIR = OUT_DIR / "rete"
INSTR = OUT_DIR / "instradamenti"
CHECKPOINT = 100


def carica_domanda_nodi(N, punti, celle):
    """Ritorna (origini dict nodo -> (dest array, val array)), pesi e dettaglio perdite."""
    punti_zona = {cod: [(int(p["nodo"]), float(p["peso"])) for p in elenco]
                  for cod, elenco in punti["zone"].items()}
    # zona fittizia per i viaggi con un estremo fuori dalle 212 zone
    if "FUORI" not in punti_zona:
        usa_porte = defaultdict(float)
        for cod, elenco in punti_zona.items():
            for nodo, _ in elenco:
                usa_porte[nodo] += 1.0
        if usa_porte:
            tot = sum(usa_porte.values())
            punti_zona["FUORI"] = [(n, v / tot) for n, v in usa_porte.items()]
    # zone rappresentate SOLO da porte (fuori dal taglio OSM)
    zona_porta = {cod for cod, elenco in punti["zone"].items()
                  if elenco and all(p["tipo"] == "porta" for p in elenco)}

    D = defaultdict(float)
    for par, arr, ora, peso, n in celle:
        D[(par, arr)] += peso

    dem = defaultdict(float)
    peso_tot = 0.0
    perso_zone = 0.0
    perso_self = 0.0
    dett = defaultdict(lambda: [0.0, 0.0])   # categoria -> [perso, peso]
    for (par, arr), w in D.items():
        peso_tot += w
        op = punti_zona.get(par) or punti_zona.get("FUORI")
        dp = punti_zona.get(arr) or punti_zona.get("FUORI")
        esterna_par = par in zona_porta or par not in punti_zona
        esterna_arr = arr in zona_porta or arr not in punti_zona
        # un viaggio interno a una zona esterna (fuori dal taglio) avviene fuori
        # dalla rete studiata: non deve produrre traffico sulle strade di Torino
        if par == arr and esterna_par:
            perso_self += w
            dett["intra_porta_fuori_rete"][0] += w
            dett["intra_porta_fuori_rete"][1] += w
            continue
        if not op or not dp:
            perso_zone += w
            continue
        fraz_self = 0.0
        for (no, wo) in op:
            for (nd, wd) in dp:
                if no == nd:
                    fraz_self += wo * wd
                else:
                    dem[(no, nd)] += w * wo * wd
        perso_self += w * fraz_self
        if par == arr:
            cat = "intra_esterna" if esterna_par else "intra_interna"
        elif esterna_par and esterna_arr:
            cat = "inter_porta_porta"
        elif esterna_par or esterna_arr:
            cat = "inter_porta_interna"
        else:
            cat = "inter_interna"
        dett[cat][0] += w * fraz_self
        dett[cat][1] += w

    per_origine = defaultdict(lambda: ([], []))
    for (no, nd), v in dem.items():
        per_origine[no][0].append(nd)
        per_origine[no][1].append(v)
    origini = {}
    for no, (dlist, vlist) in per_origine.items():
        origini[no] = (np.array(dlist, dtype=np.int64), np.array(vlist, dtype=np.float64))
    return origini, peso_tot, perso_zone, perso_self, dett


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", type=int, default=0, help="usa solo N origini (prova rapida)")
    ap.add_argument("--verifica", action="store_true", help="verifica 20 percorsi con networkx")
    args = ap.parse_args()

    t_inizio = time.time()
    rete = rete_osm.carica(RETE_DIR)
    xy = rete["nodi_xy"]
    N = len(xy)
    archi = rete["archi"]
    edge_a = rete["edge_a"]
    n_archi = len(archi)
    n_edge = len(edge_a)

    punti = json.loads((OUT_DIR / "punti.json").read_text(encoding="utf-8"))
    domanda = json.loads((OUT_DIR / "domanda_auto.json").read_text(encoding="utf-8"))
    celle = domanda["celle"]
    quote = domanda["quote_orarie"]
    share_diurno = sum(quote[str(h)] for h in range(6, 22))

    cache_dem = OUT_DIR / "domanda_nodi.npz"
    if cache_dem.is_file():
        z = np.load(cache_dem)
        righe, col, val = z["righe"], z["col"], z["val"]
        peso_tot = float(z["peso_tot"]); perso_zone = float(z["perso_zone"]); perso_self = float(z["perso_self"])
        dett = json.loads(str(z["dettaglio"]))
        print("domanda fra nodi: ripresa dalla cache")
    else:
        print("costruisco la domanda fra nodi ...")
        origini_tmp, peso_tot, perso_zone, perso_self, dett = carica_domanda_nodi(N, punti, celle)
        righe = np.concatenate([o[0] for o in origini_tmp.values()]) if origini_tmp else np.zeros(0, np.int64)
        col, val = [], []
        for no, (dl, vl) in origini_tmp.items():
            col.extend([no] * len(dl))
            val.extend(vl)
        col = np.array(col, dtype=np.int64)
        val = np.array(val, dtype=np.float64)
        np.savez_compressed(cache_dem, righe=righe, col=col, val=val,
                            peso_tot=peso_tot, perso_zone=perso_zone, perso_self=perso_self,
                            dettaglio=json.dumps(dett))
    print(f"  coppie di nodi con domanda: {len(val):,}")
    print(f"  peso totale (viaggi/giorno): {peso_tot:,.0f}")
    print(f"  senza flusso perche' origine e destinazione cadono sullo STESSO nodo: "
          f"{perso_self:,.0f} ({100*perso_self/peso_tot:.1f}%) - dettaglio:")
    for k in sorted(dett, key=lambda k: -dett[k][1]):
        p, t = dett[k]
        print(f"      {k:16s} peso {t:11,.0f}  senza flusso {p:10,.0f} ({100*p/t:5.1f}%)")

    origini = defaultdict(lambda: {"dest": [], "val": []})
    for nd, no, v in zip(righe, col, val):
        origini[int(no)]["dest"].append(int(nd))
        origini[int(no)]["val"].append(v)
    origini = {k: (np.array(v["dest"], np.int64), np.array(v["val"], np.float64))
               for k, v in origini.items()}
    lista_origini = sorted(origini)
    if args.prova:
        lista_origini = lista_origini[:args.prova]
    print(f"  nodi di origine: {len(lista_origini):,}")

    # --- matrice dei tempi (dedup: tengo l'arco piu' veloce per ogni coppia) ---
    import scipy.sparse as sp
    from scipy.sparse.csgraph import dijkstra
    src = archi[:, 0].astype(np.int64)
    dst = archi[:, 1].astype(np.int64)
    w = archi[:, 2].astype(np.float64)
    chiave = src * N + dst
    order = np.argsort(chiave, kind="stable")
    chiave_s = chiave[order]
    primo = np.concatenate(([True], chiave_s[1:] != chiave_s[:-1]))
    pos_primo = np.nonzero(primo)[0]
    idx_arco_unico = order[pos_primo].copy()     # indice dell'arco per ogni coppia unica
    # fra i duplicati tengo il piu' veloce
    fine = np.append(pos_primo[1:], len(chiave_s))
    for u, (a0, a1) in enumerate(zip(pos_primo, fine)):
        if a1 - a0 > 1:
            sotto = order[a0:a1]
            idx_arco_unico[u] = sotto[np.argmin(w[sotto])]
    chiavi_uni = chiave_s[primo]
    n_dup = len(chiave) - len(chiavi_uni)
    nodi_loop = int((src == dst).sum())
    src_u = (chiavi_uni // N).astype(np.int64)
    dst_u = (chiavi_uni % N).astype(np.int64)
    w_u = w[idx_arco_unico]
    tieni = src_u != dst_u
    M = sp.csr_matrix((w_u[tieni], (src_u[tieni], dst_u[tieni])), shape=(N, N))
    print(f"  archi: {n_archi:,}  coppie uniche: {len(chiavi_uni):,} (duplicati risolti: {n_dup}, "
          f"self-loop tolti: {nodi_loop})")

    # --- checkpoint ---
    INSTR.mkdir(parents=True, exist_ok=True)
    stato = INSTR / "parziale.npz"
    # firma della rete: se cambia (rete ricostruita), il checkpoint non vale piu'
    firma = f"{n_archi}-{n_edge}-{round(float(archi[:, 2].sum()), 3)}"
    flusso_archi = np.zeros(n_archi, dtype=np.float64)
    peso_perso = 0.0
    fatte = set()
    if stato.is_file():
        z = np.load(stato, allow_pickle=True)
        if "firma" in z.files and str(z["firma"]) == firma:
            flusso_archi = z["flusso_archi"]
            peso_perso = float(z["peso_perso"])
            fatte = set(int(x) for x in z["origini_fatte"])
            print(f"  ripresa: {len(fatte):,} origini gia' fatte")
        else:
            print("  checkpoint di un'altra rete: lo ignoro e ricalcolo da zero")

    restanti = [o for o in lista_origini if o not in fatte]
    print(f"  origini da fare: {len(restanti):,}")
    t0 = time.time()
    peso_perso_origini = []
    batch = 10
    for i in range(0, len(restanti), batch):
        gruppo = restanti[i:i + batch]
        dist, pred = dijkstra(M, indices=gruppo, return_predecessors=True)
        for k, o in enumerate(gruppo):
            di = dist[k]
            pr = pred[k]
            dest, val = origini[o]
            finiti = np.isfinite(di[dest])
            perdita = float(val[~finiti].sum())
            peso_perso += perdita
            if perdita > 100:
                peso_perso_origini.append((int(o), round(perdita, 1),
                                           round(100 * perdita / max(val.sum(), 1), 1)))
            dd = dest[finiti]
            vv = val[finiti]
            q = np.zeros(N, dtype=np.float64)
            np.add.at(q, dd, vv)
            ok = np.nonzero(np.isfinite(di))[0]
            ord_ = ok[np.argsort(-di[ok])].tolist()
            ql = q.tolist()
            prl = pr.tolist()
            for n in ord_:
                p = prl[n]
                if p >= 0:
                    ql[p] += ql[n]
            s = np.asarray(ql, dtype=np.float64)
            nz = np.nonzero(s)[0]
            if len(nz):
                prn = pr[nz]
                buoni = prn >= 0
                nz = nz[buoni]
                prn = prn[buoni]
                ch = prn.astype(np.int64) * N + nz
                pos = np.searchsorted(chiavi_uni, ch)
                pos = np.clip(pos, 0, len(chiavi_uni) - 1)
                okk = chiavi_uni[pos] == ch
                ar = idx_arco_unico[pos[okk]]
                flusso_archi += np.bincount(ar, weights=s[nz[okk]], minlength=n_archi)
        fatte.update(gruppo)
        if (i // batch) % 5 == 0 or i + batch >= len(restanti):
            np.savez_compressed(stato, flusso_archi=flusso_archi,
                                peso_perso=peso_perso,
                                firma=firma,
                                origini_fatte=np.array(sorted(fatte), dtype=np.int64))
            print(f"  {min(i+batch,len(restanti)):,}/{len(restanti):,} origini  "
                  f"({time.time()-t0:.0f} s)")

    durata = time.time() - t0
    peso_perso_origini.sort(key=lambda t: -t[1])
    print(f"  peso non raggiungibile: {peso_perso:,.0f} ({100*peso_perso/peso_tot:.2f}%) - "
          f"{len(peso_perso_origini)} origini con perdita > 100")
    for t in peso_perso_origini[:10]:
        print(f"      nodo {t[0]}: perso {t[1]:,.0f} ({t[2]}% della sua domanda)")
    flusso_dir = flusso_archi
    flusso_diurno_dir = flusso_dir * share_diurno

    # flusso per tratto (due versi sommati) e veicoli-km
    ind_edge = archi[:, 3].astype(np.int64)
    flusso_edge = np.bincount(ind_edge, weights=flusso_dir, minlength=n_edge)
    # veicoli-km = somma su ogni passaggio di (lunghezza dell'arco percorso)
    lung_arco = rete["edge_len"][ind_edge]
    veicoli_km = float((flusso_dir * lung_arco).sum() / 1000.0)
    veicoli_ora = float((flusso_dir * archi[:, 2]).sum() / 3600.0)

    np.savez_compressed(
        OUT_DIR / "archi_flusso.npz",
        flusso_dir=flusso_dir.astype(np.float64),
        flusso_diurno_dir=flusso_diurno_dir.astype(np.float64),
        flusso_edge=flusso_edge.astype(np.float64),
        share_diurno=share_diurno,
    )
    riepilogo = {
        "stimato": True,
        "variante": "V0 (tutto o niente, popolazione per tutti gli estremi, "
                    "schema unico per tutte le ore, percorso piu' veloce)",
        "origini_usate": len(lista_origini),
        "paia_nodi_con_domanda": int(len(val)),
        "peso_totale_viaggi_giorno": round(peso_tot, 1),
        "peso_perso_stesso_nodo": round(perso_self, 1),
        "peso_perso_non_raggiungibile": round(peso_perso, 1),
        "peso_perso_zona_senza_punti": round(perso_zone, 1),
        "origini_con_perdita_non_raggiungibile": [
            {"nodo": t[0], "peso": t[1], "quota_pct": t[2]} for t in peso_perso_origini[:10]],
        "n_origini_con_perdita": len(peso_perso_origini),
        "quota_peso_perso": round((perso_self + peso_perso + perso_zone) / peso_tot, 5),
        "veicoli_km_modello": round(veicoli_km, 0),
        "veicoli_ora_totali": round(veicoli_ora, 0),
        "lunghezza_media_viaggio_km": round(veicoli_km / max(peso_tot - perso_self - peso_perso, 1), 2),
        "share_diurno_6_21": round(share_diurno, 5),
        "durata_s": round(durata, 1),
        "duplicati_archi_risolti": int(n_dup),
        "self_loop_tolti": nodi_loop,
        "data": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (INSTR / "riepilogo.json").write_text(json.dumps(riepilogo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(riepilogo, ensure_ascii=False, indent=1))

    if args.verifica:
        verifica_networkx(rete, M, lista_origini)

    print(f"\nDurata pacchetto D: {time.time()-t_inizio:.0f} s")


def verifica_networkx(rete, M, lista_origini, n_prove=20):
    """Ricalcola 20 percorsi (origine -> destinazione scelti a caso) con networkx
    sullo stesso grafo e confronta lunghezza e tempo con scipy (tolleranza 2%)."""
    import networkx as nx
    from scipy.sparse.csgraph import dijkstra
    a = rete["archi"]
    rng = np.random.default_rng(777)
    orig = rng.choice(lista_origini, size=min(n_prove, len(lista_origini)), replace=False)
    dist, pred = dijkstra(M, indices=orig, return_predecessors=True)
    G = nx.DiGraph()
    for (s, t, w, e, d) in a:
        if G.has_edge(int(s), int(t)):
            if w < G[int(s)][int(t)]["weight"]:
                G[int(s)][int(t)]["weight"] = float(w)
        else:
            G.add_edge(int(s), int(t), weight=float(w))
    out = []
    for k, o in enumerate(orig):
        # destinazione: il nodo piu' lontano raggiungibile
        ok = np.isfinite(dist[k])
        if ok.sum() < 2:
            continue
        dmax = int(np.argmax(np.where(ok, dist[k], -1)))
        try:
            lung = nx.shortest_path_length(G, int(o), dmax, weight="weight")
        except Exception:
            continue
        t_scipy = float(dist[k, dmax])
        err = abs(lung - t_scipy) / max(t_scipy, 1e-9)
        out.append((int(o), dmax, round(t_scipy, 2), round(float(lung), 2), round(err * 100, 3)))
    np.savez_compressed(OUT_DIR / "verifica_networkx.npz",
                        tab=np.array(out, dtype=np.float64))
    print("\nVERIFICA INDIPENDENTE (networkx su 20 coppie): errori % tempo")
    for riga in out:
        print("   da", riga[0], "a", riga[1], "scipy", riga[2], "networkx", riga[3], f"err {riga[4]}%")
    if out:
        print(f"   errore massimo {max(r[4] for r in out):.3f}% (tolleranza 2%)")


if __name__ == "__main__":
    main()
