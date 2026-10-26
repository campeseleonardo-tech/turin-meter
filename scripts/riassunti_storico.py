#!/usr/bin/env python3
"""
riassunti_storico.py  -  formato e lettura dei RIASSUNTI dello storico (scritti dallo script 97).

Lo storico SQLite della raccolta (data/storico_backup.sqlite, GB) non sta in git. Al suo posto si tengono riassunti piccoli, che
gli script 27, 70, 26 e 71 leggono quando lo storico non c'e' (o con --riassunti) e che danno gli stessi numeri.

Cartella: data/storico_riassunti/
  anagrafica.json                    sensori 5T (nome, direzione, lat, lng) e parcheggi 5T (id, nome, lat, lng, totale)
  passaggi_AAAA-MM.zip               per ogni giorno GTFS (start_date): meta.json + colonne binarie dei passaggi
                                     (GPS e feed): corsa (indice), fermata (stop_sequence) e ritardo in millisecondi
                                     rispetto all'orario programmato; corsa e fermata sono differenze rispetto alla riga prima
                                     (si comprime molto meglio); il resto (linea, verso, fermata, orario) si ricava dal GTFS
  sensori5t_AAAA-MM.json.gz          per giorno locale, sensore e ora: [letture, somma flussi, letture con flusso>0,
                                     somma velocita'*flusso, somma flussi>0] + prima/ultima lettura del giorno + conteggi
  parcheggi_AAAA-MM.json.gz          per giorno locale, parcheggio e ora: [letture valide, somma occupazione] + conteggi
  ora_tipica.json                    posizioni dei mezzi in un feriale tipico 7:30-8:30 (animazione della home)

Questo modulo contiene: le funzioni per scrivere (usate da 97), la classe SorgenteRiassunti (stessa interfaccia di
SorgenteDb dello script 27) e i lettori dei riassunti 5T e parcheggi.
"""
import gzip
import json
import os
import sys
import zipfile
from array import array
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402

RADICE = comuni.RADICE
CARTELLA = RADICE / "data" / "storico_riassunti"      # si puo' cambiare (prove)
VERSIONE = 1


# ---------------------------------------------------------------- utilita'
def cartella(c=None):
    return Path(c) if c else CARTELLA


def mese_da_giorno(giorno):
    """'20261013' -> '2026-10'"""
    return f"{giorno[0:4]}-{giorno[4:6]}"


def mese_da_data(d):
    """'2026-10-13' -> '2026-10'"""
    return d[:7]


def _le(a):
    """array in little endian (il formato dei file)."""
    if sys.byteorder == "big":
        a.byteswap()
    return a


def _bytes(a):
    b = array(a.typecode, a)
    return _le(b).tobytes()


def _da_bytes(codice, dati):
    a = array(codice)
    a.frombytes(dati)
    return _le(a)


def scrivi_atomico(percorso, contenuto):
    percorso = Path(percorso)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    tmp = percorso.with_name(percorso.name + ".part")
    tmp.write_bytes(contenuto)
    os.replace(tmp, percorso)


