#!/usr/bin/env python3
"""
04_genera_mappa.py  -  costruisce la mappa interattiva  GTT/mappa_torino.html

Legge gli ULTIMI file in data/raw (quelli scaricati da 01_scarica_dati.py) e li
incorpora in un unico file HTML che si apre con un doppio clic nel browser.
Usa solo la libreria standard di Python. Non scarica niente da internet.

Per avere la mappa aggiornata:
    1) python 01_scarica_dati.py
    2) python 04_genera_mappa.py
    3) apri GTT/mappa_torino.html

Cosa mette nella mappa:
  - OFFERTA programmata GTT per ora e tipo di giorno (feriale/sabato/domenica):
    passaggi alle fermate, corse/ora per linea, passaggi/ora per km2 per zona.
  - TRAFFICO 5T: 5 minuti piu' recenti dei sensori.
  - MEZZI GTT: posizione dei mezzi all'ultimo aggiornamento.
  - (le ZONE STATISTICHE 2011 non si usano piu' dal 18/10; leggi_zone resta per eventuali riusi)
  - SEZIONI DI CENSIMENTO 2021 (se presenti, da 05_prepara_sezioni.py): abitanti, famiglie, abitazioni e indicatori residenti di eta'/occupazione.
  I nuovi indicatori sono profili dei residenti, non conteggi di viaggi, mezzi o orari.
"""
import csv
import io
import json
import math
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    candidata = Path.home() / "Desktop" / "GTT"
    return candidata if candidata.is_dir() else AQUI.parent


RADICE = trova_radice()
RAW = RADICE / "data" / "raw"
# il modello della pagina sta in GTT/scripts: lo cerco li' anche se questo script e' stato copiato altrove
TEMPLATE = next((c for c in (AQUI / "mappa_template.html", RADICE / "scripts" / "mappa_template.html") if c.is_file()),
                RADICE / "scripts" / "mappa_template.html")
USCITA = RADICE / "mappa_torino.html"
for _c in (AQUI, RADICE / "scripts"):
    if (_c / "comuni.py").is_file():
        sys.path.insert(0, str(_c))
        break
import comuni  # noqa: E402  (PERIODO fisso dei dati)
from schede.r6 import fattori_auto_mappa  # noqa: E402  (fattore del controllo per i tempi in auto della mappa)
TIPI_GIORNO = ["fer", "sab", "dom"]
csv.field_size_limit(10**8)


def ultimo(prefisso):
    trovati = sorted(RAW.glob(prefisso + "*"))
    if not trovati:
        sys.exit(f"File non trovato in {RAW}: {prefisso}*  (lancia prima 01_scarica_dati.py)")
    return trovati[-1]


# ---------------------------------------------------------------- protobuf (senza librerie)
def _varint(b, i):
    r = s = 0
    while True:
        x = b[i]
        i += 1
        r |= (x & 0x7F) << s
        s += 7
        if not x & 0x80:
            return r, i


def _campi(b):
    i, out = 0, []
    while i < len(b):
        k, i = _varint(b, i)
        fn, wt = k >> 3, k & 7
        if wt == 0:
            v, i = _varint(b, i)
        elif wt == 1:
            v = b[i:i + 8]
            i += 8
        elif wt == 2:
            n, i = _varint(b, i)
            v = b[i:i + n]
            i += n
        elif wt == 5:
            v = b[i:i + 4]
            i += 4
        else:
            raise ValueError(f"tipo protobuf non gestito: {wt}")
        out.append((fn, wt, v))
    return out


def leggi_mezzi(percorso):
    """Posizioni mezzi GTT (GTFS-RT vehicle positions) -> (timestamp_feed, lista)."""
    top = _campi(percorso.read_bytes())
    ts = 0
    for f, w, v in top:
        if f == 1:
            for f2, w2, v2 in _campi(v):
                if f2 == 3:
                    ts = v2
    mezzi = []
    for f, w, v in top:
        if f != 2:
            continue
        ent = {f1: v1 for f1, w1, v1 in _campi(v)}
        if 4 not in ent:
            continue
        veh = {f1: v1 for f1, w1, v1 in _campi(ent[4])}
        if 2 not in veh:
            continue
        pos = {f1: v1 for f1, w1, v1 in _campi(veh[2])}
        if 1 not in pos or 2 not in pos:
            continue
        linea = ""
        if 1 in veh:
            for f1, w1, v1 in _campi(veh[1]):
                if f1 == 5:
                    linea = v1.decode("utf-8", "replace")
        vid = ""
        if 8 in veh:
            for f1, w1, v1 in _campi(veh[8]):
                if f1 == 1:
                    vid = v1.decode("utf-8", "replace")
        mezzi.append({
            "r": linea, "id": vid,
            "la": round(struct.unpack("<f", pos[1])[0], 5),
            "lo": round(struct.unpack("<f", pos[2])[0], 5),
            "ts": veh.get(5, ts),
        })
    return ts, mezzi


# ---------------------------------------------------------------- 5T
def nome_locale(tag):
    return tag.rsplit("}", 1)[-1]


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def leggi_5t(percorso):
    radice = ET.parse(percorso).getroot()
    sensori = []
    for e in radice.iter():
        if nome_locale(e.tag) != "FDT_data":
            continue
        a = e.attrib
        sf = next((c.attrib for c in e if nome_locale(c.tag) == "speedflow"), {})
        sensori.append({
            "id": a.get("lcd1"), "via": a.get("Road_name", ""), "dir": a.get("direction", ""),
            "la": num(a.get("lat")), "lo": num(a.get("lng")), "acc": num(a.get("accuracy")),
            "fl": num(sf.get("flow")), "v": num(sf.get("speed")), "per": num(a.get("period")) or 5,
        })
    meta = {k: radice.attrib.get(k) for k in ("generation_time", "start_time", "end_time")}
    return meta, [s for s in sensori if s["la"] is not None and s["lo"] is not None]


def leggi_sensori_tipici(sensori):
    """Traffico tipico dei sensori dallo script 26 (data/processed/velocita_5t.json, solo letture affidabili).
    Ritorna {"meta": {periodo, giorni}, "s": {id: [72 voci: [km/h, veicoli/ora] o 0]}} o None. Indice = tipo*24 + ora."""
    f = RADICE / "data" / "processed" / "velocita_5t.json"
    if not f.is_file():
        print("  (velocita_5t.json non trovato: lancia 26_velocita_5t.py; i sensori restano senza dati)")
        return None
    j = json.loads(f.read_text(encoding="utf-8"))
    ids = {str(x["id"]) for x in sensori}
    out, celle_ok = {}, 0
    for sid, sd in j["sensori"].items():
        voci = [0] * 72
        for tipo, ore in sd.get("celle", {}).items():
            for ora, c in ore.items():
                if c.get("ok") and c.get("v") is not None:
                    voci[int(tipo) * 24 + int(ora)] = [round(c["v"], 1), round(c["f"])]
                    celle_ok += 1
        if any(voci):
            out[sid] = voci
    giorni = {k: v for k, v in j["giorni"].items()}
    for t, nome in (("0", "feriali"), ("1", "sabati"), ("2", "domeniche")):
        if giorni.get(t, 0) < VEL_GIORNI_MIN:
            print(f"  AVVISO: sensori 5T: solo {giorni.get(t, 0)} giorni {nome} (meno di {VEL_GIORNI_MIN}): media provvisoria")
    print(f"  sensori tipici: {len(out)} sensori con dati ({len(set(out) & ids)} presenti nell'XML 5T), {celle_ok} celle ok, "
          f"periodo {j['periodo']['da']} - {j['periodo']['a']}, giorni {giorni}")
    return {"meta": {"periodo": j["periodo"], "giorni": giorni}, "s": out}


