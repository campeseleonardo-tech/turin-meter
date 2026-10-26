#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Risultato 9 — attesa promessa contro attesa reale.

Documento del risultato: sviluppo/note_tecniche/R4_puntualita.md.

Domanda: sulle linee frequenti, quanti minuti in piu' aspetta in media chi arriva alla fermata a caso,
rispetto a quanto promette l'orario?

Formula (per fermata, linea, verso, fascia oraria): con intervalli h1..hn fra passaggi consecutivi
  attesa media = somma(h^2) / (2 * somma(h))
  attesa promessa = formula sugli orari GTFS; attesa reale = formula sugli arrivi misurati con il GPS (dal Giro 5; prima dal feed)
  attesa in piu' = reale - promessa

Corse mancanti (D1), forbice:
  stima BASSA: solo tratti di corse programmate consecutive TUTTE viste dal GPS; promessa e reale
               calcolate sugli stessi tratti (le corse mancanti non creano buchi).
  stima ALTA:  una corsa assente sia dal feed dei ritardi sia dal GPS (mezzi_gtt) e' considerata non
               effettuata; una corsa presente solo nel GPS (o con lettura scartata) arriva in orario.
               Promessa = tutte le corse programmate.
Linee frequenti (D2): intervallo programmato medio <= 12 minuti per fermata-linea-verso-fascia.
Media della citta' (D3): pesata sul numero di intervalli programmati.
Solo ore con la raccolta attiva (almeno 50 minuti letti nell'ora) e solo linee presenti nel feed quel giorno.

Riusa, senza modificarlo, scripts/27_risultato4_regolarita.py (dal Giro 5: passaggi dal GPS, costruisci_passaggi_gps).

Se lo storico SQLite non c'e' (o con --riassunti) legge i riassunti dello script 97 (data/storico_riassunti/): stessi numeri.

Uso:
  python scripts/70_risultato9_attesa.py            giro completo, scrive JSON e rapporto
  python scripts/70_risultato9_attesa.py --riassunti   come sopra, dai riassunti anche se lo storico c'e'
  python scripts/70_risultato9_attesa.py --prova    solo 15/10, rapporto a schermo, nessun file
  python scripts/70_risultato9_attesa.py --freq 10  sensibilita' (soglia diversa), nessun file
Uscite: data/processed/risultato9_attesa.json, docs/rapporti/RAPPORTO_RISULTATO9_ATTESA.txt
"""

import csv
import importlib.util
import io
import json
import math
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("r4", RADICE / "scripts" / "27_risultato4_regolarita.py")
r4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r4)

OUT_JSON = RADICE / "data" / "processed" / "risultato9_attesa.json"
IN_R4 = RADICE / "data" / "processed" / "risultato4_regolarita.json"   # scritto dallo script 27: modo_linea
OUT_RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_RISULTATO9_ATTESA.txt"
OUT_RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
TAG = "MISURATO"
GIORNO_PROVA = "20261015"

FREQ_MAX = 12.0          # D2, minuti
MIN_MINUTI_ORA = 50      # ora "attiva" se la raccolta ha letto almeno 50 minuti
MIN_INTERVALLI_BUS_AVVISO = 10000   # Giro 6: sotto questi intervalli osservati sui bus (feriale) la media per modo e' poco affidabile
MAX_MANCANTI = 0.20      # linea-fascia con piu' del 20% di corse assenti dal feed -> dati scarsi
MIN_INTERVALLI_CHIAVE = 6    # intervalli programmati minimi per fermata-linea-verso-fascia (somma dei giorni)
MIN_INTERVALLI_CLASSIFICA = 30
LINEE_ESEMPIO = ("4", "15", "68")
LINEE_GPS = ("4", "15")
FASCE = r4.FASCE

P_LINEA, P_DIR, P_STOP, P_SCHED, P_EST, P_SEQ, P_TRIP = (r4.P_LINEA, r4.P_DIR, r4.P_STOP, r4.P_SCHED,
                                                       r4.P_EST, r4.P_SEQ, r4.P_TRIP)

# posizioni negli accumulatori per chiave (linea, dir, stop, fascia, tipo)
(A_N_SCH, A_SCH2, A_SCH1, A_ALTA2, A_ALTA1, A_N_BASSA, A_OBS2, A_OBS1, A_BSCH2, A_BSCH1,
 A_CORSE, A_MANCA_FEED, A_MANCA_TUTTI) = range(13)


def nuovo_acc():
    return [0.0] * 13


def attesa(s2, s1):
    return s2 / (2.0 * s1) if s1 > 0 else None


# ---------- GTFS: calendario e fermate ----------

def carica_calendario(percorso=None):
    servizio, cal, eccezioni, fermate = {}, {}, defaultdict(dict), {}
    with zipfile.ZipFile(percorso or r4.GTFS) as z:
        leggi = lambda n: csv.DictReader(io.TextIOWrapper(z.open(n), encoding="utf-8-sig"))
        for r in leggi("trips.txt"):
            servizio[r["trip_id"]] = r["service_id"]
        for r in leggi("calendar.txt"):
            cal[r["service_id"]] = r
        for r in leggi("calendar_dates.txt"):
            eccezioni[r["date"]][r["service_id"]] = r["exception_type"]
        for r in leggi("stops.txt"):
            fermate[r["stop_id"]] = (r["stop_name"], float(r["stop_lat"]), float(r["stop_lon"]))
    return servizio, cal, eccezioni, fermate


def servizi_attivi(giorno, cal, eccezioni):
    d = datetime.strptime(giorno, "%Y%m%d").date()
    col = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")[d.weekday()]
    attivi = {s for s, r in cal.items() if r["start_date"] <= giorno <= r["end_date"] and r[col] == "1"}
    for s, tipo in eccezioni.get(giorno, {}).items():
        if tipo == "1":
            attivi.add(s)
        else:
            attivi.discard(s)
    return attivi


# ---------- un giorno ----------

def mezzanotte_utc(giorno):
    d = datetime.strptime(giorno, "%Y%m%d").date()
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc) - timedelta(hours=r4.offset_data_locale(d))


def elabora_giorno(sorg, giorno, trip_info, nome_linea, prog, servizio, cal, eccezioni, acc, esempi, fermate):
    mezz = mezzanotte_utc(giorno)
    d = datetime.strptime(giorno, "%Y%m%d").date()
    tipo = str(r4.tipo_giorno_data(d))
    # Giro 5: gli arrivi vengono dal GPS (r4.costruisci_passaggi_gps); "nel_feed" ora sono le corse viste nel GPS
    passaggi, _cop = sorg.passaggi_gps(giorno, (trip_info, nome_linea, prog), fermate)
    gps = sorg.corse_gps(giorno)
    nel_feed = set(gps)
    stimato = {(p[P_TRIP], p[P_SEQ]): p[P_EST] for p in passaggi}
    linee_coperte = {nome_linea.get(trip_info[t][0]) for t in nel_feed if t in trip_info}
    attive = sorg.ore_attive(giorno, MIN_MINUTI_ORA)
    attivi = servizi_attivi(giorno, cal, eccezioni)

    gruppi = defaultdict(list)
    base = mezz.timestamp()
    for (tid, seq), (secondi, stop) in prog.items():
        if servizio.get(tid) not in attivi or tid not in trip_info:
            continue
        route, direzione = trip_info[tid]
        linea = nome_linea.get(route, route)
        if linea not in linee_coperte:
            continue
        gruppi[(linea, direzione, stop)].append((base + secondi, tid, seq))

    conteggi = {"corse_programmate": len({t for v in gruppi.values() for _, t, _ in v}),
                "ore_attive": len(attive), "linee_coperte": len(linee_coperte)}
    for (linea, direzione, stop), lista in gruppi.items():
        lista.sort()
        # tratti: passaggi consecutivi nella stessa fascia e in ore con raccolta attiva
        tratti, corrente, fascia_cor = [], [], None
        for ts, tid, seq in lista:
            ora_ok = int(ts) // 3600 * 3600 in attive
            fascia = r4.fascia_oraria(r4.a_roma(datetime.fromtimestamp(ts, timezone.utc)).hour)
            if not ora_ok or fascia != fascia_cor:
                if len(corrente) >= 2:
                    tratti.append((fascia_cor, corrente))
                corrente, fascia_cor = [], fascia
            if ora_ok:
                corrente.append((ts, tid, seq))
        if len(corrente) >= 2:
            tratti.append((fascia_cor, corrente))

        for fascia, tr in tratti:
            a = acc.setdefault((linea, direzione, stop, fascia, tipo), nuovo_acc())
            hs = [(tr[i + 1][0] - tr[i][0]) / 60.0 for i in range(len(tr) - 1)]
            a[A_N_SCH] += len(hs)
            a[A_SCH2] += sum(h * h for h in hs)
            a[A_SCH1] += sum(hs)
            a[A_CORSE] += len(tr)
            # stima alta: tolte le corse assenti da feed e GPS; arrivo = stimato, altrimenti orario
            arrivi = []
            for ts, tid, seq in tr:
                est = stimato.get((tid, seq))
                if est is None and tid not in nel_feed:
                    a[A_MANCA_FEED] += 1
                    if tid not in gps:
                        a[A_MANCA_TUTTI] += 1
                        continue
                arrivi.append(est if est is not None else ts)
            arrivi.sort()
            ha = [(arrivi[i + 1] - arrivi[i]) / 60.0 for i in range(len(arrivi) - 1)]
            if len(arrivi) >= 2:
                a[A_ALTA2] += sum(h * h for h in ha)
                a[A_ALTA1] += sum(ha)
            # stima bassa: sotto-tratti di corse consecutive tutte con arrivo stimato
            corsa = []
            for ts, tid, seq in tr + [(None, None, None)]:
                est = stimato.get((tid, seq)) if tid else None
                if est is not None:
                    corsa.append((ts, est))
                    continue
                if len(corsa) >= 2:
                    sch = [(corsa[i + 1][0] - corsa[i][0]) / 60.0 for i in range(len(corsa) - 1)]
                    oss_ord = sorted(e for _, e in corsa)
                    oss = [(oss_ord[i + 1] - oss_ord[i]) / 60.0 for i in range(len(oss_ord) - 1)]
                    a[A_N_BASSA] += len(oss)
                    a[A_OBS2] += sum(h * h for h in oss)
                    a[A_OBS1] += sum(oss)
                    a[A_BSCH2] += sum(h * h for h in sch)
                    a[A_BSCH1] += sum(sch)
                corsa = []
            if (giorno == GIORNO_PROVA and fascia == "punta_mattina" and linea in LINEE_ESEMPIO
                    and linea not in esempi and len(tr) >= 6):
                esempi[linea] = {
                    "linea": linea, "direzione": direzione, "stop_id": stop, "giorno": giorno,
                    "passaggi": [[r4.a_roma(datetime.fromtimestamp(ts, timezone.utc)).strftime("%H:%M:%S"),
                                  (r4.a_roma(datetime.fromtimestamp(stimato[(tid, seq)], timezone.utc)).strftime("%H:%M:%S")
                                   if (tid, seq) in stimato else None),
                                  tid in nel_feed, tid in gps] for ts, tid, seq in tr]}
    return tipo, conteggi, passaggi


# ---------- controllo col GPS (passo 4) ----------

def metri(lat1, lon1, lat2, lon2):
    kx = 111320.0 * math.cos(math.radians(lat1))
    return (lon2 - lon1) * kx, (lat2 - lat1) * 110540.0


def controllo_gps(con, giorno, passaggi, fermate, nome_linea_set=LINEE_GPS, max_passaggi=600):
    """Confronta l'arrivo stimato dal feed con il passaggio del mezzo vicino alla fermata (GPS ogni ~minuto,
    tempo interpolato sul segmento piu' vicino, entro 60 m)."""
    scelti = [p for p in passaggi if p[P_LINEA] in nome_linea_set][::7][:max_passaggi]
    corse = {p[P_TRIP] for p in scelti}
    mezz = mezzanotte_utc(giorno)
    da, a = (mezz + timedelta(hours=2)).isoformat(), (mezz + timedelta(hours=26)).isoformat()
    pos = defaultdict(list)
    for corsa, ts, lat, lng in con.execute(
            "SELECT corsa, ts_feed, lat, lng FROM mezzi_gtt WHERE letto_utc BETWEEN ? AND ?", (da, a)):
        if corsa in corse and ts and lat and lng:
            pos[corsa].append((ts, lat, lng))
    diff, fermate_viste = [], set()
    for p in scelti:
        punti = sorted(set(pos.get(p[P_TRIP], [])))
        info = fermate.get(p[P_STOP])
        if len(punti) < 2 or not info:
            continue
        _, flat, flon = info
        migliore = None
        for (t0, la0, lo0), (t1, la1, lo1) in zip(punti, punti[1:]):
            if t1 - t0 > 180 or t1 <= t0:
                continue
            x0, y0 = metri(flat, flon, la0, lo0)
            x1, y1 = metri(flat, flon, la1, lo1)
            dx, dy = x1 - x0, y1 - y0
            l2 = dx * dx + dy * dy
            f = 0.0 if l2 == 0 else max(0.0, min(1.0, -(x0 * dx + y0 * dy) / l2))
            dist = math.hypot(x0 + f * dx, y0 + f * dy)
            if migliore is None or dist < migliore[0]:
                migliore = (dist, t0 + f * (t1 - t0))
        if migliore and migliore[0] <= 60:
            diff.append((p[P_EST] - migliore[1]) / 60.0)
            fermate_viste.add(p[P_STOP])
    diff.sort()
    n = len(diff)
    med = diff[n // 2] if n else None
    med_abs = sorted(abs(x) for x in diff)[n // 2] if n else None
    entro1 = round(100.0 * sum(abs(x) <= 1 for x in diff) / n, 1) if n else None
    return {"linee": list(nome_linea_set), "giorno": giorno, "passaggi_confrontati": n,
            "fermate": len(fermate_viste), "differenza_mediana_min": round(med, 2) if n else None,
            "differenza_assoluta_mediana_min": round(med_abs, 2) if n else None,
            "entro_1_min_pct": entro1}


def controllo_gps_giorno(sorg, giorno, ctx, fermate):
    """Controllo del feed (non della fonte usata): servono i passaggi stimati dal feed e le posizioni GPS grezze.
    Dai riassunti non si puo' rifare: si legge il risultato calcolato dallo script 97 sullo storico."""
    if hasattr(sorg, "con"):
        passaggi_feed = sorg.passaggi_feed(giorno, ctx)[0]
        return controllo_gps(sorg.con, giorno, passaggi_feed, fermate)
    return sorg.controllo_gps(giorno)


# ---------- aggregazione ----------

def valori(a):
    swt = attesa(a[A_SCH2], a[A_SCH1])
    alta = attesa(a[A_ALTA2], a[A_ALTA1])
    b_sch = attesa(a[A_BSCH2], a[A_BSCH1])
    b_obs = attesa(a[A_OBS2], a[A_OBS1])
    return {"promessa": swt, "reale_alta": alta,
            "piu_bassa": (b_obs - b_sch) if b_obs is not None and b_sch is not None else None,
            "piu_alta": (alta - swt) if alta is not None and swt is not None else None,
            "promessa_bassa": b_sch, "reale_bassa": b_obs}


def frequente(a, freq):
    return a[A_N_SCH] >= MIN_INTERVALLI_CHIAVE and a[A_SCH1] / a[A_N_SCH] <= freq


def media_pesata(chiavi, acc):
    """Media pesata sugli intervalli programmati (D3) di promessa, reale e attesa in piu'."""
    somma = defaultdict(float)
    for k in chiavi:
        a = acc[k]
        v = valori(a)
        if v["piu_bassa"] is None or v["piu_alta"] is None:
            continue
        w = a[A_N_SCH]
        somma["w"] += w
        for campo in ("promessa", "piu_bassa", "piu_alta", "promessa_bassa", "reale_bassa", "reale_alta"):
            somma[campo] += w * v[campo]
        somma["n_bassa"] += a[A_N_BASSA]
        somma["corse"] += a[A_CORSE]
        somma["manca_feed"] += a[A_MANCA_FEED]
        somma["manca_tutti"] += a[A_MANCA_TUTTI]
    if not somma["w"]:
        return None
    w = somma["w"]
    prom = somma["promessa"] / w
    return {"promessa_min": round(prom, 2),
            "reale_min_bassa": round(prom + somma["piu_bassa"] / w, 2),
            "reale_min_alta": round(prom + somma["piu_alta"] / w, 2),
            "in_piu_min_bassa": round(somma["piu_bassa"] / w, 2),
            "in_piu_min_alta": round(somma["piu_alta"] / w, 2),
            "in_piu_pct_bassa": round(100 * somma["piu_bassa"] / somma["promessa_bassa"], 1),
            "intervalli_programmati": int(w), "intervalli_osservati": int(somma["n_bassa"]),
            "corse_assenti_feed_pct": round(100 * somma["manca_feed"] / somma["corse"], 1) if somma["corse"] else None,
            "corse_assenti_tutto_pct": round(100 * somma["manca_tutti"] / somma["corse"], 1) if somma["corse"] else None}


def aggrega(acc, freq, fermate, modo_linea=None):
    chiavi_freq = [k for k, a in acc.items() if frequente(a, freq)]
    # dati scarsi: linea-fascia-tipo con piu' del 20% di corse assenti dal feed
    per_lft = defaultdict(lambda: [0.0, 0.0])
    for k in chiavi_freq:
        linea, _, _, fascia, tipo = k
        per_lft[(linea, fascia, tipo)][0] += acc[k][A_CORSE]
        per_lft[(linea, fascia, tipo)][1] += acc[k][A_MANCA_FEED]
    scarse = {lft for lft, (c, m) in per_lft.items() if c and m / c > MAX_MANCANTI}
    buone = [k for k in chiavi_freq if (k[0], k[3], k[4]) not in scarse]

    citta = {t: media_pesata([k for k in buone if k[4] == t], acc) for t in r4.TIPI}
    citta_fascia = {t: {f: media_pesata([k for k in buone if k[4] == t and k[3] == f], acc) for f in FASCE}
                    for t in r4.TIPI}
    linee = defaultdict(list)
    for k in buone:
        linee[(k[4], k[0])].append(k)
    per_linea = {}
    for (t, linea), ks in linee.items():
        m = media_pesata(ks, acc)
        if m:
            per_linea.setdefault(t, {})[linea] = m
    fermate_k = defaultdict(list)
    for k in buone:
        if k[4] == "0":
            fermate_k[(k[0], k[1], k[2])].append(k)
    per_fermata = []
    for (linea, d, stop), ks in fermate_k.items():
        m = media_pesata(ks, acc)
        if m and m["intervalli_osservati"] >= MIN_INTERVALLI_CLASSIFICA:
            info = fermate.get(stop, ("?", None, None))
            per_fermata.append({"linea": linea, "direzione": d, "stop_id": stop, "nome": info[0],
                                "lat": info[1], "lon": info[2], **m})
    per_fermata.sort(key=lambda x: -x["in_piu_min_bassa"])
    scarse_elenco = sorted(({"linea": l, "fascia": f, "tipo": t,
                             "assenti_pct": round(100 * per_lft[(l, f, t)][1] / per_lft[(l, f, t)][0], 1)}
                            for (l, f, t) in scarse), key=lambda x: -x["assenti_pct"])
    # attesa per modo (tram / metro / bus): stessa media pesata sulle chiavi buone di quel tipo di giorno e di quel modo
    modi = None
    if modo_linea:
        modi = {t: {m: media_pesata([k for k in buone if k[4] == t and modo_linea.get(k[0], "bus") == m], acc)
                    for m in sorted(set(modo_linea.values()))} for t in r4.TIPI}
    return {"citta": citta, "citta_fascia": citta_fascia, "linee": per_linea, "fermate": per_fermata, "modi": modi,
            "chiavi_frequenti": len(chiavi_freq), "chiavi_usate": len(buone),
            "dati_scarsi": scarse_elenco}


# ---------- main ----------

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    prova = "--prova" in args
    freq = float(args[args.index("--freq") + 1]) if "--freq" in args else FREQ_MAX
    scrivi = not prova and "--freq" not in args

    gtfs = r4.GtfsPerGiorno(True)   # il GTFS valido in ogni giorno (data/gtfs_archivio); con un solo GTFS e' sempre lo stesso
    modo_linea = None
    if IN_R4.exists():
        modo_linea = json.loads(IN_R4.read_text(encoding="utf-8")).get("modo_linea")
    if not modo_linea:
        print(f"AVVISO: manca modo_linea in {IN_R4.name} (lancia prima scripts/27): niente attesa per modo", file=sys.stderr)
    fermate = {}                    # unione delle fermate delle versioni usate
    sorg = r4.apri_sorgente("--riassunti" in args)
    print(f"Sorgente dei dati: {sorg.nome}", file=sys.stderr)
    giorni = [g for g in sorg.giorni() if r4.comuni.nel_periodo(g, "gps")]   # periodo fisso (L9): comuni.PERIODO
    esclusi_gps = []
    if prova:
        giorni = [GIORNO_PROVA]
    else:
        # Giro 6: stessi giorni dello script 27 (via quelli con poco GPS)
        giorni, esclusi_gps = r4.giorni_gps_validi(sorg, giorni, lambda g: gtfs.stato(g).trip_info)
        for e in esclusi_gps:
            print(f"Giorno escluso (poco GPS): {e['giorno']}, {e['corse_viste']} corse viste, mediana del tipo {e['mediana_tipo']}",
                  file=sys.stderr)
    acc, esempi, per_giorno, gps = {}, {}, {}, None
    cal_di = None
    tipi_giorno = {t: 0 for t in r4.TIPI}
    for n, giorno in enumerate(giorni, 1):
        print(f"[{n}/{len(giorni)}] {giorno}...", file=sys.stderr)
        st = gtfs.stato(giorno)
        trip_info, nome_linea, prog = st.trip_info, st.nome_linea, st.prog
        if cal_di != st.path:
            servizio, cal, eccezioni, _f = carica_calendario(st.path)
            cal_di = st.path
        fermate.update(st.fermate)
        tipo, conteggi, passaggi = elabora_giorno(sorg, giorno, trip_info, nome_linea, prog, servizio, cal,
                                                  eccezioni, acc, esempi, st.fermate)
        tipi_giorno[tipo] += 1
        per_giorno[giorno] = {"tipo": tipo, **conteggi}
        if giorno == GIORNO_PROVA:
            print("  controllo GPS...", file=sys.stderr)
            gps = controllo_gps_giorno(sorg, giorno, (trip_info, nome_linea, prog), st.fermate)
        del passaggi
    sorg.chiudi()

    ris = aggrega(acc, freq, fermate, modo_linea)
    # sensibilita' D2 (solo citta', feriale)
    sens = {}
    for f in (10.0, 12.0, 15.0):
        c = aggrega(acc, f, fermate)["citta"]["0"]
        sens[str(int(f))] = c
    nomi_tipo = {"0": "feriale", "1": "sabato", "2": "domenica"}

    R = []
    R.append("RISULTATO 9 — ATTESA PROMESSA CONTRO ATTESA REALE")
    R.append("=" * 66)
    R.append(f"Giorni: {giorni[0]} -> {giorni[-1]} ({len(giorni)}: feriali {tipi_giorno['0']}, sabati "
             f"{tipi_giorno['1']}, domeniche {tipi_giorno['2']}); solo ore con raccolta attiva (>= {MIN_MINUTI_ORA} min letti)")
    if esclusi_gps:
        R.append("Giorni esclusi per poco GPS (stessa regola dello script 27): " + "; ".join(
            f"{e['giorno']} ({e['corse_viste']} corse viste, mediana del tipo {e['mediana_tipo']:g})" for e in esclusi_gps))
    else:
        R.append("Giorni esclusi per poco GPS: nessuno")
    R.append(f"Linee frequenti: intervallo programmato medio <= {freq:g} min per fermata-linea-verso-fascia "
             f"(almeno {MIN_INTERVALLI_CHIAVE} intervalli)")
    R.append(f"Chiavi fermata-linea-verso-fascia-giorno frequenti: {ris['chiavi_frequenti']}, usate: {ris['chiavi_usate']} "
             f"(tolte quelle con > {int(MAX_MANCANTI * 100)}% di corse assenti dal GPS)")
    R.append("")
    fer = ris["citta"]["0"]
    if fer:
        R.append("I NUMERI (feriale, linee frequenti, media pesata sugli intervalli programmati)")
        R.append(f"  attesa promessa:  {fer['promessa_min']:.1f} min")
        R.append(f"  attesa reale:     {fer['reale_min_bassa']:.1f} min (stima bassa) - {fer['reale_min_alta']:.1f} min (stima alta)")
        R.append(f"  attesa in piu':   {fer['in_piu_min_bassa']:.1f} - {fer['in_piu_min_alta']:.1f} min "
                 f"(stima bassa = +{fer['in_piu_pct_bassa']:.0f}% sulla promessa)")
        R.append(f"  corse programmate assenti dal GPS: {fer['corse_assenti_feed_pct']}%")
    R.append("")
    R.append("PER TIPO DI GIORNO")
    R.append("tipo      | promessa | reale bassa | reale alta | in piu' bassa | in piu' alta | intervalli oss.")
    for t in r4.TIPI:
        c = ris["citta"][t]
        if c:
            R.append(f"{nomi_tipo[t]:<9} | {c['promessa_min']:8.1f} | {c['reale_min_bassa']:11.1f} | {c['reale_min_alta']:10.1f} | "
                     f"{c['in_piu_min_bassa']:13.1f} | {c['in_piu_min_alta']:12.1f} | {c['intervalli_osservati']:>10}")
    R.append("")
    R.append("PER FASCIA ORARIA (feriale)")
    R.append("fascia        | promessa | in piu' bassa | in piu' alta | intervalli oss.")
    for f in FASCE:
        c = ris["citta_fascia"]["0"][f]
        if c:
            R.append(f"{f:<13} | {c['promessa_min']:8.1f} | {c['in_piu_min_bassa']:13.1f} | {c['in_piu_min_alta']:12.1f} | {c['intervalli_osservati']:>10}")
    R.append("")
    R.append("SENSIBILITA' alla soglia 'frequente' (feriale): ")
    for f, c in sens.items():
        if c:
            R.append(f"  <= {f} min: promessa {c['promessa_min']:.1f}, in piu' {c['in_piu_min_bassa']:.1f} - "
                     f"{c['in_piu_min_alta']:.1f} min, intervalli {c['intervalli_programmati']}")
    R.append("")
    lin = ris["linee"].get("0", {})
    classifica = sorted(((v["in_piu_min_bassa"], k, v) for k, v in lin.items()
                         if v["intervalli_osservati"] >= MIN_INTERVALLI_CLASSIFICA), reverse=True)
    R.append(f"10 LINEE CON PIU' ATTESA IN PIU' (feriale, stima bassa, >= {MIN_INTERVALLI_CLASSIFICA} intervalli osservati)")
    for i, (_, k, v) in enumerate(classifica[:10], 1):
        R.append(f"{i:2}. linea {k:<5} promessa {v['promessa_min']:4.1f} min | in piu' {v['in_piu_min_bassa']:4.1f} - "
                 f"{v['in_piu_min_alta']:4.1f} min | assenti {v['corse_assenti_feed_pct']}% | intervalli {v['intervalli_osservati']}")
    R.append("")
    R.append("20 FERMATE (linea e verso) CON PIU' ATTESA IN PIU' (feriale, stima bassa)")
    for i, x in enumerate(ris["fermate"][:20], 1):
        R.append(f"{i:2}. linea {x['linea']:<5} v{x['direzione']} {x['nome'][:34]:<34} promessa {x['promessa_min']:4.1f} | "
                 f"in piu' {x['in_piu_min_bassa']:4.1f} - {x['in_piu_min_alta']:4.1f} min | intervalli {x['intervalli_osservati']}")
    R.append("")
    R.append(f"DATI SCARSI (linea-fascia-tipo con > {int(MAX_MANCANTI * 100)}% corse assenti dal GPS, fuori dai numeri): "
             f"{len(ris['dati_scarsi'])}")
    for x in ris["dati_scarsi"][:15]:
        R.append(f"  linea {x['linea']:<5} {x['fascia']:<13} {nomi_tipo[x['tipo']]:<9} assenti {x['assenti_pct']}%")
    R.append("")
    R.append("CONTROLLO COL GPS (passo 4): arrivo stimato dal feed - passaggio del GPS vicino alla fermata")
    R.append("  (e' un controllo del feed, non della fonte usata: dal Giro 5 gli arrivi di questo rapporto vengono dal GPS)")
    if gps:
        R.append(f"  linee {', '.join(gps['linee'])}, giorno {gps['giorno']}: {gps['passaggi_confrontati']} passaggi, "
                 f"{gps['fermate']} fermate")
        R.append(f"  differenza mediana {gps['differenza_mediana_min']} min, |differenza| mediana "
                 f"{gps['differenza_assoluta_mediana_min']} min, entro 1 minuto: {gps['entro_1_min_pct']}%")
        if gps["differenza_assoluta_mediana_min"] is not None and gps["differenza_assoluta_mediana_min"] > 1:
            R.append("  ATTENZIONE: |differenza| mediana oltre 1 minuto -> da decidere con Leo (piano, passo 4)")
    R.append("")
    R.append("ESEMPI PER IL CONTROLLO A MANO (passo 2): orario, arrivo misurato dal GPS (ora italiana), corsa vista dal GPS (feed= e gps= coincidono)")
    for linea, e in sorted(esempi.items()):
        R.append(f"  linea {linea} verso {e['direzione']} fermata {e['stop_id']} ({fermate.get(e['stop_id'], ('?',))[0]}), {e['giorno']}")
        for sch, est, f, g in e["passaggi"]:
            R.append(f"    {sch}  {est or '   -    '}  feed={'si' if f else 'no'} gps={'si' if g else 'no'}")
    R.append("")
    R.append("Nota: le due stime usano tratti diversi (la bassa solo i tratti senza corse mancanti); per una singola")
    R.append("linea la 'alta' puo' quindi uscire poco sotto la 'bassa'. Per la citta' la forbice e' ordinata.")
    R.append("Limiti: arrivi misurati con il GPS (meno di 60 m dalla fermata); solo linee urbane viste dal GPS quel giorno; niente notte;")
    R.append("corse mancanti -> forbice bassa/alta; chi arriva 'a caso' (vero per le linee frequenti); pochi giorni.")
    R.append("")
    R.append("ATTESA PER MODO (feriale, linee frequenti, stessa media pesata della citta')")
    if ris.get("modi") is None:
        R.append("  (manca modo_linea: lancia prima scripts/27_risultato4_regolarita.py)")
    else:
        R.append("modo  | promessa | in piu' bassa - alta | reale bassa - alta | intervalli programmati | intervalli oss.")
        for m, c in ris["modi"]["0"].items():
            if c:
                R.append(f"{m:<5} | {c['promessa_min']:8.1f} | {c['in_piu_min_bassa']:8.1f} - {c['in_piu_min_alta']:<8.1f} | "
                         f"{c['reale_min_bassa']:8.1f} - {c['reale_min_alta']:<8.1f} | {c['intervalli_programmati']:>22} | "
                         f"{c['intervalli_osservati']:>10}")
            else:
                R.append(f"{m:<5} | nessuna linea frequente con dati")
    # Giro 6: riepilogo di quanto resta dopo l'esclusione dei giorni senza GPS
    R.append("")
    R.append("RIEPILOGO DEI DATI USATI (Giro 6)")
    R.append(f"  chiavi fermata-linea-verso-fascia-giorno frequenti: {ris['chiavi_frequenti']}, usate: {ris['chiavi_usate']}")
    modi_f = (ris.get("modi") or {}).get("0") or {}
    for m in ("tram", "bus"):
        c = modi_f.get(m)
        R.append(f"  {m}: intervalli osservati {c['intervalli_osservati'] if c else 0}, programmati {c['intervalli_programmati'] if c else 0}")
    n_bus = (modi_f.get("bus") or {}).get("intervalli_osservati", 0)
    if n_bus < MIN_INTERVALLI_BUS_AVVISO:
        R.append(f"  AVVISO: i bus hanno {n_bus} intervalli osservati, meno di {MIN_INTERVALLI_BUS_AVVISO}: da decidere con Leo")
    else:
        R.append(f"  OK: i bus hanno {n_bus} intervalli osservati (almeno {MIN_INTERVALLI_BUS_AVVISO})")
    testo = "\n".join(R)
    print(testo)

    if scrivi:
        out = {"tag": TAG, "generato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "parametri": {"freq_max_min": freq, "min_minuti_ora": MIN_MINUTI_ORA, "max_mancanti": MAX_MANCANTI,
                             "min_intervalli_chiave": MIN_INTERVALLI_CHIAVE,
                             "min_intervalli_classifica": MIN_INTERVALLI_CLASSIFICA},
               "periodo": {"da": r4.da_gttfs(giorni[0]), "a": r4.da_gttfs(giorni[-1])}, "giorni": tipi_giorno,
               "giorni_esclusi_gps": esclusi_gps, "per_giorno": per_giorno, "sensibilita_freq": sens, "controllo_gps": gps, "esempi": esempi, **ris}
        OUT_JSON.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
        OUT_RAPPORTO.write_text(testo, encoding="utf-8")
        print(f"Scritto: {OUT_JSON}\nScritto: {OUT_RAPPORTO}")


if __name__ == "__main__":
    main()
