#!/usr/bin/env python3
"""Accessibilita' per sezione di censimento (motore R5/r5py).
Scrive data/processed/accessibilita.json + docs/rapporti/RAPPORTO_ACCESSIBILITA.txt.

Scelte (vedi sviluppo/note_tecniche/METODO.md):
- D1: dentro Torino solo il catalogo comunale; i servizi OSM (script 20) entrano
  soltanto nei lotti che contengono sezioni FUORI Torino.
- D2: cammino 4,8 km/h = 80 m/min (anche per i margini).
- D3: destinazioni accorpate in celle di ~50 m; il peso della cella dice quanti
  punti originali contiene, cosi' il conteggio resta identico (r5py non pesa le
  destinazioni, quindi il peso e' applicato qui, lato conteggio).
- D4: ore del TP 08/14/23/02 di lunedi' 12/10/2026.
- Con --salva-tappe si scrive un file ogni --salva-ogni lotti in data/processed/
  accessibilita_parziale/, con dentro TUTTI i lotti calcolati da quel gruppo (corretto
  il 14/10: prima conteneva solo l'ultimo lotto, e al rilancio si rifaceva ~80% del
  lavoro). Se il giro si interrompe, al rilancio i lotti gia' salvati vengono
  ricaricati e non ricalcolati (i file vecchi da un lotto solo restano validi).
- Centroidi corretti: le sezioni in SEZIONI_FUORI_RETE (a piedi quasi a zero
  per un centroide lontano dalla rete) vengono spostate sul nodo OSM piu'
  vicino entro RAGGIO_CENTROIDE metri (cache in centroidi_fuori_rete.json).
"""
import argparse
import datetime as dt
import json
import math
import os
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402

RADICE = Path(__file__).resolve().parent.parent
SEZIONI = RADICE / "data/processed/sezioni_torino.json"
CATALOGO = RADICE / "data/processed/catalogo"
GTFS = RADICE / "data/raw/gtt_gtfs_20261003_224530.zip"
OSM_TAGLIATO = RADICE / "data/otp/rete/torino_cintura.osm.pbf"
JAVA_HOME = RADICE / "data/otp/jdk-25.0.4.1+1-jre"
OUT = RADICE / "data/processed/accessibilita.json"
RAPPORTO = RADICE / "docs/rapporti/RAPPORTO_ACCESSIBILITA.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
DIR_PARZ = RADICE / "data/processed/accessibilita_parziale"
CENTROIDI = RADICE / "data/processed/centroidi_fuori_rete.json"

GRUPPI = ["scuole", "salute", "cibo", "fermate", "verde"]

# Sezioni di Torino con R5 sotto il 20% della linea d'aria (Fase 4, 11/10):
# sospetto centroide in area senza strade (parco, cortile, ferrovia).
SEZIONI_FUORI_RETE = {
    "12720002588": "R5 a piedi 0 con 4 destinazioni in linea d'aria (Fase 4)",
    "12720004264": "R5 a piedi 11% della linea d'aria (Fase 4)",
    "12720005521": "R5 a piedi 0 con prove in linea d'aria (Fase 4)",
    "12720006601": "R5 a piedi 6% della linea d'aria (Fase 4)",
    # via Chieti (R1 v2, 20/10): fermata GTT a 75-179 m che il calcolo a piedi non raggiunge
    "12720005328": "via Chieti: zero fermate a piedi con una fermata a 179 m (R1 v2)",
    "12720000972": "via Chieti: zero fermate a piedi con una fermata a 75 m (R1 v2)",
}
RAGGIO_CENTROIDE = 200  # metri: raggio in cui si cerca il nodo OSM piu' vicino

TAG_VERDE = {
    "leisure": {"park", "garden", "playground", "pitch", "dog_park", "golf_course"},
    "landuse": {"cemetery", "forest", "grass", "recreation_ground", "village_green", "meadow"},
}


def log(msg):
    print(msg, flush=True)


def tieni_pc_sveglio():
    """Chiede a Windows di non sospendere il PC finche' lo script gira.
    Va ALL'INIZIO del calcolo, non alla fine."""
    if sys.platform == "win32":
        import ctypes
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        esito = ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED)  # SetThreadExecutionState sta in kernel32
        log("PC tenuto sveglio durante il calcolo"
            if esito else "ATTENZIONE: richiesta anti-sospensione non accettata")


