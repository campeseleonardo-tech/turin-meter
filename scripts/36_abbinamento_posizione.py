#!/usr/bin/env python3
"""36_abbinamento_posizione.py

Abbina i 92 sensori 5T usabili a un corridoio stradale di
data/processed/importanza_vie.json, usando la POSIZIONE, non solo il nome.
Vedi sviluppo/note_tecniche/R8_traffico.md.

Per ogni sensore usabile (non in data/processed/sensori_esclusi.json):
- i 3 corridoi piu' vicini entro 60 m (nome, punteggio, distanza, se hanno lo
  stesso nome della via del sensore);
- classe:
  * SICURO   = esiste un corridoio con lo STESSO nome entro 60 m (la regola di
               prima, script 24/34);
  * DA_VEDERE= nessun corridoio con lo stesso nome, ma un corridoio con un nome
               DIVERSO entro 40 m: da far vedere a Claude per la conferma;
  * NESSUNO  = niente entro quelle distanze.

In piu': le coppie di versi (due sensori con lo stesso nome normalizzato, segno
opposto, a non piu' di 200 m fra loro: si potranno sommare, decisione 5 del piano)
e quali sensori restano senza compagno.

Le funzioni `normalizza` e `haversine_m` sono le stesse dello script 24 (caricate
con importlib: il nome del file inizia con un numero).

Output:
- data/processed/sensori_corridoi_v2.json
- docs/rapporti/RAPPORTO_ABBINAMENTO_POSIZIONE.txt  (contiene la tabella DA_VEDERE completa)

Solo libreria standard. Database in sola lettura (qui non serve nemmeno).
"""

import importlib.util
import json
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
IN_SENSORI = RADICE / "data" / "processed" / "flusso_5t_sensori.json"
IN_ESCLUSI = RADICE / "data" / "processed" / "sensori_esclusi.json"
IN_CORRIDOI = RADICE / "data" / "processed" / "importanza_vie.json"
OUT = RADICE / "data" / "processed" / "sensori_corridoi_v2.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_ABBINAMENTO_POSIZIONE.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

SOGLIA_NOME_M = 60      # SICURO: stesso nome entro questa distanza
SOGLIA_VEDERE_M = 40    # DA_VEDERE: nome diverso entro questa distanza
SOGLIA_VERSI_M = 200    # coppie di versi
PASSO_GRIGLIA = 0.001   # griglia per non confrontare ogni sensore con 10.743 corridoi
QUANTI_VICINI = 3       # quanti corridoi elencare per sensore

RIGHE = []


def scrivi(msg=""):
    RIGHE.append(str(msg))


