#!/usr/bin/env python3
"""
SUPERATO dallo script 84_risultato6_parcheggi.py (vedi sviluppo/note_tecniche/R6_parcheggi.md).
Resta per confronto e perche' lo script 84 ne riusa le funzioni (esagoni, profili, nomi): non cancellarlo.
Il suo main() NON si lancia piu': cerca uno script (la versione 2 del R6) che non c'e' piu'.

80_porte_interscambio.py  -  Risultato 6, versione con le AREE e i PUNTI PRIORITARI: dove mancano
parcheggi per lasciare l'auto vicino alle fermate importanti, e quali parcheggi grandi potrebbero
ampliarsi.

Domande a cui risponde
----------------------
  1. Quali fermate importanti hanno almeno 50 posti entro 200 m? (copertura, qualunque sia il parcheggio)
  2. In quali aree (celle esagonali di circa 2 km2) mancano parcheggi?
  3. Dove servirebbe di piu' un parcheggio, o ingrandire uno che c'e'? (20 punti prioritari)

Cosa fa
-------
  - Fermate importanti: i 378 luoghi del punteggio alto (scenario S2 di scenari.json).
  - Parcheggi trovati e considerati: tutti i tipi aperti (interscambio, garage 5T, park&ride OSM,
    parcheggi pubblici OSM). Posti = dichiarati, altrimenti stimati dalla superficie (25 m2 a posto).
  - Classi delle fermate, sui POSTI NOMINALI entro 200 m: «Nessun parcheggio» (0), «Pochi posti»
    (1-49), «50 posti o piu'» (50+). Il riempimento NON cambia le classi.
  - Riempimento: solo misura 5T (media feriale 10-16, giorni validi >= 2). Serve per colorare i
    parcheggi mostrati e per i profili. Le osservazioni a mano (data/ref/parcheggi_osservazioni.json)
    NON entrano nei dati: solo controllo a posteriori nel rapporto.
  - Parcheggi mostrati: almeno 100 posti entro 400 m da una fermata importante o da un nodo di trasporto importante
    (metro, treno, capolinea, >= 20 corse/ora), piu' tutti i garage 5T con dati di riempimento.
  - Aree: celle esagonali (lato 900 m, a punta in alto) sull'area delle fermate importanti.
    Quota senza 50 posti = (Nessun + Pochi) / fermate della cella. Critica >= 60%, Scarsa 30-59%,
    Buona < 30%. Meno di 3 fermate = dato indicativo.
  - 20 punti prioritari: fermate con «Nessun parcheggio» o «Pochi posti» raggruppate a 1 km di
    diametro (linkage complete), ordinate per punteggio; per ognuno i parcheggi >= 100 posti entro
    600 m (candidati ad ampliarsi).
  - Direzioni d'ingresso (8 settori da Piazza Castello): solo RIFERIMENTO per la scheda.
    Auto in entrata dai microdati IMQ 2022 (script 73), domanda = auto x quota (26%).

Cosa legge
----------
  data/processed/risultato6_v2/scenari.json, luoghi.json, parcheggi.json, riempimento.json,
  segnali.json, nodi.json
  data/processed/imq/spostamenti.csv (via script 73), data/processed/imq_zone.json,
  data/processed/imq_zone_geo.json (solo centroidi per le direzioni)
  data/ref/parcheggi_osservazioni.json (solo controllo a posteriori)
  scripts/73, 75 (soglie fermate), 75 nodi: funzioni riusate

Cosa scrive
-----------
  data/processed/risultato6_v2/porte.json
  docs/rapporti/RAPPORTO_R6_PORTE.txt

Come si lancia
--------------
  python scripts\\80_porte_interscambio.py
  python scripts\\80_porte_interscambio.py --soglie-aree 60,30
"""
import argparse
import importlib.util
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage

AQUI = Path(__file__).resolve().parent


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
P = RADICE / "data" / "processed" / "risultato6_v2"
SCENARI = P / "scenari.json"
LUOGHI = P / "luoghi.json"
PARCHEGGI = P / "parcheggi.json"
RIEMPIMENTO = P / "riempimento.json"
SEGNALI = P / "segnali.json"
NODI = P / "nodi.json"
OSSERVAZIONI = RADICE / "data" / "ref" / "parcheggi_osservazioni.json"
ZONE = RADICE / "data" / "processed" / "imq_zone.json"
ZONE_GEO = RADICE / "data" / "processed" / "imq_zone_geo.json"
S73 = AQUI / "73_segnali_criticita.py"
S75 = AQUI / "risultato6_v2.py"   # script tolto: main() non si lancia piu'
OUT = P / "porte.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6_PORTE.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

SCENARIO = "S2"
CENTRO_LAT, CENTRO_LON = 45.0711, 7.6857
LAT_RIF = 45.07
M_GRADO = 111000.0
COS_LAT = math.cos(math.radians(45.07))
SETTORI_NOMI = ["Nord", "Nord-est", "Est", "Sud-est", "Sud", "Sud-ovest", "Ovest", "Nord-ovest"]
N_SETTORI = 8
RAGGIO_M = 200.0
POSTI_M2 = 25.0
POSTI_COPERTA = 50
TIPI_CONSIDERATI = ("interscambio_ufficiale", "garage_5t", "park_ride_osm", "osm_pubblico")
MIN_POSTI_MOSTRATO = 100
RAGGIO_MOSTRATO_M = 400.0
RAGGIO_CANDIDATI_M = 600.0
LATO_CELLA_M = 900.0
SOGLIE_AREE = (60, 30)
MIN_FERMATE_AREA = 3
SOGLIA_PIENO, SOGLIA_LIBERO = 0.85, 0.50
MIN_GIORNI_VALIDI = 2
CAT_AREA = ("Critica", "Scarsa", "Buona")
CAT_DIR = ("Bastano", "Quasi", "Pochi", "Mancano")
CLASSI = ("Nessun parcheggio", "Pochi posti", "50 posti o più")
DESCR_REGOLA = {
    "feriali": "si riempie nei giorni feriali",
    "weekend": "si riempie di giorno anche nel weekend",
    "notte": "è più pieno di notte che di giorno",
    "fermo": "il valore non cambia: forse il contatore è fermo",
    "stabile": "sempre intorno allo stesso valore",
    "quasi_pieno": "sempre quasi pieno",
    "irregolare": "andamento irregolare",
}
PALAVELA_OSM = 104393338
R = 6371000.0


def it(n, dec=0):
    if n is None:
        return "n.d."
    s = f"{n:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x):
    return "n.d." if x is None else it(x * 100, 0) + "%"


def nome_normale(denom):
    d = re.sub(r"^\d+\s+", "", denom or "").strip()
    d = re.sub(r"^Torino-\s*", "", d).strip()
    if d.isupper():
        d = d.title().replace(" Di ", " di ").replace(" Del ", " del ").replace(" Fs", " FS")
    return d


def nome_fermata(n):
    """'Fermata 6181 - PESSIONE CAP' -> 'PESSIONE CAP' (senza prefisso e codice)."""
    return re.sub(r"^Fermata \d+\s*-\s*", "", n or "").strip()


