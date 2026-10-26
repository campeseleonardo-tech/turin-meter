#!/usr/bin/env python3
"""
25_risultato6_interscambio.py  -  Risultato 6: copertura dei parcheggi di interscambio
esistenti (Stura, Caio Mario, Sofia, Venchi Unica) rispetto alle fermate GTT piu'
critiche per pendolarismo. NON propone nuovi siti: solo analisi di copertura.

Per ogni fermata calcola tre segnali, ciascuno portato su scala 0-100 per percentile
(posizione relativa fra tutte le fermate, non un min-max sensibile a un singolo
valore estremo; valori uguali hanno lo stesso percentile), poi il punteggio di
criticita' e' la MEDIA semplice dei tre:

  (a) periferia/ingresso  <- punteggio del corridoio piu' vicino (data/processed/importanza_vie.json)
  (b) hub di linee forti  <- corse/ora nell'ora di punta, dal GTFS, giorno tipo feriale 2026-10-12
  (c) pendolarismo        <- flusso IMQ simmetrico Torino<->cintura della zona IMQ di appartenenza

Le fermate nel percentile piu' alto (soglia --percentile-critiche, default 90) sono le
"fermate critiche", escluse quelle del centro (--escludi-zone, default Q001: un
interscambio serve all'ingresso in citta', non in centro; restano nel calcolo dei
percentili). Per ciascuna si controlla la copertura (deciso con Leo il 14/10): c'e' un
parcheggio di interscambio entro --raggio-copertura-m (default 200 m, in linea d'aria)?
Se si', e' coperta: oltre, non ha senso lasciare l'auto li' e proseguire a piedi.

Parcheggi (vedi sviluppo/note_tecniche/R6_parcheggi.md): elenco e coordinate da 5T get_pk
(data/raw/5t_get_pk_*.xml, il piu' recente). "Interscambio ufficiale" = segnato SI nel
file del Comune (Stura, Caio Mario, Sofia, Venchi Unica) + Fermi (Collegno, capolinea
metro: fuori Comune, aggiunto a mano). Gli altri garage in struttura sono riportati a
parte (solo informazione, non contano per la copertura). Esclusi i posti camper.

Uso:
    python scripts\\25_risultato6_interscambio.py --prova
        Limita l'elaborazione a un campione delle fermate (le prime 400 per stop_id),
        per un controllo rapido in 1-2 minuti.
    python scripts\\25_risultato6_interscambio.py
        Giro completo su tutte le fermate.

Output:
    data/processed/risultato6_interscambio.json
    docs/rapporti/RAPPORTO_RISULTATO6.txt   <-- controlla questo prima di usare i dati
"""
import argparse
import csv
import io
import json
import math
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comuni import haversine_m, percentile_rank  # noqa: E402  (uguali alle copie che stavano qui)

AQUI = Path(__file__).resolve().parent


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    candidata = Path.home() / "Desktop" / "GTT"
    if candidata.is_dir():
        return candidata
    return AQUI.parent


RADICE = trova_radice()
GTFS_ZIP = RADICE / "data" / "raw" / "gtt_gtfs_20261003_224530.zip"
IMPORTANZA_VIE = RADICE / "data" / "processed" / "importanza_vie.json"
IMQ_OD = RADICE / "data" / "processed" / "imq_od.json"
IMQ_ZONE_GEO = RADICE / "data" / "processed" / "imq_zone_geo.json"
PARCHEGGI_5T_GLOB = "5t_get_pk_*.xml"
PARCHEGGI_ZIP = RADICE / "data" / "raw" / "parcheggi_accesso_controllato_csv.zip"
PARCHEGGI_CSV = "parcheggi_accesso_controllato.csv"
OUT = RADICE / "data" / "processed" / "risultato6_interscambio.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_RISULTATO6.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

