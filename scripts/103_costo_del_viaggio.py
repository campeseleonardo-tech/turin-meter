# -*- coding: utf-8 -*-
"""
scripts/103_costo_del_viaggio.py - Risultato 12 (scheda 6, giro L14): quanto costa muoversi, in auto e coi mezzi pubblici, oggi.

Due livelli di costo dell'auto:
- «che si sente»: carburante (consumo urbano x prezzo) + parcheggio all'arrivo;
- «pieno»: costo chilometrico ACI (carburante, manutenzione, assicurazione, pneumatici, ammortamento) + parcheggio.
Mezzi pubblici: biglietti o abbonamento GTT. Tutti i prezzi stanno in data/ref/costi.json (valori, fonte, indirizzo, data): lo script non ne contiene.

Regole (fissate il 24/10/2026 PRIMA dei numeri, `sviluppo/piani/PROMPT_LAVORI.md` blocco L14, con queste precisazioni scritte prima di calcolare):
- chilometri = lunghezza del percorso piu' veloce sulla rete del modello del traffico (stessa rete e stesso cammino minimo dello script 93);
- auto che si sente = km x consumo x prezzo, andata e ritorno, + parcheggio (2 ore in centro per una commissione, 8 ore per il lavoro; tariffa ordinaria);
  auto piena = km x costo ACI per km, andata e ritorno, + parcheggio; il costo e' la media delle due auto di riferimento (stessa Golf a benzina e a gasolio);
- mezzi: 2 biglietti per la commissione; per il lavoro l'abbonamento mensile (= 38 euro diviso 40 viaggi); lavoro = 20 giorni al mese, 2 viaggi al giorno;
- confronti: i 12 punti prioritari del R6 e i 5 interscambi verso Piazza Castello (auto fino al centro contro i mezzi dal punto), e le coppie Torino-Torino
  dello script 93 (nessun parcheggio: la destinazione non e' il centro; solo carburante e costo ACI; fasce di distanza fisse: sotto 3 km, 3-6, 6-10, oltre 10);
- numero grande: quanto costa in piu' l'auto del bus per andare al lavoro in centro, al mese, mediana dei 12 punti, costo che si sente; il costo pieno va nel testo;
- cintura: tariffe a zone non assegnate alle zone dell'indagine, la cintura resta fuori (AVVISO nel rapporto);
- limiti: prezzi di un periodo preciso, consumo medio e non della propria auto, agevolazioni non considerate, ZTL e abbonamenti alla sosta non nel calcolo.
Le distanze vengono dalla rete OSM del modello (nessun servizio esterno; dal giro F3 non c'e' piu' il controllo con un altro servizio).

Come si lancia
--------------
  python scripts\\103_costo_del_viaggio.py            (rete OSM e JSON degli script 93 e 94)
  python scripts\\103_costo_del_viaggio.py --prova    (dati finti, file con suffisso _prova)
Uscite: data/processed/costo_del_viaggio.json, docs/rapporti/RAPPORTO_COSTO_DEL_VIAGGIO.txt
"""
import argparse
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
COSTI = RADICE / "data" / "ref" / "costi.json"
OUT_JSON = PROC / "costo_del_viaggio.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_COSTO_DEL_VIAGGIO.txt"

GIORNI_MESE = 20                                   # 20 giorni di lavoro al mese, 2 viaggi al giorno
ORE_COMMISSIONE, ORE_LAVORO = 2, 8                 # ore di sosta in centro
VIAGGI_ABBONAMENTO = 40                            # abbonamento mensile / 40 viaggi
FASCE_KM = [(0.0, 3.0), (3.0, 6.0), (6.0, 10.0), (10.0, 999.0)]
CASTELLO = (45.0703, 7.6869)


