#!/usr/bin/env python3
"""87 - Popolarita' delle zone IMQ e linee GTT "utili" (lavoro 6 del Risultato 6).

SOLO LETTURA dei dati; scrive solo data/processed/popolarita_zone.json e docs/rapporti/RAPPORTO_POPOLARITA_ZONE.txt.

1. Popolarita' di ogni zona IMQ = spostamenti che ARRIVANO nella zona (IMQ 2022, COD_ARR, peso PESO come nello script 81)
   PER km2 di zona (Leo, 20/10: in cintura una zona e' un comune intero, quindi i comuni grandi non devono vincere per
   la sola superficie; restano nel file anche `arrivi` e `km2`),
   esclusi i ritorni a casa (scopi 08 e 11), in tre gruppi: lavoro/studio (01,02,03), acquisti/cure/svago (04,06,07),
   altro (05,09,10,12-16). La "popolarita'" usata per ordinare le zone e' arrivi / km2 (senza ritorni a casa); le zone con meno di MIN_INTERVISTE
   righe IMQ di arrivo hanno dati_scarsi = true e non entrano fra le piu' popolari.
   In piu' il numero di servizi nella zona, mostrato a parte e NON sommato: dentro Torino vengono dal catalogo
   comunale (completo), fuori Torino da OpenStreetMap (servizi_osm_cintura.json: scuole, salute, cibo; dato meno
   completo), quindi non sono confrontabili fra zone dentro e fuori Torino.
   "servizi" = punti del catalogo di istruzione, salute, servizi, impianti sportivi e di cultura/svago del gruppo
   commercio (mercati tematici, luoghi, musei, biblioteche, cinema); "esercizi" = attivita' commerciali (commercio/attivita).
2. Linea GTT = route_short_name del GTFS (tutte le corse, le due direzioni insieme). Zone toccate = zone che contengono
   almeno una sua fermata (per coordinate). Punteggio (a) = quante delle 20 zone piu' popolari tocca (principale);
   (b) = somma della popolarita' delle zone toccate (solo confronto, anche per gruppo di scopo).
   "Linea utile" = 25% piu' alto per (a), a pari (a) conta (b).
3. Per ogni parcheggio adatto (parcheggi_adatti.json): quante linee utili hanno una fermata a meno di 400 m a piedi
   (linea d'aria x 1,3).
"""
import csv
import json
import math
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
D = RADICE / "data"
SPOSTAMENTI = D / "processed" / "imq" / "spostamenti.csv"
ZONE = D / "processed" / "imq_zone.json"
CATALOGO = D / "processed" / "catalogo"
OSM = D / "processed" / "servizi_osm_cintura.json"
GTFS = D / "raw" / "gtt_gtfs_20261003_224530.zip"
P6 = D / "processed" / "risultato6_v2"
ADATTI, PARCHEGGI = P6 / "parcheggi_adatti.json", P6 / "parcheggi.json"
OUT = D / "processed" / "popolarita_zone.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_POPOLARITA_ZONE.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

RITORNI = ("08", "11")
GRUPPI = {"lavoro_studio": ("01", "02", "03"), "acquisti_svago": ("04", "06", "07"),
          "altro": ("05", "09", "10", "12", "13", "14", "15", "16")}
NOME_GRUPPO = {"lavoro_studio": "lavoro/studio", "acquisti_svago": "acquisti/cure/svago", "altro": "altro"}
N_TOP_ZONE = 20
MIN_INTERVISTE = 50   # Leo, 20/10: sotto questo numero di righe IMQ di arrivo la zona ha dati_scarsi e non entra fra le piu' popolari
QUOTA_UTILI = 0.25
DIST_PIEDI_M = 400.0
N_RAPPORTO = 15
# catalogo: (file, dataset) -> "servizi" oppure "esercizi" (solo punti [lat, lon, ...])
ESERCIZI = {("commercio", "attivita")}
SERVIZI = {("istruzione", None), ("salute", None), ("servizi", None), ("sicurezza_sport", "impianti_sportivi"),
           ("commercio", "mercati_tematici"), ("commercio", "luoghi"), ("commercio", "musei"),
           ("commercio", "biblioteche"), ("commercio", "cinema")}


