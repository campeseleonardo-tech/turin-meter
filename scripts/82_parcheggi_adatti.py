#!/usr/bin/env python3
"""
82_parcheggi_adatti.py  -  Risultato 6 (correzioni del 20/10/2026): quali parcheggi possono davvero servire
per lasciare l'auto e proseguire con i mezzi pubblici. Preparato da Claude, da lanciare sul PC.

Perche'
-------
Prima contava qualsiasi parcheggio aperto, anche quelli degli ospedali, delle universita', dei centri
commerciali e i garage del centro: posti che servono a chi arriva li', non a chi vuole lasciare l'auto prima.

Regole (un parcheggio e' "adatto" se le rispetta tutte; i valori sono costanti qui sotto e opzioni)
------
  1. tipo aperto: interscambio_ufficiale, garage_5t, park_ride_osm, osm_pubblico;
  2. fuori dalla zona centrale Q001-Q009 (comuni.ZONE_CENTRALI);
  3. almeno POSTI_MINIMI (20) posti, dichiarati o stimati a 25 m2 a posto;
  4. non "di destinazione": il punto del parcheggio non cade dentro (o a meno di DIST_DESTINAZIONE_M = 50 m
     da) un'area OSM con amenity=hospital/university/college, landuse=retail o shop=mall. Gli interscambi
     ufficiali e i park&ride non vengono mai esclusi da questa regola (i garage 5T si').

Cosa legge
----------
  data/processed/risultato6_v2/parcheggi.json            (inventario, script 69)
  data/processed/risultato6_v2/parcheggi_funzione.json   (zona IMQ di ogni parcheggio, script 72)
  data/processed/imq_zone_geo.json                       (solo se a un parcheggio manca la zona)
  data/otp/rete/torino_cintura.osm.pbf                    (aree di destinazione)

Cosa scrive
-----------
  data/processed/risultato6_v2/parcheggi_adatti.json
  docs/rapporti/RAPPORTO_R6_PARCHEGGI_ADATTI.txt

Come si lancia
--------------
  python scripts\\82_parcheggi_adatti.py
  python scripts\\82_parcheggi_adatti.py --senza-destinazioni   (sensibilita': non esclude le destinazioni)
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
P = RADICE / "data" / "processed" / "risultato6_v2"
PARCHEGGI = P / "parcheggi.json"
FUNZIONE = P / "parcheggi_funzione.json"
ZONE_GEO = RADICE / "data" / "processed" / "imq_zone_geo.json"
PBF = RADICE / "data" / "otp" / "rete" / "torino_cintura.osm.pbf"
OUT = P / "parcheggi_adatti.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6_PARCHEGGI_ADATTI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

TIPI_APERTI = ("interscambio_ufficiale", "garage_5t", "park_ride_osm", "osm_pubblico")
TIPI_MAI_DESTINAZIONE = ("interscambio_ufficiale", "park_ride_osm")
POSTI_MINIMI = 20
DIST_DESTINAZIONE_M = 50.0


def posti_di(p):
    if p.get("posti_dichiarati"):
        return int(p["posti_dichiarati"])
    return int(p.get("posti_stimati") or 0)   # stessa regola di posti_con() nello script 80


def motivo_destinazione(tags):
    am = tags.get("amenity")
    if am in ("hospital", "university", "college"):
        return am
    if tags.get("landuse") == "retail":
        return "retail"
    if tags.get("shop") == "mall":
        return "mall"
    return None


def proietta_geom(g):
    """Geometria shapely da (lon, lat) a metri (comuni.proietta), con shapely 2 o 1."""
    try:
        import numpy as np
        import shapely
        return shapely.transform(g, lambda a: np.column_stack([a[:, 0] * comuni.M_GRADO * np.cos(np.radians(comuni.LAT_RIF)),
                                                               a[:, 1] * comuni.M_GRADO]))
    except (ImportError, AttributeError):
        from shapely.ops import transform
        return transform(lambda x, y, z=None: comuni.proietta(y, x), g)


def aree_destinazione(pbf):
    """Aree OSM di destinazione, in coordinate locali in metri: lista (geometria shapely, motivo, nome)."""
    import osmium
    from shapely import wkb

    fab = osmium.geom.WKBFactory()
    aree = []

    class H(osmium.SimpleHandler):
        def area(self, a):
            tags = {t.k: t.v for t in a.tags}
            m = motivo_destinazione(tags)
            if not m:
                return
            try:
                g = wkb.loads(fab.create_multipolygon(a), hex=True)
            except Exception:  # noqa: BLE001 - area rotta in OSM: si salta
                return
            g = proietta_geom(g)
            if g.is_valid and g.area > 0:
                aree.append((g, m, tags.get("name") or ""))

    H().apply_file(str(pbf), locations=True)
    return aree


def zona_da_poligoni(parcheggi_senza_zona):
    """Zona IMQ per i parcheggi a cui manca (punto nel poligono)."""
    from shapely.geometry import Point, Polygon
    geo = json.loads(ZONE_GEO.read_text(encoding="utf-8"))
    poligoni = []
    for z in geo:
        g = z["g"]
        if isinstance(g, str):
            g = json.loads(g)
        if g and isinstance(g[0][0], (int, float)):
            anelli = [g]
        elif g and isinstance(g[0][0][0], (int, float)):
            anelli = g
        else:
            anelli = [an for pol in g for an in pol]
        try:
            poligoni.append((z["cod"], Polygon([(p[1], p[0]) for p in anelli[0]]).buffer(0)))
        except (ValueError, IndexError):
            continue
    out = {}
    for p in parcheggi_senza_zona:
        pt = Point(p["lon"], p["lat"])
        out[p["id"]] = next((cod for cod, pol in poligoni if pol.contains(pt)), None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posti-minimi", type=int, default=POSTI_MINIMI)
    ap.add_argument("--dist-destinazione", type=float, default=DIST_DESTINAZIONE_M)
    ap.add_argument("--senza-destinazioni", action="store_true", help="non escludere i parcheggi di destinazione")
    args = ap.parse_args()
    c = comuni.Controlli()
    t0 = time.time()

    c("esiste parcheggi.json", PARCHEGGI.exists(), bloccante=True)
    tutti = json.loads(PARCHEGGI.read_text(encoding="utf-8"))["parcheggi"]
    zona = {}
    if FUNZIONE.exists():
        zona = {f["id"]: f.get("zona_imq") for f in json.loads(FUNZIONE.read_text(encoding="utf-8"))["parcheggi"]}
    aperti = [p for p in tutti if p["tipo"] in TIPI_APERTI]
    senza_zona = [p for p in aperti if not zona.get(p["id"])]
    if senza_zona and ZONE_GEO.exists():
        print(f"zona IMQ da calcolare per {len(senza_zona)} parcheggi...")
        zona.update({k: v for k, v in zona_da_poligoni(senza_zona).items()})
    c("parcheggi aperti senza zona IMQ: pochi (< 2%)",
      sum(1 for p in aperti if not zona.get(p["id"])) < 0.02 * max(1, len(aperti)),
      dettaglio=f"{sum(1 for p in aperti if not zona.get(p['id']))} senza zona (contano come fuori dal centro)")

    aree = []
    if not args.senza_destinazioni:
        c("esiste il PBF di OpenStreetMap", PBF.exists(), bloccante=True)
        print("leggo le aree di destinazione da OpenStreetMap (ospedali, universita', centri commerciali)...")
        aree = aree_destinazione(PBF)
        print(f"  aree trovate: {len(aree)} ({dict(Counter(m for _, m, _ in aree))})")
        c("trovate aree di destinazione", len(aree) > 0, dettaglio=f"{len(aree)}")
    from shapely.geometry import Point
    from shapely.strtree import STRtree
    albero = STRtree([g for g, _, _ in aree]) if aree else None

    righe = []
    conta = Counter()
    for p in tutti:
        rec = {"id": p["id"], "nome": p.get("nome"), "tipo": p["tipo"], "zona_imq": zona.get(p["id"]),
               "posti": posti_di(p), "adatto": False, "motivo": None, "destinazione": None}
        if p["tipo"] not in TIPI_APERTI:
            rec["motivo"] = "tipo_non_aperto"
        elif rec["zona_imq"] in comuni.ZONE_CENTRALI:
            rec["motivo"] = "zona_centrale"
        elif rec["posti"] < args.posti_minimi:
            rec["motivo"] = "pochi_posti"
        else:
            if albero is not None and p["tipo"] not in TIPI_MAI_DESTINAZIONE:
                pt = Point(*comuni.proietta(p["lat"], p["lon"]))
                for i in albero.query(pt.buffer(args.dist_destinazione)):
                    g, m, nome = aree[int(i)]
                    if g.distance(pt) <= args.dist_destinazione:
                        rec["motivo"] = f"destinazione_{m}"
                        rec["destinazione"] = nome or m
                        break
            if rec["motivo"] is None:
                rec["adatto"] = True
                rec["motivo"] = "adatto"
        conta[rec["motivo"]] += 1
        righe.append(rec)

    n_aperti = len(aperti)
    catena = {"trovati": len(tutti), "aperti": n_aperti,
              "fuori_centro": n_aperti - conta["zona_centrale"],
              "con_almeno_posti_minimi": n_aperti - conta["zona_centrale"] - conta["pochi_posti"],
              "adatti": conta["adatto"]}
    adatti = [r for r in righe if r["adatto"]]
    c("almeno un parcheggio adatto", len(adatti) > 0, bloccante=True)
    c("nessun parcheggio adatto in zona centrale", not any(r["zona_imq"] in comuni.ZONE_CENTRALI for r in adatti),
      bloccante=True)
    c("gli interscambi ufficiali fuori centro sono adatti",
      all(r["adatto"] for r in righe if r["tipo"] == "interscambio_ufficiale"
          and r["zona_imq"] not in comuni.ZONE_CENTRALI and r["posti"] >= args.posti_minimi))

    dati = {"generato": time.strftime("%d/%m/%Y %H:%M"),
            "parametri": {"tipi_aperti": list(TIPI_APERTI), "zone_centrali": list(comuni.ZONE_CENTRALI),
                          "posti_minimi": args.posti_minimi, "dist_destinazione_m": args.dist_destinazione,
                          "destinazioni_escluse": not args.senza_destinazioni},
            "catena": catena, "motivi": dict(conta),
            "posti_adatti": int(sum(r["posti"] for r in adatti)),
            "parcheggi": righe, "controlli": c.righe}
    OUT.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")

    escl = sorted([r for r in righe if (r["motivo"] or "").startswith("destinazione_")], key=lambda r: -r["posti"])
    rr = ["RAPPORTO R6 - PARCHEGGI ADATTI A LASCIARE L'AUTO (script 82)",
          f"Generato il {dati['generato']}.", "",
          "== Catena dei conteggi ==",
          f"  trovati {catena['trovati']} -> aperti {catena['aperti']} -> fuori dalla zona centrale {catena['fuori_centro']}"
          f" -> con almeno {args.posti_minimi} posti {catena['con_almeno_posti_minimi']} -> adatti (non di destinazione) {catena['adatti']}",
          f"  posti nei parcheggi adatti: {dati['posti_adatti']:,}".replace(",", "."), "",
          "== Motivi ==", *(f"  {k}: {v}" for k, v in sorted(conta.items(), key=lambda kv: -kv[1])), "",
          "== I 20 parcheggi piu' grandi esclusi perche' di destinazione ==",
          *(f"  {r['posti']:6d} posti  {str(r['nome'])[:30]:30s} {r['motivo']:22s} {r['destinazione']}" for r in escl[:20]),
          "", "== Controlli ==", *("  " + x for x in c.righe)]
    RAPPORTO.write_text("\n".join(rr) + "\n", encoding="utf-8")
    print(f"Scritto: {OUT}\nScritto: {RAPPORTO}\nDurata {time.time() - t0:.0f} s; avvisi: {len(c.avvisi())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
