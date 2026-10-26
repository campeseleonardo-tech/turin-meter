#!/usr/bin/env python3
"""
77_strade_comuni.py  -  Risultato 6 v2, GIRO 2: modulo condiviso per le strade.

Cosa fa
-------
Un solo modo, usato dagli script 72 e 73, per due cose:

1. CORREGGE IL PUNTEGGIO DELLE TRATTE (Fase 5 del traffico). Nel giro 1 una strada
   primaria o secondaria poteva avere punteggio 1 e una stradina di servizio lo stesso
   punteggio di un corso: adesso
     - autostrada e tangenziale -> 5;
     - primaria -> almeno 4; secondaria -> almeno 3;
     - residenziale, di servizio, zona pedonale -> al massimo 2, ma solo se il punteggio
       non era gia' stato alzato a mano o da un sensore 5T (campo "motivi" vuoto);
     - tutte le altre classi restano come sono.
   Il punteggio del giro 1 resta salvato in "punteggio_orig".

2. TROVA LA STRADA DI UN PUNTO con una regola nuova: non piu' "il tratto piu' vicino"
   (che spesso era una stradina di servizio), ma "il tratto piu' importante entro poca
   distanza, escluse le stradine". In ordine:
     1. fra i tratti entro 50 m con classe non minore, quello con punteggio piu' alto
        (a parita', il piu' vicino) -> esito "ok";
     2. altrimenti il tratto non minore piu' vicino entro 150 m -> "strada_lontana";
     3. altrimenti il tratto minore piu' vicino entro 50 m -> "solo_minore";
     4. altrimenti niente -> "nessuna".
   Classi minori: service, residential, living_street.

Come si importa
---------------
    import importlib.util
    spec = importlib.util.spec_from_file_location("strade", "scripts/77_strade_comuni.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    strade = m.carica_strade()
    info = m.trova_strada(strade, lat, lon)

Cosa scrive
-----------
  docs/rapporti/RAPPORTO_R6V2_STRADE.txt   (solo quando si lancia la funzione di prova)

Come si lancia (prova: stampa i controlli e scrive il rapporto)
---------------------------------------------------------------
  python scripts\\77_strade_comuni.py
"""
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

AQUI = Path(__file__).resolve().parent


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
RETE = RADICE / "data" / "processed" / "traffico_d" / "rete" / "rete_auto.npz"
ASSI = RADICE / "data" / "processed" / "traffico_d" / "assi_tratte.npz"
TRATTE = RADICE / "data" / "processed" / "traffico_d" / "tratte_traffico.json"
LUOGHI = RADICE / "data" / "processed" / "risultato6_v2" / "luoghi.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6V2_STRADE.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

LAT_RIF = 45.07
FATTORE_GRADI_M = 111000.0

CLASSI_MINORI = ("service", "residential", "living_street")
PASSO_DENSIFICA_M = 25.0      # punti finti lungo i tratti lunghi, per trovarli in fretta
RAGGIO_STRETTO_M = 50.0
RAGGIO_LARGO_M = 150.0


def proietta(lon, lat):
    return (lon * FATTORE_GRADI_M * math.cos(math.radians(LAT_RIF)), lat * FATTORE_GRADI_M)


def punteggio_corretto(t):
    """Il punteggio della tratta dopo la correzione del giro 2."""
    p = t["punteggio"]
    classe = (t.get("classe") or "")
    motivi = t.get("motivi") or []
    if classe in ("motorway", "trunk"):
        return 5
    if classe == "primary":
        return max(p, 4)
    if classe == "secondary":
        return max(p, 3)
    if classe in CLASSI_MINORI and not motivi:
        return min(p, 2)
    return p


