#!/usr/bin/env python3
"""92 - Esposizione al traffico dei residenti di Torino (Piano risultati A3). SOLA LETTURA.

Domanda: quanti residenti vivono a meno di 100 m da una strada molto trafficata?
Il traffico e' il miglior sostituto che abbiamo di rumore e smog (che non misuriamo): e' una STIMA DEBOLE.

Dati letti (mai modificati):
  data/processed/traffico_d/tratte_traffico.json   tratte con veic_giorno stimato (script 65)
  data/processed/traffico_d/tratte.csv             geometria delle tratte (WKT "lon lat", script 57)
  data/processed/sezioni_torino.json               sezioni di censimento (id, c, p, a, g)
  data/processed/risultato8_traffico_tp_v2.json    solo per un controllo sul numero di tratte (facoltativo)

Regole:
  - tratta "molto trafficata" = nell'universo delle strade grandi di Torino del R8 (script 66: comune Torino,
    punteggio >= 3, lunghezza >= 300 m, stima affidabile, niente autostrade, rango < 5) con almeno 11.720 veicoli
    al giorno (la stessa soglia del R8: terzo piu' alto e dentro l'intervallo validato);
  - sezioni: Torino, abitate (almeno 1.000 ab/km2; senza superficie contano come abitate, come nello script 21);
  - distanza = dal centro della sezione (centroide d'area) alla tratta molto trafficata piu' vicina, in metri;
  - classi: esposta (meno di 100 m), vicina (da 100 a 250 m), lontana (oltre 250 m).

Uscite:
  data/processed/esposizione_traffico.json
  docs/rapporti/RAPPORTO_ESPOSIZIONE_TRAFFICO.txt   (residenti per classe e, se il campo esiste, per circoscrizione)

Controlli: le somme per classe tornano al totale delle zone abitate, nessuna distanza negativa, numero di tratte uguale
a quello del R8 (AVVISO se diverso).

Uso:  python scripts/92_esposizione_traffico.py
"""
import csv
import datetime as dt
import json
import math
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
SEZIONI = RADICE / "data/processed/sezioni_torino.json"
DIR_TRAFFICO = RADICE / "data/processed/traffico_d"
TRATTE = DIR_TRAFFICO / "tratte_traffico.json"
TRATTE_CSV = DIR_TRAFFICO / "tratte.csv"
R8 = RADICE / "data/processed/risultato8_traffico_tp_v2.json"
OUT = RADICE / "data/processed/esposizione_traffico.json"
RAPPORTO = RADICE / "docs/rapporti/RAPPORTO_ESPOSIZIONE_TRAFFICO.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

COMUNE_TORINO = 1272
SOGLIA_MOLTO_TRAFFICO = 11720      # veicoli/giorno, 6-21, due versi: il valore di riserva; di norma si legge la soglia del R8 (terzo piu' alto, cambia con i dati)
RAGGIO_ESPOSTA_M = 100.0
RAGGIO_VICINA_M = 250.0
SOGLIA_ABITATA = 1000              # ab/km2
CLASSI = ("esposta", "vicina", "lontana")
CAMPI_CIRCOSCRIZIONE = ("circoscrizione", "circ", "cir")
CAMPI_TRATTA = ("id", "comune", "punteggio", "lunghezza_m", "affidabile", "classe", "rango", "veic_giorno")
CLASSI_STRADA_ESCLUSE = ("motorway", "trunk", "motorway_link", "trunk_link")


def centroide(anello):
    """Centroide d'area di un anello [[lat,lon],...]; None se l'area e' nulla (come nello script 18)."""
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(anello, anello[1:]):
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    if abs(a) < 1e-15:
        return None
    return (cx / (3 * a), cy / (3 * a))


def dist_punto_polilinea_m(px, py, punti):
    """Distanza minima in metri fra un punto e una polilinea (coordinate piane in metri)."""
    migliore = math.inf
    for (ax, ay), (bx, by) in zip(punti, punti[1:]):
        dx, dy = bx - ax, by - ay
        t = 0.0 if dx == 0 and dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        migliore = min(migliore, math.hypot(px - (ax + t * dx), py - (ay + t * dy)))
    return migliore


def geometrie_da_csv():
    """{id tratta: [(x, y) in metri]} da tratte.csv (WKT LINESTRING(lon lat, lon lat, ...))."""
    out = {}
    with TRATTE_CSV.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            w = r["geom_wkt"]
            coppie = w[w.find("(") + 1:w.rfind(")")].split(",")
            punti = []
            for c in coppie:
                lon, lat = (float(v) for v in c.split())
                punti.append(comuni.proietta(lat, lon))
            out[int(r["id_tratta"])] = punti
    return out


def soglia_r8():
    """La soglia del R8 (universo_torino.soglie.q66 di risultato8_traffico_tp_v2.json); se il file manca, il valore di riserva."""
    if R8.is_file():
        try:
            return int(json.loads(R8.read_text(encoding="utf-8"))["universo_torino"]["soglie"]["q66"])
        except (KeyError, ValueError):
            pass
    return SOGLIA_MOLTO_TRAFFICO


