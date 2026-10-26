# -*- coding: utf-8 -*-
"""
scripts/65_affidabilita.py - Pacchetto F (Fase 5): affidabilita', universo, fasce.

Universo di analisi (regole FISSATE nel piano): tratte di asse nel comune di
Torino, rango >= 3 (secondary e superiori), lunghezza >= 300 m, escluse
autostrade/tangenziali/raccordi e le strutture (ponte/sottopasso/cavalcavia)
indipendenti. Prima cintura: tabella separata.

affidabile: false se (a) entro 1,5 km da una porta di bordo; (b) rango <= 2 con
flusso > 12.000 senza sensore; (c) struttura; (d) flusso > 100% dalla mediana
delle tratte dello stesso asse.

Fasce: fascia_50 = errore mediano leave-one-out della variante finale;
fascia_90 = 90esimo percentile. Fuori dall'intervallo validato [0,7 x min, 1,3 x
max dei sensori] la stima e' un'estrapolazione e la fascia si allarga x2.

Output: data/processed/traffico_d/tratte_traffico.json
        docs/rapporti/RAPPORTO_AFFIDABILITA.txt
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rete_osm  # noqa: E402

PROC = AQUI.parent / "data" / "processed"
OUT = PROC / "traffico_d"
RETE_DIR = OUT / "rete"
RAPPORTO = AQUI.parent / "docs" / "rapporti" / "RAPPORTO_AFFIDABILITA.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

CINTURA = {"Beinasco", "Borgaro Torinese", "Collegno", "Druento", "Grugliasco", "Moncalieri",
           "Nichelino", "Orbassano", "Pecetto Torinese", "Pino Torinese", "San Mauro Torinese",
           "Settimo Torinese", "Venaria Reale"}
STRUTTURA = re.compile(r"ponte|sottopasso|cavalcavia|viadotto|galleria|tunnel|rotatoria", re.I)
AUTOSTRADA = re.compile(r"autostrada|tangenziale|raccordo|asse di penetrazione", re.I)


def main():
    val = json.loads((OUT / "valutazione_fase5.json").read_text(encoding="utf-8"))
    finale = val["variante_finale"]
    classe = val["classe_esito"]
    fascia_50 = val["errore_mediano"]
    fascia_90 = None
    # fascia_90 = 90esimo percentile degli errori leave-one-out finali
    # lo ricaviamo dai sensori della variante finale
    sens = json.loads((OUT / finale / "sensori.json").read_text(encoding="utf-8"))["sensori"]
    unita = [s for s in sens if s.get("modello_2v") is not None]
    mis = np.array([u["misurato"] for u in unita], float)
    mod = np.array([u["modello_2v"] for u in unita], float)
    pred = np.zeros(len(unita))
    for i in range(len(unita)):
        altri = [j for j in range(len(unita)) if j != i]
        pred[i] = mod[i] * (mis[altri].sum() / mod[altri].sum())
    err = np.abs(pred - mis) / mis
    fascia_90 = float(np.percentile(err, 90))
    k = float(mis.sum() / mod.sum())

    tratte = json.loads((OUT / "tratte.json").read_text(encoding="utf-8"))["tratte"]
    tratte_by_id = {t["id"]: t for t in tratte}
    flusso = json.loads((OUT / finale / "tratte_flusso.json").read_text(encoding="utf-8"))["tratte"]
    flusso_per_id = {t["id"]: t["veic_giorno_2v"] for t in flusso}

    ztl = {}
    with (OUT / "tratte_ztl.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            ztl[int(r["id_tratta"])] = r
    tp = {}
    with (OUT / "tp_tratte.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            tp[int(r["id_tratta"])] = r

    rete = rete_osm.carica(RETE_DIR)
    xy = rete["nodi_xy"]
    n_edge = len(rete["edge_a"])
    # punteggio di importanza (script 24) mappato sui tratti via segmenti.csv della Fase 3,
    # piu' un valore di base dalla classe OSM. L'universo usa ">= 3" come da piano.
    imp = {c["nome"]: c["punteggio"]
           for c in json.loads((PROC / "importanza_vie.json").read_text(encoding="utf-8"))["corridoi"]}
    seg_nome = {}
    with (PROC / "traffico_c" / "segmenti.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            seg_nome[int(r["id_tratto"])] = r["corridoio"]
    PUNT_CLASSE = {"motorway": 5, "trunk": 5, "motorway_link": 5, "trunk_link": 5,
                   "primary": 4, "primary_link": 4, "secondary": 3, "secondary_link": 3}
    edge_punt = np.array([imp.get(seg_nome.get(e, ""), PUNT_CLASSE.get(rete["meta"]["highway"][e], 1))
                          for e in range(n_edge)], dtype=np.int64)
    porte = [(float(xy[n][0]), float(xy[n][1]))
             for n in {p["nodo"] for p in json.loads(
                 (PROC / "traffico_c" / "v3" / "porte_v3.json").read_text(encoding="utf-8"))["porte"]}]

    # sensori -> tratta piu' vicina
    sens_v2 = json.loads((PROC / "sensori_corridoi_v2.json").read_text(encoding="utf-8"))["sensori"]
    ab = json.loads((PROC / "traffico_stimato_AB.json").read_text(encoding="utf-8"))
    et = np.load(OUT / "assi_tratte.npz")["edge_tratta"]
    per_tratta_edges = defaultdict(list)
    for e in range(n_edge):
        t = int(et[e])
        if t >= 0:
            per_tratta_edges[t].append(e)
    punt_tratta = {tid: int(max(edge_punt[e] for e in es)) for tid, es in per_tratta_edges.items()}
    medi = rete_osm.punti_medi(rete)
    misurato_per_tratta = {}
    asse_con_sensore = set()
    for u in ab["unita"]:
        lcd = u["lcd1"][0]
        pos = sens_v2.get(lcd)
        if not pos:
            continue
        d, e = rete_osm.tratto_piu_vicino(rete, pos["lat"], pos["lon"], medi)
        if e is None:
            continue
        tid = int(et[e])
        if tid < 0:
            continue
        misurato_per_tratta[tid] = {"lcd1": u["lcd1"], "valore": u["f_diurno_totale"],
                                    "dist_m": round(d, 1)}
        asse_con_sensore.add(tratte_by_id[tid]["asse"])

    # intervallo validato in spazio "misurato" (piano F)
    lim_inf = 0.7 * float(mis.min()); lim_sup = 1.3 * float(mis.max())

    # flusso per tratta e mediana per asse
    per_asse = defaultdict(list)
    meta_tratta = {}
    for t in tratte:
        per_asse[t["asse"]].append(t["id"])
        meta_tratta[t["id"]] = t

    # vicini consecutivi di ogni tratta dentro la stessa catena
    per_catena = defaultdict(list)
    for t in tratte:
        per_catena[(t["asse"], t["catena"])].append(t["id"])
    vicini = {}
    for ids in per_catena.values():
        for kk, tid in enumerate(ids):
            v = []
            if kk > 0:
                v.append(ids[kk - 1])
            if kk + 1 < len(ids):
                v.append(ids[kk + 1])
            vicini[tid] = v

    def rango(t):
        return t["rango"]

    reg = []
    for t in tratte:
        tid = t["id"]
        veic = flusso_per_id.get(tid, 0.0)
        com = t["comune"]
        rt = t["rango"]
        motivi = []
        # (c) struttura
        if STRUTTURA.search(t["nome_principale"] or ""):
            motivi.append("struttura (ponte/sottopasso/ecc.)")
        # (a) bordo: entro 1,5 km da una porta
        # geometria non e' in tratte.json: usa il centroide approssimato dai WKT? usiamo
        # le coordinate del secondo punto del nome via rete
        # qui calcoliamo dal centroide ricavato in fase di creazione se disponibile
        # (fallback: nessun flag bordo)
        # (b) rango <=2 con flusso > 12000 senza sensore
        if rt <= 2 and veic > 12000 and tid not in misurato_per_tratta:
            motivi.append("rango<=2 con flusso > 12.000 senza sensore")
        # (d) "salto" rispetto alle TRATTE CONSECUTIVE dello stesso asse/catena
        # (scostamento > 100% dalla media dei vicini), implementato sui vicini
        # della catena: le tratte sono gia' tagliate ai grandi incroci.
        vic = vicini.get(tid, [])
        if len(vic) >= 1 and veic > 0:
            mv = float(np.mean([flusso_per_id.get(i, 0.0) for i in vic]))
            if mv > 500 and abs(veic - mv) > mv:
                motivi.append("flusso oltre 100% dalla media delle tratte consecutive")
        reg.append({"id": tid, "asse": t["asse"], "nome": t["nome_principale"],
                    "nomi": t.get("nomi", []),
                    "comune": com, "quartiere": t["quartiere"], "rango": rt,
                    "punteggio": punt_tratta.get(tid, 1),
                    "classe": t["classe"], "lunghezza_m": t["lunghezza_m"],
                    "corsie_totali": t["corsie_totali"],
                    "veic_giorno": round(veic, 1), "motivi": motivi})

    # flag bordo: calcolato con la geometria dal file tratte.csv
    from_mappa = {}
    with (OUT / "tratte.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            inner = r["geom_wkt"][r["geom_wkt"].find("(") + 1:r["geom_wkt"].rfind(")")]
            coppie = inner.split(",")
            x, y = coppie[len(coppie) // 2].split()
            from_mappa[int(r["id_tratta"])] = (float(y), float(x))
    for o in reg:
        c = from_mappa.get(o["id"])
        if c:
            dmin = min((rete_osm.haversine_m(c[0], c[1], la, lo) for la, lo in porte), default=1e9)
            if dmin <= 1500:
                o["motivi"].append(f"bordo (porta a {dmin:.0f} m)")
            o["dist_porta_m"] = round(dmin)

    # misura da sensore
    for o in reg:
        m = misurato_per_tratta.get(o["id"])
        if m:
            o["veic_giorno"] = float(m["valore"])
            o["misurato"] = True
            o["sensore"] = m["lcd1"]
            o["dist_sensore_m"] = m["dist_m"]
            o["motivi"] = [x for x in o["motivi"] if not x.startswith("flusso oltre")]
        else:
            o["misurato"] = False
        v = o["veic_giorno"]
        o["estrapolazione"] = bool(v < lim_inf or v > lim_sup)
        f50 = fascia_50 * (2.0 if o["estrapolazione"] else 1.0)
        f90 = fascia_90 * (2.0 if o["estrapolazione"] else 1.0)
        o["fascia_50"] = round(f50, 4); o["fascia_90"] = round(f90, 4)
        o["affidabile"] = (len(o["motivi"]) == 0)
        o["asse_con_sensore"] = o["asse"] in asse_con_sensore
        # fiducia
        if o["misurato"]:
            o["fiducia"] = "alta"
        elif o["affidabile"] and rt >= 3 and not o["estrapolazione"]:
            o["fiducia"] = "media"
        else:
            o["fiducia"] = "bassa"
        o["classe_esito"] = classe
        o["veic_per_corsia"] = round(v / max(o["corsie_totali"], 1e-9), 1)
        # TP
        t = tp.get(o["id"], {})
        o["copertura_300"] = float(t.get("copertura_300", 0) or 0)
        o["copertura_con_metro"] = float(t.get("copertura_con_metro", 0) or 0)
        o["freq_max_300"] = float(t.get("freq_max_300", 0) or 0)
        o["n_linee_300"] = int(t.get("n_linee_300", 0) or 0)
        o["metro_600"] = bool(int(t.get("metro_600", 0) or 0))
        o["ferrovia_600"] = bool(int(t.get("ferrovia_600", 0) or 0))
        z = ztl.get(o["id"], {})
        o["ztl_frazione"] = float(z.get("ztl_frazione", 0) or 0)
        o["pedonale_frazione"] = float(z.get("pedonale_frazione", 0) or 0)

    # universo
    def autostrada(o):
        return o["rango"] >= 5 or bool(AUTOSTRADA.search(o["nome"] or "")) or \
            o["classe"] in ("motorway", "trunk", "motorway_link", "trunk_link")

    def in_universo(o, comuni):
        return (o["comune"] in comuni and o["punteggio"] >= 3 and o["lunghezza_m"] >= 300
                and not autostrada(o) and o["affidabile"] and o["veic_giorno"] > 0)

    torino = [o for o in reg if in_universo(o, {"Torino"})]
    cintura = [o for o in reg if in_universo(o, CINTURA)]

    # regole F punto 2: conteggi
    def conta(motivo_inizio):
        sel = [o for o in reg if any(m.startswith(motivo_inizio) for m in o["motivi"])]
        return len(sel), round(sum(o["lunghezza_m"] for o in sel) / 1000, 1)

    doc = {
        "stimato": True, "variante_finale": finale, "classe_esito": classe,
        "taratura": {"k": round(k, 4), "fascia_50": round(fascia_50, 4),
                     "fascia_90": round(fascia_90, 4),
                     "intervallo_validato_measured": [round(lim_inf, 1), round(lim_sup, 1)]},
        "universo_torino": {"n": len(torino),
                            "km": round(sum(o["lunghezza_m"] for o in torino) / 1000, 1)},
        "universo_cintura": {"n": len(cintura),
                             "km": round(sum(o["lunghezza_m"] for o in cintura) / 1000, 1)},
        "conteggi_regole": {
            "bordo": conta("bordo"), "struttura": conta("struttura"),
            "rango2_flusso": conta("rango<=2"), "salto_asse": conta("flusso oltre")},
        "tratte": reg,
    }
    (OUT / "tratte_traffico.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    righe = []
    def a_(s=""):
        righe.append(s)
    a_("AFFIDABILITA', UNIVERSO E FASCE (pacchetto F, Fase 5)")
    a_("=" * 76)
    a_(f"variante finale: {finale}   classe di esito: {classe}")
    a_(f"taratura k = {k:.4f}   fascia 50% = +-{100*fascia_50:.0f}%   "
       f"fascia 90% = +-{100*fascia_90:.0f}%")
    a_(f"intervallo validato (misurato): [{lim_inf:,.0f}, {lim_sup:,.0f}] veic/giorno; "
       f"fuori: estrapolazione con fascia x2")
    a_("")
    a_("UNIVERSO DI TORINO: {n} tratte, {km} km".format(**doc["universo_torino"]))
    a_("PRIMA CINTURA: {n} tratte, {km} km".format(**doc["universo_cintura"]))
    a_("")
    a_("== Regole di inaffidabilita' (quante tratte e km) ==")
    for k2, (n2, km2) in doc["conteggi_regole"].items():
        a_(f"  {k2:16s}: {n2:6d} tratte  {km2:8.1f} km")
    a_("")
    a_("== Prime 20 tratte per flusso (universo + non) ==")
    for o in sorted(reg, key=lambda o: -o["veic_giorno"])[:20]:
        a_(f"  {o['veic_giorno']:9,.0f} +-{100*o['fascia_50']:2.0f}%  {str(o['nome'])[:34]:34s} "
           f"{o['comune'] or '':12s} affidabile={o['affidabile']} "
           f"{' / '.join(m[:26] for m in o['motivi'])}")
    a_("")
    a_("== Tratte citate dal piano (Via Palestrina, Corso Monte Lungo, Via Quarto dei Mille) ==")
    for chiave in ["palestrina", "monte lungo", "quarto dei mille"]:
        voci = [o for o in reg if chiave in (o["nome"] or "").lower()]
        for o in voci[:4]:
            a_(f"  {chiave:16s}: {o['veic_giorno']:9,.0f} veic/g  affidabile={o['affidabile']}  "
               f"motivi {' / '.join(o['motivi']) or '-'}")
        if not voci:
            a_(f"  {chiave:16s}: nessuna tratta (fuori universo o esclusa)")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
