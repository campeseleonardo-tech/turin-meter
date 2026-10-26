#!/usr/bin/env python3
"""
85_verifiche_correzioni.py  -  Risultato 6: verifiche INDIPENDENTI dei calcoli nuovi (81-84), rifatti con un
altro metodo. Preparato da Claude il 20/10/2026, da lanciare sul PC dopo 81 -> 82 -> 83 -> 84.

Verifiche
---------
  1. Auto del mattino (M_cint, M_tor, f_mattino) rifatte con pandas            -> uguali (+-1)
  2. Instradamento di 2 origini rifatto con networkx (se installato)           -> stesso flusso (+-0,01)
  3. c4 di 8 luoghi a caso rifatto a mano (tutti i tratti, distanza vera)      -> uguale
  4. Punteggio di 8 luoghi eleggibili rifatto con pandas (rank medio)          -> uguale (+-0,01)
  5. Classe di 8 fermate importanti rifatta a mano (distanze una per una)      -> uguale
  6. Regole "adatto" di 8 parcheggi a caso rifatte a mano                      -> coerenti
  7. Nessuna fermata importante, nessun punto, nessun parcheggio adatto in Q001-Q009
  8. Ogni fermata importante in una sola area
  A. Ogni fermata importante rispetta la regola fissa (N e M letti da fermate_importanti.json), ricalcolata
  B. Il testo della guida in mappa_template.html contiene i numeri N e M della regola (1.000 all'italiana)
Seme casuale 20261020. Scrive docs/rapporti/RAPPORTO_R6_VERIFICHE_CORREZIONI.txt. Codice di uscita 1 se una verifica
non torna (e' un controllo: non modifica nulla).

Come si lancia
--------------
  python scripts\\85_verifiche_correzioni.py
"""
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
P = RADICE / "data" / "processed" / "risultato6_v2"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6_VERIFICHE_CORREZIONI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
SEME = 20261020