def d_aria_m(la0, lo0, la1, lo1):
    """Distanza in linea d'aria in metri (equirettangolare, ok entro la citta')."""
    dx = (lo1 - lo0) * 111320.0 * math.cos(math.radians(la0))
    dy = (la1 - la0) * 110570.0
    return math.hypot(dx, dy)


def centroide(anello):
    """Centroide d'area di un anello [[lat,lon],...]; None se area nulla."""
    a = cx = cy = 0.0
    n = len(anello)
    for i in range(n - 1):
        x0, y0 = anello[i]
        x1, y1 = anello[i + 1]
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    if abs(a) < 1e-15:
        return None
    # anelli [lat,lon]: x=lat, y=lon -> centroide (lat, lon)
    return (cx / (3 * a), cy / (3 * a))


def carica_sezioni():
    sezioni = json.loads(SEZIONI.read_text(encoding="utf-8"))
    out = []
    for s in sezioni:
        if s.get("p", 0) <= 0 or not s.get("g"):
            continue
        cen = centroide(s["g"][0]) or (s["g"][0][0][0], s["g"][0][0][1])
        out.append({
            "id": s["id"],
            "comune": s["c"],
            "res": s["p"],
            "lat": cen[0],
            "lon": cen[1],
            "torino": s["c"] == 1272  # True = dentro il Comune di Torino
        })
    return out


def punti_da_catalogo(gruppo):
    d = json.loads((CATALOGO / f"{gruppo}.json").read_text(encoding="utf-8"))
    punti = []
    for ds in d["dati"]:
        for el in ds.get("elementi", []):
            try:
                punti.append((float(el[0]), float(el[1])))
            except (TypeError, ValueError, IndexError):
                continue
    return punti


def fermate_gtfs():
    import csv as csvmod
    fermate = []
    with zipfile.ZipFile(GTFS) as z:
        righe = z.read("stops.txt").decode("utf-8-sig").splitlines()
    lettori = csvmod.reader(righe)
    intest = next(lettori)
    i_la, i_lo = intest.index("stop_lat"), intest.index("stop_lon")
    i_lt = intest.index("location_type") if "location_type" in intest else None
    for c in lettori:
        if len(c) <= max(i_la, i_lo):
            continue
        if i_lt is not None and c[i_lt] not in ("", "0"):
            continue
        try:
            fermate.append((float(c[i_la]), float(c[i_lo])))
        except ValueError:
            continue
    return fermate


def verde_da_osm():
    import osmium
    punti = []

    class Verde(osmium.SimpleHandler):
        def way(self, w):
            if not w.is_closed():
                return
            if (w.tags.get("leisure") in TAG_VERDE["leisure"]
                    or w.tags.get("landuse") in TAG_VERDE["landuse"]):
                la = lo = 0.0
                n = 0
                for nd in w.nodes:
                    if nd.location.valid():
                        la += nd.location.lat
                        lo += nd.location.lon
                        n += 1
                if n >= 3:
                    punti.append((la / n, lo / n))

    Verde().apply_file(str(OSM_TAGLIATO), locations=True)
    return punti


def aggrega_punti(punti, margine_metri=50):
    """D3: raggruppa i punti in celle di ~margine_metri metri.
    Esce [(cella_lat, cella_lon, peso)] dove peso = punti originali nella cella:
    nel conteggio moltiplicare per peso equivale a contare i punti uno per uno
    (r5py non pesa le destinazioni, il peso e' applicato lato conteggio)."""
    cella = margine_metri / 111000.0
    celle = {}
    for lat, lon in punti:
        chiave = (round(lat / cella), round(lon / cella))
        celle[chiave] = celle.get(chiave, 0) + 1
    return [(k[0] * cella, k[1] * cella, pes) for k, pes in celle.items()]