# ---------------------------------------------------------------- GTFS
def leggi_csv(z, nome):
    with z.open(nome) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")))


def data_gtfs(s):
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))


# Giorni tipici FISSI: prima si prendevano "il prossimo martedi', sabato e
# domenica" rispetto al giorno in cui si rigenera la mappa, che poteva cadere sul cambio dell'ora (25/10)
# o su un festivo. Si cambiano qui, con giorni normali dentro la validita' del GTFS.
DATE_FISSE = {"fer": date(2026, 11, 10), "sab": date(2026, 11, 14), "dom": date(2026, 11, 15)}


# Accessibilita' in forma compatta: erano dizionari con i nomi dei gruppi ripetuti
# per ognuna delle 24 ore di ognuna delle ~8.300 sezioni (14,6 MB su 23,6 della mappa). Ora:
#   [ [piedi: 5 valori nell'ordine di GRUPPI_ACC], [24 ore: 5 valori o null] ]
# La mappa (espandiAcc in mappa_template.html) ricostruisce gli stessi dizionari all'avvio: valori identici.
GRUPPI_ACC = ["scuole", "salute", "cibo", "fermate", "verde"]


def compatta_acc(piedi, tp):
    altri = set(piedi) | {g for v in tp.values() for g in v}
    ore_strane = set(tp) - {f"{h:02d}" for h in range(24)}
    if altri - set(GRUPPI_ACC) or ore_strane:
        print(f"  AVVISO: gruppi o ore non previsti {sorted(altri - set(GRUPPI_ACC))} {sorted(ore_strane)}: lascio la forma estesa")
        return {"piedi": piedi, "tp": tp}
    riga = lambda d: [d.get(g) for g in GRUPPI_ACC]
    return [riga(piedi), [riga(tp[f"{h:02d}"]) if f"{h:02d}" in tp else None for h in range(24)]]


# ---------------------------------------------------------------- peso della pagina (giro 4, 21/10)
# Numeri interi in forma di testo corto. Alfabeto di 89 simboli (ASCII 35-126 senza "/", "<" e "\\", cosi' niente
# escape nel JSON e niente "</script>"). Un numero >= 0 si scrive a cifre: i simboli 0..63 chiudono il numero, i
# simboli 64..88 sono cifre intermedie in base 25 (le piu' basse per prime). Valori fino a 63 = 1 simbolo.
# I numeri con segno passano da zigzag (x>=0 -> 2x, x<0 -> -2x-1). Il lettore e' in mappa_template.html
# (blocco DECODIFICA): le due parti vanno cambiate insieme.
ALFA = "".join(chr(c) for c in range(35, 127) if c not in (47, 60, 92))
CD_FINE = 64
CD_BASE = len(ALFA) - CD_FINE


def cod_nn(z):
    """Intero >= 0 -> testo."""
    out = []
    while z >= CD_FINE:
        out.append(ALFA[CD_FINE + z % CD_BASE])
        z //= CD_BASE
    out.append(ALFA[z])
    return "".join(out)


def cod_int(x):
    """Intero con segno -> testo (zigzag)."""
    return cod_nn(2 * x if x >= 0 else -2 * x - 1)


def decod_nn(s):
    """Testo -> lista di interi >= 0 (solo per le prove)."""
    out, acc, mul = [], 0, 1
    for ch in s:
        d = ALFA.index(ch)
        if d >= CD_FINE:
            acc += (d - CD_FINE) * mul
            mul *= CD_BASE
        else:
            out.append(acc + d * mul)
            acc, mul = 0, 1
    return out


def decod_int(s):
    return [(z >> 1) if z % 2 == 0 else -((z + 1) >> 1) for z in decod_nn(s)]


def compatta_acc_testo(acc):
    """acc compatto [piedi(5), 24 ore(5 ciascuna)] -> testo con le differenze dall'ora precedente
    (le ore coi mezzi si somigliano molto: 1,6 MB invece di 4,6). Ogni altra forma resta com'e'."""
    if not (isinstance(acc, list) and len(acc) == 2 and len(acc[0]) == 5 and isinstance(acc[1], list) and len(acc[1]) == 24):
        return acc
    righe = [acc[0]] + acc[1]
    if any(not isinstance(r, list) or len(r) != 5 or any(type(v) is not int for v in r) for r in righe):
        return acc
    prec, out = [0] * 5, []
    for r in righe:
        out.extend(cod_int(v - q) for v, q in zip(r, prec))
        prec = r
    return "".join(out)


def compatta_vcomp(vc):
    """{occ, ist, aff, anz} (3 decimali) -> testo di 4 numeri: millesimi + 1, 0 = manca. Gli altri campi
    (la mappa non li legge) si tolgono. Se i valori non sono a 3 decimali resta il dizionario."""
    ch = ("occ", "ist", "aff", "anz")
    if not vc:
        return 0
    num = []
    for k in ch:
        v = vc.get(k)
        if v is None:
            num.append(0)
            continue
        m = round(v * 1000)
        if abs(m - v * 1000) > 1e-6 or m < 0:
            return {k: vc[k] for k in ch if k in vc}
        num.append(m + 1)
    return "".join(cod_nn(x) for x in num)


def compatta_fb(fb):
    """{gruppo: 'zero'|'pochissimo'} -> un intero in base 3 (ordine GRUPPI_ACC); 0 = nessun vuoto."""
    if not fb:
        return 0
    liv = {"pochissimo": 1, "zero": 2}
    if any(g not in GRUPPI_ACC or v not in liv for g, v in fb.items()):
        return fb
    return sum(liv[v] * 3 ** GRUPPI_ACC.index(g) for g, v in fb.items())


M_LAT = 110574.0   # metri per grado di latitudine (basta per una tolleranza di 5 m)
M_LON = 111320.0


def semplifica_anello(anello, tol_m=5.0, dec=4):
    """Anello chiuso [[lat, lon], ...] -> coordinate a `dec` decimali + Douglas-Peucker con tolleranza in metri.
    Non toglie anelli e non ne lascia con meno di 4 punti (quelli gia' piccoli restano com'erano).
    L'anello chiuso si spezza nel punto piu' lontano dal primo e si semplificano le due meta'."""
    if len(anello) < 4:
        return [[round(a, dec), round(b, dec)] for a, b in anello]
    arr = [(round(a, dec), round(b, dec)) for a, b in anello]
    pul = [arr[0]]
    for q in arr[1:]:
        if q != pul[-1]:
            pul.append(q)
    if pul[0] != pul[-1]:
        pul.append(pul[0])
    if len(pul) < 4:
        pul = arr
    if len(pul) <= 4:
        return [list(q) for q in pul]
    cl = M_LON * math.cos(math.radians(pul[0][0]))
    xy = [(b * cl, a * M_LAT) for a, b in pul]

    def dp(i0, i1, tieni):
        pila = [(i0, i1)]
        while pila:
            a, b = pila.pop()
            ax, ay = xy[a]
            dx, dy = xy[b][0] - ax, xy[b][1] - ay
            den = math.hypot(dx, dy)
            dmax, imax = -1.0, -1
            for i in range(a + 1, b):
                px_, py_ = xy[i]
                d = math.hypot(px_ - ax, py_ - ay) if den == 0 else abs(dy * (px_ - ax) - dx * (py_ - ay)) / den
                if d > dmax:
                    dmax, imax = d, i
            if dmax > tol_m:
                tieni[imax] = True
                pila.append((a, imax))
                pila.append((imax, b))

    n = len(pul)
    lontano = max(range(1, n - 1), key=lambda i: (xy[i][0] - xy[0][0]) ** 2 + (xy[i][1] - xy[0][1]) ** 2)
    tieni = [False] * n
    tieni[0] = tieni[n - 1] = tieni[lontano] = True
    dp(0, lontano, tieni)
    dp(lontano, n - 1, tieni)
    ris = [list(pul[i]) for i in range(n) if tieni[i]]
    return ris if len(ris) >= 4 else [list(q) for q in pul]


