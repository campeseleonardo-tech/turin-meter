#!/usr/bin/env python3
"""
24_importanza_vie.py  -  punteggio di importanza (1-5) per le vie di Torino+cintura,
combinando tre segnali: A) classificazione OSM, B) traffico reale misurato (sensori 5T),
D) elenco a mano delle arterie di ingresso note (dato da Leo, mai esaustivo).

Logica (nessuno dei tre segnali viene mai mediato via "peso a caso"):
  1. Punteggio di base da A: dal tag OSM "highway" della via (vedi MAPPA_OSM sotto).
  2. "Pavimento" da D: se il nome della via e' nell'elenco a mano, il punteggio non
     scende mai sotto 4, qualunque cosa dica OSM.
  3. Conferma da B, solo verso l'alto: se il sensore 5T piu' vicino a quella via misura
     un flusso mediano (tra le letture valide, accuratezza>0) oltre la soglia "alta"
     (75esimo percentile tra tutti i sensori), il punteggio non scende mai sotto 3.
  Punteggio finale = massimo dei tre, tetto a 5.

L'unita' di analisi e' il "corridoio": i segmenti OSM che condividono lo stesso nome
via (dopo normalizzazione) E sono fisicamente collegati o vicini fra loro (nodo OSM in
comune o meno di ~100-200 m, cosi' carreggiate e controviali di un corso restano insieme),
NON il singolo segmento stradale. E' la stessa unita' con cui si ragiona a parole
("corso Francia", che resta uno solo anche passando da Torino a Collegno), e la via puo'
avere tratti classificati diversamente in OSM: si prende il tratto piu' alto come
rappresentativo del corridoio. Vie omonime NON collegate (le tante "Strada Torino" dei
comuni di cintura) restano corridoi separati (corretto il 14/10: prima venivano unite
in un unico corridoio di 100 km con punteggio 5). Al nome si aggiunge il comune (zona IMQ
del punto centrale) solo per leggibilita'.

Non tocca nessun file esistente: scrive solo due output nuovi, non sovrascrive nulla
del progetto gia' calcolato (accessibilita, vulnerabilita, ecc.).

Uso:
    python scripts\\24_importanza_vie.py --prova
        Gira solo su un angolo piccolo di mappa (centro citta'), per controllare in 1-2
        minuti che tutto funzioni prima del giro vero. Scrive negli stessi file di
        output (non c'e' un file separato per la prova: guarda il numero di corridoi
        nel rapporto, dev'essere piccolo, prima di lanciare il giro completo).
    python scripts\\24_importanza_vie.py
        Giro completo su Torino + cintura.

Output:
    data/processed/importanza_vie.json       - dati per corridoio (punteggio, componenti, geometria)
    docs/rapporti/RAPPORTO_IMPORTANZA_VIE.txt         - riepilogo leggibile, da controllare prima di usare il resto
"""
import argparse
import json
import math
import re
import sqlite3
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comuni import PERIODO, haversine_m  # noqa: E402  (distanza in metri, uguale alla copia che stava qui; PERIODO fisso dei dati)

AQUI = Path(__file__).resolve().parent


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    candidata = Path.home() / "Desktop" / "GTT"
    if candidata.is_dir():
        return candidata
    return AQUI.parent


RADICE = trova_radice()
OSM_PBF = RADICE / "data" / "otp" / "rete" / "torino_cintura.osm.pbf"
IMQ_ZONE_GEO = RADICE / "data" / "processed" / "imq_zone_geo.json"
STORICO_5T = RADICE / "data" / "storico_backup.sqlite"
OUT = RADICE / "data" / "processed" / "importanza_vie.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_IMPORTANZA_VIE.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

# --- A: mappa tag OSM -> punteggio di base (1-5) -----------------------------------
# Qualunque tag "highway" non elencato qui prende punteggio 1 (strada locale/minore).
MAPPA_OSM = {
    "motorway": 5, "motorway_link": 5,
    "trunk": 5, "trunk_link": 5,
    "primary": 4, "primary_link": 4,
    "secondary": 3, "secondary_link": 3,
    "tertiary": 2, "tertiary_link": 2,
}