def carica_destinazioni(margine_metri, osm_cintura):
    """Destinazioni per gruppo, gia' accorpate in celle: [(lat, lon, peso, da_osm)].
    I punti OSM della cintura restano SEPARATI (riservati ai lotti fuori Torino)."""
    grezzi = {
        "scuole": punti_da_catalogo("istruzione"),
        "salute": punti_da_catalogo("salute"),
        "cibo": punti_da_catalogo("commercio"),
        "fermate": fermate_gtfs(),
        "verde": verde_da_osm(),
    }
    dest = {}
    for g in GRUPPI:
        celle = aggrega_punti(grezzi[g], margine_metri)
        dest[g] = [(la, lo, pes, False) for (la, lo, pes) in celle]
        n_osm = 0
        if g in osm_cintura and osm_cintura[g]:
            osm_agg = aggrega_punti(osm_cintura[g], margine_metri)
            dest[g].extend([(la, lo, pes, True) for (la, lo, pes) in osm_agg])
            n_osm = len(osm_cintura[g])
        log(f"  {g}: {len(grezzi[g])} punti (+{n_osm} OSM) -> "
            f"{len(dest[g])} celle (aggregazione ~{margine_metri} m)")
    return dest


def carica_servizi_osm_cintura():
    """Servizi OSM della cintura, creati dallo script 20."""
    file_osm = RADICE / "data/processed/servizi_osm_cintura.json"
    if file_osm.exists():
        data = json.loads(file_osm.read_text(encoding="utf-8"))
        osm_servizi = {}
        for group in ("scuole", "salute", "cibo"):
            osm_servizi[group] = [(p["lat"], p["lon"]) for p in data["servizi"][group]]
        return osm_servizi
    log("ATTENZIONE: servizi_osm_cintura.json non trovato: cintura senza scuole/salute/cibo")
    return {"scuole": [], "salute": [], "cibo": []}


def correggi_centroidi(sezioni):
    """Sposta l'origine delle sezioni in SEZIONI_FUORI_RETE sul nodo OSM piu'
    vicino (entro RAGGIO_CENTROIDE metri). Cache: data/processed/centroidi_fuori_rete.json."""
    bersagli = {s["id"]: (s["lat"], s["lon"]) for s in sezioni
                if s["id"] in SEZIONI_FUORI_RETE}
    if not bersagli or not SEZIONI_FUORI_RETE:
        return
    if CENTROIDI.exists():
        corretti = json.loads(CENTROIDI.read_text(encoding="utf-8"))
    else:
        import osmium

        # Modo dello sistemare: NON basta il nodo OSM piu' vicino qualunque
        # (puo' stare su autostrada/ferrovia, che R5 non pedona). Si cerca il
        # nodo piu' vicino che appartiene a una way pedonabile.
        WAY_PEDONABILI = {
            "primary", "secondary", "tertiary", "residential", "unclassified",
            "service", "road", "footway", "path", "pedestrian", "living_street",
            "track", "steps", "cycleway",
        }

        class Vicinissimi(osmium.SimpleHandler):
            def __init__(self):
                super().__init__()
                self.migliori = {k: (None, None, math.inf) for k in bersagli}

            def way(self, w):
                if w.tags.get("highway") not in WAY_PEDONABILI:
                    return
                for nd in w.nodes:
                    if not nd.location.valid():
                        continue
                    la = nd.location.lat
                    lo = nd.location.lon
                    for k, (la0, lo0) in bersagli.items():
                        if abs(la - la0) > 0.02 or abs(lo - lo0) > 0.02:
                            continue
                        dist = d_aria_m(la0, lo0, la, lo)
                        if dist < self.migliori[k][2]:
                            self.migliori[k] = (la, lo, dist)

        log(f"Correzione centroidi: cerco le way pedonabili piu' vicine a {len(bersagli)} "
            "sezioni (una passata sul taglio OSM, poi resta in cache)...")
        h = Vicinissimi()
        h.apply_file(str(OSM_TAGLIATO), locations=True)
        corretti = {}
        for k, (la, lo, dist) in h.migliori.items():
            if la is not None and dist <= RAGGIO_CENTROIDE:
                corretti[k] = {"lat": round(la, 6), "lon": round(lo, 6), "distanza": round(dist)}
            else:
                corretti[k] = {"lat": None, "lon": None,
                               "distanza": None if dist == math.inf else round(dist),
                               "nota": "nessun nodo OSM entro il raggio"}
        CENTROIDI.write_text(json.dumps(corretti, indent=1), encoding="utf-8")
        log(f"  cache scritta: {CENTROIDI.name}")
    for s in sezioni:
        c = corretti.get(s["id"])
        if not c:
            continue
        if c.get("lat") is not None:
            log(f"  {s['id']}: centroide a {c['distanza']} m dalla rete, origine spostata "
                f"({s['lat']:.5f},{s['lon']:.5f} -> {c['lat']},{c['lon']})")
            s["lat"], s["lon"] = c["lat"], c["lon"]
        else:
            log(f"  {s['id']}: nessun nodo OSM entro {RAGGIO_CENTROIDE} m, resta "
                "quasi a zero (vedi rapporto)")