def compatta_forma(anelli, dec=4):
    """Forma di una sezione (lista di anelli) -> un testo: anelli separati da spazio; per ognuno il primo punto
    e poi le differenze, in unita' di 10^-dec gradi (lat, lon); l'ultimo punto (= il primo) non si scrive."""
    scala = 10 ** dec
    anelli_s = []
    for a in anelli:
        s = semplifica_anello(a, 5.0, dec)
        if s[0] != s[-1]:
            s.append(list(s[0]))
        anelli_s.append(s)
    parti = []
    for s in anelli_s:
        prec, out = (0, 0), []
        for la, lo in s[:-1]:
            q = (round(la * scala), round(lo * scala))
            out.append(cod_int(q[0] - prec[0]) + cod_int(q[1] - prec[1]))
            prec = q
        parti.append("".join(out))
    return " ".join(parti), anelli_s


def compatta_riquadro(anelli):
    """Riquadro della sezione dalle forme ORIGINALI (5 decimali): lat min, lon min, altezza, larghezza, in 10^-5
    gradi. Serve a tenere il centro della sezione identico a prima anche dopo la semplificazione."""
    lat = [round(p[0] * 1e5) for a in anelli for p in a]
    lon = [round(p[1] * 1e5) for a in anelli for p in a]
    return cod_int(min(lat)) + cod_int(min(lon)) + cod_int(max(lat) - min(lat)) + cod_int(max(lon) - min(lon))


def compatta_fermate(stops):
    """Passaggi per ora (72 valori: 3 tipi di giorno x 24 ore) in un testo di 72 numeri."""
    for s in stops:
        d = s["d"]
        if isinstance(d, list) and len(d) == 72 and all(type(v) is int and v >= 0 for v in d):
            s["d"] = "".join(cod_nn(v) for v in d)
    return stops


COLONNE_SEZ = ["p", "a", "c", "sen", "pf1", "pf3", "v", "r1"]      # L11: «Chi abita qui» ha 3 viste (densita', anziani, persone sole)


def compatta_sezioni(sez):
    """Elenco di sezioni (dizionari) -> colonne: un elenco per campo, cosi' i nomi dei campi non si ripetono
    8.300 volte. Il campo ab (abitazioni) non era letto dalla mappa e si toglie. Ordine di ogni colonna = ordine
    delle sezioni."""
    col = {k: [x.get(k) for x in sez] for k in COLONNE_SEZ}
    col["g"], col["bb"] = [], []
    for x in sez:
        testo, _ = compatta_forma(x["g"])
        col["g"].append(testo)
        col["bb"].append(compatta_riquadro(x["g"]))
    col["acc"] = [compatta_acc_testo(x["acc"]) for x in sez]
    col["vc"] = [compatta_vcomp(x["vcomp"]) for x in sez]
    col["fb"] = [compatta_fb(x["fb"]) for x in sez]
    col["n"] = len(sez)
    return col


def catalogo_ridotto(indice):
    """Dell'indice del catalogo alla mappa servono solo id, nome, tipo e numero di elementi di ogni dato:
    licenza, CRS, campi mancanti e anomalie non si mostrano piu' (restano nei file di data/processed/catalogo)."""
    if not indice:
        return indice
    return {"gruppi": [{"id": g["id"], "nome": g.get("nome", g["id"]),
                        "dati": [{"id": d["id"], "nome": d.get("nome", d["id"]), "tipo": d.get("tipo"),
                                  "n": (d.get("stat") or {}).get("elementi")} for d in g.get("dati", [])]}
                       for g in indice.get("gruppi", [])]}


def date_riferimento(inizio, fine):
    """Un martedi', un sabato e una domenica tipici (DATE_FISSE); se una data e' fuori dalla validita' del
    feed, AVVISO e si torna alla regola vecchia (il prossimo giorno di quel tipo) solo per quella data."""
    out = {}
    oggi = max(date.today(), inizio)
    for chiave, wd in (("fer", 1), ("sab", 5), ("dom", 6)):
        fissa = DATE_FISSE.get(chiave)
        if fissa and inizio <= fissa <= fine and fissa.weekday() == wd:
            out[chiave] = fissa
            continue
        print(f"  AVVISO: data fissa {fissa} non valida per '{chiave}' (feed {inizio} - {fine}): uso la regola vecchia")
        d = oggi
        while d.weekday() != wd:
            d += timedelta(days=1)
        if d > fine:
            d -= timedelta(days=7)
        out[chiave] = d
    return out


def servizi_attivi(cal, eccezioni, d):
    giorni = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    attivi = set()
    for r in cal:
        if data_gtfs(r["start_date"]) <= d <= data_gtfs(r["end_date"]) and r[giorni[d.weekday()]] == "1":
            attivi.add(r["service_id"])
    for r in eccezioni:
        if data_gtfs(r["date"]) == d:
            if r["exception_type"] == "1":
                attivi.add(r["service_id"])
            elif r["exception_type"] == "2":
                attivi.discard(r["service_id"])
    return attivi


def semplifica(punti, tol):
    """Douglas-Peucker su lista di (lat, lon); tol in gradi."""
    if len(punti) < 3:
        return punti
    coslat = math.cos(math.radians(punti[0][0]))
    p = [(x * 1.0, y * coslat) for x, y in punti]
    tieni = [False] * len(p)
    tieni[0] = tieni[-1] = True
    pila = [(0, len(p) - 1)]
    while pila:
        a, b = pila.pop()
        ax, ay = p[a]
        bx, by = p[b]
        dx, dy = bx - ax, by - ay
        den = math.hypot(dx, dy)
        dmax, imax = 0.0, -1
        for i in range(a + 1, b):
            px, py = p[i]
            d = math.hypot(px - ax, py - ay) if den == 0 else abs(dy * (px - ax) - dx * (py - ay)) / den
            if d > dmax:
                dmax, imax = d, i
        if dmax > tol and imax > 0:
            tieni[imax] = True
            pila.append((a, imax))
            pila.append((imax, b))
    return [punti[i] for i in range(len(punti)) if tieni[i]]