def carica_script_24():
    percorso = RADICE / "scripts" / "24_importanza_vie.py"
    if not percorso.is_file():
        raise SystemExit(f"Script 24 non trovato: {percorso}")
    spec = importlib.util.spec_from_file_location("m24_importanza_vie", percorso)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def chiave_griglia(lat, lon):
    return (int(lat // PASSO_GRIGLIA), int(lon // PASSO_GRIGLIA))


def main():
    m24 = carica_script_24()

    for p in (IN_SENSORI, IN_ESCLUSI, IN_CORRIDOI):
        if not p.is_file():
            raise SystemExit(f"File non trovato: {p}")
    dati = json.loads(IN_SENSORI.read_text(encoding="utf-8"))["sensori"]
    esclusi_raw = json.loads(IN_ESCLUSI.read_text(encoding="utf-8"))
    if isinstance(esclusi_raw, dict):
        esclusi_raw = esclusi_raw.get("sensori", [])
    esclusi = {str(e["lcd1"]): e["motivo"] for e in esclusi_raw}
    corridoi = json.loads(IN_CORRIDOI.read_text(encoding="utf-8"))["corridoi"]

    sensori = {str(k): s for k, s in dati.items() if "escluso" not in s}

    # --- griglia dei punti dei corridoi: cella -> [(indice corridoio, lat, lon)] ---
    griglia = {}
    for i, c in enumerate(corridoi):
        for tratto in c["geometria"]:
            for punto in tratto:
                griglia.setdefault(chiave_griglia(punto[0], punto[1]), []).append(
                    (i, punto[0], punto[1]))

    def corridoi_vicini(lat, lon, limite_m):
        """[(indice, distanza)] dei corridoi con un punto entro limite_m."""
        ci, cj = chiave_griglia(lat, lon)
        migliori = {}
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for idx, pla, plo in griglia.get((ci + di, cj + dj), ()):
                    d = m24.haversine_m(lat, lon, pla, plo)
                    if d <= limite_m and (idx not in migliori or d < migliori[idx]):
                        migliori[idx] = d
        return sorted(migliori.items(), key=lambda kv: kv[1])

    risultato = {}
    classi = {"SICURO": 0, "DA_VEDERE": 0, "NESSUNO": 0}
    for lcd1, s in sorted(sensori.items(), key=lambda kv: str(kv[0])):
        chiave = m24.normalizza(s["via"])
        vicini = corridoi_vicini(s["lat"], s["lon"], SOGLIA_NOME_M)
        elenco = [dict(nome=corridoi[i]["nome"], punteggio=corridoi[i]["punteggio"],
                       lunghezza_km=corridoi[i]["lunghezza_km"],
                       distanza_m=round(d, 1),
                       stesso_nome=corridoi[i]["chiave_normalizzata"] == chiave)
                  for i, d in vicini]

        scelto = None
        classe = "NESSUNO"
        for e in elenco:                       # SICURO: stesso nome entro 60 m
            if e["stesso_nome"]:
                scelto, classe = e, "SICURO"
                break
        if classe == "NESSUNO":                # DA_VEDERE: nome diverso entro 40 m
            for e in elenco:
                if e["distanza_m"] <= SOGLIA_VEDERE_M:
                    scelto, classe = e, "DA_VEDERE"
                    break
        classi[classe] += 1
        risultato[lcd1] = dict(lcd1=lcd1, via=s["via"], dir=s["dir"],
                               lat=s["lat"], lon=s["lon"], urbano=s["urbano"],
                               chiave_normalizzata=chiave, classe=classe,
                               corridoio=scelto,
                               corridoi_vicini=elenco[:QUANTI_VICINI])

    # --- coppie di versi (stesso nome, segno opposto, <= 200 m) ---
    per_nome = {}
    for k, s in risultato.items():
        per_nome.setdefault(s["chiave_normalizzata"], []).append(k)
    coppie = []
    for nome, lista in per_nome.items():
        for i in range(len(lista)):
            for j in range(i + 1, len(lista)):
                a, b = risultato[lista[i]], risultato[lista[j]]
                if a["dir"] == b["dir"]:
                    continue
                d = m24.haversine_m(a["lat"], a["lon"], b["lat"], b["lon"])
                if d <= SOGLIA_VERSI_M:
                    coppie.append(dict(lcd1_a=a["lcd1"], lcd1_b=b["lcd1"],
                                       via=a["via"], distanza_m=round(d, 1)))
    in_coppia = {c["lcd1_a"] for c in coppie} | {c["lcd1_b"] for c in coppie}
    senza_compagno = sorted(k for k in risultato if k not in in_coppia)

    payload = {
        "fonte": {"sensori": "data/processed/flusso_5t_sensori.json",
                  "esclusi": "data/processed/sensori_esclusi.json",
                  "corridoi": "data/processed/importanza_vie.json"},
        "regole": {"SICURO": f"stesso nome, <= {SOGLIA_NOME_M} m",
                   "DA_VEDERE": f"nome diverso, <= {SOGLIA_VEDERE_M} m",
                   "NESSUNO": "niente entro le soglie",
                   "coppie_versi": f"stesso nome, segno opposto, <= {SOGLIA_VERSI_M} m"},
        "tag": "MISURATO (posizione) - nessun flusso assegnato o stimato qui",
        "conteggi": dict(classi, sensori_usabili=len(risultato), esclusi=len(esclusi)),
        "sensori": risultato,
        "coppie_versi": coppie,
        "senza_compagno": senza_compagno,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")

    # ---------- rapporto ----------
    sicuri = [k for k, s in risultato.items() if s["classe"] == "SICURO"]
    da_vedere = [k for k, s in risultato.items() if s["classe"] == "DA_VEDERE"]
    nessuno = [k for k, s in risultato.items() if s["classe"] == "NESSUNO"]

    scrivi("ABBINAMENTO SENSORI 5T -> CORRIDOI, PER POSIZIONE")
    scrivi("=" * 88)
    scrivi(f"sensori usabili (non esclusi): {len(risultato)}   [atteso 92]")
    scrivi("funzioni normalizza/haversine_m: prese dallo script 24 (stessa regola di distanza)")
    scrivi("")
    scrivi("(1) Classi")
    scrivi(f"  SICURO    (stesso nome, <= {SOGLIA_NOME_M} m): {classi['SICURO']}   [atteso circa 14-15]")
    scrivi(f"  DA_VEDERE (nome diverso, <= {SOGLIA_VEDERE_M} m): {classi['DA_VEDERE']}")
    scrivi(f"  NESSUNO: {classi['NESSUNO']}")
    scrivi(f"  totale: {sum(classi.values())}   [deve essere 92: "
           f"{'OK' if sum(classi.values()) == 92 else 'NON TORNA'}]")

    scrivi("")
    scrivi("(2) SICURO - abbinamento confermato dalla regola di prima")
    scrivi(f"  {'lcd1':>6}  {'via':30s} {'dir':9s} {'corridoio':30s} {'p':>2} {'km':>6} {'dist_m':>7}")
    for k in sorted(sicuri, key=lambda k: -risultato[k]["corridoio"]["punteggio"]):
        s = risultato[k]
        c = s["corridoio"]
        scrivi(f"  {k:>6}  {s['via'][:30]:30s} {s['dir'][:9]:9s} {c['nome'][:30]:30s} "
               f"{c['punteggio']:>2} {c['lunghezza_km']:>6.1f} {c['distanza_m']:>7.1f}")

    scrivi("")
    scrivi(f"(3) DA_VEDERE - TABELLA COMPLETA DA FAR VEDERE A CLAUDE ({len(da_vedere)} sensori)")
    scrivi("    'corridoio proposto' = corridoio piu' vicino con nome diverso (<= 40 m)")
    scrivi("    'vicini' = fino a 3 corridoi entro 60 m, con la distanza")
    scrivi(f"  {'lcd1':>6}  {'via':32s} {'dir':9s} {'corridoio proposto':32s} {'p':>2} "
           f"{'dist_m':>7}  vicini (nome, dist_m)")
    for k in sorted(da_vedere, key=lambda k: risultato[k]["corridoio"]["distanza_m"]):
        s = risultato[k]
        c = s["corridoio"]
        vic = "; ".join(f"{v['nome'][:26]} {v['distanza_m']:.0f}" for v in s["corridoi_vicini"])
        scrivi(f"  {k:>6}  {s['via'][:32]:32s} {s['dir'][:9]:9s} {c['nome'][:32]:32s} "
               f"{c['punteggio']:>2} {c['distanza_m']:>7.1f}  {vic}")

    scrivi("")
    scrivi(f"(4) NESSUNO - sensori senza corridoio entro le soglie: {len(nessuno)}")
    for k in sorted(nessuno):
        s = risultato[k]
        vic = "; ".join(f"{v['nome'][:26]} {v['distanza_m']:.0f}" for v in s["corridoi_vicini"]) \
            or "nessun corridoio entro 60 m"
        scrivi(f"      {k:>6}  {s['via'][:32]:32s} {s['dir'][:9]:9s} "
               f"{'urbano' if s['urbano'] else 'fuori citta':11s} {vic}")

    scrivi("")
    scrivi(f"(5) Coppie di versi (stesso nome, segno opposto, <= {SOGLIA_VERSI_M} m): {len(coppie)}")
    for c in sorted(coppie, key=lambda c: c["via"]):
        scrivi(f"      {c['via'][:36]:36s} {c['lcd1_a']:>6} + {c['lcd1_b']:>6}  "
               f"{c['distanza_m']:>6.1f} m")
    scrivi("")
    scrivi(f"(6) Sensori usabili senza compagno di verso ({len(senza_compagno)} su {len(risultato)}):")
    riga = []
    for k in senza_compagno:
        riga.append(k)
        if len(riga) == 12:
            scrivi("      " + " ".join(riga))
            riga = []
    if riga:
        scrivi("      " + " ".join(riga))

    testo = "\n".join(RIGHE)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.write(testo + "\n")
    RAPPORTO.write_text(testo + "\n", encoding="utf-8")
    print(f"\nRapporto salvato: {RAPPORTO}")
    print(f"JSON salvato: {OUT}")
    print(f"CONTROLLI: SICURO {classi['SICURO']} (atteso circa 14-15), "
          f"totale classi {sum(classi.values())} (atteso 92)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
