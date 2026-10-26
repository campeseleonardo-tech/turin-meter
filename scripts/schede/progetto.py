"""Dati di progetto.html (data/progetto.js): contatore della raccolta, zone di Torino con le 5 in doppio svantaggio, confronto feed-GPS dei ritardi.

Tutto viene da file gia' prodotti: data/storico_riassunti (contatore, come la home), data/processed/velocita_5t.json (numero di sensori),
case_fragilita_servizi.json (script 95) e omi_zone.json (poligoni delle zone OMI; se manca, come nel cloud, si riusano quelli gia' scritti in data/progetto.js),
risultato4_regolarita.json (script 27), accessibilita.json (sezioni di censimento analizzate; se manca si riusa il numero gia' in data/progetto.js), data/ref/numeri_progetto.json (fonti, settimane), assets/torino_contorno.json.
I numeri dei risultati (forbice mezzi/auto, minuti di pareggio, ...) la pagina li legge dalle schede (data/schede_risultati.js): qui non si copiano.
Le raccomandazioni («Cosa farei») hanno i loro numeri in schede/raccomandazioni.py; il controllo dei tempi in auto viene da controllo_navigatori_riepilogo.json;
costi dell'AI e del Raspberry Pi da data/ref/lavoro_ai.json.
Nessun numero e' scritto a mano."""
import json

from schede.comune import PROC, RADICE, leggi, nome_pulito
from schede.home import contatore
from schede.raccomandazioni import calcola as raccomandazioni
from schede.r10 import nome_zona

OUT = RADICE / "data" / "progetto.js"
NUMERI_PROGETTO = RADICE / "data" / "ref" / "numeri_progetto.json"
LAVORO_AI = RADICE / "data" / "ref" / "lavoro_ai.json"   # testi personali di Leo (25/10/2026): abbonamenti AI e Raspberry Pi


def _rdp(pts, tol):
    """Douglas-Peucker su una lista di (x, y); tiene il primo e l'ultimo punto."""
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    n = (dx * dx + dy * dy) ** 0.5 or 1e-9
    dmax, k = 0.0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x1 * y0 - y1 * x0) / n
        if d > dmax:
            dmax, k = d, i
    if dmax <= tol:
        return [pts[0], pts[-1]]
    return _rdp(pts[:k + 1], tol)[:-1] + _rdp(pts[k:], tol)


def _percorso(anelli, c, tol=1.1):
    """Anelli [[lat, lon], ...] -> percorso SVG relativo (interi) nel disegno del contorno di Torino (stesse coordinate di assets/torino_contorno.json)."""
    out = ""
    for anello in anelli:
        pts = [((lon - c["lon_min"]) * c["k"] * c["scala"], (c["lat_max"] - lat) * c["scala"]) for lat, lon in anello]
        m = len(pts) // 2                                    # anello chiuso: primo e ultimo punto coincidono, si semplificano le due meta'
        pts = _rdp(pts[:m + 1], tol)[:-1] + _rdp(pts[m:], tol)
        if len(pts) < 3:
            continue
        x, y = round(pts[0][0]), round(pts[0][1])
        out += f"M{x} {y}"
        for px, py in pts[1:]:
            nx, ny = round(px), round(py)
            out += f"l{nx - x} {ny - y}"
            x, y = nx, ny
        out += "z"
    return out


def _zone_gia_scritte():
    """Le zone [(codice, percorso)] di data/progetto.js com'e' oggi: servono quando manca omi_zone.json. Senza il file non si puo' fare niente."""
    if not OUT.is_file():
        raise FileNotFoundError(2, "manca omi_zone.json e data/progetto.js non c'e'", str(PROC / "omi_zone.json"))
    dati = json.loads(OUT.read_text(encoding="utf-8").split("window.PROGETTO = ", 1)[1].rstrip().rstrip(";"))
    return [(z["cod"], z["d"]) for z in dati["zone"]]


def _sezioni_censimento():
    """Sezioni di censimento analizzate: da accessibilita.json (script 18); se manca, come nel cloud, il numero gia' scritto in data/progetto.js."""
    f = PROC / "accessibilita.json"
    if f.is_file():
        return leggi("accessibilita.json")["parametri"]["campione"]
    if not OUT.is_file():
        raise FileNotFoundError(2, "manca accessibilita.json e data/progetto.js non c'e'", str(f))
    return json.loads(OUT.read_text(encoding="utf-8").split("window.PROGETTO = ", 1)[1].rstrip().rstrip(";"))["in_numeri"]["sezioni"]


def _zone_omi(c):
    """Le zone [(codice, percorso)] di Torino: dai poligoni OMI se ci sono, altrimenti da quelli gia' scritti in data/progetto.js."""
    file = PROC / "omi_zone.json"
    if not file.is_file():
        return _zone_gia_scritte()
    omi = next(x for x in json.loads(file.read_text(encoding="utf-8")) if x["c"] == 1272)["zone"]
    return [(z["z"], _percorso(z["g"], c)) for z in omi]


