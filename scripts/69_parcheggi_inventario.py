#!/usr/bin/env python3
"""
69_parcheggi_inventario.py  -  Risultato 6 v2, PASSO 2: inventario di TUTTI i parcheggi.

Cosa fa
-------
Mette in un unico elenco i parcheggi di quattro fonti:
  - 5T:  data/raw/5t_get_pk_20261014.xml (attributi ID, Name, Total, lat, lng)
  - Comune:  data/raw/parcheggi_accesso_controllato_csv.zip (coordinate Gauss-Boaga
    EPSG:3003, convertite in lat/lon con pyproj)
  - Fermi: interscambio ufficiale aggiunto a mano (e' nel 5T, non nel file del Comune)
  - OpenStreetMap: data/otp/rete/torino_cintura.osm.pbf (nodi e vie con
    amenity=parking; per le vie chiuse calcola centro e superficie in m2)
Non conta due volte lo stesso parcheggio: unisce le fonti quando sono lo stesso posto.
Assegna a ciascuno un tipo e, ai parcheggi OSM, posti dichiarati o stimati dalla
superficie (~25 m2 per posto).

Cosa legge
----------
  data/raw/5t_get_pk_20261014.xml
  data/raw/parcheggi_accesso_controllato_csv.zip
  data/otp/rete/torino_cintura.osm.pbf
  data/storico_backup.sqlite (solo per sapere chi trasmette il riempimento, sola lettura)

Cosa scrive
-----------
  data/processed/risultato6_v2/parcheggi.json
  docs/rapporti/RAPPORTO_R6V2_PARCHEGGI.txt

Come si lancia
--------------
  python scripts\\69_parcheggi_inventario.py
"""
import csv
import io
import json
import math
import sqlite3
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

import osmium
from pyproj import Transformer

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402  (PERIODO fisso dei dati)


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
XML_5T = RADICE / "data" / "raw" / "5t_get_pk_20261014.xml"
ZIP_COMUNE = RADICE / "data" / "raw" / "parcheggi_accesso_controllato_csv.zip"
CSV_COMUNE = "parcheggi_accesso_controllato.csv"
PBF = RADICE / "data" / "otp" / "rete" / "torino_cintura.osm.pbf"
DB = RADICE / "data" / "storico_backup.sqlite"
OUT = RADICE / "data" / "processed" / "risultato6_v2" / "parcheggi.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6V2_PARCHEGGI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

UFFICIALI = {"STURA", "CAIO MARIO", "SOFIA", "VENCHI UNICA", "FERMI"}  # 4 Comune + Fermi
RAGGIO_ABBINA_OSM_M = 60.0     # 5T/Comune vs OSM: entro 60 m dal centro
RAGGIO_ABBINA_NOME_M = 150.0   # 5T vs Comune: stesso nome e distanza < 150 m
MQ_PER_POSTO = 25.0
LAT_RIF = 45.07
FATTORE_GRADI_M = 111000.0
FERMI_LAT, FERMI_LON = 45.0766, 7.5903


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def normalizza(nome):
    return " ".join(nome.strip().upper().split())


def proietta(lon, lat):
    """Coordinate piane in metri (equirettangolare, come indicato nel piano)."""
    return (lon * FATTORE_GRADI_M * math.cos(math.radians(LAT_RIF)),
            lat * FATTORE_GRADI_M)


def superficie_laccio(punti):
    """Area in m2 di un anello chiuso, formula del laccio su coordinate proiettate."""
    xs = []
    ys = []
    for lon, lat in punti:
        x, y = proietta(lon, lat)
        xs.append(x)
        ys.append(y)
    area = 0.0
    n = len(xs)
    for i in range(n):
        j = (i + 1) % n
        area += xs[i] * ys[j] - xs[j] * ys[i]
    return abs(area) / 2.0


def dentro_poligono(lat, lon, anello):
    """Ray casting su anello di punti (lon, lat)."""
    n = len(anello)
    dentro = False
    j = n - 1
    for i in range(n):
        xi, yi = anello[i]
        xj, yj = anello[j]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
        ):
            dentro = not dentro
        j = i
    return dentro


