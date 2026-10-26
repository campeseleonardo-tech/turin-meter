#!/usr/bin/env python3
"""08_prepara_omi.py

Piano OMI (O1): integra le quotazioni OMI 2025/2 nella mappa.

Input (sola lettura; NON modificare):
- data/raw/omi_2025_2/*_VALORI.csv
- data/raw/omi_2025_2/*_ZONE.csv
- data/raw/omi_2025_2/TO20252/*.kml

Output:
- data/processed/omi_zone.json

Struttura output:
[
  {"c": PRO_COM,
   "zone": [
      {"z":"B1","n":"ROMA","f":"B",
       "g":[ anello [[lat,lon]...], ... ],
       "v": {"ab":[cmin,cmax,lmin,lmax], ...}}
   ]}
]

Regole (da sviluppo/MEMORIA_PROGETTO.md):
- comuni: quelli dell'area mappa (= i "c" in sezioni_torino.json); Moncucco (5070) resta fuori;
- poligoni: lon,lat -> [lat,lon], 5 decimali; semplifica Douglas-Peucker 20 m (come 05_prepara_sezioni.py);
- MultiGeometry: tutti i Polygon diventano anelli; innerBoundaryIs tenuti come anelli (verranno disegnati pieni);
- valori: per ogni (comune,zona,tipologia) tieni NORMALE se esiste, altrimenti il primo trovato;
- tipologie: ab/as/ae/vi/bo/pa/ps/ne/uf/la/ci/in/ma/cc (mappa codici come sotto).
"""

import csv
import json
import math
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


AQUI = Path(__file__).resolve().parent


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    candidata = Path.home() / "Desktop" / "GTT"
    return candidata if candidata.is_dir() else AQUI.parent


RADICE = trova_radice()
RAW = RADICE / "data" / "raw" / "omi_2025_2"
OUT = RADICE / "data" / "processed" / "omi_zone.json"
SEZIONI = RADICE / "data" / "processed" / "sezioni_torino.json"

VALORI = next(iter(sorted(RAW.glob("*_VALORI.csv"))), RAW / "VALORI.csv")   # il nome del file porta un codice di richiesta: si cerca per suffisso
ZONE = next(iter(sorted(RAW.glob("*_ZONE.csv"))), RAW / "ZONE.csv")
KML_DIR = RAW / "TO20252"

TOLL_M = 20.0
TOLL_MERGE = 0.02

TIP_MAP = {
    20: "ab",  # Abitazioni civili
    19: "as",  # Abitazioni signorili
    21: "ae",  # Abitazioni di tipo economico
    1: "vi",   # Ville e Villini
    13: "bo",  # Box
    14: "pa",  # Posti auto coperti
    15: "ps",  # Posti auto scoperti
    5: "ne",   # Negozi
    6: "uf",   # Uffici
    10: "la",  # Laboratori
    7: "ci",   # Capannoni tipici
    8: "in",   # Capannoni industriali
    9: "ma",   # Magazzini
    17: "cc",  # Centri commerciali
}


def pro_com_da_istat(s):
    """Comune_ISTAT -> PRO_COM (regole in memoria)."""
    try:
        n = int(str(s).strip())
    except ValueError:
        return None
    return n - 1000000 if n >= 1000000 else n


def _float(v):
    try:
        return float(str(v).strip().replace(",", "."))
    except ValueError:
        return None


def dp_keep(pts, tol):
    """Douglas-Peucker: ritorna maschera keep per lista di (x,y)."""
    if len(pts) < 4:
        return [True] * len(pts)
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
            st.append((a, mi))
            st.append((mi, b))
    return keep


def dp_anello(ring_latlon, tol_m):
    """Semplifica un anello chiuso: ring_latlon = [(lat,lon), ...]."""
    if len(ring_latlon) < 6:
        return ring_latlon
    if ring_latlon[0] != ring_latlon[-1]:
        ring_latlon = ring_latlon + [ring_latlon[0]]
    if len(ring_latlon) < 6:
        return ring_latlon
    lat0 = ring_latlon[0][0]
    coslat = math.cos(math.radians(lat0))
    k = 111200.0
    xy = [(lo * k * coslat, la * k) for la, lo in ring_latlon]
    x0, y0 = xy[0]
    m = max(range(1, len(xy) - 1), key=lambda i: (xy[i][0] - x0) ** 2 + (xy[i][1] - y0) ** 2)

    keepL = dp_keep(xy[: m + 1], tol_m)
    keepR = dp_keep(xy[m:], tol_m)
    left = [p for p, k0 in zip(ring_latlon[: m + 1], keepL) if k0]
    right = [p for p, k0 in zip(ring_latlon[m:], keepR) if k0]
    out = left[:-1] + right
    if not out:
        out = ring_latlon
    if out[0] != out[-1]:
        out.append(out[0])
    return out