def superficie_km2(anelli):
    """Area in km2 della zona (proiezione di comuni.proietta, formula del poligono). I poligoni sono scritti con un verso
    di percorrenza: gli anelli esterni hanno tutti lo stesso segno e i buchi il segno opposto, quindi la somma con segno
    sottrae i buchi da sola. Ritorna anche la somma senza segno (per un controllo)."""
    firmate = []
    for a in anelli:
        p = [comuni.proietta(la, lo) for la, lo in a]
        n = len(p)
        firmate.append(sum(p[i][0] * p[(i + 1) % n][1] - p[(i + 1) % n][0] * p[i][1] for i in range(n)) / 2.0)
    return abs(sum(firmate)) / 1e6, sum(abs(x) for x in firmate) / 1e6


def peso(x):
    try:
        return float((x.get("PESO") or "").replace(",", "."))
    except ValueError:
        return 0.0


def gruppo_di(scopo):
    for g, codici in GRUPPI.items():
        if scopo in codici:
            return g
    return None


def leggi_arrivi(codici_zona):
    """Arrivi per zona e gruppo; ritorni a casa esclusi. Ritorna anche i totali per il controllo."""
    arr = defaultdict(lambda: defaultdict(float))
    n_int = defaultdict(int)
    tot = {"tutti": 0.0, "arrivi": 0.0, "ritorni": 0.0, "senza_zona": 0.0, "zona_ignota": 0.0, "scopo_ignoto": 0.0}
    with SPOSTAMENTI.open(encoding="utf-8-sig") as fh:
        for x in csv.DictReader(fh, delimiter=";"):
            p = peso(x)
            scopo = (x.get("SCOPO") or "").strip()
            tot["tutti"] += p
            if scopo in RITORNI:
                tot["ritorni"] += p
                continue
            g = gruppo_di(scopo)
            z = (x.get("COD_ARR") or "").strip()
            if g is None:
                tot["scopo_ignoto"] += p
                continue
            if not z:
                tot["senza_zona"] += p
                continue
            if z not in codici_zona:
                tot["zona_ignota"] += p
                continue
            arr[z][g] += p
            n_int[z] += 1
            tot["arrivi"] += p
    return arr, n_int, tot


def punti_del_catalogo(zone_f):
    """Conta per zona i punti del catalogo comunale: servizi ed esercizi. Ritorna anche i punti fuori da ogni zona."""
    cnt = {"servizi": defaultdict(int), "esercizi": defaultdict(int)}
    fuori = {"servizi": 0, "esercizi": 0}
    dettaglio = defaultdict(int)
    for f in sorted(CATALOGO.glob("*.json")):
        if f.stem == "catalogo":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for ds in d.get("dati", []):
            chiave = (f.stem, ds.get("id"))
            if chiave in ESERCIZI:
                tipo = "esercizi"
            elif chiave in SERVIZI or (f.stem, None) in SERVIZI:
                tipo = "servizi"
            else:
                continue
            for el in ds.get("elementi", []):
                try:
                    la, lo = float(el[0]), float(el[1])
                except (TypeError, ValueError, IndexError):
                    continue
                z = zone_f(la, lo)
                if z is None:
                    fuori[tipo] += 1
                else:
                    cnt[tipo][z] += 1
                    dettaglio[(f.stem, ds.get("id"))] += 1
    return cnt, fuori, dettaglio


def punti_osm(zone_f, sezioni_torino):
    """Servizi OSM fuori Torino (scuole, salute -> servizi; cibo -> esercizi)."""
    s = json.loads(OSM.read_text(encoding="utf-8"))["servizi"]
    cnt = {"servizi": defaultdict(int), "esercizi": defaultdict(int)}
    fuori = 0
    for gruppo, tipo in (("scuole", "servizi"), ("salute", "servizi"), ("cibo", "esercizi")):
        for p in s.get(gruppo, []):
            z = zone_f(p["lat"], p["lon"])
            if z is None:
                fuori += 1
            elif z.startswith("Q"):
                continue            # dentro Torino conta solo il catalogo comunale
            else:
                cnt[tipo][z] += 1
    return cnt, fuori