# --- fonti -----------------------------------------------------------------------------

def carica_5t():
    radice = ET.parse(XML_5T).getroot()
    elenco = []
    for el in radice.iter():
        if el.tag.rsplit("}", 1)[-1] != "PK_data":
            continue
        a = el.attrib
        nome = a.get("Name", "").strip()
        if "CAMPER" in nome.upper():
            continue
        elenco.append({
            "nome": nome, "id_5t": a.get("ID"),
            "lat": float(a["lat"]), "lon": float(a["lng"]),
            "posti": int(a.get("Total") or 0) or None,
            "trasmette": "Free" in a,
        })
    return elenco


def carica_comune():
    with zipfile.ZipFile(ZIP_COMUNE) as zf, zf.open(CSV_COMUNE) as f:
        righe = list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"), delimiter=";"))
    tr = Transformer.from_crs("EPSG:3003", "EPSG:4326", always_xy=True)
    elenco = []
    for r in righe:
        try:
            x = float(r["COORD_X"].replace(",", "."))
            y = float(r["COORD_Y"].replace(",", "."))
        except (ValueError, KeyError):
            x = y = None
        lat = lon = None
        if x is not None:
            lon, lat = tr.transform(x, y)
        if lat is None and r.get("WKT_GEOM"):
            try:
                dentro = r["WKT_GEOM"][r["WKT_GEOM"].index("(") + 1:r["WKT_GEOM"].rindex(")")]
                px, py = [float(v) for v in dentro.split()]
                lon, lat = tr.transform(px, py)
            except (ValueError, IndexError):
                pass
        if lat is None:
            sys.exit(f"Coordinate non convertibili per il parcheggio del Comune "
                     f"'{r.get('DENOMINAZI')}' (ne COORD_X/COORD_Y ne WKT_GEOM).")
        def intero(v):
            try:
                return int(float(v))
            except (TypeError, ValueError):
                return None
        elenco.append({
            "nome": r.get("DENOMINAZI", "").strip(),
            "lat": lat, "lon": lon,
            "posti": intero(r.get("POSTI_TOT")),
            "interscambio": r.get("INTERSCAMB") == "SI" or r.get("PARK_RIDE") == "SI",
            "tipologia": r.get("TIPOLOGIA", ""),
        })
    return elenco