def parse_coords(txt):
    """<coordinates> -> lista (lat,lon)."""
    if not txt:
        return []
    out = []
    for trip in str(txt).strip().replace("\n", " ").split():
        p = trip.split(",")
        if len(p) < 2:
            continue
        try:
            lo = float(p[0]); la = float(p[1])
        except ValueError:
            continue
        out.append((la, lo))
    return out


def strip_apici(s):
    s = (s or "").strip()
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    return s


def leggi_area_comuni():
    if not SEZIONI.is_file():
        sys.exit("Manca data/processed/sezioni_torino.json: lancia prima 05_prepara_sezioni.py")
    sez = json.loads(SEZIONI.read_text(encoding="utf-8"))
    return {int(s.get("c", 0)) for s in sez if int(s.get("c", 0)) > 0}


def main():
    if not (VALORI.is_file() and ZONE.is_file() and KML_DIR.is_dir()):
        sys.exit("ERRORE: file OMI non trovati in data/raw/omi_2025_2. Non stanno in git (licenza non chiara): scarica a mano le quotazioni "
                 "(due CSV) e i perimetri (cartella TO20252 con i KML) dal servizio Forniture dati OMI dell'Agenzia delle Entrate; "
                 "indirizzi in docs/en/METHODS.md. Poi rilancia questo script.")

    comuni_area = leggi_area_comuni()  # atteso: 69 comuni (include Moncucco 5070)

    # --- 1) VALORI: elenco zone + valori per tipologia
    pro_by_com = {}        # Comune_amm -> PRO_COM
    fascia_by_key = {}     # (Comune_amm, Zona) -> Fascia
    v_by_key = defaultdict(dict)  # (Comune_amm, Zona) -> {tip: [cmin,cmax,lmin,lmax]}
    scelto = {}            # (Comune_amm, Zona, tip) -> stato scelto

    with open(VALORI, encoding="utf-8", newline="") as f:
        next(f)  # titolo
        rd = csv.DictReader(f, delimiter=";")
        for r in rd:
            pro = pro_com_da_istat(r.get("Comune_ISTAT"))
            if pro is None or pro not in comuni_area:
                continue
            com = (r.get("Comune_amm") or "").strip()
            zon = (r.get("Zona") or "").strip()
            if not com or not zon:
                continue
            pro_by_com.setdefault(com, pro)
            key = (com, zon)
            fascia_by_key.setdefault(key, (r.get("Fascia") or "").strip())

            try:
                cod = int(str(r.get("Cod_Tip") or "").strip())
            except ValueError:
                continue
            tip = TIP_MAP.get(cod)
            if not tip:
                continue
            st = (r.get("Stato") or "").strip().upper()
            cmin = _float(r.get("Compr_min")); cmax = _float(r.get("Compr_max"))
            lmin = _float(r.get("Loc_min")); lmax = _float(r.get("Loc_max"))
            if None in (cmin, cmax, lmin, lmax):
                continue

            kk = (com, zon, tip)
            prev = scelto.get(kk)
            if prev == "NORMALE":
                continue
            if prev is None or st == "NORMALE":
                v_by_key[key][tip] = [cmin, cmax, lmin, lmax]
                scelto[kk] = st or ""

    comuni_con_omi = sorted({pro_by_com[k[0]] for k in v_by_key.keys()})
    mancanti_comuni = sorted(c for c in comuni_area if c not in set(comuni_con_omi))
    miss_ratio = len(mancanti_comuni) / len(comuni_area) if comuni_area else 0
    print(f"OMI: comuni area {len(comuni_area)} (atteso 69); comuni coperti {len(comuni_con_omi)} (atteso 68)")
    if mancanti_comuni:
        print(f"  comuni area senza OMI: {mancanti_comuni}")
    if miss_ratio > TOLL_MERGE:
        sys.exit(f"ERRORE: comuni senza OMI oltre soglia {TOLL_MERGE:.2%} ({len(mancanti_comuni)}/{len(comuni_area)})")

    # --- 2) ZONE: nomi zona
    nome_by_key = {}   # (Comune_amm, Zona) -> nome senza apici
    with open(ZONE, encoding="utf-8", newline="") as f:
        next(f)
        rd = csv.DictReader(f, delimiter=";")
        for r in rd:
            com = (r.get("Comune_amm") or "").strip()
            zon = (r.get("Zona") or "").strip()
            key = (com, zon)
            if key in v_by_key:
                nome_by_key[key] = strip_apici(r.get("Zona_Descr"))

    # --- 3) KML: geometrie
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    g_by_key = {k: [] for k in v_by_key.keys()}   # (Comune_amm,Zona) -> [anelli]
    comuni_amm_necessari = sorted({k[0] for k in v_by_key.keys()})
    for com in comuni_amm_necessari:
        f = KML_DIR / f"{com}.kml"
        if not f.is_file():
            continue
        rad = ET.parse(f).getroot()
        for pm in rad.findall(".//k:Placemark", ns):
            data = {}
            for d in pm.findall(".//k:ExtendedData/k:Data", ns):
                n = d.attrib.get("name")
                if not n:
                    continue
                data[n] = (d.findtext("k:value", default="", namespaces=ns) or "").strip()
            codcom = data.get("CODCOM")
            codzona = data.get("CODZONA")
            if not codcom or not codzona:
                continue
            key = (codcom, codzona)
            if key not in g_by_key:
                continue
            rings = []
            for poly in pm.findall(".//k:Polygon", ns):
                outer = poly.find("k:outerBoundaryIs/k:LinearRing/k:coordinates", ns)
                if outer is not None:
                    r = parse_coords(outer.text)
                    if r:
                        r = dp_anello(r, TOLL_M)
                        rings.append([[round(la, 5), round(lo, 5)] for la, lo in r])
                for inner in poly.findall("k:innerBoundaryIs/k:LinearRing/k:coordinates", ns):
                    r = parse_coords(inner.text)
                    if r:
                        r = dp_anello(r, TOLL_M)
                        rings.append([[round(la, 5), round(lo, 5)] for la, lo in r])
            if rings:
                g_by_key[key].extend(rings)

    # --- 4) compongo output
    zone_senza_poly = [k for k, g in g_by_key.items() if not g]
    if len(zone_senza_poly) / max(1, len(g_by_key)) > TOLL_MERGE:
        sys.exit(f"ERRORE: troppe zone senza poligono ({len(zone_senza_poly)}/{len(g_by_key)})")

    comuni_out = defaultdict(list)  # pro_com -> [zone]
    for (com, zon), v in sorted(v_by_key.items(), key=lambda x: (pro_by_com.get(x[0][0], 0), x[0][1])):
        pro = pro_by_com[com]
        n = nome_by_key.get((com, zon), "")
        fascia = fascia_by_key.get((com, zon), "")
        comuni_out[pro].append({
            "z": zon,
            "n": n,
            "f": fascia,
            "g": g_by_key.get((com, zon), []),
            "v": v,
        })

    out = [{"c": pro, "zone": comuni_out[pro]} for pro in sorted(comuni_out)]

    # --- 5) controlli richiesti
    print(f"  zone (tutte): {sum(len(c['zone']) for c in out)}")
    print(f"  zone senza poligono: {len(zone_senza_poly)} (atteso 0)")
    tor = next((c for c in out if c["c"] == 1272), None)
    if not tor:
        sys.exit("ERRORE: Torino (1272) non presente in output")
    print(f"  Torino zone: {len(tor['zone'])} (atteso 47)")
    b1 = next((z for z in tor["zone"] if z["z"] == "B1"), None)
    if not b1:
        sys.exit("ERRORE: zona Torino B1 non trovata")
    print(f"  Torino B1 nome: {b1['n']} (atteso ROMA)")
    print(f"  Torino B1 ab: {b1['v'].get('ab')} (atteso [2900, 4400, 10.5, 15.7])")

    # scrivi output
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"), encoding="utf-8")
    print(f"File scritto: {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
