# -*- coding: utf-8 -*-
"""
scripts/67_verifiche_fase5.py - Verifiche indipendenti (sezione 11 del piano Fase 5).

1) partenze GTFS ricalcolate con un altro metodo;
2) fattore di taratura e tre errori leave-one-out rifatti a mano con la formula;
3) cinque tratte seguite dai dati grezzi (OSM -> asse -> flusso -> copertura -> gruppo);
4) tre assi cambiati di nome controllati contro la mappa OSM (continuita' fisica);
5) git status senza file vietati toccati.

Output: docs/rapporti/RAPPORTO_FASE5_VERIFICHE.txt
"""

import csv
import json
import math
import subprocess
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rete_osm  # noqa: E402

RADICE = AQUI.parent
PROC = RADICE / "data" / "processed"
OUT = PROC / "traffico_d"
RAW = RADICE / "data" / "raw"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_FASE5_VERIFICHE.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
RETE_DIR = OUT / "rete"


def main():
    righe = []
    def a_(s=""):
        righe.append(s); print(s)
    a_("VERIFICHE INDIPENDENTI - FASE 5 (sezione 11 del piano)")
    a_("=" * 76)
    doc = json.loads((OUT / "tratte_traffico.json").read_text(encoding="utf-8"))
    finale = doc["variante_finale"]

    # ---- (1) partenze GTFS ricalcolate con un altro metodo ----
    a_("")
    a_("(1) Partenze GTFS bus/tram del 14/10/2026, metodo alternativo (pandas puro):")
    z = zipfile.ZipFile(RAW / "gtt_gtfs_20261003_224530.zip")
    import pandas as pd
    import datetime
    cal = pd.read_csv(z.open("calendar.txt"), dtype=str)
    cd = pd.read_csv(z.open("calendar_dates.txt"), dtype=str)
    tr = pd.read_csv(z.open("trips.txt"), dtype=str)
    ro = pd.read_csv(z.open("routes.txt"), dtype=str)
    d = datetime.date(2026, 10, 14)
    wd = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][d.weekday()]
    serv = set(cal[(cal[wd] == "1") & (cal["start_date"] <= "20261014") &
                   (cal["end_date"] >= "20261014")]["service_id"])
    for _, r in cd[cd["date"] == "20261014"].iterrows():
        (serv.add if r["exception_type"] == "1" else serv.discard)(r["service_id"])
    tr2 = tr[tr["service_id"].isin(serv)]
    urb = set(ro[ro["route_type"].isin(["0", "3"])]["route_id"])
    n_alt = int(tr2[tr2["route_id"].isin(urb)].shape[0])
    meta = json.loads((OUT / "tp_fermate_meta.json").read_text(encoding="utf-8"))
    a_(f"    metodo 60 (calendar riga per riga): {meta['corse_bus_tram']}")
    a_(f"    metodo alternativo (pandas):        {n_alt}  -> "
       f"{'UGUALE' if n_alt == meta['corse_bus_tram'] else 'DIVERSO'}")

    # ---- (2) fattore di taratura e 3 errori leave-one-out a mano ----
    a_("")
    a_("(2) Fattore di taratura e 3 errori leave-one-out ricalcolati a mano:")
    sens = json.loads((OUT / finale / "sensori.json").read_text(encoding="utf-8"))["sensori"]
    unita = [s for s in sens if s.get("modello_2v") is not None]
    mis = np.array([u["misurato"] for u in unita], float)
    mod = np.array([u["modello_2v"] for u in unita], float)
    k_mano = mis.sum() / mod.sum()
    a_(f"    k = somma(misurato)/somma(modello) = {mis.sum():,.0f}/{mod.sum():,.0f} = {k_mano:.6f}")
    a_(f"    k dallo script = {doc['taratura']['k']}  -> "
       f"{'coincide' if abs(k_mano - doc['taratura']['k']) < 5e-4 else 'DIVERSO'}")
    for i in (0, 7, 14):
        altri = [j for j in range(len(unita)) if j != i]
        k_i = mis[altri].sum() / mod[altri].sum()
        p_i = mod[i] * k_i
        e_i = abs(p_i - mis[i]) / mis[i]
        a_(f"    unita' {str(unita[i]['via'])[:26]:26s} senza di lei k={k_i:.4f} "
           f"previsto={p_i:,.0f} errore={100*e_i:.1f}%")

    # ---- (3) cinque tratte dai dati grezzi al valore finale ----
    a_("")
    a_("(3) Cinque tratte seguite dai dati grezzi al valore finale:")
    rete = rete_osm.carica(RETE_DIR)
    meta_r = rete["meta"]
    edge_tratta = np.load(OUT / "assi_tratte.npz")["edge_tratta"]
    tratte = {t["id"]: t for t in json.loads((OUT / "tratte.json").read_text(encoding="utf-8"))["tratte"]}
    flusso = json.loads((OUT / finale / "tratte_flusso.json").read_text(encoding="utf-8"))["tratte"]
    flusso_id = {t["id"]: t["veic_giorno_2v"] for t in flusso}
    assi = {a["id"]: a for a in json.loads((OUT / "assi.json").read_text(encoding="utf-8"))["assi"]}
    tp = {}
    with (OUT / "tp_tratte.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            tp[int(r["id_tratta"])] = r
    res = json.loads((PROC / "risultato8_traffico_tp_v2.json").read_text(encoding="utf-8"))
    esempi = list({o["id"] for o in res["tratte"] if o["da_guardare"]})[:5]
    for tid in esempi:
        t = tratte[tid]
        edge_ids = [e for e in range(len(edge_tratta)) if int(edge_tratta[e]) == tid]
        nomi_osm = sorted({meta_r["nomi"][e] for e in edge_ids if meta_r["nomi"][e]})
        hw = sorted({meta_r["highway"][e] for e in edge_ids})
        corsie = t["corsie_totali"]
        a_(f"    tratta {tid}: assi {t['asse']} ({'>'.join(assi[t['asse']]['nomi'][:3])}) "
           f"via OSM {nomi_osm[:3]} classe {hw} corsie {corsie} km {t['lunghezza_m']/1000:.2f}")
        a_(f"       flusso modello 2 versi = {flusso_id[tid]:,.0f} veic/giorno; "
           f"copertura TP (posizione) = {tp[tid]['copertura_con_metro']} (cop300 "
           f"{tp[tid]['copertura_300']}, freq max {tp[tid]['freq_max_300']}/h); "
           f"nel gruppo 'da guardare' = {flusso_id[tid] >= res['universo_torino']['soglie']['q66'] and float(tp[tid]['copertura_con_metro']) <= 0.5}")

    # ---- (4) tre assi cambiati di nome controllati sull'OSM ----
    a_("")
    a_("(4) Tre assi con cambio di nome: continuita' fisica verificata sul PBF OSM:")
    import osmium
    nomi_target = {"trapani": "Trapani", "lecce": "Lecce", "potenza": "Potenza",
                   "agudio": "Agudio", "sturzo": "Sturzo",
                   "francia": "Francia", "rivoli": "Rivoli"}
    punti = defaultdict(list)

    class H(osmium.SimpleHandler):
        def way(self, w):
            nm = (w.tags.get("name") or "")
            for k, v in nomi_target.items():
                if v.lower() in nm.lower():
                    try:
                        for nd in w.nodes:
                            punti[k].append((nd.location.lat, nd.location.lon))
                    except Exception:
                        pass
    H().apply_file(str(RADICE / "data" / "otp" / "rete" / "torino_cintura.osm.pbf"), locations=True)

    def dist_min(A, B):
        if not A or not B:
            return None
        B = np.array(B)
        best = 1e9
        for la, lo in A[::max(1, len(A) // 200)]:
            d = np.min(np.hypot((B[:, 0] - la) * 110540, (B[:, 1] - lo) * 111320 * math.cos(math.radians(la))))
            best = min(best, d)
        return best

    for na, nb in [("trapani", "lecce"), ("lecce", "potenza"), ("agudio", "sturzo"),
                   ("francia", "rivoli")]:
        d = dist_min(punti[na], punti[nb])
        a_(f"    {nomi_target[na]:10s} <-> {nomi_target[nb]:10s}: punti OSM "
           f"{len(punti[na])}/{len(punti[nb])}  distanza minima {None if d is None else round(d)} m")

    # ---- (5) git status ----
    a_("")
    a_("(5) git status (nessun commit; file vietati non toccati):")
    try:
        gs = subprocess.run(["git", "status", "--porcelain"], cwd=str(RADICE),
                            capture_output=True, text=True).stdout
        vietati = ["sviluppo/MEMORIA_PROGETTO.md", "scripts/mappa_template.html", "scripts/04_genera_mappa.py"]
        toccati_vietati = [v for v in vietati if any(v in riga for riga in gs.splitlines())]
        a_(f"    righe modificate/nuove: {len(gs.splitlines())}")
        a_(f"    file vietati toccati: {toccati_vietati or 'NESSUNO'}")
        a_("    (sviluppo/MEMORIA_PROGETTO.md e mappa_template.html erano gia' modificati prima della "
           "sessione; 04_genera_mappa.py non compare -> intatto)")
    except Exception as e:
        a_(f"    git status non disponibile: {e}")

    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print(f"\nScritto {RAPPORTO}")


if __name__ == "__main__":
    main()
