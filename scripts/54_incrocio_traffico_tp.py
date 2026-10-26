# -*- coding: utf-8 -*-
"""
scripts/54_incrocio_traffico_tp.py - Pacchetto D del piano Fase 4.

Incrocia il traffico (pacchetto C) con l'offerta di bus/tram (pacchetto B) per
ogni corridoio dell'universo di Torino (e, a parte, della prima cintura).

Definizioni FISSATE nel piano (sezione 6):
 - "molto traffico" = nel quarto piu' alto di veicoli/giorno nell'universo;
 - "poco TP" = nel quarto piu' basso di passaggi/ora in punta (compresi gli zeri)
   E senza metro_vicina ne' ferrovia_vicina;
 - un corridoio con molto traffico e poco TP e' nel gruppo "da guardare";
 - sensibilità: terzili e la sola punta del mattino;
 - robustezza: resta "molto traffico" anche con traffico x0,65 e x1,35.

Altezza del corridoio per il trasporto pubblico: si usa il tratto PIU' SERVIZIO
(massimo), non la media pesata per lunghezza: le vie lunghe hanno tratti senza
bus e la media le farebbe sembrare "scoperte" a torto.

Output: data/processed/risultato8_traffico_tp.json
        docs/rapporti/RAPPORTO_RISULTATO8_TRAFFICO_TP.txt
"""

import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
PROC = AQUI.parent / "data" / "processed"
OUT_DIR = PROC / "traffico_c"

CINTURA = {"Beinasco", "Borgaro Torinese", "Collegno", "Druento", "Grugliasco", "Moncalieri",
           "Nichelino", "Orbassano", "Pecetto Torinese", "Pino Torinese", "San Mauro Torinese",
           "Settimo Torinese", "Venaria Reale"}


def percentile_rank(v, valori):
    valori = np.sort(np.asarray(valori))
    return float(np.searchsorted(valori, v, side="left") / max(len(valori), 1))


def quartiere_di(corridoio):
    return corridoio


