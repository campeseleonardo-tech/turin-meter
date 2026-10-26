# -*- coding: utf-8 -*-
"""
scripts/104_velocita_bus.py - Velocita' commerciale dei bus e dei tram dal GPS, ora per ora (scheda 2, giro L20 / E4).

Regole (fissate il 25/10/2026 prima dei numeri, `sviluppo/piani/PIANO_GRAFICA.md`, «Regole di E4»):
- velocita' commerciale = distanza percorsa / tempo fra le posizioni GPS consecutive, fermate comprese (le soste brevi contano, il capolinea no):
  e' lo STESSO calcolo del livello «Velocita'» di 04_genera_mappa.py (`calcola_velocita`), che qui si riusa e non si riscrive;
- giorni feriali del periodo fisso `comuni.PERIODO["gps"]` (solo giorni interi), media pesata sui campioni (intervalli fra posizioni),
  ora per ora dalle 5 alle 24, bus e tram separati e insieme; la metro non c'e' (non ha GPS nel feed);
- bus o tram dal tipo di linea del GTFS (route_type 0 = tram, 1 = metro, altro = bus; come lo script 27);
- controlli: velocita' fra 5 e 40 km/h; AVVISO per le ore con meno di 1.000 campioni.

Come si lancia
--------------
  python scripts\\104_velocita_bus.py            (legge la copia dello storico data/storico_backup.sqlite: alcuni minuti)
Uscite: data/processed/velocita_bus.json, docs/rapporti/RAPPORTO_VELOCITA_BUS.txt
"""
import csv
import io
import json
import sys
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
OUT_JSON = RADICE / "data" / "processed" / "velocita_bus.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_VELOCITA_BUS.txt"

ORE = list(range(5, 24))                 # dalle 5 alle 24 (ultima ora: 23-24)
VEL_MIN, VEL_MAX = 5.0, 40.0
CAMPIONI_MIN = 1000
FERIALE = "0"


def modi_per_codice(percorso):
    """codice della linea nel feed dei mezzi (= route_id del GTFS, es. «10U») -> tram / metro / bus da route_type."""
    modi = {}
    with zipfile.ZipFile(percorso) as z, z.open("routes.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            modi[r["route_id"]] = {"0": "tram", "1": "metro"}.get(r.get("route_type", ""), "bus")
    return modi


def media_pesata(coppie):
    """[(kmh, campioni)] -> (kmh medio pesato sui campioni, campioni)."""
    tot = sum(n for _, n in coppie)
    if tot <= 0:
        return None, 0
    return sum(v * n for v, n in coppie) / tot, tot


def main():
    c = comuni.Controlli()
    if not ((RADICE / "data" / "storico_backup.sqlite").is_file() or (RADICE / "data" / "storico.sqlite").is_file()) and OUT_JSON.is_file():
        print("AVVISO: manca la copia dello storico dei mezzi: si tiene data/processed/velocita_bus.json com'e' (fatto dal PC di Leo).")
        return
    m04 = comuni.carica_script("04_genera_mappa.py")
    m27 = comuni.carica_script("27_risultato4_regolarita.py")
    vel, meta = m04.calcola_velocita()
    c("storico dei mezzi letto", vel is not None, bloccante=True)
    modi = modi_per_codice(m27.GTFS)
    gruppi = {"bus": [], "tram": []}
    senza_modo = []
    for linea, per_tipo in vel.items():
        modo = modi.get(str(linea))
        if modo is None:
            senza_modo.append(str(linea))
            modo = "bus"
        if modo == "metro":
            continue
        gruppi[modo].append(per_tipo.get(FERIALE, {}))
    c("linee dei mezzi presenti nel GTFS", len(senza_modo) <= 3, dettaglio=f"{len(senza_modo)} senza tipo (contate come bus): {', '.join(sorted(senza_modo)[:6])}")

    risultato = {}
    for nome in ("bus", "tram", "tutti"):
        risultato[nome] = {}
        sorgenti = gruppi["bus"] + gruppi["tram"] if nome == "tutti" else gruppi[nome]
        for ora in ORE:
            v, n = media_pesata([(celle[str(ora)][0], celle[str(ora)][1]) for celle in sorgenti if str(ora) in celle])
            if v is not None:
                risultato[nome][str(ora)] = {"kmh": round(v, 1), "campioni": n}
    for nome, per_ora in risultato.items():
        c(f"{nome}: almeno 10 ore con dati", len(per_ora) >= 10, bloccante=True, dettaglio=f"{len(per_ora)} ore")
        fuori = {o: x["kmh"] for o, x in per_ora.items() if not VEL_MIN <= x["kmh"] <= VEL_MAX}
        c(f"{nome}: velocita' fra {VEL_MIN:g} e {VEL_MAX:g} km/h", not fuori, dettaglio=", ".join(f"ore {o}: {v}" for o, v in fuori.items()))
        poche = [o for o, x in per_ora.items() if x["campioni"] < CAMPIONI_MIN]
        c(f"{nome}: ogni ora con almeno {CAMPIONI_MIN} campioni", not poche, dettaglio=f"ore con meno: {', '.join(poche)}")
    giorni_fer = meta["giorni"].get(FERIALE)
    out = {"fonte": "posizioni GPS dei mezzi GTT (storico della raccolta), stesso calcolo del livello Velocita' della mappa",
           "periodo": {"da": comuni.PERIODO["gps"][0], "a": comuni.PERIODO["gps"][1]}, "giorni_feriali": giorni_fer,
           "pesi": "campioni (intervalli fra posizioni consecutive)", "ore": [ORE[0], ORE[-1] + 1],
           "controlli_regole": {"vel_min": VEL_MIN, "vel_max": VEL_MAX, "campioni_min": CAMPIONI_MIN},
           "velocita": risultato, "controlli": c.righe}
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    righe = ["VELOCITA' DEI BUS E DEI TRAM (script 104) - feriali, GPS, periodo " + f"{out['periodo']['da']} / {out['periodo']['a']}, {giorni_fer} giorni feriali", ""]
    righe.append("ora   bus km/h (campioni)   tram km/h (campioni)   tutti km/h")
    for ora in ORE:
        b, t, a = (risultato[k].get(str(ora)) for k in ("bus", "tram", "tutti"))
        fmt = lambda x: f"{x['kmh']:5.1f} ({x['campioni']:>6})" if x else "     -          "
        righe.append(f"{ora:>2}    {fmt(b)}    {fmt(t)}    {a['kmh'] if a else '-'}")
    righe += ["", "CONTROLLI"] + c.righe
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe[:25]))
    print("avvisi:", len(c.avvisi()))


if __name__ == "__main__":
    main()
