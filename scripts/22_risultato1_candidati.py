# -*- coding: utf-8 -*-
"""
scripts/22_risultato1_candidati.py - Risultato 1, fase B: dove aggiungere un servizio

Richiede un calcolo R5 NUOVO ma piccolo (non il giro di 6-7 ore di 18): le
destinazioni sono solo i punti candidati (poche decine), non tutto il catalogo.

Procedura (decisa con Leo il 12/10):
  1. Prende le sezioni di TORINO a "zero" per il gruppo scelto (da
     data/processed/accessibilita.json, ricalcolato qui per non dipendere da
     un file intermedio che potrebbe essere vecchio).
  2. Le raggruppa in celle di --cluster-metri (default 400 m): un candidato
     per cella, posizionato sul centroide pesato per residenti delle sezioni
     della cella. E' una ZONA indicativa, non un indirizzo preciso.
  3. Un solo giro R5: origini = tutte le sezioni di Torino con residenti,
     destinazioni = i candidati di tutti i gruppi scelti insieme (un giro,
     non uno per gruppo), stesso cutoff/velocita' del giro 18 (15 min, 4,8 km/h).
  4. Per ogni candidato: residenti "guadagnati" = residenti delle sezioni
     ORA A ZERO per quel gruppo che rientrerebbero nel cutoff dal candidato.
  5. Selezione greedy SENZA sovrapposizioni: si scelgono i candidati in ordine
     di guadagno, togliendo ogni volta le sezioni gia' coperte, cosi' i
     candidati finali non contano due volte gli stessi residenti.

Solo sezioni ABITATE (decisione di Leo, 20/10/2026): le sezioni a zero con densita' sotto --soglia-densita
(default SOGLIA_POCO_ABITATA di 21_risultato1_vuoti.py, 1.000 ab/km2) non generano candidati e non contano nei
residenti "a zero"; il rapporto scrive quanti candidati e quante sezioni cambiano rispetto a prima.

Ambito: SOLO Torino (deciso il 12/10: il catalogo comunale non esiste in
cintura, quindi candidati lì userebbero solo OSM, poco affidabile).

Uscite:
  data/processed/risultato1_candidati.json
  docs/rapporti/RAPPORTO_RISULTATO1_CANDIDATI.txt

Usage:
    python 22_risultato1_candidati.py --gruppi scuole,salute,cibo,fermate,verde [--cluster-metri 400] [--max-candidati 5] [--soglia-densita 1000]
"""

import argparse
import datetime as dt
import importlib.util
import json
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
ACCESS = RADICE / "data/processed/accessibilita.json"
OUT = RADICE / "data/processed/risultato1_candidati.json"
RAPPORTO = RADICE / "docs/rapporti/RAPPORTO_RISULTATO1_CANDIDATI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
COMUNE_TORINO_PREFIX = "1272"

# Riusa le funzioni del motore R5 gia' scritte e provate in 18_accessibilita.py
# (il nome del file inizia con una cifra: non si puo' fare "import 18_...",
# si carica dal percorso).
_spec = importlib.util.spec_from_file_location(
    "acc18", Path(__file__).resolve().parent / "18_accessibilita.py")
acc18 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(acc18)

# densita' e soglia "poco abitata": stesse funzioni e costante dello script 21 (un solo posto dove cambiarle)
_spec21 = importlib.util.spec_from_file_location(
    "vuoti21", Path(__file__).resolve().parent / "21_risultato1_vuoti.py")
vuoti21 = importlib.util.module_from_spec(_spec21)
_spec21.loader.exec_module(vuoti21)


def e_torino(sid):
    return str(sid).startswith(COMUNE_TORINO_PREFIX)