def elabora_gtfs(percorso):
    z = zipfile.ZipFile(percorso)
    info = leggi_csv(z, "feed_info.txt")[0]
    inizio, fine = data_gtfs(info["feed_start_date"]), data_gtfs(info["feed_end_date"])
    giorni = date_riferimento(inizio, fine)
    cal = leggi_csv(z, "calendar.txt")
    ecc = leggi_csv(z, "calendar_dates.txt") if "calendar_dates.txt" in z.namelist() else []
    attivi = [servizi_attivi(cal, ecc, giorni[k]) for k in TIPI_GIORNO]

    rotte = {}
    for r in leggi_csv(z, "routes.txt"):
        rotte[r["route_id"]] = {"s": r["route_short_name"] or r["route_id"], "t": int(r["route_type"] or 3),
                                "l": r["route_long_name"], "f": [0] * 72}
    viaggi = {}
    forme = defaultdict(Counter)
    for r in leggi_csv(z, "trips.txt"):
        flags = tuple(r["service_id"] in a for a in attivi)
        viaggi[r["trip_id"]] = (r["route_id"], flags, r.get("direction_id", ""))
        if r.get("shape_id"):
            forme[(r["route_id"], r.get("direction_id", ""))][r["shape_id"]] += 1

    fermate = {r["stop_id"]: r for r in leggi_csv(z, "stops.txt")}
    dep = defaultdict(lambda: [0] * 72)
    linee_fermata = defaultdict(set)
    inizio_corsa = {}
    with z.open("stop_times.txt") as f:
        rd = csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig"))
        ix = {n: i for i, n in enumerate(next(rd))}
        i_t, i_d, i_a, i_s, i_q = ix["trip_id"], ix["departure_time"], ix["arrival_time"], ix["stop_id"], ix["stop_sequence"]
        for r in rd:
            v = viaggi.get(r[i_t])
            if not v:
                continue
            rid, flags, _dir = v
            ora = r[i_d] or r[i_a]
            if len(ora) < 2:
                continue
            hh = int(ora[:2]) % 24
            sid = r[i_s]
            seq = int(r[i_q])
            for k in range(3):
                if flags[k]:
                    dep[sid][k * 24 + hh] += 1
            linee_fermata[sid].add(rid)
            prec = inizio_corsa.get(r[i_t])
            if prec is None or seq < prec[0]:
                inizio_corsa[r[i_t]] = (seq, hh)
    for tid, (seq, hh) in inizio_corsa.items():
        rid, flags, _dir = viaggi[tid]
        for k in range(3):
            if flags[k]:
                rotte[rid]["f"][k * 24 + hh] += 1

    # tracciati: una forma per (linea, direzione), la piu' usata
    scelte = {key: c.most_common(1)[0][0] for key, c in forme.items()}
    servono = set(scelte.values())
    pts = defaultdict(list)
    with z.open("shapes.txt") as f:
        rd = csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig"))
        ix = {n: i for i, n in enumerate(next(rd))}
        for r in rd:
            if r[ix["shape_id"]] in servono:
                pts[r[ix["shape_id"]]].append((int(float(r[ix["shape_pt_sequence"]])),
                                               float(r[ix["shape_pt_lat"]]), float(r[ix["shape_pt_lon"]])))
    linee = []
    for (rid, d), sh in sorted(scelte.items()):
        seq = [(la, lo) for _, la, lo in sorted(pts.get(sh, []))]
        seq = semplifica(seq, 0.00010)
        if len(seq) >= 2 and rid in rotte:
            linee.append({"id": rid, "d": d, "p": [[round(a, 5), round(b, 5)] for a, b in seq]})

    stops = []
    for sid, dv in dep.items():
        s = fermate.get(sid)
        if not s or not s["stop_lat"] or not s["stop_lon"]:
            continue
        nomi = sorted({rotte[r]["s"] for r in linee_fermata[sid] if r in rotte})
        stops.append({"id": sid, "n": s["stop_name"], "la": round(float(s["stop_lat"]), 5),
                      "lo": round(float(s["stop_lon"]), 5), "r": ", ".join(nomi[:14]) + ("…" if len(nomi) > 14 else ""),
                      "d": dv})
    meta = {"versione": info.get("feed_version"), "inizio": str(inizio), "fine": str(fine),
            "giorni": {k: str(v) for k, v in giorni.items()},
            "n_linee": len(rotte), "n_fermate_totali": len(fermate)}
    # solo le linee con tracciato o con corse servono al browser
    rotte = {k: v for k, v in rotte.items() if any(v["f"]) or any(l["id"] == k for l in linee)}
    return meta, rotte, linee, stops


# ---------------------------------------------------------------- zone (Gauss-Boaga -> WGS84)
def gb_a_wgs84(E, N):
    """EPSG:3003 (Monte Mario / Italy zone 1) -> WGS84, con traslazione geocentrica a 3 parametri."""
    a, f = 6378388.0, 1 / 297.0
    e2 = 2 * f - f * f
    ep2 = e2 / (1 - e2)
    k0, lon0 = 0.9996, math.radians(9.0)
    x, y = E - 1500000.0, N
    M = y / k0
    mu = M / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
            + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * math.sin(6 * mu) + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))
    C1 = ep2 * math.cos(phi1) ** 2
    T1 = math.tan(phi1) ** 2
    N1 = a / math.sqrt(1 - e2 * math.sin(phi1) ** 2)
    R1 = a * (1 - e2) / (1 - e2 * math.sin(phi1) ** 2) ** 1.5
    D = x / (N1 * k0)
    lat = phi1 - (N1 * math.tan(phi1) / R1) * (
        D ** 2 / 2 - (5 + 3 * T1 + 10 * C1 - 4 * C1 ** 2 - 9 * ep2) * D ** 4 / 24
        + (61 + 90 * T1 + 298 * C1 + 45 * T1 ** 2 - 252 * ep2 - 3 * C1 ** 2) * D ** 6 / 720)
    lon = lon0 + (D - (1 + 2 * T1 + C1) * D ** 3 / 6
                  + (5 - 2 * C1 + 28 * T1 - 3 * C1 ** 2 + 8 * ep2 + 24 * T1 ** 2) * D ** 5 / 120) / math.cos(phi1)
    # geodetiche (Hayford) -> geocentriche -> traslazione -> WGS84
    n = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    X, Y, Zc = n * math.cos(lat) * math.cos(lon), n * math.cos(lat) * math.sin(lon), n * (1 - e2) * math.sin(lat)
    X, Y, Zc = X - 104.1, Y - 49.1, Zc - 9.9
    aw, fw = 6378137.0, 1 / 298.257223563
    ew2 = 2 * fw - fw * fw
    p = math.hypot(X, Y)
    lat2 = math.atan2(Zc, p * (1 - ew2))
    for _ in range(6):
        nw = aw / math.sqrt(1 - ew2 * math.sin(lat2) ** 2)
        lat2 = math.atan2(Zc + ew2 * nw * math.sin(lat2), p)
    return math.degrees(lat2), math.degrees(math.atan2(Y, X))


def _parentesi(s):
    """Interpreta le parentesi annidate del WKT -> liste annidate; le foglie sono liste di (x, y)."""
    pila, corrente, buf = [], [], ""
    for ch in s:
        if ch == "(":
            pila.append(corrente)
            corrente = []
            buf = ""
        elif ch == ")":
            padre = pila.pop()
            if buf.strip():  # parentesi piu' interna: e' un anello di coordinate
                padre.append([tuple(float(t) for t in c.split()[:2]) for c in buf.split(",")])
            else:
                padre.append(corrente)
            buf = ""
            corrente = padre
        else:
            buf += ch
    return corrente[0]


def leggi_zone(percorso):
    z = zipfile.ZipFile(percorso)
    nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
    grezzo = z.read(nome)
    try:
        testo = grezzo.decode("utf-8-sig")
    except UnicodeDecodeError:
        testo = grezzo.decode("cp1252")  # il file del Comune non e' in UTF-8
    righe = list(csv.DictReader(io.StringIO(testo), delimiter=";"))
    zone = []
    for r in righe:
        wkt = r["WKT_GEOM"].strip()
        tipo = wkt.split("(")[0].strip().upper()
        nest = _parentesi(wkt[len(tipo):])
        poligoni = [nest] if tipo == "POLYGON" else nest
        area = 0.0
        out = []
        for poly in poligoni:
            anelli = []
            for k, anello in enumerate(poly):
                a2 = sum(anello[i][0] * anello[(i + 1) % len(anello)][1] - anello[(i + 1) % len(anello)][0] * anello[i][1]
                         for i in range(len(anello))) / 2
                area += abs(a2) if k == 0 else -abs(a2)
                ll = [gb_a_wgs84(x, y) for x, y in anello]
                ll = semplifica(ll, 0.00004)
                anelli.append([[round(a, 5), round(b, 5)] for a, b in ll])
            out.append(anelli)
        zone.append({"c": r["ZONASTAT"], "n": r["DENOM"], "km2": round(area / 1e6, 4), "g": out})
    return zone