def leggi_gtfs():
    """Ritorna fermate {stop_id: (lat, lon)} e linee {nome: set(stop_id)} (route_short_name, tutte le corse)."""
    with zipfile.ZipFile(GTFS) as z:
        def righe(nome):
            with z.open(nome) as fh:
                import io
                yield from csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8-sig", newline=""))
        fermate = {}
        for r in righe("stops.txt"):
            try:
                fermate[r["stop_id"]] = (float(r["stop_lat"]), float(r["stop_lon"]))
            except (ValueError, KeyError):
                continue
        nome_rotta = {r["route_id"]: (r.get("route_short_name") or "").strip() for r in righe("routes.txt")}
        trip_linea = {}
        for r in righe("trips.txt"):
            n = nome_rotta.get(r["route_id"])
            if n:
                trip_linea[r["trip_id"]] = n
        linee = defaultdict(set)
        for r in righe("stop_times.txt"):
            n = trip_linea.get(r["trip_id"])
            if n:
                linee[n].add(r["stop_id"])
    return fermate, linee


def main():
    c = comuni.Controlli()
    for f in (SPOSTAMENTI, ZONE, OSM, GTFS, ADATTI, PARCHEGGI, CATALOGO / "istruzione.json"):
        c(f"esiste {f.name}", f.exists(), bloccante=True)
    m72 = comuni.carica_script("72_nodi_tp.py")
    zone_imq = json.loads(ZONE.read_text(encoding="utf-8"))
    nome_zona = {z["cod"]: (z.get("denom") or "").strip() for z in zone_imq}
    macro = {z["cod"]: z["macro"] for z in zone_imq}
    c("nessuna zona senza nome", all(nome_zona.values()),
      dettaglio=", ".join(k for k, v in nome_zona.items() if not v))
    zone_geo = m72.carica_zone_imq()
    zona_di = lambda la, lo: m72.zona_di(la, lo, zone_geo)  # noqa: E731
    c("poligoni per tutte le zone", {z["cod"] for z in zone_geo} == set(nome_zona), bloccante=True,
      dettaglio=f"{len(zone_geo)} poligoni, {len(nome_zona)} zone")

    # ---- 1. popolarita' ----
    print("1. arrivi dell'IMQ per zona di arrivo e scopo...")
    arr, n_int, tot = leggi_arrivi(set(nome_zona))
    c("arrivi + ritorni a casa esclusi = totale spostamenti IMQ (stesso peso)",
       abs(tot["arrivi"] + tot["ritorni"] + tot["senza_zona"] + tot["zona_ignota"] + tot["scopo_ignoto"] - tot["tutti"])
       < 1e-6 * tot["tutti"], bloccante=True,
       dettaglio=f"arrivi {tot['arrivi']:,.0f} + ritorni {tot['ritorni']:,.0f} + senza zona {tot['senza_zona']:,.0f} + "
                 f"zona non nell'elenco {tot['zona_ignota']:,.0f} + scopo non classificato {tot['scopo_ignoto']:,.0f} "
                 f"= {tot['tutti']:,.0f}")
    c("spostamenti senza zona di arrivo, zona sconosciuta o scopo non classificato sotto l'1%",
      (tot["senza_zona"] + tot["zona_ignota"] + tot["scopo_ignoto"]) < 0.01 * tot["tutti"],
      dettaglio=f"senza zona {tot['senza_zona']:,.0f}, zona sconosciuta {tot['zona_ignota']:,.0f}, "
                f"scopo non classificato {tot['scopo_ignoto']:,.0f}")
    c("ritorni a casa esclusi sono una parte rilevante degli spostamenti", tot["ritorni"] > 0.2 * tot["tutti"],
      dettaglio=f"{tot['ritorni'] / tot['tutti']:.0%}")

    print("   servizi per zona (catalogo comunale dentro Torino, OSM fuori)...")
    cat, fuori_cat, dett_cat = punti_del_catalogo(zona_di)
    osm, fuori_osm = punti_osm(zona_di, None)
    c("punti del catalogo fuori da ogni zona IMQ", sum(fuori_cat.values()) == 0,
      dettaglio=f"servizi {fuori_cat['servizi']}, esercizi {fuori_cat['esercizi']}")
    c("punti OSM della cintura fuori da ogni zona IMQ", fuori_osm == 0, dettaglio=f"{fuori_osm}")
    cat_fuori_q = {z: n for t in cat.values() for z, n in t.items() if not z.startswith("Q")}
    c("punti del catalogo comunale in zone fuori Torino (atteso 0: il catalogo e' di Torino)", not cat_fuori_q,
      dettaglio=f"{sum(cat_fuori_q.values())} punti in " + ", ".join(f"{z} ({n})" for z, n in sorted(cat_fuori_q.items())))

    aree = {z["cod"]: superficie_km2(z["anelli"]) for z in zone_geo}
    km2 = {k: v[0] for k, v in aree.items()}
    con_buchi = {k: v for k, v in aree.items() if v[1] - v[0] > 1e-6}
    c("zone con anelli di verso opposto (buchi sottratti)", True,
      dettaglio=f"{len(con_buchi)} zone: " + ", ".join(f"{k} ({v[1]:.2f} -> {v[0]:.2f} km2)" for k, v in sorted(con_buchi.items())[:8]))
    sospette = [k for k, v in aree.items() if v[0] < 0.5 * v[1]]
    c("nessuna zona perde piu' di meta' della superficie per i buchi", not sospette, dettaglio=", ".join(sospette))
    c("nessuna superficie <= 0", all(v > 0 for v in km2.values()), bloccante=True,
      dettaglio=", ".join(f"{k} {v:.3f}" for k, v in km2.items() if v <= 0))
    km2_torino = sum(v for k, v in km2.items() if k.startswith("Q"))
    c("superficie delle zone di Torino (Q...) fra 120 e 135 km2", 120 <= km2_torino <= 135,
      dettaglio=f"{km2_torino:.1f} km2 in {sum(1 for k in km2 if k.startswith('Q'))} zone")
    zone = []
    for cod in sorted(nome_zona):
        g = {k: arr[cod].get(k, 0.0) for k in GRUPPI}
        zone.append({"cod": cod, "nome": nome_nome(nome_zona, cod), "macro": macro[cod],
                     "arrivi": sum(g.values()), "km2": round(km2[cod], 3), "popolarita": sum(g.values()) / km2[cod],
                     "dati_scarsi": n_int.get(cod, 0) < MIN_INTERVISTE,
                     "arrivi_gruppi": g, "interviste": n_int.get(cod, 0),
                     "servizi": cat["servizi"].get(cod, 0) + osm["servizi"].get(cod, 0),
                     "esercizi": cat["esercizi"].get(cod, 0) + osm["esercizi"].get(cod, 0),
                     "fonte_servizi": "catalogo comunale" if cod.startswith("Q") else "OpenStreetMap (incompleto)"})
    zone.sort(key=lambda z: (-z["popolarita"], z["cod"]))
    for z in zone:
        z["in_universo"] = z["macro"] in comuni.MACRO_UNIVERSO
    # classifica nella Citta' metropolitana, senza le zone con dati scarsi
    for k, z in enumerate([z for z in zone if z["in_universo"] and not z["dati_scarsi"]], 1):
        z["posizione"] = k
    for z in zone:
        z.setdefault("posizione", None)
    zone_u = [z for z in zone if z["in_universo"] and not z["dati_scarsi"]]
    n_scarse = sum(1 for z in zone if z["in_universo"] and z["dati_scarsi"])
    c("zone della Citta' metropolitana con dati scarsi (meno di MIN_INTERVISTE righe di arrivo)", n_scarse == 0,
      dettaglio=f"{n_scarse} su {sum(1 for z in zone if z['in_universo'])}")
    c("almeno 20 zone con dati sufficienti", len(zone_u) >= N_TOP_ZONE, bloccante=True, dettaglio=f"{len(zone_u)}")
    top = zone_u[:N_TOP_ZONE]
    cod_top = {z["cod"] for z in top}
    pop = {z["cod"]: z["popolarita"] for z in zone}
    pop_g = {z["cod"]: {k: v / z["km2"] for k, v in z["arrivi_gruppi"].items()} for z in zone}
    c("somma degli arrivi per zona = arrivi contati", abs(sum(z["arrivi"] for z in zone) - tot["arrivi"]) < 1e-6 * tot["arrivi"],
      bloccante=True)
    n_senza_arrivi = sum(1 for z in zone if z["arrivi"] == 0)
    c("zone senza nessun arrivo nell'IMQ", n_senza_arrivi == 0, dettaglio=f"{n_senza_arrivi} su {len(zone)}")
    print(f"   zone {len(zone)}; arrivi {tot['arrivi']:,.0f}; ritorni esclusi {tot['ritorni']:,.0f}")

    # ---- 2. linee GTT ----
    print("2. linee GTT (GTFS): zone toccate...")
    fermate, linee = leggi_gtfs()
    print(f"   fermate {len(fermate)}; linee (route_short_name) {len(linee)}")
    c("linee nel GTFS > 50", len(linee) > 50, bloccante=True, dettaglio=f"{len(linee)}")
    zona_fermata = {s: zona_di(*fermate[s]) for s in {s for v in linee.values() for s in v if s in fermate}}
    senza = sum(1 for z in zona_fermata.values() if z is None)
    c("fermate usate dalle linee fuori da ogni zona IMQ", senza == 0,
      dettaglio=f"{senza} su {len(zona_fermata)} (non contano per nessuna zona)")
    righe_linee = []
    for nome, stops in linee.items():
        zt = sorted({zona_fermata[s] for s in stops if zona_fermata.get(s)})
        a = sum(1 for z in zt if z in cod_top)
        b = sum(pop[z] for z in zt)
        bg = {k: sum(pop_g[z][k] for z in zt) for k in GRUPPI}
        righe_linee.append({"linea": nome, "fermate": len(stops), "zone_toccate": len(zt), "a": a, "b": b,
                            "b_gruppi": bg, "zone_top": [z for z in zt if z in cod_top]})
    righe_linee.sort(key=lambda r: (-r["a"], -r["b"], r["linea"]))
    n_utili = math.ceil(QUOTA_UTILI * len(righe_linee))
    for k, r in enumerate(righe_linee, 1):
        r["posizione"] = k
        r["utile"] = k <= n_utili
    utili = {r["linea"] for r in righe_linee if r["utile"]}
    a_soglia = righe_linee[n_utili - 1]["a"]
    print(f"   linee utili {len(utili)} (25% di {len(righe_linee)}); punteggio (a) di soglia {a_soglia}")
    c("(a) non e' uguale per tutte le linee", len({r['a'] for r in righe_linee}) > 1, bloccante=True)
    pari_soglia = sum(1 for r in righe_linee if r["a"] == a_soglia)
    c("linee con (a) uguale a quello di soglia (decide (b))", True,
      dettaglio=f"{pari_soglia} linee con (a) = {a_soglia}, di cui {sum(1 for r in righe_linee if r['a'] == a_soglia and r['utile'])} utili")
    lunghe = sorted(righe_linee, key=lambda r: (-r["fermate"], r["linea"]))[:10]
    in_prime15 = sum(1 for r in lunghe if r["posizione"] <= 15)
    c("le 10 linee piu' lunghe (per fermate) NON sono tutte fra le prime 15 per (a)", in_prime15 < 10,
      dettaglio=f"{in_prime15} su 10 sono fra le prime 15 (lunghe: {', '.join(r['linea'] for r in lunghe)})")

    # ---- 3. parcheggi adatti ----
    print("3. parcheggi adatti: linee utili entro 400 m a piedi...")
    from scipy.spatial import cKDTree
    adatti = [p for p in json.loads(ADATTI.read_text(encoding="utf-8"))["parcheggi"] if p.get("adatto")]
    geo_p = {p["id"]: p for p in json.loads(PARCHEGGI.read_text(encoding="utf-8"))["parcheggi"]}
    c("tutti i parcheggi adatti hanno coordinate", all(p["id"] in geo_p for p in adatti), bloccante=True,
      dettaglio=f"{len(adatti)} adatti")
    ids = [s for s in fermate if any(s in v for v in ())]  # placeholder, riempito sotto
    linee_di_fermata = defaultdict(set)
    for nome, stops in linee.items():
        for s in stops:
            if s in fermate:
                linee_di_fermata[s].add(nome)
    ids = list(linee_di_fermata)
    xy = np.array([comuni.proietta(*fermate[s]) for s in ids])
    albero = cKDTree(xy)
    raggio = DIST_PIEDI_M / comuni.FATTORE_PIEDI
    park = []
    for p in adatti:
        g = geo_p[p["id"]]
        vicini = albero.query_ball_point(comuni.proietta(g["lat"], g["lon"]), raggio)
        tutte = set().union(*(linee_di_fermata[ids[i]] for i in vicini)) if vicini else set()
        u = sorted(tutte & utili)
        park.append({"id": p["id"], "nome": p["nome"], "tipo": p["tipo"], "zona_imq": p.get("zona_imq"),
                     "posti": p.get("posti"), "linee_totali": len(tutte), "linee_utili": len(u), "elenco_utili": u})
    park.sort(key=lambda p: (-p["linee_utili"], -(p["posti"] or 0), p["id"]))
    senza_linee = sum(1 for p in park if p["linee_totali"] == 0)
    senza_utili = sum(1 for p in park if p["linee_utili"] == 0)
    c("parcheggi adatti senza nessuna linea entro 400 m a piedi", senza_linee == 0,
      dettaglio=f"{senza_linee} su {len(park)}")
    c("parcheggi adatti senza nessuna linea utile entro 400 m a piedi", senza_utili == 0,
      dettaglio=f"{senza_utili} su {len(park)}")

    # ---- uscite ----
    parametri = {"gruppi_scopo": GRUPPI, "ritorni_esclusi": RITORNI, "zone_top": N_TOP_ZONE, "min_interviste": MIN_INTERVISTE, "universo": comuni.MACRO_UNIVERSO, "quota_linee_utili": QUOTA_UTILI,
                 "distanza_piedi_m": DIST_PIEDI_M, "fattore_piedi": comuni.FATTORE_PIEDI, "gtfs": GTFS.name,
                 "n_linee": len(righe_linee), "n_utili": len(utili), "soglia_a": a_soglia,
                 "totali_imq": {k: round(v, 1) for k, v in tot.items()}}
    OUT.write_text(json.dumps({"parametri": parametri, "zone": zone, "linee": righe_linee, "parcheggi_adatti": park,
                               "controlli": c.righe}, ensure_ascii=False), encoding="utf-8")

    def txt_zona(z):
        g = z["arrivi_gruppi"]
        return (f"{z['posizione']:3d}. {z['cod']} {z['nome'][:28]:28s} arrivi {z['arrivi']:>9,.0f}  {z['km2']:7.2f} km2  "
                f"{z['popolarita']:>8,.0f} arrivi/km2 "
                f"(lavoro/studio {g['lavoro_studio']:,.0f}; acquisti/svago {g['acquisti_svago']:,.0f}; altro {g['altro']:,.0f}) "
                f"servizi {z['servizi']} esercizi {z['esercizi']} [{z['fonte_servizi']}]")
    r = ["RAPPORTO - POPOLARITA' DELLE ZONE E LINEE GTT UTILI (script 87)", "",
         f"Popolarita' = spostamenti IMQ che ARRIVANO nella zona per km2, ritorni a casa (scopi {', '.join(RITORNI)}) esclusi: "
         f"{tot['arrivi']:,.0f} su {tot['tutti']:,.0f} (peso IMQ); ritorni esclusi {tot['ritorni']:,.0f}.",
         "Gruppi: lavoro/studio (" + ",".join(GRUPPI["lavoro_studio"]) + "); acquisti/cure/svago ("
         + ",".join(GRUPPI["acquisti_svago"]) + "); altro (" + ",".join(GRUPPI["altro"]) + ").",
         "Servizi ed esercizi sono mostrati a parte e non sommati agli arrivi: dentro Torino vengono dal catalogo comunale,"
         " fuori da OpenStreetMap (dato meno completo): non sono confrontabili fra dentro e fuori Torino.",
         f"Linee GTT: {len(righe_linee)} (route_short_name, tutte le corse, due direzioni insieme); fermate nel GTFS {len(fermate)}.",
         f"Linea utile = {QUOTA_UTILI:.0%} piu' alto per (a) = quante delle {N_TOP_ZONE} zone piu' popolari tocca; a pari (a) "
         f"conta (b) = somma della popolarita' delle zone toccate. Utili: {len(utili)}; (a) di soglia {a_soglia}.",
         f"Parcheggio adatto: linee utili con una fermata entro {DIST_PIEDI_M:.0f} m a piedi (linea d'aria x {comuni.FATTORE_PIEDI}).",
         "", f"== Le {N_RAPPORTO} zone piu' popolari della Citta' metropolitana (Torino, cintura, resto CMTO) =="] + [txt_zona(z) for z in zone_u[:N_RAPPORTO]]
    r.append(f"Zone della Citta' metropolitana con dati scarsi (meno di {MIN_INTERVISTE} righe IMQ di arrivo, fuori dalla classifica): {n_scarse}")
    fuori_u = [z for z in zone if not z["in_universo"]][:5]
    r += ["", "Fuori dalla Citta' metropolitana (non entrano nella classifica, le linee GTT non ci arrivano): "
          + "; ".join(f"{z['nome']} ({z['arrivi']:,.0f})" for z in fuori_u) + " ..."]
    r += ["", "== Le 5 zone piu' popolari per gruppo di scopo =="]
    for g in GRUPPI:
        piu = sorted(zone_u, key=lambda z: (-pop_g[z["cod"]][g], z["cod"]))[:5]
        r.append(f"  {NOME_GRUPPO[g]}: " + "; ".join(f"{z['nome']} ({pop_g[z['cod']][g]:,.0f}/km2)" for z in piu))
    r += ["", f"== Le {N_RAPPORTO} linee piu' utili ==",
          "  pos. linea   (a) zone top toccate   (b) arrivi/km2 delle zone toccate   zone toccate   fermate   [b: lavoro | svago | altro]"]
    for x in righe_linee[:N_RAPPORTO]:
        bg = x["b_gruppi"]
        r.append(f"  {x['posizione']:3d}. {x['linea']:8s} (a)={x['a']:2d}  (b)={x['b']:>10,.0f}  zone {x['zone_toccate']:3d}  "
                 f"fermate {x['fermate']:4d}  [{bg['lavoro_studio']:,.0f} | {bg['acquisti_svago']:,.0f} | {bg['altro']:,.0f}]"
                 + ("" if x["utile"] else "  (non utile)"))
    r += ["", f"== I {N_RAPPORTO} parcheggi adatti con piu' linee utili (a pari linee: piu' posti) =="]
    for k, p in enumerate(park[:N_RAPPORTO], 1):
        r.append(f"  {k:3d}. {p['nome'][:34]:34s} {p['tipo']:22s} {p['zona_imq'] or '-':5s} posti {p['posti']}  "
                 f"linee utili {p['linee_utili']} (linee totali {p['linee_totali']}): {', '.join(p['elenco_utili'][:12])}")
    r += ["", "== Controlli ==", *("  " + x for x in c.righe)]
    RAPPORTO.write_text("\n".join(r) + "\n", encoding="utf-8")
    print("\n".join(r))
    print(f"\nScritti: {OUT.relative_to(RADICE)}, {RAPPORTO.relative_to(RADICE)}; avvisi: {len(c.avvisi())}")


def nome_nome(nomi, cod):
    return nomi[cod]


if __name__ == "__main__":
    main()