def costi_viaggio(km, c):
    """Costi (euro) di un viaggio di `km` chilometri (solo andata) verso il centro, per commissione e per lavoro, auto e mezzi.
    c = data/ref/costi.json. L'auto e' la media delle due auto di riferimento."""
    auto = c["auto"]
    prezzo = {"benzina": c["carburante"]["benzina_self_eur_l"], "gasolio": c["carburante"]["gasolio_self_eur_l"]}
    sente_km = {k: auto[k]["consumo_urbano_l_100km"] / 100.0 * prezzo[k] for k in ("benzina", "gasolio")}
    pieno_km = {k: auto[k]["costo_pieno_eur_km"] for k in ("benzina", "gasolio")}
    s_km, p_km = float(np.mean(list(sente_km.values()))), float(np.mean(list(pieno_km.values())))
    ora = c["sosta"]["tariffe_eur_ora"]["ordinaria"]
    sosta_c, sosta_l = ORE_COMMISSIONE * ora, ORE_LAVORO * ora
    biglietto = c["gtt"]["biglietto_urbano_eur"]
    abb = c["gtt"]["abbonamento_mensile_urbano_eur"]
    mezzi_c, mezzi_mese = 2 * biglietto, abb
    return {"km": round(km, 2),
            "commissione": {"auto_sente": 2 * km * s_km + sosta_c, "auto_piena": 2 * km * p_km + sosta_c, "mezzi": mezzi_c},
            "lavoro_mese": {"auto_sente": GIORNI_MESE * (2 * km * s_km + sosta_l), "auto_piena": GIORNI_MESE * (2 * km * p_km + sosta_l), "mezzi": mezzi_mese},
            "lavoro_mese_senza_sosta": {"auto_sente": GIORNI_MESE * 2 * km * s_km, "auto_piena": GIORNI_MESE * 2 * km * p_km, "mezzi": mezzi_mese},
            "per_auto": {k: {"sente_km": sente_km[k], "pieno_km": pieno_km[k]} for k in sente_km}}


def arrotonda(d, n=2):
    if isinstance(d, dict):
        return {k: arrotonda(v, n) for k, v in d.items()}
    if isinstance(d, float):
        return round(d, n)
    return d


def grafo():
    """Come matrice_auto dello script 93: matrice dei tempi (arco piu' veloce fra i duplicati) piu' le lunghezze degli stessi archi (metri)."""
    from scipy.sparse import csr_matrix
    import rete_osm
    rete = rete_osm.carica(PROC / "traffico_c" / "rete")
    xy, archi = rete["nodi_xy"], rete["archi"]
    N = len(xy)
    src, dst, w = archi[:, 0].astype(np.int64), archi[:, 1].astype(np.int64), archi[:, 2].astype(np.float64)
    chiave = src * N + dst
    ordine = np.lexsort((w, chiave))
    chiave_s = chiave[ordine]
    primo = np.concatenate(([True], chiave_s[1:] != chiave_s[:-1]))
    sel = ordine[primo]
    tieni = src[sel] != dst[sel]
    sel = sel[tieni]
    M = csr_matrix((w[sel], (src[sel], dst[sel])), shape=(N, N))
    lung = {(int(src[i]), int(dst[i])): float(rete["edge_len"][int(archi[i, 3])]) for i in sel}
    return M, lung


def km_percorsi(M, lung, coppie_nodi):
    """{(a, b): km} lungo il percorso piu' veloce (come lo script 93), per tutte le coppie di nodi chieste."""
    from scipy.sparse.csgraph import dijkstra
    per_origine = defaultdict(set)
    for a, b in coppie_nodi:
        per_origine[a].add(b)
    out = {}
    for a, destinazioni in per_origine.items():
        dist, pred = dijkstra(M, indices=a, return_predecessors=True)
        for b in destinazioni:
            if not np.isfinite(dist[b]):
                out[(a, b)] = None
                continue
            m, v = 0.0, b
            while v != a:
                u = int(pred[v])
                m += lung[(u, v)]
                v = u
            out[(a, b)] = m / 1000.0
    return out


def dati_finti():
    luoghi = [{"nome": f"PUNTO {i}", "tipo": "punto_prioritario", "lat": 45.0 + i / 100, "lon": 7.6, "km": 3.0 + 2 * i, "tp_min": 30.0 + 5 * i,
               "auto_stima_min": 15.0 + 2 * i, "rapporto_basso": 2.0} for i in range(1, 4)]
    coppie = [{"da": "Q001", "a": "Q002", "auto": 100.0 * i, "km": float(i)} for i in range(1, 7)]
    return luoghi, coppie


