#!/usr/bin/env python3
"""
costruisci_contorno_torino.py  -  il contorno del comune di Torino per le animazioni (home, caricamento della mappa).

Legge i confini dalla mappa (mappa_torino.html, D.confine_torino: anelli del comune dai confini ISTAT), li semplifica un po' e scrive
assets/torino_contorno.json: un percorso SVG (coordinate intere relative) e i numeri per passare da latitudine/longitudine al disegno:
    x = (lon - lon_min) * k * scala        y = (lat_max - lat) * scala
Uso: python scripts/costruisci_contorno_torino.py   (si rifa' solo se cambiano i confini)
"""
import json
import math
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
LARG = 1000          # larghezza del disegno, in unita'
TOLLERANZA = 0.00025  # gradi (circa 25 m): toglie i dettagli che a schermo non si vedono


def main():
    riga = next(x for x in (RADICE / "mappa_torino.html").read_text(encoding="utf-8").split("\n") if x.startswith("const DATI = "))
    anelli = json.loads(riga[len("const DATI = "):].rstrip(";"))["confine_torino"]
    if not anelli:
        raise SystemExit("ERRORE: la mappa non ha il confine di Torino")
    tutti = [p for a in anelli for p in a]
    lat_min, lat_max = min(p[0] for p in tutti), max(p[0] for p in tutti)
    lon_min, lon_max = min(p[1] for p in tutti), max(p[1] for p in tutti)
    k = math.cos(math.radians((lat_min + lat_max) / 2))
    scala = LARG / ((lon_max - lon_min) * k)
    alt = round((lat_max - lat_min) * scala)
    try:
        from shapely.geometry import Polygon
        semplifica = lambda a: list(Polygon([(p[1], p[0]) for p in a]).simplify(TOLLERANZA).exterior.coords)
        anelli_s = [[(y, x) for x, y in semplifica(a)] for a in anelli]
    except ImportError:
        anelli_s = anelli
    d = ""
    n_punti = 0
    for a in anelli_s:
        xy = [(round((p[1] - lon_min) * k * scala), round((lat_max - p[0]) * scala)) for p in a]
        pulito = [xy[0]]
        for q in xy[1:]:
            if q != pulito[-1]:
                pulito.append(q)
        if len(pulito) < 3:
            continue
        n_punti += len(pulito)
        d += "M%d %d" % pulito[0] + "".join("l%d %d" % (x - px, y - py) for (px, py), (x, y) in zip(pulito, pulito[1:])) + "z"
    out = {"larghezza": LARG, "altezza": alt, "lat_max": lat_max, "lon_min": lon_min, "k": round(k, 6), "scala": round(scala, 3), "d": d}
    p = RADICE / "assets" / "torino_contorno.json"
    p.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"{p.name}: {len(anelli)} anelli, {n_punti} punti, {p.stat().st_size} byte, disegno {LARG}x{alt}")


if __name__ == "__main__":
    main()