def domande(r4, e2):
    """Numeri dei quattro riquadri «domanda, dati, criterio, risposta» della pagina del progetto (la risposta della D2 la legge la pagina dalla scheda)."""
    tr = leggi("dove_nascono_ritardi.json")
    primo = tr["classifica"]["punta_mattina"][0]
    mr6 = json.loads((PROC / "risultato6_v2" / "mappa_r6.json").read_text(encoding="utf-8"))
    r6 = mr6["riepilogo"]
    oltre10 = r4["forbice_lettura"]["ritardo_forbice"]["feriale_oltre10_pct"]
    return {"d1": {"giorni_feriali": len(tr["giorni_feriali"]), "oltre10_pct": [round(x, 1) for x in oltre10], "min_corse": tr["regole"]["min_corse"],
                   "primo_tratto": [nome_pulito(primo["da"]), nome_pulito(primo["a"])]},
            "d3": {"volte_il_caso": round(e2["sezioni"]["confronto_col_caso"]["volte_il_caso"], 1)},
            "d4": {"senza_posti": r6["fermate_senza_posti_bastanti"], "fermate": r6["fermate_importanti"], "nessun_parcheggio": r6["fermate_nessun_parcheggio"],
                   "raggio_m": int(mr6.get("parametri", {}).get("raggio_piedi_m", 400))}}


def scrivi_progetto():
    c = json.loads((RADICE / "assets" / "torino_contorno.json").read_text(encoding="utf-8"))
    cf = leggi("case_fragilita_servizi.json")
    e2 = cf["e2_doppio_svantaggio"]
    doppie = {z["zona"].split(" ", 1)[0]: z for z in e2["zone"]}
    zone = []
    for cod, d in _zone_omi(c):
        if not d:
            continue
        voce = {"cod": cod, "d": d}
        if cod in doppie:
            voce.update({"nome": nome_zona(doppie[cod]["zona"]), "abitanti": doppie[cod]["abitanti"], "doppio": 1})
        zone.append(voce)
    mancanti = set(doppie) - {z["cod"] for z in zone}
    if mancanti:
        raise SystemExit(f"ERRORE: zone in doppio svantaggio senza poligono fra le zone: {sorted(mancanti)}")
    r4 = leggi("risultato4_regolarita.json")
    gps, feed = r4["citta"]["0"]["ritardo"], r4["confronto_feed"]["citta"]["0"]["ritardo"]
    se = e2["sezioni"]
    cont, sensori = contatore(), len(leggi("velocita_5t.json")["sensori"])
    ref = json.loads(NUMERI_PROGETTO.read_text(encoding="utf-8"))
    ctr = leggi("controllo_navigatori_riepilogo.json")
    dati = {
        "contatore": cont,
        "sensori_5t": sensori,
        # «In numeri» della home: passaggi misurati col GPS, sensori del traffico, sezioni di censimento analizzate, fonti di dati aperti, settimane di lavoro
        "in_numeri": {"passaggi": cont["passaggi"] if cont else None, "sensori": sensori, "sezioni": _sezioni_censimento(),
                       "fonti": ref["fonti"], "settimane": ref["settimane"], "commit": ref["commit"]},
        "contorno": {"larghezza": c["larghezza"], "altezza": c["altezza"], "d": c["d"]},
        "zone": zone,
        "doppio": {"residenti": se["residenti_doppio_svantaggio"], "quota": round(100 * se["quota_residenti_di_riferimento"], 1),
                   "n_su": round(10 / max(1, round(10 * se["quota_residenti_di_riferimento"]))), "n_zone": len(doppie), "abitanti_zone": e2["residenti_zone_doppio_svantaggio"]},
        "raccomandazioni": raccomandazioni(),
        "domande": domande(r4, e2),
        "controllo_auto": {"percorsi": ctr["percorsi"], "errore_pct": abs(ctr["mediana_errore_con_segno_pct"])},
        "lavoro_ai": json.loads(LAVORO_AI.read_text(encoding="utf-8")),
        "ritardi": {"gps_pct": gps, "feed_pct": feed, "rapporto": round(gps / feed, 1) if feed else None,
                    "copertura_gps_pct": r4["copertura_gps"]["totale"]["copertura_pct"], "soglia_min": r4["parametri"]["soglia_ritardo_min"]},
    }
    OUT.write_text("// generato da scripts/schede_risultati.py - non modificare a mano\nwindow.PROGETTO = " + json.dumps(dati, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"progetto.js: {len(zone)} zone di Torino ({len(doppie)} in doppio svantaggio), contatore {dati['contatore']}, "
          f"ritardi oltre {dati['ritardi']['soglia_min']:g} min: GPS {gps}% contro feed {feed}%, {kb:.0f} KB")
    if kb > 200:
        print(f"AVVISO: data/progetto.js pesa {kb:.0f} KB (limite scelto: 200 KB)")
