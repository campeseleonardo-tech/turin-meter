#!/usr/bin/env python3
"""11_prepara_catalogo.py

Costruisce il "catalogo comune" dei nuovi dati: per ogni archivio/tabella
produce un file normalizzato e un indice con i metadati richiesti dal piano
(file, fonte, anno, licenza, formato, copertura, sistema di coordinate) e i
controlli fatti (record, duplicati, campi mancanti, area, anomalie).

Sola lettura sui dati grezzi in data/raw. NON li modifica.

Output (data/processed/catalogo/):
  - catalogo.json      indice: gruppi, metadati e statistiche (senza elementi)
  - <gruppo>.json      dati per la mappa (con gli elementi) e per le simulazioni

Geometrie: i CSV usano WKT_GEOM in EPSG:3003 (Monte Mario / Italy zone 1).
Le COORD_X/Y, quando presenti, sono solo di controllo: per mercati_tematici
sono ~10 volte piu' piccole del WKT (anomalia gia' segnalata nel piano).

Privacy: telefono, email, PEC, URL e nomi di persona (es. NOME_ADD delle
attivita' commerciali) NON entrano nei prodotti.

Uso:  python scripts/11_prepara_catalogo.py
"""

import csv
import io
import json
import math
import struct
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
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
OUT_DIR = RADICE / "data" / "processed" / "catalogo"

# Verifiche sull'anno: molti file del Comune non dichiarano la data.
# "non dichiarato" e' un'informazione utile, non un vuoto da riempire a caso.
NON_DICHIARATO = "non dichiarato nel file"

# Area attesa (Torino + cintura entro ~18 km): lat 44.8-45.5, lon 7.2-8.2.
AREA_MIN = (44.80, 7.20)
AREA_MAX = (45.50, 8.20)


# ------------------------------------------------------------------ geometria
def gb_a_wgs84(E, N):
    """EPSG:3003 (Monte Mario / Italy zone 1) -> WGS84 (copia da 04_genera_mappa.py)."""
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
    """WKT -> liste annidate; le foglie sono liste di (x, y). Copia da 04."""
    pila, corrente, buf = [], [], ""
    for ch in s:
        if ch == "(":
            pila.append(corrente)
            corrente = []
            buf = ""
        elif ch == ")":
            padre = pila.pop()
            if buf.strip():
                padre.append([tuple(float(t) for t in c.split()[:2]) for c in buf.split(",")])
            else:
                padre.append(corrente)
            buf = ""
            corrente = padre
        else:
            buf += ch
    return corrente[0]


def semplifica(punti, tol):
    """Douglas-Peucker su lista di (lat, lon); tol in gradi. Copia da 04."""
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


TOL = 0.00002  # ~2 m


def wkt_geometria(wkt):
    """WKT (EPSG:3003) -> ('punto',[la,lo]) | ('linea',[[la,lo],...]) |
    ('poligono',[[[la,lo],...],...])  (una lista di anelli per poligono)."""
    wkt = (wkt or "").strip()
    if not wkt:
        return None
    tipo = wkt.split("(")[0].strip().upper()
    corpo = wkt[len(tipo):].strip()
    try:
        nest = _parentesi(corpo)
    except Exception:
        return None
    if tipo == "POINT":
        x, y = nest[0]
        la, lo = gb_a_wgs84(x, y)
        return ("punto", [round(la, 6), round(lo, 6)])
    if tipo == "LINESTRING":
        ll = [gb_a_wgs84(x, y) for x, y in nest]
        ll = semplifica(ll, TOL) if len(ll) > 2 else ll
        return ("linea", [[round(a, 6), round(b, 6)] for a, b in ll])
    if tipo == "MULTILINESTRING":
        out = []
        for linea in nest:
            ll = [gb_a_wgs84(x, y) for x, y in linea]
            ll = semplifica(ll, TOL) if len(ll) > 2 else ll
            out.append([[round(a, 6), round(b, 6)] for a, b in ll])
        return ("linee", out)
    if tipo == "POLYGON":
        polys = [nest]
    elif tipo == "MULTIPOLYGON":
        polys = nest
    else:
        return None
    out_polys = []
    for poly in polys:
        anelli = []
        for anello in poly:
            ll = [gb_a_wgs84(x, y) for x, y in anello]
            if len(ll) > 4:
                ll = semplifica(ll, TOL)
            if len(ll) >= 4:
                anelli.append([[round(a, 6), round(b, 6)] for a, b in ll])
        if anelli:
            out_polys.append(anelli)
    return ("poligoni", out_polys) if out_polys else None


