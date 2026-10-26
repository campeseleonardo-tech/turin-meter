# -*- coding: utf-8 -*-
"""
scripts/43_segmenti_corridoi.py - Pacchetto E del piano Fase 3.

Prende il flusso del modello su ogni tratto (archi_flusso.npz) e lo riporta:
 1. ai TRATTI (un record per tratto OSM fra due incroci): flusso diurno 6-21
    nei due versi, giorno intero, e le fasce 7-8, 8-9, 17-18, 18-19;
 2. ai CORRIDOI di importanza_vie.json (nome via + tratti collegati): flusso
    medio pesato per lunghezza, minimo, massimo, e il flusso del tratto piu'
    vicino al sensore.

Il campo "componenti" di un corridoio non contiene gli id dei way OSM (contiene
solo dei contatori), quindi il collegamento tratto -> corridoio si fa con il
NOME normalizzato della via (come lo script 24) e, solo se il nome non basta,
con la vicinanza (<= 25 m). Scelta dichiarata.

Controlli: conservazione del flusso nei nodi (ingresso = uscita, errore < 1%),
nessun flusso negativo, corridoi senza flusso elencati con il motivo.

Output:
  data/processed/traffico_c/segmenti.csv
  data/processed/traffico_c/corridoi_modello.json
  docs/rapporti/RAPPORTO_TRAFFICO_C_SEGMENTI.txt
"""

import csv
import json
import math
import sys
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
PROC = RADICE / "data" / "processed"
OUT_DIR = PROC / "traffico_c"
RETE_DIR = OUT_DIR / "rete"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_TRAFFICO_C_SEGMENTI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

# soglia di vicinanza tratto <-> corridoio quando il nome non basta
VICINANZA_M = 25.0
CELLA_LAT, CELLA_LON = 0.0009, 0.0013


def normalizza(nome):
    from importlib import import_module
    return import_module("24_importanza_vie").normalizza(nome)


def carica_corridoi():
    dati = json.loads((PROC / "importanza_vie.json").read_text(encoding="utf-8"))
    corridoi = dati["corridoi"]
    per_chiave = defaultdict(list)
    griglia = defaultdict(set)
    for i, c in enumerate(corridoi):
        per_chiave[c["chiave_normalizzata"]].append(i)
        for tratto in c["geometria"]:
            for k in range(len(tratto) - 1):
                (la0, lo0), (la1, lo1) = tratto[k], tratto[k + 1]
                passi = max(1, int(max(abs(la1 - la0) / CELLA_LAT, abs(lo1 - lo0) / CELLA_LON) * 4))
                for t in range(passi + 1):
                    la = la0 + (la1 - la0) * t / passi
                    lo = lo0 + (lo1 - lo0) * t / passi
                    griglia[(math.floor(la / CELLA_LAT), math.floor(lo / CELLA_LON))].add(i)
    return corridoi, per_chiave, griglia


