# -*- coding: utf-8 -*-
"""
scripts/59_ztl.py - Pacchetto C (Fase 5): ZTL unificata e aree pedonali.

Unisce le fonti:
  - data/raw/ztl_csv.zip            (poligoni del Comune, EPSG:3003, 3 zone con orari)
  - data/raw/5t_access_control_20261014.xml (ZTL Centrale del feed 5T, lat/lon,
    validita' 2022-2024, lun-ven 07:30-10:30)
  - la tabella ztl_5t raccolta sul Pi (la stessa del feed, ferma al 2024)
  - data/raw/aree_pedonali_csv.zip  (143 aree pedonali, EPSG:3003)

Produce una mappa unica delle ZTL con orari e delle aree pedonali, e per ogni
TRATTA la quota di lunghezza dentro una ZTL e dentro un'area pedonale.

Output: data/processed/traffico_d/ztl_unificata.json
        data/processed/traffico_d/tratte_ztl.csv
        docs/rapporti/RAPPORTO_ZTL.txt
"""

import csv
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rete_osm  # noqa: E402


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
RAW = RADICE / "data" / "raw"
PROC = RADICE / "data" / "processed"
OUT = PROC / "traffico_d"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_ZTL.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)


def parse_wkt_poligoni(wkt):
    """Ritorna una lista di anelli esterni [(x,y), ...] da POLYGON/MULTIPOLYGON."""
    wkt = wkt.strip()
    anelli = []
    # primo anello di ogni poligono (esterno)
    for blocco in re.findall(r"\(\(([^()]*(?:\)[^()]*\([^()]*)*)\)", wkt):
        pass
    # approccio semplice: prendi tutte le sequenze "(((...)))"
    for m in re.finditer(r"\(\(([^()]+)\)", wkt):
        pts = []
        for coppia in m.group(1).split(","):
            parti = coppia.strip().split()
            if len(parti) >= 2:
                pts.append((float(parti[0]), float(parti[1])))
        if len(pts) >= 4:
            anelli.append(pts)
    return anelli


def ore_da_fascia(ini, fin):
    def h(s):
        try:
            return int(str(s).split(":")[0])
        except Exception:
            return None
    a, b = h(ini), h(fin)
    if a is None or b is None:
        return []
    if a <= b:
        return list(range(a, b + 1))
    return list(range(a, 24)) + list(range(0, b + 1))