def avvia_rete():
    comuni.imposta_java(JAVA_HOME)   # la cartella data/otp/jdk-... se c'e', altrimenti il Java del sistema
    # heap fisso: la macchina ha 8 GB, Python e R5 devono convivere
    os.environ.setdefault("_JAVA_OPTIONS", "-Xmx3g")
    import geopandas as gpd
    from r5py import TransportNetwork
    log("Rete R5 in costruzione (prima volta: scarica r5.jar ~ 100 MB)...")
    t0 = time.time()
    rete = TransportNetwork(str(OSM_TAGLIATO), [str(GTFS)])
    log(f"Rete R5 pronta in {time.time()-t0:.0f} s")
    return rete, gpd


def gdf_da_punti(gpd, punti, id_prefisso):
    import pandas as pd
    df = pd.DataFrame({"id": [f"{id_prefisso}{i}" for i in range(len(punti))],
                       "lat": [p[0] for p in punti], "lon": [p[1] for p in punti]})
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")


def matrice(rete, moduli, orig_gdf, dest_gdf, quando, max_time, **kwargs):
    # r5py 1.x: TravelTimeMatrix e' un GeoDataFrame calcolato al costruttore
    from r5py import TravelTimeMatrix
    return TravelTimeMatrix(
        rete, origins=orig_gdf, destinations=dest_gdf,
        departure=quando, transport_modes=moduli, max_time=max_time, **kwargs)


def lotti(origins, n):
    """Origini raggruppate a lotti spazialmente compatti (griglia + ordine)."""
    ordinate = sorted(origins, key=lambda o: (round(o["lat"] / 0.02), round(o["lon"] / 0.02)))
    for i in range(0, len(ordinate), n):
        yield ordinate[i:i + n]


def conto_per_origine(mat, orig_ids, dest_by_k, margine_gradi, origine_da_pos, cutoff_min):
    """Dal DataFrame r5py (from_id,to_id,travel_time) ricava i conteggi per
    sezione e gruppo. dest_by_k: {k: (lat, lon, gruppo, peso)}."""
    per_gruppo = {oid: {g: 0 for g in GRUPPI} for oid in orig_ids}
    for r in mat.itertuples(index=False):
        oid = str(r.from_id)
        tempo = r.travel_time
        # r5py restituisce Timedelta o minuti secondo versione: normalizzo a minuti
        if hasattr(tempo, "total_seconds"):
            tempo = tempo.total_seconds() / 60.0
        if tempo is None or (isinstance(tempo, float) and tempo != tempo):
            continue
        if tempo > cutoff_min:
            continue
        la, lo, g, pes = dest_by_k[int(str(r.to_id).removeprefix("D"))]
        la0, lo0 = origine_da_pos[oid]
        if abs(la - la0) <= margine_gradi[0] and abs(lo - lo0) <= margine_gradi[1]:
            per_gruppo[oid][g] += pes  # pes = punti originali nella cella (D3)
    return per_gruppo


# ---- salvataggio a tappe e ripresa ----

def firma_run(args, n_sezioni):
    """Identifica UNA run: cambiando un parametro i parziali vecchi vengono ignorati."""
    return {
        "giorno": args.giorno,
        "ore": args.ore,
        "cutoff_piedi": args.cutoff_piedi,
        "cutoff_tp": args.cutoff_tp,
        "velocita_piedi": args.velocita_piedi,
        "velocita_tp": args.velocita_tp,
        "campione": n_sezioni,
        "margine_metri": args.margine_metri,
        "lotto_piedi": args.lotto_piedi,
        "lotto_tp": args.lotto_tp,
    }


