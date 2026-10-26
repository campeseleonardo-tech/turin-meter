# -*- coding: utf-8 -*-
"""
scripts/63_v4_valutazione.py - Pacchetto E (Fase 5): valutazione UNA VOLTA.

Stesse 20 unita'-sensore e stessa taratura leave-one-out della Fase 3, stesse
metriche (errore mediano con IC90, p90, rho di Spearman, n). Confronta V0 e V4
(e le ablazioni) e applica la regola di scelta FISSATA nel piano Fase 5:

  si adotta V4 se rho(V4) >= rho(V0) e l'errore mediano di V4 non e' peggiore
  di quello di V0 di piu' di 3 punti. Altrimenti resta V0.

Controlli obbligatori: tempi di viaggio (Castello->Collegno 20-35 min in punta),
velocita' del modello sui tratti dei sensori vs misurate.

Output: data/processed/traffico_d/valutazione_fase5.json
        docs/rapporti/RAPPORTO_TRAFFICO_V4.txt
"""

import json
import math
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rete_osm  # noqa: E402

PROC = AQUI.parent / "data" / "processed"
OUT = PROC / "traffico_d"
RETE_DIR = OUT / "rete"
RAPPORTO = AQUI.parent / "docs" / "rapporti" / "RAPPORTO_TRAFFICO_V4.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
ERRORE_A = 0.369

VARIANTI = ["v0", "v4", "abl1", "abl2", "abl3"]
ETICHETTA = {"v0": "V0 (popolazione, senza congestione/ZTL, tutte le porte)",
             "v4": "V4 (attrattori + congestione per corsia + ZTL + porte >=3)",
             "abl1": "V4 senza attrattori", "abl2": "V4 senza congestione",
             "abl3": "V4 senza porte ristrette"}

PERCORSI = [
    ("Piazza Castello -> Collegno (piazza)", (45.0703, 7.6869), (45.0721, 7.5717)),
    ("Piazza Castello -> Venaria Reale", (45.0703, 7.6869), (45.1352, 7.6330)),
    ("Piazza Castello -> Settimo Torinese", (45.0703, 7.6869), (45.1395, 7.7703)),
    ("Piazza Castello -> Moncalieri", (45.0703, 7.6869), (45.0005, 7.6810)),
    ("Piazza Castello -> Orbassano", (45.0703, 7.6869), (45.0070, 7.5373)),
    ("Piazza Castello -> Rivoli", (45.0703, 7.6869), (45.0709, 7.5167)),
]


def metriche(mis, pred):
    mis = np.asarray(mis, float); pred = np.asarray(pred, float)
    err = np.abs(pred - mis) / mis
    return {"n": len(err), "errore_mediano": float(np.median(err)),
            "errore_p90": float(np.percentile(err, 90)),
            "errore_peggiore": float(np.max(err)), "err": err}


def bootstrap_mediana(err, n_boot=5000, seed=17):
    rng = np.random.default_rng(seed); err = np.asarray(err, float); n = len(err)
    med = np.array([np.median(rng.choice(err, size=n, replace=True)) for _ in range(n_boot)])
    return float(np.percentile(med, 5)), float(np.percentile(med, 95))


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    rx = np.argsort(np.argsort(x)).astype(float); ry = np.argsort(np.argsort(y)).astype(float)
    if len(set(rx)) < 2 or len(set(ry)) < 2:
        return float("nan")
    rx -= rx.mean(); ry -= ry.mean()
    return float((rx * ry).sum() / math.sqrt((rx ** 2).sum() * (ry ** 2).sum()))


def valuta(sensori):
    unita = [s for s in sensori if s.get("modello_2v") is not None]
    mis = np.array([u["misurato"] for u in unita], float)
    mod = np.array([u["modello_2v"] for u in unita], float)
    n = len(unita)
    if n == 0:
        return unita, None, float("nan")
    pred = np.zeros(n)
    for i in range(n):
        altri = [j for j in range(n) if j != i]
        pred[i] = mod[i] * (mis[altri].sum() / mod[altri].sum())
    m = metriche(mis, pred)
    lo, hi = bootstrap_mediana(m["err"])
    esito = {"n": n, "errore_mediano": m["errore_mediano"], "ic90": [lo, hi],
             "errore_p90": m["errore_p90"], "errore_peggiore": m["errore_peggiore"],
             "rho_loo": spearman(pred, mis), "rho_grezzo": spearman(mod, mis),
             "k_totale": float(mis.sum() / mod.sum()),
             "migliore_di_A": m["errore_mediano"] < ERRORE_A, "err": m["err"]}
    return unita, esito, pred


