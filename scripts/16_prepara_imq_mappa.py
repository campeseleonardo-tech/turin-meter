#!/usr/bin/env python3
"""16_prepara_imq_mappa.py - prepara i dati IMQ 2022 per la mappa.

Legge i prodotti delle attivita' 10 (data/processed/imq_*.json e imq/*.csv) e scrive
data/processed/imq_mappa.json, compatto, con le sole 101 zone della Citta' Metropolitana
di Torino (23 Torino + 32 cintura + 46 resto CMTO):

- per zona: geometria semplificata (~30 m), centroide, residenti pesati, spostamenti in
  partenza per ora (0-23) x modo (totale/pubblico/privato/altro), scopi e quote modali
  dell'intera giornata;
- per il clic: flussi origine->destinazione in uscita (destinazioni principali).

Solo libreria standard. L'ora del giorno si lega a S.h della mappa (slider gia' presente).
Uso: python scripts/16_prepara_imq_mappa.py
"""

import csv
import json
import math
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def trova_radice():
    for c in [AQUI, *AQUI.parents]:
        if c.name.lower() == "gtt":
            return c
    d = Path.home() / "Desktop" / "GTT"
    return d if d.is_dir() else AQUI.parent


RADICE = trova_radice()
PROC = RADICE / "data" / "processed"
IN = PROC / "imq"
OUT = PROC / "imq_mappa.json"

MACRO_CMTO = ("01 Torino", "02 Cintura", "03 Resto CMTO")
SOGLIA_N = 30
TOL_DEG = 30.0 / 111320.0    # ~30 m, in gradi (scalata per cos(lat) nella semplificazione)
TOP_OD = 15                  # quante destinazioni tenere per zona

# Classificazione dei mezzi (come 14_prepara_imq.py).
PUBBLICO_TIPI = {"MBT", "BXU", "TR"}
PUBBLICO_COD = {"08", "10", "11", "23", "24"}
PRIVATO_COD = {"02", "03", "04", "05"}


def classe_mezzo(cod, tipo):
    tipo = (tipo or "").strip().upper()
    if tipo in PUBBLICO_TIPI or cod in PUBBLICO_COD:
        return "pubblico"
    if cod in PRIVATO_COD:
        return "privato"
    return "altro"


def norm_zona(c):
    c = (c or "").strip()
    if len(c) == 4 and c[0].upper() == "Q" and c[1].upper() == "C":
        return "Q0" + c[2:]
    return c


# ---------------------------------------------------------------- Douglas-Peucker
def dp(pts, tol):
    if len(pts) < 4:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1e-9
        md, mi = 0.0, None
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - x1) - dx * (pts[i][1] - y1)) / L
            if d > md:
                md, mi = d, i
        if mi is not None and md > tol:
            keep[mi] = True
            st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]


def dp_anello(ring, tol):
    if len(ring) < 6:
        return ring
    x0, y0 = ring[0]
    m = max(range(1, len(ring) - 1), key=lambda i: (ring[i][0] - x0) ** 2 + (ring[i][1] - y0) ** 2)
    return dp(ring[:m + 1], tol)[:-1] + dp(ring[m:], tol)


def semplifica_anello(ring, tol_deg):
    """Semplifica un anello chiuso [lat,lon]; scala la longitudine per cos(lat)."""
    if len(ring) < 6:
        return ring
    coslat = math.cos(math.radians(ring[0][0]))
    p = [(la, lo * coslat) for la, lo in ring]
    p2 = dp_anello(p, tol_deg)
    return [[round(la, 5), round(lo / coslat, 5)] for la, lo in p2]


def centroide(ring):
    """Centroide d'area di un anello [lat,lon]; None se area nulla."""
    s = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        cr = x1 * y2 - x2 * y1
        s += cr
        cx += (x1 + x2) * cr
        cy += (y1 + y2) * cr
    area = s / 2.0
    if area == 0:
        return None
    return cx / (6 * area), cy / (6 * area)