def clusterizza(sezioni_zero, metri):
    """Raggruppa le sezioni a zero in celle di ~metri; un candidato per cella
    sul centroide pesato per residenti. Ritorna [{lat, lon, sezioni:[id,...], res_cluster}]."""
    cella = metri / 111000.0
    celle = {}
    for s in sezioni_zero:
        k = (round(s["lat"] / cella), round(s["lon"] / cella))
        celle.setdefault(k, []).append(s)
    candidati = []
    for secs in celle.values():
        rtot = sum(s["res"] for s in secs)
        lat = sum(s["lat"] * s["res"] for s in secs) / rtot
        lon = sum(s["lon"] * s["res"] for s in secs) / rtot
        candidati.append({"lat": lat, "lon": lon,
                           "sezioni": [s["id"] for s in secs], "res_cluster": rtot})
    return candidati


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gruppi", default="scuole,salute,cibo,fermate,verde",
                     help="gruppi separati da virgola (scuole,salute,cibo,fermate,verde)")
    ap.add_argument("--cluster-metri", type=float, default=400.0)
    ap.add_argument("--max-candidati", type=int, default=5,
                     help="candidati finali proposti per gruppo (selezione greedy)")
    ap.add_argument("--soglia-densita", type=float, default=vuoti21.SOGLIA_POCO_ABITATA,
                     help="ab/km2: le sezioni sotto questa densita' non generano candidati (default: soglia di 21)")
    ap.add_argument("--guadagno-minimo", type=int, default=20,
                     help="scarta un candidato che guadagna meno di tanti residenti")
    args = ap.parse_args()
    gruppi = [g.strip() for g in args.gruppi.split(",") if g.strip()]

    access = json.loads(ACCESS.read_text(encoding="utf-8"))
    taglio = access["parametri"]["cutoff_piedi_min"]
    vel_mmin = access["parametri"]["velocita_piedi"]
    torino = [s for s in access["sezioni"] if e_torino(s["id"]) and s["res"] > 0]
    print(f"Sezioni di Torino con residenti: {len(torino)}")
    superfici = vuoti21.carica_superfici()

    def abitata(s):
        """Densita' >= soglia; senza superficie conta come abitata (come in 21)."""
        d = vuoti21.densita(s, superfici)
        return d is None or d >= args.soglia_densita

    def verificare(s):
        """Sezione "da verificare" (stessa regola dello script 21): non genera candidati."""
        return vuoti21.da_verificare(s) is not None

    def candidabile(s):
        return abitata(s) and not verificare(s)

    # ---- 1-2: sezioni a zero per gruppo + clustering in candidati
    candidati_per_gruppo = {}
    cambio_filtro = {}  # per gruppo: quanto cambia con il filtro "solo sezioni abitate"
    tutti_candidati = []  # (idx_globale, lat, lon, gruppo)
    for g in gruppi:
        zero_tutte = [s for s in torino if s["piedi"]["15"].get(g, 0) == 0]
        zero = [s for s in zero_tutte if candidabile(s)]
        n_verif = sum(1 for s in zero_tutte if abitata(s) and verificare(s))
        cand_prima = len(clusterizza(zero_tutte, args.cluster_metri)) if zero_tutte else 0
        cand = clusterizza(zero, args.cluster_metri) if zero else []
        candidati_per_gruppo[g] = cand
        cambio_filtro[g] = {"sezioni_zero_prima": len(zero_tutte), "sezioni_zero_abitate": len(zero),
                            "residenti_zero_prima": sum(s["res"] for s in zero_tutte),
                            "residenti_zero_abitate": sum(s["res"] for s in zero),
                            "candidati_prima": cand_prima, "candidati_dopo": len(cand),
                            "sezioni_da_verificare_tolte": n_verif}
        print(f"  {g}: {len(zero_tutte)} sezioni a zero, {len(zero)} abitate -> {len(cand)} candidati "
              f"(prima del filtro {cand_prima}; celle di {args.cluster_metri:.0f} m)")
        for c in cand:
            tutti_candidati.append({"gruppo": g, "lat": c["lat"], "lon": c["lon"],
                                     "sezioni_cluster": c["sezioni"]})

    if not tutti_candidati:
        print("Nessun candidato da valutare (nessuna sezione a zero nei gruppi scelti).")
        return

    # ---- 3: UN giro R5, origini = tutta Torino, destinazioni = tutti i candidati
    rete, gpd = acc18.avvia_rete()
    orig_gdf = acc18.gdf_da_punti(gpd, [(s["lat"], s["lon"]) for s in torino], "S")
    orig_gdf["id"] = [s["id"] for s in torino]
    dest_gdf = acc18.gdf_da_punti(gpd, [(c["lat"], c["lon"]) for c in tutti_candidati], "C")

    import r5py
    vel_kmh = vel_mmin * 60.0 / 1000.0
    quando = dt.datetime.combine(dt.date.fromisoformat(access["parametri"]["giorno"]), dt.time(7, 0))
    t0 = time.time()
    m = acc18.matrice(rete, [r5py.r5.TransportMode.WALK], orig_gdf, dest_gdf, quando,
                       dt.timedelta(minutes=taglio), speed_walking=vel_kmh)
    print(f"Matrice R5 (origini Torino x {len(tutti_candidati)} candidati): "
          f"{time.time()-t0:.0f} s")

    # ---- 4: per ogni candidato, insieme delle sezioni raggiunte entro il cutoff
    res_sezione = {s["id"]: s["res"] for s in torino}
    raggiunte = {i: set() for i in range(len(tutti_candidati))}
    for r in m.itertuples(index=False):
        tempo = r.travel_time
        if hasattr(tempo, "total_seconds"):
            tempo = tempo.total_seconds() / 60.0
        if tempo is None or (isinstance(tempo, float) and tempo != tempo) or tempo > taglio:
            continue
        i = int(str(r.to_id).removeprefix("C"))
        oid = str(r.from_id)
        raggiunte[i].add(oid)

    # ---- 5: selezione greedy senza sovrapposizioni, per gruppo
    esito_gruppi = {}
    for g in gruppi:
        idx_g = [i for i, c in enumerate(tutti_candidati) if c["gruppo"] == g]
        zero_ids_g = {s["id"] for s in torino if s["piedi"]["15"].get(g, 0) == 0 and candidabile(s)}
        scoperte = set(zero_ids_g)
        scelti = []
        disponibili = set(idx_g)
        while disponibili and len(scelti) < args.max_candidati:
            def guadagno(i):
                return sum(res_sezione[oid] for oid in (raggiunte[i] & scoperte))
            migliore = max(disponibili, key=guadagno)
            g_val = guadagno(migliore)
            if g_val < args.guadagno_minimo:
                break
            coperte_ora = raggiunte[migliore] & scoperte
            scelti.append({
                "lat": round(tutti_candidati[migliore]["lat"], 5),
                "lon": round(tutti_candidati[migliore]["lon"], 5),
                "residenti_guadagnati": g_val,
                "sezioni_coperte": sorted(coperte_ora),
                "n_sezioni_coperte": len(coperte_ora),
            })
            scoperte -= coperte_ora
            disponibili.discard(migliore)
        esito_gruppi[g] = {
            "residenti_a_zero_totali": sum(res_sezione[oid] for oid in zero_ids_g),
            "candidati_valutati": len(idx_g),
            "candidati_scelti": scelti,
            "residenti_guadagnati_totali": sum(c["residenti_guadagnati"] for c in scelti),
            "residenti_restano_a_zero": sum(res_sezione[oid] for oid in scoperte),
            "filtro_abitate": cambio_filtro[g],
        }

    esito = {
        "generato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "fonte": "data/processed/accessibilita.json + nuovo giro R5 (solo candidati, Torino)",
        "parametri": {"cutoff_piedi_min": taglio, "velocita_piedi_kmh": vel_kmh,
                       "cluster_metri": args.cluster_metri, "max_candidati": args.max_candidati,
                       "guadagno_minimo": args.guadagno_minimo,
                       "soglia_densita_ab_km2": args.soglia_densita},
        "nota": ("Ogni candidato e' una ZONA indicativa (centroide pesato delle sezioni scoperte "
                 "vicine), non un indirizzo o un terreno verificato disponibile. "
                 "'Residenti guadagnati' conta solo chi oggi e' a zero per quel gruppo; "
                 "i candidati di uno stesso gruppo non si sovrappongono sugli stessi residenti. "
                 "ORARIO PROGRAMMATO. Non dice se il servizio basterebbe o verrebbe usato."),
        "gruppi": esito_gruppi,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(esito, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Scritto {OUT}")

    righe = ["RAPPORTO RISULTATO 1 - fase B: dove aggiungere un servizio (solo Torino, STIMATO)",
             f"generato: {esito['generato']}",
             f"cutoff a piedi: {taglio} min   velocita': {vel_kmh:.1f} km/h   "
             f"cluster: {args.cluster_metri:.0f} m   max candidati: {args.max_candidati}",
             ""]
    for g in gruppi:
        d = esito_gruppi[g]
        righe.append(f"{g}: {d['residenti_a_zero_totali']:,} residenti a zero, "
                     f"{d['candidati_valutati']} zone candidate valutate")
        for i, c in enumerate(d["candidati_scelti"], 1):
            righe.append(f"  candidato {i}: lat {c['lat']} lon {c['lon']}  "
                         f"guadagna {c['residenti_guadagnati']:,} residenti "
                         f"({c['n_sezioni_coperte']} sezioni)")
        righe.append(f"  TOTALE con questi {len(d['candidati_scelti'])} candidati: "
                     f"{d['residenti_guadagnati_totali']:,} residenti guadagnati, "
                     f"{d['residenti_restano_a_zero']:,} restano a zero")
        f_ = d["filtro_abitate"]
        righe.append(f"  solo sezioni abitate (>= {args.soglia_densita:,.0f} ab/km2): sezioni a zero "
                     f"{f_['sezioni_zero_prima']} -> {f_['sezioni_zero_abitate']}, residenti a zero "
                     f"{f_['residenti_zero_prima']:,} -> {f_['residenti_zero_abitate']:,}, zone candidate "
                     f"{f_['candidati_prima']} -> {f_['candidati_dopo']}; "
                     f"sezioni da verificare tolte: {f_['sezioni_da_verificare_tolte']}")
        righe.append("")
    righe.append("LIMITI: zone indicative (non indirizzi/terreni verificati); non dice se il "
                 "servizio basterebbe o verrebbe usato; ORARIO PROGRAMMATO; solo Torino.")
    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(righe), encoding="utf-8")
    print(f"Scritto {RAPPORTO}")


if __name__ == "__main__":
    main()