# --- D: elenco a mano (dato da Leo il 14/10, non esaustivo, solo "pavimento") ------
ELENCO_MANO = [
    "Francia", "Regina Margherita", "Potenza", "Lecce", "Trapani", "Siracusa",
    "Vittorio", "Moncalieri", "Romania", "Grosseto", "Unita d'Italia",
    "Unione Sovietica", "Allamano", "Peschiera", "Principe Oddone", "Venezia",
    "Duca degli Abruzzi",
    "Po", "Roma", "Cernaia", "Cigna", "Sacchi", "Servais",
]

PREFISSI = ["corso", "via", "strada", "corso di", "largo", "piazza", "c.so", "v."]


def normalizza(nome):
    """'Corso Francia' -> 'francia'; toglie prefisso via/corso/ecc, accenti, apostrofi."""
    if not nome:
        return ""
    n = nome.strip().lower()
    n = re.sub(r"\s*\([^)]*\)\s*$", "", n)  # sensori 5T: 'Corso Francia(TO)' -> 'corso francia'
    n = n.replace("'", " ").replace("'", " ").replace("’", " ")
    n = (n.replace("à", "a").replace("è", "e").replace("é", "e")
           .replace("ì", "i").replace("ò", "o").replace("ù", "u"))
    n = re.sub(r"\s+", " ", n).strip()
    parole = n.split(" ")
    while parole and parole[0] in PREFISSI:
        parole = parole[1:]
    return " ".join(parole).strip()


def match_manuale(nome_norm, elenco_norm):
    """True se nome_norm contiene, come parola intera, una voce dell'elenco a mano."""
    for voce in elenco_norm:
        if re.search(rf"\b{re.escape(voce)}\b", nome_norm):
            return voce
    return None


# --- A: lettura OSM -----------------------------------------------------------------

def leggi_osm(bbox_prova=None):
    """Ritorna lista di vie: {nome, highway, punti:[(lat,lon),...]}.
    bbox_prova = (lat_min, lon_min, lat_max, lon_max) per limitare alla zona di prova."""
    try:
        import osmium
    except ImportError:
        sys.exit(
            "Manca il pacchetto 'osmium'. Installa con:\n"
            "    pip install osmium\n"
            "e rilancia questo script."
        )

    vie = []

    class Handler(osmium.SimpleHandler):
        def way(self, w):
            tag = w.tags.get("highway")
            nome = w.tags.get("name")
            if not tag or not nome:
                return  # niente nome -> non e' un "corridoio" di cui si possa parlare
            try:
                punti = [(n.lat, n.lon) for n in w.nodes if n.location.valid()]
                nodi = [n.ref for n in w.nodes]
            except Exception:
                return
            if len(punti) < 2:
                return
            if bbox_prova:
                lat_min, lon_min, lat_max, lon_max = bbox_prova
                dentro = any(lat_min <= la <= lat_max and lon_min <= lo <= lon_max for la, lo in punti)
                if not dentro:
                    return
            vie.append({"nome": nome, "highway": tag, "punti": punti, "nodi": nodi})

    Handler().apply_file(str(OSM_PBF), locations=True)
    return vie


# --- B: lettura storico 5T -----------------------------------------------------------

