#!/usr/bin/env python3
"""
72_nodi_tp.py  -  Risultato 6 v2, PASSI 4 e 5: nodi di trasporto e funzione dei parcheggi.

Cosa fa (Passo 4)
-----------------
Dal GTFS conta quante corse partono da ogni fermata in ogni ora del giorno feriale
2026-10-12, poi somma per LUOGO (gruppi di fermate vicine del Passo 1). Per ogni luogo
calcola:
  - b2 = corse/ora nelle ore dei pendolari (6-9 e 16-19);
  - b_giorno = corse/ora in tutta la giornata (6-20);
  - b1_luogo = somma delle corse/ora di punta della versione 1;
  - metro = il luogo ha una fermata della metropolitana (route_type = 1);
  - capolinea = dal luogo partono almeno 4 corse/ora fra le 6 e le 9 (prima fermata della corsa).
Dall'OpenStreetMap prende le stazioni dei treni e dice quali luoghi hanno una stazione
entro 300 m (ferro). Un luogo e' un "nodo forte" se ha metro o ferro o capolinea o b2 >= 20.

Cosa fa (Passo 5)
-----------------
Per ogni parcheggio aperto (non privato, non per clienti, non sosta lunga) dice quanto
fa davvero da interscambio: la sua firma di riempimento (Passo 3), quanti punti a favore
ha (vicinanza a un nodo forte, nodo metro/treno/capolinea, essere su un asse d'ingresso),
i posti e la tariffa. Da qui una classe: interscambio_di_fatto / solo_sulla_carta /
potenziale / non_interscambio.

NOVITA' DEL GIRO 2 (19/10/2026)
-------------------------------
- La strada di ogni parcheggio si trova con il modulo condiviso `scripts/77_strade_comuni.py`
  (non piu' "il tratto piu' vicino", ma "il tratto piu' importante entro poca distanza":
  raggio stretto 50 m, raggio largo 150 m).
- Un parcheggio in ZONA CENTRALE (predefinito Q001-Q009, opzione `--zone-centrali`) non e'
  mai un interscambio: chi arriva in centro non lascia l'auto per prendere un mezzo.
- La vicinanza a un nodo e l'essere su un asse d'ingresso NON sono piu' un via libera o
  uno stop: sono PUNTI A FAVORE (forza 0-3), usati per dire "potenziale".
- Nel rapporto c'e' la tabella di sensibilita' della zona centrale (Q001, Q001-Q005,
  Q001-Q009, Q001-Q012).

Cosa legge
----------
  data/raw/gtt_gtfs_20261003_224530.zip            (orari programmati)
  data/otp/rete/torino_cintura.osm.pbf             (stazioni dei treni)
  data/processed/risultato6_interscambio.json      (corse/ora di punta della v1)
  data/processed/risultato6_v2/luoghi.json         (Passo 1)
  data/processed/risultato6_v2/parcheggi.json      (Passo 2)
  data/processed/risultato6_v2/riempimento.json    (Passo 3)
  data/processed/traffico_d/...                    (strade e tratte, dal modulo 77)
  data/processed/imq_zone_geo.json                 (zona IMQ, per "zona centrale")

Cosa scrive
-----------
  data/processed/risultato6_v2/nodi.json
  data/processed/risultato6_v2/parcheggi_funzione.json
  docs/rapporti/RAPPORTO_R6V2_NODI.txt
  docs/rapporti/RAPPORTO_R6V2_FUNZIONE.txt

Come si lancia
--------------
  python scripts\\72_nodi_tp.py --prova     (prime 400 fermate dei luoghi, controllo rapido)
  python scripts\\72_nodi_tp.py             (giro completo)
  python scripts\\72_nodi_tp.py --zone-centrali Q001,Q002,Q003
"""
import argparse
import csv
import io
import json
import math
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import osmium

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from comuni import haversine_m  # noqa: E402  (stessa formula della copia che stava qui)


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
GTFS = RADICE / "data" / "raw" / "gtt_gtfs_20261003_224530.zip"
PBF = RADICE / "data" / "otp" / "rete" / "torino_cintura.osm.pbf"
V1 = RADICE / "data" / "processed" / "risultato6_interscambio.json"
LUOGHI = RADICE / "data" / "processed" / "risultato6_v2" / "luoghi.json"
PARCHEGGI = RADICE / "data" / "processed" / "risultato6_v2" / "parcheggi.json"
RIEMPIMENTO = RADICE / "data" / "processed" / "risultato6_v2" / "riempimento.json"
ZONE_GEO = RADICE / "data" / "processed" / "imq_zone_geo.json"
RETE = RADICE / "data" / "processed" / "traffico_d" / "rete" / "rete_auto.npz"
ASSI = RADICE / "data" / "processed" / "traffico_d" / "assi_tratte.npz"
TRATTE = RADICE / "data" / "processed" / "traffico_d" / "tratte_traffico.json"
OUT_NODI = RADICE / "data" / "processed" / "risultato6_v2" / "nodi.json"
OUT_FUNZ = RADICE / "data" / "processed" / "risultato6_v2" / "parcheggi_funzione.json"
RAP_NODI = RADICE / "docs" / "rapporti" / "RAPPORTO_R6V2_NODI.txt"
RAP_NODI.parent.mkdir(parents=True, exist_ok=True)
RAP_FUNZ = RADICE / "docs" / "rapporti" / "RAPPORTO_R6V2_FUNZIONE.txt"
RAP_FUNZ.parent.mkdir(parents=True, exist_ok=True)

