# -*- coding: utf-8 -*-
"""
scripts/17_taglia_osm.py - Estrae dall'OSM grezzo la zona Torino + cintura

Il file Geofabrik "Nord-Ovest" (564 MB, include Lombardia e Liguria) e' troppo
grande per costruire il grafo OpenTripPlanner su un PC con 8 GB di RAM.
Questo script produce un .pbf piccolo (solo Torino entro ~18 km + margine).

Come funziona (due passate con pyosmium, libreria standard di Python no):
  1) prima passata: salva in un indice le posizioni SOLO dei nodi dentro il
     riquadro; se un way (strada) passa dentro il riquadro, lo segna e tiene
     tutti i suoi nodi (anche fuori riquadro, per non troncare le strade);
  2) seconda passata: riscrive solo nodi e way trovati. Le relazioni NON
     vengono copiate (multiparchi e relazioni itinerario mancano nel taglio:
     per i percorsi a piedi servono strade, non relazioni).

Usage:
    python 17_taglia_osm.py [pbf_ingresso] [pbf_uscita]

Default:
    ingresso: data/raw/nord-ovest-261008.osm.pbf
    uscita:   data/otp/rete/torino_cintura.osm.pbf
"""

import sys
from pathlib import Path

import osmium

# Riquadro: Torino centro (45.0716, 7.6869) piu' 18 km, con margine.
# Ordine: lon_min, lat_min, lon_max, lat_max
LON_MIN, LAT_MIN, LON_MAX, LAT_MAX = 7.45, 44.90, 7.93, 45.24


def dentro(loc):
    return loc is not None and loc.valid() and LON_MIN <= loc.lon <= LON_MAX and LAT_MIN <= loc.lat <= LAT_MAX


def main():
    radice = Path(__file__).resolve().parent.parent
    ingresso = Path(sys.argv[1]) if len(sys.argv) > 1 else radice / "data/raw/nord-ovest-261008.osm.pbf"
    uscita = Path(sys.argv[2]) if len(sys.argv) > 2 else radice / "data/otp/rete/torino_cintura.osm.pbf"

    if not ingresso.is_file():
        sys.exit(f"File di ingresso non trovato: {ingresso}")
    uscita.parent.mkdir(parents=True, exist_ok=True)

    # Indice delle posizioni (solo nodi nel riquadro: poca RAM)
    # pyosmium 4.x: osmium.index.create_map("flex_mem")
    indice = osmium.index.create_map("flex_mem")
    nodi_serviti = set()   # id dei nodi da riscrivere (riquadro + nodi dei way presi)
    way_presi = set()      # id dei way da riscrivere
    contatori = {"node": 0, "way": 0}

    class Trova(osmium.SimpleHandler):
        def node(self, n):
            contatori["node"] += 1
            if contatori["node"] % 10_000_000 == 0:
                print(f"  passata 1: {contatori['node']:,} nodi visti", flush=True)
            if dentro(n.location):
                indice.set(n.id, n.location)
                nodi_serviti.add(n.id)

        def way(self, w):
            contatori["way"] += 1
            refs = [nr.ref for nr in w.nodes]
            presa = False
            for r in refs:
                try:
                    loc = indice.get(r)
                except KeyError:
                    continue
                if dentro(loc):
                    presa = True
                    break
            if presa:
                way_presi.add(w.id)
                nodi_serviti.update(refs)

    print(f"Passata 1 su {ingresso.name} ...", flush=True)
    Trova().apply_file(str(ingresso))
    print(f"  passata 1 finita: {len(nodi_serviti):,} nodi, {len(way_presi):,} way", flush=True)

    if not way_presi:
        sys.exit("Nessun way nel riquadro: controllare le coordinate del riquadro.")

    class Scrivi(osmium.SimpleHandler):
        def __init__(self):
            self.writer = osmium.SimpleWriter(str(uscita))

        def node(self, n):
            if n.id in nodi_serviti:
                self.writer.add_node(n)

        def way(self, w):
            if w.id in way_presi:
                self.writer.add_way(w)

    print(f"Passata 2: scrittura di {uscita} ...", flush=True)
    Scrivi().apply_file(str(ingresso))
    mega = uscita.stat().st_size / (1024 * 1024)
    print(f"Fatto: {uscita} ({mega:.1f} MB)")
    print(f"  nodi scritti: {len(nodi_serviti):,}")
    print(f"  way scritti:  {len(way_presi):,}")
    print("  relazioni non copiate (scelta dichiarata, vedi intestazione).")


if __name__ == "__main__":
    main()