INTERSCAMBIO_A_MANO = {"FERMI"}  # fuori Comune di Torino, non nel file del Comune
GIORNO_TIPO = "20261012"  # stesso giorno tipo feriale usato in 18_accessibilita.py
GIORNI_SETTIMANA = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def dist_punto_segmento_m(plat, plon, alat, alon, blat, blon):
    """Distanza approssimata punto-segmento usando proiezione piana locale
    (equirettangolare, con correzione coseno latitudine) - adeguata su scala
    cittadina/cintura (poche decine di km), non per distanze globali."""
    coslat = math.cos(math.radians((alat + blat) / 2))
    ax, ay = alon * coslat, alat
    bx, by = blon * coslat, blat
    px, py = plon * coslat, plat
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        t = 0.0
    else:
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    qx, qy = ax + t * dx, ay + t * dy
    # converto la differenza in metri usando haversine fra il punto e la proiezione,
    # ricostruendo lat/lon della proiezione
    qlat, qlon = qy, qx / coslat if coslat else qx
    return haversine_m(plat, plon, qlat, qlon)


# --- A: corridoi (da 24_importanza_vie.py) -------------------------------------------

def carica_corridoi():
    if not IMPORTANZA_VIE.exists():
        sys.exit(f"Non trovo {IMPORTANZA_VIE} — lancia prima 24_importanza_vie.py.")
    d = json.loads(IMPORTANZA_VIE.read_text(encoding="utf-8"))
    return d["corridoi"]


def corridoio_piu_vicino(lat, lon, corridoi, raggio_max_m=150):
    """Ritorna (nome_corridoio, punteggio, distanza_m) del corridoio piu' vicino entro
    raggio_max_m, altrimenti (None, 1, None) — fuori da un corridoio noto, trattata
    come via locale minore (punteggio base 1)."""
    migliore = None
    migliore_d = raggio_max_m
    for c in corridoi:
        if "_riquadri" not in c:  # calcolati una volta sola per corridoio
            c["_riquadri"] = [(min(p[0] for p in seg), max(p[0] for p in seg),
                               min(p[1] for p in seg), max(p[1] for p in seg)) for seg in c["geometria"]]
        for seg, (la0, la1, lo0, lo1) in zip(c["geometria"], c["_riquadri"]):
            # scarto veloce: se il punto e' fuori dal riquadro di TUTTI i punti del
            # segmento (allargato di ~1 km), salta. Con i soli estremi si perdevano i
            # tratti lunghi che passano vicino al punto solo a meta' percorso.
            if lat < la0 - 0.01 or lat > la1 + 0.01 or lon < lo0 - 0.015 or lon > lo1 + 0.015:
                continue
            for i in range(len(seg) - 1):
                d = dist_punto_segmento_m(lat, lon, seg[i][0], seg[i][1], seg[i + 1][0], seg[i + 1][1])
                if d < migliore_d:
                    migliore_d = d
                    migliore = c
    if migliore is None:
        return None, 1, None
    return migliore["nome"], migliore["punteggio"], migliore_d


# --- B: GTFS --------------------------------------------------------------------------