def pip_anello(x, y, ring):
    inside = False
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        if (y1 > y) != (y2 > y):
            if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside


def punto_in_anelli(x, y, rings):
    return sum(1 for r in rings if pip_anello(x, y, r)) % 2 == 1


# ---------------------------------------------------------------- lettura
def leggi_json(percorso):
    if not Path(percorso).is_file():
        sys.exit(f"STOP: file mancante {percorso} (attivita' 10 non completata?)")
    return json.loads(Path(percorso).read_text(encoding="utf-8"))


def main():
    zone_meta = {z["cod"]: z for z in leggi_json(PROC / "imq_zone.json")}
    geo = {z["cod"]: z for z in leggi_json(PROC / "imq_zone_geo.json")}
    res = leggi_json(PROC / "imq_residenti.json")["per_zona"]
    agg = leggi_json(PROC / "imq_aggregati.json")["per_zona"]
    od_raw = leggi_json(PROC / "imq_od.json")
    mezzi = list(csv.DictReader(open(IN / "mezzi.csv", encoding="utf-8", newline=""), delimiter=";"))
    cls_mezzo = {r["Cod_Mezzo"].strip(): classe_mezzo(r["Cod_Mezzo"].strip(), r.get("cod_tipo_mezzo"))
                 for r in mezzi}

    # zone CMTO
    cmto = [c for c, z in zone_meta.items() if z["macro"] in MACRO_CMTO]
    cmto_set = set(cmto)
    if len(cmto) != 101:
        sys.exit(f"STOP: zone CMTO attese 101, trovate {len(cmto)}")

    # --- residenti e quote/scopi dell'intera giornata ---
    zone_out = {}
    for c in cmto:
        meta = zone_meta[c]
        g = geo[c]["g"]
        # semplifica e tieni l'anello esterno (il piu' esteso) per il centroide
        gs = [semplifica_anello(r, TOL_DEG) for r in g]
        anello_out = max(gs, key=lambda r: abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1]
                                                for i in range(len(r) - 1))))
        cen = centroide(anello_out) or (anello_out[0][0], anello_out[0][1])
        if not punto_in_anelli(cen[0], cen[1], gs):   # fallback per forme concave
            mv = (sum(p[0] for p in anello_out) / len(anello_out),
                  sum(p[1] for p in anello_out) / len(anello_out))
            if punto_in_anelli(mv[0], mv[1], gs):
                cen = mv
        residenti = sum(v["v"] for sesso in res.get(c, {}).values() for v in sesso.values())
        modo = {m: agg[c]["modo"].get(m, [0, 0]) for m in ("pub", "pri", "alt")} if c in agg else {}
        tot_modo = sum(v[0] for v in modo.values())
        scopo = {k: v for k, v in agg.get(c, {}).get("scopo", {}).items()}
        zone_out[c] = {
            "c": c, "n": meta["denom"], "m": meta["macro"],
            "g": gs, "la": round(cen[0], 6), "lo": round(cen[1], 6),
            "res": round(residenti, 3),
            "scopo": {k: [round(v[0], 1), v[1]] for k, v in scopo.items()},
            "quotaPub": round(modo.get("pub", [0])[0] / tot_modo, 4) if tot_modo else None,
            "quotaPri": round(modo.get("pri", [0])[0] / tot_modo, 4) if tot_modo else None,
            "ora": [{"tot": [0.0, 0], "pub": [0.0, 0], "pri": [0.0, 0], "alt": [0.0, 0]}
                    for _ in range(24)],
        }

    # --- spostamenti per ora x modo (ricostruiti dallo CSV, origine nelle 101 zone) ---
    somma_ora = 0.0
    somma_agg = 0.0
    with open(IN / "spostamenti.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            par = norm_zona(r["COD_PAR"])
            if par not in cmto_set:
                continue
            peso = float(r["PESO"] or 0)
            if peso < 0:
                sys.exit(f"STOP: peso negativo ({peso}) per origine {par}")
            somma_ora += peso
            ora_s = (r["ORA_PAR"] or "").strip()
            if not ora_s:
                continue
            h = int(ora_s.split(":")[0]) % 24
            classi = {cls_mezzo.get((r[f"MEZZO{i}"] or "").strip()) for i in range(1, 4)}
            classi.discard(None)
            modo = "pub" if "pubblico" in classi else ("pri" if "privato" in classi else "alt")
            cella = zone_out[par]["ora"][h]
            cella["tot"][0] += peso
            cella["tot"][1] += 1
            cella[modo][0] += peso
            cella[modo][1] += 1

    # arrotonda le celle ora
    for z in zone_out.values():
        for cella in z["ora"]:
            for k in cella:
                cella[k][0] = round(cella[k][0], 3)

    # somma di controllo dai margini di fase 2 (solo zone CMTO)
    for c in cmto:
        if c in agg:
            somma_agg += sum(v[0] for v in agg[c]["modo"].values())

    # --- flussi OD in uscita (per il clic) ---
    od_out = {c: [] for c in cmto}
    for oc, dc, v, n, aff in od_raw["od"]["tot"]:
        if oc not in cmto_set:
            continue
        od_out[oc].append({"d": dc, "dn": zone_meta.get(dc, {}).get("denom", dc),
                           "v": round(v, 1), "n": n, "aff": bool(aff),
                           "est": dc not in cmto_set})
    for c in od_out:
        od_out[c].sort(key=lambda x: -x["v"])
        od_out[c] = od_out[c][:TOP_OD]

    # ------------------------------------------------------------ verifiche
    esiti = []

    def check(nome, ok, dettaglio):
        esiti.append((nome, bool(ok)))
        print(f"[{'OK ' if ok else 'STOP'}] {nome}: {dettaglio}")

    check("101 zone CMTO", len(zone_out) == 101, f"{len(zone_out)}")
    check("geometria per ogni zona", all(z["g"] for z in zone_out.values()),
          f"{sum(1 for z in zone_out.values() if not z['g'])} senza")
    check("nessun valore negativo", all(c[0] >= 0 for z in zone_out.values()
                                        for cella in z["ora"] for c in cella.values()), "ok")
    check("somma spostamenti per ora = margini fase 2 (CMTO)",
          abs(somma_ora - somma_agg) / max(somma_agg, 1) < 0.001,
          f"{somma_ora:.0f} vs {somma_agg:.0f} ({100*(somma_ora-somma_agg)/max(somma_agg,1):+.3f}%)")
    tot_res = sum(z["res"] for z in zone_out.values())
    check("residenti CMTO ~ 1.942.688", abs(tot_res - 1942688) / 1942688 < 0.01,
          f"{tot_res:.0f}")
    fuori_cen = [z["c"] for z in zone_out.values()
                 if not punto_in_anelli(z["la"], z["lo"], z["g"])]
    print(f"[NOTA] centroidi fuori dalla geometria (solo per le linee): "
          f"{fuori_cen if fuori_cen else 'nessuno'}")
    check("flussi OD per ogni zona", all(c in od_out for c in cmto), f"{len(od_out)}")

    out = {
        "meta": {
            "fonte": "IMQ 2022 - Agenzia della Mobilita' Piemontese / MTM (microdati open data)",
            "universo": "residenti 11-84 anni, giorno feriale",
            "zone": len(zone_out), "nota": "quartieri di Torino: confini 1984",
        },
        "zone": [zone_out[c] for c in cmto],
        "od": od_out,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"\n  scritto {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")

    fallite = [n for n, ok in esiti if not ok]
    if fallite:
        sys.exit("STOP: verifiche fallite: " + ", ".join(fallite))
    print("Verifiche superate. Prosegui con 04_genera_mappa.py.")


if __name__ == "__main__":
    main()