def main():
    random.seed(SEME)
    c = comuni.Controlli()
    t0 = time.time()
    m81 = comuni.carica_script("81_auto_di_passaggio.py")
    pas = json.loads((P / "auto_passaggio.json").read_text(encoding="utf-8"))
    imp = json.loads((P / "fermate_importanti.json").read_text(encoding="utf-8"))
    porte = json.loads((P / "porte.json").read_text(encoding="utf-8"))
    ad = json.loads((P / "parcheggi_adatti.json").read_text(encoding="utf-8"))
    luoghi = {l["id_luogo"]: l for l in json.loads((P / "luoghi.json").read_text(encoding="utf-8"))["luoghi"]}
    seg = {s["id_luogo"]: s for s in json.loads((P / "segnali.json").read_text(encoding="utf-8"))["luoghi"]}
    parch = {p["id"]: p for p in json.loads((P / "parcheggi.json").read_text(encoding="utf-8"))["parcheggi"]}

    # 1. domanda con pandas
    import pandas as pd
    df = pd.read_csv(m81.SPOSTAMENTI, sep=";", dtype=str, encoding="utf-8-sig").fillna("")
    df["peso"] = pd.to_numeric(df["PESO"].str.replace(",", "."), errors="coerce").fillna(0.0)
    hm = df["ORA_PAR"].str.strip().str.split(":", expand=True)
    df["min"] = pd.to_numeric(hm[0], errors="coerce") * 60 + pd.to_numeric(hm[1], errors="coerce")
    for col in ("COD_PAR", "COD_ARR", "MEZZO1", "MEZZO2", "MEZZO3"):
        df[col] = df[col].str.strip()
    auto = df[df["MEZZO1"].isin(comuni.MODI_AUTO) & df["min"].between(*comuni.MATTINO_MINUTI)
              & (df["COD_PAR"] != "") & (df["COD_ARR"] != "")]
    cint = auto[~auto["COD_PAR"].str.startswith("Q") & auto["COD_ARR"].str.startswith("Q")]
    tor = auto[auto["COD_PAR"].str.startswith("Q") & ~auto["COD_PAR"].isin(comuni.ZONE_CENTRALI)
               & auto["COD_ARR"].isin(comuni.ZONE_CENTRALI)]
    f_m = cint[cint["MEZZO2"].isin(comuni.MEZZI_PUBBLICI) | cint["MEZZO3"].isin(comuni.MEZZI_PUBBLICI)]
    for nome, val, atteso in (("M_cint", cint["peso"].sum(), pas["M_cint"]), ("M_tor", tor["peso"].sum(), pas["M_tor"]),
                              ("f_mattino", f_m["peso"].sum(), pas["f_mattino"])):
        c(f"1. {nome} rifatto con pandas", abs(val - atteso) <= 1, dettaglio=f"{val:.1f} contro {atteso}")

    # 2-3. instradamento e c4
    if pas.get("c4_metodo") == "instradamento":
        import rete_osm
        rete = rete_osm.carica(m81.RETE_DIR)
        z = np.load(m81.OUT_NPZ)
        flusso_edge = z["flusso_edge"]
        try:
            import networkx as nx
            m42 = comuni.carica_script("42_instradamento.py")
            punti = json.loads(m81.PUNTI.read_text(encoding="utf-8"))
            _, _, cint_c, tor_c, _ = m81.leggi_domanda()
            celle = cint_c + (tor_c if pas["torinesi"] else [])
            origini, *_ = m42.carica_domanda_nodi(len(rete["nodi_xy"]), punti, celle)
            scelte = random.sample(sorted(origini), min(2, len(origini)))
            sotto = {o: origini[o] for o in scelte}
            fl_81, _, _ = m81.instrada(rete, sotto)
            fe_81 = np.bincount(rete["archi"][:, 3].astype(np.int64), weights=fl_81, minlength=len(rete["edge_a"]))
            G = nx.DiGraph()
            for a, b, t, e, *_ in rete["archi"]:
                a, b, e = int(a), int(b), int(e)
                if a != b and (not G.has_edge(a, b) or t < G[a][b]["weight"]):
                    G.add_edge(a, b, weight=float(t), e=e)
            fe_nx = np.zeros(len(rete["edge_a"]))
            for o, (dest, val) in sotto.items():
                _, cammini = nx.single_source_dijkstra(G, int(o))
                for d, v in zip(dest, val):
                    cm = cammini.get(int(d))
                    if cm:
                        for u, w in zip(cm[:-1], cm[1:]):
                            fe_nx[G[u][w]["e"]] += v
            diff = float(np.abs(fe_nx - fe_81).max())
            c("2. instradamento di 2 origini uguale a networkx", diff <= 0.01 * max(1.0, fe_nx.max()),
              dettaglio=f"differenza massima {diff:.3f} (con percorsi di uguale durata puo' differire: guardare)")
        except ImportError:
            c("2. networkx non installato: verifica dell'instradamento saltata", True)
        ids = random.sample(sorted(pas["luoghi"]), min(8, len(pas["luoghi"])))
        off, pts = rete["edge_off"], rete["edge_pts"]
        for i in ids:
            l = luoghi[i]
            # solo i tratti con un punto entro 1 km (per fare in fretta), poi distanza vera sul tracciato
            vicino = np.nonzero((np.abs(pts[:, 0] - l["lat"]) < 0.01) & (np.abs(pts[:, 1] - l["lon"]) < 0.013))[0]
            edges = set(np.searchsorted(off, vicino, side="right") - 1)
            best = 0.0
            for e in edges:
                if rete_osm.distanza_punto_tracciato_m(l["lat"], l["lon"], pts[off[e]:off[e + 1]]) <= m81.RAGGIO_STRADA_M:
                    best = max(best, float(flusso_edge[e]))
            c(f"3. c4 di {i} rifatto a mano", abs(round(best) - pas["luoghi"][i]["c4"]) <= 1,
              dettaglio=f"{round(best)} contro {pas['luoghi'][i]['c4']}")
    else:
        c("2-3. c4 col ripiego: verifiche dell'instradamento saltate", True)

    # 4. punteggio con pandas
    zone = {z["cod"]: z["macro"] for z in json.loads((RADICE / "data" / "processed" / "imq_zone.json").read_text(encoding="utf-8"))}
    el = [i for i, l in luoghi.items() if l.get("zona_imq") and zone.get(l["zona_imq"]) in comuni.MACRO_UNIVERSO
          and l["zona_imq"] not in comuni.ZONE_CENTRALI]
    t = pd.DataFrame({"id": el,
                      "a2": [seg.get(i, {}).get("a2") if seg.get(i, {}).get("a2") is not None else 1 for i in el],
                      "b2": [seg.get(i, {}).get("b2") or 0 for i in el],
                      "c4": [(pas["luoghi"].get(i) or {}).get("c4", 0) for i in el],
                      "e": [seg.get(i, {}).get("e") or 0 for i in el]}).set_index("id")
    pesi = imp["parametri"]["pesi"]
    n = len(t)
    pc = {s: (t[s].rank(method="average") - 1) / (n - 1) * 100 for s in ("a2", "b2", "c4")}
    pc["e"] = t["e"].astype(float)
    tot = sum(pesi.values())
    pt = sum(pesi[s] * pc[s] for s in pesi) / tot
    imp_pt = {x["id_luogo"]: x["punteggio"] for x in imp["importanti"]}
    for i in random.sample(sorted(imp_pt), min(8, len(imp_pt))):
        c(f"4. punteggio di {i} rifatto con pandas", abs(pt[i] - imp_pt[i]) <= 0.01, dettaglio=f"{pt[i]:.2f} contro {imp_pt[i]}")
    reg = imp["parametri"].get("regola")
    if reg:
        # regola fissa (Leo, 20/10), ricalcolata da nodi.json, segnali.json e auto_passaggio.json con N e M di fermate_importanti.json
        nodi = {n["id_luogo"]: n for n in json.loads((P / "nodi.json").read_text(encoding="utf-8"))["luoghi"]}
        nodo = {i: bool(nodi.get(i, {}).get("metro") or nodi.get(i, {}).get("ferro") or nodi.get(i, {}).get("capolinea")) for i in el}
        attese = {i for i in el if (nodo[i] or t.at[i, "b2"] >= reg["n_corse"]) and t.at[i, "c4"] >= reg["m_auto"]}
        c("A. ogni fermata importante rispetta la regola e nessuna fermata che la rispetta manca",
          set(imp_pt) == attese,
          dettaglio=f"regola N {reg['n_corse']}, M {reg['m_auto']}: {len(attese)} attese contro {len(imp_pt)}; "
                    f"fuori regola {len(set(imp_pt) - attese)}, mancanti {len(attese - set(imp_pt))}")
        template = (AQUI / "mappa_template.html").read_text(encoding="utf-8")
        m_it = f"{reg['m_auto']:,}".replace(",", ".")
        c("B. il testo della guida in mappa_template.html contiene i numeri della regola",
          f"almeno {reg['n_corse']} corse" in template and f"almeno {m_it} auto" in template,
          dettaglio=f"cercati «almeno {reg['n_corse']} corse» e «almeno {m_it} auto»")
    else:
        soglia = imp["soglia"]
        c("4. numero di fermate importanti dalla soglia", int((pt >= soglia - 0.005).sum()) == len(imp_pt),
          dettaglio=f"{int((pt >= soglia - 0.005).sum())} contro {len(imp_pt)}")

    # 5. classi
    par = porte["parametri"]
    raggio = par["raggio_piedi_m"] / par["fattore_piedi"]
    adatti = [parch[r["id"]] for r in ad["parcheggi"] if r["adatto"]]

    def posti(p):
        return int(p["posti_dichiarati"]) if p.get("posti_dichiarati") else int(p.get("posti_stimati") or 0)

    ferm = {f["id"]: f for f in porte["fermate"]}
    for fid in random.sample(sorted(ferm), min(8, len(ferm))):
        f = ferm[fid]
        pn = sum(posti(p) for p in adatti if comuni.haversine_m(f["lat"], f["lon"], p["lat"], p["lon"]) <= raggio)
        pot = (pas["luoghi"].get(fid) or {}).get("c4", 0) * par["quota_mattino"]
        cl = ("Poche auto da fermare" if pot < par["min_auto"] else "Nessun parcheggio" if pn <= 0
              else "Posti insufficienti" if pn < pot else "Posti sufficienti")
        c(f"5. classe di {fid} rifatta a mano", cl == f["classe"] and abs(pn - f["posti_adatti"]) <= 1,
          dettaglio=f"{cl} / {pn} posti contro {f['classe']} / {f['posti_adatti']}")

    # 6. regole "adatto"
    centrali = set(comuni.ZONE_CENTRALI)
    for r in random.sample(ad["parcheggi"], min(8, len(ad["parcheggi"]))):
        p = parch[r["id"]]
        atteso = (p["tipo"] in ("interscambio_ufficiale", "garage_5t", "park_ride_osm", "osm_pubblico")
                  and r["zona_imq"] not in centrali and posti(p) >= ad["parametri"]["posti_minimi"]
                  and not (r["motivo"] or "").startswith("destinazione_"))
        c(f"6. regole 'adatto' di {r['id']} ({p['tipo']})", atteso == r["adatto"], dettaglio=f"motivo {r['motivo']}")

    # 7-8. centro e aree
    c("7. nessuna fermata importante in Q001-Q009", not any(f["zona"] in centrali for f in porte["fermate"]))
    c("7. nessun parcheggio adatto in Q001-Q009", not any(r["zona_imq"] in centrali for r in ad["parcheggi"] if r["adatto"]))
    vic = [p for p in porte["punti_prioritari"]
           if comuni.haversine_m(p["centro"][0], p["centro"][1], comuni.CENTRO_LAT, comuni.CENTRO_LON) < 2500]
    c("7. punti prioritari vicini al centro (solo informazione: le loro fermate sono fuori da Q001-Q009)", True,
      dettaglio="a meno di 2,5 km da Piazza Castello: " + (", ".join(p["nome"] for p in vic) or "nessuno"))
    pp = porte["punti_prioritari"]

    def dist(p, q):
        return comuni.haversine_m(p["centro"][0], p["centro"][1], q["centro"][0], q["centro"][1])
    doppi = [(p["nome"], q["nome"]) for i, p in enumerate(pp) for q in pp[i + 1:]
             if dist(p, q) < 2000 or (p.get("strada") and p.get("strada") == q.get("strada") and dist(p, q) < 5000)]
    c("7. un punto per asse (rifatto: nessuna coppia di punti a meno di 2 km o sulla stessa strada a meno di 5 km)",
      not doppi, dettaglio=", ".join(f"{a}-{b}" for a, b in doppi) or f"{len(pp)} punti")
    c("7. nessun punto prioritario a meno di 3 km da Piazza Castello (rifatto da zero)",
      not any(comuni.haversine_m(p["centro"][0], p["centro"][1], comuni.CENTRO_LAT, comuni.CENTRO_LON) < 3000 for p in pp))
    c("8. ogni fermata importante in una sola area", sum(a["n_fermate"] for a in porte["aree"]) == len(porte["fermate"]))

    errori = [r for r in c.righe if not r.startswith("OK")]
    RAPPORTO.write_text("\n".join(["RAPPORTO R6 - VERIFICHE INDIPENDENTI DELLE CORREZIONI (script 85)",
                                   f"Generato il {time.strftime('%d/%m/%Y %H:%M')}; seme {SEME}.", "",
                                   *c.righe, "", f"Verifiche non superate: {len(errori)}"]) + "\n", encoding="utf-8")
    print(f"Scritto: {RAPPORTO}\nVerifiche non superate: {len(errori)}; durata {time.time() - t0:.0f} s")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
