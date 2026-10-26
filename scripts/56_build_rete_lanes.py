# -*- coding: utf-8 -*-
"""
scripts/56_build_rete_lanes.py - Pacchetto B (Fase 5), parte 1: ricostruisce la
rete stradale dal taglio OSM con i nuovi tag (lanes, oneway, bridge, tunnel...).

Usa scripts/rete_osm.py esteso (copia di sicurezza .bak_18ott dell'originale).
La rete NON sovrascrive quella della Fase 3: scrive in
data/processed/traffico_d/rete/ (nuova cartella). Geometria e topologia restano
identiche (stesso algoritmo): il controllo e' che n_nodi e n_archi_base
coincidano con data/processed/traffico_c/rete.

Output: data/processed/traffico_d/rete/rete_auto.npz
        data/processed/traffico_d/rete/rete_auto_metadati.json
"""

import json
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rete_osm  # noqa: E402


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
PBF = RADICE / "data" / "otp" / "rete" / "torino_cintura.osm.pbf"
OUT = RADICE / "data" / "processed" / "traffico_d" / "rete"
RETE_FASE3 = RADICE / "data" / "processed" / "traffico_c" / "rete"


def main():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    nodi, nodi_xy, archi_base, archi = rete_osm.costruisci(PBF)
    rete_osm.salva(OUT, nodi_xy, archi_base, archi)
    durata = time.time() - t0

    # controllo di compatibilita' con la rete della Fase 3
    ref = json.loads((RETE_FASE3 / "rete_auto_metadati.json").read_text(encoding="utf-8"))
    nuovo = json.loads((OUT / "rete_auto_metadati.json").read_text(encoding="utf-8"))
    stesso = (ref["n_nodi"] == nuovo["n_nodi"] and ref["n_archi_base"] == nuovo["n_archi_base"])
    print(f"rete Fase 5: {nuovo['n_nodi']:,} nodi, {nuovo['n_archi_base']:,} tratti, "
          f"{durata:.1f} s")
    print(f"rete Fase 3: {ref['n_nodi']:,} nodi, {ref['n_archi_base']:,} tratti -> "
          f"{'IDENTICA' if stesso else 'DIVERSA (da capire)'}")

    n_conv = sum(1 for c in nuovo["nomi"] if c)
    print(f"tratti con nome OSM: {n_conv:,} ({100*n_conv/nuovo['n_archi_base']:.1f}%)")
    print(f"tratti con corsie stimate (nessun tag lanes): "
          f"{sum(nuovo['corsie_stimate']):,} ({100*sum(nuovo['corsie_stimate'])/nuovo['n_archi_base']:.1f}%)")

    (OUT.parent / "riepilogo_rete.json").write_text(json.dumps({
        "stimato": False, "n_nodi": nuovo["n_nodi"], "n_archi_base": nuovo["n_archi_base"],
        "identica_alla_fase3": stesso, "durata_s": round(durata, 1),
        "tratti_con_nome": n_conv,
        "tratti_corsie_stimate": int(sum(nuovo["corsie_stimate"])),
        "data": time.strftime("%Y-%m-%d %H:%M:%S"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