GIORNO_TIPO = "20261012"
GIORNI = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
ORE_PENDOLARI = (6, 7, 8, 9, 16, 17, 18, 19)
ORE_GIORNO = tuple(range(6, 21))
RAGGIO_FERRO_M = 300.0
SOGLIA_NODO_FREQUENTE = 20.0
RAGGIO_ASSE_M = 150.0
ZONE_CENTRALI_DEFAULT = tuple(f"Q{i:03d}" for i in range(1, 10))   # Q001...Q009
RAGGIO_NODO_PARCHEGGIO_M = 400.0
LAT_RIF = 45.07
FATTORE_GRADI_M = 111000.0
TIPI_ESCLUSI = ("privato", "clienti", "lungo_strada")


def proietta(lon, lat):
    return (lon * FATTORE_GRADI_M * math.cos(math.radians(LAT_RIF)), lat * FATTORE_GRADI_M)


def dist_punto_segmento_m(px, py, ax, ay, bx, by):
    """Distanza in metri fra il punto (px,py) e il segmento (ax,ay)-(bx,by),
    tutti in coordinate piane in metri."""
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        t = 0.0
    else:
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy)


# --- Passo 4: GTFS -----------------------------------------------------------------------

def servizi_attivi(zf, giorno):
    import datetime
    data = datetime.date(int(giorno[:4]), int(giorno[4:6]), int(giorno[6:8]))
    colonna = GIORNI[data.weekday()]
    attivi = set()
    with zf.open("calendar.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            if r[colonna] == "1" and r["start_date"] <= giorno <= r["end_date"]:
                attivi.add(r["service_id"])
    try:
        with zf.open("calendar_dates.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                if r["date"] != giorno:
                    continue
                if r["exception_type"] == "1":
                    attivi.add(r["service_id"])
                elif r["exception_type"] == "2":
                    attivi.discard(r["service_id"])
    except KeyError:
        pass
    return attivi


def leggi_gtfs():
    """Ritorna (ore_per_fermata, prime_partenze, fermate_metro, fermate_gtfs)."""
    zf = zipfile.ZipFile(GTFS)
    attivi = servizi_attivi(zf, GIORNO_TIPO)
    print(f"  servizi attivi il {GIORNO_TIPO}: {len(attivi)}")

    tipo_route = {}
    with zf.open("routes.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            tipo_route[r["route_id"]] = r["route_type"]

    trip_route = {}
    with zf.open("trips.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            if r["service_id"] in attivi:
                trip_route[r["trip_id"]] = r["route_id"]
    print(f"  corse attive: {len(trip_route)}")

    fermate_gtfs = {}
    with zf.open("stops.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            try:
                fermate_gtfs[r["stop_id"]] = (float(r["stop_lat"]), float(r["stop_lon"]), r["stop_name"])
            except (TypeError, ValueError):
                continue

    ore = defaultdict(lambda: [0] * 24)
    prima_seq = {}
    prima_info = {}
    with zf.open("stop_times.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            tid = r["trip_id"]
            if tid not in trip_route:
                continue
            orario = r.get("departure_time") or r.get("arrival_time") or ""
            if not orario:
                continue
            try:
                ora = int(orario.split(":")[0]) % 24
            except ValueError:
                continue
            sid = r["stop_id"]
            ore[sid][ora] += 1
            try:
                seq = int(r["stop_sequence"])
            except ValueError:
                continue
            if tid not in prima_seq or seq < prima_seq[tid]:
                prima_seq[tid] = seq
                prima_info[tid] = (sid, ora)

    prime = defaultdict(lambda: [0] * 24)
    for tid, (sid, ora) in prima_info.items():
        prime[sid][ora] += 1

    fermate_metro = set()
    for tid, rid in trip_route.items():
        if tipo_route.get(rid) == "1":
            sid, _ = prima_info.get(tid, (None, None))
            if sid:
                fermate_metro.add(sid)
    with zf.open("stop_times.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            tid = r["trip_id"]
            if tid in trip_route and tipo_route.get(trip_route[tid]) == "1":
                fermate_metro.add(r["stop_id"])
    print(f"  fermate con metropolitana: {len(fermate_metro)}")
    return ore, prime, fermate_metro, fermate_gtfs


# --- Passo 4: stazioni dei treni da OSM ---------------------------------------------------

class Stazioni(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.trovate = []

    def _valuta(self, tag, lat, lon):
        if tag.get("railway") != "station" and not (
                tag.get("public_transport") == "station" and tag.get("train") == "yes"):
            return
        if tag.get("station") == "subway" or tag.get("subway") == "yes":
            return
        self.trovate.append({"nome": tag.get("name"), "lat": lat, "lon": lon})

    def node(self, n):
        self._valuta(n.tags, n.location.lat, n.location.lon)

    def way(self, w):
        if w.tags.get("railway") != "station" and not (
                w.tags.get("public_transport") == "station" and w.tags.get("train") == "yes"):
            return
        if w.tags.get("station") == "subway" or w.tags.get("subway") == "yes":
            return
        punti = [(nd.location.lat, nd.location.lon) for nd in w.nodes if nd.location.valid()]
        if not punti:
            return
        self._valuta(w.tags, sum(p[0] for p in punti) / len(punti),
                     sum(p[1] for p in punti) / len(punti))


def carica_stazioni():
    h = Stazioni()
    h.apply_file(str(PBF), locations=True)
    return h.trovate


# --- Passo 5: strade (modulo condiviso 77 del giro 2) ------------------------------------

def carica_modulo_strade():
    """Carica scripts/77_strade_comuni.py: un solo modo di trovare la strada di un punto."""
    import importlib.util
    percorso = AQUI / "77_strade_comuni.py"
    spec = importlib.util.spec_from_file_location("strade_comuni", percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# --- zone IMQ ---------------------------------------------------------------------------

def dentro_poligono(lat, lon, anelli):
    for anello in anelli:
        n = len(anello)
        dentro = False
        j = n - 1
        for i in range(n):
            yi, xi = anello[i]
            yj, xj = anello[j]
            if ((yi > lat) != (yj > lat)) and (
                lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
            ):
                dentro = not dentro
            j = i
        if dentro:
            return True
    return False


def carica_zone_imq():
    geo = json.loads(ZONE_GEO.read_text(encoding="utf-8"))
    zone = []
    for z in geo:
        g = z["g"]
        if isinstance(g, str):
            g = json.loads(g)
        if g and isinstance(g[0][0], (int, float)):
            anelli = [g]
        elif g and isinstance(g[0][0][0], (int, float)):
            anelli = g
        else:
            anelli = [anello for poligono in g for anello in poligono]
        lat_min = min(p[0] for anello in anelli for p in anello)
        lat_max = max(p[0] for anello in anelli for p in anello)
        lon_min = min(p[1] for anello in anelli for p in anello)
        lon_max = max(p[1] for anello in anelli for p in anello)
        zone.append({"cod": z["cod"], "anelli": anelli,
                     "bbox": (lat_min, lon_min, lat_max, lon_max)})
    return zone


def zona_di(lat, lon, zone):
    for z in zone:
        lat_min, lon_min, lat_max, lon_max = z["bbox"]
        if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
            continue
        if dentro_poligono(lat, lon, z["anelli"]):
            return z["cod"]
    return None


# --- main --------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true",
                    help="limita i luoghi alle fermate delle prime 400 fermate per stop_id")
    ap.add_argument("--zone-centrali", default=",".join(ZONE_CENTRALI_DEFAULT),
                    help="zone IMQ considerate 'centro' per i parcheggi (default Q001-Q009)")
    ap.add_argument("--raggio-stretto", type=float, default=50.0,
                    help="raggio stretto per la ricerca della strada (default 50 m)")
    ap.add_argument("--raggio-largo", type=float, default=150.0,
                    help="raggio largo per la ricerca della strada (default 150 m)")
    ap.add_argument("--raggio-nodo-m", type=float, default=RAGGIO_NODO_PARCHEGGIO_M,
                    help="distanza massima da un nodo forte per il punto a favore (default 400 m)")
    args = ap.parse_args()

    for p in (GTFS, PBF, V1, LUOGHI, PARCHEGGI, RIEMPIMENTO, RETE, ASSI, TRATTE, ZONE_GEO):
        if not p.exists():
            sys.exit(f"Manca: {p}")

    dati_v1 = json.loads(V1.read_text(encoding="utf-8"))
    corse_punta_v1 = {f["stop_id"]: f.get("corse_ora_punta", 0) for f in dati_v1["fermate"]}
    luoghi = json.loads(LUOGHI.read_text(encoding="utf-8"))["luoghi"]
    if args.prova:
        stop_prova = set(sorted(corse_punta_v1)[:400])
        luoghi = [l for l in luoghi if set(l["stop_ids"]) & stop_prova]
        print(f"[--prova] luoghi con le prime 400 fermate: {len(luoghi)}")

    print("Passo 4: leggo il GTFS (corse per fermata e ora)...")
    ore, prime, fermate_metro, fermate_gtfs = leggi_gtfs()

    print("Passo 4: leggo le stazioni dei treni da OpenStreetMap...")
    stazioni = carica_stazioni()
    print(f"  stazioni trovate: {len(stazioni)}")

    print("Passo 4: calcolo i segnali per luogo...")
    nodi = []
    for l in luoghi:
        tot = [0] * 24
        prim = [0] * 24
        for sid in l["stop_ids"]:
            v = ore.get(sid)
            if v:
                for h in range(24):
                    tot[h] += v[h]
            w = prime.get(sid)
            if w:
                for h in range(24):
                    prim[h] += w[h]
        b2 = sum(tot[h] for h in ORE_PENDOLARI) / len(ORE_PENDOLARI)
        b_giorno = sum(tot[h] for h in ORE_GIORNO) / len(ORE_GIORNO)
        b1_luogo = sum(corse_punta_v1.get(sid, 0) for sid in l["stop_ids"])
        metro = any(sid in fermate_metro for sid in l["stop_ids"])
        capolinea = sum(prim[h] for h in (6, 7, 8, 9)) / 4.0 >= 4.0
        ferro = any(haversine_m(l["lat"], l["lon"], s["lat"], s["lon"]) <= RAGGIO_FERRO_M
                    for s in stazioni)
        forte = metro or ferro or capolinea or b2 >= SOGLIA_NODO_FREQUENTE
        tipo_nodo = "metro" if metro else ("ferro" if ferro else (
            "capolinea" if capolinea else ("frequente" if b2 >= SOGLIA_NODO_FREQUENTE else None)))
        nodi.append({
            "id_luogo": l["id_luogo"], "nome": l["nome"], "lat": l["lat"], "lon": l["lon"],
            "zona_imq": l["zona_imq"], "in_centro": l["in_centro"], "n_fermate": l["n_fermate"],
            "b2_corse_ora_pendolari": round(b2, 3),
            "b_giorno_corse_ora": round(b_giorno, 3),
            "b1_luogo": b1_luogo,
            "metro": metro, "ferro": ferro, "capolinea": capolinea,
            "nodo_forte": forte, "tipo_nodo": tipo_nodo,
        })
    n_forti = sum(1 for n in nodi if n["nodo_forte"])

    print("Passo 5: carico il modulo delle strade (77) e trovo gli assi di ingresso...")
    m77 = carica_modulo_strade()
    strade = m77.carica_strade()
    print(f"  assi di ingresso (Torino + almeno un altro comune): {len(strade['assi_ingresso'])}")

    parcheggi = json.loads(PARCHEGGI.read_text(encoding="utf-8"))["parcheggi"]
    riemp = {r["id_5t"]: r for r in json.loads(RIEMPIMENTO.read_text(encoding="utf-8"))["parcheggi"]}
    zone = carica_zone_imq()
    zone_centrali = {z.strip() for z in args.zone_centrali.split(",") if z.strip()}
    raggio_nodo = args.raggio_nodo_m

    print("Passo 5: calcolo posizione, uso, punti a favore e classe di ogni parcheggio...")
    nodi_forti = [n for n in nodi if n["nodo_forte"]]
    TIRO_FERRO = ("metro", "ferro", "capolinea")
    grezzi = []
    for p in parcheggi:
        if p["tipo"] in TIPI_ESCLUSI:
            continue
        d_nodo, n_vicino = None, None
        for n in nodi_forti:
            dd = haversine_m(p["lat"], p["lon"], n["lat"], n["lon"])
            if d_nodo is None or dd < d_nodo:
                d_nodo, n_vicino = dd, n
        strada = m77.trova_strada(strade, p["lat"], p["lon"],
                                  raggio_stretto=args.raggio_stretto,
                                  raggio_largo=args.raggio_largo)
        cod_zona = zona_di(p["lat"], p["lon"], zone)
        zona_centrale = cod_zona in zone_centrali
        r = riemp.get(p["id_5t"]) if p["id_5t"] else None
        uso = r["firma"] if r else "sconosciuto"
        posti = p["posti_dichiarati"] or p["posti_stimati"]

        # punti a favore (0-3): non bloccano e non aprono da soli, pesano
        nodo_vicino = d_nodo is not None and d_nodo <= raggio_nodo
        nodo_ferro_metro = bool(nodo_vicino and n_vicino["tipo_nodo"] in TIRO_FERRO)
        su_asse = bool(strada["asse_ingresso"])
        forza = int(nodo_vicino) + int(nodo_ferro_metro) + int(su_asse)
        punti = []
        if nodo_vicino:
            punti.append(f"nodo: {n_vicino['tipo_nodo']} {n_vicino['nome'][:28]} "
                         f"{round(d_nodo)} m")
        if su_asse:
            punti.append(f"asse d'ingresso: {strada['nome'] or '-'} "
                         f"{strada['distanza_m']} m")
        grezzi.append({
            "id": p["id"], "nome": p["nome"], "tipo": p["tipo"],
            "lat": p["lat"], "lon": p["lon"],
            "dist_nodo_forte_m": round(d_nodo) if d_nodo is not None else None,
            "tipo_nodo": n_vicino["tipo_nodo"] if n_vicino else None,
            "zona_imq": cod_zona, "zona_centrale": zona_centrale,
            "nodo_vicino": nodo_vicino, "nodo_ferro_metro": nodo_ferro_metro,
            "su_asse_ingresso": su_asse,
            "strada": strada["nome"], "strada_classe": strada["classe"],
            "strada_esito": strada["esito"], "strada_distanza_m": strada["distanza_m"],
            "forza": forza, "punti_a_favore": punti,
            "uso": uso, "posti": posti, "a_pagamento": p["a_pagamento"],
        })

    USI_SCONOSCIUTI = ("sconosciuto", "nessun_dato", "dati_insufficienti")
    USI_NON_PENDOLARI = ("residenziale", "destinazione", "misto", "dato_bloccato", "vuoto")

    def classe_di(g, centrali):
        """Regole del giro 2 (prima regola che vale). Ritorna (classe, motivo)."""
        if g["zona_imq"] in centrali:
            return "non_interscambio", "zona_centrale"
        if g["tipo"] in ("interscambio_ufficiale", "park_ride_osm") and (
                g["uso"] in USI_NON_PENDOLARI or g["uso"] == "vuoto"):
            return "solo_sulla_carta", "dichiarato_non_usato"
        if g["uso"] == "pendolare":
            return "interscambio_di_fatto", "uso_pendolare"
        if g["uso"] in USI_SCONOSCIUTI and g["forza"] >= 1:
            return "potenziale", "punti_a_favore"
        if g["uso"] in USI_SCONOSCIUTI:
            return "non_interscambio", "nessun_punto"
        return "non_interscambio", "firma_non_pendolare"

    funzione = []
    for g in grezzi:
        classe, motivo = classe_di(g, zone_centrali)
        funzione.append({**g, "classe": classe, "motivo": motivo})

    OUT_NODI.parent.mkdir(parents=True, exist_ok=True)
    OUT_NODI.write_text(json.dumps({
        "giorno_tipo": GIORNO_TIPO,
        "ore_pendolari": list(ORE_PENDOLARI),
        "assi_ingresso": sorted(strade["assi_ingresso"]),
        "nomi_assi_ingresso": {str(a): strade["nome_asse"].get(a) for a in sorted(strade["assi_ingresso"])},
        "stazioni": stazioni,
        "luoghi": nodi,
    }, ensure_ascii=False), encoding="utf-8")
    OUT_FUNZ.parent.mkdir(parents=True, exist_ok=True)
    OUT_FUNZ.write_text(json.dumps({
        "zone_centrali": sorted(zone_centrali), "raggio_nodo_m": raggio_nodo,
        "raggio_stretto_m": args.raggio_stretto, "raggio_largo_m": args.raggio_largo,
        "parcheggi": funzione,
    }, ensure_ascii=False), encoding="utf-8")

    # --- rapporti ---
    n_tipi = Counter(n["tipo_nodo"] for n in nodi if n["nodo_forte"])
    righe = []
    righe.append("RAPPORTO R6 v2 — NODI DI TRASPORTO (Passo 4)")
    righe.append(f"modalita': {'PROVA' if args.prova else 'completa'}")
    righe.append(f"luoghi: {len(nodi)}; nodi forti: {n_forti}")
    righe.append("un luogo e' nodo forte se ha metro, o una stazione entro 300 m, o e' capolinea,"
                 f" o ha almeno {SOGLIA_NODO_FREQUENTE:.0f} corse/ora nelle ore dei pendolari")
    righe.append(f"  per tipo: {dict(n_tipi)}")
    righe.append(f"  con b2 >= 20 senza altro motivo (frequente): "
                 f"{sum(1 for n in nodi if n['tipo_nodo'] == 'frequente')}")
    righe.append("")
    righe.append("== Stazioni dei treni trovate in OpenStreetMap ==")
    for s in sorted(stazioni, key=lambda s: (s["nome"] or "")):
        righe.append(f"  {s['nome'] or '(senza nome)':35s} {s['lat']:.5f}, {s['lon']:.5f}")
    controllo = ("Porta Nuova", "Porta Susa", "Lingotto", "Stura", "Rebaudengo")
    nomi_st = " | ".join((s["nome"] or "") for s in stazioni)
    righe.append("")
    righe.append("== Controllo delle stazioni attese ==")
    for c in controllo:
        righe.append(f"  {c}: {'trovata' if c.lower() in nomi_st.lower() else 'NON TROVATA'}")
    metro_luoghi = [n for n in nodi if n["metro"]]
    righe.append("")
    righe.append("== Luoghi con la metropolitana ==")
    righe.append(f"  totale: {len(metro_luoghi)}")
    for n in sorted(metro_luoghi, key=lambda n: n["nome"]):
        righe.append(f"  {n['nome'][:45]:45s} zona={n['zona_imq'] or '-'} b2={n['b2_corse_ora_pendolari']:.1f} "
                     f"tipo={n['tipo_nodo']}")
    righe.append("")
    righe.append("== Primi 25 nodi forti per corse/ora pendolari ==")
    for n in sorted(nodi, key=lambda n: -n["b2_corse_ora_pendolari"])[:25]:
        righe.append(f"  {n['b2_corse_ora_pendolari']:6.1f}  {n['nome'][:45]:45s} zona={n['zona_imq'] or '-':5s} "
                     f"{n['tipo_nodo'] or '-'}{' (NON forte)' if not n['nodo_forte'] else ''}")
    RAP_NODI.parent.mkdir(parents=True, exist_ok=True)
    RAP_NODI.write_text("\n".join(righe) + "\n", encoding="utf-8")

    conteggi = Counter(f["classe"] for f in funzione)
    posti_per_classe = Counter()
    for f in funzione:
        posti_per_classe[f["classe"]] += f["posti"] or 0
    conteggi_motivo = Counter(f["motivo"] for f in funzione)
    righe = []
    righe.append("RAPPORTO R6 v2 (giro 2) — QUANTO OGNI PARCHEGGIO FA DA INTERSCAMBIO (Passo 5)")
    righe.append(f"parcheggi considerati (esclusi privati, per clienti e sosta lunga): {len(funzione)}")
    righe.append("NOVITA' DEL GIRO 2: la vicinanza a un nodo e l'essere su un asse d'ingresso NON sono")
    righe.append("piu' un via libera o uno stop, ma PUNTI A FAVORE (forza 0-3). Il primo filtro e' la")
    righe.append(f"zona centrale (qui: {', '.join(sorted(zone_centrali))}): li' un parcheggio non e' un")
    righe.append("interscambio, perche' chi arriva in centro non lascia l'auto per prendere un mezzo.")
    righe.append("  interscambio_di_fatto = firma 'pendolare' (l'auto si riempie al mattino e si")
    righe.append("                          svuota la sera) e non e' in zona centrale")
    righe.append("  solo_sulla_carta     = dichiarato interscambio o park&ride ma con firma non da pendolari")
    righe.append("  potenziale           = firma sconosciuta o senza dati, ma con almeno un punto a favore")
    righe.append("  non_interscambio     = tutto il resto")
    righe.append("")
    righe.append("== Parametri dichiarati di questo giro (provvisori, si possono cambiare) ==")
    righe.append(f"  zona centrale dei parcheggi: {', '.join(sorted(zone_centrali))} "
                 f"(opzione --zone-centrali)")
    righe.append(f"  punti a favore: nodo forte entro {raggio_nodo:.0f} m, di cui metro/treno/"
                 f"capolinea; asse d'ingresso (opzione --raggio-nodo-m)")
    righe.append(f"  ricerca della strada: raggio stretto {args.raggio_stretto:.0f} m, raggio largo "
                 f"{args.raggio_largo:.0f} m (opzioni --raggio-stretto/--raggio-largo)")
    righe.append("")
    righe.append("== Quanti parcheggi e quanti posti per classe ==")
    for c in ("interscambio_di_fatto", "solo_sulla_carta", "potenziale", "non_interscambio"):
        righe.append(f"  {c:22s} {conteggi.get(c, 0):5d} parcheggi   posti {posti_per_classe.get(c, 0):6d}")
    righe.append("")
    righe.append("== Per motivo ==")
    for m, n in sorted(conteggi_motivo.items(), key=lambda kv: -kv[1]):
        posti = sum(f["posti"] or 0 for f in funzione if f["motivo"] == m)
        righe.append(f"  {m:22s} {n:5d} parcheggi   posti {posti:6d}")
    righe.append("")
    righe.append("== Quanti parcheggi per forza (punti a favore) ==")
    for forza in range(4):
        sel1 = [f for f in funzione if f["forza"] == forza]
        righe.append(f"  forza {forza}: {len(sel1):5d} parcheggi   "
                     f"di cui 'di fatto' {sum(1 for f in sel1 if f['classe'] == 'interscambio_di_fatto')}   "
                     f"'potenziale' {sum(1 for f in sel1 if f['classe'] == 'potenziale')}")
    righe.append("")
    righe.append("== TABELLA DI SENSIBILITA' della zona centrale ==")
    righe.append("  zone centrali | di fatto | solo sulla carta | potenziale | non interscambio (di cui zona centrale)")
    insiemi = {
        "Q001": ("Q001",),
        "Q001-Q005": tuple(f"Q{i:03d}" for i in range(1, 6)),
        "Q001-Q009 (default)": tuple(f"Q{i:03d}" for i in range(1, 10)),
        "Q001-Q012": tuple(f"Q{i:03d}" for i in range(1, 13)),
    }
    for etichetta, insieme in insiemi.items():
        c = Counter()
        n_centro = 0
        for g in grezzi:
            classe, motivo = classe_di(g, set(insieme))
            c[classe] += 1
            if motivo == "zona_centrale":
                n_centro += 1
        righe.append(f"  {etichetta:20s} {c.get('interscambio_di_fatto', 0):7d} "
                     f"{c.get('solo_sulla_carta', 0):16d} {c.get('potenziale', 0):10d} "
                     f"{c.get('non_interscambio', 0):10d} ({n_centro})")
    righe.append("")
    righe.append("== I 5 interscambi ufficiali e i garage 5T ==")
    righe.append("  nome | tipo | zona | centrale | firma | forza | tariffa | classe")
    for f in sorted(funzione, key=lambda f: (f["tipo"] != "interscambio_ufficiale", f["tipo"], f["nome"])):
        if f["tipo"] not in ("interscambio_ufficiale", "garage_5t"):
            continue
        righe.append(f"  {f['nome'][:24]:24s} {f['tipo'][:22]:22s} {str(f['zona_imq'] or '-'):5s} "
                     f"{str(f['zona_centrale']):5s} {f['uso']:18s} {f['forza']} "
                     f"{str(f['a_pagamento']):6s} {f['classe']}")
    righe.append("")
    righe.append("== I 20 'potenziale' con piu' posti ==")
    potenziali = sorted([f for f in funzione if f["classe"] == "potenziale"],
                        key=lambda f: -(f["posti"] or 0))[:20]
    for f in potenziali:
        righe.append(f"  {str(f['posti'] or '-'):>5} posti  {f['nome'][:34]:34s} {f['tipo'][:14]:14s} "
                     f"forza={f['forza']} {str(f['dist_nodo_forte_m']):>5} m da {str(f['tipo_nodo'] or '-'):10s} "
                     f"tariffa={f['a_pagamento']}  punti: {'; '.join(f['punti_a_favore']) or '-'}")
    righe.append("")
    righe.append("== Controlli (non sono motivo di stop) ==")
    attesi_centro = ("MOLINETTE", "CTO", "PALAGIUSTIZIA", "NIZZA", "STATI UNITI", "ANCONA",
                     "BACIGALUPO", "FONTANESI", "VENTIMIGLIA")
    for nome in attesi_centro:
        f = next((x for x in funzione if x["nome"] == nome), None)
        if f is None:
            righe.append(f"  {nome}: non presente fra i parcheggi considerati")
        else:
            righe.append(f"  {nome}: {f['classe']} / {f['motivo']} (zona {f['zona_imq']}) "
                         f"{'OK' if f['classe'] == 'non_interscambio' and f['motivo'] == 'zona_centrale' else 'DA GUARDARE'}")
    f = next((x for x in funzione if x["nome"] == "FERMI"), None)
    if f:
        righe.append(f"  FERMI: {f['classe']} forza={f['forza']} "
                     f"{'OK' if f['classe'] == 'potenziale' and f['forza'] >= 2 else 'DA GUARDARE'}")
    vicino_fermi = sorted([x for x in funzione if x["tipo"] == "osm_pubblico" and x["classe"] == "potenziale"
                           and (x["posti"] or 0) >= 200
                           and haversine_m(45.0766, 7.5903, x["lat"], x["lon"]) <= 500],
                          key=lambda x: -(x["posti"] or 0))
    righe.append(f"  grandi parcheggi OSM gratuiti vicino a Fermi (potenziale): {len(vicino_fermi)}")
    for x in vicino_fermi[:6]:
        righe.append(f"     {x['posti']} posti, {round(haversine_m(45.0766, 7.5903, x['lat'], x['lon']))} m, "
                     f"forza={x['forza']} ({'OK' if x['classe'] == 'potenziale' else 'DA GUARDARE'})")
    for nome in ("STURA", "CAIO MARIO", "SOFIA", "VENCHI UNICA"):
        f = next((x for x in funzione if x["nome"] == nome), None)
        if f:
            righe.append(f"  {nome}: {f['classe']} ({f['motivo']}, firma {f['uso']}) "
                         f"{'OK' if f['classe'] == 'solo_sulla_carta' else 'DA GUARDARE'}")
    di_fatto = [f for f in funzione if f["classe"] == "interscambio_di_fatto"]
    righe.append("")
    righe.append(f"== Parcheggi 'interscambio di fatto': {len(di_fatto)} ==")
    for f in sorted(di_fatto, key=lambda f: -(f["posti"] or 0)):
        righe.append(f"  {str(f['posti'] or '-'):>5} posti  {f['nome'][:30]:30s} zona={f['zona_imq'] or '-':5s} "
                     f"forza={f['forza']}{' (di fatto, senza nodo ne asse vicino)' if f['forza'] == 0 else ''}")
    righe.append("")
    righe.append("== Limiti ==")
    righe.append("- La 'zona centrale' Q001-Q009 e' una scelta provvisoria: vedi la tabella di sensibilita'.")
    righe.append("- Le firme del riempimento vengono da 2 giorni feriali.")
    righe.append("- La vicinanza e' in linea d'aria, non a piedi.")
    RAP_FUNZ.parent.mkdir(parents=True, exist_ok=True)
    RAP_FUNZ.write_text("\n".join(righe) + "\n", encoding="utf-8")

    print(f"Scritto: {OUT_NODI}")
    print(f"Scritto: {OUT_FUNZ}")
    print(f"Scritto: {RAP_NODI}")
    print(f"Scritto: {RAP_FUNZ}")
    print(f"nodi forti: {n_forti} su {len(nodi)}; tipi: {dict(n_tipi)}")
    print(f"classi parcheggi: {dict(conteggi)}")
    print(f"motivi: {dict(conteggi_motivo)}")
    for nome in ("VENCHI UNICA", "SOFIA", "FERMI", "STURA", "CAIO MARIO", "MOLINETTE"):
        f = next((x for x in funzione if x["nome"] == nome), None)
        if f:
            print(f"  {nome}: {f['classe']} / {f['motivo']} (uso={f['uso']}, forza={f['forza']}, "
                  f"zona={f['zona_imq']}, dist={f['dist_nodo_forte_m']} m, strada={f['strada']})")


if __name__ == "__main__":
    sys.exit(main())