# ------------------------------------------------------------------ lettura
def decodifica(b):
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("latin-1", "replace")


def leggi_righe_csv(testo, delim=None):
    if delim is None:
        prima = testo.splitlines()[0] if testo.splitlines() else ""
        delim = ";" if prima.count(";") >= prima.count(",") else ","
    return list(csv.DictReader(io.StringIO(testo), delimiter=delim))


def righe_da_fonte(fonte):
    """fonte: ('zipcsv', nomezip, membro) | ('csv', nomefile) | ('shp', nomezip)."""
    tipo = fonte[0]
    if tipo == "zipcsv":
        with zipfile.ZipFile(RAW / fonte[1]) as z:
            return leggi_righe_csv(decodifica(z.read(fonte[2]))), None
    if tipo == "csv":
        return leggi_righe_csv(decodifica((RAW / fonte[1]).read_bytes())), None
    if tipo == "shp":
        return leggi_shp(RAW / fonte[1])
    raise ValueError(f"fonte sconosciuta: {fonte}")


# ---- shapefile (solo geometrie Point) e DBF, senza librerie esterne
def _leggi_dbf(data):
    nrec = struct.unpack("<I", data[4:8])[0]
    hsize = struct.unpack("<H", data[8:10])[0]
    rsize = struct.unpack("<H", data[10:12])[0]
    campi = []
    off = 32
    while data[off] != 0x0D:
        nome = data[off:off + 11].split(b"\x00")[0].decode("latin-1")
        typ = chr(data[off + 11])
        ln = data[off + 16]
        dec = data[off + 17]
        campi.append((nome, typ, ln, dec))
        off += 32
    righe = []
    pos = hsize
    for _ in range(nrec):
        rec = data[pos:pos + rsize]
        pos += rsize
        if not rec or rec[0:1] == b"*":
            continue
        d = {}
        p = 1
        for nome, typ, ln, dec in campi:
            grezzo = rec[p:p + ln]
            p += ln
            testo = grezzo.decode("latin-1", "replace").strip()
            d[nome] = testo
        righe.append(d)
    return righe


def leggi_shp(percorso):
    with zipfile.ZipFile(percorso) as z:
        base = None
        for n in z.namelist():
            if n.endswith(".dbf"):
                base = n[:-4]
        dbf = _leggi_dbf(z.read(base + ".dbf"))
        shp = z.read(base + ".shp")
    # SHP: header 100 byte; ogni record: 8 byte + shape type (int LE) + X,Y (double LE)
    punti = []
    off = 100
    while off < len(shp):
        if off + 12 > len(shp):
            break
        clen = struct.unpack(">I", shp[off + 4:off + 8])[0]
        stype = struct.unpack("<i", shp[off + 8:off + 12])[0]
        if stype == 1:  # Point
            x, y = struct.unpack("<dd", shp[off + 12:off + 28])
            la, lo = gb_a_wgs84(x, y)
            punti.append([round(la, 6), round(lo, 6)])
        elif stype == 0:
            punti.append(None)
        else:
            punti.append(None)
        off += 8 + clen * 2
    righe = []
    for r, p in zip(dbf, punti):
        r["_la"] = p[0] if p else None
        r["_lo"] = p[1] if p else None
        righe.append(r)
    return righe, "shp"


# ------------------------------------------------------------------ registro
# Ogni dato: fonte, metadati e come ricavare id / nome / indirizzo / categoria.
def D(id, nome, archivio, **kw):
    d = {"id": id, "nome": nome, "archivio": archivio}
    d.update(kw)
    return d


FONTE_CT = "Comune di Torino (open data / servizi online)"
LIC_CT = "non dichiarata nel file (presumibilmente open data Comune di Torino, da confermare)"

