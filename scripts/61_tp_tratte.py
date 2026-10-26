# -*- coding: utf-8 -*-
"""
scripts/61_tp_tratte.py - Pacchetto D (Fase 5), parte 2: copertura TP delle tratte.

Per ogni TRATTA (script 57) calcola la copertura del trasporto pubblico usando
SOLO le coordinate delle fermate (mai i nomi):

  - copertura_300 = quota di lunghezza entro 300 m da una fermata bus/tram con
    almeno 4 partenze/ora in punta (7-9);
  - freq_max_300, n_linee_300, n_fermate_300, dist_mediana_fermata_m;
  - metro_600 / ferrovia_600 (stazione entro 600 m) e copertura_con_metro
    (bus/tram oppure stazione);
  - sensibilita': raggi 200/400 m e soglie 6/h, 2/h.

Diagnostica richiesta dal piano: spiega perche' nella Fase 4 Corso Cairoli
risultava con le linee 24 e 93 ma 0,0 passaggi/ora (e Corso Fiume 1 linea, 0,0).

Output: data/processed/traffico_d/tp_tratte.csv
        docs/rapporti/RAPPORTO_TP_ACCESSIBILITA.txt
"""

import csv
import json
import math
import sys
from collections import defaultdict
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
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_TP_ACCESSIBILITA.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

RAGGIO = 300.0
SOGLIA_MIN = 4.0


class GrigliaStops:
    def __init__(self, stops, cella_m=300.0):
        self.stops = stops
        self.lat0 = 45.0
        self.cell_lat = cella_m / 110540.0
        self.cell_lon = cella_m / (111320.0 * math.cos(math.radians(self.lat0)))
        self.g = defaultdict(list)
        for i, s in enumerate(stops):
            self.g[self._cella(s["lat"], s["lon"])].append(i)

    def _cella(self, la, lo):
        return (math.floor(la / self.cell_lat), math.floor(lo / self.cell_lon))

    def vicini(self, la, lo, raggio_m):
        n = int(raggio_m / 300.0) + 1
        ci, cj = self._cella(la, lo)
        out = []
        for di in range(-n, n + 1):
            for dj in range(-n, n + 1):
                out.extend(self.g.get((ci + di, cj + dj), ()))
        return out


def ricampiona(geom, passo_m=50.0):
    out = [geom[0]]
    acc = 0.0
    for k in range(len(geom) - 1):
        d = rete_osm.haversine_m(geom[k][1], geom[k][0], geom[k + 1][1], geom[k + 1][0])
        if d <= 0:
            continue
        acc += d
        if acc >= passo_m:
            out.append(geom[k + 1]); acc = 0.0
    if out[-1] != geom[-1]:
        out.append(geom[-1])
    return out


def punti_ferrovia(pbf):
    import osmium
    pts = []

    class H(osmium.SimpleHandler):
        def node(self, n):
            if (n.tags.get("railway") or "") in ("station", "halt"):
                pts.append((n.location.lat, n.location.lon))

        def way(self, w):
            if (w.tags.get("railway") or "") in ("rail", "light_rail", "narrow_gauge"):
                if (w.tags.get("tunnel") or "").lower() in ("yes", "building_passage"):
                    return
                try:
                    for nd in w.nodes:
                        pts.append((nd.location.lat, nd.location.lon))
                except Exception:
                    pass

    H().apply_file(str(pbf), locations=True)
    return pts


