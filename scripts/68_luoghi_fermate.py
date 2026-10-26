#!/usr/bin/env python3
"""
68_luoghi_fermate.py  -  Risultato 6 v2, PASSO 1: dai fermate ai "luoghi".

Cosa fa
-------
Le due fermate ai lati della stessa via, o piu' paline nello stesso punto, sono in
realta' UN SOLO posto. Questo script unisce a catena le fermate che distano meno di
40 metri l'una dall'altra (se A e' vicino a B e B e' vicino a C, allora A, B e C sono
lo stesso "luogo") e calcola per ogni luogo: posizione media, nome piu' frequente,
zona IMQ, e se contiene fermate critiche o coperte secondo la versione 1.

Cosa legge
----------
  data/processed/risultato6_interscambio.json   (fermate della versione 1)
  data/processed/imq_zone_geo.json              (poligoni delle zone IMQ)

Cosa scrive
-----------
  data/processed/risultato6_v2/luoghi.json
  docs/rapporti/RAPPORTO_R6V2_LUOGHI.txt

Come si lancia
--------------
  python scripts\\68_luoghi_fermate.py --prova     (solo le prime 400 fermate, controllo rapido)
  python scripts\\68_luoghi_fermate.py             (giro completo)
"""
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
IN_FERMATE = RADICE / "data" / "processed" / "risultato6_interscambio.json"
IN_ZONE = RADICE / "data" / "processed" / "imq_zone_geo.json"
OUT = RADICE / "data" / "processed" / "risultato6_v2" / "luoghi.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6V2_LUOGHI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

RAGGIO_UNIONE_M = 40.0        # fermate entro 40 m = stesso luogo (a catena)
LATO_CELLA = 0.0005           # gradi, griglia per non confrontare tutte le coppie
ZONA_CENTRO = "Q001"


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def dentro_poligono(lat, lon, anelli):
    """Ray casting; True se il punto e' dentro almeno un anello (lista di [lat, lon])."""
    for anello in anelli:
        n = len(anello)
        dentro = False
        j = n - 1
        for i in range(n):
            yi, xi = anello[i]
            yj, xj = anello[j]
            if ((yi > lat) != (yj > lat)) and (
                lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
            ):
                dentro = not dentro
            j = i
        if dentro:
            return True
    return False


def carica_zone_imq():
    if not IN_ZONE.exists():
        sys.exit(f"Non trovo {IN_ZONE}")
    geo = json.loads(IN_ZONE.read_text(encoding="utf-8"))
    zone = []
    for z in geo:
        g = z["g"]
        if isinstance(g, str):
            g = json.loads(g)
        if g and isinstance(g[0][0], (int, float)):
            anelli = [g]
        elif g and isinstance(g[0][0][0], (int, float)):
            anelli = g
        else:
            anelli = [anello for poligono in g for anello in poligono]
        lat_min = min(p[0] for anello in anelli for p in anello)
        lat_max = max(p[0] for anello in anelli for p in anello)
        lon_min = min(p[1] for anello in anelli for p in anello)
        lon_max = max(p[1] for anello in anelli for p in anello)
        zone.append({"cod": z["cod"], "anelli": anelli,
                     "bbox": (lat_min, lon_min, lat_max, lon_max)})
    return zone


def zona_di(lat, lon, zone):
    for z in zone:
        lat_min, lon_min, lat_max, lon_max = z["bbox"]
        if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
            continue
        if dentro_poligono(lat, lon, z["anelli"]):
            return z["cod"]
    return None


def trova_luoghi(fermate, raggio_m):
    """Unione a catena con union-find, usando una griglia di celle per non confrontare
    tutte le coppie. Ritorna la lista delle liste di indici."""
    n = len(fermate)
    genitore = list(range(n))

    def trova(i):
        while genitore[i] != i:
            genitore[i] = genitore[genitore[i]]
            i = genitore[i]
        return i

    def unisci(i, j):
        ri, rj = trova(i), trova(j)
        if ri != rj:
            genitore[rj] = ri

    celle = {}
    for i, f in enumerate(fermate):
        cx = int(math.floor(f["lat"] / LATO_CELLA))
        cy = int(math.floor(f["lon"] / LATO_CELLA))
        celle.setdefault((cx, cy), []).append(i)

    for (cx, cy), indici in celle.items():
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                if (dx, dy) == (0, 0):
                    vicini = indici
                    for a in range(len(vicini)):
                        for b in range(a + 1, len(vicini)):
                            i, j = vicini[a], vicini[b]
                            fi, fj = fermate[i], fermate[j]
                            if haversine_m(fi["lat"], fi["lon"], fj["lat"], fj["lon"]) <= raggio_m:
                                unisci(i, j)
                    continue
                altri = celle.get((cx + dx, cy + dy))
                if not altri:
                    continue
                if (dx, dy) > (0, 0):
                    continue  # evita di ripetere la stessa coppia di celle
                for i in indici:
                    fi = fermate[i]
                    for j in altri:
                        fj = fermate[j]
                        if haversine_m(fi["lat"], fi["lon"], fj["lat"], fj["lon"]) <= raggio_m:
                            unisci(i, j)

    gruppi = {}
    for i in range(n):
        gruppi.setdefault(trova(i), []).append(i)
    return list(gruppi.values())


