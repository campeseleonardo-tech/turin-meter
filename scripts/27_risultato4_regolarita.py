#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Risultato 4 — Bus in ritardo e bus irregolari.

Domanda
-------
1. Puntualità: quanti passaggi dei mezzi GTT alle fermate arrivano con **più di 5 minuti**
   di ritardo? Su quali linee e a che ora va peggio?
2. Regolarità: sulle linee frequenti, quante volte i mezzi arrivano **a grappolo** (due
   attaccati) o lasciano un **buco** (attesa molto più lunga del previsto)?

Decisioni (D1-D9, non modificabili)
-----------------------------------
D1 passaggio = per ogni (trip_id, start_date, seq) si tiene solo l'ultima lettura
   (la letto_utc più recente) in cui quella seq compare;
D2 ritardo = arr.delay/60 minuti; se arr ha "time": (time - orario_programmato)/60, con
   orario programmato = mezzanotte locale di start_date + arrival_time GTFS, in UTC;
D3 scarto se |arrivo stimato - letto_utc| > 10 min, o se corsa/seq non è nel GTFS;
D4 classi: anticipo se < -1 min; puntuale se -1..+5; in ritardo se > +5;
D5 arrivo stimato = orario programmato + ritardo;
D6 regolarità solo su coppie con intervallo programmato <= 15 minuti;
D7 grappolo se osservato < 0,5 x programmato; buco se > 2 x programmato; altrimenti
   regolare;
D8 linea in classifica solo con >= 200 passaggi (puntualità, nel tipo di giorno) o
   >= 100 coppie (regolarità);
D9 fasce: punta_mattina 7-9, giorno 9-16, punta_sera 16-19, sera 19-24, notte 0-7
   (ora locale dell'arrivo programmato).

Input (sola lettura)
--------------------
data/storico_backup.sqlite  -> tabella trip_update_gtt (letto_utc, trip_id, start_date,
                               payload JSON con stu[].arr.delay o stu[].arr.time) e mezzi_gtt (GPS).
                               Se lo storico non c'e' (o con --riassunti) si leggono i riassunti
                               data/storico_riassunti/passaggi_AAAA-MM.zip scritti dallo script 97: stessi numeri;
data/raw/gtt_gtfs_20261003_224530.zip -> trips.txt, routes.txt, stop_times.txt.

Output
------
data/processed/risultato4_regolarita.json
docs/rapporti/RAPPORTO_RISULTATO4.txt

Uso
---
python scripts/27_risultato4_regolarita.py [--prova] [--fonte gps|feed] [--riassunti]
--prova = solo start_date 20261013, rapporto a schermo, nessun file scritto.
--riassunti = legge i riassunti dello storico (script 97) anche se lo storico c'e'.
--fonte = da dove vengono gli arrivi: gps (predefinita dal 21/10, Giro 5) oppure feed (calcolo di prima, D1-D3).
--sposta-secondi N (F3, §6.3 del piano) = forbice dovuta alla lettura al minuto: il Pi legge una posizione al minuto e l'istante di passaggio misurato puo'
    cadere fino a un minuto PRIMA di quello vero, quindi il ritardo vero e' piu' grande o uguale. Con N > 0 tutti i passaggi GPS si spostano di N secondi
    in avanti e lo script scrive solo data/processed/risultato4_sposta_N.json (riassunto), senza toccare risultato4_regolarita.json. Si lancia con 30 e 60,
    poi (senza opzione) con 0: quest'ultimo giro legge i riassunti e scrive nel JSON principale i campi anticipo_forbice, ritardo_forbice e punto_anticipo.
Con gps le regole D1-D3 valgono solo per il confronto col feed; D4-D9 restano.

Aggiunte B1 e B2 (piano R4 parte B, 21/10): in coda al rapporto e nel JSON ("confronto_gtt") senza toccare il resto.
B1: la quota di passaggi oltre 10 minuti in 4 definizioni: (a) a ogni fermata, (b) solo alla prima fermata della corsa,
    (c) solo alla fermata di mezzo della corsa, (d) solo fuori dalle ore di punta (fuori da 7-9 e 16-19);
    per feriale, sabato, domenica e media della settimana pesata 5 / 1 / 1 (pesi sulle percentuali dei tre tipi di giorno).
B2: (i) il numero (a) con tutti i passaggi spostati di -1 e +1 minuto; (ii) forbice per i passaggi senza GPS
    (passaggi programmati delle corse viste senza arrivo GPS valido): tutti puntuali oppure tutti con la quota di ritardo
    dei peggiori 10% di giorni dello stesso tipo. Le corse mai viste dal GPS non si contano (non si sa se hanno girato).
"""

import csv
import io
import json
import math
import re
import sqlite3
import sys
import zipfile
from array import array
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402  (haversine_m per la lunghezza delle corse)
import riassunti_storico as rs  # noqa: E402  (sorgente alternativa: i riassunti dello storico, script 97)

RADICE = Path(__file__).resolve().parent.parent
DB = RADICE / "data" / "storico_backup.sqlite"
GTFS = RADICE / "data" / "raw" / "gtt_gtfs_20261003_224530.zip"
GTFS_ARCHIVIO = RADICE / "data" / "gtfs_archivio"   # zip del GTFS archiviati dal Pi (L4): per ogni giorno si usa il GTFS valido allora
OUT_JSON = RADICE / "data" / "processed" / "risultato4_regolarita.json"
OUT_RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_RISULTATO4.txt"
SPOSTAMENTI_S = (30, 60)                        # F3 §6.3: i giri con --sposta-secondi (il giro a 0 e' quello principale)
SOGLIA_PUNTO_ANTICIPO_PCT = 15.0                # il punto chiave sull'anticipo si mostra solo se anche a +60 s la quota resta sopra il 15%
OUT_RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
POPOLARITA = RADICE / "data" / "processed" / "popolarita_zone.json"     # script 87: linee utili

TAG = "MISURATO"
GIORNO_PROVA = "20261013"

# D2/D3/D4/D6/D8
SOGLIA_RITARDO = 5.0
SOGLIA_ANTICIPO = -1.0
MAX_LETTURA = 600.0          # secondi (10 minuti)
FREQ_MAX = 15.0              # minuti
MIN_PASSAGGI = 200
MIN_COPPIE = 100
SOGLIA_RITARDO_10 = 10.0     # ritardo oltre 10 minuti: la misura del rapporto GTT 2025
RIF_GTT_RITARDO10_PCT = 2.3  # rapporto di sostenibilita' GTT 2025: passaggi bus/tram in ritardo > 10', anno 2025 (docs/rapporti/RIASSUNTO_RAPPORTO_SOSTENIBILITA_2025.md)
FINE_CORSA_ULTIME = 3        # fine corsa = passaggi alle ultime 3 fermate della corsa
MIN_FINE_CORSA = 100         # passaggi di fine corsa minimi per entrare nella classifica dei minuti ogni 10 km
MODI = ("tram", "metro", "bus")
# B1/B2
DEFINIZIONI = (("a", "a ogni fermata (come oggi)"), ("b", "solo alla prima fermata della corsa"),
               ("c", "solo alla fermata di mezzo della corsa"), ("d", "solo fuori dalle ore di punta (fuori da 7-9 e 16-19)"))
PESI_SETTIMANA = {"0": 5, "1": 1, "2": 1}     # feriale, sabato, domenica
SPOSTAMENTI_MIN = (-1, 0, 1)                  # B2 (i)
QUOTA_GIORNI_PEGGIORI = 0.10                  # B2 (ii): il 10% dei giorni peggiori (almeno 1) dello stesso tipo

# arrivi misurati con il GPS dei mezzi (tabella mezzi_gtt). Il feed resta solo come confronto.
FONTE_ARRIVI = "gps"             # "gps" (predefinita) oppure "feed" con --fonte feed (calcolo di prima)
DIST_GPS_M = 60.0                # passaggio GPS valido: a meno di 60 m dalla fermata
SEGMENTO_MAX_S = 180             # segmento fra due posizioni consecutive lungo al massimo 180 s
MAX_RITARDO_VERO_MIN = 60.0      # |ritardo| oltre 60 minuti = corrispondenza sbagliata, passaggio non valido
MIN_QUOTA_GIORNO_GPS = 0.5       # Giro 6: un giorno entra solo con almeno meta' della mediana delle corse viste dei giorni dello stesso tipo
COPERTURA_MIN_PCT = 60.0         # controllo: passaggi con GPS valido / programmati delle corse viste
RITARDO_GPS_FERIALE_ATTESO = (8.0, 25.0)   # buon senso dalla prova del Giro 4 (circa 15%)
MIN_PASSAGGI_CLASSIFICA = 2000   # classifica delle linee peggiori: solo linee ordinarie (Leo, 20/10/2026)


def linea_ordinaria(nome):
    """Linee ordinarie: nome fatto solo di cifre (es. 4, 17, 68). Speciali e varianti (RV2, VEX, LS1, 68+, 17/) no."""
    return str(nome).isdigit()

TIPI = ("0", "1", "2")                        # 0 feriale, 1 sabato, 2 domenica
FASCE = ("punta_mattina", "giorno", "punta_sera", "sera", "notte")   # D9

# posizioni nei tuple dei passaggi
P_LINEA, P_DIR, P_STOP, P_SCHED, P_EST, P_RIT, P_FASCIA, P_SEQ, P_FONTE, P_TRIP = range(10)


# ---------- ora locale Europe/Rome (come in comuni.py) ----------

def ultima_domenica(anno, mese):
    """Giorno dell'ultima domenica del mese (date.weekday: lun=0 ... dom=6)."""
    ultimo = monthrange(anno, mese)[1]
    gw = date(anno, mese, ultimo).weekday()
    return ultimo - ((gw - 6) % 7)


def offset_roma(utc):
    """Offset in ore di Europe/Rome per un datetime UTC. Regola UE."""
    y = utc.year
    inizio = datetime(y, 3, ultima_domenica(y, 3), 1, tzinfo=timezone.utc)
    fine = datetime(y, 10, ultima_domenica(y, 10), 1, tzinfo=timezone.utc)
    return 2 if inizio <= utc < fine else 1


def a_roma(utc):
    return utc + timedelta(hours=offset_roma(utc))


def offset_data_locale(d):
    """Offset in ore valevole alla mezzanotte locale del giorno d."""
    for off in (2, 1):
        candidato = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) - timedelta(hours=off)
        if offset_roma(candidato) == off:
            return off
    return 2


