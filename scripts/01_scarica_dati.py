#!/usr/bin/env python3
"""
01_scarica_dati.py  -  scarica i dati aperti di Torino nella cartella data/raw.

Usa SOLO la libreria standard di Python (nessuna installazione).
Si lancia dal PC: python 01_scarica_dati.py

Cosa scarica (tutte fonti aperte, licenza CC-BY / IODL):
  - GTT: orari programmati (GTFS)               -> gtt_gtfs.zip
  - GTT: tempo reale (posizioni, ritardi, avvisi) -> gtt_vehicle_position.pb, ...
  - 5T: flussi di traffico (91 sensori, 5 minuti) -> 5t_flussi_<data>.xml
  - Comune di Torino: zone statistiche (CSV + shapefile)

Cosa NON scarica (da fare a mano, vedi docs/en/METHODS.md):
  - ISTAT pendolarismo 2011 (sezioni di censimento) e basi territoriali 2021
    perche' non conosco l'indirizzo diretto dei file e non voglio indovinarlo.

Ogni file ha un esito stampato a schermo. Se un file fallisce, gli altri
continuano. Nulla viene cancellato o sovrascritto: i file esistenti restano
e il nuovo viene salvato con data e ora nel nome.
"""
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent

def trova_radice():
    """La cartella del progetto e' quella chiamata GTT, ovunque venga lanciato lo script."""
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    candidata = Path.home() / "Desktop" / "GTT"
    if candidata.is_dir():
        return candidata
    return AQUI.parent


RADICE = trova_radice()
RAW = RADICE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

UA = "GTT-progetto-personale/0.1 (studio personale)"

FONTI = [
    # (nome file, url, descrizione)
    ("gtt_gtfs.zip", "https://www.gtt.to.it/open_data/gtt_gtfs.zip",
     "GTT orari programmati (GTFS)"),
    ("gtt_vehicle_position.pb", "https://percorsieorari.gtt.to.it/das_gtfsrt/vehicle_position.aspx",
     "GTT posizioni dei mezzi (tempo reale)"),
    ("gtt_trip_update.pb", "https://percorsieorari.gtt.to.it/das_gtfsrt/trip_update.aspx",
     "GTT ritardi/aggiornamenti corse (tempo reale)"),
    ("gtt_alerts.pb", "https://percorsieorari.gtt.to.it/das_gtfsrt/alerts.aspx",
     "GTT avvisi di servizio (tempo reale)"),
    ("5t_flussi.xml", "https://opendata.5t.torino.it/get_fdt",
     "5T flussi di traffico (91 sensori, 5 minuti)"),
    ("zone_statistiche_csv.zip", "http://geoportale.comune.torino.it/geodati/zip/zone_statistiche_csv.zip",
     "Comune di Torino zone statistiche (CSV)"),
    ("zone_statistiche_geo.zip", "http://geoportale.comune.torino.it/geodati/zip/zone_statistiche_geo.zip",
     "Comune di Torino zone statistiche (shapefile)"),
]


def scarica(nome, url, descr):
    adesso = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base, _, ext = nome.rpartition(".")
    destinazione = RAW / f"{base}_{adesso}.{ext}"
    richiesta = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(richiesta, timeout=120) as r:
            dati = r.read()
            codice = r.status
    except urllib.error.HTTPError as e:
        print(f"  [ERRORE] {descr}: il server risponde {e.code} ({e.reason})")
        return False
    except Exception as e:  # rete assente, timeout, ecc.
        print(f"  [ERRORE] {descr}: {e}")
        return False
    destinazione.write_bytes(dati)
    print(f"  [OK] {descr}: {len(dati):,} byte -> {destinazione.name} (HTTP {codice})")
    return True


def main():
    print(f"Cartella del progetto: {RADICE}")
    print(f"Cartella di destinazione: {RAW}\n")
    esiti = []
    for nome, url, descr in FONTI:
        print(f"- {descr}")
        esiti.append((descr, scarica(nome, url, descr)))
        time.sleep(1)  # cortesia verso i server
    print("\nRiepilogo:")
    for descr, ok in esiti:
        print(f"  {'OK    ' if ok else 'FALLITO'}  {descr}")
    if not all(ok for _, ok in esiti):
        print("\nSe qualcosa e' fallito, copia il messaggio di errore e portalo nella chat.")
        sys.exit(1)


if __name__ == "__main__":
    main()