def dentro(la, lo, zona):
    for poly in zona["g"]:
        n = 0
        for anello in poly:
            j = len(anello) - 1
            for i in range(len(anello)):
                yi, xi = anello[i]
                yj, xj = anello[j]
                if (xi > lo) != (xj > lo) and la < (yj - yi) * (lo - xi) / (xj - xi) + yi:
                    n += 1
                j = i
        if n % 2 == 1:
            return True
    return False


def assegna_zone(zone, stops):
    for z in zone:
        z["d"] = [0] * 72
        z["nf"] = 0
        lat = [p[0] for poly in z["g"] for anello in poly for p in anello]
        lon = [p[1] for poly in z["g"] for anello in poly for p in anello]
        z["_bb"] = (min(lat), max(lat), min(lon), max(lon))
    fuori = 0
    for s in stops:
        trovata = False
        for z in zone:
            b = z["_bb"]
            if b[0] <= s["la"] <= b[1] and b[2] <= s["lo"] <= b[3] and dentro(s["la"], s["lo"], z):
                z["nf"] += 1
                z["d"] = [a + c for a, c in zip(z["d"], s["d"])]
                trovata = True
                break
        if not trovata:
            fuori += 1
    for z in zone:
        del z["_bb"]
    return fuori


# ---------------------------------------------------------------- velocita' commerciale misurata
# Ora legale italiana (copiata da 06_dati_live.py, che non si importa ne' si modifica)
def _ultima_domenica(anno, mese):
    d = date(anno, mese, 31)
    while d.weekday() != 6:
        d -= timedelta(days=1)
    return d


def _locale(dt_utc):
    a = dt_utc.year
    inizio = datetime(a, 3, _ultima_domenica(a, 3).day, 1, tzinfo=timezone.utc)
    fine = datetime(a, 10, _ultima_domenica(a, 10).day, 1, tzinfo=timezone.utc)
    return dt_utc + timedelta(hours=2 if inizio <= dt_utc < fine else 1)


VEL_GIORNI_MIN = 3     # sotto questi giorni per un tipo di giorno la media e' provvisoria (AVVISO)
VEL_DT_MIN, VEL_DT_MAX = 20, 180   # secondi tra due posizioni consecutive
VEL_MAX_KMH = 90       # oltre: errore GPS, si scarta
VEL_FERMO_M = 20       # spostamento sotto cui il mezzo conta come fermo
VEL_SOSTA_MAX_S = 300  # fermo piu' di 5 minuti di fila = capolinea, si scarta


def _haversine_m(la1, lo1, la2, lo2):
    p1, p2 = math.radians(la1), math.radians(la2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2
    return 12742000 * math.asin(math.sqrt(a))


def calcola_velocita():
    """Velocita' commerciale (fermate incluse) per linea x tipo di giorno x ora, dallo storico dei mezzi. Sola lettura.
    Ritorna (vel, meta) oppure (None, None) se il database manca o e' bloccato."""
    import sqlite3
    # sul PC la raccolta e' ferma: si legge la copia settimanale dal Pi (backup_da_leopi.py)
    db = RADICE / "data" / "storico_backup.sqlite"
    if not db.is_file():
        db = RADICE / "data" / "storico.sqlite"
    if not db.is_file():
        print("  (velocita': ne' storico_backup.sqlite ne' storico.sqlite trovati, livello Velocita' saltato)")
        return None, None
    somme = {}   # (linea, tipo, ora) -> [metri, secondi, campioni, {giorni}]
    primo = ultimo = None
    righe = scartati = 0
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=30)
        try:
            # si scarta la lettura se ts_feed dista piu' di un'ora dal momento in cui e' stata letta:
            # orologio di bordo sbagliato (es. mezzo 2897U, ~3 anni avanti) o posizione vecchia ripetuta dal feed
            fuori_ora = con.execute("SELECT count(*) FROM mezzi_gtt WHERE "
                                    "abs(ts_feed - CAST(strftime('%s', letto_utc) AS INTEGER)) > 3600").fetchone()[0]
            cur = con.execute("SELECT veicolo, linea, ts_feed, lat, lng FROM mezzi_gtt "
                              "WHERE abs(ts_feed - CAST(strftime('%s', letto_utc) AS INTEGER)) <= 3600 "
                              "ORDER BY veicolo, ts_feed")
            veic = linea = None
            base = None          # (ts, lat, lng) ultima posizione di riferimento
            pend = []            # tratti fermi non ancora decisi: (chiave, secondi)

            def chiudi_sosta():
                # il fermo si tiene solo se breve (fermata); lungo = capolinea
                if pend and sum(p[1] for p in pend) <= VEL_SOSTA_MAX_S:
                    for k, s in pend:
                        c = somme.get(k)
                        if c is None:
                            c = somme[k] = [0.0, 0.0, 0, set()]
                        c[1] += s
                        c[2] += 1
                        c[3].add(k[3])
                pend.clear()

            for v, ln, ts, la, lo in cur:
                righe += 1
                if ts is None or la is None or lo is None or not ln:
                    continue
                if v != veic or ln != linea:
                    chiudi_sosta()
                    veic, linea, base = v, ln, (ts, la, lo)
                    continue
                dt = ts - base[0]
                if dt < VEL_DT_MIN:
                    continue                     # feed non aggiornato: si aspetta una posizione piu' nuova
                if dt > VEL_DT_MAX:
                    chiudi_sosta()
                    base = (ts, la, lo)
                    continue
                d = _haversine_m(base[1], base[2], la, lo)
                if d / dt * 3.6 > VEL_MAX_KMH:
                    scartati += 1
                    chiudi_sosta()
                    base = (ts, la, lo)
                    continue
                loc = _locale(datetime.fromtimestamp(base[0], timezone.utc))
                if not comuni.nel_periodo(loc.date(), "gps"):      # periodo fisso (L9b): solo giorni interi di comuni.PERIODO
                    chiudi_sosta()
                    base = (ts, la, lo)
                    continue
                tipo = 1 if loc.weekday() == 5 else 2 if loc.weekday() == 6 else 0
                chiave = (ln, tipo, loc.hour, loc.toordinal())
                if primo is None or base[0] < primo: primo = base[0]
                if ultimo is None or ts > ultimo: ultimo = ts
                if d < VEL_FERMO_M:
                    pend.append((chiave, dt))
                else:
                    chiudi_sosta()
                    c = somme.get(chiave)
                    if c is None:
                        c = somme[chiave] = [0.0, 0.0, 0, set()]
                    c[0] += d; c[1] += dt; c[2] += 1; c[3].add(chiave[3])
                base = (ts, la, lo)
            chiudi_sosta()
        finally:
            con.close()
    except sqlite3.Error as e:
        print(f"  (velocita': database non leggibile ora: {e}; livello Velocita' saltato)")
        return None, None
    # le chiavi hanno anche il giorno: si riuniscono per linea x tipo x ora
    tot = {}
    for (ln, tipo, ora, giorno), (m, s, n, _) in somme.items():
        c = tot.setdefault((ln, tipo, ora), [0.0, 0.0, 0, set()])
        c[0] += m; c[1] += s; c[2] += n; c[3].add(giorno)
    vel = {}
    for (ln, tipo, ora), (m, s, n, gg) in tot.items():
        if s > 0:
            vel.setdefault(ln, {}).setdefault(str(tipo), {})[str(ora)] = [round(m / s * 3.6, 1), n, len(gg)]
    ore = round((ultimo - primo) / 3600, 1) if primo is not None else 0
    # giorni distinti con dati per tipo di giorno (tutto lo storico, non una finestra)
    gg_tipo = {0: set(), 1: set(), 2: set()}
    for (ln, tipo, ora, giorno) in somme:
        gg_tipo[tipo].add(giorno)
    giorni = {str(t): len(g) for t, g in gg_tipo.items()}
    for t, nome in ((0, "feriali"), (1, "sabati"), (2, "domeniche")):
        if len(gg_tipo[t]) < VEL_GIORNI_MIN:
            print(f"  AVVISO: velocita': solo {len(gg_tipo[t])} giorni {nome} nello storico (meno di {VEL_GIORNI_MIN}): media provvisoria")
    meta = {"primo": primo, "ultimo": ultimo, "ore": ore, "righe": righe, "scartati_gps": scartati, "giorni": giorni}
    ore_con_dati = sum(len(o) for t in vel.values() for o in t.values())
    print(f"  velocita': {len(vel)} linee con dati, {ore_con_dati} celle linea/tipo/ora, {ore} ore di storico, "
          f"giorni feriali/sabati/domeniche {giorni['0']}/{giorni['1']}/{giorni['2']} "
          f"({righe} righe lette, {scartati} salti GPS scartati, {fuori_ora} righe con ora della posizione lontana oltre 1 h dalla lettura)")
    return vel, meta