def main():
    from pyproj import Transformer
    from shapely.geometry import Polygon, Point
    from shapely.strtree import STRtree
    tr = Transformer.from_crs("EPSG:3003", "EPSG:4326", always_xy=True)

    zone = []
    # --- fonte 1: comune (EPSG:3003) ---
    zf = zipfile.ZipFile(RAW / "ztl_csv.zip")
    for r in csv.DictReader(io.TextIOWrapper(zf.open("ztl.csv"), encoding="utf-8-sig"),
                            delimiter=";"):
        anelli_ll = []
        for an in parse_wkt_poligoni(r["WKT_GEOM"]):
            anelli_ll.append([tr.transform(x, y) for (x, y) in an])  # (lon, lat)
        zone.append({
            "nome": r["DENOMINAZI"].strip(),
            "fonti": ["comune_ztl_csv"],
            "poligoni": anelli_ll,
            "orari": [{"giorni": "lun-sab", "inizio": r["ORA_INIZIO"], "fine": r["ORA_FINE"]}],
            "sospensioni": r["SOSPENS"][:200],
            "ordinanza": r["ORDINANZA"],
            "validita": "2016-2017",
            "fonte_vecchia": True,
            "stato": "attiva",
        })

    # --- fonte 2: 5T (lat/lon) ---
    xml = (RAW / "5t_access_control_20261014.xml").read_text(encoding="utf-8", errors="replace")
    import xml.etree.ElementTree as ET
    rad = ET.fromstring(xml)
    ns = {"a": "https://simone.5t.torino.it/ns/access_control.xsd"}
    for z in rad.findall("a:ztl", ns):
        nome = z.get("name") or ""
        pts = []
        for p in z.findall("a:polyline/a:point", ns):
            pts.append((float(p.get("lng")), float(p.get("lat"))))  # (lon, lat)
        orari = []
        polit = z.find("a:access_policy/a:time_policy", ns)
        if polit is not None:
            wd = polit.find("a:weekday", ns)
            if wd is not None:
                orari.append({"giorni": "lun-ven", "inizio": wd.get("start_time"),
                              "fine": wd.get("end_time")})
        zone.append({
            "nome": nome.replace("ZTL ", "").strip().lower(),
            "fonti": ["5t_access_control"],
            "poligoni": [pts] if pts else [],
            "orari": orari,
            "sospensioni": "",
            "ordinanza": "",
            "validita": "2022-2024",
            "fonte_vecchia": False,
            "stato": "attiva",
        })

    # --- unione: zone con lo stesso nome si fondono (la piu' recente detta gli orari) ---
    per_nome = {}
    for z in zone:
        k = z["nome"].strip().lower()
        if k not in per_nome:
            per_nome[k] = z
        else:
            base = per_nome[k]
            base["fonti"] += z["fonti"]
            base["poligoni"] += z["poligoni"]
            if z["fonte_vecchia"] is False and base["fonte_vecchia"]:
                base["orari"] = z["orari"]          # la piu' recente vince
                base["validita"] = z["validita"]
                base["fonte_vecchia"] = False
                base["discordanza_orari"] = True
    unificate = [{**z, "ore_attive": sorted({h for o in z["orari"]
                                             for h in ore_da_fascia(o["inizio"], o["fine"])})}
                 for z in per_nome.values()]

    # --- aree pedonali ---
    zf2 = zipfile.ZipFile(RAW / "aree_pedonali_csv.zip")
    pedonali = []
    for r in csv.DictReader(io.TextIOWrapper(zf2.open("aree_pedonali.csv"), encoding="utf-8-sig"),
                            delimiter=";"):
        anelli_ll = []
        for an in parse_wkt_poligoni(r["WKT_GEOM"]):
            anelli_ll.append([tr.transform(x, y) for (x, y) in an])
        if anelli_ll:
            pedonali.append({"nome": r["DENOMINAZI"].strip(),
                             "circoscrizione": r["CIRCOSCRIZ"],
                             "poligoni": anelli_ll})

    # --- indici spaziali ---
    def shapely_zone(z):
        polys = []
        for an in z["poligoni"]:
            if len(an) >= 4:
                try:
                    p = Polygon(an)
                    if not p.is_valid:
                        p = p.buffer(0)
                    if p.area > 0:
                        polys.append(p)
                except Exception:
                    pass
        return polys

    ztl_polys = []; ztl_ids = []
    for i, z in enumerate(unificate):
        for p in shapely_zone(z):
            ztl_polys.append(p); ztl_ids.append(i)
    ztl_tree = STRtree(ztl_polys) if ztl_polys else None
    ped_polys = []
    for pa in pedonali:
        for an in pa["poligoni"]:
            if len(an) >= 4:
                try:
                    p = Polygon(an)
                    if not p.is_valid:
                        p = p.buffer(0)
                    if p.area > 0:
                        ped_polys.append(p)
                except Exception:
                    pass
    ped_tree = STRtree(ped_polys) if ped_polys else None

    def dentro(an, tree, polys):
        if tree is None:
            return False
        pt = Point(an)
        for j in np.atleast_1d(tree.query(pt)):
            if polys[j].contains(pt):
                return True
        return False

    # --- tratte: quota dentro ZTL / aree pedonali ---
    righe_csv = []
    with (OUT / "tratte.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            geom = []
            inner = r["geom_wkt"][r["geom_wkt"].find("(") + 1:r["geom_wkt"].rfind(")")]
            for coppia in inner.split(","):
                x, y = coppia.split()
                geom.append((float(x), float(y)))  # (lon, lat)
            # ricampiona ogni ~25 m
            camp = [geom[0]]
            acc = 0.0
            for k in range(len(geom) - 1):
                d = rete_osm.haversine_m(geom[k][1], geom[k][0], geom[k + 1][1], geom[k + 1][0])
                if d <= 0:
                    continue
                acc += d
                if acc >= 25:
                    camp.append(geom[k + 1]); acc = 0.0
            if camp[-1] != geom[-1]:
                camp.append(geom[-1])
            quali = set()
            n_ztl = 0
            for (lo, la) in camp:
                if dentro((lo, la), ztl_tree, ztl_polys):
                    n_ztl += 1
                    for j in np.atleast_1d(ztl_tree.query(Point(lo, la))):
                        if ztl_polys[j].contains(Point(lo, la)):
                            quali.add(ztl_ids[j])
            n_ped = sum(1 for (lo, la) in camp if dentro((lo, la), ped_tree, ped_polys))
            fraz = n_ztl / max(len(camp), 1)
            fraz_ped = n_ped / max(len(camp), 1)
            righe_csv.append({
                "id_tratta": int(r["id_tratta"]), "id_asse": int(r["id_asse"]),
                "nome": r["nome_principale"], "comune": r["comune"],
                "ztl_frazione": round(fraz, 3), "pedonale_frazione": round(fraz_ped, 3),
                "ztl_zone": [unificate[i]["nome"] for i in sorted(quali)],
                "ztl_ore": sorted({h for i in quali for h in unificate[i]["ore_attive"]}),
            })

    with (OUT / "tratte_ztl.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["id_tratta", "id_asse", "nome", "comune", "ztl_frazione",
                    "pedonale_frazione", "ztl_zone", "ztl_ore"])
        for r in righe_csv:
            w.writerow([r["id_tratta"], r["id_asse"], r["nome"] or "", r["comune"] or "",
                        r["ztl_frazione"], r["pedonale_frazione"],
                        "|".join(r["ztl_zone"]), "|".join(str(h) for h in r["ztl_ore"])])

    (OUT / "ztl_unificata.json").write_text(json.dumps({
        "stimato": False,
        "nota": ("ZTL unificate dal Comune (2016-2017) e dal feed 5T (2022-2024, la piu' "
                 "recente detta gli orari) + 143 aree pedonali. Coordinate lat/lon."),
        "n_zone": len(unificate), "n_aree_pedonali": len(pedonali),
        "zone": unificate,
    }, ensure_ascii=False), encoding="utf-8")

    # --- controlli ---
    righe = []
    def a_(s=""):
        righe.append(s)
    a_("ZTL UNIFICATA E AREE PEDONALI (pacchetto C, Fase 5)")
    a_("=" * 74)
    a_("== Sorgenti e campi ==")
    a_("  comune ztl_csv.zip: WKT_GEOM (EPSG:3003), DENOMINAZI, ORA_INIZIO, ORA_FINE, "
      "SOSPENS, ORDINANZA")
    a_("  5t_access_control_20261014.xml: poligono lat/lon, <weekday start_time end_time>, "
      "validita' 2022-2024")
    a_("  aree_pedonali_csv.zip: WKT_GEOM (EPSG:3003), DENOMINAZI, CIRCOSCRIZ, SUPERFICIE")
    a_("")
    a_("== Zone unificate ==")
    for z in unificate:
        a_(f"  {z['nome']:12s} fonti={','.join(z['fonti'])}  validita={z['validita']}  "
           f"orari={[(o['giorni'],o['inizio'],o['fine']) for o in z['orari']]}  "
           f"fonte_vecchia={z['fonte_vecchia']}  poligoni={len(z['poligoni'])}")
    a_(f"  aree pedonali: {len(pedonali)} (somma superfici dichiarate: "
       f"{sum(1 for _ in pedonali)} elementi)")
    a_("")
    a_("== Sensori 5T dentro una ZTL o un'area pedonale ==")
    sens = json.loads((PROC / "sensori_corridoi_v2.json").read_text(encoding="utf-8"))["sensori"]
    n_dentro = 0
    for lcd, s in sens.items():
        la, lo = s.get("lat"), s.get("lon")
        if la is None:
            continue
        z_in = dentro((lo, la), ztl_tree, ztl_polys)
        p_in = dentro((lo, la), ped_tree, ped_polys)
        if z_in or p_in:
            n_dentro += 1
            a_(f"  {lcd:>8} {str(s.get('via'))[:34]:34s} ztl={z_in} pedonale={p_in}")
    a_(f"  totale sensori dentro ZTL o pedonale: {n_dentro}")
    a_("")
    a_("== Controlli su strade note (quota in ZTL / pedonale) ==")
    per_nome = {}
    for r in righe_csv:
        nome = (r["nome"] or "").lower()
        if r["comune"] == "Torino":
            per_nome.setdefault(nome, []).append(r)
    for chiave in ["roma", "castello", "montebello", "san massimo", "cairoli",
                   "vittorio emanuele ii", "garibaldi", "po"]:
        voci = [v for k, vv in per_nome.items() if chiave in k for v in vv]
        if not voci:
            a_(f"  {chiave:22s}: nessuna tratta col nome")
            continue
        fz = max(v["ztl_frazione"] for v in voci)
        fp = max(v["pedonale_frazione"] for v in voci)
        zone_n = sorted({z for v in voci for z in v["ztl_zone"]})
        a_(f"  {chiave:22s}: {len(voci):4d} tratte  ztl_frazione max {fz:.2f}  "
           f"pedonale max {fp:.2f}  zone {','.join(zone_n) or '-'}")
    a_("")
    a_("  Confronto con la conoscenza di Leo (solo riferimento, NON taratura):")
    a_("   - Via Roma: pedonale (atteso pedonale_frazione alta).")
    a_("   - Piazza Castello: area pedonale + centro ZTL.")
    a_("   - Via Montebello: ZTL con molte universita', in parte pedonale.")
    a_("   - Via San Massimo: dentro la ZTL Centrale (Leo: 'trafficata nonostante la ZTL').")
    a_("   - Corso Cairoli: tratto verso Piazza Vittorio; piu' avanti inizia la ZTL.")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))
    print(f"\nScritti {OUT/'ztl_unificata.json'}, {OUT/'tratte_ztl.csv'}, {RAPPORTO}")


if __name__ == "__main__":
    main()