def settore_di(lat, lon, n=N_SETTORI):
    dx = (lon - CENTRO_LON) * COS_LAT
    dy = lat - CENTRO_LAT
    passo = 360.0 / n
    angolo = (math.degrees(math.atan2(dx, dy)) + 360 + passo / 2) % 360
    return int(angolo // passo)


def settore_angoli(i, n=N_SETTORI):
    passo = 360.0 / n
    return round(i * passo - passo / 2, 1), round(i * passo + passo / 2, 1)


def classe_nominale(posti):
    if posti == 0:
        return CLASSI[0]
    if posti < POSTI_COPERTA:
        return CLASSI[1]
    return CLASSI[2]


def categoria_dir(copertura):
    if copertura is None or copertura >= 1:
        return CAT_DIR[0]
    if copertura >= 0.5:
        return CAT_DIR[1]
    if copertura >= 0.2:
        return CAT_DIR[2]
    return CAT_DIR[3]


def categoria_area(quota, soglie):
    if quota >= soglie[0] / 100:
        return CAT_AREA[0]
    if quota >= soglie[1] / 100:
        return CAT_AREA[1]
    return CAT_AREA[2]


def carica_modulo(percorso, nome):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def dist_matrix(parcheggi, luoghi):
    """Distanze in metri (parcheggi x luoghi), formula della sfera."""
    plat = np.radians(np.array([p["lat"] for p in parcheggi]))
    plon = np.radians(np.array([p["lon"] for p in parcheggi]))
    slat = np.radians(np.array([l["lat"] for l in luoghi]))
    slon = np.radians(np.array([l["lon"] for l in luoghi]))
    dlat = plat[:, None] - slat[None, :]
    dlon = plon[:, None] - slon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(plat)[:, None] * np.cos(slat)[None, :] * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def _anelli_geo(g):
    if isinstance(g, str):
        g = json.loads(g)
    if g and isinstance(g[0][0], (int, float)):
        return [g]
    if g and isinstance(g[0][0][0], (int, float)):
        return g
    return [anello for poligono in g for anello in poligono]


def proietta(lat, lon):
    """Metri su un piano locale: x verso est, y verso nord."""
    return lon * M_GRADO * COS_LAT, lat * M_GRADO


def inverti(x, y):
    return y / M_GRADO, x / (M_GRADO * COS_LAT)


def cella_di(x, y, a=LATO_CELLA_M):
    """Coordinate assiali (q, r) della cella esagonale a punta in alto che contiene (x, y)."""
    q = (math.sqrt(3) / 3 * x - y / 3) / a
    r = (2 / 3 * y) / a
    xc, zc = q, r
    yc = -xc - zc
    rx, ry, rz = round(xc), round(yc), round(zc)
    dx, dy, dz = abs(rx - xc), abs(ry - yc), abs(rz - zc)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return int(rx), int(rz)


def centro_cella(q, r, a=LATO_CELLA_M):
    return a * math.sqrt(3) * (q + r / 2), a * 1.5 * r


def vertici_cella(q, r, a=LATO_CELLA_M):
    cx, cy = centro_cella(q, r, a)
    out = []
    for k in range(6):
        ang = math.radians(60 * k - 30)
        lat, lon = inverti(cx + a * math.cos(ang), cy + a * math.sin(ang))
        out.append([round(lat, 5), round(lon, 5)])
    return out


def _profilo(dizionario):
    if not dizionario:
        return None
    return [round(float(dizionario.get(str(h), 0)), 3) for h in range(24)]


def haversine_vettore(lat0, lon0, lats, lons):
    p1 = math.radians(lat0)
    p2 = np.radians(lats)
    dphi = p2 - p1
    dl = np.radians(lons - lon0)
    a = np.sin(dphi / 2) ** 2 + math.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def descrivi_profilo(pf, pw):
    """Descrizione in parole di un garage (regole in ordine): N = notte 2-5, G = giorno 10-16, W = weekend 10-16,
    in % di riempimento medio feriale; amp = differenza tra la punta piu' alta e la piu' bassa dell'ora."""
    N = 100 * float(np.mean([pf[h] for h in (2, 3, 4, 5)]))
    G = 100 * float(np.mean([pf[h] for h in range(10, 17)]))
    W = 100 * float(np.mean([pw[h] for h in range(10, 17)])) if pw else None
    amp = 100 * (max(pf) - min(pf))
    n, g = round(N), round(G)
    if G - N >= 20 and (W is None or G - W >= 10):
        return "feriali", f"si riempie nei giorni feriali: {n}% di notte, {g}% di giorno"
    if G - N >= 20 and W is not None and G - W < 10:
        return "weekend", f"si riempie di giorno anche nel weekend: {n}% di notte, {g}% di giorno"
    if N - G >= 10:
        return "notte", f"è più pieno di notte che di giorno: {n}% di notte, {g}% di giorno"
    if amp < 6:
        if G < 15 or G > 85:
            return "fermo", f"il valore non cambia ({g}%): forse il contatore è fermo"
        return "stabile", f"sempre intorno al {g}%"
    if G >= 85 and N >= 70:
        return "quasi_pieno", f"sempre quasi pieno: {n}% di notte, {g}% di giorno"
    return "irregolare", f"andamento irregolare: {n}% di notte, {g}% di giorno"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--soglie-aree", default="60,30", help="soglie Critica,Scarsa in percentuale (default 60,30)")
    args = ap.parse_args()
    soglie_aree = tuple(float(x) for x in args.soglie_aree.split(","))

    for f in (SCENARI, LUOGHI, PARCHEGGI, RIEMPIMENTO, SEGNALI, NODI, OSSERVAZIONI, ZONE, ZONE_GEO, S73, S75):
        if not f.exists():
            sys.exit(f"Manca: {f}")

    print("leggo gli input...")
    sc = json.loads(SCENARI.read_text(encoding="utf-8"))
    luoghi_all = {l["id_luogo"]: l for l in json.loads(LUOGHI.read_text(encoding="utf-8"))["luoghi"]}
    pk = json.loads(PARCHEGGI.read_text(encoding="utf-8"))
    parcheggi_all = pk["parcheggi"]
    riemp = json.loads(RIEMPIMENTO.read_text(encoding="utf-8"))
    segnali = json.loads(SEGNALI.read_text(encoding="utf-8"))
    nodi_all = json.loads(NODI.read_text(encoding="utf-8"))["luoghi"]
    obs_file = json.loads(OSSERVAZIONI.read_text(encoding="utf-8"))
    ZONE_INFO = {z["cod"]: z for z in json.loads(ZONE.read_text(encoding="utf-8"))}
    geo = json.loads(ZONE_GEO.read_text(encoding="utf-8"))
    riemp_per_5t = {r["id_5t"]: r for r in riemp["parcheggi"]}

    quota = segnali["f"]["totale"] / segnali["c2_totale"]

    def luogo_da(l, punteggio):
        return {"id_luogo": l["id_luogo"], "nome": l["nome"], "lat": l["lat"], "lon": l["lon"],
                "zona_imq": l["zona_imq"], "zona_nome": nome_normale(ZONE_INFO.get(l["zona_imq"], {}).get("denom", "")),
                "punteggio": punteggio}

    fermate_in = [luogo_da(luoghi_all[c["id_luogo"]], c["punteggio"]) for c in sc["scenari"][SCENARIO]["critici"]]
    print(f"fermate importanti: {len(fermate_in)}")

    # nodi forti (metro, treno, capolinea, frequente)
    nodi_forti = [n for n in nodi_all if n.get("nodo_forte")]
    print(f"nodi forti: {len(nodi_forti)}")

    # parcheggi
    parcheggi = [p for p in parcheggi_all if p["tipo"] in TIPI_CONSIDERATI]
    print(f"parcheggi trovati {len(parcheggi_all)}, considerati {len(parcheggi)}")

    def posti_con(p, m2=POSTI_M2):
        if p.get("posti_dichiarati"):
            return int(p["posti_dichiarati"])
        if m2 == POSTI_M2:
            return int(p["posti_stimati"] or 0)
        if p.get("superficie_m2"):
            return int(round(p["superficie_m2"] / m2))
        return int(p["posti_stimati"] or 0)

    def stato_di(p):
        r = riemp_per_5t.get(p.get("id_5t")) if p.get("id_5t") else None
        if r and r.get("G_giorno_feriale") is not None and len(r.get("giorni_validi", [])) >= MIN_GIORNI_VALIDI:
            g = float(r["G_giorno_feriale"])
            stato = "pieno" if g >= SOGLIA_PIENO else "libero" if g < SOGLIA_LIBERO else "a_meta"
            return {"stato": stato, "fonte_stato": "misura", "riempimento_giorno": round(g, 4),
                    "fonte_testo": "5T, media feriale 10-16"}
        return {"stato": "non_misurato", "fonte_stato": None, "riempimento_giorno": None, "fonte_testo": None}

    info_p = {p["id"]: stato_di(p) for p in parcheggi}
    posti = np.array([posti_con(p) for p in parcheggi], dtype=float)

    # distanze: fermate importanti e nodi forti
    D_f = dist_matrix(parcheggi, fermate_in)
    D_n = dist_matrix(parcheggi, nodi_forti)

    # ---- classi delle fermate (posti nominali entro 200 m) ----
    def classi_fermate(luoghi_c, raggio=RAGGIO_M, soglia=POSTI_COPERTA, m2=POSTI_M2):
        dist = dist_matrix(parcheggi, luoghi_c)
        pos = np.array([posti_con(p, m2) for p in parcheggi], dtype=float)
        pn = (dist <= raggio).T @ pos
        return dist, pn

    dist_base, pn_base = classi_fermate(fermate_in)
    fermate = []
    for si, l in enumerate(fermate_in):
        sel = np.nonzero(dist_base[:, si] <= RAGGIO_M)[0]
        pn = int(pn_base[si])
        fermate.append({
            "id": l["id_luogo"], "nome": l["nome"], "lat": round(l["lat"], 5), "lon": round(l["lon"], 5),
            "zona": l["zona_imq"], "zona_nome": l["zona_nome"], "punteggio": round(l["punteggio"], 2),
            "classe": classe_nominale(pn), "posti_nominali_200": pn,
            "_sel": sel, "_si": si,
        })
    conta = Counter(f["classe"] for f in fermate)
    n0, n1, n2 = conta[CLASSI[0]], conta[CLASSI[1]], conta[CLASSI[2]]
    print(f"  fermate: nessun parcheggio {n0}, pochi posti {n1}, 50+ {n2}")

    # ---- auto in entrata (script 73) e direzioni (riferimento) ----
    print("auto in entrata: leggo i microdati IMQ (script 73)...")
    m73 = carica_modulo(S73, "segnali_criticita_73")
    _righe, c2, c2_int, _c3, tot_c2, n_c2 = m73.zone_c2_c3()
    c2_nonq = {z: v for z, v in c2.items() if not z.startswith("Q")}
    print(f"  auto in entrata al mattino: {tot_c2:.0f} ({n_c2} interviste)")
    centroidi = {}
    for g in geo:
        punti = [q for anello in _anelli_geo(g["g"]) for q in anello]
        centroidi[g["cod"]] = (sum(p[0] for p in punti) / len(punti), sum(p[1] for p in punti) / len(punti))

    # parcheggi entro 200 m da una fermata importante, piu' i garage 5T (come prima, per la direzione)
    idx_dir = sorted(set(np.nonzero((D_f <= RAGGIO_M).any(axis=1))[0].tolist())
                     | {i for i, p in enumerate(parcheggi) if p["tipo"] == "garage_5t"})

    def calcola_direzioni(n_sett=N_SETTORI, m2=POSTI_M2, quota_v=quota):
        pos = np.array([posti_con(p, m2) for p in parcheggi], dtype=float)
        out = []
        for k in range(n_sett):
            zone_k = sorted([(z, v) for z, v in c2_nonq.items()
                             if settore_di(*centroidi[z], n=n_sett) == k], key=lambda x: -x[1])
            auto_k = sum(v for _, v in zone_k)
            int_k = sum(c2_int.get(z, 0) for z, _ in zone_k)
            idir = [i for i in idx_dir if settore_di(parcheggi[i]["lat"], parcheggi[i]["lon"], n_sett) == k]
            posti_k = float(sum(pos[i] for i in idir))
            dom = auto_k * quota_v
            cop = posti_k / dom if dom > 0 else None
            out.append({
                "codice": k, "nome": SETTORI_NOMI[k] if n_sett == 8 else f"Settore {k + 1}",
                "angolo_da": settore_angoli(k, n_sett)[0], "angolo_a": settore_angoli(k, n_sett)[1],
                "comuni_principali": [nome_normale(ZONE_INFO.get(z, {}).get("denom", z)) for z, _ in zone_k[:3]],
                "auto_in_entrata": round(auto_k, 1), "interviste": int_k, "domanda": round(dom, 1),
                "posti_nominali": int(posti_k), "copertura": round(cop, 3) if cop is not None else None,
                "mancano": round(max(0.0, dom - posti_k), 1), "categoria": categoria_dir(cop),
            })
        return out

    direzioni = calcola_direzioni()
    direzioni.sort(key=lambda d: (-d["mancano"], d["codice"]))

    # ---- aree esagonali ----
    print("aree esagonali...")
    xy_f = np.array([proietta(f["lat"], f["lon"]) for f in fermate])
    cella_f = []
    for x, y in xy_f:
        cella_f.append(cella_di(x, y))
    gruppi_cella = {}
    for i, c in enumerate(cella_f):
        gruppi_cella.setdefault(c, []).append(i)

    aree = []
    for (q, r), membri in gruppi_cella.items():
        n = len(membri)
        nes = sum(1 for i in membri if fermate[i]["classe"] == CLASSI[0])
        poc = sum(1 for i in membri if fermate[i]["classe"] == CLASSI[1])
        ok = n - nes - poc
        quota_s = (nes + poc) / n
        park = sorted(set(np.nonzero((dist_base[:, membri] <= RAGGIO_M).any(axis=1))[0].tolist()))
        pn_cella = int(sum(posti[i] for i in park))
        pieni = [{"nome": parcheggi[i]["nome"], "posti": int(posti[i])} for i in park
                 if info_p[parcheggi[i]["id"]]["stato"] == "pieno"]
        pieni.sort(key=lambda x: -x["posti"])
        zn = Counter(fermate[i]["zona_nome"] for i in membri if fermate[i]["zona_nome"]).most_common(2)
        cx_, cy_ = centro_cella(q, r)
        clat, clon = inverti(cx_, cy_)
        senza = sorted([fermate[i] for i in membri if fermate[i]["classe"] != CLASSI[2]],
                       key=lambda f: -f["punteggio"])[:5]
        aree.append({
            "id": f"c{q}_{r}", "centro": [round(clat, 5), round(clon, 5)], "poligono": vertici_cella(q, r),
            "n_fermate": n, "nessun": nes, "pochi": poc, "ok": ok,
            "quota_senza": round(quota_s, 3), "categoria": categoria_area(quota_s, soglie_aree),
            "indicativo": n < MIN_FERMATE_AREA,
            "zone_principali": [z for z, _ in zn], "posti_nominali_200": pn_cella,
            "parcheggi_pieni": pieni,
            "fermate_senza": [{"nome": f["nome"], "punteggio": f["punteggio"]} for f in senza],
        })
    aree.sort(key=lambda a: (-a["quota_senza"], -a["n_fermate"]))
    # etichetta: la prima zona principale; una sola area per nome (quella con piu' fermate, a parita' la piu' a nord);
    # le aree indicative (meno di 3 fermate) non hanno etichetta
    for a in aree:
        a["etichetta"] = a["zone_principali"][0] if a["zone_principali"] else None
    migliore = {}
    for a in aree:
        if not a["etichetta"] or a["indicativo"]:
            continue
        chiave = (a["n_fermate"], a["centro"][0])
        cur = migliore.get(a["etichetta"])
        if cur is None or chiave > (cur["n_fermate"], cur["centro"][0]):
            migliore[a["etichetta"]] = a
    for a in aree:
        a["mostra_etichetta"] = migliore.get(a["etichetta"]) is a if a["etichetta"] else False
    print(f"  celle: {len(aree)}")

    # ---- 20 punti prioritari ----
    print("20 punti prioritari (raggruppamento a 1 km)...")
    idx_pr = [i for i, f in enumerate(fermate) if f["classe"] != CLASSI[2]]
    pts = xy_f[idx_pr]
    punti = []
    if len(idx_pr) >= 2:
        Z = linkage(pts, method="complete")
        etichette = fcluster(Z, 1000, "distance")
    else:
        etichette = np.ones(len(idx_pr), dtype=int)
    gruppi = {}
    for k, g in zip(idx_pr, etichette):
        gruppi.setdefault(int(g), []).append(k)
    for g, membri in gruppi.items():
        score = sum(fermate[k]["punteggio"] for k in membri)
        capo = max(membri, key=lambda k: fermate[k]["punteggio"])
        cx_g = float(np.mean([xy_f[k][0] for k in membri]))
        cy_g = float(np.mean([xy_f[k][1] for k in membri]))
        clat, clon = inverti(cx_g, cy_g)
        # parcheggi che servono almeno una fermata del gruppo (ognuno una volta)
        serv = np.nonzero((dist_base[:, membri] <= RAGGIO_M).any(axis=1))[0]
        pn_g = int(sum(posti[i] for i in serv))
        # parcheggi grandi entro 600 m dal centro del gruppo: candidati ad ampliarsi
        dc = haversine_vettore(clat, clon, np.array([p["lat"] for p in parcheggi]),
                               np.array([p["lon"] for p in parcheggi]))
        cand = [i for i in np.nonzero((dc <= RAGGIO_CANDIDATI_M) & (posti >= MIN_POSTI_MOSTRATO))[0]]
        cand.sort(key=lambda i: dc[i])
        punti.append({
            "nome": nome_fermata(fermate[capo]["nome"]), "zona_nome": fermate[capo]["zona_nome"],
            "centro": [round(clat, 5), round(clon, 5)], "n_fermate": len(membri),
            "punteggio": round(score, 1), "posti_nominali_200": pn_g,
            "nessun": sum(1 for k in membri if fermate[k]["classe"] == CLASSI[0]),
            "pochi": sum(1 for k in membri if fermate[k]["classe"] == CLASSI[1]),
            "candidati": [{"nome": parcheggi[i]["nome"], "dist_m": round(float(dc[i])), "posti": int(posti[i]),
                           "stato": info_p[parcheggi[i]["id"]]["stato"]} for i in cand[:8]],
            "fermate": [{"nome": nome_fermata(fermate[k]["nome"]), "punteggio": fermate[k]["punteggio"],
                         "classe": fermate[k]["classe"]}
                        for k in sorted(membri, key=lambda k: -fermate[k]["punteggio"])],
            "_membri": membri,
        })
    punti.sort(key=lambda p: -p["punteggio"])
    punti = punti[:20]
    for i, p in enumerate(punti):
        p["ordine"] = i + 1
        p.pop("_membri")
    print(f"  punti prioritari: {len(punti)}")

    # ---- parcheggi mostrati ----
    nodo_tipo = {}
    d_nodi_400 = D_n <= RAGGIO_MOSTRATO_M
    mostrati = []
    for i, p in enumerate(parcheggi):
        vicino_f = D_f[i].min() <= RAGGIO_MOSTRATO_M
        vicino_n = bool(d_nodi_400[i].any())
        e_garage = p["tipo"] == "garage_5t" and p.get("id_5t") in riemp_per_5t and \
            riemp_per_5t[p["id_5t"]].get("G_giorno_feriale") is not None
        if not ((posti[i] >= MIN_POSTI_MOSTRATO and (vicino_f or vicino_n)) or e_garage):
            continue
        if vicino_n:
            ns = [nodi_forti[j] for j in np.nonzero(d_nodi_400[i])[0]]
            if any(n.get("metro") for n in ns):
                nodo = "metro"
            elif any(n.get("ferro") for n in ns):
                nodo = "treno"
            elif any(n.get("capolinea") for n in ns):
                nodo = "capolinea"
            else:
                nodo = "frequente"
        else:
            nodo = "nessuno"
        mostrati.append(i)
        nodo_tipo[i] = nodo

    # ---- profili dei garage 5T con dati ----
    profili = []
    for r in riemp["parcheggi"]:
        if r.get("profilo_feriale") is None:
            continue
        pf = _profilo(r.get("profilo_feriale"))
        pw = _profilo(r.get("profilo_weekend"))
        if pf is None:
            continue
        regola, testo = descrivi_profilo(pf, pw)
        profili.append({
            "id_5t": r["id_5t"], "nome": r["nome"], "posti": r.get("totale_posti"), "firma": r.get("firma"),
            "regola": regola, "descrizione": testo,
            "giorni_validi": len(r.get("giorni_validi", [])),
            "profilo_feriale": pf, "profilo_weekend": pw,
        })
    profili.sort(key=lambda x: -(x["posti"] or 0))
    desc_5t = {x["id_5t"]: x["descrizione"] for x in profili}
    profili_medi = {}
    for regola in sorted({x["regola"] for x in profili}):
        gruppo = [x for x in profili if x["regola"] == regola and x["profilo_feriale"]]
        if len(gruppo) >= 2:
            media = [round(float(np.mean([x["profilo_feriale"][h] for x in gruppo])), 3) for h in range(24)]
            profili_medi[regola] = {"descrizione": DESCR_REGOLA[regola], "n": len(gruppo), "profilo_feriale": media}

    # parcheggi mostrati, in forma pulita
    parcheggi_out = []
    for i in mostrati:
        p = parcheggi[i]
        st = info_p[p["id"]]
        r = riemp_per_5t.get(p.get("id_5t")) if p.get("id_5t") else None
        origine = ("dichiarati" if p.get("posti_dichiarati") else
                   "stimati (25 m² a posto, ±30%)" if p.get("posti_stimati") else "nessuno")
        parcheggi_out.append({
            "id": p["id"], "nome": p["nome"], "lat": round(p["lat"], 5), "lon": round(p["lon"], 5),
            "posti": int(posti[i]), "posti_origine": origine, "a_pagamento": p["a_pagamento"],
            "stato": st["stato"], "riempimento_giorno": st["riempimento_giorno"],
            "dist_fermata_importante_m": round(float(D_f[i].min())),
            "nodo_vicino": nodo_tipo[i],
            "profilo_feriale": _profilo(r.get("profilo_feriale")) if r else None,
            "profilo_weekend": _profilo(r.get("profilo_weekend")) if r else None,
            "descrizione": desc_5t.get(p.get("id_5t")),
            "_tipo": p["tipo"], "_osm": p.get("id_osm"),
        })
    parcheggi_out.sort(key=lambda x: -x["posti"])

    # parcheggi vicini (max 6) per ogni fermata
    fermate_out = []
    for f in fermate:
        vic = sorted(((parcheggi[j], float(dist_base[j, f["_si"]])) for j in f["_sel"]), key=lambda x: x[1])
        fermate_out.append({k: v for k, v in f.items() if not k.startswith("_")})
        fermate_out[-1]["parcheggi"] = [{"id": p["id"], "nome": p["nome"], "dist_m": round(d),
                                         "posti": posti_con(p), "stato": info_p[p["id"]]["stato"]}
                                        for p, d in vic[:6]]

    # ---- sensibilita' ----
    print("sensibilita'...")
    def conta_classi(pn):
        return {"nessun": int(np.sum(pn == 0)), "pochi": int(np.sum((pn > 0) & (pn < POSTI_COPERTA))),
                "ok": int(np.sum(pn >= POSTI_COPERTA))}

    sens = {"distanza": {}, "posti_coperta": {}, "posti_m2": {}, "quota": {}, "settori": {},
            "soglia_fermate": {}, "soglie_aree": {}}
    for ra in (100, 200, 400):
        _d, pn = classi_fermate(fermate_in, raggio=float(ra))
        sens["distanza"][str(ra)] = conta_classi(pn)
    for su in (30, 50, 100):
        sens["posti_coperta"][str(su)] = {"ok": int(np.sum(pn_base >= su)),
                                          "non_ok": int(np.sum(pn_base < su))}
    for m2 in (20, 25, 33):
        sens["posti_m2"][str(m2)] = [{"nome": d["nome"], "categoria": d["categoria"]}
                                     for d in calcola_direzioni(m2=float(m2))]
    for q in (0.15, 0.26, 0.40):
        sens["quota"][str(int(q * 100))] = {"mancano_pochi": sum(1 for d in calcola_direzioni(quota_v=q)
                                                                  if d["categoria"] in ("Mancano", "Pochi"))}
    for ns in (6, 8, 12):
        sens["settori"][str(ns)] = dict(Counter(d["categoria"] for d in calcola_direzioni(n_sett=ns)))

    # soglia delle fermate (script 75): 5/10/15%
    m75 = carica_modulo(S75, "risultato6_v2_75")
    segnali_u = _segnali_universo(m75)
    controllo_soglia = False
    for pct_v in (5, 10, 15):
        m75.PERCENTILE_CRITICHE = float(100 - pct_v)   # percentile: 90 = il 10% piu' alto
        rr = m75.valuta_scenario(segnali_u, m75.SCENARI[SCENARIO]["segnali"])
        ids = rr["critici"]
        lst = [luogo_da(luoghi_all[i], rr["punteggi"][i]["punteggio"]) for i in ids]
        if pct_v == 10:
            controllo_soglia = len(ids) == 378 and set(ids) == {f["id"] for f in fermate}
        _d, pn = classi_fermate(lst)
        sens["soglia_fermate"][str(pct_v)] = {"fermate": len(lst), **conta_classi(pn)}
    m75.PERCENTILE_CRITICHE = 90.0
    print(f"  10% = 378 fermate e stessi luoghi di S2: {'OK' if controllo_soglia else 'NO'}")

    # soglie aree
    for s_alt in ((50, 25), (66, 33)):
        cnt = Counter(categoria_area(a["quota_senza"], s_alt) for a in aree)
        sens["soglie_aree"][f"{s_alt[0]}/{s_alt[1]}"] = {k: cnt.get(k, 0) for k in CAT_AREA}

    # ---- controlli ----
    somma_auto = sum(d["auto_in_entrata"] for d in direzioni)
    somma_dom = sum(d["domanda"] for d in direzioni)
    n_cella_ok = len(aree)
    fermate_in_cella = sum(a["n_fermate"] for a in aree)
    palavela = next((p for p in parcheggi_all if p.get("id_osm") == PALAVELA_OSM), None)
    palavela_ok = False
    pal_dist = None
    if palavela is not None:
        pal_i = next((i for i, p in enumerate(parcheggi) if p["id"] == palavela["id"]), None)
        if pal_i is not None:
            pal_dist = round(float(D_f[pal_i].min()))
            palavela_ok = any(p["id"] == palavela["id"] for p in parcheggi_out) and posti_con(palavela) >= 500
    ids_mostrati = {p["id"] for p in parcheggi_out}
    garage_con_dati = [p for p in parcheggi if p["tipo"] == "garage_5t" and p.get("id_5t") in riemp_per_5t
                       and riemp_per_5t[p["id_5t"]].get("G_giorno_feriale") is not None]
    tutti_garage = all(p["id"] in ids_mostrati for p in garage_con_dati)
    ctrl = [("378 fermate importanti", len(fermate) == 378),
            ("fermate per classe nominale = 147/59/172", (n0, n1, n2) == (147, 59, 172)),
            ("ogni fermata in una sola area", sum(a["n_fermate"] for a in aree) == 378),
            ("numero di aree tra 55 e 110", 55 <= n_cella_ok <= 110),
            ("somma fermate delle aree = 378", fermate_in_cella == 378),
            ("somma auto in entrata = 95.297", abs(somma_auto - 95297) <= 1),
            ("somma domanda = 24.459", abs(somma_dom - 24459) <= 5),
            ("nessun valore negativo", all(d["mancano"] >= 0 for d in direzioni)),
            ("soglia 10% riproduce le 378 fermate", controllo_soglia),
            ("Palavela (OSM 104393338) tra i parcheggi mostrati, >= 500 posti", palavela_ok),
            ("tutti i garage 5T con dati sono mostrati", tutti_garage),
            ("parcheggi mostrati tra 190 e 240", 190 <= len(parcheggi_out) <= 240)]
    for nome, ok in ctrl:
        print(f"  {'OK ' if ok else 'NO '} {nome}")
    print(f"  parcheggi mostrati: {len(parcheggi_out)}; garage 5T con dati: {len(garage_con_dati)}")

    # ---- riepilogo ----
    print("riepilogo e controlli di dati...")
    tipi = Counter(p["tipo"] for p in parcheggi_all)
    esclusi = {t: tipi[t] for t in ("lungo_strada", "clienti", "privato")}
    n_dich = sum(1 for p in parcheggi if p.get("posti_dichiarati"))
    n_stim = sum(1 for p in parcheggi if not p.get("posti_dichiarati") and p.get("posti_stimati"))
    grandi = [i for i in range(len(parcheggi)) if posti[i] >= POSTI_COPERTA]
    posti_50 = float(sum(posti[i] for i in grandi))
    f200 = [i for i in grandi if (D_f[i] <= RAGGIO_M).any()]
    fn200 = [i for i in grandi if (D_f[i] <= RAGGIO_M).any() or (D_n[i] <= RAGGIO_M).any()]
    # validazione dei 25 m2 (OSM con posti dichiarati, >= 20)
    m2_list = [p["superficie_m2"] / p["posti_dichiarati"] for p in parcheggi
               if p.get("posti_dichiarati") and p["posti_dichiarati"] >= 20 and p.get("superficie_m2")]
    mediana_m2 = float(np.median(m2_list)) if m2_list else None
    q25, q75 = (float(np.percentile(m2_list, 25)), float(np.percentile(m2_list, 75))) if m2_list else (None, None)
    # quota misurata sui parcheggi mostrati (quello che il lettore vede)
    posti_tot_cons = float(sum(p["posti"] for p in parcheggi_out))
    posti_misurati = float(sum(p["posti"] for p in parcheggi_out if p["stato"] != "non_misurato"))
    giorni = sorted({d for r in riemp["parcheggi"] for d in r.get("giorni_validi", [])
                     if datetime.strptime(d, "%Y-%m-%d").weekday() < 5})
    pieni_mostrati = [p for p in parcheggi_out if p["stato"] == "pieno"]
    cat_cnt = Counter(a["categoria"] for a in aree)
    riepilogo = {
        "parcheggi_trovati": len(parcheggi_all), "parcheggi_esclusi": esclusi,
        "parcheggi_considerati": len(parcheggi), "parcheggi_con_50_posti": len(grandi),
        "posti_con_50_posti": int(posti_50), "parcheggi_mostrati": len(parcheggi_out),
        "posti_mostrati": int(sum(p["posti"] for p in parcheggi_out)),
        "parcheggi_50_entro_200_da_fermata": len(f200), "posti_50_entro_200_da_fermata": int(sum(posti[i] for i in f200)),
        "parcheggi_50_entro_200_da_fermata_o_nodo": len(fn200), "posti_50_entro_200_da_fermata_o_nodo": int(sum(posti[i] for i in fn200)),
        "parcheggi_dichiarati": n_dich, "parcheggi_stimati": n_stim,
        "validazione_25m2": {"mediana_m2_per_posto": round(mediana_m2, 1) if mediana_m2 else None,
                             "fascia_25_75": [round(q25, 1), round(q75, 1)] if m2_list else None,
                             "campione": len(m2_list)},
        "verifica_palavela": {"nome": palavela["nome"] if palavela else None,
                              "posti_stimati": int(posti_con(palavela)) if palavela else None,
                              "dist_fermata_importante_m": pal_dist,
                              "nota": "sito turistico: «fino a 600» posti (verifica a mano, non è un dato)"},
        "fermate_nessun_parcheggio": n0, "fermate_pochi_posti": n1, "fermate_50_piu": n2,
        "fermate_senza_50_posti": n0 + n1,
        "aree_per_categoria": {k: cat_cnt.get(k, 0) for k in CAT_AREA}, "n_aree": len(aree),
        "quota_posti_misurati": round(posti_misurati / posti_tot_cons * 100, 1) if posti_tot_cons else None,
        "parcheggi_pieni_n": len(pieni_mostrati), "posti_pieni_totali": int(sum(p["posti"] for p in pieni_mostrati)),
        "garage_con_dati": len(garage_con_dati), "giorni_feriali_validi": giorni,
        "auto_in_entrata_totale": round(somma_auto), "domanda_totale": round(somma_dom),
        "top10_aree": [{k: a[k] for k in ("id", "centro", "n_fermate", "nessun", "pochi", "quota_senza", "categoria",
                                          "indicativo", "zone_principali")} for a in aree[:10]],
        "punti_prioritari_top": [{"ordine": p["ordine"], "nome": p["nome"], "zona": p["zona_nome"],
                                  "n_fermate": p["n_fermate"], "punteggio": p["punteggio"]} for p in punti[:10]],
        "parcheggi_pieni_top10": [{"nome": p["nome"], "posti": p["posti"], "fonte": "5T"}
                                  for p in sorted(pieni_mostrati, key=lambda p: -p["posti"])[:10]],
        "profili_medi": profili_medi,
        "riferimento_direzioni": [{"nome": d["nome"], "codice": d["codice"], "auto_in_entrata": d["auto_in_entrata"],
                                   "domanda": d["domanda"], "posti_nominali": d["posti_nominali"],
                                   "copertura": d["copertura"], "categoria": d["categoria"],
                                   "comuni_principali": d["comuni_principali"]} for d in direzioni],
        "affidabilita": [
            {"voce": "Parcheggi trovati nei dati aperti", "valore": f"{it(len(parcheggi_all))}"},
            {"voce": "Esclusi (lungo strada {}, solo clienti {}, privati {})".format(
                it(esclusi["lungo_strada"]), it(esclusi["clienti"]), it(esclusi["privato"])),
             "valore": f"{it(len(parcheggi_all) - len(parcheggi))}"},
            {"voce": "Considerati nel calcolo", "valore": f"{it(len(parcheggi))}"},
            {"voce": "Con posti dichiarati / stimati a 25 m² a posto", "valore": f"{it(n_dich)} / {it(n_stim)}"},
            {"voce": "Validazione dei 25 m² (mediana m² per posto, OSM con posti dichiarati)",
             "valore": f"{round(mediana_m2, 1) if mediana_m2 else 'n.d.'} (25°-75°: {round(q25, 1) if m2_list else 'n.d.'}-{round(q75, 1) if m2_list else 'n.d.'}; {len(m2_list)} parcheggi)"},
            {"voce": "Quota di posti con riempimento misurato", "valore": f"{it(round(posti_misurati / posti_tot_cons * 100, 1), 1)}%"},
            {"voce": "Garage 5T con dati di riempimento", "valore": f"{len(garage_con_dati)} (giorni feriali: {', '.join(d[8:10] + '/' + d[5:7] for d in giorni)})"},
            {"voce": "Non sappiamo", "valore": "se i parcheggi senza dato di riempimento (es. Fermi) sono pieni; quali parcheggi non sono in OpenStreetMap"},
        ],
    }

    # verifica a posteriori (non entra nei dati)
    verifiche = []
    for o in obs_file["osservazioni"]:
        dentro = [i for i, p in enumerate(parcheggi)
                  if m73.haversine_m(p["lat"], p["lon"], o["lat"], o["lon"]) <= o["raggio_m"]]
        misurati_v = [i for i in dentro if info_p[parcheggi[i]["id"]]["fonte_stato"] == "misura"]
        xo, yo = proietta(o["lat"], o["lon"])
        cella = cella_di(xo, yo)
        area = next((a for a in aree if a["id"] == f"c{cella[0]}_{cella[1]}"), None)
        if area is None:
            vicina = min(fermate, key=lambda f: m73.haversine_m(f["lat"], f["lon"], o["lat"], o["lon"]))
            area = next((a for a in aree if a["id"] == f"c{cella_di(*proietta(vicina['lat'], vicina['lon']))[0]}_"
                         f"{cella_di(*proietta(vicina['lat'], vicina['lon']))[1]}"), None)
            nota_area = "area della fermata importante più vicina"
        else:
            nota_area = "area che contiene il punto"
        dd = next(d for d in direzioni if d["codice"] == settore_di(o["lat"], o["lon"]))
        if not dentro:
            esito = "non può confermare: nessun parcheggio considerato entro il raggio"
        elif not misurati_v:
            esito = "non può confermare: nessun parcheggio entro il raggio trasmette il riempimento"
        else:
            pieni = [i for i in misurati_v if info_p[parcheggi[i]["id"]]["stato"] == "pieno"]
            if len(pieni) == len(misurati_v):
                esito = "il metodo conferma: i parcheggi misurati sono pieni"
            elif not pieni:
                esito = "il metodo non conferma: i parcheggi misurati non sono pieni"
            else:
                esito = "il metodo conferma in parte"
        verifiche.append({
            "nome": o.get("nome_per_leggere", o["id"]), "raggio_m": o["raggio_m"],
            "parcheggi_entro_raggio": len(dentro), "posti_entro_raggio": int(sum(posti[i] for i in dentro)),
            "misurati": [{"nome": parcheggi[i]["nome"], "stato": info_p[parcheggi[i]["id"]]["stato"],
                          "G": info_p[parcheggi[i]["id"]]["riempimento_giorno"]} for i in misurati_v],
            "area": f"{area['categoria']} ({pct(area['quota_senza'])} senza 50 posti)" if area else "nessuna",
            "nota_area": nota_area,
            "direzione": dd["nome"], "direzione_categoria": dd["categoria"], "esito": esito,
        })

    # criteri (testi per la scheda)
    def cnt_sens(k):
        s = sens["distanza"][k]
        return f"{it(s['nessun'] + s['pochi'])}"

    criteri = [
        {"nome": "Fermate importanti", "valore": "il 10% più alto del punteggio, su 4.425 luoghi della Città metropolitana (378 fermate)",
         "perche": "sono i punti dove passa più gente e più mezzi; il punteggio mescola 7 segnali (importanza della strada, corse nelle ore dei pendolari, pendolari della zona, ZTL, calo di velocità, nodo treno o metro)",
         "effetto": f"con soglia 5%: {sens['soglia_fermate']['5']['fermate']} fermate ({sens['soglia_fermate']['5']['nessun'] + sens['soglia_fermate']['5']['pochi']} senza 50 posti); con 15%: {sens['soglia_fermate']['15']['fermate']} ({sens['soglia_fermate']['15']['nessun'] + sens['soglia_fermate']['15']['pochi']} senza 50 posti)"},
        {"nome": "Parcheggi contati", "valore": f"tutti i parcheggi aperti: {it(len(parcheggi_all))} trovati, {it(len(parcheggi))} considerati (esclusi {it(len(parcheggi_all) - len(parcheggi))}: lungo strada, solo clienti, privati)",
         "perche": "per ogni auto conta ogni posto dove può fermarsi tutto il giorno",
         "effetto": "i parcheggi di OpenStreetMap sono incompleti: il numero reale è maggiore"},
        {"nome": "Posti", "valore": f"dichiarati, o stimati a 25 m² a posto ({it(n_stim)} dei {it(len(parcheggi))} considerati stimati)",
         "perche": "spesso il numero di posti manca",
         "effetto": "la validazione sui parcheggi con posti dichiarati conferma circa 25 m² a posto; il Palavela è stimato, la fonte web dice «fino a 600»"},
        {"nome": "Fermata coperta", "valore": "almeno 50 posti nominali entro 200 m",
         "perche": "con meno posti l'auto non trova quasi mai dove fermarsi",
         "effetto": f"a 100 m le fermate senza 50 posti sono {cnt_sens('100')}, a 400 m {it(sens['distanza']['400']['nessun'] + sens['distanza']['400']['pochi'])} (su {it(n0 + n1)} a 200 m); con 30 posti {it(sens['posti_coperta']['30']['non_ok'])} senza, con 100 posti {it(sens['posti_coperta']['100']['non_ok'])}"},
        {"nome": "Parcheggi in mappa", "valore": f"almeno {MIN_POSTI_MOSTRATO} posti entro 400 m da una fermata importante o da un nodo di trasporto importante, più tutti i garage 5T con dati",
         "perche": "nella mappa restano i parcheggi grandi, vicini a dove si entra o si sale sul mezzo",
         "effetto": f"sono {it(len(parcheggi_out))} parcheggi su {it(len(grandi))} con almeno 50 posti: coprono {it(sum(p['posti'] for p in parcheggi_out))} posti; la copertura delle fermate resta a 200 m, indipendente da questa scelta"},
        {"nome": "Riempimento", "valore": "misurato dove il 5T lo trasmette (2 giorni feriali, 10-16); pieno ≥ 85%; gli altri parcheggi non hanno il dato",
         "perche": "un parcheggio pieno non serve",
         "effetto": f"il riempimento colora i parcheggi e disegna i profili; non cambia il conteggio delle fermate. Misurati: {it(round(posti_misurati / posti_tot_cons * 100, 1), 1)}% dei posti, {len(garage_con_dati)} garage 5T"},
        {"nome": "Aree", "valore": f"celle esagonali di circa 2 km² (lato 900 m); Critica ≥ {soglie_aree[0]:g}%, Scarsa {soglie_aree[1]:g}-{soglie_aree[0] - 1:g}%, Buona < {soglie_aree[1]:g}% delle fermate senza 50 posti",
         "perche": "una cella è un pezzo di città riconoscibile; le zone IMQ erano troppo grandi e diseguali",
         "effetto": f"con soglie 50/25: {', '.join(f'{k} {v}' for k, v in sens['soglie_aree']['50/25'].items())}; con 66/33: {', '.join(f'{k} {v}' for k, v in sens['soglie_aree']['66/33'].items())}; celle con meno di {MIN_FERMATE_AREA} fermate: dato indicativo"},
        {"nome": "20 punti prioritari", "valore": "fermate senza 50 posti raggruppate entro 1 km; parcheggi ≥ 100 posti entro 600 m come candidati ad ampliarsi",
         "perche": "risponde a «dove metterne uno o ingrandirlo»", "effetto": "l'ordine dipende dal punteggio della fermata e dal raggruppamento a 1 km"},
        {"nome": "Direzioni d'ingresso (solo riferimento)", "valore": "8 settori da Piazza Castello; domanda = auto in entrata × quota",
         "perche": "stima di riferimento per la scheda, non guida la mappa",
         "effetto": f"con quota 15%: Mancano+Pochi {sens['quota']['15']['mancano_pochi']}; con 40%: {sens['quota']['40']['mancano_pochi']}"},
    ]

    # ---- dati di uscita ----
    dati = {
        "generato": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "quota_interscambio": round(quota, 4),
        "soglia_aree": list(soglie_aree),
        "fonti": ["data/processed/risultato6_v2/scenari.json", "data/processed/risultato6_v2/luoghi.json",
                  "data/processed/risultato6_v2/parcheggi.json", "data/processed/risultato6_v2/riempimento.json",
                  "data/processed/risultato6_v2/nodi.json", "data/processed/risultato6_v2/segnali.json",
                  "data/processed/imq/spostamenti.csv"],
        "direzioni": direzioni,
        "aree": aree,
        "punti_prioritari": punti,
        "fermate": fermate_out,
        "parcheggi": [{k: v for k, v in p.items() if not k.startswith("_")} for p in parcheggi_out],
        "profili": profili,
        "sensibilita": sens,
        "criteri": criteri,
        "riepilogo": riepilogo,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")
    print(f"\nScritto: {OUT} ({OUT.stat().st_size} byte)")

    _rapporto(dati, ctrl, verifiche, somma_auto, somma_dom, parcheggi_all, parcheggi, posti_misurati, posti_tot_cons)
    return 0


def _segnali_universo(m75):
    """Stessi passi di main() dello script 75: solo Citta' metropolitana, c2_ztl completato."""
    segnali_tutti = json.loads(m75.SEGNALI.read_text(encoding="utf-8"))["luoghi"]
    nodi = {n["id_luogo"]: n for n in json.loads(m75.NODI.read_text(encoding="utf-8"))["luoghi"]}
    istat = json.loads(m75.ISTAT.read_text(encoding="utf-8"))
    macro = {z["cod"]: z["macro"] for z in json.loads(m75.ZONE.read_text(encoding="utf-8"))}
    completate = set(istat["zone_completate"])
    zone_istat = istat["zone"]
    for s in segnali_tutti:
        s["c2_ztl_completo"] = s["c2_ztl"]
        if s["zona_imq"] in completate and zone_istat.get(s["zona_imq"], {}).get("c2_completo") is not None:
            s["c2_ztl_completo"] = round(zone_istat[s["zona_imq"]]["c2_completo"] + (s["c3"] or 0.0), 1)
        s["c2_ztl_scenari"] = s["c2_ztl_completo"]
        s["b_giorno"] = nodi.get(s["id_luogo"], {}).get("b_giorno_corse_ora")
    return [s for s in segnali_tutti if macro.get(s["zona_imq"]) in m75.MACRO_UNIVERSO]


def _rapporto(dati, ctrl, verifiche, somma_auto, somma_dom, parcheggi_all, parcheggi, posti_misurati, posti_tot):
    rm = dati["riepilogo"]
    sens = dati["sensibilita"]
    r = []
    r.append("RAPPORTO R6 - PARCHEGGI PER LASCIARE L'AUTO: AREE, PUNTI PRIORITARI, PARCHEGGI")
    r.append(f"Generato il {dati['generato']} da scripts/80_porte_interscambio.py.")
    r.append("")
    r.append("Domande: quali fermate importanti hanno almeno 50 posti entro 200 m? In quali aree mancano?")
    r.append("Dove servirebbe di più un parcheggio, o ingrandirne uno che c'è?")
    r.append("")
    r.append("== Fermate importanti (378) ==")
    r.append(f"  nessun parcheggio entro 200 m: {rm['fermate_nessun_parcheggio']}")
    r.append(f"  pochi posti (1-49): {rm['fermate_pochi_posti']}")
    r.append(f"  50 posti o più: {rm['fermate_50_piu']}")
    r.append(f"  senza 50 posti in totale: {rm['fermate_senza_50_posti']}")
    r.append("")
    r.append("== Parcheggi: conteggi ==")
    r.append(f"  trovati {it(rm['parcheggi_trovati'])}; esclusi {it(sum(rm['parcheggi_esclusi'].values()))} "
             f"(lungo strada {it(rm['parcheggi_esclusi']['lungo_strada'])}, solo clienti {it(rm['parcheggi_esclusi']['clienti'])}, "
             f"privati {it(rm['parcheggi_esclusi']['privato'])}); considerati {it(rm['parcheggi_considerati'])}")
    r.append(f"  con almeno 50 posti: {it(rm['parcheggi_con_50_posti'])} ({it(rm['posti_con_50_posti'])} posti)")
    r.append(f"  mostrati in mappa: {it(rm['parcheggi_mostrati'])} ({it(rm['posti_mostrati'])} posti)")
    r.append(f"  posti dichiarati / stimati: {it(rm['parcheggi_dichiarati'])} / {it(rm['parcheggi_stimati'])}")
    r.append(f"  posti in parcheggi da 50+ entro 200 m da una fermata importante: {it(rm['posti_50_entro_200_da_fermata'])} "
             f"({rm['parcheggi_50_entro_200_da_fermata']} parcheggi)")
    r.append(f"  idem, da fermata importante o nodo forte: {it(rm['posti_50_entro_200_da_fermata_o_nodo'])} "
             f"({rm['parcheggi_50_entro_200_da_fermata_o_nodo']} parcheggi)")
    v = rm["validazione_25m2"]
    r.append(f"  validazione dei 25 m²: mediana {v['mediana_m2_per_posto']} m² per posto, "
             f"25°-75° percentile {v['fascia_25_75']}, su {v['campione']} parcheggi OSM con posti dichiarati")
    pal = rm["verifica_palavela"]
    r.append(f"  Palavela (OSM 104393338): {pal['posti_stimati']} posti stimati, a {pal['dist_fermata_importante_m']} m "
             f"dalla fermata importante più vicina. {pal['nota']}")
    r.append("")
    r.append("== Aree (celle esagonali di circa 2 km²) ==")
    r.append(f"{'Area':10s} {'Fermate':>8s} {'Nessun':>7s} {'Pochi':>6s} {'50+':>5s} {'Quota senza':>12s} {'Categoria':>10s}  Zone principali")
    for a in dati["aree"]:
        nota = " (indicativo)" if a["indicativo"] else ""
        zp = ", ".join(a["zone_principali"])
        r.append(f"{a['id']:10s} {a['n_fermate']:>8d} {a['nessun']:>7d} {a['pochi']:>6d} {a['ok']:>5d} "
                 f"{pct(a['quota_senza']):>12s} {a['categoria'] + nota:>10s}  {zp}")
    r.append("  aree per categoria: " + ", ".join(f"{k} {rm['aree_per_categoria'][k]}" for k in CAT_AREA))
    r.append("")
    r.append("== 20 punti prioritari ==")
    for p in dati["punti_prioritari"]:
        r.append(f"  {p['ordine']:2d}. {p['nome']} ({p['zona_nome']}): {p['n_fermate']} fermate, punteggio {p['punteggio']}, "
                 f"posti entro 200 m {it(p['posti_nominali_200'])}")
        for c in p["candidati"][:4]:
            r.append(f"        candidato ad ampliarsi: {c['nome']}, {c['dist_m']} m, {it(c['posti'])} posti, {c['stato']}")
    r.append("")
    r.append("== Direzioni d'ingresso (solo riferimento) ==")
    for d in dati["direzioni"]:
        r.append(f"  {d['nome']:10s} auto {it(d['auto_in_entrata'])}, domanda {it(d['domanda'])}, "
                 f"posti {it(d['posti_nominali'])}, copertura {pct(d['copertura'])}, {d['categoria']}")
    r.append(f"  auto in entrata al mattino: {it(somma_auto)} [STIMATO, IMQ 2022]; domanda: {it(somma_dom)} [STIMATO]")
    r.append("")
    r.append("== Sensibilità ==")
    for k, v2 in sens["distanza"].items():
        r.append(f"  distanza {k} m: nessun {v2['nessun']}, pochi {v2['pochi']}, 50+ {v2['ok']}")
    for k, v2 in sens["posti_coperta"].items():
        r.append(f"  soglia {k} posti: sotto la soglia {v2['non_ok']}, sopra {v2['ok']}")
    for k, v2 in sens["soglia_fermate"].items():
        r.append(f"  soglia fermate {k}%: {v2['fermate']} fermate, nessun {v2['nessun']}, pochi {v2['pochi']}, 50+ {v2['ok']}")
    for k, v2 in sens["soglie_aree"].items():
        r.append(f"  soglie aree {k}: " + ", ".join(f"{x} {v2[x]}" for x in CAT_AREA))
    for k, v2 in sens["settori"].items():
        r.append(f"  settori {k}: " + ", ".join(f"{x} {n}" for x, n in v2.items()))
    r.append("")
    r.append("== Controlli ==")
    for nome, ok in ctrl:
        r.append(f"  {'OK' if ok else 'NO'} {nome}")
    r.append("")
    r.append("== Verifica a posteriori (non entra nei dati mostrati) ==")
    r.append("Le osservazioni a mano di Leo servono solo a vedere se il metodo le conferma.")
    for v2 in verifiche:
        r.append(f"- {v2['nome']} (raggio {v2['raggio_m']} m):")
        r.append(f"  parcheggi considerati entro il raggio: {v2['parcheggi_entro_raggio']} ({it(v2['posti_entro_raggio'])} posti)")
        r.append("  misurati: " + ("; ".join(f"{m['nome']} {m['stato']} (G {m['G']})" for m in v2["misurati"]) or "nessuno"))
        r.append(f"  area: {v2['area']} ({v2['nota_area']})")
        r.append(f"  direzione: {v2['direzione']} ({v2['direzione_categoria']})")
        r.append(f"  esito: {v2['esito']}")
    r.append("")
    r.append("== Limiti ==")
    r.append("- Auto in entrata: indagine campionaria IMQ 2022, per zona di origine.")
    r.append("- Quota di chi cambia con un mezzo pubblico: 299 interviste.")
    r.append("- Posti stimati dalla superficie (25 m² a posto): errore di circa il 30%.")
    r.append(f"- Riempimento misurato su pochi giorni [DATI SCARSI]; copre il {it(posti_misurati / posti_tot * 100, 1)}% dei posti; "
             f"{rm['garage_con_dati']} garage 5T.")
    r.append("- Alcuni parcheggi importanti non trasmettono il riempimento: non sappiamo se sono pieni.")
    r.append("- La distanza pesa molto: a 100 m le fermate senza 50 posti sono molte di più, a 400 m molte di meno.")
    r.append("- Distanze in linea d'aria, non a piedi.")
    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(r) + "\n", encoding="utf-8")
    print(f"Scritto: {RAPPORTO}")


if __name__ == "__main__":
    sys.exit(main())