# ---------------------------------------------------------------- puntualita' delle linee (Risultato 4)
R4_FILE = RADICE / "data" / "processed" / "risultato4_regolarita.json"
R4_FASCE = {"notte": "0-7", "punta_mattina": "7-9", "giorno": "9-16", "punta_sera": "16-19", "sera": "19-24"}   # D9 del piano


def leggi_r4():
    """Per il tema «Puntualita' delle linee»: {nome linea minuscolo: {tipo: {fascia: % in ritardo oltre 5 min}, "n": {tipo: passaggi}}}
    solo per linee e fasce con almeno min_passaggi passaggi (dal JSON dello script 27). Ritorna (dati, meta) oppure (None, None)."""
    if not R4_FILE.exists():
        print("  (puntualita': risultato4_regolarita.json non trovato, tema Puntualita' senza dati: lancia scripts/27)")
        return None, None
    j = json.loads(R4_FILE.read_text(encoding="utf-8"))
    minimo = j["parametri"]["min_passaggi"]
    out = {}
    for linea, per_tipo in j["linee"].items():
        for tipo, b in per_tipo.items():
            fasce = {f: v["ritardo"] for f, v in (b.get("fasce") or {}).items() if v["passaggi"] >= minimo}
            if not fasce:
                continue
            e = out.setdefault(str(linea).lower(), {"n": {}})
            e[tipo] = fasce
            e["n"][tipo] = b["passaggi"]
    meta = {"periodo": j["periodo"], "soglia_min": j["parametri"]["soglia_ritardo_min"], "min_passaggi": minimo,
            "fasce": R4_FASCE, "giorni": j["giorni"]}
    print(f"  puntualita': {len(out)} linee con dati (almeno {minimo} passaggi per fascia), periodo {j['periodo']['da']} - {j['periodo']['a']}")
    return out, meta


PRO_COM_TORINO = 1272


def nomi_comuni(codici):
    """Nomi dei comuni (PRO_COM -> nome) dal file dei confini ISTAT 2022 (dbf letto a mano, senza librerie)."""
    f = RADICE / "data" / "raw" / "istat" / "confini_2022" / "Limiti01012022_g.zip"
    if not f.is_file():
        print("  (confini ISTAT 2022 non trovati: nelle schede restano i codici dei comuni)")
        return {}
    with zipfile.ZipFile(f) as z:
        b = z.read(next(n for n in z.namelist() if n.endswith("Com01012022_g_WGS84.dbf")))
    n_rec, l_head, l_rec = struct.unpack("<IHH", b[4:12])
    campi, pos = [], 32
    while b[pos] != 0x0D:
        nome = b[pos:pos + 11].split(b"\0")[0].decode()
        campi.append((nome, b[pos + 16]))
        pos += 32
    off, inizio = {}, 1
    for nome, lung in campi:
        off[nome] = (inizio, inizio + lung)
        inizio += lung
    out = {}
    for k in range(n_rec):
        r = b[l_head + k * l_rec: l_head + (k + 1) * l_rec]
        c = int(r[off["PRO_COM"][0]:off["PRO_COM"][1]].strip() or 0)
        if c in codici:
            out[c] = r[off["COMUNE"][0]:off["COMUNE"][1]].decode("utf-8", "replace").strip()
    print(f"  nomi dei comuni: {len(out)} su {len(codici)}")
    return out


def _utm32_a_wgs84(x, y):
    """UTM 32N (WGS84) -> (lat, lon) in gradi (stessa formula dello script 05)."""
    A, F = 6378137.0, 1 / 298.257223563
    E2 = F * (2 - F)
    EP2 = E2 / (1 - E2)
    K0 = 0.9996
    x -= 500000.0
    mu = (y / K0) / (A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    p = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
         + (151 * e1 ** 3 / 96) * math.sin(6 * mu) + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))
    c1 = EP2 * math.cos(p) ** 2
    t1 = math.tan(p) ** 2
    n1 = A / math.sqrt(1 - E2 * math.sin(p) ** 2)
    r1 = A * (1 - E2) / (1 - E2 * math.sin(p) ** 2) ** 1.5
    d = x / (n1 * K0)
    lat = p - (n1 * math.tan(p) / r1) * (d * d / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 * c1 - 9 * EP2) * d ** 4 / 24
                                          + (61 + 90 * t1 + 298 * c1 + 45 * t1 * t1 - 252 * EP2 - 3 * c1 * c1) * d ** 6 / 720)
    lon = (d - (1 + 2 * t1 + c1) * d ** 3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1 * c1 + 8 * EP2 + 24 * t1 * t1) * d ** 5 / 120) / math.cos(p)
    return math.degrees(lat), 9.0 + math.degrees(lon)


