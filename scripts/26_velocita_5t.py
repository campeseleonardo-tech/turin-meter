#!/usr/bin/env python3
"""26_velocita_5t.py

Calcola la velocita' e il flusso TIPICI dei sensori 5T, per sensore x tipo di
giorno x ora locale, usando solo le letture affidabili.

Differenze rispetto al "tipico" di data/stat.js (06_dati_live.py sul Pi):
- qui si usano SOLO le letture con una riga in accuratezza_5t e
  accuratezza > 0 (la tabella esiste dal 08/10 21:30 UTC: le letture precedenti
  si escludono perche' non hanno storico di affidabilita');
- il "tipico" di stat.js non scarta nulla.

Regole (vedi sviluppo/note_tecniche/R8_traffico.md):
- velocita' tipica = media PESATA PER IL FLUSSO (sum(v*f)/sum(f)) solo su
  letture con flusso > 0, cosi' come in stat.js, per poter confrontare;
- flusso tipico = media del flusso su TUTTE le letture affidabili della cella,
  zeri compresi;
- cella "ok" = almeno 2 giorni distinti e almeno 6 letture con flusso > 0;
- tipo di giorno: 0 = feriale (lun-ven), 1 = sabato, 2 = domenica;
- ore locali Europe/Rome calcolate a mano (niente zoneinfo).

Letture in SOLA LETTURA su data/storico_backup.sqlite; se lo storico non c'e' (o con --riassunti) si leggono
i riassunti scritti dallo script 97 (data/storico_riassunti/sensori5t_*.json.gz): stessi numeri.
Output:
- data/processed/velocita_5t.json
- docs/rapporti/RAPPORTO_VELOCITA_5T.txt

Con --prova si calcolano solo i primi 2 giorni locali dopo l'8/10 21:30 UTC e
il rapporto va SOLO su console (non tocca i file di output).

Solo libreria standard.
"""

import argparse
import json
import sqlite3
import sys
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402  (PERIODO fisso dei dati)
import riassunti_storico as rs  # noqa: E402  (riassunti dello storico, script 97)

RADICE = Path(__file__).resolve().parents[1]
DB = RADICE / "data" / "storico_backup.sqlite"
OUT = RADICE / "data" / "processed" / "velocita_5t.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_VELOCITA_5T.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

MIN_GIORNI = 2      # giorni distinti minimi per una cella "ok"
MIN_LETTURE = 6     # letture con flusso > 0 minimi per una cella "ok"
INIZIO_ACCURATEZZA = datetime(2026, 10, 8, 21, 30, tzinfo=timezone.utc)
PROVA_GIORNI = 2    # giorni locali usati con --prova

RIGHE = []          # testo del rapporto


def scrivi(msg=""):
    RIGHE.append(str(msg))


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


def parsa_utc(s):
    """Timestamp ISO (con Z o +00:00, con o senza millisecondi) -> datetime UTC."""
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def tipo_giorno(d):
    """0 = feriale (lun-ven), 1 = sabato, 2 = domenica."""
    return {5: 1, 6: 2}.get(d.weekday(), 0)


def nome_tipo(t):
    return {0: "feriale", 1: "sabato", 2: "domenica"}[t]


# ---------- lettura ----------

def apri_db(percorso):
    if not percorso.is_file():
        raise SystemExit(f"DB non trovato: {percorso}")
    con = sqlite3.connect(f"file:{percorso}?mode=ro", uri=True, timeout=60)
    con.execute("PRAGMA busy_timeout=60000")
    return con


