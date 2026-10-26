#!/usr/bin/env python3
"""Servizi OSM della cintura: SOLO i punti FUORI dal Comune di Torino.

Il confine e' il perimetro unito delle sezioni di censimento con comune 1272
(sezioni_torino.json): un punto OSM e' dentro Torino se cade dentro l'anello
(per lo strano caso dei fori, si guarda la parita' sui rings della sezione).

In piu' conta i punti OSM DENTRO Torino e li confronta col catalogo comunale
(istruzione/salute/commercio): il rapporto dice quanto la fonte OSM copre e
quanto la cintura resta sottostimata al confine (da dichiarare in mappa).
"""
import datetime as dt
import json
import math
from pathlib import Path

import osmium

RADICE = Path(__file__).resolve().parent.parent
PBF = RADICE / "data/otp/rete/torino_cintura.osm.pbf"
SEZIONI = RADICE / "data/processed/sezioni_torino.json"
OUT = RADICE / "data/processed/servizi_osm_cintura.json"
CATALOGO = RADICE / "data/processed/catalogo"

GRUPPI = {"scuole": "istruzione", "salute": "salute", "cibo": "commercio"}
CELLA = 0.01  # griglia di ~1 km per la ricerca dei poligoni candidati

SCHOOL_AMENITY = {"school", "kindergarten", "childcare", "college", "university"}
HEALTH_AMENITY = {"pharmacy", "hospital", "clinic", "doctors", "dentist"}


def in_anello(la, lo, anello):
    """Ray casting su un anello [[lat,lon],...]: raggio verso est."""
    dentro = False
    j = len(anello) - 1
    for i in range(len(anello)):
        lai, loi = anello[i]
        laj, loj = anello[j]
        if (lai > la) != (laj > la):
            lo_bordo = loi + (loj - loi) * (la - lai) / (laj - lai)
            if lo < lo_bordo:
                dentro = not dentro
        j = i
    return dentro


class Perimetro:
    """Poligoni delle sezioni di comune 1272, con griglia spaziale per non
    testare un punto contro Duemila sezioni."""

    def __init__(self):
        sezioni = json.loads(SEZIONI.read_text(encoding="utf-8"))
        self.anelli = []   # per sezione: lista di anelli (per gestire multi-part e fori)
        self.griglia = {}  # (celLa_lat, cella_lon) -> [indice sezione]
        self.bbox = None
        for s in sezioni:
            if str(s.get("c")) != "1272" or not s.get("g"):
                continue
            indice = len(self.anelli)
            self.anelli.append(s["g"])
            for anello in s["g"]:
                las = [p[0] for p in anello]
                los = [p[1] for p in anello]
                b = (min(las), min(los), max(las), max(los))
                if self.bbox is None:
                    self.bbox = b
                else:
                    self.bbox = (min(self.bbox[0], b[0]), min(self.bbox[1], b[1]),
                                 max(self.bbox[2], b[2]), max(self.bbox[3], b[3]))
                for cla in range(int(math.floor(b[0] / CELLA)), int(math.floor(b[2] / CELLA)) + 1):
                    for clo in range(int(math.floor(b[1] / CELLA)), int(math.floor(b[3] / CELLA)) + 1):
                        self.griglia.setdefault((cla, clo), []).append(indice)
        self.bbox = (self.bbox[0] - 0.002, self.bbox[1] - 0.002,
                     self.bbox[2] + 0.002, self.bbox[3] + 0.002)
        self.sondaggi = 0

    def dentro(self, la, lo):
        """True se il punto cade nel perimetro di Torino (comune 1272)."""
        if not (self.bbox[0] <= la <= self.bbox[2] and self.bbox[1] <= lo <= self.bbox[3]):
            return False
        for indice in self.griglia.get((int(math.floor(la / CELLA)),
                                        int(math.floor(lo / CELLA))), []):
            self.sondaggi += 1
            if any(in_anello(la, lo, anello) for anello in self.anelli[indice]):
                return True
        return False