def confine_torino():
    """Confine del comune di Torino (PRO_COM 1272) dai confini ISTAT 2022 (WGS84), anelli [[lat, lon], ...] semplificati
    (circa 5 m). Il .shp si legge in sequenza: un record per riga del dbf, nello stesso ordine. [] se il file manca."""
    f = RADICE / "data" / "raw" / "istat" / "confini_2022" / "Limiti01012022_g.zip"
    if not f.is_file():
        print("  (confini ISTAT 2022 non trovati: niente confine di Torino in mappa)")
        return []
    with zipfile.ZipFile(f) as z:
        nomi = z.namelist()
        dbf = z.read(next(n for n in nomi if n.endswith("Com01012022_g_WGS84.dbf")))
        shp = z.read(next(n for n in nomi if n.endswith("Com01012022_g_WGS84.shp")))
    n_rec, l_head, l_rec = struct.unpack("<IHH", dbf[4:12])
    campi, pos = [], 32
    while dbf[pos] != 0x0D:
        campi.append((dbf[pos:pos + 11].split(b"\0")[0].decode(), dbf[pos + 16]))
        pos += 32
    inizio, off = 1, {}
    for nome, lung in campi:
        off[nome] = (inizio, inizio + lung)
        inizio += lung
    anelli, o = [], 100
    for k in range(n_rec):
        lung_parole = struct.unpack(">i", shp[o + 4:o + 8])[0]
        corpo = o + 8
        r = dbf[l_head + k * l_rec: l_head + (k + 1) * l_rec]
        if int(r[off["PRO_COM"][0]:off["PRO_COM"][1]].strip() or 0) == PRO_COM_TORINO and struct.unpack("<i", shp[corpo:corpo + 4])[0] == 5:
            n_parti, n_punti = struct.unpack("<2i", shp[corpo + 36:corpo + 44])
            parti = list(struct.unpack(f"<{n_parti}i", shp[corpo + 44:corpo + 44 + 4 * n_parti])) + [n_punti]
            p0 = corpo + 44 + 4 * n_parti
            pts = struct.unpack(f"<{2 * n_punti}d", shp[p0:p0 + 16 * n_punti])
            for a_, b_ in zip(parti, parti[1:]):
                ring = [_utm32_a_wgs84(pts[2 * i], pts[2 * i + 1]) for i in range(a_, b_)]      # (lat, lon)
                ring = semplifica(ring, 0.00005)
                if len(ring) >= 4:
                    anelli.append([[round(la, 5), round(lo, 5)] for la, lo in ring])
            break
        o = corpo + lung_parole * 2
    print(f"  confine di Torino: {len(anelli)} anelli, {sum(len(a) for a in anelli)} punti")
    return anelli


# ---------------------------------------------------------------- main
def leggi_omi():
    """Legge data/processed/omi_zone.json (O1); ritorna lista compatta o None."""
    f = RADICE / "data" / "processed" / "omi_zone.json"
    comuni.richiedi_fonte(f)      # L12: il file non sta in git; senza, la mappa perderebbe il tema Prezzo delle case: ci si ferma
    try:
        dati_omi = json.loads(f.read_text(encoding="utf-8"))
        # Calcola log: comuni, zone, zone con tipologia ab
        n_comuni = len(dati_omi)
        n_zone = sum(len(c.get("zone", [])) for c in dati_omi)
        n_ab = sum(1 for c in dati_omi for z in c.get("zone", []) if "ab" in (z.get("v") or {}))
        print(f"  OMI: {n_comuni} comuni, {n_zone} zone, {n_ab} zone con tipologia ab")
        return dati_omi
    except Exception as e:
        print(f"  (omi_zone.json non leggibile: {e}; tema OMI saltato)")
        return None


def leggi_imq():
    """Legge data/processed/imq_mappa.json (attivita' 10); ritorna l'oggetto o None."""
    f = RADICE / "data" / "processed" / "imq_mappa.json"
    comuni.richiedi_fonte(f)      # L12: il file non sta in git; senza, la mappa perderebbe il tema Spostamenti: ci si ferma
    try:
        dati_imq = json.loads(f.read_text(encoding="utf-8"))
        n_zone = len(dati_imq.get("zone", []))
        n_od = len(dati_imq.get("od", {}))
        print(f"  IMQ: {n_zone} zone CMTO, {n_od} zone con flussi OD")
        return dati_imq
    except Exception as e:
        print(f"  (imq_mappa.json non leggibile: {e}; tema IMQ saltato)")
        return None


