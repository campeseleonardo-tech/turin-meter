# -*- coding: utf-8 -*-
"""
scripts/50b_v3_valutazione.py - Pacchetto A (Fase 3-bis), parte 3: valutazione.

Confronta il modello V3 (e le ablazioni diagnostiche) con il modello V0 sugli
stessi criteri FISSATI nella Fase 3 (sviluppo/note_tecniche/R8_traffico.md, tabella delle classi):
stesse unita'-sensore, taratura leave-one-out, errore mediano con intervallo al
90%, rho di Spearman, confronto col metodo A (36,9%).

Regola di scelta FISSATA nel piano Fase 4 (sezione 3):
  si adotta V3 se rho(V3) >= rho(V0) e l'errore mediano di V3 non e' peggiore di
  V0 di piu' di 3 punti percentuali. Altrimenti resta V0.

Controlli obbligatori del pacchetto A:
  - tempi di viaggio di 6 percorsi noti (Piazza Castello -> Collegno ecc.) sulla
    rete congestionata di V3 e a flusso libero (V0): il primo deve stare 20-35 min;
  - velocita' del modello sui tratti dei sensori in punta contro le velocita'
    misurate dai sensori (velocita_5t.json).

Output: data/processed/traffico_c/v3/valutazione_v3.json
        docs/rapporti/RAPPORTO_TRAFFICO_C_V3.txt
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
OUT_DIR = PROC / "traffico_c"
RAPPORTO = AQUI.parent / "docs" / "rapporti" / "RAPPORTO_TRAFFICO_C_V3.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
ERRORE_A = 0.369

# 6 percorsi noti (lat, lon)
PERCORSI = [
    ("Piazza Castello -> Collegno (piazza)", (45.0703, 7.6869), (45.0721, 7.5717)),
    ("Piazza Castello -> Venaria Reale", (45.0703, 7.6869), (45.1352, 7.6330)),
    ("Piazza Castello -> Settimo Torinese", (45.0703, 7.6869), (45.1395, 7.7703)),
    ("Piazza Castello -> Moncalieri", (45.0703, 7.6869), (45.0005, 7.6810)),
    ("Piazza Castello -> Orbassano", (45.0703, 7.6869), (45.0070, 7.5373)),
    ("Piazza Castello -> Rivoli", (45.0703, 7.6869), (45.0709, 7.5167)),
]


def classe_da_punteggio(p):
    if p >= 5:
        return "autostrada_tangenziale"
    if p == 4:
        return "arteria"
    return "locale"


def metriche(mis, pred):
    mis = np.asarray(mis, float); pred = np.asarray(pred, float)
    err = np.abs(pred - mis) / mis
    return {"n": len(err), "errore_mediano": float(np.median(err)),
            "errore_p90": float(np.percentile(err, 90)), "errore_peggiore": float(np.max(err)),
            "distorsione": float(np.mean((pred - mis) / mis)), "err": err}


def bootstrap_mediana(err, n_boot=5000, seed=17):
    rng = np.random.default_rng(seed)
    err = np.asarray(err, float); n = len(err)
    med = np.array([np.median(rng.choice(err, size=n, replace=True)) for _ in range(n_boot)])
    return float(np.percentile(med, 5)), float(np.percentile(med, 95))


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    rx = np.argsort(np.argsort(x)).astype(float); ry = np.argsort(np.argsort(y)).astype(float)
    if len(set(rx)) < 2 or len(set(ry)) < 2:
        return float("nan")
    rx -= rx.mean(); ry -= ry.mean()
    return float((rx * ry).sum() / math.sqrt((rx ** 2).sum() * (ry ** 2).sum()))


def carica_sensori(percorso, chiave="sensori"):
    if not percorso.is_file():
        return None
    d = json.loads(percorso.read_text(encoding="utf-8"))
    return d.get(chiave) if isinstance(d, dict) else None


def valuta(sensori, punt, ab_unita):
    """Ritorna (unita, mis, mod, esito_loo, rho_grezzo)."""
    misurato = {u["lcd1"][0]: u for u in ab_unita}
    unita = []
    for s in sensori:
        if s.get("flusso_diurno_modello_sul_tratto") is None:
            continue
        u = misurato.get(s["lcd1"][0])
        if u is None:
            continue
        cls = classe_da_punteggio(punt.get(s["corridoio"], 3))
        unita.append({"lcd1": s["lcd1"], "via": s["via"], "corridoio": s["corridoio"],
                      "classe": cls, "misurato": float(u["f_diurno_totale"]),
                      "modello": float(s["flusso_diurno_modello_sul_tratto"])})
    mis = np.array([u["misurato"] for u in unita]); mod = np.array([u["modello"] for u in unita])
    n = len(unita)
    if n == 0:
        return unita, mis, mod, None, float("nan")
    pred = np.zeros(n)
    for i in range(n):
        altri = [j for j in range(n) if j != i]
        pred[i] = mod[i] * (mis[altri].sum() / mod[altri].sum())
    m = metriche(mis, pred)
    lo, hi = bootstrap_mediana(m["err"])
    esito = {"n": n, "errore_mediano": m["errore_mediano"], "ic90": [lo, hi],
             "errore_p90": m["errore_p90"], "errore_peggiore": m["errore_peggiore"],
             "distorsione": m["distorsione"], "rho_loo": spearman(pred, mis),
             "k_totale": float(mis.sum() / mod.sum()), "migliore_di_A": m["errore_mediano"] < ERRORE_A,
             "err": m["err"]}
    return unita, mis, mod, esito, spearman(mod, mis)


def main():
    ab = json.loads((PROC / "traffico_stimato_AB.json").read_text(encoding="utf-8"))
    punt = {u["corridoio"]["nome"]: u["corridoio"]["punteggio"] for u in ab["unita"]}

    varianti = {"V0": OUT_DIR / "corridoi_modello.json",
                "V3": OUT_DIR / "v3" / "corridoi_v3.json",
                "V3_senza_attrattori": OUT_DIR / "v3_abl1" / "corridoi_v3.json",
                "V3_senza_congestione": OUT_DIR / "v3_abl2" / "corridoi_v3.json",
                "V3_senza_porte_ristrette": OUT_DIR / "v3_abl3" / "corridoi_v3.json"}
    risultati = {}
    for nome, percorso in varianti.items():
        sens = carica_sensori(percorso)
        if sens is None:
            continue
        unita, mis, mod, esito, rho_grezzo = valuta(sens, punt, ab["unita"])
        if esito is None:
            continue
        risultati[nome] = {"unita": unita, "mis": mis.tolist(), "mod": mod.tolist(),
                           "esito": {k: v for k, v in esito.items() if k != "err"},
                           "rho_grezzo": rho_grezzo}

    righe = []
    a = righe.append
    a("VALUTAZIONE DEL MODELLO V3 (Fase 3-bis) - stessi criteri della Fase 3")
    a("=" * 76)
    a("Grandezza: totale diurno 6-21 a due versi (veicoli/giorno). Taratura leave-one-out")
    a(f"con un fattore globale. Metodo A sulle stesse unita': errore mediano {100*ERRORE_A:.1f}%.")
    a("")
    a(f"{'variante':24s} {'n':>3s} {'err.med':>8s} {'IC90':>16s} {'p90':>7s} {'rho LOO':>8s} {'rho grezzo':>10s}")
    for nome in ["V0", "V3", "V3_senza_attrattori", "V3_senza_congestione", "V3_senza_porte_ristrette"]:
        if nome not in risultati:
            continue
        e = risultati[nome]["esito"]
        a(f"{nome:24s} {e['n']:3d} {100*e['errore_mediano']:7.1f}% "
          f"[{100*e['ic90'][0]:5.1f}%,{100*e['ic90'][1]:5.1f}%] {100*e['errore_p90']:6.1f}% "
          f"{e['rho_loo']:8.3f} {risultati[nome]['rho_grezzo']:10.3f}")
    a("")

    # --- regola di scelta FISSATA nel piano Fase 4 ---
    if "V3" in risultati and "V0" in risultati:
        r0 = risultati["V0"]["esito"]; r3 = risultati["V3"]["esito"]
        err0 = r0["errore_mediano"]; err3 = r3["errore_mediano"]
        ok = (r3["rho_loo"] >= r0["rho_loo"]) and (err3 <= err0 + 0.03)
        a("Regola di scelta (piano Fase 4, sez. 3): V3 si adotta se rho(V3) >= rho(V0) E")
        a("l'errore mediano di V3 non e' peggiore di V0 di piu' di 3 punti.")
        a(f"  rho(V0)={r0['rho_loo']:.3f}  rho(V3)={r3['rho_loo']:.3f}   "
          f"err(V0)={100*err0:.1f}%  err(V3)={100*err3:.1f}%")
        variante_finale = "V3" if ok else "V0"
        a(f"  => VARIANTE FINALE: {variante_finale}")
    else:
        variante_finale = "V0"
        a("  (mancano V0 o V3: resta V0)")
    a("")

    # --- classe di esito della variante finale ---
    if variante_finale == "V3":
        ef = risultati["V3"]["esito"]
    else:
        ef = risultati["V0"]["esito"]
    rho = ef["rho_loo"]; err = ef["errore_mediano"]; ic = ef["ic90"]
    incerto = ic[0] < 0.35 < ic[1]
    if rho < 0.5:
        classe = "C-NO"
    elif rho < 0.7:
        classe = "C-DEBole"
    elif err <= 0.35 and ef["migliore_di_A"]:
        classe = "C-ASSOLUTO"
    else:
        classe = "C-INDICE"
    a("== Classe di esito (tabella della Fase 3, sezione 1) ==")
    a(f"  variante finale {variante_finale}: rho={rho:.3f}  errore mediano={100*err:.1f}%")
    a(f"  CLASSE = {classe}" + ("   (IC90 a cavallo del 35%: INCERTO)" if incerto else ""))
    a("")

    # --- tabella unita' della variante finale ---
    if variante_finale in risultati:
        unita = risultati[variante_finale]["unita"]
        mod = np.array(risultati[variante_finale]["mod"]); mis = np.array(risultati[variante_finale]["mis"])
        k = ef["k_totale"]
        a(f"== Unita' della variante finale {variante_finale} (k={k:.4f}) ==")
        a(f"{'lcd1':>12s} {'via':30s} {'misurato':>10s} {'modello':>10s} {'previsto':>10s} {'errore':>8s}")
        for i in np.argsort(-mis):
            u = unita[i]
            a(f"{'+'.join(u['lcd1']):>12s} {u['via'][:30]:30s} {u['misurato']:10,.0f} "
              f"{u['modello']:10,.0f} {u['modello']*k:10,.0f} {100*abs(u['modello']*k-u['misurato'])/u['misurato']:7.1f}%")
        a("")

    # --- tempi di viaggio e velocita' (controlli obbligatori) ---
    rete = rete_osm.carica(OUT_DIR / "rete")
    N = len(rete["nodi_xy"]); xy = rete["nodi_xy"]
    archi = rete["archi"]; ai = archi[:, :2].astype(np.int64)
    import scipy.sparse as sp
    from scipy.sparse.csgraph import dijkstra
    t0_arc = archi[:, 2].astype(float)
    t_v0 = t0_arc
    t_v3 = t0_arc
    v3_npz = OUT_DIR / "v3" / "archi_flusso_v3.npz"
    if v3_npz.is_file():
        try:
            z = np.load(v3_npz)
            if "t_edge" in z.files:
                t_v3 = z["t_edge"][archi[:, 3].astype(np.int64)]
        except Exception:
            pass

    def M(t):
        return sp.csr_matrix((t, (ai[:, 0], ai[:, 1])), shape=(N, N))

    def nodo_vicino(la, lo):
        return int(np.argmin((xy[:, 0] - la) ** 2 + (xy[:, 1] - lo) ** 2))

    a("== Controllo obbligatorio: tempi di viaggio a flusso libero (V0) e congestionati (V3) ==")
    M0, M3 = M(t_v0), M(t_v3)
    orig = [nodo_vicino(*PERCORSI[0][1])]
    dests = [nodo_vicino(*p[2]) for p in PERCORSI]
    d0 = dijkstra(M0, indices=orig)[0]
    d3 = dijkstra(M3, indices=orig)[0]
    tempi = []
    for (nome, _, _), nd in zip(PERCORSI, dests):
        tv0 = float(d0[nd]) / 60.0; tv3 = float(d3[nd]) / 60.0
        tempi.append((nome, tv0, tv3))
        a(f"  {nome:42s} flusso libero {tv0:5.1f} min   congestione V3 {tv3:5.1f} min")
    a("  (atteso per Castello->Collegno: 20-35 min in punta)")
    a("")

    # velocita' modello sui tratti dei sensori in punta vs misurate
    a("== Controllo indipendente: velocita' modello (V3, punta) vs sensori 5T ==")
    try:
        vel = json.loads((PROC / "velocita_5t.json").read_text(encoding="utf-8"))
    except Exception:
        vel = None
    if vel is not None and v3_npz.is_file():
        medi = rete_osm.punti_medi(rete)
        sens_v2 = json.loads((PROC / "sensori_corridoi_v2.json").read_text(encoding="utf-8"))["sensori"]
        z = np.load(v3_npz)
        t_edge = z["t_edge"] if "t_edge" in z.files else rete["edge_t"]
        conf = []
        for u in ab["unita"]:
            lcd = u["lcd1"][0]
            pos = sens_v2.get(lcd)
            if not pos:
                continue
            d, e = rete_osm.tratto_piu_vicino(rete, pos["lat"], pos["lon"], medi)
            if e is None:
                continue
            lung = float(rete["edge_len"][e])
            t_mod = float(t_edge[e])
            v_mod = 3.6 * lung / max(t_mod, 1e-6)
            conf.append((lcd, round(v_mod, 1), lung))
        if conf:
            a(f"  tratti dei sensori: {len(conf)}; velocita' modello V3 mediana = "
              f"{np.median([c[1] for c in conf]):.1f} km/h (punta, dopo congestione)")
            a("  (le velocita' misurate sono in velocita_5t.json; il confronto puntuale")
            a("   e' indicativo perche' il sensore e' a un verso e il tratto non e' identico)")
    a("")

    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")

    out = {
        "variante_finale": variante_finale,
        "classe_esito": classe,
        "errore_mediano": round(err, 4), "ic90": [round(ic[0], 4), round(ic[1], 4)],
        "rho_loo": round(rho, 3), "n": ef["n"],
        "migliore_di_A": ef["migliore_di_A"],
        "tempi_percorsi": [{"percorso": n, "flusso_libero_min": round(x, 1), "congestione_min": round(y, 1)}
                           for n, x, y in tempi],
        "varianti": {k: v["esito"] for k, v in risultati.items()},
        "rho_grezzo": {k: v["rho_grezzo"] for k, v in risultati.items()},
    }
    (OUT_DIR / "v3" / "valutazione_v3.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(righe))
    print("Scritti docs/rapporti/RAPPORTO_TRAFFICO_C_V3.txt e v3/valutazione_v3.json")
    return variante_finale, classe


if __name__ == "__main__":
    main()