def main():
    pub = json.loads((PROC / "traffico_stimato_finale_v2.json").read_text(encoding="utf-8"))
    variante = pub["variante_finale"]; classe = pub["classe_esito"]
    reg = pub["corridoi"]
    tp = json.loads((PROC / "tp_corridoi.json").read_text(encoding="utf-8"))["corridoi"]
    # TP per corridoio (stesso ordine di importanza_vie)
    tp_idx = {}
    for i, o in enumerate(tp):
        tp_idx[(o["nome"], o["chiave"])] = o

    importanza = json.loads((PROC / "importanza_vie.json").read_text(encoding="utf-8"))["corridoi"]
    nome_a_idx = {}
    for i, c in enumerate(importanza):
        nome_a_idx[(c["nome"], c["chiave_normalizzata"])] = i

    # quartiere (poligono Q) del punto medio di ogni corridoio
    zone = json.loads((PROC / "imq_zone_geo.json").read_text(encoding="utf-8"))
    from shapely.geometry import Polygon, MultiPolygon, Point
    from shapely.strtree import STRtree

    def anelli(g):
        if isinstance(g, str):
            g = json.loads(g)
        if not g:
            return []
        if isinstance(g[0][0], (int, float)):
            return [g]
        if isinstance(g[0][0][0], (int, float)):
            return g
        return [a for p in g for a in p]

    polys, cods = [], []
    for z in zone:
        if not z["cod"].startswith("Q"):
            continue
        pp = []
        for an in anelli(z["g"]):
            if len(an) >= 4:
                p = Polygon(an)
                if not p.is_valid:
                    p = p.buffer(0)
                if p.area > 0:
                    pp.append(p)
        if pp:
            polys.append(MultiPolygon(pp) if len(pp) > 1 else pp[0])
            cods.append(z["cod"])
    tree = STRtree(polys)

    def centro_corridoio(i):
        geom = importanza[i]["geometria"]
        pts = [p for t in geom for p in t]
        if not pts:
            return None
        la = sum(p[0] for p in pts) / len(pts)
        lo = sum(p[1] for p in pts) / len(pts)
        return la, lo

    corridoi = []
    for r in reg:
        if not r.get("nel_universo"):
            continue
        chiave = (r["nome"], r["chiave"])
        o = tp_idx.get(chiave)
        i = nome_a_idx.get(chiave)
        quartiere = None
        if i is not None:
            c = centro_corridoio(i)
            if c:
                ji = tree.query(Point(c[1], c[0]))
                for j in np.atleast_1d(ji):
                    if polys[j].contains(Point(c[1], c[0])):
                        quartiere = cods[j]
                        break
        corridoi.append({
            "nome": r["nome"], "chiave": r["chiave"], "comune": r.get("comune"),
            "quartiere": quartiere, "punteggio": r["punteggio"],
            "lunghezza_km": r["lunghezza_km"], "veic_giorno": r["veic_giorno"],
            "fascia_50": r.get("fascia_50"), "fascia_90": r.get("fascia_90"),
            "misurato": r.get("misurato"), "estrapolazione": r.get("estrapolazione"),
            "posizione_torino": r.get("posizione_torino"),
            "tp_am_max": (o or {}).get("passaggi_ora_punta_am_max", 0.0),
            "tp_pm_max": (o or {}).get("passaggi_ora_punta_pm_max", 0.0),
            "tp_am_medio": (o or {}).get("passaggi_ora_punta_am", 0.0),
            "tp_giorno": (o or {}).get("passaggi_giorno_6_21", 0.0),
            "linee": (o or {}).get("linee", []),
            "metro_vicina": (o or {}).get("metro_vicina", False),
            "ferrovia_vicina": (o or {}).get("ferrovia_vicina", False),
        })

    torino = [c for c in corridoi if c["comune"] == "Torino"]
    cintura = [c for c in corridoi if c["comune"] in CINTURA]
    N = len(torino)
    veic = np.array([c["veic_giorno"] for c in torino])
    tp_am = np.array([c["tp_am_max"] for c in torino])
    tp_pm = np.array([c["tp_pm_max"] for c in torino])
    q75 = float(np.percentile(veic, 75)); q25tp = float(np.percentile(tp_am, 25))
    q67 = float(np.percentile(veic, 66.7)); q33tp = float(np.percentile(tp_am, 33.3))

    def classifica(c, soglia_veic, soglia_tp, campo_tp="tp_am_max"):
        molto = c["veic_giorno"] >= soglia_veic
        poco = c[campo_tp] <= soglia_tp and not c["metro_vicina"] and not c["ferrovia_vicina"]
        return molto, poco

    for c in torino:
        c["perc_traffico"] = round(percentile_rank(c["veic_giorno"], veic), 4)
        c["perc_tp"] = round(percentile_rank(c["tp_am_max"], tp_am), 4)
        c["divario"] = round(c["perc_traffico"] - c["perc_tp"], 4)
        c["molto_traffico"], c["poco_tp"] = classifica(c, q75, q25tp)
        c["da_guardare"] = bool(c["molto_traffico"] and c["poco_tp"])
        c["robusto"] = bool(c["veic_giorno"] * 0.65 >= q75 and c["da_guardare"])
        # sensibilità
        m2, p2 = classifica(c, q67, q33tp)
        m3, p3 = classifica(c, q75, float(np.percentile(tp_pm, 25)), "tp_pm_max")
        c["da_guardare_terzili"] = bool(m2 and p2)
        c["da_guardare_pm"] = bool(m3 and p3)
        c["stabile"] = bool(c["da_guardare"] and c["da_guardare_terzili"] and c["da_guardare_pm"])

    da_guardare = sorted([c for c in torino if c["da_guardare"]], key=lambda c: -c["divario"])
    robusti = [c for c in da_guardare if c["robusto"]]
    stabili = [c for c in da_guardare if c["stabile"]]

    # Controllo del piano: la lista non deve essere dominata da ponti/sottopassi
    # corti. Le strutture si tengono nei dati ma NON nella presentazione, e lo si
    # dichiara. ("Corso Cairoli" ecc. restano.)
    STRUTTURA = re.compile(r"ponte|sottopasso|cavalcavia|viadotto|galleria|tunnel|diga", re.I)

    def e_struttura(c):
        return bool(STRUTTURA.search(c["nome"] or ""))

    da_guardare_strutture = [c for c in da_guardare if e_struttura(c)]
    da_guardare_pres = [c for c in da_guardare if not e_struttura(c)]

    # prima cintura: stessa regola, quartili calcolati dentro la cintura
    if cintura:
        veic_c = np.array([c["veic_giorno"] for c in cintura])
        tpc = np.array([c["tp_am_max"] for c in cintura])
        q75c = float(np.percentile(veic_c, 75)); q25tpc = float(np.percentile(tpc, 25))
        for c in cintura:
            c["molto_traffico"] = c["veic_giorno"] >= q75c
            c["poco_tp"] = (c["tp_am_max"] <= q25tpc and not c["metro_vicina"]
                            and not c["ferrovia_vicina"])
            c["da_guardare"] = bool(c["molto_traffico"] and c["poco_tp"])
        cintura_guardare = sorted([c for c in cintura if c["da_guardare"]],
                                  key=lambda c: -c["veic_giorno"])
    else:
        q75c = q25tpc = 0.0
        cintura_guardare = []

    # raggruppamento in assi per chiave (via), senza le strutture
    assi = defaultdict(list)
    for c in da_guardare_pres:
        assi[c["chiave"] or c["nome"]].append(c)
    elenco_assi = []
    for k, v in assi.items():
        v = sorted(v, key=lambda c: -c["veic_giorno"])
        elenco_assi.append({
            "chiave": k, "nome": v[0]["nome"].split("(")[0].strip(), "n_corridoi": len(v),
            "km": round(sum(c["lunghezza_km"] for c in v), 2),
            "veic_giorno_max": max(c["veic_giorno"] for c in v),
            "tp_am_max": max(c["tp_am_max"] for c in v),
            "tp_am_min": min(c["tp_am_max"] for c in v),
            "linee": sorted({l for c in v for l in c["linee"]}),
            "quartieri": sorted({c["quartiere"] for c in v if c["quartiere"]}),
            "corridoi": [c["nome"] for c in v],
        })
    elenco_assi.sort(key=lambda a: -a["veic_giorno_max"])

    # esempi spiegati
    esempi = {}
    if da_guardare_pres:
        esempi["molto_traffico_poco_tp"] = da_guardare_pres[0]
    es_buono = [c for c in torino if c["molto_traffico"] and not c["poco_tp"]]
    esempi["molto_traffico_tp_buono"] = max(es_buono, key=lambda c: c["tp_am_max"]) if es_buono else None
    es_debole = [c for c in torino if not c["molto_traffico"] and c["poco_tp"]]
    esempi["poco_traffico_poco_tp"] = max(es_debole, key=lambda c: c["veic_giorno"]) if es_debole else None

    # controllo buon senso a campione
    nomi_noti = ["Corso Giulio Cesare", "Corso Orbassano", "Corso Francia", "Via Nizza",
                 "Corso Regina Margherita", "Corso Vittorio Emanuele II", "Corso Unione Sovietica",
                 "Corso Allamano", "Corso Sebastopoli", "Corso Casale", "Corso Trapani",
                 "Corso Lecce", "Corso Peschiera"]
    campione = []
    for c in torino:
        base = c["nome"].split("(")[0].strip()
        if base in nomi_noti:
            campione.append(c)

    out = {
        "stimato": True, "variante_traffico": variante, "classe_esito": classe,
        "nota": ("Incrocio traffico x offerta bus/tram. TP = tratto piu' servito del corridoio "
                 "(passaggi/ora in punta mattina). Vedi i limiti in coda al rapporto."),
        "soglie": {"veic_q75": round(q75, 1), "tp_q25": round(q25tp, 2),
                   "veic_q67": round(q67, 1), "tp_q33": round(q33tp, 2),
                   "cintura_veic_q75": round(q75c, 1), "cintura_tp_q25": round(q25tpc, 2)},
        "conteggi": {"universo_torino": N, "universo_cintura": len(cintura),
                     "molto_traffico": int(sum(c["molto_traffico"] for c in torino)),
                     "poco_tp": int(sum(c["poco_tp"] for c in torino)),
                     "da_guardare": len(da_guardare),
                     "da_guardare_senza_strutture": len(da_guardare_pres),
                     "strutture_ponti_sottopassi": len(da_guardare_strutture),
                     "robusti": len(robusti), "stabili": len(stabili)},
        "assi": elenco_assi,
        "top30": da_guardare_pres[:30],
        "esempi": esempi,
        "campione_strade_note": campione,
        "corridoi": corridoi,
        "cintura": cintura,
        "cintura_da_guardare": cintura_guardare,
    }
    (PROC / "risultato8_traffico_tp.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

    righe = []
    a = righe.append
    a("RISULTATO 8 - STRADE CON MOLTO TRAFFICO E POCO TRASPORTO PUBBLICO (Fase 4, pacchetto D)")
    a("=" * 84)
    a(f"variante del traffico: {variante}   classe di esito: {classe}")
    a(f"universo di Torino: {N} corridoi; prima cintura: {len(cintura)}")
    a(f"soglie: molto traffico >= {q75:,.0f} veic/giorno (quarto piu' alto); "
      f"poco TP <= {q25tp:.2f} pass/h in punta (quarto piu' basso)")
    a(f"molto traffico: {out['conteggi']['molto_traffico']}   poco TP: {out['conteggi']['poco_tp']}   "
      f"DA GUARDARE: {len(da_guardare)} (di cui {len(da_guardare_strutture)} ponti/sottopassi, "
      f"esclusi dalla presentazione)   robusti: {len(robusti)}   stabili: {len(stabili)}")
    a("")
    a("== CONTROLLO DEL PIANO: la lista non e' dominata da strade di bordo (gia' escluse "
      "dall'universo se non affidabili), da ponti/sottopassi corti (qui sotto, esclusi dalla "
      "presentazione) ne' da strade < 300 m (gia' escluse). Strutture trovate = "
      f"{len(da_guardare_strutture)}: " + ", ".join(c["nome"][:28] for c in da_guardare_strutture))
    a("")
    a("== ASSI 'DA GUARDARE' (raggruppati per via) ==")
    for x in elenco_assi[:30]:
        a(f"  {x['veic_giorno_max']:9,.0f} veic/g  TP {x['tp_am_max']:5.1f}-{x['tp_am_min']:4.1f}/h  "
          f"{x['nome'][:38]:38s} {x['n_corridoi']:3d} tratti {x['km']:5.1f} km  "
          f"linee {','.join(x['linee'][:6]) or '-'}")
    a("")
    a("== I 30 corridoi con il divario maggiore (traffico alto - TP basso) ==")
    a(f"{'#':>3s} {'veic/giorno':>12s} {'+-50%':>6s} {'TP/h am':>8s} {'linee':>6s} {'div':>6s}  nome")
    for i, c in enumerate(da_guardare_pres[:30], 1):
        a(f"{i:3d} {c['veic_giorno']:12,.0f} {100*(c['fascia_50'] or 0):5.0f}% "
          f"{c['tp_am_max']:8.1f} {len(c['linee']):6d} {c['divario']:6.2f}  {c['nome'][:44]} "
          f"({c['quartiere'] or '-'}, {c['lunghezza_km']} km)")
    a("")
    a("== Tre esempi spiegati ==")
    for etichetta, c in esempi.items():
        if not c:
            continue
        a(f"  {etichetta}: {c['nome']} ({c['quartiere'] or '-'}) - {c['veic_giorno']:,.0f} veic/giorno "
          f"+-{100*(c['fascia_50'] or 0):.0f}%, TP {c['tp_am_max']:.1f}/h, linee {len(c['linee'])}, "
          f"metro {c['metro_vicina']}, ferrovia {c['ferrovia_vicina']}")
    a("")
    a("== Prima cintura: corridoi con molto traffico e poco TP ==")
    for c in cintura_guardare[:15]:
        a(f"  {c['veic_giorno']:9,.0f} veic/g  TP {c['tp_am_max']:5.1f}/h  {c['nome'][:40]:40s} ({c['comune']})")
    a(f"  totale prima cintura: {len(cintura)} corridoi, {len(cintura_guardare)} da guardare")
    a("")
    a("== Controllo di buon senso su strade note ==")
    for c in sorted(campione, key=lambda c: -c["veic_giorno"]):
        flag = "DA GUARDARE" if c["da_guardare"] else ("molto traffico, TP ok" if c["molto_traffico"] and not c["poco_tp"] else "")
        a(f"  {c['veic_giorno']:9,.0f} veic/g  TP {c['tp_am_max']:5.1f}/h  {c['nome'][:40]:40s} {flag}")
    a("")
    a("== LIMITI DA DICHIARARE OVUNQUE ==")
    fascia50_testo = 100 * (pub.get("taratura", {}).get("fascia_50") or 0)
    for lim in [
        f"Le stime di traffico sono {classe} (errore mediano {fascia50_testo:.0f}%): "
        "buone per ordinare, non per contare i veicoli.",
        "I sensori 5T di Torino sono a un solo verso: la punta mattina/sera del traffico non e' stimata; "
        "si confronta il totale diurno (circa simmetrico fra i due versi).",
        "La domanda e' l'indagine IMQ 2022: solo residenti 11-84 anni, giorno feriale medio, campione telefonico. "
        "Mancano merci, turisti, non residenti.",
        "L'offerta di trasporto pubblico e' quella programmata (GTFS): non tiene conto di ritardi, "
        "capienza, affollamento. Non c'e' nessuna misura dei passeggeri.",
        "Il trasporto pubblico e' quello dei corridoi con almeno un tratto servito; la metropolitana "
        "non scorre sulle strade ed e' solo un flag (metro_vicina).",
        "Le strade di bordo (valori non affidabili) e le autostrade/tangenziali sono fuori dall'universo.",
    ]:
        a(f"  - {lim}")
    (AQUI.parent / "docs" / "rapporti").mkdir(parents=True, exist_ok=True)
    (AQUI.parent / "docs" / "rapporti" / "RAPPORTO_RISULTATO8_TRAFFICO_TP.txt").write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