def prepara_catalogo():
    """Legge l'indice del catalogo (11_prepara_catalogo.py) e scrive per la mappa
    un file JS per gruppo in data/catalogo/, cosi' la pagina carica un gruppo
    solo quando viene scelto (senza server: si usa <script src>)."""
    cat_dir = RADICE / "data" / "processed" / "catalogo"
    indice_f = cat_dir / "catalogo.json"
    if not indice_f.is_file():
        print("  (catalogo non trovato: tema Catalogo vuoto; lancia 11_prepara_catalogo.py)")
        return None
    try:
        indice = json.loads(indice_f.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  (catalogo.json non leggibile: {e}; tema Catalogo saltato)")
        return None
    map_dir = RADICE / "data" / "catalogo"
    map_dir.mkdir(parents=True, exist_ok=True)
    n_js = 0
    for g in indice.get("gruppi", []):
        f = cat_dir / f"{g['id']}.json"
        if not f.is_file():
            continue
        testo = f.read_text(encoding="utf-8")
        (map_dir / f"{g['id']}.js").write_text(
            'window.CATALOGO=window.CATALOGO||{};window.CATALOGO["%s"]=%s;' % (g["id"], testo),
            encoding="utf-8")
        n_js += 1
    n_dati = sum(len(g.get("dati", [])) for g in indice.get("gruppi", []))
    print(f"  catalogo: {len(indice.get('gruppi', []))} gruppi, {n_dati} dati, {n_js} file js pronti per il caricamento su richiesta")
    return indice



def main():
    print(f"Cartella del progetto: {RADICE}")
    if not TEMPLATE.is_file():
        sys.exit(f"Manca il modello della pagina: {TEMPLATE}\nLancia lo script da GTT\\scripts oppure copia li' mappa_template.html.")
    # le zone statistiche 2011 non sono piu' disegnate da nessun tema (revisione mappa 18/10): non si leggono
    f_gtfs, f_5t = ultimo("gtt_gtfs_"), ultimo("5t_flussi_")
    f_vp = ultimo("gtt_vehicle_position_")
    print("Uso questi file:", f_gtfs.name, f_5t.name, f_vp.name, sep="\n  ")

    print("Leggo GTFS (qualche secondo)...")
    meta_gtfs, rotte, linee, stops = elabora_gtfs(f_gtfs)
    print(f"  fermate con passaggi: {len(stops)}, linee con tracciato: {len(linee)}")
    meta5t, sensori = leggi_5t(f_5t)
    ts_vp, mezzi = leggi_mezzi(f_vp)
    print(f"  sensori 5T: {len(sensori)}, mezzi GTT: {len(mezzi)}")

    # ---- vulnerabilità (dai file 19 e 23) ----
    vuln_data = {}
    f_vuln = RADICE / "data" / "processed" / "vulnerabilita_mappa.json"
    if f_vuln.is_file():
        vuln_data = json.loads(f_vuln.read_text(encoding="utf-8"))
        print(f"  vulnerabilità mappa: {len(vuln_data['sezioni'])} sezioni")
    vuln = {x["id"]: x for x in vuln_data.get("sezioni", [])}

    # ---- accessibilità per gruppo, a piedi (15') e con mezzi pubblici (45', 4 fasce orarie) ----
    # (dal file 18, tema "Accessibilità ai servizi")
    acc = {}
    f_acc = RADICE / "data" / "processed" / "accessibilita.json"
    if f_acc.is_file():
        acc_data = json.loads(f_acc.read_text(encoding="utf-8"))
        acc = {x["id"]: compatta_acc(x.get("piedi", {}).get("15", {}), x.get("tp", {}))
               for x in acc_data.get("sezioni", [])}
        print(f"  accessibilità a piedi e TP: {len(acc)} sezioni (forma compatta: la mappa la riespande all'avvio)")

    # ---- risultato 1: dove manca un servizio (fase A, per gruppo) + candidati per aggiungerne uno (fase B) ----
    fb_zero = {}
    r1, r1_meta = {}, None
    f_fb = RADICE / "data" / "processed" / "risultato1_vuoti.json"
    if f_fb.is_file():
        fb_data = json.loads(f_fb.read_text(encoding="utf-8"))
        fb_zero = {x["id"]: x.get("manca", {}) for x in fb_data.get("sezioni_manca", [])}
        print(f"  risultato1 (dove manca un servizio): {len(fb_zero)} sezioni segnalate")
        v2 = fb_data.get("v2")
        if v2:
            r1 = {x["id"]: [x["n_mancanti"], x["m"], 1 if x["poco"] else 0, 1 if x["verif"] else 0]
                  for x in v2["sezioni"]}
            r1_meta = {"soglia": v2["soglia_poco_abitata_ab_km2"], "ora_tp": v2["ora_tp_cintura"],
                       "ordine": v2["ordine_bit"], "titolo": v2["titolo"]["residenti_abitati_con_3_o_piu_mancanti"]}
        else:
            print("  AVVISO: lancia prima 21_risultato1_vuoti.py (manca la sezione v2: niente vista 0-5)")
    fb_candidati = {}
    f_fbc = RADICE / "data" / "processed" / "risultato1_candidati.json"
    if f_fbc.is_file():
        fbc_data = json.loads(f_fbc.read_text(encoding="utf-8"))
        for g, gd in fbc_data.get("gruppi", {}).items():
            fb_candidati[g] = [{"lat": c["lat"], "lon": c["lon"], "residenti_guadagnati": c["residenti_guadagnati"],
                                 "n_sezioni_coperte": c["n_sezioni_coperte"]} for c in gd.get("candidati_scelti", [])]
        print(f"  risultato1 (candidati nuovo servizio): {', '.join(f'{g}:{len(v)}' for g, v in fb_candidati.items())}")
    # Risultato 6: zone IMQ, fermate importanti, parcheggi (file unico prodotto dallo script 79-80)
    r6 = None
    f_r6 = RADICE / "data" / "processed" / "risultato6_v2" / "mappa_r6.json"
    if f_r6.is_file():
        r6 = json.loads(f_r6.read_text(encoding="utf-8"))
        r6.update(fattori_auto_mappa())          # tempi in auto: una sola stima, la corretta col controllo (decisione 16 di §2)
        print(f"  risultato6: {len(r6['aree'])} aree, {len(r6['punti_prioritari'])} punti prioritari, "
              f"{len(r6['fermate'])} fermate importanti, {len(r6['parcheggi'])} parcheggi")

    sez, f_sez = [], RADICE / "data" / "processed" / "sezioni_torino.json"
    if f_sez.is_file():
        sez = [{"p": x["p"], "a": x["a"], "g": x["g"], "c": x.get("c", 0), "f": x.get("f", 0), "ab": x.get("ab", 0),
                "occ": x.get("occ"), "p1564": x.get("p1564"), "sen": x.get("sen"),
                "p014": x.get("p014"), "em": x.get("em"), "ist9": x.get("ist9"), "it": x.get("it"),
                "pf1": x.get("pf1"), "pf3": x.get("pf3"),
                "v": vuln.get(x.get("id",""), {}).get("v"),
                "vcomp": vuln.get(x.get("id",""), {}).get("comp", {}),
                "acc": acc.get(x.get("id",""), {}),
                "fb": fb_zero.get(x.get("id",""), {}),
                "r1": r1.get(x.get("id",""))}
               for x in json.loads(f_sez.read_text(encoding="utf-8")) if x["p"] > 0]   # indicatori ISTAT 2021 per residenti
        if r1_meta:
            somma_r1 = sum(x["p"] for x in json.loads(f_sez.read_text(encoding="utf-8"))
                           if str(x["id"]).startswith("1272") and x["p"] > 0 and r1.get(x["id"])
                           and r1[x["id"]][2] == 0 and r1[x["id"]][3] == 0 and r1[x["id"]][0] >= 3)
            esito_r1 = "OK" if somma_r1 == r1_meta["titolo"] else "AVVISO"
            print(f"  {esito_r1}: titolo risultato 1: {somma_r1:,} residenti di Torino abitati con 3+ servizi mancanti "
                  f"(script 21: {r1_meta['titolo']:,}); sezioni con r1: {sum(1 for x in sez if x['r1'])}")
        print(f"  sezioni di censimento abitate: {len(sez)}, abitanti {sum(x['p'] for x in sez)}, famiglie {sum(x['f'] for x in sez)}, abitazioni {sum(x['ab'] for x in sez)}")
    else:
        print("  (sezioni di censimento non trovate: lancia 05_prepara_sezioni.py per il livello Domanda)")

    vel, vel_meta = calcola_velocita()   # None se lo storico non c'e'
    t5 = leggi_sensori_tipici(sensori)   # traffico tipico dei sensori (script 26), al posto di data/stat.js
    r4, r4_meta = leggi_r4()             # puntualita' per linea, dallo script 27 (None se manca)
    omi = leggi_omi()
    imq = leggi_imq()
    catalogo = prepara_catalogo()   # indice dei nuovi dati + file js per il caricamento su richiesta

    comuni = nomi_comuni({int(x["c"]) for x in sez if x.get("c")} | {PRO_COM_TORINO}) if sez else {}
    dati = {
        "vel": vel or {}, "vel_meta": vel_meta,
        "r4": r4 or {}, "r4_meta": r4_meta,   # puntualita' per linea e fascia (tema «Puntualita' delle linee»)
        "t5": t5,
        "confine_torino": confine_torino(),   # anelli del comune di Torino (linea scura in mappa)
        "comuni": comuni,   # PRO_COM -> nome, per schede e tooltip
        "omi": omi,     # OMI quote immobiliari
        "imq": imq,     # Mobilita' IMQ 2022 (attivita' 10)
        "catalogo": catalogo,   # indice del catalogo (i dati per gruppo stanno in data/catalogo/*.js)
        "meta": {
            "costruita_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "gtfs": meta_gtfs, "t5": meta5t, "mezzi_ts": ts_vp,
            "file": {"gtfs": f_gtfs.name, "t5": f_5t.name, "mezzi": f_vp.name},
        },
        "rotte": rotte, "linee": linee, "fermate": stops, "sensori": sensori, "sezioni": sez,
        "fb_candidati": fb_candidati,
        "r1_meta": r1_meta,
        "r6": r6,
    }
    f_rt = RADICE / "data" / "processed" / "dove_nascono_ritardi.json"       # script 106: tratti dove i bus perdono tempo (tema «Dove i bus perdono tempo»)
    if f_rt.is_file():
        rt = json.loads(f_rt.read_text(encoding="utf-8"))
        if not rt.get("prova"):
            dati["ritardi_tratti"] = rt["tratti_mappa"]
            print(f"Tratti dove i bus perdono tempo: {len(rt['tratti_mappa']['tratti'])}")
    dati["sezioni"] = compatta_sezioni(sez)
    dati["fermate"] = compatta_fermate(stops)
    dati["catalogo"] = catalogo_ridotto(catalogo)
    testo = json.dumps(dati, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace('"__DATI__"', testo)
    try:   # chiavi da browser degli sfondi (CARTO, Esri) da config_locale.json; senza, quello sfondo non compare
        import config_locale
        html = config_locale.metti_chiavi_mappa(html)
    except ImportError:
        pass
    USCITA.write_text(html, encoding="utf-8")
    print(f"\nMappa creata: {USCITA}  ({USCITA.stat().st_size / 1e6:.1f} MB)")
    print("Aprila con doppio clic (serve internet solo per le mattonelle della cartina).")


if __name__ == "__main__":
    main()