def main():
    risultati = {}
    for v in VARIANTI:
        f = OUT / v / "sensori.json"
        if not f.is_file():
            print(f"  (manca {f})")
            continue
        sens = json.loads(f.read_text(encoding="utf-8"))["sensori"]
        unita, esito, pred = valuta(sens)
        if esito is None:
            continue
        risultati[v] = {"unita": unita, "esito": esito, "pred": pred.tolist()}

    righe = []
    def a_(s=""):
        righe.append(s)
    a = a_
    a_("MODELLO DEL TRAFFICO V4 - VALUTAZIONE (Fase 5, pacchetto E)")
    a_("=" * 78)
    a_("Grandezza: totale diurno 6-21 a due versi (veicoli/giorno). Sensore a un verso x2.")
    a_(f"Taratura leave-one-out con un solo fattore globale (come Fase 3). Metodo A: {100*ERRORE_A:.1f}%.")
    a_("")
    a(f"{'variante':8s} {'n':>3s} {'err.med':>8s} {'IC90':>16s} {'p90':>7s} {'rho LOO':>8s} {'rho grezzo':>10s} {'k':>7s}")
    for v in VARIANTI:
        if v not in risultati:
            continue
        e = risultati[v]["esito"]
        a(f"{v:8s} {e['n']:3d} {100*e['errore_mediano']:7.1f}% "
          f"[{100*e['ic90'][0]:5.1f}%,{100*e['ic90'][1]:5.1f}%] {100*e['errore_p90']:6.1f}% "
          f"{e['rho_loo']:8.3f} {e['rho_grezzo']:10.3f} {e['k_totale']:7.3f}")
    a("")

    # --- regola di scelta ---
    if "v0" in risultati and "v4" in risultati:
        r0 = risultati["v0"]["esito"]; r4 = risultati["v4"]["esito"]
        ok = (r4["rho_loo"] >= r0["rho_loo"]) and (r4["errore_mediano"] <= r0["errore_mediano"] + 0.03)
        variante_finale = "v4" if ok else "v0"
        a("Regola di scelta (piano Fase 5, pacchetto E): V4 si adotta se rho(V4) >= rho(V0) E")
        a("l'errore mediano di V4 non e' peggiore di V0 di piu' di 3 punti.")
        a(f"  rho(V0)={r0['rho_loo']:.3f}  rho(V4)={r4['rho_loo']:.3f}   "
          f"err(V0)={100*r0['errore_mediano']:.1f}%  err(V4)={100*r4['errore_mediano']:.1f}%")
        a(f"  => VARIANTE FINALE: {variante_finale.upper()}")
    else:
        variante_finale = "v0"
        a("  (mancano V0 o V4: resta V0)")
    a("")

    ef = risultati[variante_finale]["esito"]
    rho = ef["rho_loo"]; err = ef["errore_mediano"]; ic = ef["ic90"]
    incerto = ic[0] < 0.35 < ic[1]
    if rho < 0.5:
        classe = "C-NO"
    elif rho < 0.7:
        classe = "C-DEBOLE"
    elif err <= 0.35 and ef["migliore_di_A"]:
        classe = "C-ASSOLUTO"
    else:
        classe = "C-INDICE"
    a("== Classe di esito (tabella Fase 3, sezione 1) ==")
    a(f"  variante finale {variante_finale}: rho={rho:.3f}  errore mediano={100*err:.1f}%  "
      f"IC90 [{100*ic[0]:.1f}%,{100*ic[1]:.1f}%]")
    a(f"  CLASSE = {classe}" + ("   (IC90 a cavallo del 35%: INCERTO)" if incerto else ""))
    a("")

    # --- tabella unita' ---
    a(f"== Unita' della variante finale ({variante_finale}) ==")
    unita = risultati[variante_finale]["unita"]
    k = ef["k_totale"]
    for i in np.argsort([-u["misurato"] for u in unita]):
        u = unita[i]
        a(f"  {str(u['lcd1'][0]):>6} {str(u['via'])[:26]:26s} misurato {u['misurato']:9,.0f} "
          f"modello2v {u['modello_2v']:9,.0f} previsto {u['modello_2v']*k:9,.0f} "
          f"err {100*ef['err'][i]:5.1f}%")
    a("")

    # --- tempi di viaggio ---
    rete = rete_osm.carica(RETE_DIR)
    N = len(rete["nodi_xy"]); xy = rete["nodi_xy"]
    archi = rete["archi"]
    import scipy.sparse as sp
    from scipy.sparse.csgraph import dijkstra

    def nodo_vicino(la, lo):
        return int(np.argmin((xy[:, 0] - la) ** 2 + (xy[:, 1] - lo) ** 2))

    def tempi(t_arc):
        M = sp.csr_matrix((t_arc, (archi[:, 0].astype(np.int64), archi[:, 1].astype(np.int64))),
                          shape=(N, N))
        o = nodo_vicino(*PERCORSI[0][1])
        d = dijkstra(M, indices=[o])[0]
        return [float(d[nodo_vicino(*p[2])]) / 60.0 for p in PERCORSI]

    t0 = tempi(archi[:, 2].astype(float))
    t4 = None
    try:
        z = np.load(OUT / "v4" / "archi_flusso.npz")
        t4 = tempi(z["t_arc"])
    except Exception as e:
        print("no t_arc v4", e)
    a("== Tempi di viaggio (minuti) ==")
    a(f"{'percorso':44s} {'flusso libero':>13s} {'V4 punta':>9s}")
    for (nome, _, _), a0, a4 in zip(PERCORSI, t0, t4 or [float('nan')] * len(PERCORSI)):
        a(f"  {nome:42s} {a0:13.1f} {a4:9.1f}")
    a("  (atteso Castello->Collegno in punta: 20-35 minuti)")
    a("")

    # --- velocita' modello vs sensori ---
    a("== Velocita' del modello sui tratti dei sensori (punta) vs misurate ==")
    try:
        vel = json.loads((PROC / "velocita_5t.json").read_text(encoding="utf-8"))["sensori"]
        sens_v2 = json.loads((PROC / "sensori_corridoi_v2.json").read_text(encoding="utf-8"))["sensori"]
        ab = json.loads((PROC / "traffico_stimato_AB.json").read_text(encoding="utf-8"))
        z = np.load(OUT / "v4" / "archi_flusso.npz")
        t_arc = z["t_arc"]
        edge_len = rete["edge_len"]
        medi = rete_osm.punti_medi(rete)
        vmod = []; vmis = []
        for u in ab["unita"]:
            lcd = u["lcd1"][0]
            pos = sens_v2.get(lcd)
            vm = vel.get(lcd)
            if not pos or not vm:
                continue
            d, e = rete_osm.tratto_piu_vicino(rete, pos["lat"], pos["lon"], medi)
            if e is None:
                continue
            arcs = np.nonzero(archi[:, 3].astype(np.int64) == e)[0]
            if len(arcs) == 0:
                continue
            ta = float(np.mean(t_arc[arcs]))
            vv = 3.6 * float(edge_len[e]) / max(ta, 1e-6)
            # velocita' misurata in punta (media delle ore 7-9, giorno feriale "0")
            celle = (vm.get("celle") or {}).get("0", {}) if isinstance(vm, dict) else {}
            vmis_v = None
            for kk in ("7", "8", "9"):
                c = celle.get(kk)
                if c and c.get("ok") and c.get("v"):
                    vmis_v = c["v"]; break
            if vmis_v:
                vmod.append(vv); vmis.append(float(vmis_v))
        if vmod:
            a(f"  coppie modello/misurato: {len(vmod)}   mediana modello {np.median(vmod):.1f} km/h   "
              f"mediana misurata in punta {np.median(vmis):.1f} km/h")
    except Exception as e:
        a(f"  (confronto velocita' non disponibile: {e})")
    a("")

    out = {
        "variante_finale": variante_finale, "classe_esito": classe,
        "errore_mediano": round(err, 4), "ic90": [round(ic[0], 4), round(ic[1], 4)],
        "rho_loo": round(rho, 3), "rho_grezzo": round(ef["rho_grezzo"], 3),
        "n": ef["n"], "k": round(k, 4), "migliore_di_A": ef["migliore_di_A"],
        "incerto": bool(incerto),
        "varianti": {v: {kk: vv for kk, vv in r["esito"].items() if kk != "err"}
                     for v, r in risultati.items()},
        "tempi_percorsi": [{"percorso": p[0], "flusso_libero": round(a0, 1),
                            "v4_punta": None if t4 is None else round(a4, 1)}
                           for p, a0, a4 in zip(PERCORSI, t0, t4 or [None] * len(PERCORSI))],
    }
    (OUT / "valutazione_fase5.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))
    return variante_finale, classe


if __name__ == "__main__":
    main()