def mediana(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true", help="dati finti, file con suffisso _prova")
    args = ap.parse_args()
    c = comuni.Controlli()
    costi = json.loads(COSTI.read_text(encoding="utf-8"))
    pb, pg = costi["carburante"]["benzina_self_eur_l"], costi["carburante"]["gasolio_self_eur_l"]
    c("prezzi dei carburanti fra 1 e 3 euro al litro", 1 <= pb <= 3 and 1 <= pg <= 3, bloccante=True, dettaglio=f"benzina {pb}, gasolio {pg}")

    if args.prova:
        luoghi, coppie = dati_finti()
    else:
        comuni.richiedi_fonte(PROC / "imq_zone.json")      # derivato dall'IMQ, fuori da git: serve per i nomi delle zone dello script 93
        m93 = comuni.carica_script("93_tp_contro_auto.py")
        r6 = json.loads((PROC / "r6_bus_contro_auto.json").read_text(encoding="utf-8"))
        luoghi = [dict(l) for l in r6["luoghi"]]
        tp = json.loads((PROC / "tp_contro_auto.json").read_text(encoding="utf-8"))
        coppie = [dict(p) for p in tp["coppie"] if p["gruppo"] == "a"]
        zone_tutte = m93.carica_zone(False)
        zone = {z: v for z, v in zone_tutte.items() if z.startswith("Q")}                  # solo Torino (cod. Q...)
        extra = [(l["nome"], (l["lat"], l["lon"]), CASTELLO) for l in luoghi]
        _t, nodi_extra, _sp = m93.matrice_auto(zone, extra)                                # aggancia i nodi come nello script 93
        M, lung = grafo()
        nodi_luoghi = {l["nome"]: nodi_extra[k] for k, l in enumerate(luoghi)}
        richieste = [nodi_luoghi[l["nome"]] for l in luoghi]
        km_l = km_percorsi(M, lung, richieste)
        for l in luoghi:
            a, b = nodi_luoghi[l["nome"]]
            l["km"] = km_l[(a, b)]
        c("tutti i luoghi hanno una lunghezza", all(l["km"] is not None for l in luoghi), bloccante=True)
        senza = [(p["da"], p["a"]) for p in coppie if p["da"] not in zone or p["a"] not in zone]
        c("coppie Torino-Torino con le zone sul grafo", not senza, bloccante=True, dettaglio=f"{len(senza)} fuori")
        cn = {(pa["nodo"], pb_["nodo"]) for p in coppie for pa in zone[p["da"]]["punti"] for pb_ in zone[p["a"]]["punti"]}
        km_p = km_percorsi(M, lung, cn)
        for p in coppie:
            tot, ok = 0.0, True
            for pa in zone[p["da"]]["punti"]:
                for pb_ in zone[p["a"]]["punti"]:
                    k = km_p[(pa["nodo"], pb_["nodo"])]
                    if k is None:
                        ok = False
                        continue
                    tot += pa["peso"] * pb_["peso"] * k
            p["km"] = tot if ok else None
        coppie = [p for p in coppie if p["km"] is not None]

    km_tutti = [l["km"] for l in luoghi] + [p["km"] for p in coppie]
    c("chilometri fra 1 e 80", all(1.0 <= k <= 80.0 for k in km_tutti), bloccante=True, dettaglio=f"da {min(km_tutti):.1f} a {max(km_tutti):.1f}")

    for l in luoghi:
        l.update(costi_viaggio(l["km"], costi))
        l["minuti_in_piu_coi_mezzi"] = round(l["tp_min"] - l["auto_stima_min"], 1) if l.get("tp_min") is not None else None
        l["risparmio_mese_sente"] = l["lavoro_mese"]["auto_sente"] - l["lavoro_mese"]["mezzi"]
        l["risparmio_mese_pieno"] = l["lavoro_mese"]["auto_piena"] - l["lavoro_mese"]["mezzi"]
    punti = [l for l in luoghi if l["tipo"] == "punto_prioritario"]
    inter = [l for l in luoghi if l["tipo"] == "interscambio"]
    tutti_costi = [x for l in luoghi for sez in ("commissione", "lavoro_mese") for x in l[sez].values()]
    c("nessun costo negativo o nullo", all(x > 0 for x in tutti_costi), bloccante=True)
    c("l'auto che si sente costa meno dell'auto piena", all(l["lavoro_mese"]["auto_sente"] < l["lavoro_mese"]["auto_piena"] for l in luoghi), bloccante=True)

    # coppie Torino-Torino per fascia di distanza (lavoro al mese, senza sosta)
    fasce = []
    for da, a in FASCE_KM:
        s = [p for p in coppie if da <= p["km"] < a]
        cs = [costi_viaggio(p["km"], costi)["lavoro_mese_senza_sosta"] for p in s]
        fasce.append({"da_km": da, "a_km": None if a > 500 else a, "coppie": len(s), "auto": round(sum(p["auto"] for p in s)),
                      "km_mediano": round(mediana([p["km"] for p in s]), 1) if s else None,
                      "auto_sente_mese": round(mediana([x["auto_sente"] for x in cs]), 2) if s else None,
                      "auto_piena_mese": round(mediana([x["auto_piena"] for x in cs]), 2) if s else None,
                      "mezzi_mese": costi["gtt"]["abbonamento_mensile_urbano_eur"]})
    c("coppie nelle fasce = coppie con chilometri", sum(f["coppie"] for f in fasce) == len(coppie), bloccante=True, dettaglio=f"{len(coppie)} coppie")
    c("coppie Torino-Torino in ogni fascia", all(f["coppie"] > 0 for f in fasce), dettaglio=", ".join(f"{f['coppie']}" for f in fasce))
    c("cintura: tariffe a zone non assegnate alle zone dell'indagine", False, dettaglio="la cintura resta fuori; la scheda usa Torino e i punti del R6")

    sente = mediana([l["risparmio_mese_sente"] for l in punti])
    pieno = mediana([l["risparmio_mese_pieno"] for l in punti])
    riepilogo = {"punti": len(punti), "interscambi": len(inter), "coppie_torino": len(coppie),
                 "differenza_mese_sente_mediana": round(sente, 2), "differenza_mese_pieno_mediana": round(pieno, 2),
                 "auto_mese_sente_mediana": round(mediana([l["lavoro_mese"]["auto_sente"] for l in punti]), 2),
                 "auto_mese_pieno_mediana": round(mediana([l["lavoro_mese"]["auto_piena"] for l in punti]), 2),
                 "mezzi_mese": costi["gtt"]["abbonamento_mensile_urbano_eur"],
                 "minuti_in_piu_mediana": round(mediana([l["minuti_in_piu_coi_mezzi"] for l in punti if l["minuti_in_piu_coi_mezzi"] is not None]), 1),
                 "commissione_auto_sente_mediana": round(mediana([l["commissione"]["auto_sente"] for l in punti]), 2),
                 "commissione_auto_piena_mediana": round(mediana([l["commissione"]["auto_piena"] for l in punti]), 2),
                 "commissione_mezzi": punti[0]["commissione"]["mezzi"],
                 "parcheggio_lavoro_giorno": round(ORE_LAVORO * costi["sosta"]["tariffe_eur_ora"]["ordinaria"], 2),
                 "carburante_giorno_mediana": round(mediana([l["lavoro_mese"]["auto_sente"] / GIORNI_MESE - ORE_LAVORO * costi["sosta"]["tariffe_eur_ora"]["ordinaria"] for l in punti]), 2),
                 "km_mediano_punti": round(mediana([l["km"] for l in punti]), 1)}
    # un mese di lavoro in centro, due casi (L22): sosta pagata in strada e parcheggio gratis al lavoro; mezzi: biglietti, abbonamenti, tariffe agevolate GTT
    ora_sosta = costi["sosta"]["tariffe_eur_ora"]["ordinaria"]
    carb_mese = mediana([l["lavoro_mese_senza_sosta"]["auto_sente"] for l in punti])
    pieno_senza_sosta = mediana([l["lavoro_mese_senza_sosta"]["auto_piena"] for l in punti])
    agevolati = []
    for v in costi["gtt"]["agevolati"]["voci"]:
        mese = v["eur_mese"] if "eur_mese" in v else (v["eur_anno"] + v.get("spese_pratica_eur", 0.0)) / 12.0
        agevolati.append({"id": v["id"], "nome": v["nome"], "eur_mese": round(mese, 2), "annuale": "eur_anno" in v, "eur_anno": v.get("eur_anno")})
    # chilometri sotto i quali, senza sosta da pagare, l'auto che si sente costa meno dell'abbonamento mensile (stessa formula di costi_viaggio)
    euro_per_km_mese = costi_viaggio(1.0, costi)["lavoro_mese_senza_sosta"]["auto_sente"]
    riepilogo["soglia_km_senza_sosta"] = round(costi["gtt"]["abbonamento_mensile_urbano_eur"] / euro_per_km_mese, 2)
    riepilogo["mese"] = {
        "sosta_pagata": {"sente": riepilogo["auto_mese_sente_mediana"], "pieno": riepilogo["auto_mese_pieno_mediana"],
                         "carburante": round(carb_mese, 2), "sosta": round(GIORNI_MESE * ORE_LAVORO * ora_sosta, 2)},
        "parcheggio_gratis": {"sente": round(carb_mese, 2), "pieno": round(pieno_senza_sosta, 2)},
        "mezzi": {"biglietti": round(VIAGGI_ABBONAMENTO * costi["gtt"]["biglietto_urbano_eur"], 2), "mensile": costi["gtt"]["abbonamento_mensile_urbano_eur"],
                  "annuale_su_12": round(costi["gtt"]["abbonamento_annuale_urbano_eur"] / 12.0, 2), "agevolati": agevolati}}
    c("la sosta pagata pesa piu' del carburante (caso principale)", riepilogo["mese"]["sosta_pagata"]["sosta"] > riepilogo["mese"]["sosta_pagata"]["carburante"])
    out = {"titolo": "Quanto costa muoversi", "consultato": costi["consultato"],
           "regole": {"giorni_mese": GIORNI_MESE, "ore_sosta_commissione": ORE_COMMISSIONE, "ore_sosta_lavoro": ORE_LAVORO, "viaggi_abbonamento": VIAGGI_ABBONAMENTO,
                      "fasce_km": [[a, None if b > 500 else b] for a, b in FASCE_KM],
                      "auto": "media delle due auto di riferimento (Golf VIII 115 CV a benzina e a gasolio)",
                      "sosta": "tariffa ordinaria (ZTL centrale non nel calcolo)", "prova": bool(args.prova)},
           "prezzi": {"benzina_self_eur_l": pb, "gasolio_self_eur_l": pg,
                      "consumo_urbano_benzina": costi["auto"]["benzina"]["consumo_urbano_l_100km"], "consumo_urbano_gasolio": costi["auto"]["gasolio"]["consumo_urbano_l_100km"],
                      "aci_benzina_eur_km": costi["auto"]["benzina"]["costo_pieno_eur_km"], "aci_gasolio_eur_km": costi["auto"]["gasolio"]["costo_pieno_eur_km"],
                      "biglietto_urbano": costi["gtt"]["biglietto_urbano_eur"], "abbonamento_mensile": costi["gtt"]["abbonamento_mensile_urbano_eur"],
                      "sosta_ordinaria_ora": costi["sosta"]["tariffe_eur_ora"]["ordinaria"], "sosta_ztl_ora": costi["sosta"]["tariffe_eur_ora"]["ztl_centrale"]},
           "riepilogo": riepilogo, "punti": arrotonda(punti), "interscambi": arrotonda(inter), "fasce_distanza": fasce,
           "controlli": c.righe}
    out_json = OUT_JSON.with_name("costo_del_viaggio_prova.json") if args.prova else OUT_JSON
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    righe = ["QUANTO COSTA MUOVERSI (script 103) - prezzi consultati il " + costi["consultato"], "",
             f"Lavoro in centro, al mese, mediana dei {len(punti)} punti del R6 (km mediano {riepilogo['km_mediano_punti']}):",
             f"  auto che si sente {riepilogo['auto_mese_sente_mediana']} euro, auto piena {riepilogo['auto_mese_pieno_mediana']} euro, mezzi {riepilogo['mezzi_mese']} euro",
             f"  differenza che si sente {riepilogo['differenza_mese_sente_mediana']} euro, differenza piena {riepilogo['differenza_mese_pieno_mediana']} euro; minuti in piu' coi mezzi {riepilogo['minuti_in_piu_mediana']}",
             f"Commissione (2 ore in centro): auto che si sente {riepilogo['commissione_auto_sente_mediana']}, auto piena {riepilogo['commissione_auto_piena_mediana']}, mezzi {riepilogo['commissione_mezzi']} euro", "",
             "PUNTI E INTERSCAMBI (km, minuti in piu' coi mezzi, auto che si sente al mese, auto piena al mese, mezzi al mese)"]
    for l in punti + inter:
        righe.append(f"  {l['nome']}: {l['km']:.1f} km, {l['minuti_in_piu_coi_mezzi']} min, {l['lavoro_mese']['auto_sente']:.0f} / {l['lavoro_mese']['auto_piena']:.0f} / {l['lavoro_mese']['mezzi']:.0f} euro")
    righe += ["", "COPPIE TORINO-TORINO per fascia di distanza (lavoro al mese, senza sosta; mediana)"]
    for f in fasce:
        righe.append(f"  {f['da_km']}-{f['a_km']} km: {f['coppie']} coppie, auto che si sente {f['auto_sente_mese']}, piena {f['auto_piena_mese']}, mezzi {f['mezzi_mese']}")
    righe += ["", "CONTROLLI"] + c.righe
    rapporto = RAPPORTO.with_name("RAPPORTO_COSTO_DEL_VIAGGIO_prova.txt") if args.prova else RAPPORTO
    rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe[:12]))
    print("avvisi:", len(c.avvisi()))


if __name__ == "__main__":
    main()
