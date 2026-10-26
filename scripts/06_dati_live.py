#!/usr/bin/env python3
"""
06_dati_live.py - trasforma lo storico raccolto (data/storico.sqlite) in piccoli file che la mappa rilegge da sola.

Scrive in GTT/data/:
  live.js      ogni minuto: ultime posizioni reali dei mezzi GTT e ultimo traffico 5T.
  stat.js      ogni 15 minuti: traffico tipico per sensore/ora/tipo di giorno, mezzi reali per linea/ora,
               quanti dati ci sono, giornate disponibili per il replay.
  replay_AAAA-MM-GG.js   una giornata registrata di posizioni reali (per lo slider "Replay").

Lo lancia in automatico il supervisore. A mano (per prova):  python 06_dati_live.py   (tutto)  |  --solo-live
Solo libreria standard. Legge il database in sola lettura.
"""
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RADICE = next((c for c in [AQUI, *AQUI.parents] if c.name.lower() == "gtt"), AQUI.parent)
DB = RADICE / "data" / "storico.sqlite"
DATA = RADICE / "data"
CACHE = DATA / "agg_cache.json"
GIORNI_REPLAY = 10


# ---- ora legale italiana senza database dei fusi orari (Windows spesso non lo ha)
def ultima_domenica(anno, mese):
    d = date(anno, mese, 31 if mese in (3, 10) else 30)
    while d.weekday() != 6:
        d -= timedelta(days=1)
    return d


def offset_roma(dt_utc):
    a = dt_utc.year
    inizio = datetime(a, 3, ultima_domenica(a, 3).day, 1, tzinfo=timezone.utc)
    fine = datetime(a, 10, ultima_domenica(a, 10).day, 1, tzinfo=timezone.utc)
    return 2 if inizio <= dt_utc < fine else 1


def locale(dt_utc):
    return (dt_utc + timedelta(hours=offset_roma(dt_utc))).replace(tzinfo=None)


def parse_utc(s):
    s = s.replace("Z", "+00:00")
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def tipo_giorno(d):  # 0 feriale, 1 sabato, 2 domenica
    return 1 if d.weekday() == 5 else 2 if d.weekday() == 6 else 0


def apri():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=30)
    return con


def scrivi(percorso, nome_var, oggetto):
    testo = f"window.{nome_var}=" + json.dumps(oggetto, separators=(",", ":"), ensure_ascii=False) + ";\n"
    tmp = percorso.with_suffix(percorso.suffix + ".tmp")
    tmp.write_text(testo, encoding="utf-8")
    tmp.replace(percorso)


# ------------------------------------------------------------------ LIVE
def live():
    con = apri()
    ora = datetime.now(timezone.utc)
    ultimi = [r[0] for r in con.execute("SELECT DISTINCT letto_utc FROM mezzi_gtt ORDER BY letto_utc DESC LIMIT 1")]
    mezzi, letto = [], None
    if ultimi:
        letto = ultimi[0]
        for vid, linea, la, lo, ts, v in con.execute(
                "SELECT veicolo, linea, lat, lng, ts_feed, velocita FROM mezzi_gtt WHERE letto_utc=?", (letto,)):
            mezzi.append({"id": vid, "r": linea, "la": round(la, 5), "lo": round(lo, 5), "ts": ts})
    gen = con.execute("SELECT MAX(generato_utc) FROM flussi_5t").fetchone()[0]
    t5 = {}
    if gen:
        # media degli ultimi 3 rilevamenti (15 min) per ogni sensore + ultimo valore
        recenti = [r[0] for r in con.execute("SELECT DISTINCT generato_utc FROM flussi_5t ORDER BY generato_utc DESC LIMIT 3")]
        q = ",".join("?" * len(recenti))
        for lcd, fl, v, g in con.execute(f"SELECT lcd1, flusso, velocita, generato_utc FROM flussi_5t WHERE generato_utc IN ({q}) ORDER BY generato_utc", recenti):
            e = t5.setdefault(lcd, {"fl": None, "v": None, "f15": [], "v15": []})
            e["fl"], e["v"] = fl, v
            if fl is not None:
                e["f15"].append(fl)
                if v is not None and fl > 0:
                    e["v15"].append((v, fl))
        for e in t5.values():
            f15, v15 = e.pop("f15"), e.pop("v15")
            e["fm"] = round(sum(f15) / len(f15), 1) if f15 else None
            tot = sum(w for _, w in v15)
            e["vm"] = round(sum(v * w for v, w in v15) / tot, 1) if tot else None
    n = con.execute("SELECT COUNT(DISTINCT letto_utc) FROM mezzi_gtt").fetchone()[0]
    con.close()
    scrivi(DATA / "live.js", "LIVE", {"generato": ora.isoformat(timespec="seconds"), "mezzi_letto": letto, "mezzi": mezzi,
                                       "t5_gen": gen, "t5": t5, "letture_mezzi": n})
    return len(mezzi), len(t5)