def fascia_oraria(h):
    if 7 <= h < 9:
        return "punta_mattina"
    if 9 <= h < 16:
        return "giorno"
    if 16 <= h < 19:
        return "punta_sera"
    if 19 <= h < 24:
        return "sera"
    return "notte"


def tipo_giorno_data(d):
    return {5: 1, 6: 2}.get(d.weekday(), 0)


def da_gttfs(g):
    return f"{g[0:4]}-{g[4:6]}-{g[6:8]}"


# ---------- GTFS ----------

def carica_gtfs(percorso=None):
    """(percorso: default GTFS) Ritorna trip_info, nome_linea, prog e, in piu': modo_linea (nome -> tram/metro/bus da route_type),
    ultima_seq (corsa -> ultima stop_sequence) e km_corsa (corsa -> somma delle distanze in linea d'aria fra fermate
    consecutive)."""
    trip_info = {}
    nome_linea = {}
    modo_linea = {}
    prog = {}
    coord = {}
    per_corsa = {}
    with zipfile.ZipFile(percorso or GTFS) as z:
        with z.open("routes.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                nome_linea[r["route_id"]] = r["route_short_name"]
                # route_type 0 tram, 1 metro, altro bus (3 = bus, 7 = funicolare)
                modo_linea[r["route_short_name"]] = {"0": "tram", "1": "metro"}.get(r.get("route_type", ""), "bus")
        with z.open("stops.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                try:
                    coord[r["stop_id"]] = (float(r["stop_lat"]), float(r["stop_lon"]))
                except (ValueError, KeyError):
                    continue
        with z.open("trips.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                trip_info[r["trip_id"]] = (r["route_id"], int(r["direction_id"] or 0))
        with z.open("stop_times.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                h, m, s = (int(x) for x in r["arrival_time"].split(":"))
                seq = int(r["stop_sequence"])
                prog[(r["trip_id"], seq)] = (h * 3600 + m * 60 + s, r["stop_id"])
                per_corsa.setdefault(r["trip_id"], []).append((seq, r["stop_id"]))
    ultima_seq, km_corsa = {}, {}
    for tid, lista in per_corsa.items():
        lista.sort()
        ultima_seq[tid] = lista[-1][0]
        km = 0.0
        for (_, a), (_, b) in zip(lista[:-1], lista[1:]):
            if a in coord and b in coord:
                km += comuni.haversine_m(coord[a][0], coord[a][1], coord[b][0], coord[b][1])
        km_corsa[tid] = km / 1000.0
    return trip_info, nome_linea, prog, modo_linea, ultima_seq, km_corsa


def versioni_gtfs():
    """[(AAAAMMGG, percorso)] degli zip del GTFS archiviati dal Pi (data/gtfs_archivio/gtt_gtfs_AAAAMMGG[_n].zip), in ordine di data."""
    if not GTFS_ARCHIVIO or not Path(GTFS_ARCHIVIO).is_dir():
        return []
    out = []
    for f in sorted(Path(GTFS_ARCHIVIO).glob("gtt_gtfs_*.zip")):
        m = re.fullmatch(r"gtt_gtfs_(\d{8})(?:_\d+)?\.zip", f.name)
        if m:
            out.append((m.group(1), f))
    return sorted(out, key=lambda x: (x[0], x[1].name))


def modi_linea(percorso):
    """nome della linea -> tram/metro/bus da routes.txt di un GTFS (senza caricare il resto)."""
    modi = {}
    with zipfile.ZipFile(percorso) as z, z.open("routes.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            modi[r["route_short_name"]] = {"0": "tram", "1": "metro"}.get(r.get("route_type", ""), "bus")
    return modi


def gtfs_del_giorno(giorno):
    """GTFS valido in un giorno (AAAAMMGG): il piu' recente archiviato con data <= giorno; per i giorni prima del primo archivio
    (o senza archivio) quello di oggi in data/raw (GTFS). Con un solo GTFS tutti i giorni usano lo stesso: i numeri non cambiano."""
    valido = None
    for data, f in versioni_gtfs():
        if data <= giorno:
            valido = f
    return valido or GTFS


class GtfsPerGiorno:
    """Il GTFS giusto per ogni giorno. stato(giorno) ritorna un oggetto con trip_info, nome_linea, prog, modo_linea, ultima_seq, km_corsa,
    fermate, ctx, prima_seq, meta_seq; ricarica solo quando la versione cambia (in memoria ce n'e' una alla volta)."""

    def __init__(self, con_fermate=True):
        self.con_fermate = con_fermate
        self.percorso, self.corrente = None, None

    def stato(self, giorno):
        p = gtfs_del_giorno(giorno)
        if p != self.percorso:
            print(f"Carico il GTFS {Path(p).name} (giorno {giorno})...", file=sys.stderr)
            self.corrente = None   # libera la versione precedente prima di caricare la nuova
            trip_info, nome_linea, prog, modo_linea, ultima_seq, km_corsa = carica_gtfs(p)
            seqs = defaultdict(list)
            for (tid_, seq_) in prog:
                seqs[tid_].append(seq_)
            prima_seq, meta_seq = {}, {}
            for tid_, lista_ in seqs.items():
                lista_.sort()
                prima_seq[tid_], meta_seq[tid_] = lista_[0], lista_[(len(lista_) - 1) // 2]
            print(f"GTFS: {len(trip_info)} corse, {len(prog)} fermate di corsa", file=sys.stderr)
            self.corrente = SimpleNamespace(
                path=p, trip_info=trip_info, nome_linea=nome_linea, prog=prog, modo_linea=modo_linea, ultima_seq=ultima_seq, km_corsa=km_corsa,
                fermate=carica_fermate(p) if self.con_fermate else {}, ctx=(trip_info, nome_linea, prog), prima_seq=prima_seq, meta_seq=meta_seq)
            self.percorso = p
        return self.corrente


def carica_fermate(percorso=None):
    """stop_id -> (nome, lat, lon) da stops.txt (come lo script 70)."""
    fermate = {}
    with zipfile.ZipFile(percorso or GTFS) as z:
        with z.open("stops.txt") as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                try:
                    fermate[r["stop_id"]] = (r.get("stop_name", ""), float(r["stop_lat"]), float(r["stop_lon"]))
                except (ValueError, KeyError):
                    continue
    return fermate


# ---------- passaggi dal GPS ----------

def _segmento(punti, i, flat, flon, kx):
    """(dist, istante) del punto del segmento i piu' vicino alla fermata; None se il segmento non e' usabile.
    Stessa geometria di controllo_gps() dello script 70, con il rifiuto veloce dei segmenti lontani."""
    t0, la0, lo0 = punti[i]
    t1, la1, lo1 = punti[i + 1]
    if t1 <= t0 or t1 - t0 > SEGMENTO_MAX_S:
        return None
    x0, y0 = (lo0 - flon) * kx, (la0 - flat) * 110540.0
    x1, y1 = (lo1 - flon) * kx, (la1 - flat) * 110540.0
    r = DIST_GPS_M
    if (x0 > r and x1 > r) or (x0 < -r and x1 < -r) or (y0 > r and y1 > r) or (y0 < -r and y1 < -r):
        return (1e9, t0)
    dx, dy = x1 - x0, y1 - y0
    l2 = dx * dx + dy * dy
    f = 0.0 if l2 == 0 else max(0.0, min(1.0, -(x0 * dx + y0 * dy) / l2))
    return (math.hypot(x0 + f * dx, y0 + f * dy), t0 + f * (t1 - t0))


def cerca_vincolata(punti, flat, flon, kx, t_prec, i0, partenza=False):
    """Primo gruppo di segmenti vicini alla fermata con istante >= t_prec, dal segmento i0.
    Ritorna (istante, indice del segmento) del piu' vicino del gruppo, oppure None.
    partenza=True (L9b al capolinea, dal giro L23 a tutte le fermate): il bus aspetta fermo vicino alla fermata e il punto piu' vicino
    cade durante l'attesa; il passaggio e' invece l'ultimo istante del gruppo, quando il bus se ne va (l'orario GTFS e' di partenza)."""
    migliore = None
    for i in range(i0, len(punti) - 1):
        s = _segmento(punti, i, flat, flon, kx)
        vicino = s is not None and s[0] <= DIST_GPS_M and s[1] >= t_prec
        if vicino:
            if partenza or migliore is None or s[0] < migliore[0]:
                migliore = (s[0], s[1], i)
        elif migliore is not None and s is not None:
            break
    return (migliore[1], migliore[2]) if migliore else None


def passaggi_corsa(punti, fermate_corsa, sched_base, fermate):
    """Per ogni fermata della corsa (ordinata per stop_sequence) il passaggio GPS valido:
    {seq: istante}. Il passaggio di una fermata viene solo dopo quello della fermata prima."""
    out = {}
    t_prec, i0 = -1e18, 0
    for n, (seq, sec, stop) in enumerate(fermate_corsa):
        info = fermate.get(stop)
        if not info:
            continue
        flat, flon = info[1], info[2]
        kx = 111320.0 * math.cos(math.radians(flat))
        # L23: nel GTFS GTT arrival_time = departure_time nel 100% delle righe di stop_times: l'orario di una fermata e' un istante solo, da leggere come
        # partenza. Il passaggio e' quindi per TUTTE le fermate l'ultimo istante del gruppo vicino (quando il bus riparte), come gia' al capolinea (L9b).
        r = cerca_vincolata(punti, flat, flon, kx, t_prec, i0, partenza=True)
        if r is None or abs(r[0] - (sched_base + sec)) / 60.0 > MAX_RITARDO_VERO_MIN:
            continue
        out[seq] = r[0]
        t_prec, i0 = r[0], r[1]
    return out


def giorni_gps_validi(sorg, giorni, trip_info):
    """Giro 6. Tiene i giorni con abbastanza GPS: corse viste (stessa finestra e stessa regola di costruisci_passaggi_gps:
    corsa nel GTFS, almeno 2 posizioni) almeno MIN_QUOTA_GIORNO_GPS volte la mediana dei giorni dello stesso tipo
    (feriale, sabato, domenica). Ritorna (giorni validi in ordine, esclusi = [{"giorno", "corse_viste", "mediana_tipo"}])."""
    viste, tipo = {}, {}
    for giorno in giorni:
        data = datetime.strptime(giorno, "%Y%m%d").date()
        viste[giorno] = sorg.corse_viste(giorno, trip_info(giorno) if callable(trip_info) else trip_info)
        tipo[giorno] = tipo_giorno_data(data)
    validi, esclusi = [], []
    for giorno in giorni:
        med = mediana([viste[g] for g in giorni if tipo[g] == tipo[giorno]])
        if viste[giorno] >= MIN_QUOTA_GIORNO_GPS * med:
            validi.append(giorno)
        else:
            esclusi.append({"giorno": giorno, "corse_viste": viste[giorno], "mediana_tipo": med})
    return validi, esclusi


def costruisci_passaggi_gps(con, giorno, trip_info, nome_linea, prog, fermate):
    """Come costruisci_passaggi ma con gli arrivi del GPS (tabella mezzi_gtt). Ritorna (passaggi, copertura).
    Le tuple sono le stesse (P_LINEA ... P_TRIP): P_EST = istante GPS, P_RIT = ritardo vero in minuti, P_FONTE = "gps".
    copertura = passaggi programmati delle corse viste, con GPS valido, corse viste, corse GPS fuori GTFS, righe lette."""
    data = datetime.strptime(giorno, "%Y%m%d").date()
    off = offset_data_locale(data)
    mezz = datetime(data.year, data.month, data.day, tzinfo=timezone.utc) - timedelta(hours=off)
    base = mezz.timestamp()
    finestra = (base + 2 * 3600, base + 26 * 3600)       # finestra come lo script 70
    pos = defaultdict(list)
    righe = 0
    for corsa, ts, lat, lng in con.execute(
            "SELECT corsa, ts_feed, lat, lng FROM mezzi_gtt WHERE letto_utc BETWEEN ? AND ?",
            ((mezz + timedelta(hours=2)).isoformat(), (mezz + timedelta(hours=26)).isoformat())):
        righe += 1
        if corsa and ts and lat and lng:
            pos[corsa].append((ts, lat, lng))
    corse = [t for t in pos if t in trip_info]
    corse_set = set(corse)
    fuori = len(pos) - len(corse)
    stops_corsa = defaultdict(list)
    for (tid, seq), (sec, stop) in prog.items():
        if tid in corse_set:
            stops_corsa[tid].append((seq, sec, stop))
    passaggi = []
    cop = {"programmati": 0, "validi": 0, "corse_viste": 0, "corse_fuori_gtfs": fuori, "righe": righe}
    fascia_cache = {}
    for tid in corse:
        punti = sorted(set(pos[tid]))
        if len(punti) < 2:
            continue
        cop["corse_viste"] += 1
        fermate_c = sorted(stops_corsa[tid])
        route, direzione = trip_info[tid]
        linea = nome_linea.get(route, route)
        trovati = passaggi_corsa(punti, fermate_c, base, fermate)
        for seq, sec, stop in fermate_c:
            sched = base + sec
            if finestra[0] <= sched <= finestra[1]:
                cop["programmati"] += 1
            if seq not in trovati:
                continue
            cop["validi"] += 1
            h = int(sched) // 3600
            if h not in fascia_cache:
                fascia_cache[h] = fascia_oraria(a_roma(datetime.fromtimestamp(sched, timezone.utc)).hour)
            t = trovati[seq]
            passaggi.append((linea, direzione, stop, sched, t, (t - sched) / 60.0, fascia_cache[h], seq, "gps", tid))
    return passaggi, cop


# ---------- aggregatori ----------

def agg_punt():
    return [0, 0, 0, 0, array("d"), 0]          # ..., ritardi, passaggi in ritardo oltre SOGLIA_RITARDO_10


def agg_reg():
    return [0, 0, 0, 0]


def conta_punt(a, rit):
    a[0] += 1
    if rit < SOGLIA_ANTICIPO:
        a[1] += 1
    elif rit > SOGLIA_RITARDO:
        a[3] += 1
    else:
        a[2] += 1
    a[4].append(rit)
    if rit > SOGLIA_RITARDO_10:
        a[5] += 1


def mediana(vals):
    if not vals:
        return 0.0
    v = sorted(vals)
    n = len(v)
    return round(v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0, 1)


def p90(vals):
    if not vals:
        return 0.0
    v = sorted(vals)
    return round(v[int(round(0.9 * (len(v) - 1)))], 1)


def pct(x, n):
    return round(100.0 * x / n, 1) if n else 0.0


def stat_punt(a):
    n = a[0]
    return {"passaggi": n, "anticipo": pct(a[1], n), "puntuale": pct(a[2], n),
            "ritardo": pct(a[3], n), "ritardo10": round(100.0 * a[5] / n, 2) if n else 0.0, "ritardo10_n": a[5],
            "mediana": mediana(a[4]), "p90": p90(a[4])}


def stat_reg(a):
    n = a[0]
    return {"coppie": n, "grappolo": pct(a[1], n), "buco": pct(a[2], n),
            "regolare": pct(a[3], n)}


# ---------- un giorno alla volta ----------

def leggi_giorno(con, giorno):
    """D1: ultima lettura per (trip_id, seq) del giorno."""
    ultimo = {}
    for letto, trip_id, payload in con.execute(
            "SELECT letto_utc, trip_id, payload FROM trip_update_gtt "
            "WHERE start_date = ? ORDER BY letto_utc", (giorno,)):
        try:
            p = json.loads(payload)
        except (ValueError, TypeError):
            continue
        tid = ((p.get("trip") or {}).get("trip_id")) or trip_id
        for e in (p.get("stu") or []):
            arr = e.get("arr")
            seq = e.get("seq")
            if not arr or seq is None:
                continue
            ultimo[(tid, seq)] = (letto, arr)
    return ultimo


def costruisci_passaggi(ultimo, giorno, trip_info, nome_linea, prog):
    """D2-D5: trasforma le ultime letture in passaggi validi."""
    data = datetime.strptime(giorno, "%Y%m%d").date()
    tipo = str(tipo_giorno_data(data))
    off = offset_data_locale(data)
    mezzanotte = datetime(data.year, data.month, data.day, tzinfo=timezone.utc) - timedelta(hours=off)
    passaggi = []
    scarti = [0, 0, 0]       # fuori GTFS, lettura lontana, lettura lontana con ritardo oltre SOGLIA_RITARDO_10
    esempi = {"delay": None, "time": None}
    for (tid, seq), (letto, arr) in ultimo.items():
        info = trip_info.get(tid)
        p = prog.get((tid, seq))
        if info is None or p is None:
            scarti[0] += 1
            continue
        secondi, stop_id = p
        route_id, direzione = info
        sched = mezzanotte + timedelta(seconds=secondi)
        if not isinstance(arr, dict):
            continue
        if arr.get("delay") is not None:
            rit = arr["delay"] / 60.0
            fonte = "delay"
        elif arr.get("time") is not None:
            rit = (arr["time"] - sched.timestamp()) / 60.0
            fonte = "time"
        else:
            continue                     # né delay né time: nessun ritardo utilizzabile
        est = sched + timedelta(minutes=rit)
        letto_dt = datetime.fromisoformat(letto)
        if abs((est - letto_dt).total_seconds()) > MAX_LETTURA:
            scarti[1] += 1
            if rit > SOGLIA_RITARDO_10:
                scarti[2] += 1      # solo informativo: D3 li scarta, ma sono ritardi lunghi (vedi «OLTRE 10 MINUTI»)
            continue
        if esempi[fonte] is None:
            esempi[fonte] = {
                "trip_id": tid, "seq": seq, "start_date": giorno, "letto": letto,
                "arr": dict(arr), "fonte": fonte,
                "orario_gtfs": f"{secondi // 3600:02d}:{secondi % 3600 // 60:02d}:{secondi % 60:02d}",
                "sched_utc": sched.isoformat(), "est_utc": est.isoformat(),
                "ritardo_min": round(rit, 2)}
        passaggi.append((nome_linea.get(route_id, route_id), direzione, stop_id,
                         sched.timestamp(), est.timestamp(), rit,
                         fascia_oraria(a_roma(sched).hour), seq, fonte, tid))
    return passaggi, scarti, tipo, esempi


def regolarita(passaggi, tipo):
    """D6-D7: coppie di passaggi consecutivi alla stessa fermata.

    Ritorna (totali città, totali per nome linea, esempio di grappolo).
    """
    gruppi = {}
    for pg in passaggi:
        gruppi.setdefault((pg[P_LINEA], pg[P_DIR], pg[P_STOP]), []).append(pg)
    coppie = agg_reg()
    per_linea = {}
    esempio = None
    for lista in gruppi.values():
        if len(lista) < 2:
            continue
        lista.sort(key=lambda x: x[P_SCHED])
        for i in range(len(lista) - 1):
            a, b = lista[i], lista[i + 1]
            prog_i = (b[P_SCHED] - a[P_SCHED]) / 60.0
            if not 0 < prog_i <= FREQ_MAX:      # D6
                continue
            obs_i = (b[P_EST] - a[P_EST]) / 60.0
            if obs_i < 0.5 * prog_i:
                classe = 1                      # grappolo
            elif obs_i > 2 * prog_i:
                classe = 2                      # buco
            else:
                classe = 3                      # regolare
            coppie[0] += 1
            coppie[classe] += 1
            t = per_linea.setdefault((tipo, a[P_LINEA]), agg_reg())
            t[0] += 1
            t[classe] += 1
            if classe == 1 and esempio is None:
                esempio = {"linea": a[P_LINEA], "direzione": a[P_DIR], "stop_id": a[P_STOP],
                           "sched_a": datetime.fromtimestamp(a[P_SCHED], timezone.utc).isoformat(),
                           "sched_b": datetime.fromtimestamp(b[P_SCHED], timezone.utc).isoformat(),
                           "est_a": datetime.fromtimestamp(a[P_EST], timezone.utc).isoformat(),
                           "est_b": datetime.fromtimestamp(b[P_EST], timezone.utc).isoformat(),
                           "prog_min": round(prog_i, 2), "obs_min": round(obs_i, 2),
                           "tipo": tipo}
    return coppie, per_linea, esempio


# ---------- sorgenti dei dati: database dello storico oppure riassunti (script 97) ----------

def mezzanotte_utc(giorno):
    d = datetime.strptime(giorno, "%Y%m%d").date()
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc) - timedelta(hours=offset_data_locale(d))


class SorgenteDb:
    """Legge lo storico SQLite (sola lettura). Metodi comuni con rs.SorgenteRiassunti.
    ctx = (trip_info, nome_linea, prog) del GTFS."""
    nome = "storico SQLite"

    def __init__(self, percorso):
        self.con = sqlite3.connect(f"file:{percorso}?mode=ro", uri=True, timeout=60)

    def giorni(self):
        return [r[0] for r in self.con.execute("SELECT DISTINCT start_date FROM trip_update_gtt ORDER BY 1")]

    def corse_viste(self, giorno, trip_info):
        mezz = mezzanotte_utc(giorno)
        n = 0
        for (corsa,) in self.con.execute(
                "SELECT corsa FROM mezzi_gtt WHERE letto_utc BETWEEN ? AND ? AND corsa <> '' AND ts_feed AND lat AND lng "
                "GROUP BY corsa HAVING COUNT(DISTINCT ts_feed || '|' || lat || '|' || lng) >= 2",
                ((mezz + timedelta(hours=2)).isoformat(), (mezz + timedelta(hours=26)).isoformat())):
            n += corsa in trip_info
        return n

    def passaggi_feed(self, giorno, ctx):
        """(passaggi, scarti, tipo, esempi, letture usate)"""
        ultimo = leggi_giorno(self.con, giorno)
        passaggi, sc, tipo, es = costruisci_passaggi(ultimo, giorno, *ctx)
        return passaggi, sc, tipo, es, len(ultimo)

    def passaggi_gps(self, giorno, ctx, fermate):
        return costruisci_passaggi_gps(self.con, giorno, *ctx, fermate)

    def corse_gps(self, giorno):
        mezz = mezzanotte_utc(giorno)
        da, a = (mezz + timedelta(hours=2)).isoformat(), (mezz + timedelta(hours=26)).isoformat()
        return {r[0] for r in self.con.execute("SELECT DISTINCT corsa FROM mezzi_gtt WHERE letto_utc BETWEEN ? AND ?", (da, a))}

    def ore_attive(self, giorno, min_minuti):
        """Inizio (timestamp UTC) delle ore in cui la raccolta ha letto almeno min_minuti minuti."""
        return {h for h, n in self.ore_minuti(giorno).items() if n >= min_minuti}

    def ore_minuti(self, giorno):
        """{inizio dell'ora (timestamp UTC): minuti distinti con almeno una lettura del feed dei ritardi}"""
        mezz = mezzanotte_utc(giorno)
        da, a = (mezz + timedelta(hours=2)).isoformat(), (mezz + timedelta(hours=26)).isoformat()
        per_ora = defaultdict(int)
        for (minuto,) in self.con.execute("SELECT DISTINCT substr(letto_utc,1,16) FROM trip_update_gtt "
                                          "WHERE letto_utc BETWEEN ? AND ?", (da, a)):
            t = datetime.fromisoformat(minuto + ":00+00:00")
            per_ora[int(t.timestamp()) // 3600 * 3600] += 1
        return dict(per_ora)

    def chiudi(self):
        self.con.close()


def fascia_da_ts(ts):
    """Fascia oraria (D9) di un istante programmato dato in secondi UTC."""
    return fascia_oraria(a_roma(datetime.fromtimestamp(ts, timezone.utc)).hour)


def apri_sorgente(forza_riassunti=False):
    """Lo storico se c'e' (e non si forza), altrimenti i riassunti dello script 97."""
    if not forza_riassunti and DB.exists():
        return SorgenteDb(DB)
    sorg = rs.SorgenteRiassunti(fascia=fascia_da_ts)
    if not sorg.giorni():
        raise SystemExit(f"Manca lo storico ({DB}) e non ci sono riassunti in {rs.CARTELLA}: "
                         f"lancia scripts/97_riassunti_storico.py (o scarica i dati con scripts/scarica_dati.py).")
    return sorg


# ---------- main ----------

def forbice_lettura(j_citta, j_def):
    """F3 §6.3: dai riassunti dei giri con --sposta-secondi (30 e 60) e dai numeri del giro a 0 secondi, la forbice dovuta alla lettura al minuto.
    Ritardi: il numero grande e' quello a 0 secondi (il piu' prudente), la forbice va [0 s, +60 s]. Anticipo: forbice [+60 s, 0 s].
    Il punto sull'anticipo si mostra solo se anche a +60 s la quota resta sopra SOGLIA_PUNTO_ANTICIPO_PCT. Senza i riassunti il blocco dice che mancano."""
    riass = {}
    for s in SPOSTAMENTI_S:
        f = OUT_JSON.with_name(f"risultato4_sposta_{s}.json")
        if f.is_file():
            riass[s] = json.loads(f.read_text(encoding="utf-8"))
    if 60 not in riass:
        print("AVVISO: manca risultato4_sposta_60.json (lancia prima lo script con --sposta-secondi 30 e 60): forbice della lettura non scritta")
        return {"forbice_lettura": {"scritta": False}}
    zero = {"citta": {t: {k: j_citta[t][k] for k in ("passaggi", "anticipo", "puntuale", "ritardo", "ritardo10")} for t in j_citta},
            "settimana": {d_: j_def[d_]["settimana"] for d_ in j_def}}
    per = {"0": zero, **{str(s): r for s, r in sorted(riass.items())}}
    fer0, fer60 = zero["citta"]["0"], riass[60]["citta"]["0"]
    set0, set60 = zero["settimana"]["a"], riass[60]["settimana"]["a"]
    return {"forbice_lettura": {
        "scritta": True, "spostamenti_s": [0, *sorted(riass)], "per_spostamento": per,
        "anticipo_forbice": {"feriale_pct": [fer60["anticipo"], fer0["anticipo"]]},
        "ritardo_forbice": {"feriale_oltre5_pct": [fer0["ritardo"], fer60["ritardo"]], "feriale_oltre10_pct": [fer0["ritardo10"], fer60["ritardo10"]],
                            "settimana_oltre5_pct": [set0["ritardo5_pct"], set60["ritardo5_pct"]], "settimana_oltre10_pct": [set0["ritardo10_pct"], set60["ritardo10_pct"]]},
        "punto_anticipo": bool(fer60["anticipo"] > SOGLIA_PUNTO_ANTICIPO_PCT),
        "regola": "ritardi: numero grande a 0 secondi, forbice [0 s, +60 s]; anticipo: forbice [+60 s, 0 s]; punto sull'anticipo solo se anche a +60 s la quota resta sopra "
                  f"il {SOGLIA_PUNTO_ANTICIPO_PCT:g}%"}}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    prova = "--prova" in sys.argv[1:]
    fonte = FONTE_ARRIVI
    if "--fonte" in sys.argv[1:]:
        fonte = sys.argv[sys.argv.index("--fonte") + 1]
        if fonte not in ("gps", "feed"):
            raise SystemExit("--fonte vuole gps oppure feed")
    gps = fonte == "gps"
    forza_riassunti = "--riassunti" in sys.argv[1:]
    sposta_s = 0
    if "--sposta-secondi" in sys.argv[1:]:
        sposta_s = int(sys.argv[sys.argv.index("--sposta-secondi") + 1])
        if sposta_s < 0 or not gps:
            raise SystemExit("--sposta-secondi vuole un numero >= 0 e la fonte gps")

    gtfs = GtfsPerGiorno(gps)   # il GTFS valido in ogni giorno (data/gtfs_archivio); finche' c'e' un solo GTFS e' sempre lo stesso
    modo_linea = {}             # unione dei modi delle versioni usate

    sorg = apri_sorgente(forza_riassunti)
    print(f"Sorgente dei dati: {sorg.nome}", file=sys.stderr)
    giorni = [g for g in sorg.giorni() if comuni.nel_periodo(g, "gps")]   # periodo fisso (L9): comuni.PERIODO
    if DB.exists():
        comuni.controlla_copia_storico(DB)
    if prova:
        giorni = [g for g in giorni if g == GIORNO_PROVA]
        if not giorni:
            raise SystemExit(f"Nessuna riga per {GIORNO_PROVA}")
    esclusi_gps = []
    if gps and not prova:
        giorni, esclusi_gps = giorni_gps_validi(sorg, giorni, lambda g: gtfs.stato(g).trip_info)
        for e in esclusi_gps:
            print(f"Giorno escluso (poco GPS): {e['giorno']}, {e['corse_viste']} corse viste, mediana del tipo {e['mediana_tipo']}",
                  file=sys.stderr)
    print(f"Giorni: {giorni}", file=sys.stderr)

    giorni_tipo = {"0": 0, "1": 0, "2": 0}
    punt_citta, punt_citta_fascia, punt_linea, punt_fascia = {}, {}, {}, {}
    reg_citta, reg_linea = {}, {}
    punt_modo = {}                       # (tipo, modo) -> aggregato di puntualita'
    fine = {}                            # (tipo, linea) -> [(ritardo, km_corsa)] dei passaggi alle ultime fermate
    corse_osservate = corse_con_fine = 0
    lontane = {}                         # tipo -> [passaggi scartati per lettura lontana, di cui con ritardo > 10 min]
    scarti = {"fuori_gtfs": 0, "lettura_lontana": 0, "usati": 0}
    cop_tot = {"programmati": 0, "validi": 0, "corse_viste": 0, "corse_fuori_gtfs": 0, "righe": 0}
    cop_giorno = {}
    conf_citta, conf_modo, conf_reg_citta, conf_reg_linea = {}, {}, {}, {}   # confronto col feed (solo con fonte gps)
    conf_scarti = {"fuori_gtfs": 0, "lettura_lontana": 0, "usati": 0}
    letti_totali = 0
    # B1/B2: contatori [passaggi, oltre 5, oltre 10, in anticipo (L9)]
    def_cnt = defaultdict(lambda: [0, 0, 0, 0])   # (definizione, tipo)
    punta_n = defaultdict(int)                    # tipo: passaggi nelle ore di punta (per il controllo della somma)
    sh_cnt = defaultdict(lambda: [0, 0, 0])       # (tipo, spostamento)
    giorno_cnt = defaultdict(lambda: [0, 0, 0])   # (tipo, giorno): definizione (a)
    mancanti = defaultdict(int)                   # tipo: passaggi programmati senza GPS valido
    # controlli indipendenti (passo 5)
    per_fonte = {"delay": array("d"), "time": array("d"), "gps": array("d")}
    per_seq = {"seq 1-5": array("d"), "seq 6-15": array("d"),
               "seq 16-30": array("d"), "seq 31+": array("d")}
    esempi = {"delay": None, "time": None}
    es_grappolo = None

    for n, giorno in enumerate(giorni, 1):
        print(f"[{n}/{len(giorni)}] giorno {giorno}...", file=sys.stderr)
        st = gtfs.stato(giorno)
        ultima_seq, km_corsa, fermate, ctx = st.ultima_seq, st.km_corsa, st.fermate, st.ctx
        prima_seq, meta_seq = st.prima_seq, st.meta_seq
        modo_linea.update(st.modo_linea)
        passaggi, sc, tipo, es, n_letti = sorg.passaggi_feed(giorno, ctx)
        letti_totali += n_letti
        l = lontane.setdefault(tipo, [0, 0])
        l[0] += sc[1]
        l[1] += sc[2]
        if gps:
            # il feed serve solo al confronto (citta' e modi); D1-D3 valgono solo per lui
            conf_scarti["fuori_gtfs"] += sc[0]
            conf_scarti["lettura_lontana"] += sc[1]
            conf_scarti["usati"] += len(passaggi)
            for pg in passaggi:
                conta_punt(conf_citta.setdefault(tipo, agg_punt()), pg[P_RIT])
                conta_punt(conf_modo.setdefault((tipo, modo_linea.get(pg[P_LINEA], "bus")), agg_punt()), pg[P_RIT])
            c_f, per_linea_f, _es = regolarita(passaggi, tipo)
            r = conf_reg_citta.setdefault(tipo, agg_reg())
            for i in range(4):
                r[i] += c_f[i]
            for k, t in per_linea_f.items():
                r = conf_reg_linea.setdefault(k, agg_reg())
                for i in range(4):
                    r[i] += t[i]
            del passaggi
            passaggi, cop = sorg.passaggi_gps(giorno, ctx, fermate)
            if sposta_s:         # F3 §6.3: l'istante vero e' fino a un minuto dopo quello letto
                passaggi = [tuple(pg[:P_EST]) + (pg[P_EST] + sposta_s, pg[P_RIT] + sposta_s / 60.0) + tuple(pg[P_RIT + 1:]) for pg in passaggi]
            cop_giorno[giorno] = cop
            for k, v in cop.items():
                cop_tot[k] += v
            es = {"delay": None, "time": None}
            print(f"      GPS: {cop['validi']} passaggi validi su {cop['programmati']} programmati "
                  f"({cop['corse_viste']} corse viste)", file=sys.stderr)
        else:
            scarti["fuori_gtfs"] += sc[0]
            scarti["lettura_lontana"] += sc[1]
        scarti["usati"] += len(passaggi)
        giorni_tipo[str(tipo)] += 1
        for k, v in es.items():
            if esempi[k] is None and v is not None:
                esempi[k] = v
        visti, visti_fine = set(), set()
        if gps:
            mancanti[tipo] += max(0, cop_giorno[giorno]["programmati"] - cop_giorno[giorno]["validi"])
        for pg in passaggi:
            rit_ = pg[P_RIT]
            for d_, cond_ in (("a", True), ("b", pg[P_SEQ] == prima_seq.get(pg[P_TRIP])), ("c", pg[P_SEQ] == meta_seq.get(pg[P_TRIP])),
                              ("d", pg[P_FASCIA] not in ("punta_mattina", "punta_sera"))):
                if cond_:
                    c_ = def_cnt[(d_, tipo)]
                    c_[0] += 1
                    c_[1] += rit_ > SOGLIA_RITARDO
                    c_[2] += rit_ > SOGLIA_RITARDO_10
                    c_[3] += rit_ < SOGLIA_ANTICIPO
            if pg[P_FASCIA] in ("punta_mattina", "punta_sera"):
                punta_n[tipo] += 1
            for sp_ in SPOSTAMENTI_MIN:
                c_ = sh_cnt[(tipo, sp_)]
                c_[0] += 1
                c_[1] += rit_ + sp_ > SOGLIA_RITARDO
                c_[2] += rit_ + sp_ > SOGLIA_RITARDO_10
            c_ = giorno_cnt[(tipo, giorno)]
            c_[0] += 1
            c_[1] += rit_ > SOGLIA_RITARDO
            c_[2] += rit_ > SOGLIA_RITARDO_10
            modo = modo_linea.get(pg[P_LINEA], "bus")
            conta_punt(punt_modo.setdefault((tipo, modo), agg_punt()), pg[P_RIT])
            tid = pg[P_TRIP]
            visti.add(tid)
            us = ultima_seq.get(tid)
            if us is not None and pg[P_SEQ] >= us - (FINE_CORSA_ULTIME - 1) and km_corsa.get(tid):
                fine.setdefault((tipo, pg[P_LINEA]), []).append((pg[P_RIT], km_corsa[tid]))
                visti_fine.add(tid)
            conta_punt(punt_citta.setdefault(tipo, agg_punt()), pg[P_RIT])
            conta_punt(punt_citta_fascia.setdefault((tipo, pg[P_FASCIA]), agg_punt()), pg[P_RIT])
            conta_punt(punt_linea.setdefault((tipo, pg[P_LINEA]), agg_punt()), pg[P_RIT])
            conta_punt(punt_fascia.setdefault((tipo, pg[P_LINEA], pg[P_FASCIA]), agg_punt()), pg[P_RIT])
            per_fonte[pg[P_FONTE]].append(pg[P_RIT])
            if pg[P_SEQ] <= 5:
                per_seq["seq 1-5"].append(pg[P_RIT])
            elif pg[P_SEQ] <= 15:
                per_seq["seq 6-15"].append(pg[P_RIT])
            elif pg[P_SEQ] <= 30:
                per_seq["seq 16-30"].append(pg[P_RIT])
            else:
                per_seq["seq 31+"].append(pg[P_RIT])
        corse_osservate += len(visti)
        corse_con_fine += len(visti_fine)
        c, per_linea, es = regolarita(passaggi, tipo)
        if c[0]:
            r = reg_citta.setdefault(tipo, agg_reg())
            for i in range(4):
                r[i] += c[i]
        for k, t in per_linea.items():
            r = reg_linea.setdefault(k, agg_reg())
            for i in range(4):
                r[i] += t[i]
        if es_grappolo is None and es is not None:
            es_grappolo = es
        del passaggi
    sorg.chiudi()

    # ---------- output JSON ----------
    per = {"da": da_gttfs(giorni[0]), "a": da_gttfs(giorni[-1])}
    parametri = {"soglia_ritardo_min": SOGLIA_RITARDO, "soglia_anticipo_min": SOGLIA_ANTICIPO,
                 "max_lettura_lontana_min": MAX_LETTURA / 60, "freq_max_min": FREQ_MAX,
                 "min_passaggi": MIN_PASSAGGI, "min_passaggi_classifica": MIN_PASSAGGI_CLASSIFICA,
                 "min_coppie": MIN_COPPIE, "soglia_ritardo10_min": SOGLIA_RITARDO_10,
                 "rif_gtt_ritardo10_pct": RIF_GTT_RITARDO10_PCT,
                 "rif_gtt_fonte": "rapporto di sostenibilita' GTT 2025: passaggi bus/tram in ritardo > 10 minuti, anno 2025 "
                                  "(docs/rapporti/RIASSUNTO_RAPPORTO_SOSTENIBILITA_2025.md)",
                 "fine_corsa_ultime_fermate": FINE_CORSA_ULTIME, "min_fine_corsa": MIN_FINE_CORSA}
    j_citta = {}
    for t, a in punt_citta.items():
        blocco = stat_punt(a)
        blocco.update(stat_reg(reg_citta.get(t, agg_reg())))
        j_citta[t] = blocco
    j_linee = {}
    for (t, linea), a in punt_linea.items():
        c = reg_linea.get((t, linea), agg_reg())
        if a[0] < MIN_PASSAGGI and c[0] < MIN_COPPIE:      # D8
            continue
        blocco = stat_punt(a)
        blocco.update(stat_reg(c))
        fas = {}
        for f in FASCE:
            b = punt_fascia.get((t, linea, f))
            if b and b[0]:
                fas[f] = stat_punt(b)
        blocco["fasce"] = fas
        fc = fine.get((t, linea))
        if fc:
            blocco["fine_corsa"] = {
                "passaggi": len(fc), "ritardo_mediana": mediana([r for r, _ in fc]),
                "km_mediana": round(float(mediana([k for _, k in fc])), 1),
                "min_per_10km": round(float(mediana([r / k * 10.0 for r, k in fc])), 1)}
        j_linee.setdefault(linea, {})[t] = blocco

    # tram contro bus: aggregati per modo (puntualita' dai passaggi; regolarita' sommando le linee del modo)
    reg_modo = {}
    for (t, linea), c in reg_linea.items():
        r = reg_modo.setdefault((t, modo_linea.get(linea, "bus")), agg_reg())
        for i in range(4):
            r[i] += c[i]
    j_modi = {}
    for (t, modo), a in punt_modo.items():
        blocco = stat_punt(a)
        blocco.update(stat_reg(reg_modo.get((t, modo), agg_reg())))
        j_modi.setdefault(modo, {})[t] = blocco

    # linee utili (script 87) contro le altre: somme dei contatori, non medie di percentuali
    j_utili = None
    utili_set = set()
    if POPOLARITA.exists():
        pop = json.loads(POPOLARITA.read_text(encoding="utf-8"))
        utili_set = {x["linea"] for x in pop["linee"] if x.get("utile")}
        j_utili = {}
        for t in TIPI:
            gruppi = {"utili": [0, 0, 0], "altre": [0, 0, 0]}      # passaggi, ritardo>5, ritardo>10
            coppie = {"utili": agg_reg(), "altre": agg_reg()}
            for (tt, linea), a in punt_linea.items():
                if tt != t:
                    continue
                k = "utili" if linea in utili_set else "altre"
                gruppi[k][0] += a[0]
                gruppi[k][1] += a[3]
                gruppi[k][2] += a[5]
                c = reg_linea.get((t, linea))
                if c:
                    for i in range(4):
                        coppie[k][i] += c[i]
            if gruppi["utili"][0] or gruppi["altre"][0]:
                j_utili[t] = {k: {"passaggi": g[0], "ritardo": pct(g[1], g[0]), "ritardo10": round(100.0 * g[2] / g[0], 2) if g[0] else 0.0, "ritardo10_n": g[2],
                                  "coppie": coppie[k][0], "grappolo_buco": pct(coppie[k][1] + coppie[k][2], coppie[k][0])}
                              for k, g in gruppi.items()}

    # ---------- B1 e B2: confronto con GTT ----------
    q2 = lambda x, n: round(100.0 * x / n, 2) if n else None
    tipi_ok = [t for t in TIPI if def_cnt[("a", t)][0]]
    def settimana(valori):
        """Media pesata 5/1/1 delle percentuali dei tipi di giorno presenti (pesi riscalati se ne manca uno)."""
        pv = [(PESI_SETTIMANA[t], valori[t]) for t in tipi_ok if valori.get(t) is not None]
        return round(sum(w * v for w, v in pv) / sum(w for w, _ in pv), 2) if pv else None
    j_def = {}
    for d_, nome_ in DEFINIZIONI:
        per_t = {}
        for t in tipi_ok:
            n_, o5_, o10_, an_ = def_cnt[(d_, t)]
            per_t[t] = {"passaggi": n_, "ritardo5": o5_, "ritardo10": o10_, "ritardo5_pct": q2(o5_, n_), "ritardo10_pct": q2(o10_, n_),
                        "anticipo_pct": q2(an_, n_)}
        j_def[d_] = {"nome": nome_, "per_tipo": per_t,
                     "settimana": {"ritardo5_pct": settimana({t: v["ritardo5_pct"] for t, v in per_t.items()}),
                                   "ritardo10_pct": settimana({t: v["ritardo10_pct"] for t, v in per_t.items()})}}
    j_sp = {}
    for sp_ in SPOSTAMENTI_MIN:
        j_sp[f"{sp_:+d}"] = {t: {"ritardo5_pct": q2(sh_cnt[(t, sp_)][1], sh_cnt[(t, sp_)][0]),
                                 "ritardo10_pct": q2(sh_cnt[(t, sp_)][2], sh_cnt[(t, sp_)][0])} for t in tipi_ok}
    j_forbice = None
    if gps:
        j_forbice = {}
        for t in tipi_ok:
            n_, o5_, o10_, _an = def_cnt[("a", t)]
            m_ = mancanti[t]
            giorni_t = sorted(((g_, c_) for (tt_, g_), c_ in giorno_cnt.items() if tt_ == t),
                              key=lambda x: -(x[1][2] / x[1][0] if x[1][0] else 0))
            k_ = max(1, math.ceil(QUOTA_GIORNI_PEGGIORI * len(giorni_t)))
            peggiori = giorni_t[:k_]
            n_p = sum(c_[0] for _, c_ in peggiori)
            r5_p = sum(c_[1] for _, c_ in peggiori) / n_p if n_p else 0.0
            r10_p = sum(c_[2] for _, c_ in peggiori) / n_p if n_p else 0.0
            j_forbice[t] = {
                "passaggi_con_gps": n_, "passaggi_senza_gps": m_, "giorni": len(giorni_t),
                "giorni_peggiori": [g_ for g_, _ in peggiori],
                "quota_peggiori_ritardo5_pct": round(100 * r5_p, 2), "quota_peggiori_ritardo10_pct": round(100 * r10_p, 2),
                "ritardo10_pct": {"misurato": q2(o10_, n_), "mancanti_puntuali": q2(o10_, n_ + m_),
                                  "mancanti_come_peggiori": q2(o10_ + m_ * r10_p, n_ + m_)},
                "ritardo5_pct": {"misurato": q2(o5_, n_), "mancanti_puntuali": q2(o5_, n_ + m_),
                                 "mancanti_come_peggiori": q2(o5_ + m_ * r5_p, n_ + m_)}}
    confronto_gtt = {"riferimento_gtt_ritardo10_pct": RIF_GTT_RITARDO10_PCT, "pesi_settimana": PESI_SETTIMANA,
                     "fonte": fonte, "definizioni": j_def,
                     "incertezza": {"spostamento_min": j_sp, "senza_gps": j_forbice}}

    json_out = {
        "generato": datetime.now().astimezone().isoformat(timespec="seconds"),
        "tag": TAG, "periodo": per, "giorni": giorni_tipo, "parametri": parametri,
        "scarti": scarti, "citta": j_citta, "linee": j_linee,
        "modi": j_modi, "modo_linea": modo_linea,
        "corse_fine": {"osservate": corse_osservate, "con_fine_corsa": corse_con_fine}}
    json_out["fonte"] = fonte
    json_out["confronto_gtt"] = confronto_gtt
    json_out["fasce_feriale"] = {f: stat_punt(punt_citta_fascia[("0", f)]) for f in FASCE if punt_citta_fascia.get(("0", f)) and punt_citta_fascia[("0", f)][0]}   # per la scheda 1 (non si legge piu' dal rapporto)
    if gps:
        # il feed resta solo come confronto: stessi campi di "citta" e "modi"
        reg_modo_f = {}
        for (t, linea), cc in conf_reg_linea.items():
            r = reg_modo_f.setdefault((t, modo_linea.get(linea, "bus")), agg_reg())
            for i in range(4):
                r[i] += cc[i]
        cf_citta = {}
        for t, a in conf_citta.items():
            b = stat_punt(a)
            b.update(stat_reg(conf_reg_citta.get(t, agg_reg())))
            cf_citta[t] = b
        cf_modi = {}
        for (t, modo), a in conf_modo.items():
            b = stat_punt(a)
            b.update(stat_reg(reg_modo_f.get((t, modo), agg_reg())))
            cf_modi.setdefault(modo, {})[t] = b
        json_out["confronto_feed"] = {
            "citta": cf_citta, "modi": cf_modi, "scarti": conf_scarti,
            "max_lettura_lontana_min": MAX_LETTURA / 60,
            "lettura_lontana_per_tipo": {t: {"scartati": v[0], "ritardo10": v[1]} for t, v in lontane.items()}}
        json_out["giorni_esclusi_gps"] = esclusi_gps
        json_out["copertura_gps"] = {
            "totale": {**cop_tot, "copertura_pct": pct(cop_tot["validi"], cop_tot["programmati"])},
            "per_giorno": {g: {**v, "copertura_pct": pct(v["validi"], v["programmati"])} for g, v in cop_giorno.items()}}
        json_out["regole_gps"] = {"dist_gps_m": DIST_GPS_M, "segmento_max_s": SEGMENTO_MAX_S,
                                  "max_ritardo_vero_min": MAX_RITARDO_VERO_MIN,
                                  "finestra": "dalle 02:00 locali del giorno a 26 ore dalla mezzanotte locale (come lo script 70)",
                                  "fermate_in_ordine": True, "origine": "gps"}
    else:
        json_out["lettura_lontana_per_tipo"] = {t: {"scartati": v[0], "ritardo10": v[1]} for t, v in lontane.items()}
    if j_utili is not None:
        json_out["linee_utili"] = j_utili
        json_out["n_linee_utili"] = len(utili_set)

    # ---------- rapporto ----------
    R = []
    R.append("RISULTATO 4 — Bus in ritardo e bus irregolari")
    R.append("=" * 66)
    if gps:
        R.append("Arrivi misurati con il GPS dei mezzi (dal 21/10); prima dal feed GTT, che sottostima i ritardi: "
                 "vedi CONFRONTO COL FEED")
    R.append(f"Periodo: {per['da']} -> {per['a']}   giorni: feriale {giorni_tipo['0']}, "
             f"sabato {giorni_tipo['1']}, domenica {giorni_tipo['2']}")
    if gps:
        R.append(f"Passaggi con GPS valido: {scarti['usati']} (su {cop_tot['programmati']} programmati dalle corse viste)")
    else:
        tot_sc = scarti["fuori_gtfs"] + scarti["lettura_lontana"] + scarti["usati"]
        R.append(f"Passaggi osservati (ultime letture): {tot_sc}")
        R.append(f"  usati: {scarti['usati']} ({pct(scarti['usati'], tot_sc)}%)")
        R.append(f"  scartati fuori GTFS: {scarti['fuori_gtfs']} ({pct(scarti['fuori_gtfs'], tot_sc)}%)")
        R.append(f"  scartati lettura lontana (>10 min): {scarti['lettura_lontana']} "
                 f"({pct(scarti['lettura_lontana'], tot_sc)}%)")
    R.append("")
    fer = j_citta.get("0", {})
    R.append("I 3 NUMERI (feriale)")
    R.append(f"1. passaggi in ritardo > 5 min: {fer.get('ritardo', 0.0)}%")
    R.append(f"2. coppie a grappolo {fer.get('grappolo', 0.0)}% + a buco {fer.get('buco', 0.0)}%"
             f" = {round(fer.get('grappolo', 0.0) + fer.get('buco', 0.0), 1)}% (linee frequenti)")
    R.append(f"3. ritardo mediano: {fer.get('mediana', 0.0)} min")
    R.append("")
    nomi = {"0": "feriale", "1": "sabato", "2": "domenica"}
    if gps:
        R.append("COPERTURA DEL GPS")
        R.append("giorno    | righe GPS | corse viste | corse GPS fuori GTFS | passaggi programmati | con GPS valido | copertura")
        for g, v in cop_giorno.items():
            R.append(f"{g} | {v['righe']:9} | {v['corse_viste']:11} | {v['corse_fuori_gtfs']:20} | {v['programmati']:20} "
                     f"| {v['validi']:14} | {pct(v['validi'], v['programmati'])}%")
        if esclusi_gps:
            R.append("Giorni esclusi per poco GPS (corse viste sotto " + f"{MIN_QUOTA_GIORNO_GPS:g}" + " volte la mediana dei giorni dello stesso tipo): "
                     + "; ".join(f"{e['giorno']} ({e['corse_viste']} corse viste, mediana {e['mediana_tipo']:g})" for e in esclusi_gps))
        else:
            R.append("Giorni esclusi per poco GPS: nessuno")
        R.append(f"totale: {cop_tot['validi']} passaggi con GPS valido su {cop_tot['programmati']} programmati delle corse viste "
                 f"({pct(cop_tot['validi'], cop_tot['programmati'])}%); le corse mai viste dal GPS non si contano.")
        R.append(f"GPS valido: stessa corsa a meno di {DIST_GPS_M:.0f} m dalla fermata, segmenti di non piu' di {SEGMENTO_MAX_S} s, "
                 f"fermate in ordine, |ritardo| <= {MAX_RITARDO_VERO_MIN:.0f} min; finestra dalle 02:00 locali (come lo script 70).")
        R.append("")
        R.append("CONFRONTO COL FEED (feriale): lo stesso calcolo con il feed GTT di prima (regole D1-D3), per spiegare perche' i numeri sono cambiati")
        R.append("insieme | passaggi | % ritardo>5 | % ritardo>10 | % grappolo+buco | coppie")
        cf = json_out["confronto_feed"]
        for nome, b_feed, b_gps in (("citta'", cf["citta"].get("0"), j_citta.get("0")),
                                    ("tram", cf["modi"].get("tram", {}).get("0"), j_modi.get("tram", {}).get("0")),
                                    ("bus", cf["modi"].get("bus", {}).get("0"), j_modi.get("bus", {}).get("0"))):
            for etichetta, b in (("feed", b_feed), ("GPS", b_gps)):
                if b:
                    R.append(f"{nome:6} {etichetta:4} | {b['passaggi']:8} | {b['ritardo']:11} | {b['ritardo10']:12} "
                             f"| {round(b['grappolo'] + b['buco'], 1):15} | {b['coppie']}")
        R.append(f"Il feed smette di elencare la fermata all'orario programmato: per i mezzi in ritardo la sua stima resta troppo bassa. "
                 f"Scarti D3 del feed (solo confronto): fuori GTFS {cf['scarti']['fuori_gtfs']}, lettura lontana {cf['scarti']['lettura_lontana']}, "
                 f"usati {cf['scarti']['usati']}.")
        R.append("")
    R.append("PUNTUALITA' CITTA' — per tipo di giorno")
    R.append("tipo giorno | passaggi | % anticipo | % puntuale | % ritardo>5 | mediana | p90")
    for t in TIPI:
        if t in j_citta:
            c = j_citta[t]
            R.append(f"{nomi[t]:11} | {c['passaggi']:8} | {c['anticipo']:10} | {c['puntuale']:10} "
                     f"| {c['ritardo']:11} | {c['mediana']:7} | {c['p90']}")
    R.append("")
    R.append("PUNTUALITA' CITTA' — fasce orarie (feriale, ora locale dell'arrivo programmato)")
    R.append("fascia        | passaggi | % anticipo | % puntuale | % ritardo>5 | mediana | p90")
    for f in FASCE:
        b = punt_citta_fascia.get(("0", f))
        if b and b[0]:
            c = stat_punt(b)
            R.append(f"{f:13} | {c['passaggi']:8} | {c['anticipo']:10} | {c['puntuale']:10} "
                     f"| {c['ritardo']:11} | {c['mediana']:7} | {c['p90']}")
    R.append("")

    class_p = sorted(((v["ritardo"], k) for k, v in
                      ((ln, j_linee[ln]["0"]) for ln in j_linee if "0" in j_linee[ln])
                      if v["passaggi"] >= MIN_PASSAGGI_CLASSIFICA and linea_ordinaria(k)), reverse=True)
    R.append(f"10 LINEE PEGGIORI PER % IN RITARDO (feriale, linee ordinarie, >= {MIN_PASSAGGI_CLASSIFICA} passaggi)")
    for i, (val, ln) in enumerate(class_p[:10], 1):
        c = j_linee[ln]["0"]
        R.append(f"{i:2}. linea {ln:<5} {val:5}% in ritardo | {c['passaggi']} passaggi "
                 f"| mediana {c['mediana']} min | p90 {c['p90']} min")
    R.append("")

    class_r = sorted(((round(v["grappolo"] + v["buco"], 1), k) for k, v in
                      ((ln, j_linee[ln]["0"]) for ln in j_linee if "0" in j_linee[ln])
                      if v["coppie"] >= MIN_COPPIE and linea_ordinaria(k)), reverse=True)
    R.append(f"10 LINEE PEGGIORI PER IRREGOLARITA' (feriale, linee ordinarie, >= {MIN_COPPIE} coppie)")
    for i, (val, ln) in enumerate(class_r[:10], 1):
        c = j_linee[ln]["0"]
        R.append(f"{i:2}. linea {ln:<5} {val:5}% grappolo+buco | {c['coppie']} coppie "
                 f"| grappolo {c['grappolo']}% | buco {c['buco']}%")
    R.append("")
    if gps:
        R.append(" con il GPS dei mezzi GTT (Raspberry Pi, una posizione al minuto circa): il ritardo e' l'istante in cui "
                 "il mezzo passa a meno di 60 m dalla fermata meno l'orario programmato; sabato e domenica con pochi giorni:.")
    else:
        R.append(" dal feed GTFS-Realtime GTT; il ritardo è quello stimato dal sistema GTT "
                 "alla fermata nell'ultima lettura prima dell'arrivo; sabato e domenica con 1 solo "
                 "giorno:.")

    # ---- aggiunte del Giro 2 (in coda: il testo di sopra resta com'e') ----
    R.append("")
    R.append("OLTRE 10 MINUTI (stessa misura del rapporto GTT 2025)")
    R.append("tipo giorno | passaggi | % ritardo>5 | % ritardo>10")
    for t in TIPI:
        if t in j_citta:
            c = j_citta[t]
            R.append(f"{nomi[t]:11} | {c['passaggi']:8} | {c['ritardo']:11} | {c['ritardo10']}")
    for modo in MODI:
        c = j_modi.get(modo, {}).get("0")
        if c:
            R.append(f"feriale {modo:5} | {c['passaggi']:8} | {c['ritardo']:11} | {c['ritardo10']}")
    lf = lontane.get("0", [0, 0])
    fer10 = j_citta.get("0", {})
    if fer10 and not gps:
        stima_alta = 100.0 * (fer10["ritardo10_n"] + lf[1]) / (fer10["passaggi"] + lf[0]) if fer10["passaggi"] + lf[0] else 0.0
        R.append(f"ATTENZIONE (feriale): la regola D3 scarta i passaggi con la lettura piu' lontana di {int(MAX_LETTURA / 60)} minuti "
                 f"dall'arrivo stimato; tra gli scartati {lf[1]} (su {lf[0]}) hanno un ritardo oltre {SOGLIA_RITARDO_10:g} minuti, "
                 f"mentre tra i passaggi usati ce ne sono {fer10['ritardo10_n']}. La misura sopra e' quindi un MINIMO; includendo "
                 f"gli scartati (stima alta, lettura non definitiva) l'oltre {SOGLIA_RITARDO_10:g} minuti salirebbe a {round(stima_alta, 2)}%.")
    if gps:
        R.append(f"GTT dichiara {RIF_GTT_RITARDO10_PCT}% nel 2025: il suo metodo non e' pubblicato; noi misuriamo a ogni fermata con il GPS, "
                 f"su pochi giorni di ottobre e sulle linee urbane.")
    else:
        R.append(f"GTT dichiara {RIF_GTT_RITARDO10_PCT}% nel 2025 (anno intero, tutte le linee, bus e tram): confronto solo come "
                 f"ordine di grandezza (noi: pochi giorni di ottobre, linee urbane del feed).")
    R.append("")
    R.append("TRAM CONTRO BUS (feriale)")
    R.append("modo  | passaggi | % ritardo>5 | % ritardo>10 | mediana | % grappolo+buco | coppie")
    for modo in MODI:
        c = j_modi.get(modo, {}).get("0")
        if c:
            R.append(f"{modo:5} | {c['passaggi']:8} | {c['ritardo']:11} | {c['ritardo10']:12} | {c['mediana']:7} "
                     f"| {round(c['grappolo'] + c['buco'], 1):15} | {c['coppie']}")
    R.append("")
    # classifica per ritardo a fine corsa (mediana, minuti); i minuti ogni 10 km restano come colonna (Leo, 21/10: per km premiava le linee corte)
    class_fc = sorted(((v["fine_corsa"]["ritardo_mediana"], v["fine_corsa"]["min_per_10km"], ln) for ln, v in
                       ((ln, j_linee[ln]["0"]) for ln in j_linee if "0" in j_linee[ln])
                       if "fine_corsa" in v and v["fine_corsa"]["passaggi"] >= MIN_FINE_CORSA and linea_ordinaria(ln)),
                      reverse=True)
    R.append(f"RITARDO A FINE CORSA (feriale, linee ordinarie, >= {MIN_FINE_CORSA} passaggi alle ultime "
             f"{FINE_CORSA_ULTIME} fermate): le 10 con piu' ritardo a fine corsa (mediana, minuti); "
             f"i minuti ogni 10 km sono solo una colonna: per km le linee corte vengono premiate")
    for i, (val, per10, ln) in enumerate(class_fc[:10], 1):
        fc = j_linee[ln]["0"]["fine_corsa"]
        R.append(f"{i:2}. linea {ln:<5} {modo_linea.get(ln, 'bus'):5} | ritardo a fine corsa {val} min "
                 f"| corsa {fc['km_mediana']} km | {per10} min ogni 10 km | {fc['passaggi']} passaggi")
    R.append("")
    R.append("LINEE UTILI CONTRO ALTRE (linee utili = quelle dello script 87)")
    if j_utili is None:
        R.append(f"(manca {POPOLARITA.name}: lancia prima scripts/87_popolarita_zone.py)")
    else:
        R.append(f"linee utili: {len(utili_set)}")
        R.append("tipo giorno | gruppo | passaggi | % ritardo>5 | % ritardo>10 | % grappolo+buco | coppie")
        for t in TIPI:
            for k in ("utili", "altre"):
                v = j_utili.get(t, {}).get(k)
                if v:
                    R.append(f"{nomi[t]:11} | {k:6} | {v['passaggi']:8} | {v['ritardo']:11} | {v['ritardo10']:12} "
                             f"| {v['grappolo_buco']:15} | {v['coppie']}")
    # ---- B1 e B2 (in coda) ----
    R.append("")
    R.append("CONFRONTO CON GTT")
    R.append(f"GTT dichiara {RIF_GTT_RITARDO10_PCT}% dei passaggi bus/tram oltre {SOGLIA_RITARDO_10:g} minuti (anno 2025, tutte le linee, metodo non pubblicato).")
    R.append("Qui la stessa quota in 4 definizioni; settimana = media pesata 5 feriale / 1 sabato / 1 domenica delle percentuali.")
    for sog_, chiave_, tit_ in ((SOGLIA_RITARDO_10, "ritardo10", "OLTRE 10 MINUTI"), (SOGLIA_RITARDO, "ritardo5", "OLTRE 5 MINUTI")):
        R.append(f"{tit_}: definizione | feriale | sabato | domenica | settimana | passaggi feriale")
        for d_, nome_ in DEFINIZIONI:
            b_ = j_def[d_]
            cel = [("-" if b_["per_tipo"].get(t, {}).get(chiave_ + "_pct") is None else f"{b_['per_tipo'][t][chiave_ + '_pct']}%") for t in TIPI]
            R.append(f"({d_}) {nome_:<50} | {cel[0]:>7} | {cel[1]:>7} | {cel[2]:>8} | {str(b_['settimana'][chiave_ + '_pct']) + '%':>9} | "
                     f"{b_['per_tipo'].get('0', {}).get('passaggi', 0)}")
    R.append("")
    R.append("Incertezza (i): il numero (a) con tutti i passaggi spostati di -1 e +1 minuto (oltre 10 | oltre 5)")
    for sp_ in SPOSTAMENTI_MIN:
        k_ = f"{sp_:+d}"
        R.append(f"  {k_:>2} min: " + "; ".join(f"{nomi[t]} {j_sp[k_][t]['ritardo10_pct']}% | {j_sp[k_][t]['ritardo5_pct']}%" for t in tipi_ok))
    if j_forbice is not None:
        R.append("Incertezza (ii): passaggi programmati delle corse viste senza GPS valido; forbice sulla quota oltre 10 minuti")
        R.append("  (le corse mai viste dal GPS non si contano; 'peggiori' = quota del 10% dei giorni peggiori dello stesso tipo, almeno 1 giorno)")
        R.append("  tipo giorno | con GPS | senza GPS | misurato | mancanti puntuali | mancanti come i peggiori | quota peggiori")
        for t in tipi_ok:
            f_ = j_forbice[t]
            R.append(f"  {nomi[t]:11} | {f_['passaggi_con_gps']:7} | {f_['passaggi_senza_gps']:9} | {f_['ritardo10_pct']['misurato']:7}% | "
                     f"{f_['ritardo10_pct']['mancanti_puntuali']:16}% | {f_['ritardo10_pct']['mancanti_come_peggiori']:23}% | "
                     f"{f_['quota_peggiori_ritardo10_pct']}%")
    testo = "\n".join(R) + "\n"

    # ---------- controlli (passo 5) a schermo ----------
    C = []
    C.append("CONTROLLI (passo 5)")
    C.append(f"  mediana con arr.delay  : {mediana(per_fonte['delay'])} min "
             f"({len(per_fonte['delay'])} passaggi)")
    C.append(f"  mediana con arr.time   : {mediana(per_fonte['time'])} min "
             f"({len(per_fonte['time'])} passaggi)")
    for k, v in per_seq.items():
        C.append(f"  mediana {k:12}: {mediana(v):6} min ({len(v)} passaggi)")
    for f in FASCE:
        b = punt_citta_fascia.get(("0", f))
        if b and b[0]:
            C.append(f"  feriale {f:13}: {pct(b[3], b[0])}% in ritardo>5 ({b[0]} passaggi)")
    fer_somma = round(fer.get("anticipo", 0) + fer.get("puntuale", 0) + fer.get("ritardo", 0), 1)
    fer_reg = round(fer.get("grappolo", 0) + fer.get("buco", 0) + fer.get("regolare", 0), 1)
    C.append(f"  somma classi puntualita' feriale: {fer_somma}%")
    C.append(f"  somma classi regolarita' feriale: {fer_reg}%")
    # controlli del Giro 2
    def esito(ok):
        return "OK" if ok else "AVVISO"
    for t in TIPI:
        if t in j_citta:
            somma_modi = sum(j_modi.get(m, {}).get(t, {}).get("passaggi", 0) for m in MODI)
            C.append(f"  {esito(somma_modi == j_citta[t]['passaggi'])} {nomi[t]}: passaggi tram + metro + bus = citta' "
                     f"({somma_modi} contro {j_citta[t]['passaggi']})")
            C.append(f"  {esito(j_citta[t]['ritardo10'] <= j_citta[t]['ritardo'])} {nomi[t]}: oltre 10 minuti "
                     f"({j_citta[t]['ritardo10']}%) <= oltre 5 minuti ({j_citta[t]['ritardo']}%)")
    if gps:
        cop_pct = 100.0 * cop_tot["validi"] / cop_tot["programmati"] if cop_tot["programmati"] else 0.0
        C.append(f"  {esito(cop_pct > COPERTURA_MIN_PCT)} copertura GPS {round(cop_pct, 1)}% (OK sopra {COPERTURA_MIN_PCT:g}%)")
        r5 = j_citta.get("0", {}).get("ritardo", 0.0)
        C.append(f"  {esito(RITARDO_GPS_FERIALE_ATTESO[0] <= r5 <= RITARDO_GPS_FERIALE_ATTESO[1])} oltre 5 minuti feriale col GPS: {r5}% "
                 f"(OK fra {RITARDO_GPS_FERIALE_ATTESO[0]:g}% e {RITARDO_GPS_FERIALE_ATTESO[1]:g}%)")
        for t in TIPI:
            if t in j_citta:
                C.append(f"  {esito(-5 <= j_citta[t]['mediana'] <= 10)} {nomi[t]}: mediana {j_citta[t]['mediana']} min fra -5 e +10")
    for t in tipi_ok:
        for d_, _n in DEFINIZIONI:
            n_, o5_, o10_, _an = def_cnt[(d_, t)]
            C.append(f"  {esito(o10_ <= o5_)} {nomi[t]} ({d_}): oltre 10 minuti ({o10_}) <= oltre 5 minuti ({o5_}), su {n_} passaggi")
        a_n = def_cnt[("a", t)][0]
        C.append(f"  {esito(a_n == j_citta[t]['passaggi'])} {nomi[t]} (a): passaggi = totale della citta' ({a_n} contro {j_citta[t]['passaggi']})")
        C.append(f"  {esito(def_cnt[('d', t)][0] + punta_n[t] == a_n)} {nomi[t]}: passaggi fuori punta + di punta = totale "
                 f"({def_cnt[('d', t)][0]} + {punta_n[t]} contro {a_n})")
        C.append(f"  {esito(sh_cnt[(t, 0)][2] == def_cnt[('a', t)][2] and sh_cnt[(t, 0)][0] == a_n)} {nomi[t]}: spostamento 0 uguale a (a)")
        if j_forbice is not None:
            f_ = j_forbice[t]["ritardo10_pct"]
            C.append(f"  {esito(f_['mancanti_puntuali'] <= f_['misurato'] <= f_['mancanti_come_peggiori'] + 1e-9)} {nomi[t]}: forbice "
                     f"{f_['mancanti_puntuali']} <= {f_['misurato']} <= {f_['mancanti_come_peggiori']}")
    quota_fc = 100.0 * corse_con_fine / corse_osservate if corse_osservate else 0.0
    C.append(f"  {esito(quota_fc > 30)} corse osservate con almeno un passaggio di fine corsa: {round(quota_fc, 1)}% "
             f"({corse_con_fine} su {corse_osservate}; OK sopra 30%)")
    C.append(f"  {esito(j_utili is not None)} linee utili: " + (f"{len(utili_set)} linee da {POPOLARITA.name}"
             if j_utili is not None else f"manca {POPOLARITA.name}, blocco non scritto"))
    for k in ("delay", "time"):
        if esempi[k]:
            C.append(f"  esempio {k}: {json.dumps(esempi[k], ensure_ascii=False)}")
    if es_grappolo:
        C.append(f"  esempio grappolo: {json.dumps(es_grappolo, ensure_ascii=False)}")
    testo_c = "\n".join(C) + "\n"

    sys.stdout.write("\n" + testo)
    sys.stdout.write("\n" + testo_c)

    if sposta_s and not prova:
        riassunto = {"sposta_secondi": sposta_s, "periodo": per, "citta": {t: {k: j_citta[t][k] for k in ("passaggi", "anticipo", "puntuale", "ritardo", "ritardo10")} for t in j_citta},
                     "settimana": {d_: j_def[d_]["settimana"] for d_ in j_def}}
        dest = OUT_JSON.with_name(f"risultato4_sposta_{sposta_s}.json")
        dest.write_text(json.dumps(riassunto, ensure_ascii=False), encoding="utf-8")
        print(f"(--sposta-secondi {sposta_s}) scritto solo il riassunto: {dest}")
    elif not prova:
        json_out.update(forbice_lettura(j_citta, j_def))
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(json.dumps(json_out, ensure_ascii=False), encoding="utf-8")
        OUT_RAPPORTO.write_text(testo, encoding="utf-8")
        print(f"Scritto: {OUT_JSON}\nScritto: {OUT_RAPPORTO}")
    else:
        print("(--prova: nessun file scritto)")


if __name__ == "__main__":
    main()