GRUPPI = [
    {"id": "istruzione", "nome": "Istruzione e assistenza all'infanzia",
     "desc": "Scuole, universita' e servizi per l'infanzia. Luoghi da mostrare in mappa; senza iscritti o capienza sono attrattori potenziali, non numeri di viaggi.",
     "dati": [
         D("scuole", "Scuole (sedi)", ("zipcsv", "scuole_csv.zip", "scuole.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_PT_ING", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["ORDINE"], attr=["TIPOLOGIA", "DETTAGLIO", "STATALE", "PARITARIA", "COMUNALE", "TIPO_SCUOL"],
           atteso=610,
           note="Punti di ingresso delle sedi. ORDINE = ordine di scuola; TIPO_SCUOL distingue sede centrale/plesso/succursale: piu' righe possono essere la stessa scuola."),
         D("universita", "Universita' (sedi e facolta')", ("zipcsv", "universita_csv.zip", "universita.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_UNIVERS", nome_campo="DENOMINAZI", ind_campo="INDIRIZZO",
           cat_campo=["FACOLTA"], attr=[], atteso=29,
           note="Mancano numero di iscritti e flussi: solo attrattore potenziale."),
         D("infanzia_nidi_comunali", "Nidi comunali", ("zipcsv", "servizi_infanzia_csv.zip", "si_nidi_comunali.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_NIDO_CO", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["TIPO"], attr=["CAP_MAX", "NOTE"], atteso=54,
           note="CAP_MAX = capienza massima dichiarata. Piu' righe possono essere lo stesso civico su piani diversi."),
         D("infanzia_nidi_convenzionati", "Nidi convenzionati", ("zipcsv", "servizi_infanzia_csv.zip", "si_nidi_convenzionati.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_NIDO_PR", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["TIPO"], attr=["POSTI", "POSTI_CONV"], atteso=66),
         D("infanzia_nidi_aziendali", "Nidi aziendali", ("zipcsv", "servizi_infanzia_csv.zip", "si_nidi_aziendali.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_NIDO_AZ", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["TIPO"], attr=["POS_TOTALI", "AZIENDA"], atteso=8),
         D("infanzia_micronidi", "Micronidi in famiglia", ("zipcsv", "servizi_infanzia_csv.zip", "si_nidi_micronidi_famiglia.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_MICRONI", nome_campo="ENTE", ind_campo="INDIRIZZO",
           cat_campo=["GESTORE"], attr=["POSTI"], atteso=16),
         D("infanzia_primavera", "Sezioni primavera", ("zipcsv", "servizi_infanzia_csv.zip", "si_primavera.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_INF_PRI", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=[], attr=["NUM_POSTI"], atteso=4),
         D("infanzia_ludoteche", "Ludoteche", ("zipcsv", "servizi_infanzia_csv.zip", "si_ludoteche.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_INF_L", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["TIPO"], attr=[], atteso=30),
         D("infanzia_centri", "Centri per bambini e famiglie", ("zipcsv", "servizi_infanzia_csv.zip", "si_centri.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_INF_CEN", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=[], attr=["ORARIO", "NOTE"], atteso=12),
         D("infanzia_babyparking", "Baby parking", ("zipcsv", "servizi_infanzia_csv.zip", "si_babyparking.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_INF_BP", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=[], attr=["NUM_POSTI"], atteso=15),
     ]},
    {"id": "salute", "nome": "Salute e servizi sociali",
     "desc": "Ospedali, consultori, farmacie e strutture socio-assistenziali. Per accessibilita' e orari; senza volumi misurati non si prevedono utenti.",
     "dati": [
         D("ospedali", "Ospedali (accessi)", ("zipcsv", "ospedali_csv.zip", "ospedali.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_OSPEDAL", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["TIPO_ACCES"], attr=["TIPO_OSPED", "AZIENDA", "ORARIO_VIS"], atteso=44,
           note="Un record non e' un ospedale: piu' accessi (principale, secondario, pronto soccorso) possono appartenere alla stessa struttura."),
         D("consultori", "Consultori", ("zipcsv", "consultori_csv.zip", "consultori.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_CONSULT", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["TIPO_CONSU"], attr=["ORARIO"], atteso=37),
         D("farmacie", "Farmacie", ("zipcsv", "farmacie_csv.zip", "farmacie.csv"), fonte=FONTE_CT,
           anno="2011 circa (le ferie citate sono del 2011)", licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_FARMACI", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["NOTTURNA"], attr=["ORARIO_INV", "ORARIO_EST", "CHIUS_INV", "COMUNALE"], atteso=243,
           note="Dato datato 2011: gli orari sono probabilmente non aggiornati. NOTTURNA segnala il servizio notturno."),
         D("socio_assistenziali", "Strutture socio-assistenziali", ("zipcsv", "strutture_socio_assistenziali_csv.zip", "strutture_socio_assistenziali.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="IDCIVICO", nome_campo="DENOM", ind_campo="INDIRIZZ",
           cat_campo=["SETTORE"], attr=["DIUR_RES", "UTENZA", "PROPRIET", "GESTIONE"], atteso=151,
           note="DIUR_RES distingue servizio diurno (D) e residenziale (R). Nessuna capienza dichiarata."),
     ]},
    {"id": "commercio", "nome": "Commercio, mercati e luoghi d'interesse",
     "desc": "Attivita' commerciali, mercati, luoghi d'interesse e cultura. Le attivita' non hanno una data di chiusura affidabile: non sono tutte aperte.",
     "dati": [
         D("attivita", "Attivita' commerciali (punti)", ("zipcsv", "attivita_commerciali_csv.zip", "attivita_commerciali.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo=None, nome_campo=None, ind_campo="INDIRIZZ",
           cat_campo=["DESC_RIP"], attr=["TIPO_LOC", "MQ_TOT_V", "ZONASTAT", "NCIRCO"], atteso=31271,
           speciale="attivita",
           note="Nessuna data di chiusura affidabile: non assumere che ogni attivita' sia ancora aperta. Nome esercente (NOME_ADD) escluso per privacy."),
         D("mercati", "Mercati (aree)", ("zipcsv", "mercati_csv.zip", "mercati.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="poligoni", id_campo="ID_MERC", nome_campo="DENOM", ind_campo="LUOGO",
           cat_campo=["GIORNI"], attr=[], atteso=42,
           note="Attrattore attivo solo nei giorni di mercato (campo GIORNI)."),
         D("mercati_tematici", "Mercati tematici", ("zipcsv", "mercati_tematici_csv.zip", "mercati_tematici.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_MER_T", nome_campo="DENOM", ind_campo="LUOGO",
           cat_campo=["TEMA"], attr=["CADENZA", "POSTI"], atteso=16,
           note="Anomalia COORD_X/Y ~10 volte piu' piccole del WKT (vedi controllo). Eventi periodici: il campo POSTI e' il numero di banchi."),
         D("luoghi", "Locali storici e luoghi particolari", ("zipcsv", "luoghi_csv.zip", "luoghi.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_LUOGO_L", nome_campo="DESCRIZION", ind_campo="INDIRIZZO",
           cat_campo=["TIPO"], attr=["NOTE"], atteso=21,
           note="Non e' un catalogo generico: solo 'locali storici' e 'luoghi particolari'."),
         D("musei", "Musei", ("zipcsv", "musei_csv.zip", "musei.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_TIPOPTO", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["LUOGO"], attr=[], atteso=51,
           note="Nessun conteggio di visitatori."),
         D("biblioteche", "Biblioteche", ("zipcsv", "biblioteche_csv.zip", "biblioteche.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_BIBLIOT", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["CIRCOSCRIZ"], attr=["ORARIO", "ACC_DISAB"], atteso=20),
         D("cinema", "Cinema", ("zipcsv", "cinema_csv.zip", "cinema.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_CINEMA", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["CIRCOSCRIZ"], attr=["NUM_SALE"], atteso=26,
           note="NUM_SALE = numero di sale dichiarate."),
     ]},
    {"id": "sicurezza_sport", "nome": "Sicurezza e sport",
     "desc": "Sedi di pubblica sicurezza e impianti sportivi. Per copertura e accessibilita'; non come flusso di visite.",
     "dati": [
         D("carabinieri", "Carabinieri", ("zipcsv", "pubblica_sicurezza_csv.zip", "carabinieri.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_CARABIN", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=[], attr=[], atteso=25),
         D("guardia_finanza", "Guardia di Finanza", ("zipcsv", "pubblica_sicurezza_csv.zip", "guardia_finanza.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_GDF", nome_campo="SEDE", ind_campo="INDIRIZZO",
           cat_campo=[], attr=[], atteso=4),
         D("polizia_municipale", "Polizia Municipale", ("zipcsv", "pubblica_sicurezza_csv.zip", "polizia_municipale.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_POL_MUN", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["SEDE"], attr=["ORARIO"], atteso=12),
         D("protezione_civile", "Protezione Civile", ("zipcsv", "pubblica_sicurezza_csv.zip", "protezione_civile.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_PROTCIV", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=[], attr=["UFFICIO", "OR_NR_VERD"], atteso=1),
         D("questura", "Questura e Commissariati", ("zipcsv", "pubblica_sicurezza_csv.zip", "sedi_questura_commissariati.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_POL_STA", nome_campo="SEDE", ind_campo="INDIRIZZO",
           cat_campo=["UFFICIO"], attr=["ORARIO"], atteso=28),
         D("vigili_fuoco", "Vigili del Fuoco", ("zipcsv", "pubblica_sicurezza_csv.zip", "vigili_fuoco.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_VIGILIF", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=[], attr=["ORARIO"], atteso=7),
         D("impianti_sportivi", "Impianti sportivi", ("zipcsv", "impianti_sportivi_csv.zip", "impianti_sportivi.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_R_IMP_T", nome_campo="DENOMINAZI", ind_campo="INDIRIZZO",
           cat_campo=["DISCIPLINA"], attr=["COMPETENZA", "POLIVALENT"], atteso=686,
           note="Piu' righe possono descrivere discipline diverse nello stesso impianto. Capienza e calendario eventi non sono nel file."),
     ]},
    {"id": "reti", "nome": "Reti e accessibilita'",
     "desc": "Aree pedonali, percorsi ciclabili e accessibili, fermate metro, sharing, ricarica, parcheggi e ZTL. Posizioni disponibili; disponibilita' in tempo reale no.",
     "dati": [
         D("aree_pedonali", "Aree pedonali", ("zipcsv", "aree_pedonali_csv.zip", "aree_pedonali.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="poligoni", id_campo="ID_A_PEDO", nome_campo="DENOMINAZI", ind_campo=None,
           cat_campo=["CIRCOSCRIZ"], attr=["SUPERFICIE"], atteso=143),
         D("ciclabili", "Percorsi ciclabili", ("zipcsv", "percorsi_ciclabili_csv.zip", "percorsi_ciclabili.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino e cintura",
           tipo="linee", id_campo="ID_PERCORSO_CIC", nome_campo="DENOMINAZIONE", ind_campo=None,
           cat_campo=["TIPOLOGIA"], attr=["DIREZIONE", "STATO", "LUNGHEZZA", "COMUNE"], atteso=4151,
           note="Tutti i record risultano in stato ES (in esercizio): verificare continuita' e lunghezze."),
         D("percorsi_loges", "Percorsi accessibili (Loges)", ("zipcsv", "percorsi_loges_csv.zip", "percorsi_loges.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="linee", id_campo="ID_PERCORS", nome_campo=None, ind_campo=None,
           cat_campo=[], attr=["N_FERM_GTT"], atteso=58),
         D("fermate_metro", "Fermate metropolitana", ("shp", "fermate_metro_geo.zip"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="Shapefile (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_FERMATA", nome_campo="DENOMINAZI", ind_campo=None,
           cat_campo=["TIPO"], attr=[], atteso=23,
           note="Da confrontare con il GTFS GTT gia' in mappa; integrare solo accessi o attributi nuovi."),
         D("bike_sharing", "Stazioni bike sharing", ("shp", "stazioni_bike_sharing_geo.zip"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="Shapefile (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_BIKE_SH", nome_campo="STAZIONE", ind_campo=None,
           cat_campo=[], attr=[], atteso=87),
         D("car_sharing", "Stazioni car sharing", ("shp", "stazioni_car_sharing_geo.zip"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="Shapefile (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_CAR_SHA", nome_campo="DENOMINAZI", ind_campo="UBICAZIONE",
           cat_campo=["TIPO"], attr=[], atteso=83),
         D("ricarica_elettrica", "Stazioni di ricarica elettrica", ("shp", "stazioni_ricarica_veicoli_elettr_geo.zip"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="Shapefile (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="id", nome_campo="indirizzo", ind_campo=None,
           cat_campo=["stato"], attr=["operatore", "potenza"], atteso=95),
         D("parcheggi_strutture", "Parcheggi ad accesso controllato", ("zipcsv", "parcheggi_accesso_controllato_csv.zip", "parcheggi_accesso_controllato.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_PARCHEG", nome_campo="DENOMINAZI", ind_campo="UBICAZIONE",
           cat_campo=["TIPOLOGIA"], attr=["POSTI_TOT", "POSTI_ROT", "POSTI_ABB", "ANNO_ATTIV"], atteso=39,
           note="POSTI_TOT = posti dichiarati, non posti liberi in tempo reale."),
         D("parcheggi_disabili", "Stalli per disabili", ("zipcsv", "parcheggi_disabili_csv.zip", "parcheggi_disabili.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_STALLO", nome_campo="VIA", ind_campo="NUM_CIVICO",
           cat_campo=[], attr=["NUM_STALLI", "DATA_RIL"], atteso=1817),
         D("parcheggi_zona_blu", "Parcheggi zona blu (aree)", ("zipcsv", "parcheggi_zona_blu_csv.zip", "parcheggi_zona_blu.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="poligoni", id_campo="ID_ZON_BLU", nome_campo="ZONA", ind_campo="SOTTOZONA",
           cat_campo=[], attr=[], atteso=19),
         D("ztl", "ZTL (zone a traffico limitato)", ("zipcsv", "ztl_csv.zip", "ztl.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="poligoni", id_campo="ID_ZTL", nome_campo="DENOMINAZI", ind_campo=None,
           cat_campo=[], attr=["ORA_INIZIO", "ORA_FINE", "ORDINANZA", "SOSPENS"], atteso=3,
           note="Verificare che le ordinanze siano ancora valide prima di usarle nei percorsi auto."),
     ]},
    {"id": "servizi", "nome": "Servizi e uffici pubblici",
     "desc": "Sedi amministrative comunali, uffici postali, anagrafici e turistici. Luoghi di riferimento, non flussi.",
     "dati": [
         D("sedi_amministrative", "Sedi amministrative comunali", ("zipcsv", "sedi_amministrative_csv.zip", "sedi_amministrative.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_SEDE", nome_campo="ENTE", ind_campo="INDIRIZZO",
           cat_campo=["ENTE"], attr=["CIRCOSCRIZ"], atteso=164),
         D("uffici_postali", "Uffici postali", ("zipcsv", "uffici_csv.zip", "uffici_postali.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_POSTA", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=["TURNO"], attr=["ORARIO"], atteso=78),
         D("uffici_anagrafici", "Uffici anagrafici", ("zipcsv", "uffici_csv.zip", "uffici_anagrafici.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_ANAGRAF", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=[], attr=["ORARIO", "PRENOTAZIO"], atteso=15),
         D("uffici_turistici", "Uffici turistici", ("zipcsv", "uffici_csv.zip", "uffici_turistici.csv"), fonte=FONTE_CT,
           anno=NON_DICHIARATO, licenza=LIC_CT, formato="CSV con WKT (EPSG:3003)", copertura="Torino citta'",
           tipo="punti", id_campo="ID_TURISTI", nome_campo="DENOMINAZ", ind_campo="INDIRIZZO",
           cat_campo=[], attr=[], atteso=3),
     ]},
]


# ------------------------------------------------------------------ processing
def valore(r, campo):
    if not campo:
        return ""
    return (r.get(campo) or "").strip()


def elabora_dato(d):
    """Ritorna (elementi, tipo, statistiche, anomalie)."""
    righe, origine = righe_da_fonte(d["archivio"])
    n = len(righe)
    anomalie = []
    tipo = d["tipo"]

    # duplicati sull'id
    idc = d.get("id_campo")
    dup = 0
    if idc:
        visti = Counter(valore(r, idc) for r in righe if valore(r, idc))
        dup = sum(c - 1 for c in visti.values() if c > 1)
    # campi mancanti (nome, indirizzo, attributi, categoria)
    controlla = [c for c in ([d.get("nome_campo"), d.get("ind_campo")] + list(d.get("cat_campo") or []) + list(d.get("attr") or [])) if c]
    mancanti = {c: sum(1 for r in righe if not valore(r, c)) for c in controlla}

    # confronto COORD_X/Y vs WKT (prima di convertire)
    if origine is None and ("COORD_X" in (righe[0] if righe else {}) or "COORD_X" in (righe[0] if righe else {})):
        cx, wx = [], []
        for r in righe[:2000]:
            try:
                cx.append(float((r.get("COORD_X") or "").replace(",", ".")))
                y = r.get("WKT_GEOM", "")
                if y.startswith("POINT"):
                    wx.append(float(y.split("(")[1].split()[0]))
            except (ValueError, IndexError):
                continue
        if cx and wx and sum(wx) != 0:
            ratio = (sum(cx) / len(cx)) / (sum(wx) / len(wx))
            if not (0.5 <= ratio <= 2.0):
                anomalie.append(f"COORD_X/WKT ~ {ratio:.3f} (COORD_X circa {1/ratio:.1f} volte il WKT)")

    if d.get("speciale") == "attivita":
        return elabora_attivita(righe, d)

    elementi = []
    senza_geom = 0
    lats, lons = [], []
    for r in righe:
        if origine == "shp":
            geom = ("punto", [r["_la"], r["_lo"]]) if r.get("_la") is not None else None
        else:
            geom = wkt_geometria(valore(r, "WKT_GEOM"))
        if geom is None:
            senza_geom += 1
            continue
        gt, g = geom
        nome = valore(r, d.get("nome_campo"))
        ind = valore(r, d.get("ind_campo"))
        cat = " · ".join(x for x in (valore(r, c) for c in (d.get("cat_campo") or [])) if x)
        attr = [valore(r, c) for c in (d.get("attr") or [])]
        idv = valore(r, idc) if idc else ""
        if gt == "punto":
            elementi.append([g[0], g[1], nome, cat, idv, ind] + attr)
            lats.append(g[0]); lons.append(g[1])
        elif gt == "linea":
            elementi.append([nome, cat, idv, g] + attr)
            lats += [p[0] for p in g]; lons += [p[1] for p in g]
        elif gt == "linee":
            for g1 in g:
                elementi.append([nome, cat, idv, g1] + attr)
                lats += [p[0] for p in g1]; lons += [p[1] for p in g1]
        elif gt == "poligoni":
            for poly in g:
                elementi.append([nome, cat, idv, poly] + attr)
                lats += [p[0] for an in poly for p in an]
                lons += [p[1] for an in poly for p in an]

    fuori = sum(1 for la, lo in zip(lats, lons)
                if not (AREA_MIN[0] <= la <= AREA_MAX[0] and AREA_MIN[1] <= lo <= AREA_MAX[1]))
    if lats and fuori:
        anomalie.append(f"{fuori} geometrie fuori dall'area attesa")

    stat = {
        "record": n,
        "elementi": len(elementi),
        "senza_geometria": senza_geom,
        "duplicati_id": dup,
        "campi_mancanti": mancanti,
        "bbox": ([round(min(lats), 5), round(min(lons), 5)], [round(max(lats), 5), round(max(lons), 5)]) if lats else None,
        "fuori_area": fuori,
    }
    return elementi, tipo, stat, anomalie


def elabora_attivita(righe, d):
    """Attivita' commerciali: punti + conteggi per categoria. Niente nomi di persona."""
    elementi = []
    per_cat = Counter()
    lats, lons = [], []
    senza = 0
    for r in righe:
        geom = wkt_geometria(valore(r, "WKT_GEOM"))
        if geom is None or geom[0] != "punto":
            senza += 1
            continue
        la, lo = geom[1]
        cat = valore(r, "DESC_RIP") or valore(r, "CAT_MER") or "non indicata"
        per_cat[cat] += 1
        # [la, lo, nome, cat, id, ind, TIPO_LOC, MQ_TOT_V, ZONASTAT, NCIRCO]
        elementi.append([la, lo, "", cat, "", valore(r, "INDIRIZZ"),
                         valore(r, "TIPO_LOC"), valore(r, "MQ_TOT_V"), valore(r, "ZONASTAT"), valore(r, "NCIRCO")])
        lats.append(la); lons.append(lo)
    fuori = sum(1 for la, lo in zip(lats, lons)
                if not (AREA_MIN[0] <= la <= AREA_MAX[0] and AREA_MIN[1] <= lo <= AREA_MAX[1]))
    stat = {
        "record": len(righe),
        "elementi": len(elementi),
        "senza_geometria": senza,
        "duplicati_id": 0,
        "campi_mancanti": {},
        "bbox": ([round(min(lats), 5), round(min(lons), 5)], [round(max(lats), 5), round(max(lons), 5)]) if lats else None,
        "fuori_area": fuori,
        "categorie": [{"nome": k, "n": v} for k, v in per_cat.most_common()],
    }
    return elementi, "punti", stat, []


def elabora_alberate():
    """Alberate: NON si disegnano 131.994 alberi. Aggregato per AMBITO."""
    with zipfile.ZipFile(RAW / "alberate.zip") as z:
        testo = decodifica(z.read("alberate.csv"))
    righe = leggi_righe_csv(testo)
    gruppi = defaultdict(lambda: [0, 0.0, 0.0, Counter()])
    n_punti = 0
    for r in righe:
        geom = wkt_geometria(valore(r, "WKT_GEOM"))
        if geom is None:
            continue
        la, lo = geom[1]
        ambito = valore(r, "AMBITO") or "non indicato"
        g = gruppi[ambito]
        g[0] += 1; g[1] += la; g[2] += lo; g[3][valore(r, "SPECIE") or "non indicata"] += 1
        n_punti += 1
    elementi = []
    for ambito, (c, sla, slo, sp) in sorted(gruppi.items(), key=lambda kv: -kv[1][0]):
        specie = ", ".join(f"{k} ({v})" for k, v in sp.most_common(3))
        elementi.append([round(sla / c, 6), round(slo / c, 6), ambito, "alberate", "", "", c, len(sp), specie])
    stat = {"record": len(righe), "elementi": len(elementi), "punti_validi": n_punti,
            "duplicati_id": 0, "campi_mancanti": {}, "bbox": None, "fuori_area": 0}
    return elementi, "punti", stat, ["dato voluminoso: rappresentato come aggregato per ambito, non come singoli alberi"]


# ------------------------------------------------------------------ main
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    indice = {"generato_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "crs_geometrie": "EPSG:3003 (Monte Mario / Italy zone 1) -> WGS84",
              "nota": "Sola lettura sui dati grezzi. Elementi compatti: punti [la,lo,nome,cat,id,indirizzo,*attr]; "
                      "linee [nome,cat,id,[[la,lo]...],*attr]; poligoni [nome,cat,id,[anelli],*attr].",
              "gruppi": []}
    tot_dati = 0
    for gr in GRUPPI:
        print(f"\n### Gruppo: {gr['nome']}")
        dati_out = []
        for d in gr["dati"]:
            try:
                elementi, tipo, stat, anomalie = elabora_dato(d)
            except Exception as e:
                print(f"  ERRORE su {d['id']}: {e}")
                raise
            atteso = d.get("atteso")
            avviso = ""
            if atteso is not None and stat["record"] != atteso:
                avviso = f"  ATTESO {atteso}"
            print(f"  {d['id']:<26} record {stat['record']:>7}  elementi {stat['elementi']:>7}"
                  f"  dup {stat['duplicati_id']:>3}  senza geom {stat['senza_geometria']:>3}"
                  f"  fuori area {stat['fuori_area']:>4}{avviso}")
            if anomalie:
                for a in anomalie:
                    print(f"      ANOMALIA: {a}")
            meta = {k: d.get(k) for k in ("id", "nome", "fonte", "anno", "licenza", "formato",
                                          "copertura", "crs") if d.get(k) is not None}
            meta["crs"] = meta.get("crs") or "EPSG:3003"
            meta["tipo"] = tipo
            meta["campi"] = list(d.get("attr") or [])
            meta["cat_campi"] = list(d.get("cat_campo") or [])
            meta["note"] = d.get("note", "")
            meta["stat"] = stat
            meta["anomalie"] = anomalie
            dati_out.append((meta, elementi))
            tot_dati += 1
        # file per la mappa (con elementi)
        gruppo_file = {"id": gr["id"], "nome": gr["nome"], "desc": gr["desc"],
                       "generato_utc": indice["generato_utc"],
                       "dati": [dict(m, elementi=el) for m, el in dati_out]}
        (OUT_DIR / f"{gr['id']}.json").write_text(
            json.dumps(gruppo_file, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"),
            encoding="utf-8")
        # indice (senza elementi)
        indice["gruppi"].append({"id": gr["id"], "nome": gr["nome"], "desc": gr["desc"],
                                 "dati": [m for m, _ in dati_out]})

    # alberate a parte (grande, aggregata): lo metto nel gruppo reti come dato extra
    try:
        elementi, tipo, stat, anomalie = elabora_alberate()
        print(f"\n  {'alberate (aggregate)':<26} record {stat['record']:>7}  ambiti {stat['elementi']:>7}")
        for a in anomalie:
            print(f"      ANOMALIA: {a}")
        meta = {"id": "alberate", "nome": "Alberate (aggregate per ambito)", "fonte": FONTE_CT,
                "anno": NON_DICHIARATO, "licenza": LIC_CT, "formato": "CSV con WKT (EPSG:3003)",
                "copertura": "Torino citta'", "crs": "EPSG:3003", "tipo": tipo, "campi": ["numero", "specie", "prime_specie"],
                "cat_campi": [], "note": "Non rappresenta un attrattore: utile per aggregati di ombra/comfort. "
                "Non si disegnano i 131.994 alberi singoli.", "stat": stat, "anomalie": anomalie, "elementi": elementi}
        reti_file = json.loads((OUT_DIR / "reti.json").read_text(encoding="utf-8"))
        reti_file["dati"].append(meta)
        (OUT_DIR / "reti.json").write_text(
            json.dumps(reti_file, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"), encoding="utf-8")
        for g in indice["gruppi"]:
            if g["id"] == "reti":
                g["dati"].append({k: v for k, v in meta.items() if k != "elementi"})
    except Exception as e:
        print(f"  ERRORE sulle alberate: {e}")

    (OUT_DIR / "catalogo.json").write_text(
        json.dumps(indice, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"), encoding="utf-8")
    print(f"\nCatalogo: {tot_dati} dati in {len(indice['gruppi'])} gruppi -> {OUT_DIR / 'catalogo.json'}")
    for f in sorted(OUT_DIR.glob("*.json")):
        print(f"  {f.name}: {f.stat().st_size/1e6:.2f} MB")


if __name__ == "__main__":
    main()