def tratte_molto_trafficate(doc, soglia):
    """Tratte dell'universo di Torino del R8 con veic_giorno >= soglia."""
    tratte = doc["tratte"]
    mancano = [c for c in CAMPI_TRATTA if tratte and c not in tratte[0]]
    if mancano:
        sys.exit(f"ERRORE: campi {mancano} non trovati in {TRATTE.name}; campi presenti: {sorted(tratte[0])}")
    scelte = [o for o in tratte
              if o["comune"] == "Torino" and o["punteggio"] >= 3 and o["lunghezza_m"] >= 300 and o["affidabile"]
              and o["classe"] not in CLASSI_STRADA_ESCLUSE and o["rango"] < 5 and o["veic_giorno"] > 0]
    return scelte, [o for o in scelte if o["veic_giorno"] >= soglia]


def classe_di(d):
    return "esposta" if d < RAGGIO_ESPOSTA_M else "vicina" if d <= RAGGIO_VICINA_M else "lontana"


def riepilogo(sezioni):
    """Residenti e sezioni per classe, in un sottoinsieme di sezioni [{"res", "classe"}]."""
    tot = sum(s["res"] for s in sezioni)
    r = {c: {"residenti": 0, "sezioni": 0} for c in CLASSI}
    for s in sezioni:
        r[s["classe"]]["residenti"] += s["res"]
        r[s["classe"]]["sezioni"] += 1
    for c in CLASSI:
        r[c]["quota"] = round(100.0 * r[c]["residenti"] / tot, 2) if tot else None
    return {"residenti": tot, "classi": r}