def servizi_attivi_oggi(zf):
    giorno = GIORNO_TIPO
    colonna = GIORNI_SETTIMANA[5]  # placeholder, sovrascritto sotto dal calcolo reale
    import datetime
    data = datetime.date(int(giorno[:4]), int(giorno[4:6]), int(giorno[6:8]))
    colonna = GIORNI_SETTIMANA[data.weekday()]

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
    """Ritorna (fermate: {stop_id:(lat,lon,nome)}, corse_ora_punta: {stop_id: int})."""
    zf = zipfile.ZipFile(GTFS_ZIP)

    attivi = servizi_attivi_oggi(zf)
    print(f"  servizi attivi il {GIORNO_TIPO}: {len(attivi)}")

    trip_attivo = set()
    with zf.open("trips.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            if r["service_id"] in attivi:
                trip_attivo.add(r["trip_id"])
    print(f"  corse attive il {GIORNO_TIPO}: {len(trip_attivo)}")

    fermate = {}
    with zf.open("stops.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            try:
                fermate[r["stop_id"]] = (float(r["stop_lat"]), float(r["stop_lon"]), r["stop_name"])
            except (TypeError, ValueError):
                continue

    conteggio = {}  # stop_id -> {ora: set(trip_id)}
    with zf.open("stop_times.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            tid = r["trip_id"]
            if tid not in trip_attivo:
                continue
            sid = r["stop_id"]
            orario = r.get("arrival_time") or r.get("departure_time") or ""
            if not orario:
                continue
            try:
                ora = int(orario.split(":")[0]) % 24  # GTFS puo' avere ore >=24 (dopo mezzanotte)
            except ValueError:
                continue
            conteggio.setdefault(sid, {}).setdefault(ora, set()).add(tid)

    corse_ora_punta = {
        sid: max(len(trips) for trips in per_ora.values())
        for sid, per_ora in conteggio.items()
    }
    return fermate, corse_ora_punta


# --- C: zone IMQ e pendolarismo simmetrico ---------------------------------------------

def dentro_poligono(lat, lon, anelli):
    """Ray casting; 'anelli' e' una lista di anelli [[lat,lon],...] (puo' averne piu' di
    uno se la zona ha piu' parti); True se il punto e' dentro ALMENO un anello."""
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
    geo = json.loads(IMQ_ZONE_GEO.read_text(encoding="utf-8"))
    zone = []
    for z in geo:
        g = z["g"]
        if isinstance(g, str):
            g = json.loads(g)
        # normalizzo a lista-di-anelli: alcuni formati GeoJSON-like hanno un livello di
        # nesting in piu' (poligono con buchi, o multipoligono)
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


def punteggio_pendolari_per_zona():
    """Formula simmetrica confermata il 14/10: per ogni zona, somma dei flussi OD che
    attraversano il confine Torino/cintura (un capo e' un quartiere 'Q0xx', l'altro un
    comune di cintura) e toccano quella zona, contando entrambe le direzioni."""
    d = json.loads(IMQ_OD.read_text(encoding="utf-8"))
    od = d["od"]["tot"]
    punteggio = {}
    for o, dst, val, n, flag in od:
        if not o or not dst:
            continue
        o_torino, d_torino = o.startswith("Q"), dst.startswith("Q")
        if o_torino == d_torino:
            continue  # niente attraversamento di confine: non conta
        punteggio[o] = punteggio.get(o, 0.0) + val
        punteggio[dst] = punteggio.get(dst, 0.0) + val
    return punteggio


# --- D: parcheggi (5T get_pk + flag interscambio dal Comune) ----------------------------

def nomi_interscambio_comune():
    """Nomi dei parcheggi segnati come interscambio / park&ride nel file del Comune."""
    with zipfile.ZipFile(PARCHEGGI_ZIP) as zf, zf.open(PARCHEGGI_CSV) as f:
        righe = list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"), delimiter=";"))
    return {r.get("DENOMINAZI", "").strip().upper() for r in righe
            if r.get("INTERSCAMB") == "SI" or r.get("PARK_RIDE") == "SI"}


def carica_parcheggi():
    file_pk = sorted((RADICE / "data" / "raw").glob(PARCHEGGI_5T_GLOB))
    if not file_pk:
        sys.exit(f"Manca data/raw/{PARCHEGGI_5T_GLOB} (copia di https://opendata.5t.torino.it/get_pk).")
    radice = ET.parse(file_pk[-1]).getroot()
    interscambio = nomi_interscambio_comune() | INTERSCAMBIO_A_MANO
    parcheggi = []
    for el in radice.iter():
        if el.tag.rsplit("}", 1)[-1] != "PK_data":
            continue
        a = el.attrib
        nome = a.get("Name", "").strip()
        if "CAMPER" in nome.upper():
            continue
        parcheggi.append({
            "id": a.get("ID"), "nome": nome, "posti": int(a.get("Total") or 0),
            "lat": float(a["lat"]), "lon": float(a["lng"]),
            "interscambio": nome.upper() in interscambio,
        })
    trovati = {p["nome"].upper() for p in parcheggi if p["interscambio"]}
    mancanti = sorted(interscambio - trovati)
    return parcheggi, file_pk[-1].name, mancanti


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true", help="campione di 400 fermate, per un controllo rapido")
    ap.add_argument("--percentile-critiche", type=float, default=90.0,
                    help="percentile minimo di punteggio_criticita' per essere 'fermata critica' (default 90)")
    ap.add_argument("--escludi-zone", default="Q001",
                    help="zone IMQ (separate da virgola) le cui fermate non possono essere critiche (default Q001 centro)")
    ap.add_argument("--raggio-copertura-m", type=float, default=200.0,
                    help="distanza massima a piedi (linea d'aria, m) fermata-parcheggio per dirla coperta (default 200)")
    args = ap.parse_args()
    zone_escluse = {z.strip() for z in args.escludi_zone.split(",") if z.strip()}

    for percorso in (IMPORTANZA_VIE, IMQ_OD, IMQ_ZONE_GEO, GTFS_ZIP, PARCHEGGI_ZIP):
        if not percorso.exists():
            sys.exit(f"Manca: {percorso}")

    print("Carico i corridoi (importanza vie)...")
    corridoi = carica_corridoi()
    print(f"  {len(corridoi)} corridoi.")

    print("Leggo il GTFS (corse/ora per fermata, giorno tipo feriale)...")
    fermate_gtfs, corse_ora_punta = leggi_gtfs()
    print(f"  {len(fermate_gtfs)} fermate, {len(corse_ora_punta)} con almeno una corsa.")

    stop_ids = sorted(fermate_gtfs.keys())
    if args.prova:
        stop_ids = stop_ids[:400]
        print(f"  [--prova] limito a {len(stop_ids)} fermate.")

    print("Carico le zone IMQ e calcolo il punteggio pendolari per zona...")
    zone_imq = carica_zone_imq()
    punteggio_zona = punteggio_pendolari_per_zona()
    print(f"  {len(zone_imq)} zone, {len(punteggio_zona)} con punteggio pendolari.")

    print("Assegno ogni fermata a corridoio e zona IMQ...")
    record = {}
    for sid in stop_ids:
        lat, lon, nome = fermate_gtfs[sid]
        nome_corr, punt_corr, dist_corr = corridoio_piu_vicino(lat, lon, corridoi)
        cod_zona = zona_di(lat, lon, zone_imq)
        record[sid] = {
            "stop_id": sid, "nome": nome, "lat": lat, "lon": lon,
            "corridoio": nome_corr, "punteggio_corridoio": punt_corr,
            "distanza_corridoio_m": dist_corr,
            "zona_imq": cod_zona,
            "pendolari_raw": punteggio_zona.get(cod_zona, 0.0),
            "corse_ora_punta": corse_ora_punta.get(sid, 0),
        }

    print("Normalizzo i tre segnali per percentile e calcolo il punteggio di criticita'...")
    perc_corridoio = percentile_rank({k: v["punteggio_corridoio"] for k, v in record.items()})
    perc_corse = percentile_rank({k: v["corse_ora_punta"] for k, v in record.items()})
    perc_pend = percentile_rank({k: v["pendolari_raw"] for k, v in record.items()})
    for sid, r in record.items():
        r["perc_corridoio"] = perc_corridoio[sid]
        r["perc_corse_ora"] = perc_corse[sid]
        r["perc_pendolari"] = perc_pend[sid]
        r["punteggio_criticita"] = (perc_corridoio[sid] + perc_corse[sid] + perc_pend[sid]) / 3.0

    valori_crit = [r["punteggio_criticita"] for r in record.values()]
    valori_crit.sort()
    idx = max(0, min(len(valori_crit) - 1, round(args.percentile_critiche / 100 * (len(valori_crit) - 1))))
    soglia_critica = valori_crit[idx]
    for r in record.values():
        r["in_zona_esclusa"] = r["zona_imq"] in zone_escluse
        r["fermata_critica"] = r["punteggio_criticita"] >= soglia_critica and not r["in_zona_esclusa"]

    print("Carico i parcheggi (5T) e segno quelli di interscambio...")
    parcheggi, file_pk, mancanti = carica_parcheggi()
    for p in parcheggi:
        p["corridoio"], _, _ = corridoio_piu_vicino(p["lat"], p["lon"], corridoi)
    inter = [p for p in parcheggi if p["interscambio"]]
    print(f"  {len(parcheggi)} parcheggi da {file_pk}, di cui interscambio: " + ", ".join(p["nome"] for p in inter))
    if mancanti:
        print(f"  ATTENZIONE: interscambio non trovati in 5T: {', '.join(mancanti)}")

    print("Calcolo la copertura (parcheggio entro il raggio a piedi)...")
    raggio = args.raggio_copertura_m
    for r in record.values():
        vicini = sorted(
            ((haversine_m(r["lat"], r["lon"], p["lat"], p["lon"]), i) for i, p in enumerate(parcheggi)),
        )
        vicini = [(d, parcheggi[i]) for d, i in vicini if d <= raggio]
        inter_vicino = next(((d, p) for d, p in vicini if p["interscambio"]), None)
        r["parcheggio_interscambio"] = inter_vicino[1]["nome"] if inter_vicino else None
        r["distanza_interscambio_m"] = round(inter_vicino[0]) if inter_vicino else None
        r["garage_vicini"] = [p["nome"] for d, p in vicini if not p["interscambio"]]
        r["coperta"] = (inter_vicino is not None) if r["fermata_critica"] else None
    for p in parcheggi:
        entro = [r for r in record.values() if haversine_m(r["lat"], r["lon"], p["lat"], p["lon"]) <= raggio]
        p["fermate_entro_raggio"] = len(entro)
        p["critiche_entro_raggio"] = sum(1 for r in entro if r["fermata_critica"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "modalita_prova": args.prova,
        "giorno_tipo": GIORNO_TIPO,
        "percentile_critiche": args.percentile_critiche,
        "zone_escluse": sorted(zone_escluse),
        "raggio_copertura_m": raggio,
        "fonte_parcheggi": file_pk,
        "parcheggi": parcheggi,
        "fermate": list(record.values()),
    }, ensure_ascii=False), encoding="utf-8")

    critiche = [r for r in record.values() if r["fermata_critica"]]
    coperte = [r for r in critiche if r["coperta"]]
    scoperte = [r for r in critiche if r["coperta"] is False]
    escluse_sopra = [r for r in record.values() if r["in_zona_esclusa"] and r["punteggio_criticita"] >= soglia_critica]

    righe = []
    righe.append("RAPPORTO RISULTATO 6 — copertura parcheggi di interscambio")
    righe.append(f"modalita': {'PROVA (campione 400 fermate)' if args.prova else 'completa'}")
    righe.append(f"fermate analizzate: {len(record)}")
    righe.append(f"soglia 'fermata critica': percentile {args.percentile_critiche} "
                 f"(punteggio >= {soglia_critica:.1f} su 100)")
    righe.append(f"zone escluse (centro): {', '.join(sorted(zone_escluse)) or '-'}  "
                 f"-> fermate sopra soglia ma escluse: {len(escluse_sopra)}")
    righe.append(f"fermate critiche (fuori dalle zone escluse): {len(critiche)}")
    righe.append(f"  coperte (parcheggio di interscambio entro {raggio:.0f} m): {len(coperte)}")
    righe.append(f"  SCOPERTE: {len(scoperte)}")
    righe.append(f"  scoperte ma con un garage in struttura entro {raggio:.0f} m (solo informazione): "
                 f"{sum(1 for r in scoperte if r['garage_vicini'])}")
    righe.append("")
    righe.append(f"== Parcheggi di interscambio (fonte {file_pk}) ==")
    for p in inter:
        righe.append(f"  {p['nome']:18s} posti={p['posti']:>5}  fermate entro {raggio:.0f} m: "
                     f"{p['fermate_entro_raggio']:3d} (critiche {p['critiche_entro_raggio']})  via vicina: {p['corridoio']}")
    if mancanti:
        righe.append(f"  ATTENZIONE: interscambio non trovati nel file 5T: {', '.join(mancanti)}")
    righe.append(f"  (altri {len(parcheggi) - len(inter)} garage in struttura: solo informazione)")
    righe.append("")
    righe.append("== Fermate critiche COPERTE ==")
    for r in sorted(coperte, key=lambda r: -r["punteggio_criticita"]):
        righe.append(f"  [{r['punteggio_criticita']:5.1f}] {r['nome']:40s} <- {r['parcheggio_interscambio']} "
                     f"({r['distanza_interscambio_m']} m)")
    righe.append("")
    righe.append("== Prime 25 fermate critiche SCOPERTE (per punteggio) ==")
    scoperte.sort(key=lambda r: -r["punteggio_criticita"])
    for r in scoperte[:25]:
        righe.append(
            f"  [{r['punteggio_criticita']:5.1f}] {r['nome']:40s} corridoio={(r['corridoio'] or '-')[:32]:32s} "
            f"corse_ora={r['corse_ora_punta']:3d}  zona_imq={r['zona_imq'] or '-'}"
        )
    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")

    print(f"Scritto: {OUT}")
    print(f"Scritto: {RAPPORTO}  <-- controlla questo prima di usare i dati")


if __name__ == "__main__":
    sys.exit(main())
