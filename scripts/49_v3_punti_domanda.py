# -*- coding: utf-8 -*-
"""
scripts/49_v3_punti_domanda.py - Pacchetto A (Fase 3-bis), parte 1: modello V3.

Costruisce gli ingredienti del modello piu' realistico V3 (fissato nel piano
sviluppo/note_tecniche/R8_traffico.md, non modificabile):
  1. DESTINAZIONI PER ATTRATTORI: ogni zona ha insiemi di punti pesati per
     gruppo di scopo (casa, lavoro, studio, acquisti, cure, altro). "casa" =
     popolazione (punti del modello V0); gli altri = punti di servizio
     geolocalizzati (catalogo comunale per Torino, servizi OSM per la cintura),
     agganciati al nodo stradale piu' vicino;
  2. la domanda viene ricostruita dalle catene di spostamenti (righe consecutive
     per persona e "uscita"), cosi' si sa se un viaggio parte da casa o da un
     altro posto (scopo del viaggio precedente);
  3. PORTE di rango alto (>= 3, cioe' almeno secondary): le zone esterne al
     taglio entrano da queste, con peso proporzionale alla capacita'.

V0 (modello attuale) resta intatto: questo script scrive solo nella cartella v3.

Output:
  data/processed/traffico_c/v3/punti_v3.json
  data/processed/traffico_c/v3/porte_v3.json
  data/processed/traffico_c/v3/domanda_v3.json
  docs/rapporti/RAPPORTO_TRAFFICO_C_V3.txt (intestazione)
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

RADICE = AQUI.parent
PROC = RADICE / "data" / "processed"
OUT_DIR = PROC / "traffico_c"
V3 = OUT_DIR / "v3"
RETE_DIR = OUT_DIR / "rete"
CATALOGO = PROC / "catalogo"
SPOSTAMENTI = PROC / "imq" / "spostamenti.csv"

LON_MIN, LAT_MIN, LON_MAX, LAT_MAX = 7.45, 44.90, 7.93, 45.24
CENTRO = (45.0703, 7.6869)
SEED = 20261017
MAX_NODI_GRUPPO = 8

# scopo IMQ -> gruppo
GRUPPO_SCOPO = {
    "08": "casa", "11": "casa",
    "01": "lavoro", "02": "lavoro",
    "06": "studio",
    "03": "acquisti",
    "05": "cure",
    "07": "altro", "04": "altro", "09": "altro", "10": "altro",
    "12": "altro", "13": "altro", "14": "altro", "15": "altro", "16": "altro",
}
GRUPPI = ["casa", "lavoro", "studio", "acquisti", "cure", "altro"]

# dataset del catalogo comunale per gruppo di attrattore
ATTRATTORI = {
    "lavoro": [("servizi", "sedi_amministrative"), ("servizi", "uffici_postali"),
               ("servizi", "uffici_anagrafici"), ("servizi", "uffici_turistici"),
               ("sicurezza_sport", "carabinieri"), ("sicurezza_sport", "guardia_finanza"),
               ("sicurezza_sport", "polizia_municipale"), ("sicurezza_sport", "protezione_civile"),
               ("sicurezza_sport", "questura"), ("sicurezza_sport", "vigili_fuoco"),
               ("commercio", "attivita")],
    "studio": [("istruzione", "scuole"), ("istruzione", "universita")],
    "acquisti": [("commercio", "attivita"), ("commercio", "mercati_tematici")],
    "cure": [("salute", "ospedali"), ("salute", "consultori"), ("salute", "farmacie"),
             ("salute", "socio_assistenziali")],
    "altro": [("sicurezza_sport", "impianti_sportivi"), ("commercio", "musei"),
              ("commercio", "biblioteche"), ("commercio", "cinema"), ("commercio", "luoghi")],
}
# servizi OSM della cintura per gruppo
OSM_GRUPPO = {"studio": ["scuole"], "cure": ["salute"], "acquisti": ["cibo"], "lavoro": ["cibo"]}
# capacita' di riferimento per le porte (veicoli/ora) -> peso relativo
CAP_RANGO = {5: 8000, 4: 4000, 3: 2500}


# ------------------------------------------------------------------ geometria
def anelli_di(g):
    if isinstance(g, str):
        g = json.loads(g)
    if not g:
        return []
    if isinstance(g[0][0], (int, float)):
        return [g]
    if isinstance(g[0][0][0], (int, float)):
        return g
    return [a for p in g for a in p]


def poligoni_zone():
    zone = json.loads((PROC / "imq_zone_geo.json").read_text(encoding="utf-8"))
    from shapely.geometry import Polygon, MultiPolygon  # noqa: F401
    from shapely.strtree import STRtree
    polys, cods = [], []
    for z in zone:
        anelli = anelli_di(z["g"])
        pp = []
        for an in anelli:
            if len(an) >= 4:
                p = Polygon(an)
                if not p.is_valid:
                    p = p.buffer(0)
                if p.area > 0:
                    pp.append(p)
        if pp:
            polys.append(MultiPolygon(pp) if len(pp) > 1 else pp[0])
            cods.append(z["cod"])
    return polys, cods, STRtree(polys)


class GrigliaNodi:
    def __init__(self, xy_utili, indici_utili, cella=0.0015):
        self.cella = cella
        self.xy = xy_utili
        self.ind = indici_utili
        self.g = defaultdict(list)
        for k, (la, lo) in enumerate(xy_utili):
            self.g[(math.floor(la / cella), math.floor(lo / cella))].append(k)

    def snap(self, la, lo, raggi=2):
        c = self.cella
        ci, cj = math.floor(la / c), math.floor(lo / c)
        best = (1e18, None)
        for di in range(-raggi, raggi + 1):
            for dj in range(-raggi, raggi + 1):
                for k in self.g.get((ci + di, cj + dj), ()):
                    d2 = (self.xy[k, 0] - la) ** 2 + (self.xy[k, 1] - lo) ** 2
                    if d2 < best[0]:
                        best = (d2, k)
        if best[1] is None:
            k = int(np.argmin((self.xy[:, 0] - la) ** 2 + (self.xy[:, 1] - lo) ** 2))
            return int(self.ind[k])
        return int(self.ind[best[1]])


def zone_utili(rete):
    """Nodi del nocciolo della rete (componente fortemente connessa piu' grande)."""
    xy = rete["nodi_xy"]
    N = len(xy)
    archi = rete["archi"]
    ai = archi[:, :2].astype(np.int64)
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    entrata = np.bincount(ai[:, 1], minlength=N)
    uscita = np.bincount(ai[:, 0], minlength=N)
    utili = (entrata > 0) & (uscita > 0)
    G = sp.csr_matrix((np.ones(len(ai)), (ai[:, 0], ai[:, 1])), shape=(N, N))
    _n, lab = connected_components(G, directed=True, connection="strong")
    grande = int(np.argmax(np.bincount(lab)))
    utili &= (lab == grande)
    ind = np.nonzero(utili)[0]
    return xy[utili], ind


def main():
    t_inizio = __import__("time").time()
    rete = rete_osm.carica(RETE_DIR)
    xy_utili, ind_utili = zone_utili(rete)
    print(f"nodi utili: {len(ind_utili):,}")
    griglia = GrigliaNodi(xy_utili, ind_utili)

    punti_v0 = json.loads((OUT_DIR / "punti.json").read_text(encoding="utf-8"))["zone"]

    # --- punti attrattori per zona e gruppo ---
    zpolys, zcods, ztree = poligoni_zone()
    from shapely.geometry import Point
    conteggi = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # zona -> gruppo -> nodo -> peso
    punti_non_assegnati = 0
    n_punti_attr = defaultdict(int)

    def aggiungi(gruppo, lat, lon, peso=1.0):
        nonlocal punti_non_assegnati
        j = ztree.query(Point(lat, lon))
        cod = None
        for ji in np.atleast_1d(j):
            if zpolys[ji].contains(Point(lat, lon)):
                cod = zcods[ji]
                break
        if cod is None:
            punti_non_assegnati += 1
            return
        nodo = griglia.snap(lat, lon)
        conteggi[cod][gruppo][nodo] += peso
        n_punti_attr[gruppo] += 1

    # catalogo comunale (Torino)
    for gruppo, fonti in ATTRATTORI.items():
        for file, dsid in fonti:
            d = json.loads((CATALOGO / f"{file}.json").read_text(encoding="utf-8"))
            for ds in d["dati"]:
                if ds["id"] != dsid:
                    continue
                for el in ds.get("elementi") or []:
                    if ds.get("tipo") == "punti" and isinstance(el, list) and len(el) >= 2:
                        lat, lon = el[0], el[1]
                        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                            aggiungi(gruppo, float(lat), float(lon))
    # servizi OSM della cintura
    osm = json.loads((PROC / "servizi_osm_cintura.json").read_text(encoding="utf-8"))["servizi"]
    for gruppo, chiavi in OSM_GRUPPO.items():
        for k in chiavi:
            for el in osm.get(k, []):
                aggiungi(gruppo, float(el["lat"]), float(el["lon"]))
    print(f"punti attrattori: {dict(n_punti_attr)}  non assegnati a una zona: {punti_non_assegnati:,}")

    # --- punti_v3.json ---
    zone_out = {}
    for cod, elenco_v0 in punti_v0.items():
        casa = [{"nodo": int(p["nodo"]), "peso": float(p["peso"]),
                 "lat": float(p["lat"]), "lon": float(p["lon"]),
                 "tipo": p.get("tipo", "sezione")} for p in elenco_v0]
        z = {"casa": casa}
        for gruppo in GRUPPI[1:]:
            d = conteggi.get(cod, {}).get(gruppo, {})
            if not d:
                z[gruppo] = []          # fallback a "casa" deciso in assegnazione
                continue
            voci = sorted(d.items(), key=lambda kv: -kv[1])[:MAX_NODI_GRUPPO]
            tot = sum(v for _, v in voci) or 1.0
            z[gruppo] = [{"nodo": int(n), "peso": round(v / tot, 8),
                          "lat": round(float(rete["nodi_xy"][n, 0]), 6),
                          "lon": round(float(rete["nodi_xy"][n, 1]), 6)} for n, v in voci]
        zone_out[cod] = z
    V3.mkdir(parents=True, exist_ok=True)
    (V3 / "punti_v3.json").write_text(json.dumps({
        "stimato": True,
        "nota": ("V3: punti per zona e gruppo di scopo. 'casa' = popolazione (come V0). "
                 "Altri gruppi = attrattori geolocalizzati (catalogo comunale Torino + OSM cintura). "
                 "Dove un gruppo non ha dati si usa 'casa' (fallback)."),
        "gruppi": GRUPPI, "max_nodi_gruppo": MAX_NODI_GRUPPO,
        "zone": zone_out,
    }, ensure_ascii=False), encoding="utf-8")
    con_attr = sum(1 for z in zone_out.values() if any(z[g] for g in GRUPPI[1:]))
    print(f"zone con almeno un gruppo di attrattori: {con_attr} su {len(zone_out)}")

    # --- porte V3 (solo rango >= 3), pesos per capacita' ---
    porte_v0 = json.loads((OUT_DIR / "porte.json").read_text(encoding="utf-8"))["porte"]
    porte = [p for p in porte_v0 if p["rango"] >= 3]
    print(f"porte rango>=3: {len(porte)} su {len(porte_v0)}")
    # sensori esterni utili (entro 5 km da una porta) - conteggio diagnostico
    sensori_v2 = json.loads((PROC / "sensori_corridoi_v2.json").read_text(encoding="utf-8"))["sensori"]
    n_sens_porte = 0
    for s in sensori_v2.values():
        for p in porte:
            if rete_osm.haversine_m(s["lat"], s["lon"], p["lat"], p["lon"]) <= 5000:
                n_sens_porte += 1
                break
    print(f"sensori esterni entro 5 km da una porta di rango>=3: {n_sens_porte}")

    # --- domanda V3 (catene di spostamenti) ---
    zone_ok = {z["cod"] for z in json.loads((PROC / "imq_zone.json").read_text(encoding="utf-8"))}
    celle = defaultdict(lambda: [0.0, 0])
    quote_ora = defaultdict(float)
    tot = 0.0
    n_catene = 0
    orig_da_casa = 0
    tot_viaggi = 0
    chiave_prev = None
    gruppo_prev = None
    with SPOSTAMENTI.open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            chiave = (r.get("LOTTO"), r.get("SESSO"), r.get("ATTIVITA"),
                      r.get("COD_CAMP"), r.get("COD_DIM"), r.get("PROGR_USC"))
            if chiave != chiave_prev:
                n_catene += 1
                gruppo_prev = None
                chiave_prev = chiave
            scopo = (r.get("SCOPO") or "").strip()
            gruppo = GRUPPO_SCOPO.get(scopo, "altro")
            mezzi = [(r.get(f"MEZZO{i}") or "").strip() for i in (1, 2, 3)]
            if "03" in mezzi:
                altri = [m for m in mezzi if m and m != "03" and m not in {"", "01", "16", "20", "26"}]
                if not altri:
                    par = (r.get("COD_PAR") or "").strip()
                    arr = (r.get("COD_ARR") or "").strip()
                    ora_s = (r.get("ORA_PAR") or "").strip()
                    try:
                        ora = int(ora_s.split(":")[0])
                    except Exception:
                        ora = None
                    if ora is not None and 0 <= ora <= 23:
                        peso = float((r.get("PESO") or "0").replace(",", ".") or 0)
                        og = "casa" if gruppo_prev is None or gruppo_prev == "casa" else gruppo_prev
                        if og == "casa":
                            orig_da_casa += 1
                        dg = gruppo if arr in zone_ok else "casa"
                        celle[(par, arr, ora, og, dg)][0] += peso
                        celle[(par, arr, ora, og, dg)][1] += 1
                        quote_ora[ora] += peso
                        tot += peso
                        tot_viaggi += 1
            gruppo_prev = gruppo
    quote = {str(h): (quote_ora.get(h, 0.0) / tot if tot else 0.0) for h in range(24)}
    celle_out = [[par, arr, ora, round(peso, 4), n, og, dg]
                 for (par, arr, ora, og, dg), (peso, n) in sorted(celle.items())]
    (V3 / "domanda_v3.json").write_text(json.dumps({
        "stimato": False,
        "fonte": "IMQ 2022, auto conducente, con origine/destinazione per gruppo di scopo",
        "nota": ("og = gruppo del posto da cui parte il viaggio (casa se inizio di un'uscita "
                 "o se il viaggio precedente era di ritorno a casa; altrimenti lo scopo del "
                 "viaggio precedente). dg = gruppo dello scopo del viaggio."),
        "totali": {"peso_auto_conducente": round(tot, 4), "n_viaggi": tot_viaggi,
                   "catene": n_catene, "origini_da_casa": orig_da_casa},
        "quote_orarie": quote,
        "celle": celle_out,
    }, ensure_ascii=False), encoding="utf-8")
    print(f"domanda: {tot:,.0f} viaggi/giorno, {tot_viaggi:,} righe, catene {n_catene:,}, "
          f"celle {len(celle_out):,}")

    # --- porte_v3.json ---
    (V3 / "porte_v3.json").write_text(json.dumps({
        "stimato": False,
        "nota": "Porte di rango >= 3 (secondary/primary/trunk/motorway). Peso proporzionale alla capacita'.",
        "cap_rango": CAP_RANGO,
        "sensori_entro_5km": n_sens_porte,
        "porte": porte,
    }, ensure_ascii=False), encoding="utf-8")
    print(f"Fatto in {__import__('time').time()-t_inizio:.0f} s")


if __name__ == "__main__":
    main()