def main():
    controlli = comuni.Controlli()
    for f in (SEZIONI, TRATTE, TRATTE_CSV):
        if not f.is_file():
            sys.exit(f"ERRORE: manca {f}")
    doc = json.loads(TRATTE.read_text(encoding="utf-8"))
    soglia = soglia_r8()
    universo, molto = tratte_molto_trafficate(doc, soglia)
    fascia = round(doc["taratura"]["fascia_50"] * 100)   # «sbaglia del ±X%» in meta' dei casi
    print(f"Tratte: {len(doc['tratte'])} in tutto, {len(universo)} nell'universo di Torino, "
          f"{len(molto)} molto trafficate (>= {soglia:,} veicoli/giorno)")
    controlli("ci sono tratte molto trafficate", len(molto) > 0, bloccante=True, dettaglio=f"{len(molto)}")
    if R8.is_file():
        n_r8 = json.loads(R8.read_text(encoding="utf-8"))["conteggi"]["molto_traffico"]
        controlli("tratte molto trafficate = quelle del R8", len(molto) == n_r8, dettaglio=f"qui {len(molto)}, R8 {n_r8}")

    geom = geometrie_da_csv()
    senza_geom = [o["id"] for o in molto if o["id"] not in geom]
    controlli("tutte le tratte hanno la geometria", not senza_geom, bloccante=True, dettaglio=f"senza: {senza_geom[:5]}")
    linee = []   # (bounding box, punti)
    for o in molto:
        p = geom[o["id"]]
        xs, ys = [q[0] for q in p], [q[1] for q in p]
        linee.append(((min(xs), min(ys), max(xs), max(ys)), p))
    km = sum(o["lunghezza_m"] for o in molto) / 1000.0

    # sezioni abitate di Torino
    sezioni_geo = json.loads(SEZIONI.read_text(encoding="utf-8"))
    righe, circ_trovata = [], False
    for s in sezioni_geo:
        if s.get("c") != COMUNE_TORINO or s.get("p", 0) <= 0 or not s.get("g"):
            continue
        a = s.get("a")
        if a and a > 0 and s["p"] / a < SOGLIA_ABITATA:
            continue
        cen = centroide(s["g"][0]) or tuple(s["g"][0][0])
        px, py = comuni.proietta(cen[0], cen[1])
        d = math.inf
        for (x0, y0, x1, y1), p in linee:
            # salta le tratte che non possono battere la distanza gia' trovata
            if math.hypot(max(x0 - px, 0, px - x1), max(y0 - py, 0, py - y1)) > d:
                continue
            d = min(d, dist_punto_polilinea_m(px, py, p))
        circ = next((str(s[c]) for c in CAMPI_CIRCOSCRIZIONE if s.get(c) not in (None, "")), None)
        circ_trovata = circ_trovata or circ is not None
        righe.append({"id": str(s["id"]), "res": s["p"], "dist_m": d, "classe": classe_di(d), "circ": circ})
    controlli("ci sono sezioni abitate", len(righe) > 0, bloccante=True, dettaglio=f"{len(righe)}")
    controlli("nessuna distanza negativa", all(r["dist_m"] >= 0 for r in righe), bloccante=True)
    controlli("tutte le distanze calcolate", all(math.isfinite(r["dist_m"]) for r in righe), bloccante=True)

    tot = riepilogo(righe)
    somma = sum(c["residenti"] for c in tot["classi"].values())
    controlli("somma dei residenti per classe = zone abitate", somma == tot["residenti"], bloccante=True,
              dettaglio=f"{somma:,} / {tot['residenti']:,}")
    controlli("somma delle sezioni per classe = zone abitate",
              sum(c["sezioni"] for c in tot["classi"].values()) == len(righe), bloccante=True)
    quota_esposti = tot["classi"]["esposta"]["quota"]
    controlli("gli esposti sono una minoranza (sotto il 50%)", quota_esposti < 50, dettaglio=f"{quota_esposti}%")

    if circ_trovata:
        circoscrizioni = {}
        for c in sorted({r["circ"] for r in righe if r["circ"] is not None}):
            circoscrizioni[c] = riepilogo([r for r in righe if r["circ"] == c])
        somma_c = sum(v["residenti"] for v in circoscrizioni.values())
        controlli("somma delle circoscrizioni = zone abitate", somma_c == sum(r["res"] for r in righe if r["circ"] is not None),
                  bloccante=True, dettaglio=f"{somma_c:,}")
        nota_circ = None
    else:
        circoscrizioni = None
        nota_circ = ("Per circoscrizione saltato: le sezioni di sezioni_torino.json non hanno il campo "
                     f"({', '.join(CAMPI_CIRCOSCRIZIONE)}).")
        print("  " + nota_circ)

    avviso = f"stima debole: il modello del traffico sbaglia del ±{fascia}%"
    esito = {
        "generato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stimato": True,
        "avviso": avviso,
        "parametri": {"soglia_molto_traffico_veic_giorno": soglia, "raggio_esposta_m": RAGGIO_ESPOSTA_M,
                      "raggio_vicina_m": RAGGIO_VICINA_M, "soglia_abitata_ab_km2": SOGLIA_ABITATA,
                      "fascia_errore_pct": fascia},
        "tratte": {"molto_trafficate": len(molto), "universo_torino": len(universo), "km_molto_trafficate": round(km, 1)},
        "residenti_zone_abitate": tot["residenti"],
        "sezioni_zone_abitate": len(righe),
        "classi": tot["classi"],
        "circoscrizioni": circoscrizioni,
        "nota_circoscrizioni": nota_circ,
        "sezioni": [{"id": r["id"], "classe": r["classe"], "dist_m": round(r["dist_m"], 1)} for r in righe],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(esito, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Scritto {OUT}")

    nomi = {"esposta": f"esposta (a meno di {RAGGIO_ESPOSTA_M:.0f} m)",
            "vicina": f"vicina ({RAGGIO_ESPOSTA_M:.0f}-{RAGGIO_VICINA_M:.0f} m)",
            "lontana": f"lontana (oltre {RAGGIO_VICINA_M:.0f} m)"}
    out = ["RAPPORTO ESPOSIZIONE AL TRAFFICO (Piano risultati A3, STIMATO)",
           f"generato: {esito['generato']}",
           avviso,
           "",
           f"Strade molto trafficate: {len(molto)} tratte, {km:,.1f} km, almeno {soglia:,} veicoli al giorno "
           f"(stessa soglia del R8; universo: strade grandi di Torino, {len(universo)} tratte).",
           f"Residenti: zone abitate di Torino (almeno {SOGLIA_ABITATA:,} ab/km2), {tot['residenti']:,} residenti in {len(righe):,} sezioni.",
           "Distanza dal centro della sezione alla tratta molto trafficata piu' vicina.",
           "",
           "RESIDENTI PER CLASSE"]
    for c in CLASSI:
        r = tot["classi"][c]
        out.append(f"  {nomi[c]:28s} {r['residenti']:>9,} residenti  {r['quota']:>5}%  ({r['sezioni']:,} sezioni)")
    out += ["", "PER CIRCOSCRIZIONE"]
    if circoscrizioni:
        for c, v in circoscrizioni.items():
            out.append(f"  {c}: {v['residenti']:,} residenti; " + "; ".join(
                f"{k} {v['classi'][k]['residenti']:,} ({v['classi'][k]['quota']}%)" for k in CLASSI))
    else:
        out.append("  " + nota_circ)
    out += ["", "CONTROLLI"] + [f"  {r}" for r in controlli.righe]
    out += ["", "LIMITI: il traffico e' una stima (classe C-DEBOLE) e sostituisce rumore e smog, che non misuriamo; "
                "si guarda il centro della sezione, non le case; non contano strade fuori dall'universo del R8 "
                "(autostrade, tangenziale, strade piccole); le strade fuori Torino non sono incluse."]
    RAPPORTO.write_text("\n".join(out), encoding="utf-8")
    print(f"Scritto {RAPPORTO}")


if __name__ == "__main__":
    main()