def leggi_5t():
    """Ritorna lista di sensori: {nome_strada, lat, lon, flusso_mediano}.
    Scarta le letture con accuratezza 0 (sensore non valido in quel momento)."""
    if not STORICO_5T.exists():
        print(f"ATTENZIONE: non trovo {STORICO_5T} — salto il segnale B (nessun dato 5T).")
        return []
    con = sqlite3.connect(f"file:{STORICO_5T}?mode=ro", uri=True)
    try:
        sensori = con.execute(
            "SELECT lcd1, nome_strada, lat, lng FROM sensori_5t"
        ).fetchall()
        risultato = []
        for lcd1, nome_strada, lat, lng in sensori:
            if not nome_strada or lat is None or lng is None:
                continue
            letture = con.execute(
                """SELECT f.flusso FROM flussi_5t f
                   JOIN accuratezza_5t a ON a.generato_utc=f.generato_utc AND a.lcd1=f.lcd1
                   WHERE f.lcd1=? AND a.accuratezza>0 AND f.flusso IS NOT NULL
                     AND date(datetime(substr(f.generato_utc,1,19), '+2 hours')) BETWEEN ? AND ?""",
                (lcd1, *PERIODO["sensori"]),      # periodo fisso (L9b): solo giorni interi
            ).fetchall()
            valori = [v for (v,) in letture if v is not None]
            if not valori:
                continue
            risultato.append({
                "nome_strada": nome_strada, "lat": lat, "lon": lng,
                "flusso_mediano": statistics.median(valori), "n_letture": len(valori),
            })
        return risultato
    finally:
        con.close()


# --- comune (solo etichetta) ---------------------------------------------------------

def carica_comuni():
    """Zone IMQ come (bbox, anelli, comune): Torino per le zone Q, altrimenti il nome zona."""
    if not IMQ_ZONE_GEO.exists():
        return []
    zone = []
    for z in json.loads(IMQ_ZONE_GEO.read_text(encoding="utf-8")):
        g = z["g"]
        if isinstance(g, str):
            g = json.loads(g)
        if g and isinstance(g[0][0], (int, float)):
            anelli = [g]
        elif g and isinstance(g[0][0][0], (int, float)):
            anelli = g
        else:
            anelli = [anello for poligono in g for anello in poligono]
        pts = [p for a in anelli for p in a]
        bbox = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
        comune = "Torino" if z["cod"].startswith("Q") else z["denom"].title()
        zone.append((bbox, anelli, comune))
    return zone


def comune_di(lat, lon, zone):
    for (la0, lo0, la1, lo1), anelli, comune in zone:
        if not (la0 <= lat <= la1 and lo0 <= lon <= lo1):
            continue
        for anello in anelli:
            dentro, j = False, len(anello) - 1
            for i in range(len(anello)):
                yi, xi = anello[i]
                yj, xj = anello[j]
                if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi:
                    dentro = not dentro
                j = i
            if dentro:
                return comune
    return None


# --- combinazione A + D + B -----------------------------------------------------------

CELLA_LAT, CELLA_LON = 0.0009, 0.0013  # ~100 m x ~100 m a Torino