def nome_luogo(fermate_gruppo):
    """Nome di fermata piu' frequente; a parita' di frequenza, il piu' corto."""
    conta = Counter(f["nome"] for f in fermate_gruppo)
    return sorted(conta.items(), key=lambda kv: (-kv[1], len(kv[0]), kv[0]))[0][0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true",
                    help="solo le prime 400 fermate per stop_id, per un controllo rapido")
    ap.add_argument("--raggio-m", type=float, default=RAGGIO_UNIONE_M)
    args = ap.parse_args()

    for p in (IN_FERMATE, IN_ZONE):
        if not p.exists():
            sys.exit(f"Manca: {p}")

    dati = json.loads(IN_FERMATE.read_text(encoding="utf-8"))
    fermate = [f for f in dati["fermate"] if f.get("lat") is not None]
    fermate.sort(key=lambda f: f["stop_id"])
    if args.prova:
        fermate = fermate[:400]
        print(f"[--prova] uso le prime {len(fermate)} fermate per stop_id")
    print(f"fermate in ingresso: {len(fermate)}")

    print("carico le zone IMQ...")
    zone = carica_zone_imq()

    print(f"unisco le fermate entro {args.raggio_m:.0f} m (a catena)...")
    gruppi = trova_luoghi(fermate, args.raggio_m)
    print(f"  gruppi trovati: {len(gruppi)}")

    # i luoghi si numerano per latitudine poi longitudine
    descrittori = []
    for idx in gruppi:
        membri = [fermate[i] for i in idx]
        lat = sum(m["lat"] for m in membri) / len(membri)
        lon = sum(m["lon"] for m in membri) / len(membri)
        descrittori.append((lat, lon, membri))

    descrittori.sort(key=lambda t: (t[0], t[1]))

    luoghi = []
    senza_zona = 0
    for k, (lat, lon, membri) in enumerate(descrittori, start=1):
        cod = zona_di(lat, lon, zone)
        if cod is None:
            senza_zona += 1
            membri_ordinati = sorted(membri, key=lambda m: m["stop_id"])
            cod = membri_ordinati[0].get("zona_imq")
        luoghi.append({
            "id_luogo": f"L{k:05d}",
            "nome": nome_luogo(membri),
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "stop_ids": sorted(m["stop_id"] for m in membri),
            "n_fermate": len(membri),
            "zona_imq": cod,
            "in_centro": cod == ZONA_CENTRO,
            "critico_v1": any(bool(m.get("fermata_critica")) for m in membri),
            "coperto_v1": any(bool(m.get("coperta")) for m in membri),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "raggio_unione_m": args.raggio_m,
        "n_fermate_ingresso": len(fermate),
        "n_luoghi": len(luoghi),
        "luoghi": luoghi,
    }, ensure_ascii=False), encoding="utf-8")

    # --- rapporto ---
    conta = Counter(l["n_fermate"] for l in luoghi)
    distr = [(k, conta.get(k, 0)) for k in (1, 2, 3)]
    oltre = sum(v for k, v in conta.items() if k >= 4)
    n_critici = sum(1 for l in luoghi if l["critico_v1"])
    n_coperti = sum(1 for l in luoghi if l["coperto_v1"])
    fermate_critiche_v1 = sum(1 for f in fermate if f.get("fermata_critica"))
    luoghi_critici_v1 = sum(1 for l in luoghi if l["critico_v1"])

    righe = []
    righe.append("RAPPORTO R6 v2 — LUOGHI DI FERMATA (Passo 1)")
    righe.append(f"modalita': {'PROVA (400 fermate)' if args.prova else 'completa'}")
    righe.append(f"fermate in ingresso: {len(fermate)}")
    righe.append(f"luoghi (fermate entro {args.raggio_m:.0f} m unite a catena): {len(luoghi)}")
    righe.append(f"riduzione: {len(fermate)} fermate -> {len(luoghi)} luoghi "
                 f"({100 * (1 - len(luoghi) / max(1, len(fermate))):.1f}% in meno)")
    righe.append(f"luoghi senza zona IMQ trovata nel punto medio (usata la zona della prima "
                 f"fermata): {senza_zona}")
    righe.append("")
    righe.append("== Quante fermate per luogo ==")
    for k, v in distr:
        righe.append(f"  {k} fermata/e: {v} luoghi")
    righe.append(f"  4 o piu': {oltre} luoghi")
    righe.append("")
    righe.append(f"luoghi con almeno una fermata critica (v1): {n_critici}")
    righe.append(f"luoghi con almeno una fermata coperta (v1): {n_coperti}")
    righe.append("")
    righe.append(f"611 fermate critiche della versione 1 = {luoghi_critici_v1} luoghi")
    righe.append(f"(controllo: fermate critiche v1 nel file letto = {fermate_critiche_v1})")
    righe.append("")
    righe.append("== I 10 luoghi con piu' fermate ==")
    for l in sorted(luoghi, key=lambda l: (-l["n_fermate"], l["nome"]))[:10]:
        righe.append(f"  {l['n_fermate']:2d} fermate  {l['nome']:45s} zona={l['zona_imq'] or '-'}")
    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")

    print(f"Scritto: {OUT}")
    print(f"Scritto: {RAPPORTO}")
    print(f"luoghi={len(luoghi)}  critici_v1={n_critici}  coperti_v1={n_coperti}")


if __name__ == "__main__":
    sys.exit(main())
