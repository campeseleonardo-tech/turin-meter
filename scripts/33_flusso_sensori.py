#!/usr/bin/env python3
"""33_flusso_sensori.py  (v2 - 17/10, Fase 2 passo 7b)

Mette in fila, sensore per sensore, il flusso tipico in veicoli/ora
delle 24 ore locali, per ogni tipo di giorno (0 feriale, 1 sabato, 2 domenica),
e aggiunge le misure DIURNE, che sono quelle su cui si puo' contare davvero.

Legge data/processed/velocita_5t.json (prodotto dallo script 26) e l'elenco dei
sensori da escludere data/processed/sensori_esclusi.json (script 35). NON
ricalcola niente dal database.

Novita' della v2 rispetto alla v1:
- i sensori esclusi (morti / bloccati / pochi dati) restano nel file con il campo
  "escluso": "<motivo>" e NESSUN valore: cosi' non si usano per sbaglio.
- per gli altri, per ogni tipo di giorno, si aggiungono:
  * f_diurno       = somma delle ore locali 6-21 (16 ore), solo se TUTTE e 16
                     sono ok, altrimenti null (non si somma un pezzo di giornata);
  * n_ore_diurne_ok= quante delle 16 ore diurne sono ok;
  * f_punta_am     = massimo fra le ore 7-9 (null se nessuna di quelle e' ok);
  * f_punta_pm     = massimo fra le ore 16-19 (null se nessuna di quelle e' ok);
  * quota_diurna   = f_diurno / totale_giorno, solo dove esiste totale_giorno;
  * totale_giorno_stimato = f_diurno diviso la mediana di quota_diurna, scritto
                     come {"valore": ..., "stimato": true} [STIMATO].

L'ora 1 locale (23 UTC) NON viene riempita: nell'ora 1 il sistema non produce
dati affidabili (Fase 1, passo 2ter), quindi non ha un valore e resta com'e'.
Le ore mancanti non si interpolano mai.

Come si legge il resto:
- f_ora[h] = flusso tipico di quell'ora SOLO se la cella del file di partenza
  e' "ok", altrimenti null.
- totale_giorno = somma delle 24 ore, scritta SOLO se tutte e 24 sono ok.
- totale_parziale = somma delle ore che ci sono (sempre scritta).
- I SENSORI NON SI SOMMANO TRA LORO.

Output:
- data/processed/flusso_5t_sensori.json
- docs/rapporti/RAPPORTO_FLUSSO_5T_SENSORI.txt

Con --prova si stampa a console il blocco dei primi 5 sensori (per codice) e NON
si scrive nessun file.

Solo libreria standard.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402

RADICE = Path(__file__).resolve().parents[1]
IN = RADICE / "data" / "processed" / "velocita_5t.json"
ESCLUSI = RADICE / "data" / "processed" / "sensori_esclusi.json"
OUT = RADICE / "data" / "processed" / "flusso_5t_sensori.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_FLUSSO_5T_SENSORI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

ORE = 24
NOME_TIPO = {0: "feriale", 1: "sabato", 2: "domenica"}
LIMITE_ALTO = 6000        # controllo di plausibilita' sui singoli valori orari
PROVA_SENSORI = 5         # quanti sensori stampa --prova
DIURNO = list(range(6, 22))   # ore locali 6-21: 16 ore
PUNTA_AM = list(range(7, 10))  # ore locali 7-9
PUNTA_PM = list(range(16, 20))  # ore locali 16-19
DECIMALI_QUOTA = 4        # arrotondamento dichiarato di quota_diurna

RIGHE = []


def scrivi(msg=""):
    RIGHE.append(str(msg))


def leggi_esclusi():
    """lcd1 -> motivo ("morto" / "bloccato" / "pochi dati")."""
    if not ESCLUSI.is_file():
        raise SystemExit(f"Elenco esclusi non trovato: {ESCLUSI} (prima lo script 35)")
    dati = json.loads(ESCLUSI.read_text(encoding="utf-8"))
    if isinstance(dati, dict):
        dati = dati.get("sensori", [])
    return {str(e["lcd1"]): e["motivo"] for e in dati}


def blocco_tipi(sensore, mediana_quota):
    """Costruisce il dizionario 'tipo' di UN sensore, solo per i tipi di giorno
    che hanno almeno una cella ok. mediana_quota = mediana di quota_diurna
    (serve per totale_giorno_stimato)."""
    tipi = {}
    for t, celle in sensore["celle"].items():
        ok = {int(ora): c for ora, c in celle.items() if c.get("ok")}
        if not ok:
            continue
        f_ora = [None] * ORE
        for ora, c in ok.items():
            f_ora[ora] = c["f"]
        n_ore_ok = sum(1 for x in f_ora if x is not None)
        parziale = sum(x for x in f_ora if x is not None)
        totale = parziale if n_ore_ok == ORE else None
        f_punta = ora_punta = None
        for h, x in enumerate(f_ora):
            if x is not None and (f_punta is None or x > f_punta):
                f_punta, ora_punta = x, h

        # --- misure diurne ---
        orari_diurni = [f_ora[h] for h in DIURNO]
        n_ore_diurne_ok = sum(1 for x in orari_diurni if x is not None)
        f_diurno = sum(orari_diurni) if n_ore_diurne_ok == len(DIURNO) else None

        def massimo_finestra(ore):
            vals = [f_ora[h] for h in ore if f_ora[h] is not None]
            return max(vals) if vals else None

        quota = None
        if f_diurno is not None and totale:
            quota = round(f_diurno / totale, DECIMALI_QUOTA)

        # stima del totale sulle 24 ore: diurno / quota diurna mediana
        stima = None
        if f_diurno is not None and mediana_quota:
            stima = {"valore": round(f_diurno / mediana_quota),
                     "stimato": True,
                     "stimato_da": "f_diurno / mediana(quota_diurna)"}

        tipi[int(t)] = dict(
            f_ora=f_ora, n_ore_ok=n_ore_ok, totale_giorno=totale,
            totale_parziale=parziale, f_punta=f_punta, ora_punta=ora_punta,
            n_ore_diurne_ok=n_ore_diurne_ok, f_diurno=f_diurno,
            f_punta_am=massimo_finestra(PUNTA_AM),
            f_punta_pm=massimo_finestra(PUNTA_PM),
            quota_diurna=quota,
            totale_giorno_stimato=stima)
    return tipi


def main():
    ap = argparse.ArgumentParser(
        description="Flusso tipico 5T per sensore, ora e tipo di giorno (v2)")
    ap.add_argument("--prova", action="store_true",
                    help=f"stampa a console solo i primi {PROVA_SENSORI} sensori "
                         "senza scrivere i file di output")
    args = ap.parse_args()

    if not IN.is_file():
        raise SystemExit(f"File di partenza non trovato: {IN}")
    dati = json.loads(IN.read_text(encoding="utf-8"))
    comuni.controlla_periodo(dati.get("periodo"), "sensori")      # periodo fisso (L9)
    esclusi = leggi_esclusi()

    # --- prima passata: blocchi dei sensori non esclusi, per ricavare la mediana ---
    parziali = {}
    for lcd1, s in sorted(dati["sensori"].items(), key=lambda kv: str(kv[0])):
        if str(lcd1) in esclusi:
            continue
        parziali[str(lcd1)] = (s, blocco_tipi(s, None))

    quote = [b["quota_diurna"] for _, tipi in parziali.values()
             for b in tipi.values() if b["quota_diurna"] is not None]
    mediana_quota = statistics.median(quote) if quote else None
    n_quote = len(quote)

    # --- seconda passata: valori definitivi (con la stima) ---
    sensori = {}
    for lcd1, s in sorted(dati["sensori"].items(), key=lambda kv: str(kv[0])):
        k = str(lcd1)
        if k in esclusi:
            sensori[k] = dict(lcd1=s.get("lcd1", lcd1), via=s["via"], dir=s["dir"],
                              lat=s["lat"], lon=s["lon"], urbano=s["urbano"],
                              escluso=esclusi[k])
            continue
        sensori[k] = dict(lcd1=s.get("lcd1", lcd1), via=s["via"], dir=s["dir"],
                          lat=s["lat"], lon=s["lon"], urbano=s["urbano"],
                          tipo=blocco_tipi(s, mediana_quota))

    valore = {k: v for k, v in sensori.items() if "escluso" not in v}

    # --- controlli ---
    con_f_diurno = [k for k, s in valore.items()
                    if any(b["f_diurno"] is not None for b in s["tipo"].values())]
    con_quota = [k for k, s in valore.items()
                 if any(b["quota_diurna"] is not None for b in s["tipo"].values())]
    con_stima = [k for k, s in valore.items()
                 if any(b["totale_giorno_stimato"] is not None for b in s["tipo"].values())]
    negativi, alti, massimo = [], [], None
    for k, s in valore.items():
        for t, b in s["tipo"].items():
            for h, x in enumerate(b["f_ora"]):
                if x is None:
                    continue
                if x < 0:
                    negativi.append((k, t, h, x))
                if x > LIMITE_ALTO:
                    alti.append((k, t, h, x))
                if massimo is None or x > massimo:
                    massimo = x

    if not args.prova:
        payload = {
            "generato_partendo_da": dati.get("generato"),
            "fonte": [
                "data/processed/velocita_5t.json (flusso tipico, sensori 5T)",
                "data/processed/sensori_esclusi.json (sensori da non usare)",
            ],
            "tag": "MISURATO; i campi totale_giorno_stimato sono",
            "nota": "I sensori NON si sommano tra loro: ogni valore vale per quel sensore, in quel punto.",
            "periodo": dati.get("periodo"),
            "sensori": sensori,
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                       encoding="utf-8")
    else:
        chiavi = sorted(valore)[:PROVA_SENSORI]
        print(f"--prova: solo i primi {len(chiavi)} sensori non esclusi per codice, "
              "nessun file scritto.")
        print(json.dumps({k: valore[k] for k in chiavi}, ensure_ascii=False, indent=1))
        return 0

    # ---------- rapporto ----------
    scrivi("FLUSSO 5T PER SENSORE, ORA E TIPO DI GIORNO  (v2)")
    scrivi("=" * 78)
    scrivi(f"letto da: {IN}")
    scrivi(f"sensori esclusi da: {ESCLUSI}")
    scrivi(f"periodo dei dati: {dati.get('periodo', {}).get('da')} -> "
           f"{dati.get('periodo', {}).get('a')} (giorni locali)")
    scrivi("I sensori NON si sommano tra loro: ogni numero vale per quel sensore.")
    scrivi("Misure diurne: ore locali 6-21 (16 ore). f_diurno solo se tutte e 16 sono ok.")
    scrivi("totale_giorno solo con tutte e 24 le ore ok; le ore mancanti non si interpolano;")
    scrivi("l'ora 1 locale non viene riempita (in quell'ora il sistema non da' dati affidabili).")

    scrivi("")
    scrivi("(1) Copertura")
    scrivi(f"  sensori in tutto nel file: {len(sensori)}")
    scrivi(f"  esclusi (nessun valore, campo 'escluso'): {len(esclusi)}   [attesi 17]")
    scrivi(f"  sensori usabili (con valori): {len(valore)}   [attesi 92]")
    scrivi(f"  sensori con f_diurno: {len(con_f_diurno)}   [atteso: la maggior parte dei 92]")
    scrivi(f"  sensori con quota_diurna: {len(con_quota)}")
    scrivi(f"  sensori con totale_giorno_stimato: {len(con_stima)}")
    scrivi("  motivo per cui manca il totale giornaliero a molti: serve che TUTTE e 24 le ore siano ok.")

    scrivi("")
    scrivi("(2) Quota diurna (f_diurno / totale_giorno) sui sensori con totale_giorno")
    if quote:
        scrivi(f"  sensori (x tipo di giorno): {n_quote}")
        scrivi(f"  mediana: {mediana_quota:.4f}   minimo: {min(quote):.4f}   massimo: {max(quote):.4f}")
        scrivi(f"  mediana usata per il totale_giorno_stimato: {mediana_quota:.4f}")
    else:
        scrivi("  nessun sensore con tutte e 24 le ore ok: stima non possibile")

    # 15 sensori urbani con piu' veicoli/giorno
    def veicoli_giorno(k):
        b = valore[k]["tipo"].get(0)
        if not b:
            return 0
        return b["totale_giorno"] if b["totale_giorno"] is not None else b["totale_parziale"]

    urbani = sorted([k for k, s in valore.items() if s["urbano"]],
                    key=lambda k: (-veicoli_giorno(k), k))
    scrivi("")
    scrivi("(3) I 15 sensori urbani con piu' veicoli/giorno (feriale)")
    scrivi("    tot = giornaliero misurato; * = solo parziale; stim = stima 24 h (diurno/quota mediana)")
    scrivi(f"  {'lcd1':>6}  {'via':30s} {'dir':9s} {'tot':>7} {'punta':>5} {'f_diurno':>8} "
           f"{'punta am':>8} {'punta pm':>8} {'stim':>7}  note")
    for k in urbani[:15]:
        s = valore[k]
        b = s["tipo"].get(0, {})
        tg = b.get("totale_giorno")
        nota = ""
        if tg is not None:
            tg_txt = f"{tg}"
        elif b.get("totale_parziale") is not None:
            tg_txt = f"{b['totale_parziale']}"
            nota = f"* parziale su {b.get('n_ore_ok', 0)} ore ok"
        else:
            tg_txt, nota = "-", "nessuna ora ok"
        fd = b.get("f_diurno")
        st = b.get("totale_giorno_stimato") or {}
        def num(x):
            return "-" if x is None else f"{x}"
        scrivi(f"  {k:>6}  {s['via'][:30]:30s} {s['dir'][:9]:9s} {tg_txt:>7} "
               f"{num(b.get('ora_punta')):>5} {num(fd):>8} {num(b.get('f_punta_am')):>8} "
               f"{num(b.get('f_punta_pm')):>8} {num(st.get('valore')):>7}  {nota}")

    # profilo orario completo dei primi 3
    scrivi("")
    scrivi("(4) Profilo orario completo (feriale) dei primi 3 sensori urbani della lista sopra")
    for k in urbani[:3]:
        s = valore[k]
        b = s["tipo"].get(0, {})
        scrivi(f"  {k}  {s['via']} ({s['dir']})  totale_giorno={b.get('totale_giorno')} "
               f"f_diurno={b.get('f_diurno')} ore_ok={b.get('n_ore_ok')} "
               f"ore_diurne_ok={b.get('n_ore_diurne_ok')} quota_diurna={b.get('quota_diurna')}")
        scrivi("    ora   " + " ".join(f"{h:>5}" for h in range(ORE)))
        scrivi("    veic/h" + " ".join(
            ("    -" if x is None else f"{x:>5}") for x in b.get("f_ora", [None] * ORE)))

    # sensori esclusi
    scrivi("")
    scrivi(f"(5) Sensori esclusi ({len(esclusi)}), senza nessun valore")
    for k in sorted(esclusi, key=lambda k: (esclusi[k], k)):
        s = sensori[k]
        scrivi(f"      {k:>6}  {s['via'][:34]:34s} {s['dir'][:9]:9s} "
               f"{'urbano' if s['urbano'] else 'fuori citta':11s} escluso: {esclusi[k]}")

    scrivi("")
    scrivi("(6) Controlli sui valori orari (solo sensori usabili)")
    n_vals = sum(1 for s in valore.values() for b in s["tipo"].values()
                 for x in b["f_ora"] if x is not None)
    scrivi(f"  valori orari scritti: {n_vals}")
    scrivi(f"  valori negativi: {len(negativi)}" +
           ("" if not negativi else " -> " + ", ".join(str(x) for x in negativi[:10])))
    scrivi(f"  valori oltre {LIMITE_ALTO} veic/h: {len(alti)}" +
           ("" if not alti else " -> " + ", ".join(str(x) for x in alti[:10])))
    scrivi(f"  valore massimo trovato: {massimo}   [atteso circa 3202]")

    testo = "\n".join(RIGHE)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.write(testo + "\n")
    RAPPORTO.write_text(testo + "\n", encoding="utf-8")
    print(f"\nRapporto salvato: {RAPPORTO}")
    print(f"JSON salvato: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