class RaccoltaOsm(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.record = []

    def node(self, n):
        if n.tags.get("amenity") != "parking":
            return
        if not n.location.valid():
            return
        t = n.tags
        self.record.append({
            "sorgente": "OSM_nodo", "osm_id": n.id, "osm_tipo": "node",
            "lat": n.location.lat, "lon": n.location.lon,
            "poligono": None, "superficie_m2": None,
            "name": t.get("name"), "parking": t.get("parking"),
            "capacity": t.get("capacity"), "fee": t.get("fee"),
            "access": t.get("access"), "park_ride": t.get("park_ride"),
            "building_levels": t.get("building:levels"),
        })

    def way(self, w):
        if w.tags.get("amenity") != "parking":
            return
        punti = [(nd.location.lon, nd.location.lat) for nd in w.nodes
                 if nd.location.valid()]
        if not punti:
            return
        chiuso = len(punti) >= 4 and (abs(punti[0][0] - punti[-1][0]) < 1e-12
                                      and abs(punti[0][1] - punti[-1][1]) < 1e-12)
        t = w.tags
        lat = sum(p[1] for p in punti) / len(punti)
        lon = sum(p[0] for p in punti) / len(punti)
        self.record.append({
            "sorgente": "OSM_via", "osm_id": w.id, "osm_tipo": "way",
            "lat": lat, "lon": lon,
            "poligono": punti if chiuso else None,
            "superficie_m2": superficie_laccio(punti) if chiuso else None,
            "name": t.get("name"), "parking": t.get("parking"),
            "capacity": t.get("capacity"), "fee": t.get("fee"),
            "access": t.get("access"), "park_ride": t.get("park_ride"),
            "building_levels": t.get("building:levels"),
        })


def carica_osm():
    h = RaccoltaOsm()
    h.apply_file(str(PBF), locations=True)
    for o in h.record:
        o["_bbox"] = None
        if o["poligono"]:
            lon = [p[0] for p in o["poligono"]]
            lat = [p[1] for p in o["poligono"]]
            o["_bbox"] = (min(lat), min(lon), max(lat), max(lon))
    return h.record


def id_con_riempimento():
    """ID 5T che hanno trasmesso almeno una lettura di occupazione con 'liberi' non nullo."""
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        righe = c.execute("select distinct id from occupazione_pk where liberi is not null "
                          "and date(datetime(substr(generato_utc,1,19), '+2 hours')) between ? and ?",
                          comuni.PERIODO["parcheggi"]).fetchall()      # periodo fisso (L9b)
    finally:
        c.close()
    return {r[0] for r in righe}


# --- costruzione ------------------------------------------------------------------------

def main():
    for p in (XML_5T, ZIP_COMUNE, PBF, DB):
        if not p.exists():
            sys.exit(f"Manca: {p}")

    print("leggo i parcheggi 5T...")
    p5t = carica_5t()
    print(f"  5T (senza camper): {len(p5t)}")
    print("leggo i parcheggi del Comune...")
    pcom = carica_comune()
    print(f"  Comune: {len(pcom)}")

    # controllo: i 4 del Comune convertiti devono essere entro 300 m dalla stessa voce 5T
    per_nome_5t = {normalizza(p["nome"]): p for p in p5t}
    for c in pcom:
        if not c["interscambio"]:
            continue
        r = per_nome_5t.get(normalizza(c["nome"]))
        if r is None:
            continue
        d = haversine_m(c["lat"], c["lon"], r["lat"], r["lon"])
        print(f"  controllo conversione {c['nome']}: {d:.0f} m dal punto 5T")
        if d > 300:
            sys.exit(f"Convertito male il parcheggio del Comune '{c['nome']}': {d:.0f} m dal 5T.")

    print("leggo i parcheggi OpenStreetMap...")
    osm = carica_osm()
    print(f"  OSM: {len(osm)} ({sum(1 for o in osm if o['poligono'])} vie chiuse)")
    if len(osm) < 5000 or len(osm) > 5400:
        sys.exit(f"Parcheggi OSM fuori dall'atteso (~5.176): {len(osm)}")

    print("unisco 5T e Comune (stesso nome e meno di 150 m)...")
    for c in pcom:
        c["usato"] = False
    base = []
    for p in p5t:
        base.append({
            "nome": p["nome"], "fonti": ["5T"], "id_5t": p["id_5t"],
            "lat": p["lat"], "lon": p["lon"], "posti_5t": p["posti"],
            "posti_comune": None, "trasmette": p["trasmette"],
            "interscambio_comune": normalizza(p["nome"]) in UFFICIALI,
            "osm": [],
        })
    indice_nome = {}
    for b in base:
        indice_nome.setdefault(normalizza(b["nome"]), []).append(b)
    for c in pcom:
        nome_c = normalizza(c["nome"])
        cand = indice_nome.get(nome_c)
        scelto = None
        if cand:
            for b in cand:
                if haversine_m(b["lat"], b["lon"], c["lat"], c["lon"]) < RAGGIO_ABBINA_NOME_M:
                    scelto = b
                    break
        if scelto is None:
            base.append({
                "nome": c["nome"], "fonti": ["Comune"], "id_5t": None,
                "lat": c["lat"], "lon": c["lon"], "posti_5t": None,
                "posti_comune": c["posti"], "trasmette": False,
                "interscambio_comune": c["interscambio"], "osm": [],
            })
            c["usato"] = True
            continue
        scelto["fonti"].append("Comune")
        scelto["posti_comune"] = c["posti"]
        scelto["interscambio_comune"] = scelto["interscambio_comune"] or c["interscambio"]
        c["usato"] = True
    print(f"  record 5T + Comune dopo l'unione: {len(base)}")

    print("abbino gli OSM ai parcheggi 5T/Comune (dentro il poligono o entro 60 m)...")
    assegnazione = {}
    for oi, o in enumerate(osm):
        bbox = o["_bbox"]
        for bi, b in enumerate(base):
            d = None
            if o["poligono"]:
                if (bbox[0] - 0.002 <= b["lat"] <= bbox[2] + 0.002
                        and bbox[1] - 0.003 <= b["lon"] <= bbox[3] + 0.003):
                    if dentro_poligono(b["lat"], b["lon"], o["poligono"]):
                        d = 0.0
            if d is None:
                dc = haversine_m(b["lat"], b["lon"], o["lat"], o["lon"])
                if dc <= RAGGIO_ABBINA_OSM_M:
                    d = dc
            if d is not None and (oi not in assegnazione or d < assegnazione[oi][0]):
                assegnazione[oi] = (d, bi)
    usati = set()
    for oi, (d, bi) in assegnazione.items():
        base[bi]["osm"].append(osm[oi])
        usati.add(oi)
    print(f"  OSM abbinati a un parcheggio 5T/Comune: {len(usati)}")

    print("costruisco i record finali...")
    con_riempimento = id_con_riempimento()
    record = []

    def nota_per_tipo(tipo, b, o_principale):
        if tipo in ("interscambio_ufficiale", "garage_5t"):
            if b is not None and b.get("id_5t") and b["id_5t"] in con_riempimento:
                return "posti e riempimento dal 5T"
            return "nessun riempimento trasmesso"
        if tipo == "park_ride_osm":
            return "segnato park&ride in OpenStreetMap; posti solo se indicati"
        if tipo == "osm_pubblico":
            return "parcheggio aperto da OpenStreetMap; posti dichiarati o stimati dalla superficie"
        if tipo == "lungo_strada":
            return "sosta lungo la strada: non contata nei posti"
        if tipo == "clienti":
            return "solo per clienti (es. centri commerciali): non contato"
        return "privato: escluso"

    def tipo_di(b, osm_list):
        nome = normalizza(b["nome"]) if b else ""
        if b is not None and b["interscambio_comune"] and nome in UFFICIALI:
            return "interscambio_ufficiale"
        if b is not None and (("5T" in b["fonti"]) or ("Comune" in b["fonti"])):
            return "garage_5t"
        o = osm_list[0] if osm_list else None
        if o is not None and (o.get("park_ride") or "").lower() == "yes":
            return "park_ride_osm"
        if o is not None and (o.get("access") or "").lower() in ("private", "no"):
            return "privato"
        if o is not None and (o.get("access") or "").lower() == "customers":
            return "clienti"
        if o is not None and (o.get("parking") or "").lower() in ("street_side", "lane", "layby"):
            return "lungo_strada"
        return "osm_pubblico"

    def intero_o_none(v):
        try:
            return int(str(v).strip())
        except (TypeError, ValueError):
            return None

    for b in base:
        osm_list = b["osm"]
        tipo = tipo_di(b, osm_list)
        o = osm_list[0] if osm_list else None
        posti_dich = b["posti_5t"]
        if posti_dich is None:
            posti_dich = b["posti_comune"]
        if posti_dich is None and o is not None and tipo in ("park_ride_osm", "osm_pubblico"):
            posti_dich = intero_o_none(o.get("capacity"))
        superficie = None
        for x in osm_list:
            if x["superficie_m2"]:
                superficie = (superficie or 0.0) + x["superficie_m2"]
        posti_stim = None
        if (posti_dich is None and superficie and superficie > 0
                and tipo in ("park_ride_osm", "osm_pubblico")):
            posti_stim = superficie / MQ_PER_POSTO
            if o is not None and (o.get("parking") or "").lower() == "multi-storey":
                liv = intero_o_none(o.get("building_levels"))
                if liv:
                    posti_stim *= liv
            posti_stim = int(round(posti_stim))
        if tipo in ("interscambio_ufficiale", "garage_5t"):
            a_pag = True
        elif tipo == "privato":
            a_pag = None
        else:
            fee = (o.get("fee") or "").lower() if o is not None else ""
            a_pag = True if fee == "yes" else (False if fee == "no" else "ignota")
        park_ride = bool(b["interscambio_comune"]) or (o is not None and (o.get("park_ride") or "").lower() == "yes")
        record.append({
            "nome": b["nome"], "tipo": tipo, "fonti": b["fonti"],
            "lat": round(b["lat"], 6), "lon": round(b["lon"], 6),
            "posti_dichiarati": posti_dich,
            "posti_stimati": posti_stim,
            "superficie_m2": round(superficie) if superficie else None,
            "a_pagamento": a_pag, "park_ride": park_ride,
            "id_5t": b["id_5t"],
            "id_osm": o["osm_id"] if o is not None else None,
            "parking": o.get("parking") if o is not None else None,
            "access": o.get("access") if o is not None else None,
            "nota": nota_per_tipo(tipo, b, o),
        })

    non_usati = [osm[i] for i in range(len(osm)) if i not in usati]
    for o in non_usati:
        tipo = tipo_di(None, [o])
        posti_dich = intero_o_none(o.get("capacity")) if tipo in ("park_ride_osm", "osm_pubblico") else None
        posti_stim = None
        if (posti_dich is None and o["superficie_m2"] and tipo in ("park_ride_osm", "osm_pubblico")):
            posti_stim = o["superficie_m2"] / MQ_PER_POSTO
            if (o.get("parking") or "").lower() == "multi-storey":
                liv = intero_o_none(o.get("building_levels"))
                if liv:
                    posti_stim *= liv
            posti_stim = int(round(posti_stim))
        if tipo == "privato":
            a_pag = None
        else:
            fee = (o.get("fee") or "").lower()
            a_pag = True if fee == "yes" else (False if fee == "no" else "ignota")
        record.append({
            "nome": o.get("name") or f"OSM {o['osm_tipo']} {o['osm_id']}",
            "tipo": tipo, "fonti": ["OSM"], "lat": round(o["lat"], 6), "lon": round(o["lon"], 6),
            "posti_dichiarati": posti_dich, "posti_stimati": posti_stim,
            "superficie_m2": round(o["superficie_m2"]) if o["superficie_m2"] else None,
            "a_pagamento": a_pag,
            "park_ride": (o.get("park_ride") or "").lower() == "yes",
            "id_5t": None, "id_osm": o["osm_id"],
            "parking": o.get("parking"), "access": o.get("access"),
            "nota": nota_per_tipo(tipo, None, o),
        })

    # id stabili: prima i 5 ufficiali, poi gli altri con fonti 5T/Comune, poi gli OSM
    def chiave_ordine(r):
        prio = 0 if r["tipo"] == "interscambio_ufficiale" else (
            1 if ("5T" in r["fonti"] or "Comune" in r["fonti"]) else 2)
        return (prio, r["nome"])
    record.sort(key=chiave_ordine)
    for i, r in enumerate(record, start=1):
        r["id"] = f"P{i:05d}"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "n_5t": len(p5t), "n_comune": len(pcom), "n_osm": len(osm),
        "n_osm_abbinati": len(usati),
        "parcheggi": record,
    }, ensure_ascii=False), encoding="utf-8")

    # --- controlli e rapporto ---
    conteggio = Counter(r["tipo"] for r in record)
    posti_dich_per_tipo = {}
    posti_stim_per_tipo = {}
    for r in record:
        posti_dich_per_tipo[r["tipo"]] = posti_dich_per_tipo.get(r["tipo"], 0) + (r["posti_dichiarati"] or 0)
        posti_stim_per_tipo[r["tipo"]] = posti_stim_per_tipo.get(r["tipo"], 0) + (r["posti_stimati"] or 0)
    ufficiali = [r for r in record if r["tipo"] == "interscambio_ufficiale"]
    n_parkride_osm = sum(1 for o in osm if (o.get("park_ride") or "").lower() == "yes")

    righe = []
    righe.append("RAPPORTO R6 v2 — INVENTARIO DEI PARCHEGGI (Passo 2)")
    righe.append(f"parcheggi 5T (senza camper): {len(p5t)}")
    righe.append(f"parcheggi del Comune: {len(pcom)}")
    righe.append(f"parcheggi OpenStreetMap: {len(osm)} (di cui {n_parkride_osm} park&ride, "
                 f"{sum(1 for o in osm if o.get('capacity'))} con 'capacity')")
    righe.append(f"OSM abbinati a un parcheggio 5T/Comune (non contati due volte): {len(usati)}")
    righe.append(f"parcheggi finali nell'elenco: {len(record)}")
    righe.append("")
    righe.append("== Conteggi per tipo ==")
    ordine_tipi = ["interscambio_ufficiale", "garage_5t", "park_ride_osm", "osm_pubblico",
                   "lungo_strada", "clienti", "privato"]
    for t in ordine_tipi:
        righe.append(f"  {t:22s} {conteggio.get(t, 0):5d}   posti dichiarati {posti_dich_per_tipo.get(t, 0):6d}"
                     f"   posti stimati {posti_stim_per_tipo.get(t, 0):6d}")
    righe.append("")
    righe.append("== Nota per tipo (uguale per tutti i parcheggi di quel tipo) ==")
    for t in ordine_tipi:
        esempio = next((r for r in record if r["tipo"] == t), None)
        if esempio:
            righe.append(f"  {t}: {esempio['nota']}")
    righe.append("")
    righe.append("== I 5 interscambi ufficiali e i parcheggi OSM entro 500 m ==")
    for u in ufficiali:
        righe.append(f"  {u['nome']}  posti={u['posti_dichiarati']}  ({u['nota']})")
        vicini = [r for r in record if r is not u and "OSM" in r["fonti"]
                  and haversine_m(u["lat"], u["lon"], r["lat"], r["lon"]) <= 500]
        vicini.sort(key=lambda r: haversine_m(u["lat"], u["lon"], r["lat"], r["lon"]))
        for r in vicini[:60]:
            righe.append(f"      {haversine_m(u['lat'], u['lon'], r['lat'], r['lon']):5.0f} m  "
                         f"{r['tipo']:14s} sup={r['superficie_m2'] or '-':>7} posti="
                         f"{r['posti_dichiarati'] or r['posti_stimati'] or '-':>5} "
                         f"pagamento={r['a_pagamento']} parking={r['parking'] or '-'}")
        if len(vicini) > 60:
            righe.append(f"      ... e altri {len(vicini) - 60}")
    righe.append("")
    righe.append("== Controllo Fermi (45,0766; 7,5903) entro 500 m ==")
    aperti = ("interscambio_ufficiale", "garage_5t", "park_ride_osm", "osm_pubblico")
    vicini_fermi = [r for r in record if r["tipo"] in aperti
                    and haversine_m(FERMI_LAT, FERMI_LON, r["lat"], r["lon"]) <= 500]
    tot_sup = sum(r["superficie_m2"] or 0 for r in vicini_fermi)
    pag = Counter(str(r["a_pagamento"]) for r in vicini_fermi)
    righe.append(f"  parcheggi aperti entro 500 m: {len(vicini_fermi)}")
    righe.append(f"  superficie totale: {tot_sup:.0f} m2")
    righe.append(f"  tariffa: {dict(pag)}")
    sotterranei = [r for r in vicini_fermi
                   if (r["parking"] or "") == "underground" and (r["superficie_m2"] or 0) > 20000]
    for r in sotterranei:
        righe.append(f"  sotterraneo grande: {r['superficie_m2']} m2 a "
                     f"{haversine_m(FERMI_LAT, FERMI_LON, r['lat'], r['lon']):.0f} m")
    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")

    print(f"Scritto: {OUT}")
    print(f"Scritto: {RAPPORTO}")
    print(f"parcheggi={len(record)} ufficiali={len(ufficiali)}")
    print("per tipo:", dict(conteggio))
    print(f"Fermi entro 500 m: {len(vicini_fermi)} parcheggi aperti, {tot_sup:.0f} m2, tariffa {dict(pag)}")


if __name__ == "__main__":
    sys.exit(main())