def scrivi_json(percorso, obj):
    scrivi_atomico(percorso, json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def scrivi_json_gz(percorso, obj):
    dati = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    scrivi_atomico(percorso, gzip.compress(dati, 9, mtime=0))


def leggi_json_gz(percorso):
    with gzip.open(percorso, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


# ---------------------------------------------------------------- passaggi (scripts 27 e 70)
def colonne_passaggi(passaggi, base, con_fonte, p_trip, p_seq, p_est, p_fonte, p_sched):
    """Da una lista di tuple di passaggi (le stesse dello script 27) a (lista delle corse, colonne binarie).
    Le corse sono indicate con l'indice nell'ordine della prima comparsa. Colonne: differenza dell'indice della corsa e della
    stop_sequence rispetto al passaggio prima (di solito 0 e +1), ritardo in millisecondi rispetto all'orario programmato."""
    indice, corse = {}, []
    trip, seq, rit, fonte = array("i"), array("h"), array("i"), array("B")
    t_prec = s_prec = 0
    for p in passaggi:
        tid = p[p_trip]
        i = indice.get(tid)
        if i is None:
            i = indice[tid] = len(corse)
            corse.append(tid)
        trip.append(i - t_prec)
        seq.append(p[p_seq] - s_prec)
        t_prec, s_prec = i, p[p_seq]
        rit.append(int(round((p[p_est] - p[p_sched]) * 1000)))
        if con_fonte:
            fonte.append(0 if p[p_fonte] == "delay" else 1)
    cols = {"trip": _bytes(trip), "seq": _bytes(seq), "rit": _bytes(rit)}
    if con_fonte:
        cols["fonte"] = _bytes(fonte)
    return corse, cols


def _percorso_passaggi(mese, c=None):
    return cartella(c) / f"passaggi_{mese}.zip"


def salva_giorno_passaggi(giorno, meta, gps_cols, feed_cols, c=None):
    """Aggiunge (o sostituisce) il giorno nello zip del suo mese. meta: dizionario JSON-izzabile."""
    percorso = _percorso_passaggi(mese_da_giorno(giorno), c)
    voci = {}
    if percorso.exists():
        with zipfile.ZipFile(percorso) as z:
            for n in z.namelist():
                if not n.startswith(giorno + "/"):
                    voci[n] = z.read(n)
    voci[f"{giorno}/meta.json"] = json.dumps(meta, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    for k, b in gps_cols.items():
        voci[f"{giorno}/gps_{k}.bin"] = b
    for k, b in feed_cols.items():
        voci[f"{giorno}/feed_{k}.bin"] = b
    percorso.parent.mkdir(parents=True, exist_ok=True)
    tmp = percorso.with_name(percorso.name + ".part")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for n in sorted(voci):
            z.writestr(zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0)), voci[n], zipfile.ZIP_DEFLATED, 9)
    os.replace(tmp, percorso)


def giorni_passaggi_presenti(c=None):
    """{giorno: dimensione in byte nello zip} per tutti i giorni gia' riassunti."""
    out = {}
    for p in sorted(cartella(c).glob("passaggi_*.zip")):
        with zipfile.ZipFile(p) as z:
            for i in z.infolist():
                g = i.filename.split("/")[0]
                out[g] = out.get(g, 0) + i.compress_size
    return out


class SorgenteRiassunti:
    """Stessa interfaccia di SorgenteDb (script 27): i dati vengono dai riassunti. ctx = (trip_info, nome_linea, prog).
    fascia = funzione (istante programmato in secondi UTC) -> fascia oraria, passata dallo script 27."""
    nome = "riassunti dello storico (script 97)"

    def __init__(self, c=None, fascia=None):
        self.cartella = cartella(c)
        self.fascia = fascia
        self._zip = {}
        self._meta_cache = {}
        self._giorni = None

    # --- accesso ai file
    def _z(self, giorno):
        mese = mese_da_giorno(giorno)
        if mese not in self._zip:
            self._zip[mese] = zipfile.ZipFile(_percorso_passaggi(mese, self.cartella))
        return self._zip[mese]

    def giorni(self):
        if self._giorni is None:
            self._giorni = sorted(set(giorni_passaggi_presenti(self.cartella)))
        return list(self._giorni)

    def meta(self, giorno):
        if giorno not in self._meta_cache:
            self._meta_cache[giorno] = json.loads(self._z(giorno).read(f"{giorno}/meta.json").decode("utf-8"))
        return self._meta_cache[giorno]

    def _colonne(self, giorno, prefisso):
        z = self._z(giorno)
        leggi = lambda nome, cod: _da_bytes(cod, z.read(f"{giorno}/{prefisso}_{nome}.bin"))
        try:
            fonte = leggi("fonte", "B")
        except KeyError:
            fonte = None
        return leggi("trip", "i"), leggi("seq", "h"), leggi("rit", "i"), fonte

    # --- interfaccia comune
    def corse_viste(self, giorno, trip_info):
        return self.meta(giorno)["cop"]["corse_viste"]

    def passaggi_gps(self, giorno, ctx, fermate):
        """(passaggi, copertura): le tuple dello script 27 (linea, verso, fermata, orario, istante GPS, ritardo, fascia, seq, 'gps', corsa)."""
        trip_info, nome_linea, prog = ctx
        m = self.meta(giorno)
        base = m["base"]
        corse = m["corse_gps_passaggi"]
        trip, seq, rit_ms, _ = self._colonne(giorno, "gps")
        fascia_cache, out = {}, []
        i_corsa = s = 0
        for i in range(len(trip)):
            i_corsa += trip[i]
            s += seq[i]
            tid = corse[i_corsa]
            sec, stop = prog[(tid, s)]
            route, direzione = trip_info[tid]
            sched = base + sec
            h = int(sched) // 3600
            if h not in fascia_cache:
                fascia_cache[h] = self.fascia(sched)
            t = sched + rit_ms[i] / 1000.0
            out.append((nome_linea.get(route, route), direzione, stop, sched, t, (t - sched) / 60.0, fascia_cache[h], s, "gps", tid))
        return out, dict(m["cop"])

    def passaggi_feed(self, giorno, ctx):
        """(passaggi, scarti, tipo, esempi, letture) come SorgenteDb.passaggi_feed."""
        trip_info, nome_linea, prog = ctx
        m = self.meta(giorno)
        base = m["base"]
        corse = m["corse_feed"]
        trip, seq, rit_ms, fonte = self._colonne(giorno, "feed")
        fascia_cache, out = {}, []
        i_corsa = s = 0
        for i in range(len(trip)):
            i_corsa += trip[i]
            s += seq[i]
            tid = corse[i_corsa]
            sec, stop = prog[(tid, s)]
            route, direzione = trip_info[tid]
            sched = base + sec
            h = int(sched) // 3600
            if h not in fascia_cache:
                fascia_cache[h] = self.fascia(sched)
            t = sched + rit_ms[i] / 1000.0
            out.append((nome_linea.get(route, route), direzione, stop, sched, t, (t - sched) / 60.0, fascia_cache[h], s,
                        "delay" if fonte[i] == 0 else "time", tid))
        return out, list(m["scarti"]), m["tipo"], m["esempi"], m["letti"]

    def corse_gps(self, giorno):
        return set(self.meta(giorno)["corse_gps"])

    def ore_minuti(self, giorno):
        return {int(h): n for h, n in self.meta(giorno)["ore_minuti"].items()}

    def ore_attive(self, giorno, min_minuti):
        return {h for h, n in self.ore_minuti(giorno).items() if n >= min_minuti}

    def controllo_gps(self, giorno):
        return self.meta(giorno).get("controllo_gps")

    def chiudi(self):
        for z in self._zip.values():
            z.close()
        self._zip = {}


# ---------------------------------------------------------------- sensori 5T (script 26)
def riassumi_5t(con, dal_utc=None, al_utc=None, solo_mese=None):
    """Riassunto per giorno locale dei sensori 5T. Le letture sono quelle affidabili (accuratezza > 0, flusso presente).
    dal_utc/al_utc: limiti ISO su generato_utc (per riassumere un mese alla volta, con un giorno di margine);
    solo_mese 'AAAA-MM': tiene solo i giorni locali di quel mese. Ritorna {data: record}."""
    clausola, par = "", []
    if dal_utc:
        clausola += " AND f.generato_utc >= ?"
        par.append(dal_utc)
    if al_utc:
        clausola += " AND f.generato_utc < ?"
        par.append(al_utc)
    giorni = {}

    def rec(d):
        return giorni.setdefault(d, {"celle": {}, "prima": None, "ultima": None, "scartate": 0, "senza_riga": 0, "totale": 0})

    for g, lcd1, flusso, vel in con.execute(
            "SELECT f.generato_utc, f.lcd1, f.flusso, f.velocita FROM flussi_5t f "
            "JOIN accuratezza_5t a ON a.generato_utc = f.generato_utc AND a.lcd1 = f.lcd1 "
            "WHERE a.accuratezza > 0 AND f.flusso IS NOT NULL" + clausola, par):
        loc = comuni.ora_locale(datetime.fromisoformat(g.replace("Z", "+00:00")).astimezone(timezone.utc))
        d = loc.date().isoformat()
        r = rec(d)
        m = loc.hour * 60 + loc.minute
        r["prima"] = m if r["prima"] is None else min(r["prima"], m)
        r["ultima"] = m if r["ultima"] is None else max(r["ultima"], m)
        c = r["celle"].setdefault(lcd1, {}).setdefault(str(loc.hour), [0, 0.0, 0, 0.0, 0.0])
        c[0] += 1
        c[1] += flusso
        if flusso > 0 and vel is not None:
            c[2] += 1
            c[3] += vel * flusso
            c[4] += flusso
    # conteggi per l'ora UTC (un'ora UTC cade in una sola ora locale)
    for campo, sql in (("scartate", "JOIN accuratezza_5t a ON a.generato_utc = f.generato_utc AND a.lcd1 = f.lcd1 WHERE a.accuratezza = 0"),
                       ("senza_riga", "LEFT JOIN accuratezza_5t a ON a.generato_utc = f.generato_utc AND a.lcd1 = f.lcd1 WHERE a.generato_utc IS NULL"),
                       ("totale", "WHERE 1 = 1")):
        for ora, n in con.execute(f"SELECT substr(f.generato_utc,1,13), COUNT(*) FROM flussi_5t f {sql}" + clausola + " GROUP BY 1", par):
            t = datetime.fromisoformat(ora + ":00:00+00:00")
            rec(comuni.ora_locale(t).date().isoformat())[campo] += n
    if solo_mese:
        giorni = {d: r for d, r in giorni.items() if mese_da_data(d) == solo_mese}
    return giorni


def salva_5t_mese(mese, giorni, c=None):
    scrivi_json_gz(cartella(c) / f"sensori5t_{mese}.json.gz",
                   {"versione": VERSIONE, "mese": mese, "generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "giorni": giorni})


def carica_5t(c=None):
    """Tutti i giorni dei riassunti 5T: {data: record}."""
    out = {}
    for p in sorted(cartella(c).glob("sensori5t_*.json.gz")):
        out.update(leggi_json_gz(p)["giorni"])
    return out


# ---------------------------------------------------------------- parcheggi (script 71)
def riassumi_parcheggi(con, parcheggi, dal_utc=None, al_utc=None, solo_mese=None):
    """Riassunto per giorno locale: per parcheggio e ora [letture valide, somma dell'occupazione 0-1], piu' i conteggi.
    parcheggi = {id: totale posti dalla tabella parcheggi_5t} (usato quando la lettura non ha il totale)."""
    clausola, par = "", []
    if dal_utc:
        clausola += " WHERE generato_utc >= ?"
        par.append(dal_utc)
    if al_utc:
        clausola += (" AND" if clausola else " WHERE") + " generato_utc < ?"
        par.append(al_utc)
    giorni = {}
    for generato, pid, stato, totale, liberi in con.execute(
            "SELECT generato_utc, id, stato, totale, liberi FROM occupazione_pk" + clausola, par):
        dt = datetime.strptime(generato[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        loc = comuni.ora_locale(dt)
        d = loc.date().isoformat()
        r = giorni.setdefault(d, {"celle": {}, "scartate": 0, "righe": 0})
        r["righe"] += 1
        if pid not in parcheggi:
            continue
        if stato != 1 or liberi is None:
            r["scartate"] += 1
            continue
        tot = totale or parcheggi[pid]
        if not tot:
            r["scartate"] += 1
            continue
        occ = max(0.0, min(1.0, 1.0 - liberi / tot))
        c = r["celle"].setdefault(pid, {}).setdefault(str(loc.hour), [0, 0.0])
        c[0] += 1
        c[1] += occ
    if solo_mese:
        giorni = {d: r for d, r in giorni.items() if mese_da_data(d) == solo_mese}
    return giorni


def salva_parcheggi_mese(mese, giorni, c=None):
    scrivi_json_gz(cartella(c) / f"parcheggi_{mese}.json.gz",
                   {"versione": VERSIONE, "mese": mese, "generato": datetime.now(timezone.utc).isoformat(timespec="seconds"), "giorni": giorni})


def carica_parcheggi(c=None):
    out = {}
    for p in sorted(cartella(c).glob("parcheggi_*.json.gz")):
        out.update(leggi_json_gz(p)["giorni"])
    return out


# ---------------------------------------------------------------- anagrafica
def salva_anagrafica(sensori, parcheggi, c=None):
    """sensori: {lcd1: [nome, direzione, lat, lng]}; parcheggi: [[id, nome, lat, lng, totale], ...]"""
    scrivi_json(cartella(c) / "anagrafica.json", {"versione": VERSIONE, "sensori": sensori, "parcheggi": parcheggi})


def carica_anagrafica(c=None):
    p = cartella(c) / "anagrafica.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def esiste_5t(c=None):
    return any(cartella(c).glob("sensori5t_*.json.gz")) and (cartella(c) / "anagrafica.json").exists()


def esiste_parcheggi(c=None):
    return any(cartella(c).glob("parcheggi_*.json.gz")) and (cartella(c) / "anagrafica.json").exists()