# ------------------------------------------------------------------ STATISTICHE
def carica_cache():
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {"mezzi": {}, "t5": {}}


def stat():
    con = apri()
    cache = carica_cache()
    ora_corrente = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
    # --- mezzi: per ora UTC chiusa -> {linea: osservazioni}, _s = numero di letture distinte
    snaps = dict(con.execute("SELECT substr(letto_utc,1,13), COUNT(DISTINCT letto_utc) FROM mezzi_gtt GROUP BY 1"))
    for h, ns in snaps.items():
        if h >= ora_corrente or (h in cache["mezzi"] and cache["mezzi"][h]["_s"] == ns):
            continue
        d = {"_s": ns}
        for linea, n in con.execute("SELECT linea, COUNT(*) FROM mezzi_gtt WHERE substr(letto_utc,1,13)=? AND linea<>'' GROUP BY linea", (h,)):
            d[linea] = n
        cache["mezzi"][h] = d
    # --- traffico 5T per ora UTC chiusa -> {sensore: [somma flusso, somma velocita*flusso, n misure]}
    for h, in con.execute("SELECT DISTINCT substr(generato_utc,1,13) FROM flussi_5t").fetchall():
        if h >= ora_corrente or h in cache["t5"]:
            continue
        d = {}
        for lcd, sf, svf, n, nr in con.execute(
                "SELECT lcd1, SUM(flusso), SUM(velocita*flusso), COUNT(*), COUNT(DISTINCT generato_utc) FROM flussi_5t "
                "WHERE substr(generato_utc,1,13)=? AND flusso IS NOT NULL GROUP BY lcd1", (h,)):
            d[lcd] = [sf or 0, svf or 0, n]
        cache["t5"][h] = d
    CACHE.write_text(json.dumps(cache, separators=(",", ":")), encoding="utf-8")

    # --- aggregazione per tipo di giorno e ora locale
    reale = defaultdict(lambda: [[0.0, 0] for _ in range(72)])      # linea -> [somma(veicoli per lettura), n ore]
    for h, d in cache["mezzi"].items():
        dtu = datetime.fromisoformat(h + ":00:00").replace(tzinfo=timezone.utc)
        lo = locale(dtu)
        k = tipo_giorno(lo) * 24 + lo.hour
        for linea, n in d.items():
            if linea != "_s":
                c = reale[linea][k]; c[0] += n / d["_s"]; c[1] += 1
    reale_out = {l: [round(a / b, 2) if b else None for a, b in v] for l, v in reale.items()}
    cop = {}   # numero di ore-campione per ora del giorno/tipo di giorno
    for h, d in cache["mezzi"].items():
        dtu = datetime.fromisoformat(h + ":00:00").replace(tzinfo=timezone.utc)
        lo = locale(dtu); k = tipo_giorno(lo) * 24 + lo.hour
        cop[k] = cop.get(k, 0) + 1

    tip = defaultdict(lambda: [[0.0, 0.0, 0, 0] for _ in range(72)])  # sensore -> [sf, svf, nmisure, nore]
    for h, d in cache["t5"].items():
        dtu = datetime.fromisoformat(h + ":00:00").replace(tzinfo=timezone.utc)
        lo = locale(dtu); k = tipo_giorno(lo) * 24 + lo.hour
        for lcd, (sf, svf, n) in d.items():
            c = tip[lcd][k]; c[0] += sf; c[1] += svf; c[2] += n; c[3] += 1
    tip_out = {}
    for lcd, v in tip.items():
        riga = []
        for sf, svf, n, nore in v:
            if n == 0:
                riga.append(None)
            else:
                riga.append([round(svf / sf, 1) if sf > 0 else None, round(sf / n, 0), nore])   # velocita pesata, flusso/ora (il valore 5T e' gia' in veicoli/ora: sempre multiplo di 12), ore-campione
        tip_out[lcd] = riga

    # --- riepilogo e giornate per il replay
    primo, ultimo = con.execute("SELECT MIN(letto_utc), MAX(letto_utc) FROM mezzi_gtt").fetchone()
    giorni = {}
    for (s,) in con.execute("SELECT DISTINCT letto_utc FROM mezzi_gtt"):
        g = locale(parse_utc(s)).date().isoformat()
        giorni[g] = giorni.get(g, 0) + 1
    con.close()
    ore_mezzi = len(cache["mezzi"]); ore_t5 = len(cache["t5"])
    scrivi(DATA / "stat.js", "STAT", {
        "generato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "primo": primo, "ultimo": ultimo, "ore_mezzi": ore_mezzi, "ore_t5": ore_t5,
        "giorni": dict(sorted(giorni.items())), "tipico": tip_out, "reale": reale_out, "copertura": cop,
    })
    return ore_mezzi, ore_t5, len(tip_out), len(reale_out)