def main():
    rete = rete_osm.carica(RETE_DIR)
    xy = rete["nodi_xy"]
    meta = rete["meta"]
    edge_a = rete["edge_a"]
    edge_len = rete["edge_len"]
    archi = rete["archi"]
    n_edge = len(edge_a)

    z = np.load(OUT_DIR / "archi_flusso.npz")
    flusso_dir = z["flusso_dir"]                     # giorno intero, per arco orientato
    flusso_diurno = z["flusso_diurno_dir"]
    domanda = json.loads((OUT_DIR / "domanda_auto.json").read_text(encoding="utf-8"))
    quote = domanda["quote_orarie"]
    fasce = {
        "7_8": quote["7"], "8_9": quote["8"], "17_18": quote["17"], "18_19": quote["18"],
    }

    # --- controlli sui flussi ---
    negativo = int((flusso_dir < 0).sum())
    n_nodi = len(xy)
    # per ogni nodo: somma archi entranti - uscenti
    src = archi[:, 0].astype(np.int64)
    dst = archi[:, 1].astype(np.int64)
    entr = np.bincount(dst, weights=flusso_dir, minlength=n_nodi)
    usc = np.bincount(src, weights=flusso_dir, minlength=n_nodi)
    bilancio = entr - usc
    uscita_tot = float(flusso_dir.sum())
    # nodi con |bilancio| > 1% del flusso medio uscente
    soglia = 0.01 * (uscita_tot / max(n_nodi, 1))
    nodi_sbilanciati = int((np.abs(bilancio) > max(soglia, 1e-3)).sum())
    perc_sbilanciati = 100.0 * nodi_sbilanciati / n_nodi

    # --- da archi a tratti (due versi) ---
    ind = archi[:, 3].astype(np.int64)
    verso = archi[:, 4].astype(np.int64)
    f_ab = np.zeros(n_edge); f_ba = np.zeros(n_edge)
    np.add.at(f_ab, ind[verso == 0], flusso_diurno[verso == 0])
    np.add.at(f_ba, ind[verso == 1], flusso_diurno[verso == 1])
    f_ab_g = np.zeros(n_edge); f_ba_g = np.zeros(n_edge)
    np.add.at(f_ab_g, ind[verso == 0], flusso_dir[verso == 0])
    np.add.at(f_ba_g, ind[verso == 1], flusso_dir[verso == 1])
    f_tot = f_ab + f_ba
    f_tot_g = f_ab_g + f_ba_g
    veicoli_km_diurno = float((f_tot * edge_len).sum() / 1000.0)

    # --- corridoi ---
    corridoi, per_chiave, griglia = carica_corridoi()
    print(f"corridoi: {len(corridoi):,}; celle di griglia: {len(griglia):,}")
    nome_edge = [normalizza(meta["nomi"][e]) if meta["nomi"][e] else "" for e in range(n_edge)]

    # punto medio di ogni tratto
    medi = np.array([rete_osm.punto_medio(rete, e) for e in range(n_edge)])

    def distanza_a_corridoio(i, la, lo):
        best = 1e18
        for tratto in corridoi[i]["geometria"]:
            for k in range(len(tratto) - 1):
                la1, lo1 = tratto[k]
                la2, lo2 = tratto[k + 1]
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

    assegna = [None] * n_edge
    metodo = [""] * n_edge
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
                    d = distanza_a_corridoio(i, la, lo)
                    if d < best[0]:
                        best = (d, i)
                if best[0] <= 200:
                    scelto = best[1]
        if scelto is not None:
            assegna[e] = scelto
            metodo[e] = "nome"
            continue
        # fallback: vicinanza <= 25 m
        ci, cj = math.floor(la / CELLA_LAT), math.floor(lo / CELLA_LON)
        vicini = set()
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                vicini |= griglia.get((ci + di, cj + dj), set())
        best = (1e18, None)
        for i in vicini:
            d = distanza_a_corridoio(i, la, lo)
            if d < best[0]:
                best = (d, i)
        if best[1] is not None and best[0] <= VICINANZA_M:
            assegna[e] = best[1]
            metodo[e] = "vicinanza"

    # --- segmenti.csv ---
    with (OUT_DIR / "segmenti.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["id_tratto", "corridoio", "nome_osm", "highway", "lunghezza_m",
                    "flusso_diurno_AB", "flusso_diurno_BA", "flusso_diurno_tot",
                    "flusso_giorno_tot", "h7_8", "h8_9", "h17_18", "h18_19", "stimato"])
        for e in range(n_edge):
            c = assegna[e]
            nome_cor = corridoi[c]["nome"] if c is not None else ""
            w.writerow([e, nome_cor, meta["nomi"][e] or "", meta["highway"][e],
                        round(float(edge_len[e]), 1),
                        round(float(f_ab[e]), 2), round(float(f_ba[e]), 2), round(float(f_tot[e]), 2),
                        round(float(f_tot_g[e]), 2),
                        round(float(f_tot[e] * fasce["7_8"]), 2), round(float(f_tot[e] * fasce["8_9"]), 2),
                        round(float(f_tot[e] * fasce["17_18"]), 2), round(float(f_tot[e] * fasce["18_19"]), 2),
                        "true"])

    # --- corridoi_modello.json ---
    per_corridoio = defaultdict(list)
    for e in range(n_edge):
        if assegna[e] is not None:
            per_corridoio[assegna[e]].append(e)

    # sensori: tratto piu' vicino al sensore (per il confronto del pacchetto F)
    medi = None
    info_sensori = []

    out = []
    senza_flusso = 0
    for i, c in enumerate(corridoi):
        edge_ids = per_corridoio.get(i, [])
        if not edge_ids:
            out.append({"nome": c["nome"], "chiave": c["chiave_normalizzata"],
                        "punteggio": c["punteggio"], "lunghezza_km": c["lunghezza_km"],
                        "n_tratti": 0, "senza_flusso": True,
                        "motivo": "nessun tratto della rete in auto abbinato (strada pedonale, "
                                  "o nome non presente nella rete OSM caricata)",
                        "stimato": True})
            senza_flusso += 1
            continue
        lung = edge_len[edge_ids]
        fl = f_tot[edge_ids]
        medio = float((fl * lung).sum() / max(lung.sum(), 1e-9))
        out.append({
            "nome": c["nome"], "chiave": c["chiave_normalizzata"],
            "comune": c.get("comune"), "punteggio": c["punteggio"],
            "lunghezza_km": c["lunghezza_km"], "n_tratti": len(edge_ids),
            "km_tratti_modello": round(float(lung.sum() / 1000), 3),
            "flusso_diurno_medio": round(medio, 1),
            "flusso_diurno_min": round(float(fl.min()), 1),
            "flusso_diurno_max": round(float(fl.max()), 1),
            "flusso_diurno_totale_su_tratti": round(float(fl.sum()), 1),
            "stimato": True,
        })

    # sensori: tratto piu' vicino al sensore (serve al confronto del pacchetto F)
    medi = rete_osm.punti_medi(rete)
    sensori_v2 = json.loads((PROC / "sensori_corridoi_v2.json").read_text(encoding="utf-8"))["sensori"]
    ab = json.loads((PROC / "traffico_stimato_AB.json").read_text(encoding="utf-8"))
    idx_nome = {o["nome"]: k for k, o in enumerate(out)}
    for u in ab["unita"]:
        lcd = u["lcd1"][0]
        pos = sensori_v2.get(lcd)
        if not pos:
            continue
        d, e = rete_osm.tratto_piu_vicino(rete, pos["lat"], pos["lon"], medi)
        fl = float(f_tot[e]) if e is not None else None
        info_sensori.append({
            "lcd1": u["lcd1"], "via": pos["via"], "lat": pos["lat"], "lon": pos["lon"],
            "dist_sensore_tratto_m": None if e is None else round(d, 1),
            "flusso_diurno_modello_sul_tratto": None if fl is None else round(fl, 1),
            "corridoio": u["corridoio"]["nome"],
            "misurato_diurno_2versi": u["f_diurno_totale"]})
        k = idx_nome.get(u["corridoio"]["nome"])
        if k is not None:
            out[k]["flusso_diurno_tratto_sensore"] = info_sensori[-1]["flusso_diurno_modello_sul_tratto"]
            out[k]["dist_sensore_tratto_m"] = info_sensori[-1]["dist_sensore_tratto_m"]

    (OUT_DIR / "corridoi_modello.json").write_text(json.dumps({
        "stimato": True,
        "nota": ("Flusso diurno 6-21 a due versi (veicoli/giorno) del modello V0, "
                 "prima della taratura sui sensori (pacchetto F)."),
        "corridoi": out,
        "sensori": info_sensori,
    }, ensure_ascii=False), encoding="utf-8")

    # --- rapporto ---
    righe = []
    a = righe.append
    a("RAPPORTO TRATTI E CORRIDOI (pacchetto E, metodo C)")
    a("=" * 70)
    a(f"  tratti totali: {n_edge:,}")
    a(f"  tratti assegnati a un corridoio per nome: {sum(1 for m in metodo if m=='nome'):,}")
    a(f"  tratti assegnati per vicinanza (<=25 m): {sum(1 for m in metodo if m=='vicinanza'):,}")
    a(f"  tratti senza corridoio: {sum(1 for m in metodo if not m):,} (strade senza nome o nole)")
    a(f"  corridoi con almeno un tratto: {len(corridoi)-senza_flusso:,} su {len(corridoi):,}")
    a(f"  corridoi senza flusso: {senza_flusso:,}")
    a("")
    a("  CONTROLLI")
    a(f"   flussi negativi: {negativo}")
    a(f"   nodi con ingresso != uscita (oltre 1% del flusso medio): {nodi_sbilanciati:,} "
      f"({perc_sbilanciati:.2f}% dei {n_nodi:,} nodi)")
    a(f"   veicoli-km diurni (6-21) del modello: {veicoli_km_diurno:,.0f}")
    a("")
    a("  20 corridoi con piu' veicoli-km diurni (modello grezzo):")
    for c in sorted([o for o in out if o.get("n_tratti")], 
                    key=lambda o: -o["flusso_diurno_medio"] * o["km_tratti_modello"])[:20]:
        a(f"    {c['flusso_diurno_medio']:9,.0f} veic/g  {c['nome'][:45]:45s} "
          f"punteggio {c['punteggio']}  {c['km_tratti_modello']:6.1f} km  max {c['flusso_diurno_max']:,.0f}")
    a("")
    a("  Sensori (unita' di confronto) - modello grezzo sul tratto piu' vicino:")
    for s in info_sensori:
        m = s["flusso_diurno_modello_sul_tratto"]
        a(f"    {str(s['lcd1'][0]):>6}  {s['via'][:34]:34s}  modello "
          f"{'n/d' if m is None else format(m, ',.0f'):>10}   misurato "
          f"{s['misurato_diurno_2versi']:>10,}   tratto a {s['dist_sensore_tratto_m']} m")
    a("")
    a("  20 corridoi di Torino (chiave quartiere) con piu' traffico diurno medio:")
    tor = [o for o in out if o.get("n_tratti") and (o.get("comune") == "Torino")]
    for c in sorted(tor, key=lambda o: -o["flusso_diurno_medio"])[:20]:
        a(f"    {c['flusso_diurno_medio']:9,.0f} veic/g  {c['nome'][:45]:45s} "
          f"punteggio {c['punteggio']}  {c['km_tratti_modello']:6.1f} km")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