def carica_strade(verbose=False):
    """Carica strade e tratte, corregge i punteggi e prepara l'indice dei tratti."""
    rete = np.load(RETE)
    edge_pts = rete["edge_pts"]
    edge_off = rete["edge_off"]
    edge_tratta = np.load(ASSI)["edge_tratta"]
    tratte = json.loads(TRATTE.read_text(encoding="utf-8"))["tratte"]

    comuni_asse = defaultdict(set)
    nome_asse = {}
    lunghezza_asse = defaultdict(float)
    for t in tratte:
        t["punteggio_orig"] = t["punteggio"]
        t["punteggio_corr"] = punteggio_corretto(t)
        if t.get("comune"):
            comuni_asse[t["asse"]].add(t["comune"])
        nome_asse.setdefault(t["asse"], t.get("nome"))
        lunghezza_asse[t["asse"]] += t.get("lunghezza_m") or 0.0
    assi_ingresso = {a for a, cs in comuni_asse.items() if "Torino" in cs and len(cs) > 1}
    per_id = {}
    for t in tratte:
        per_id[t["id"]] = {
            "id": t["id"], "asse": t["asse"], "nome": t.get("nome"),
            "comune": t.get("comune"), "classe": t.get("classe"),
            "punteggio_corr": t["punteggio_corr"], "punteggio_orig": t["punteggio_orig"],
            "motivi": t.get("motivi") or [],
            "asse_ingresso": t["asse"] in assi_ingresso,
            "veic_giorno": t.get("veic_giorno"), "lunghezza_m": t.get("lunghezza_m"),
            "comuni_asse": sorted(comuni_asse.get(t["asse"], [])),
        }

    # classe e punteggio per tratto (edge)
    n_edge = len(edge_off) - 1
    edge_classe = [None] * n_edge
    edge_punteggio = [None] * n_edge
    for e in range(n_edge):
        tid = int(edge_tratta[e])
        if tid < 0:
            continue
        info = per_id.get(tid)
        if info is None:
            continue
        edge_classe[e] = info["classe"]
        edge_punteggio[e] = info["punteggio_corr"]

    # indice dei punti: vertici veri + punti finti ogni 25 m lungo i tratti lunghi
    xs, ys, punto_edge = [], [], []
    for e in range(n_edge):
        pts = edge_pts[edge_off[e]:edge_off[e + 1]]
        prec = None
        for p in pts:
            x, y = proietta(p[1], p[0])
            if prec is not None:
                dx, dy = x - prec[0], y - prec[1]
                d = math.hypot(dx, dy)
                if d > PASSO_DENSIFICA_M:
                    n = int(d // PASSO_DENSIFICA_M)
                    for k in range(1, n + 1):
                        xs.append(prec[0] + dx * k / (n + 1))
                        ys.append(prec[1] + dy * k / (n + 1))
                        punto_edge.append(e)
            xs.append(x)
            ys.append(y)
            punto_edge.append(e)
            prec = (x, y)
    albero = cKDTree(np.column_stack([np.array(xs), np.array(ys)]))
    if verbose:
        print(f"  indice: {len(xs)} punti per {n_edge} tratti, {len(tratte)} tratte, "
              f"{len(assi_ingresso)} assi di ingresso")
    return {
        "edge_pts": edge_pts, "edge_off": edge_off, "edge_tratta": edge_tratta,
        "tratte": tratte, "per_id": per_id, "assi_ingresso": assi_ingresso,
        "nome_asse": nome_asse, "comuni_asse": comuni_asse,
        "lunghezza_asse": lunghezza_asse,
        "edge_classe": edge_classe, "edge_punteggio": edge_punteggio,
        "albero": albero, "punto_edge": np.array(punto_edge, dtype=np.int64),
        "n_edge": n_edge,
    }


def _dist_punto_segmento(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _vicini(lat, lon, strade, raggio_m):
    """Tratti la cui distanza dal punto e' <= raggio_m, con la distanza esatta."""
    x, y = proietta(lon, lat)
    idx = strade["albero"].query_ball_point([x, y], raggio_m + PASSO_DENSIFICA_M)
    candidati = set(int(strade["punto_edge"][i]) for i in idx)
    esiti = {}
    for e in candidati:
        pts = strade["edge_pts"][strade["edge_off"][e]:strade["edge_off"][e + 1]]
        migliore = None
        for i in range(len(pts) - 1):
            ax, ay = proietta(pts[i][1], pts[i][0])
            bx, by = proietta(pts[i + 1][1], pts[i + 1][0])
            d = _dist_punto_segmento(x, y, ax, ay, bx, by)
            if migliore is None or d < migliore:
                migliore = d
        if migliore is not None and migliore <= raggio_m:
            esiti[e] = migliore
    return esiti


def trova_strada(strade, lat, lon, raggio_stretto=RAGGIO_STRETTO_M, raggio_largo=RAGGIO_LARGO_M):
    """La strada di un punto: vedi la regola nella docstring del modulo."""
    non_minori = _vicini(lat, lon, strade, raggio_stretto)
    scelta = None
    esito = "nessuna"
    if non_minori:
        candidati = [(e, d) for e, d in non_minori.items()
                     if strade["edge_classe"][e] not in CLASSI_MINORI
                     and strade["edge_punteggio"][e] is not None]
        if candidati:
            scelta = max(candidati, key=lambda ed: (strade["edge_punteggio"][ed[0]], -ed[1]))
            esito = "ok"
    if scelta is None:
        larghi = _vicini(lat, lon, strade, raggio_largo)
        candidati = [(e, d) for e, d in larghi.items()
                     if strade["edge_classe"][e] not in CLASSI_MINORI
                     and strade["edge_punteggio"][e] is not None]
        if candidati:
            scelta = min(candidati, key=lambda ed: ed[1])
            esito = "strada_lontana"
    if scelta is None:
        candidati = [(e, d) for e, d in non_minori.items()
                     if strade["edge_classe"][e] in CLASSI_MINORI
                     and strade["edge_punteggio"][e] is not None]
        if candidati:
            scelta = min(candidati, key=lambda ed: ed[1])
            esito = "solo_minore"
    if scelta is None:
        return {"tratta": None, "asse": None, "nome": None, "comune": None, "classe": None,
                "punteggio_corr": None, "asse_ingresso": None, "distanza_m": None,
                "esito": "nessuna", "comuni_asse": []}
    edge, distanza = scelta
    tid = int(strade["edge_tratta"][edge])
    info = strade["per_id"].get(tid, {})
    return {"tratta": tid, "asse": info.get("asse"), "nome": info.get("nome"),
            "comune": info.get("comune"), "classe": info.get("classe"),
            "punteggio_corr": info.get("punteggio_corr"),
            "asse_ingresso": info.get("asse_ingresso"),
            "distanza_m": round(distanza, 1), "esito": esito,
            "comuni_asse": info.get("comuni_asse", [])}


# --- prova -----------------------------------------------------------------------------

def prova():
    print("carico le strade e correggo i punteggi...")
    strade = carica_strade(verbose=True)
    tratte = strade["tratte"]

    cambiate = [t for t in tratte if t["punteggio_corr"] != t["punteggio_orig"]]
    km = sum(t.get("lunghezza_m") or 0.0 for t in cambiate) / 1000.0
    print(f"  tratte corrette: {len(cambiate)} su {len(tratte)} ({km:.0f} km)")

    # controllo 1: primarie e secondarie
    eccezioni = [t for t in tratte
                 if (t["classe"] == "primary" and t["punteggio_corr"] < 4)
                 or (t["classe"] == "secondary" and t["punteggio_corr"] < 3)]
    print(f"  controllo primarie>=4 e secondarie>=3: eccezioni {len(eccezioni)}")

    # controllo 2: Via Torino a Venaria Reale
    print("  controllo Via Torino a Venaria Reale:")
    via_to = [t for t in tratte
              if t.get("comune") == "Venaria Reale"
              and any("torino" in (n or "").lower()
                      for n in ([t.get("nome") or ""] + (t.get("nomi") or [])))]
    for t in via_to:
        print(f"    id {t['id']}: {t.get('nome')} classe={t['classe']} "
              f"{t['punteggio_orig']} -> {t['punteggio_corr']}")

    # controllo 3: la fermata GENOVA N.212
    luoghi = json.loads(LUOGHI.read_text(encoding="utf-8"))["luoghi"]
    genova = next((l for l in luoghi if "GENOVA N.212" in l["nome"].upper()), None)
    esito_genova = None
    if genova:
        esito_genova = trova_strada(strade, genova["lat"], genova["lon"])
        print(f"  controllo {genova['nome']}: {esito_genova}")

    # controllo 4: Fermi e Venchi Unica
    punti = {"FERMI (5T)": (45.076464, 7.591056), "VENCHI UNICA (5T)": (45.074104, 7.615765)}
    esiti_punti = {}
    for nome, (lat, lon) in punti.items():
        e = trova_strada(strade, lat, lon)
        esiti_punti[nome] = e
        print(f"  controllo {nome}: {e}")
    # distanza della strada attesa (Corso Francia) dal parcheggio Fermi, per capire
    # se il risultato diverso dipende dai dati o dalla regola
    vicini_fermi = _vicini(punti["FERMI (5T)"][0], punti["FERMI (5T)"][1], strade, 1500)
    d_francia = [d for e, d in vicini_fermi.items()
                 if (strade["per_id"].get(int(strade["edge_tratta"][e]), {}).get("nome") or "").lower()
                 == "francia"]
    d_francia = min(d_francia) if d_francia else None
    print(f"  distanza del tratto 'francia' piu' vicino a Fermi: {d_francia}")

    # conteggio degli esiti sui luoghi
    conteggio = Counter()
    for l in luoghi:
        e = trova_strada(strade, l["lat"], l["lon"])
        conteggio[e["esito"]] += 1
    print(f"  esiti sui {len(luoghi)} luoghi: {dict(conteggio)}")

    # --- rapporto ---
    righe = []
    righe.append("RAPPORTO R6 v2 (giro 2) — STRADE E PUNTEGGI CORRETTI")
    righe.append("Le strade e le tratte vengono dai file del traffico (Fase 5).")
    righe.append(f"tratte totali: {len(tratte)}; tratte il cui punteggio cambia: {len(cambiate)} "
                 f"({km:.0f} km)")
    righe.append("regola: autostrada e tangenziale 5; primaria almeno 4; secondaria almeno 3; "
                 "residenziale, di servizio e zona pedonale al massimo 2 se il punteggio non era "
                 "gia' stato alzato a mano o da un sensore (motivi vuoto).")
    righe.append("")
    righe.append("== Tabella classe x punteggio, prima e dopo ==")
    classi = Counter(t["classe"] for t in tratte)
    for classe in sorted(classi, key=lambda c: (-classi[c], c)):
        prima = Counter(t["punteggio_orig"] for t in tratte if t["classe"] == classe)
        dopo = Counter(t["punteggio_corr"] for t in tratte if t["classe"] == classe)
        def dist(d):
            return " ".join(f"{k}:{d[k]}" for k in sorted(d))
        righe.append(f"  {classe:16s} n={classi[classe]:6d}   prima {dist(prima):40s} dopo {dist(dopo)}")
    righe.append("")
    righe.append("== I 20 tratti piu' lunghi il cui punteggio SCENDE (con i motivi) ==")
    ridotti = sorted([t for t in tratte if t["punteggio_corr"] < t["punteggio_orig"]],
                     key=lambda t: -(t.get("lunghezza_m") or 0))[:20]
    for t in ridotti:
        righe.append(f"  {t.get('lunghezza_m') or 0:7.0f} m  {str(t.get('nome') or '-')[:34]:34s} "
                     f"{str(t.get('comune') or '-'):14s} {t['classe']:12s} "
                     f"{t['punteggio_orig']} -> {t['punteggio_corr']}  motivi={t.get('motivi')}")
    righe.append("")
    righe.append("== I 20 tratti piu' lunghi il cui punteggio SALE ==")
    alzati = sorted([t for t in tratte if t["punteggio_corr"] > t["punteggio_orig"]],
                    key=lambda t: -(t.get("lunghezza_m") or 0))[:20]
    for t in alzati:
        righe.append(f"  {t.get('lunghezza_m') or 0:7.0f} m  {str(t.get('nome') or '-')[:34]:34s} "
                     f"{str(t.get('comune') or '-'):14s} {t['classe']:12s} "
                     f"{t['punteggio_orig']} -> {t['punteggio_corr']}  "
                     f"veicoli/giorno={t.get('veic_giorno')}")
    righe.append("")
    righe.append("== Controlli ==")
    righe.append(f"  primarie con punteggio < 4: {sum(1 for t in tratte if t['classe'] == 'primary' and t['punteggio_corr'] < 4)}"
                 f" (deve essere 0)")
    righe.append(f"  secondarie con punteggio < 3: {sum(1 for t in tratte if t['classe'] == 'secondary' and t['punteggio_corr'] < 3)}"
                 f" (deve essere 0)")
    for t in via_to:
        righe.append(f"  Via Torino a Venaria Reale (id {t['id']}): {t.get('nome')} classe={t['classe']} "
                     f"{t['punteggio_orig']} -> {t['punteggio_corr']}")
    if not via_to:
        righe.append("  Via Torino a Venaria Reale: nei dati del traffico NON esiste nessuna tratta "
                     "con nome che contiene 'torino' nel comune di Venaria Reale (controllato sia "
                     "il campo nome sia l'elenco nomi): controllo non applicabile. La regola generale "
                     "e' comunque verificata sopra (0 secondarie sotto 3).")
    if genova:
        righe.append(f"  {genova['nome']} ({genova['lat']:.5f}, {genova['lon']:.5f}): "
                     f"strada '{esito_genova['nome']}' ({esito_genova['classe']}), "
                     f"punteggio {esito_genova['punteggio_corr']}, "
                     f"{esito_genova['distanza_m']} m, esito {esito_genova['esito']}, "
                     f"asse d'ingresso {esito_genova['asse_ingresso']}")
    else:
        righe.append("  GENOVA N.212: NON TROVATA nei luoghi")
    for nome, e in esiti_punti.items():
        righe.append(f"  {nome}: strada '{e['nome']}' ({e['classe']}), punteggio {e['punteggio_corr']}, "
                     f"{e['distanza_m']} m, esito {e['esito']}, asse d'ingresso {e['asse_ingresso']}, "
                     f"comuni dell'asse {e['comuni_asse']}")
    if d_francia is not None:
        righe.append(f"    (Corso Francia in questa rete stradale dista {d_francia:.0f} m dal parcheggio "
                     f"Fermi: piu' dei 50 m del primo passo della regola, per questo non viene scelto)")
    righe.append("")
    righe.append(f"== Assi di ingresso: {len(strade['assi_ingresso'])} ==")
    righe.append("(asse con tratte a Torino e in almeno un altro comune)")
    righe.append("Il giro 1 ne contava 91: la differenza sono gli assi il cui unico 'altro comune' e' "
                 "vuoto (None), che questo giro ignora come chiede il piano.")
    righe.append("I 30 assi di ingresso piu' lunghi:")
    for a in sorted(strade["assi_ingresso"], key=lambda a: -strade["lunghezza_asse"][a])[:30]:
        righe.append(f"  {strade['lunghezza_asse'][a] / 1000:6.1f} km  {str(strade['nome_asse'].get(a) or '-')[:34]:34s} "
                     f"comuni: {', '.join(sorted(strade['comuni_asse'][a]))}")
    righe.append("")
    righe.append(f"== Esito della ricerca della strada sui {len(luoghi)} luoghi ==")
    for k in ("ok", "strada_lontana", "solo_minore", "nessuna"):
        righe.append(f"  {k:15s} {conteggio.get(k, 0):5d}")
    righe.append("")
    righe.append("== Limiti ==")
    righe.append("- Il punteggio delle tratte viene dalla stima del traffico della Fase 5, che e' "
                 "debole (errore ±38%): qui conta solo come ordine di importanza.")
    righe.append("- La correzione per classe e' una scelta del 19/10: primarie e secondarie non "
                 "possono valere meno di 4 e 3; le stradine restano al massimo 2.")
    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print(f"Scritto: {RAPPORTO}")

    # esito dei controlli (per capire subito se fermarsi)
    ok = (len(eccezioni) == 0
          and genova is not None
          and esito_genova["esito"] in ("ok", "strada_lontana")
          and (esito_genova["classe"] or "") not in CLASSI_MINORI
          and (esito_genova["punteggio_corr"] or 0) >= 4)
    print(f"CONTROLLI PRINCIPALI: {'OK' if ok else 'DA GUARDARE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(prova())