def main():
    ap = argparse.ArgumentParser(
        description="Velocita'/flusso tipici dei sensori 5T (sola lettura)")
    ap.add_argument("--prova", action="store_true",
                    help=f"solo i primi {PROVA_GIORNI} giorni locali dopo "
                         "l'8/10 21:30 UTC; rapporto solo su console")
    ap.add_argument("--riassunti", action="store_true",
                    help="legge i riassunti dello storico (script 97) anche se lo storico c'e'")
    args = ap.parse_args()

    # sorgente: lo storico SQLite (riassunto al volo con la stessa funzione dello script 97) oppure i riassunti gia' scritti
    if DB.is_file() and not args.riassunti:
        sorgente = "storico SQLite"
        con = apri_db(DB)
        cur = con.cursor()
        anag_grezza = {lcd1: [nome, direzione, lat, lng] for lcd1, nome, direzione, lat, lng in cur.execute(
            "SELECT lcd1, nome_strada, direzione, lat, lng FROM sensori_5t")}
        giorni_dati = rs.riassumi_5t(con)
        con.close()
    else:
        if not rs.esiste_5t():
            raise SystemExit(f"Manca lo storico ({DB}) e non ci sono riassunti 5T in {rs.CARTELLA}: "
                             "lancia scripts/97_riassunti_storico.py (o scarica i dati con scripts/scarica_dati.py).")
        sorgente = "riassunti dello storico (script 97)"
        anag_grezza = rs.carica_anagrafica()["sensori"]
        giorni_dati = rs.carica_5t()

    giorni_dati = {d: r for d, r in giorni_dati.items() if comuni.nel_periodo(d, "sensori")}   # periodo fisso (L9): comuni.PERIODO
    anagrafica = {}
    for lcd1, (nome, direzione, lat, lng) in anag_grezza.items():
        anagrafica[lcd1] = dict(via=nome or "", dir=direzione or "?",
                                lat=lat, lon=lng,
                                urbano="(TO)" in (nome or ""))

    # letture scartate: accuratezza = 0 / senza riga / totale (servono al rapporto)
    n_scartate = sum(r["scartate"] for r in giorni_dati.values())
    n_senza_riga = sum(r["senza_riga"] for r in giorni_dati.values())
    n_tot_flussi = sum(r["totale"] for r in giorni_dati.values())

    # giorni con letture affidabili, in ordine; ogni giorno: n letture, prima/ultima lettura (minuti), celle
    giorni_loc = {date.fromisoformat(d): r for d, r in giorni_dati.items() if r["celle"]}
    n_letture_giorno = {d: sum(c[0] for ore in r["celle"].values() for c in ore.values()) for d, r in giorni_loc.items()}

    # --- eventuale filtro per la prova: primi N giorni locali dopo INIZIO_ACCURATEZZA ---
    if args.prova:
        # giorni locali SUCCESSIVI a quello dell'inizio accuratezza
        # (l'8/10 l'accuratezza copre solo le ultime mezz'ora: si salta)
        limite = a_roma(INIZIO_ACCURATEZZA).date()
        giorni_ok = sorted(d for d in giorni_loc if d > limite)[:PROVA_GIORNI]
        giorni_loc = {d: r for d, r in giorni_loc.items() if d in set(giorni_ok)}
        print(f"--prova: {len(giorni_ok)} giorni locali "
              f"({', '.join(str(d) for d in sorted(giorni_ok))}), "
              f"letture {sum(n_letture_giorno[d] for d in giorni_loc)}")

    # --- giorni parziali ai bordi del periodo: si escludono (regola 17/10) ---
    # Il primo e l'ultimo giorno locale dei dati contano solo se coprono tutta la
    # giornata (primo giorno: prima lettura entro le 00:30; ultimo: ultima dopo le 23:30).
    giorni_esclusi = set()
    if giorni_loc:
        primo_g, ultimo_g = min(giorni_loc), max(giorni_loc)
        if giorni_loc[primo_g]["prima"] > 30:
            giorni_esclusi.add(primo_g)
        if giorni_loc[ultimo_g]["ultima"] < 23 * 60 + 30:
            giorni_esclusi.add(ultimo_g)
        giorni_loc = {d: r for d, r in giorni_loc.items() if d not in giorni_esclusi}
    n_letture = sum(n_letture_giorno[d] for d in giorni_loc)

    # --- accumulo per (sensore, tipo, ora) ---
    celle = {}      # (lcd1, tipo, ora) -> dict
    giorni_tipo = set()
    primo = ultimo = None
    for d in sorted(giorni_loc):
        giorni_tipo.add((tipo_giorno(d), d))
        primo = d if primo is None or d < primo else primo
        ultimo = d if ultimo is None or d > ultimo else ultimo
        for lcd1, ore in giorni_loc[d]["celle"].items():
            for ora, (n, sf, n_pos, svf, sf_pos) in ore.items():
                k = (lcd1, tipo_giorno(d), int(ora))
                c = celle.setdefault(k, dict(sf=0.0, n=0, svf=0.0, sf_pos=0.0,
                                             n_pos=0, giorni=set()))
                c["sf"] += sf
                c["n"] += n
                c["giorni"].add(d)
                c["svf"] += svf
                c["sf_pos"] += sf_pos
                c["n_pos"] += n_pos

    # --- costruzione output ---
    sensori = {lcd1: dict(**info, celle={}) for lcd1, info in anagrafica.items()}
    n_celle = n_ok = 0
    ok_per_tipo = {0: 0, 1: 0, 2: 0}
    tot_per_tipo = {0: 0, 1: 0, 2: 0}
    for (lcd1, tipo, ora), c in celle.items():
        v = round(c["svf"] / c["sf_pos"], 1) if c["sf_pos"] > 0 else None
        f = round(c["sf"] / c["n"])
        g = len(c["giorni"])
        ok = g >= MIN_GIORNI and c["n_pos"] >= MIN_LETTURE
        celle_out = sensori[lcd1]["celle"].setdefault(str(tipo), {})
        celle_out[str(ora)] = dict(v=v, f=f, n=c["n"], g=g, ok=ok)
        n_celle += 1
        tot_per_tipo[tipo] += 1
        if ok:
            n_ok += 1
            ok_per_tipo[tipo] += 1

    giorni = {str(t): len({d for tt, d in giorni_tipo if tt == t}) for t in (0, 1, 2)}

    if not args.prova:
        payload = {
            "generato": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fonte": "storico_backup.sqlite (o i suoi riassunti), solo letture con accuratezza>0",
            "tag": "MISURATO",
            "periodo": {"da": primo.isoformat(), "a": ultimo.isoformat()},
            "giorni": giorni,
            "parametri": {"min_giorni": MIN_GIORNI, "min_letture": MIN_LETTURE},
            "sensori": sensori,
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                       encoding="utf-8")

    # --- rapporto ---
    scrivi("VELOCITA' 5T TIPICA (solo letture affidabili)")
    scrivi("=" * 72)
    scrivi(f"sorgente (sola lettura): {sorgente}" + (f", {DB}" if sorgente == "storico SQLite" else ""))
    if args.prova:
        scrivi("MODALITA' PROVA: i file di output NON sono stati scritti.")
    scrivi(f"periodo (giorni locali): {primo} -> {ultimo}")
    if giorni_esclusi: scrivi("giorni parziali esclusi (bordo del periodo): " + ", ".join(str(d) for d in sorted(giorni_esclusi)))
    scrivi(f"letture affidabili usate: {n_letture}")
    scrivi(f"letture scartate (accuratezza = 0): {n_scartate} "
           f"({n_scartate / n_tot_flussi:.1%} di {n_tot_flussi} flussi)")
    scrivi(f"letture senza riga in accuratezza_5t (prima del 08/10 21:30 UTC): "
           f"{n_senza_riga} ({n_senza_riga / n_tot_flussi:.1%})")
    scrivi("giorni per tipo: " + ", ".join(
        f"{nome_tipo(t)} {giorni[str(t)]}" for t in (0, 1, 2)))
    scrivi(f"celle (sensore x tipo x ora): {n_celle}, di cui ok: {n_ok}")
    scrivi("celle ok per tipo: " + ", ".join(
        f"{nome_tipo(t)} {ok_per_tipo[t]}/{tot_per_tipo[t]}" for t in (0, 1, 2)))
    if n_ok == 0:
        scrivi("nota: nessuna cella ok perche' servono almeno "
               f"{MIN_GIORNI} GIORNI dello stesso tipo; con così pochi giorni "
               "e' strutturalmente impossibile (non e' un errore dei dati).")

    with_ok = [lcd1 for lcd1, s in sensori.items() if any(
        c["ok"] for celle_t in s["celle"].values() for c in celle_t.values())]
    urbani_ok = [lcd1 for lcd1 in with_ok if sensori[lcd1]["urbano"]]
    scrivi(f"\nsensori con almeno una cella ok: {len(with_ok)} su {len(sensori)} "
           f"(urbani: {len(urbani_ok)} su "
           f"{sum(1 for s in sensori.values() if s['urbano'])})")

    def cella(lcd1, tipo, ora):
        return sensori[lcd1]["celle"].get(str(tipo), {}).get(str(ora))

    def fmt(c):
        if not c or not c["ok"]:
            return "-"
        return f"{c['v']:.1f}"

    # 10 sensori urbani con piu' celle ok
    def n_ok_sensore(lcd1):
        return sum(1 for celle_t in sensori[lcd1]["celle"].values()
                   for c in celle_t.values() if c["ok"])

    top = sorted(urbani_ok, key=lambda l: (-n_ok_sensore(l), l))[:10]
    scrivi("\n-- 10 sensori urbani con piu' celle ok (velocita' feriale km/h) --")
    scrivi(f"{'lcd1':>7}  {'via':34s} {'direzione':9s} {'h8':>5} {'h13':>5} {'h18':>5} "
           f"{'h3':>5}  celle ok")
    for lcd1 in top:
        s = sensori[lcd1]
        scrivi(f"{lcd1:>7}  {s['via'][:34]:34s} {s['dir'][:9]:9s} "
               f"{fmt(cella(lcd1, 0, 8)):>5} {fmt(cella(lcd1, 0, 13)):>5} "
               f"{fmt(cella(lcd1, 0, 18)):>5} {fmt(cella(lcd1, 0, 3)):>5}  "
               f"{n_ok_sensore(lcd1)}")

    # 10 celle feriali urbane piu' lente
    lente = []
    for (lcd1, tipo, ora), c in celle.items():
        if tipo != 0 or not sensori[lcd1]["urbano"]:
            continue
        if c["sf_pos"] <= 0 or not (len(c["giorni"]) >= MIN_GIORNI
                                    and c["n_pos"] >= MIN_LETTURE):
            continue
        lente.append((round(c["svf"] / c["sf_pos"], 1), lcd1, ora))
    lente.sort()
    scrivi("\n-- 10 celle feriali urbane piu' lente (ok, velocita' km/h) --")
    for v, lcd1, ora in lente[:10]:
        s = sensori[lcd1]
        scrivi(f"  {v:5.1f}  {s['via'][:38]:38s} {s['dir'][:9]:9s} ora {ora:02d}  "
               f"(lcd1 {lcd1})")

    testo = "\n".join(RIGHE) + "\n"
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.write(testo)
    if not args.prova:
        RAPPORTO.write_text(testo, encoding="utf-8")
        print(f"Rapporto salvato: {RAPPORTO}")
        print(f"JSON salvato: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