class Estrattore(osmium.SimpleHandler):
    def __init__(self, perimetro):
        super().__init__()
        self.perimetro = perimetro
        self.fuori = {g: [] for g in GRUPPI}
        self.dentro = {g: 0 for g in GRUPPI}

    @staticmethod
    def categoria(amenity, healthcare, shop):
        """Ritorna "scuole" / "salute" / "cibo" / None. Un punto vale piu'
        gruppi se porta piu' tag (contato in entrambi)."""
        out = []
        if amenity in SCHOOL_AMENITY:
            out.append("scuole")
        if amenity in HEALTH_AMENITY or healthcare:
            out.append("salute")
        if shop or amenity == "marketplace":
            out.append("cibo")
        return out

    def punto(self, la, lo, amenity, healthcare, shop):
        cats = self.categoria(amenity, healthcare, shop)
        if not cats:
            return
        if self.perimetro.dentro(la, lo):
            for g in cats:
                self.dentro[g] += 1
        else:
            for g in cats:
                self.fuori[g].append((round(la, 6), round(lo, 6)))

    def node(self, n):
        if not n.location.valid():
            return
        self.punto(n.location.lat, n.location.lon, n.tags.get("amenity", ""),
                   n.tags.get("healthcare", ""), n.tags.get("shop", ""))

    def way(self, w):
        if not w.is_closed():
            return
        las = []
        los = []
        for nd in w.nodes:
            if nd.location.valid():
                las.append(nd.location.lat)
                los.append(nd.location.lon)
        if not las:
            return
        self.punto(sum(las) / len(las), sum(los) / len(los), w.tags.get("amenity", ""),
                   w.tags.get("healthcare", ""), w.tags.get("shop", ""))


def punti_catalogo(gruppo):
    """Numero di punti validi nel catalogo comunale di quel gruppo."""
    d = json.loads((CATALOGO / f"{GRUPPI[gruppo]}.json").read_text(encoding="utf-8"))
    n = 0
    for ds in d["dati"]:
        for el in ds.get("elementi", []):
            try:
                float(el[0])
                float(el[1])
                n += 1
            except (TypeError, ValueError, IndexError):
                pass
    return n


def main():
    perimetro = Perimetro()
    b = perimetro.bbox
    print(f"Perimetro Torino (sezioni 1272): lon {b[1]:.3f}-{b[3]:.3f}", end="")
    print(f" lat {b[0]:.3f}-{b[2]:.3f}, "
          f"{len(perimetro.anelli)} sezioni, {len(perimetro.griglia)} celle griglia")

    print(f"Estraggo da {PBF.name}...")
    e = Estrattore(perimetro)
    e.apply_file(str(PBF), locations=True)

    confronto = {}
    for g in GRUPPI:
        n_cat = punti_catalogo(g)
        n_osm_dentro = e.dentro[g]
        confronto[g] = {
            "catalogo_torino": n_cat,
            "osm_dentro_torino": n_osm_dentro,
            "osm_fuori_torino": len(e.fuori[g]),
            "rapporto_osm_catalogo": round(n_osm_dentro / n_cat, 3) if n_cat else None,
            "nota": "OSM conta oggetti con tag, il catalogo comunale punti gestiti: "
                    "parentele diverse, il numero serve a stimare la copertura.",
        }
        print(f"  {g}: OSM dentro Torino {n_osm_dentro} contro catalogo {n_cat} "
              f"({confronto[g]['rapporto_osm_catalogo']}x); fuori Torino {len(e.fuori[g])}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "generato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "fonte": "OSM tramite pyosmium",
        "avviso": "Servizi OSM della cintura di Torino. SOLO punti fuori dal Comune "
                  "(perimetro delle sezioni di comune 1272, controllo punto-in-poligono). "
                  "Il conteggio DENTRO Torino e' riportato solo per il confronto col catalogo.",
        "servizi": {
            g: [{"lat": la, "lon": lo, "fonte": "OSM"} for (la, lo) in punti]
            for g, punti in e.fuori.items()
        },
        "confronto_torino": confronto,
        "parametri": {
            "file_osm": str(PBF),
            "confine_citta": "perimetro unito delle sezioni di censimento ISTAT 2021 "
                             "con comune 1272 (sezioni_torino.json)",
            "griglia_cella_gradi": CELLA,
            "nodi_detti_candidati": perimetro.sondaggi,
        },
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Scritto {OUT}")


if __name__ == "__main__":
    main()