# ------------------------------------------------------------------ REPLAY
def replay(solo_oggi=False):
    con = apri()
    righe = list(con.execute("SELECT DISTINCT letto_utc FROM mezzi_gtt ORDER BY letto_utc"))
    per_giorno = defaultdict(list)
    for (s,) in righe:
        lo = locale(parse_utc(s))
        per_giorno[lo.date().isoformat()].append((s, lo.hour * 60 + lo.minute + lo.second / 60))
    scelti = sorted(per_giorno)[-GIORNI_REPLAY:]
    if solo_oggi:
        scelti = scelti[-1:]
    fatti = []
    for g in scelti:
        veicoli, indice, snaps = [], {}, []
        for s, minuto in per_giorno[g]:
            flat = []
            for vid, linea, la, lo_ in con.execute("SELECT veicolo, linea, lat, lng FROM mezzi_gtt WHERE letto_utc=?", (s,)):
                if vid not in indice:
                    indice[vid] = len(veicoli); veicoli.append([vid, linea])
                flat += [indice[vid], round((la - 44) * 1e5), round((lo_ - 7) * 1e5)]
            snaps.append([round(minuto, 1), flat])
        scrivi(DATA / f"replay_{g}.js", "REPLAY_" + g.replace("-", "_"), {"g": g, "tipo": tipo_giorno(date.fromisoformat(g)), "v": veicoli, "s": snaps})
        fatti.append(g)
    con.close()
    # elimina i replay piu' vecchi dei GIORNI_REPLAY
    for p in sorted(DATA.glob("replay_*.js"))[:-GIORNI_REPLAY]:
        try:
            p.unlink()
        except OSError:
            pass
    return fatti


def tutto():
    return {"live": live(), "stat": stat(), "replay": replay()}


if __name__ == "__main__":
    if not DB.is_file():
        sys.exit(f"Database non trovato: {DB}")
    if "--solo-live" in sys.argv:
        print(live())
    else:
        print(tutto())