def main():
    # fermate bus/tram e metro
    stops = []
    with (OUT / "tp_fermate.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            stops.append({
                "fermata": r["fermata"], "lat": float(r["lat"]), "lon": float(r["lon"]),
                "am": float(r["partenze_ora_am"]), "pm": float(r["partenze_ora_pm"]),
                "giorno": int(r["partenze_giorno_6_21"]), "n_linee": int(r["n_linee"]),
                "linee": set(x for x in r["linee"].split("|") if x),
                "tipo": r["tipo"],
            })
    bus = [s for s in stops if s["tipo"] == "bus_tram"]
    metro = [s for s in stops if s["tipo"] == "metro"]
    print(f"fermate bus/tram: {len(bus):,}  metro: {len(metro):,}")

    g_bus = GrigliaStops(bus)
    g_metro = GrigliaStops(metro)
    ferro_pts = punti_ferrovia(RAW.parent / "otp" / "rete" / "torino_cintura.osm.pbf")
    print(f"punti ferroviari OSM: {len(ferro_pts):,}")
    g_ferro = GrigliaStops([{"lat": la, "lon": lo} for (la, lo) in ferro_pts])

    # diagnostica Fase 4: passaggi per corridoio (vecchio metodo)
    vecchio = {}
    f4 = PROC / "tp_corridoi.json"
    if f4.is_file():
        for o in json.loads(f4.read_text(encoding="utf-8"))["corridoi"]:
            vecchio[o["nome"]] = o

    def analizza(camp, raggio, soglia):
        n_cop = 0
        freq_max = 0.0
        fermate_vicine = set()
        linee_vicine = set()
        for (lo, la) in camp:
            trov = False
            for i in g_bus.vicini(la, lo, raggio):
                s = bus[i]
                if rete_osm.haversine_m(la, lo, s["lat"], s["lon"]) <= raggio:
                    if s["am"] >= soglia:
                        trov = True
                        freq_max = max(freq_max, s["am"])
                        fermate_vicine.add(s["fermata"])
                        linee_vicine |= s["linee"]
            if trov:
                n_cop += 1
        return (n_cop / max(len(camp), 1), freq_max, fermate_vicine, linee_vicine)

    def distanza_min(camp, raggio=1000.0):
        dmin = []
        for (lo, la) in camp:
            best = raggio
            for i in g_bus.vicini(la, lo, raggio):
                s = bus[i]
                d = rete_osm.haversine_m(la, lo, s["lat"], s["lon"])
                if d < best:
                    best = d
            dmin.append(best)
        return dmin

    righe_out = []
    with (OUT / "tratte.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            geom = []
            inner = r["geom_wkt"][r["geom_wkt"].find("(") + 1:r["geom_wkt"].rfind(")")]
            for coppia in inner.split(","):
                x, y = coppia.split()
                geom.append((float(x), float(y)))
            camp = ricampiona(geom, 50.0)
            cop300, fmax, ferm, lin = analizza(camp, RAGGIO, SOGLIA_MIN)
            cop200 = analizza(camp, 200.0, SOGLIA_MIN)[0]
            cop400 = analizza(camp, 400.0, SOGLIA_MIN)[0]
            cop300_6 = analizza(camp, RAGGIO, 6.0)[0]
            cop300_2 = analizza(camp, RAGGIO, 2.0)[0]
            dm = distanza_min(camp)
            # metro / ferrovia entro 600 m
            m600 = f600 = False
            for (lo, la) in camp:
                if not m600:
                    for i in g_metro.vicini(la, lo, 600.0):
                        s = metro[i]
                        if rete_osm.haversine_m(la, lo, s["lat"], s["lon"]) <= 600.0:
                            m600 = True; break
                if not f600:
                    for i in g_ferro.vicini(la, lo, 600.0):
                        s = ferro_pts[i]
                        if rete_osm.haversine_m(la, lo, s[0], s[1]) <= 600.0:
                            f600 = True; break
                if m600 and f600:
                    break
            # copertura con metro/ferrovia: punto coperto se fermata con >=4/h entro 300
            # oppure stazione entro 600
            n_cop_m = 0
            for (lo, la) in camp:
                ok = False
                for i in g_bus.vicini(la, lo, RAGGIO):
                    s = bus[i]
                    if s["am"] >= SOGLIA_MIN and rete_osm.haversine_m(la, lo, s["lat"], s["lon"]) <= RAGGIO:
                        ok = True; break
                if not ok:
                    for i in g_metro.vicini(la, lo, 600.0):
                        s = metro[i]
                        if rete_osm.haversine_m(la, lo, s["lat"], s["lon"]) <= 600.0:
                            ok = True; break
                if not ok:
                    for i in g_ferro.vicini(la, lo, 600.0):
                        s = ferro_pts[i]
                        if rete_osm.haversine_m(la, lo, s[0], s[1]) <= 600.0:
                            ok = True; break
                if ok:
                    n_cop_m += 1
            cop_con_metro = n_cop_m / max(len(camp), 1)
            dm_med = float(np.median(dm)) if dm else None
            righe_out.append({
                "id_tratta": int(r["id_tratta"]), "id_asse": int(r["id_asse"]),
                "nome": r["nome_principale"], "comune": r["comune"], "quartiere": r["quartiere"],
                "copertura_300": round(cop300, 3), "copertura_200": round(cop200, 3),
                "copertura_400": round(cop400, 3), "copertura_300_soglia6": round(cop300_6, 3),
                "copertura_300_soglia2": round(cop300_2, 3),
                "freq_max_300": round(fmax, 2), "n_linee_300": len(lin),
                "n_fermate_300": len(ferm), "dist_mediana_fermata_m": None if dm_med is None else round(dm_med, 0),
                "metro_600": bool(m600), "ferrovia_600": bool(f600),
                "copertura_con_metro": round(cop_con_metro, 3),
                "linee_300": "|".join(sorted(lin)[:12]),
            })

    with (OUT / "tp_tratte.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["id_tratta", "id_asse", "nome", "comune", "quartiere", "copertura_300",
                    "copertura_200", "copertura_400", "copertura_300_soglia6",
                    "copertura_300_soglia2", "freq_max_300", "n_linee_300", "n_fermate_300",
                    "dist_mediana_fermata_m", "metro_600", "ferrovia_600",
                    "copertura_con_metro", "linee_300"])
        for o in righe_out:
            w.writerow([o["id_tratta"], o["id_asse"], o["nome"] or "", o["comune"] or "",
                        o["quartiere"] or "", o["copertura_300"], o["copertura_200"],
                        o["copertura_400"], o["copertura_300_soglia6"], o["copertura_300_soglia2"],
                        o["freq_max_300"], o["n_linee_300"], o["n_fermate_300"],
                        o["dist_mediana_fermata_m"], int(o["metro_600"]), int(o["ferrovia_600"]),
                        o["copertura_con_metro"], o["linee_300"]])

    # --- controlli di buon senso ---
    righe = []
    def a_(s=""):
        righe.append(s)
    a_("COPERTURA DEL TRASPORTO PUBBLICO PER TRATTA (pacchetto D, Fase 5)")
    a_("=" * 76)
    a_("Principio: SOLO coordinate delle fermate (mai i nomi). Coperta = fermata bus/tram")
    a_(f"con >= {SOGLIA_MIN:.0f} partenze/ora in punta mattina entro {RAGGIO:.0f} m.")
    a_(f"tratte analizzate: {len(righe_out):,}")
    a_("")
    cop = np.array([o["copertura_300"] for o in righe_out])
    a_("== Sensibilita' (quante tratte cambiano gruppo 'coperta' a >=50% di lunghezza) ==")
    base = cop >= 0.5
    for lab, arr in [("200 m", np.array([o["copertura_200"] for o in righe_out])),
                     ("400 m", np.array([o["copertura_400"] for o in righe_out])),
                     ("soglia 6/h", np.array([o["copertura_300_soglia6"] for o in righe_out])),
                     ("soglia 2/h", np.array([o["copertura_300_soglia2"] for o in righe_out]))]:
        alt = arr >= 0.5
        a_(f"  {lab:12s}: coperta {alt.sum():6d}  cambiano rispetto a 300m/4h: "
           f"{int((alt != base).sum()):5d}")
    a_(f"  base 300m/4h: coperta {int(base.sum())} su {len(base)} "
       f"({100*base.mean():.1f}%)")
    a_(f"  con metro/ferrovia (copertura_con_metro>=0.5): "
       f"{int((np.array([o['copertura_con_metro'] for o in righe_out])>=0.5).sum())}")
    a_("")
    a_("== Controlli di buon senso (per posizione): tratte note devono avere copertura alta ==")
    per_nome = defaultdict(list)
    for o in righe_out:
        if o["comune"] == "Torino":
            per_nome[(o["nome"] or "").lower()].append(o)
    for chiave in ["francia", "regina margherita", "nizza", "vittorio emanuele ii",
                   "giulio cesare", "cairoli", "fiume"]:
        voci = [v for k, vv in per_nome.items() if chiave in k for v in vv]
        if not voci:
            a_(f"  {chiave:22s}: nessuna tratta col nome")
            continue
        c_max = max(v["copertura_300"] for v in voci)
        c_med = float(np.median([v["copertura_300"] for v in voci]))
        fmax = max(v["freq_max_300"] for v in voci)
        a_(f"  {chiave:22s}: {len(voci):4d} tratte  copertura300 max {c_max:.2f} / mediana "
           f"{c_med:.2f}  freq max {fmax:.1f}/h")
    a_("")
    a_("== 10 tratte con copertura 0 (giudizio dell'agente) ==")
    zero = [o for o in righe_out if o["copertura_300"] == 0 and o["comune"] == "Torino"]
    zero.sort(key=lambda o: (o["dist_mediana_fermata_m"] or 0))
    for o in zero[:10]:
        a_(f"  {str(o['nome'])[:30]:30s} {str(o['quartiere']):5s} "
           f"fermata piu' vicina {o['dist_mediana_fermata_m']} m  ({o['n_fermate_300']} entro 300 m)")
    a_("")
    a_("== DIAGNOSTICA richiesta: Corso Cairoli e Corso Fiume (metodo vecchio vs nuovo) ==")
    for nome in ["Cairoli", "Fiume"]:
        # vecchio metodo
        vecchi = {k: v for k, v in vecchio.items() if nome.lower() in k.lower()}
        a_(f"  {nome} - metodo vecchio (Fase 4, passaggi sulla strada):")
        for k, v in vecchi.items():
            a_(f"      {k}: passaggi ora punta am = {v.get('passaggi_ora_punta_am_max')} "
               f"(max), linee {v.get('n_linee')}, km coperti {v.get('km_coperti')}")
        # nuovo metodo: tratte con questo nome e le fermate vicine
        voci = [v for k, vv in per_nome.items() if nome.lower() in k for v in vv]
        a_(f"      nuovo metodo (posizione fermate): {len(voci)} tratte "
           f"copertura300 max {max((v['copertura_300'] for v in voci), default=0):.2f}, "
           f"freq max {max((v['freq_max_300'] for v in voci), default=0):.1f}/h")
        # fermate entro 300 m dalla tratta peggiore
        if voci:
            peggiore = min(voci, key=lambda v: v["copertura_300"])
            # trova le fermate vicine al centro della tratta
            with (OUT / "tratte.csv").open(encoding="utf-8", newline="") as fh:
                for r in csv.DictReader(fh, delimiter=";"):
                    if int(r["id_tratta"]) == peggiore["id_tratta"]:
                        inner = r["geom_wkt"][r["geom_wkt"].find("(") + 1:r["geom_wkt"].rfind(")")]
                        coppie = inner.split(",")
                        x, y = coppie[len(coppie) // 2].split()
                        la0, lo0 = float(y), float(x)
                        break
            vic = []
            for i in g_bus.vicini(la0, lo0, 300.0):
                s = bus[i]
                d = rete_osm.haversine_m(la0, lo0, s["lat"], s["lon"])
                if d <= 300:
                    vic.append((round(d), s["fermata"], s["am"], sorted(s["linee"])[:6]))
            vic.sort()
            a_(f"      fermate entro 300 m dal punto medio della tratta {peggiore['id_tratta']}:")
            for d, fid, am, li in vic[:8]:
                a_(f"        {d:4d} m  fermata {fid}  {am:.1f} partenze/h  linee {','.join(li)}")
    a_("")
    a_("Vedi anche docs/rapporti/RAPPORTO_TP_PER_STRADA.txt (metodo vecchio) per il confronto.")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))
    print(f"\nScritto {OUT/'tp_tratte.csv'}")


if __name__ == "__main__":
    main()