def salva_parziale(fase, indice_lotto, risultati, ids, firma, lotti_dentro=None):
    """Un file per gruppo di lotti: 'lotti' elenca tutti i lotti le cui sezioni sono
    in 'sezioni' (cosi' la ripresa li salta tutti, non solo l'ultimo)."""
    DIR_PARZ.mkdir(parents=True, exist_ok=True)
    path = DIR_PARZ / f"{fase}_{indice_lotto:06d}.json"
    contenuto = {
        "generato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "fase": fase,
        "lotto": indice_lotto,
        "lotti": lotti_dentro or [indice_lotto],
        "firma": firma,
        "sezioni": [risultati[oid] for oid in ids],
    }
    path.write_text(json.dumps(contenuto, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8")
    return path


def riprendi_parziali(fase, firma):
    """Lotti gia' calcolati per una fase: {lotto: {id: risultato}}.
    Ignora i file di un'altra run (firma diversa) o di formato vecchio."""
    if not DIR_PARZ.exists():
        return {}
    archivio = {}
    for p in sorted(DIR_PARZ.glob(f"{fase}_*.json")):
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            log(f"  parziale NON letto (corrotto?): {p.name}")
            continue
        if c.get("fase") != fase or c.get("firma") != firma or "lotto" not in c:
            log(f"  parziale di un'altra run ignorato: {p.name}")
            continue
        sezioni = {s["id"]: s for s in c["sezioni"]}
        for n in c.get("lotti") or [c["lotto"]]:  # file vecchi: solo "lotto"
            archivio[n] = sezioni
    return archivio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campione", type=int, default=0)
    ap.add_argument("--ore", default="8,14,23,2")
    ap.add_argument("--giorno", default="2026-10-12")
    ap.add_argument("--gtfs", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--cutoff-piedi", type=int, default=15)
    ap.add_argument("--cutoff-tp", type=int, default=45)
    ap.add_argument("--lotto-piedi", type=int, default=100)
    ap.add_argument("--lotto-tp", type=int, default=20)  # Rispetto a 40: meno memoria
    ap.add_argument("--giro-prova", action="store_true")
    ap.add_argument("--salva-tappe", action="store_true")  # salva a tappe E riprende
    ap.add_argument("--salva-ogni", type=int, default=5)  # salvataggio ogni N lotti
    ap.add_argument("--margine-metri", type=int, default=50)  # D3: celle di aggregazione
    ap.add_argument("--velocita-piedi", type=float, default=80)  # 4.8 km/h = 80 m/min
    ap.add_argument("--velocita-tp", type=float, default=4.8)  # 4.8 km/h per margine TP
    ap.add_argument("--niente-correzione-centroidi", action="store_true")
    ap.add_argument("--solo-piedi", action="store_true",
                    help="salta la parte coi mezzi pubblici (e --ore): serve per le soglie 5 e 10 minuti")
    args = ap.parse_args()
    args.ore = [] if args.solo_piedi else [int(x) for x in args.ore.split(",") if x.strip()]
    global GTFS, OUT, RAPPORTO
    if args.gtfs:
        GTFS = Path(args.gtfs)
        if not GTFS.is_absolute():
            GTFS = RADICE / GTFS
    if args.out:
        nome_out = Path(args.out).stem  # vale sia "accessibilita_piedi5" sia un percorso con .json
        OUT = RADICE / "data/processed" / f"{nome_out}.json"
        RAPPORTO = RADICE / "docs" / "rapporti" / f"RAPPORTO_{nome_out.upper()}.txt"
        RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    tieni_pc_sveglio()

    sezioni = carica_sezioni()
    log(f"Sezioni con residenti: {len(sezioni)}")
    if args.campione > 0:
        passo = max(1, len(sezioni) // args.campione)
        sezioni = sezioni[::passo][:args.campione]
        log(f"Campione: {len(sezioni)} sezioni (una ogni {passo})")

    if not args.niente_correzione_centroidi:
        correggi_centroidi(sezioni)

    osm_cintura = carica_servizi_osm_cintura()
    dest = carica_destinazioni(args.margine_metri, osm_cintura)

    # dest_piatti: (lat, lon, gruppo, peso, e_osm_cintura)
    dest_piatti = [(p[0], p[1], g, p[2], p[3]) for g in GRUPPI for p in dest[g]]
    log(f"Destinazioni totali: {len(dest_piatti)} celle (raggruppate col peso)")

    rete, gpd = avvia_rete()
    if args.giro_prova:
        log("Giro di prova: rete costruita, fermo qui.")
        return

    orig_gdf_tutte = gdf_da_punti(gpd, [(s["lat"], s["lon"]) for s in sezioni], "S")
    orig_gdf_tutte["id"] = [s["id"] for s in sezioni]
    dest_gdf_tutte = gdf_da_punti(gpd, [(p[0], p[1]) for p in dest_piatti], "D")
    origine_da_pos = {str(s["id"]): (s["lat"], s["lon"]) for s in sezioni}

    # margine in linea d'aria (lat,lon) oltre il cutoff + 20% di respiro
    km_piedi = args.cutoff_piedi * args.velocita_piedi / 1000.0  # metri/min -> km
    margine_piedi = (km_piedi / 111.32 * 1.2, km_piedi / 111.32 / 0.7071 * 1.2)
    # margine TP: 20 km in linea d'aria FISSI, indipendenti dalla velocita'
    # (verifica 11/10: il margine legato alla velocita' tagliava destinazioni che
    # nel cutoff di 45 min ci possono stare, es. di notte col treno)
    margine_tp = (20.0 / 111.32, 20.0 / 111.32 / 0.7071)

    risultati = {s["id"]: {
        "id": s["id"],
        "lat": round(s["lat"], 5),
        "lon": round(s["lon"], 5),
        "res": s["res"],
        "piedi": {},
        "tp": {}
    } for s in sezioni}

    firma = firma_run(args, len(sezioni))
    n_lotti_piedi = (len(sezioni) + args.lotto_piedi - 1) // args.lotto_piedi
    n_lotti_tp = (len(sezioni) + args.lotto_tp - 1) // args.lotto_tp
    giorno = dt.date.fromisoformat(args.giorno)
    # velocita' di cammino per R5 (km/h): PRIMA predefinita di R5 (3,6), ora quella
    # dichiarata dal piano (D2: 4,8 km/h = 80 m/min), per i percorsi a piedi e per
    # la tratte di ingresso/uscita col TP
    vel_cammino_kmh = args.velocita_piedi * 60.0 / 1000.0
    log(f"Velocita' cammino fissata a {vel_cammino_kmh:.1f} km/h "
        "(prima R5 usava i suoi 3,6 km/h)")

    in_attesa = {}  # fase -> lotti calcolati ma non ancora salvati: [(n, ids)]

    def salva(parz_fase, n, lotto, forza=False):
        """Accumula il lotto; ogni --salva-ogni lotti (o a fine fase, forza=True) scrive
        un file con TUTTI i lotti accumulati dall'ultimo salvataggio."""
        if not args.salva_tappe:
            return
        coda = in_attesa.setdefault(parz_fase, [])
        if lotto is not None:
            coda.append((n, [s["id"] for s in lotto]))
        ultimo = n_lotti_piedi if parz_fase == "piedi" else n_lotti_tp
        # anche len(coda): alla ripresa i lotti multipli di 5 sono spesso gia' salvati
        # (e saltati), e senza questa condizione la coda si svuoterebbe solo a fine fase
        if coda and (forza or n % args.salva_ogni == 0 or len(coda) >= args.salva_ogni or n == ultimo):
            ids = [i for _, gruppo in coda for i in gruppo]
            p = salva_parziale(parz_fase, coda[-1][0], risultati, ids, firma, [m for m, _ in coda])
            log(f"  salvato {p.name} (lotti {coda[0][0]}-{coda[-1][0]})")
            coda.clear()

    # ---- A PIEDI (indipendente dall'ora: R5 a piedi non usa gli orari)
    log(f"A piedi: cutoff {args.cutoff_piedi} min, velocita' {args.velocita_piedi:.0f} m/min...")
    fatti = riprendi_parziali("piedi", firma) if args.salva_tappe else {}
    if fatti:
        log(f"  ripresa: {len(fatti)} lotti a piedi gia' calcolati, li ricarico")
        for lotto_fatto in fatti.values():
            for oid, rr in lotto_fatto.items():
                if oid in risultati:
                    risultati[oid]["piedi"] = rr["piedi"]
    t0 = time.time()
    for n, lotto in enumerate(lotti(sezioni, args.lotto_piedi), 1):
        if n in fatti:
            log(f"  lotto a piedi #{n}: gia' fatto, salto")
            continue
        ids = [s["id"] for s in lotto]
        orig = orig_gdf_tutte[orig_gdf_tutte["id"].isin(ids)]
        la0 = min(s["lat"] for s in lotto) - margine_piedi[0]
        la1 = max(s["lat"] for s in lotto) + margine_piedi[0]
        lo0 = min(s["lon"] for s in lotto) - margine_piedi[1]
        lo1 = max(s["lon"] for s in lotto) + margine_piedi[1]
        dentro = [(k, p) for k, p in enumerate(dest_piatti)
                  if la0 <= p[0] <= la1 and lo0 <= p[1] <= lo1]
        dest_gdf = dest_gdf_tutte.iloc[[k for k, _ in dentro]]
        dest_by_k = {k: (p[0], p[1], p[2], p[3]) for k, p in dentro}
        quando = dt.datetime.combine(giorno, dt.time(7, 0))
        m = matrice(rete, [__import__("r5py").r5.TransportMode.WALK],
                    orig, dest_gdf, quando, dt.timedelta(minutes=args.cutoff_piedi),
                    speed_walking=vel_cammino_kmh)
        conteggi = conto_per_origine(m, ids, dest_by_k, margine_piedi, origine_da_pos,
                                     args.cutoff_piedi)
        for oid, cg in conteggi.items():
            risultati[oid]["piedi"][str(args.cutoff_piedi)] = cg
        log(f"  lotto a piedi {n}: {len(lotto)} sezioni, {len(dest_by_k)} celle dest "
            f"({time.time()-t0:.0f} s)")
        salva("piedi", n, lotto)
    salva("piedi", n_lotti_piedi, None, forza=True)  # eventuali lotti rimasti in coda

    # ---- COL TRASPORTO PUBBLICO, per ora (destinazioni STESSE per tutte le origini:
    # catalogo comunale dentro Torino + punti OSM solo fuori, vedi FIX 4)
    from r5py import TransportMode as TM
    if args.solo_piedi:
        log("--solo-piedi: parte coi mezzi pubblici saltata")
    for ora in args.ore:  # con --solo-piedi args.ore e' vuoto
        log(f"TP ore {ora:02d}:00, cutoff {args.cutoff_tp} min, velocita' {args.velocita_tp:.1f} km/h...")
        fatti = riprendi_parziali(f"tp_{ora}", firma) if args.salva_tappe else {}
        for dd in fatti.values():
            for oid, rr in dd.items():
                if oid in risultati:
                    risultati[oid]["tp"][f"{ora:02d}"] = rr["tp"][f"{ora:02d}"]
        if fatti:
            log(f"  ripresa: {len(fatti)} lotti dell'ora {ora:02d} gia' calcolati, li ricarico")
        t0 = time.time()
        for n, lotto in enumerate(lotti(sezioni, args.lotto_tp), 1):
            if n in fatti:
                log(f"  lotto {ora:02d} #{n}: gia' fatto, salto")
                continue
            ids = [s["id"] for s in lotto]
            orig = orig_gdf_tutte[orig_gdf_tutte["id"].isin(ids)]
            la0 = min(s["lat"] for s in lotto) - margine_tp[0]
            la1 = max(s["lat"] for s in lotto) + margine_tp[0]
            lo0 = min(s["lon"] for s in lotto) - margine_tp[1]
            lo1 = max(s["lon"] for s in lotto) + margine_tp[1]
            dentro = [(k, p) for k, p in enumerate(dest_piatti)
                      if la0 <= p[0] <= la1 and lo0 <= p[1] <= lo1]
            dest_gdf = dest_gdf_tutte.iloc[[k for k, _ in dentro]]
            dest_by_k = {k: (p[0], p[1], p[2], p[3]) for k, p in dentro}
            quando = dt.datetime.combine(giorno, dt.time(ora, 0))
            m = matrice(rete, [TM.TRANSIT, TM.WALK], orig, dest_gdf, quando,
                        dt.timedelta(minutes=args.cutoff_tp),
                        speed_walking=vel_cammino_kmh)
            conteggi = conto_per_origine(m, ids, dest_by_k, margine_tp, origine_da_pos,
                                         args.cutoff_tp)
            for oid, cg in conteggi.items():
                risultati[oid]["tp"][f"{ora:02d}"] = cg
            log(f"  lotto {ora:02d} #{n}: {len(lotto)} sezioni, "
                f"{len(dest_by_k)} celle dest ({time.time()-t0:.0f} s)")
            salva(f"tp_{ora}", n, lotto)
        salva(f"tp_{ora}", n_lotti_tp, None, forza=True)

    esito = {
        "generato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "avviso": "ORARIO PROGRAMMATO, non misurato: niente ritardi, capienze o "
                  "domanda. Motore R5/r5py su GTFS + OSM tagliato (17). Destinazioni accorpate "
                  "in celle di ~50 m col peso dei punti. Destinazioni uguali per tutte le "
                  "sezioni: catalogo comunale (dentro Torino) + OSM (solo punti fuori dal "
                  "Comune). " + f"Centroidi corretti per sezione: {sorted(SEZIONI_FUORI_RETE)}.",
        "parametri": {
            "solo_piedi": args.solo_piedi,
            "giorno": args.giorno,
            "ore": args.ore,
            "cutoff_piedi_min": args.cutoff_piedi,
            "cutoff_tp_min": args.cutoff_tp,
            "velocita_piedi": args.velocita_piedi,
            "velocita_tp": args.velocita_tp,
            "lotto_piedi": args.lotto_piedi,
            "lotto_tp": args.lotto_tp,
            "campione": len(sezioni),
            "margine_metri": args.margine_metri,
        },
        "gruppi": {g: len(dest[g]) for g in GRUPPI},
        "sezioni": [risultati[s["id"]] for s in sezioni],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(esito, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    log(f"Scritto {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")

    # ---- rapporto (Torino e cintura SEMPRE separate: mai mediane miste)
    def mediana(vals):
        v = sorted(vals)
        return v[len(v) // 2] if v else 0

    def comune_di(s):
        return int(str(s["id"])[:4])

    gr = {
        "Torino (comune 1272)": [s for s in esito["sezioni"] if comune_di(s) == 1272],
        "Cintura (comuni != 1272)": [s for s in esito["sezioni"] if comune_di(s) != 1272],
    }
    righe = [
        "RAPPORTO ACCESSIBILITA' (orario programmato, STIMATO - motore R5/r5py su GTFS + OSM)",
        f"generato: {esito['generato']}  giorno tipo: {args.giorno}  ore: {args.ore}",
        f"sezioni: {len(esito['sezioni'])} (Torino {len(gr['Torino (comune 1272)'])}, "
        f"cintura {len(gr['Cintura (comuni != 1272)'])})",
        f"cutoff a piedi: {args.cutoff_piedi} min ({args.velocita_piedi:.0f} m/min)  "
        + ("TP: non calcolato (--solo-piedi)" if args.solo_piedi else f"TP: {args.cutoff_tp} min"),
        f"gruppi (celle di destinazione): {esito['gruppi']}",
        "  NOTA: le destinazioni sono accorpate in celle di ~50 m con peso: il totale pesato "
        "vale il numero dei punti originali. Destinazioni STESSE per tutte le sezioni "
        "(catalogo comunale + OSM della cintura), margine TP 20 km in linea d'aria.",
        "",
    ]
    for nome, g in gr.items():
        if not g:
            continue
        righe.append(f"== {nome}: {len(g)} sezioni ==")
        righe.append("  Servizi raggiungibili A PIEDI entro "
                     f"{args.cutoff_piedi} min (mediane pesate per gruppo):")
        for grp in GRUPPI:
            righe.append(f"    {grp:8s}: {mediana([r['piedi'][str(args.cutoff_piedi)][grp] for r in g]):.0f}")
        for ora in args.ore:
            chi = f"{ora:02d}"
            righe.append(f"  COL TP alle {chi}:00 (mediana servizi totali entro {args.cutoff_tp} min): "
                         f"{mediana([sum(r['tp'][chi].values()) for r in g]):.0f}")
        for ora in args.ore:
            chi = f"{ora:02d}"
            zero = sum(1 for r in g if sum(r["tp"][chi].values()) == 0)
            if zero:
                righe.append(f"  ATENZIONE: {zero} sezioni senza NESSUN servizio entro "
                             f"{args.cutoff_tp} min alle {chi}:00")
        zp = sum(1 for r in g if sum(r["piedi"][str(args.cutoff_piedi)].values()) == 0)
        righe.append(f"  Sezioni a zero anche a piedi: {zp}")
        righe.append("")

    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(righe), encoding="utf-8")
    log(f"Scritto {RAPPORTO}")


if __name__ == "__main__":
    main()