def raggruppa_collegati(segmenti):
    """Divide i segmenti con lo stesso nome in gruppi fisicamente collegati: due segmenti
    stanno insieme se hanno un nodo OSM in comune o passano a meno di ~100-200 m l'uno
    dall'altro (celle vicine), anche indirettamente attraverso altri segmenti dello
    stesso nome. Cosi' le due carreggiate e i controviali di un corso restano un
    corridoio solo, mentre vie omonime in comuni diversi (km di distanza) si separano."""
    padre = list(range(len(segmenti)))

    def radice(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    def unisci(i, j):
        ri, rj = radice(i), radice(j)
        if ri != rj:
            padre[ri] = rj

    primo_con_nodo = {}
    celle = {}
    for i, seg in enumerate(segmenti):
        for nodo in seg["nodi"]:
            unisci(i, primo_con_nodo.setdefault(nodo, i))
        pts = seg["punti"]
        for k in range(len(pts) - 1):
            (la0, lo0), (la1, lo1) = pts[k], pts[k + 1]
            passi = max(1, int(max(abs(la1 - la0) / CELLA_LAT, abs(lo1 - lo0) / CELLA_LON) * 2))
            for t in range(passi + 1):
                la, lo = la0 + (la1 - la0) * t / passi, lo0 + (lo1 - lo0) * t / passi
                celle.setdefault((math.floor(la / CELLA_LAT), math.floor(lo / CELLA_LON)), set()).add(i)
    for (ci, cj), dentro in celle.items():
        vicini = set(dentro)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                vicini |= celle.get((ci + di, cj + dj), set())
        primo = next(iter(vicini))
        for i in vicini:
            unisci(i, primo)
    gruppi = {}
    for i, seg in enumerate(segmenti):
        gruppi.setdefault(radice(i), []).append(seg)
    return list(gruppi.values())


def costruisci_corridoi(vie_osm, sensori_5t):
    elenco_norm = [normalizza(v) for v in ELENCO_MANO]
    zone_comuni = carica_comuni()

    per_nome = {}
    for v in vie_osm:
        chiave = normalizza(v["nome"])
        if not chiave:
            continue
        per_nome.setdefault(chiave, []).append(v)

    gruppi = []  # (chiave, {"nomi_originali", "segmenti"})
    for chiave, segmenti in per_nome.items():
        for pezzo in raggruppa_collegati(segmenti):
            gruppi.append((chiave, {"nomi_originali": {s["nome"] for s in pezzo}, "segmenti": pezzo}))

    # soglia "alta" per B: 75esimo percentile del flusso mediano fra tutti i sensori validi
    flussi_sensori = sorted(s["flusso_mediano"] for s in sensori_5t)
    soglia_b = None
    if flussi_sensori:
        idx = max(0, min(len(flussi_sensori) - 1, round(0.75 * (len(flussi_sensori) - 1))))
        soglia_b = flussi_sensori[idx]

    corridoi = []
    for chiave, g in gruppi:
        a_base = max((MAPPA_OSM.get(s["highway"], 1) for s in g["segmenti"]), default=1)

        voce_d = match_manuale(chiave, elenco_norm)
        floor_d = voce_d is not None

        # B: sensori il cui nome strada (normalizzato) corrisponde a questo corridoio,
        # entro 60 m da un punto qualsiasi del corridoio (evita falsi match di solo nome,
        # controlla tutti i punti del tracciato e non solo gli estremi del segmento).
        sensori_match = []
        for s in sensori_5t:
            if normalizza(s["nome_strada"]) != chiave:
                continue
            vicino = any(
                haversine_m(s["lat"], s["lon"], la, lo) <= 60
                for seg in g["segmenti"] for la, lo in seg["punti"]
            )
            if vicino:
                sensori_match.append(s)
        flusso_rappresentativo = (
            statistics.median(s["flusso_mediano"] for s in sensori_match) if sensori_match else None
        )
        floor_b = (
            soglia_b is not None and flusso_rappresentativo is not None
            and flusso_rappresentativo >= soglia_b
        )

        punteggio = a_base
        if floor_d:
            punteggio = max(punteggio, 4)
        if floor_b:
            punteggio = max(punteggio, 3)
        punteggio = min(5, punteggio)

        n_segmenti = len(g["segmenti"])
        lunghezza_m = 0.0
        for seg in g["segmenti"]:
            pts = seg["punti"]
            lunghezza_m += sum(haversine_m(*pts[i], *pts[i + 1]) for i in range(len(pts) - 1))

        piu_lungo = max(g["segmenti"], key=lambda s: len(s["punti"]))["punti"]
        comune = comune_di(*piu_lungo[len(piu_lungo) // 2], zone_comuni) if zone_comuni else None
        # nome mostrato: quello con piu' punti di tracciato (il tratto principale, non
        # una piazza/largo omonimo collegato)
        peso_nome = {}
        for seg in g["segmenti"]:
            peso_nome[seg["nome"]] = peso_nome.get(seg["nome"], 0) + len(seg["punti"])
        nome_base = max(sorted(peso_nome), key=lambda n: peso_nome[n])
        corridoi.append({
            "nome": f"{nome_base} ({comune})" if comune else nome_base,
            "comune": comune,
            "nomi_osm_visti": sorted(g["nomi_originali"]),
            "chiave_normalizzata": chiave,
            "punteggio": punteggio,
            "componenti": {
                "osm_base": a_base,
                "pavimento_elenco_a_mano": voce_d,
                "sensori_5t_abbinati": len(sensori_match),
                "flusso_mediano_5t": flusso_rappresentativo,
                "soglia_alta_5t": soglia_b,
            },
            "n_segmenti_osm": n_segmenti,
            "lunghezza_km": round(lunghezza_m / 1000, 2),
            "geometria": [seg["punti"] for seg in g["segmenti"]],
        })

    corridoi.sort(key=lambda c: (-c["punteggio"], -c["lunghezza_km"]))
    return corridoi, elenco_norm


def scrivi_rapporto(corridoi, elenco_norm, vie_osm, sensori_5t, prova):
    trovati = {c["componenti"]["pavimento_elenco_a_mano"] for c in corridoi if c["componenti"]["pavimento_elenco_a_mano"]}
    non_trovati = [voce for voce, norm in zip(ELENCO_MANO, elenco_norm) if norm not in trovati]

    righe = []
    righe.append("RAPPORTO IMPORTANZA VIE (A: tag OSM, D: elenco a mano, B: sensori 5T reali)")
    righe.append(f"modalita': {'PROVA (zona limitata)' if prova else 'completa Torino+cintura'}")
    righe.append(f"vie OSM con nome lette: {len(vie_osm)}  ->  corridoi (per nome + collegamento fisico) risultanti: {len(corridoi)}")
    righe.append(f"sensori 5T con almeno una lettura valida: {len(sensori_5t)}")
    righe.append("")
    righe.append("== Controllo elenco a mano (D): voci NON trovate in OSM (da verificare il nome) ==")
    if non_trovati:
        for voce in non_trovati:
            righe.append(f"  MANCA: {voce}")
    else:
        righe.append("  (tutte le voci dell'elenco sono state trovate)")
    righe.append("")
    righe.append("== Primi 20 corridoi per punteggio (controllo a vista) ==")
    for c in corridoi[:20]:
        comp = c["componenti"]
        righe.append(
            f"  [{c['punteggio']}] {c['nome']:35s} km={c['lunghezza_km']:6.2f}  "
            f"osm_base={comp['osm_base']}  pavimento_D={comp['pavimento_elenco_a_mano'] or '-'}  "
            f"5T_sensori={comp['sensori_5t_abbinati']}  5T_flusso={comp['flusso_mediano_5t']}"
        )
    righe.append("")
    righe.append("== Corridoi piu' lunghi (controllo: oltre ~30 km solo autostrade/tangenziali) ==")
    for c in sorted(corridoi, key=lambda c: -c["lunghezza_km"])[:15]:
        righe.append(f"  [{c['punteggio']}] {c['nome']:45s} km={c['lunghezza_km']:6.2f}  osm_base={c['componenti']['osm_base']}")
    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true",
                    help="gira solo su un riquadro piccolo in centro citta', per un controllo rapido")
    args = ap.parse_args()

    if not OSM_PBF.exists():
        sys.exit(f"Non trovo {OSM_PBF} — controlla il percorso.")

    bbox_prova = (45.055, 7.660, 45.085, 7.700) if args.prova else None  # centro Torino

    print("Leggo le vie da OpenStreetMap...")
    vie_osm = leggi_osm(bbox_prova=bbox_prova)
    print(f"  {len(vie_osm)} segmenti stradali con nome letti.")

    print("Leggo lo storico 5T...")
    sensori_5t = leggi_5t()
    print(f"  {len(sensori_5t)} sensori con almeno una lettura valida.")

    print("Combino i tre segnali per corridoio...")
    corridoi, elenco_norm = costruisci_corridoi(vie_osm, sensori_5t)
    print(f"  {len(corridoi)} corridoi (vie per nome + collegamento) risultanti.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "modalita_prova": args.prova,
        "elenco_a_mano_usato": ELENCO_MANO,
        "corridoi": corridoi,
    }, ensure_ascii=False), encoding="utf-8")
    scrivi_rapporto(corridoi, elenco_norm, vie_osm, sensori_5t, args.prova)

    print(f"Scritto: {OUT}")
    print(f"Scritto: {RAPPORTO}  <-- controlla questo prima di usare i dati")


if __name__ == "__main__":
    sys.exit(main())
