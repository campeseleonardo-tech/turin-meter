# -*- coding: utf-8 -*-
"""
scripts/100_ore_del_giorno.py - Bus contro auto non solo all'ora di punta: le stesse domande degli script 93 (coppie di zone) e 94
(punti prioritari e interscambi del R6, verso Piazza Castello) a 4 ore del giorno.

Sola lettura sui dati. Scelte fissate prima di vedere i numeri (sviluppo/piani/PROMPT_LAVORI.md, blocco L3):
  - ORE (costante qui sotto): 8:00, 13:00, 17:30, 21:00. Giorno feriale 2026-10-12, finestra di 30 minuti attorno all'ora, mediana, cammino a 4,8 km/h:
    come 93 e 94 (per le 8:00 partenza 7:45 e finestra 30 minuti). Il calcolo dei mezzi e dell'auto a flusso libero e' quello degli script 93 e 94 (le funzioni si
    importano da li').
  - auto all'ora h = tempo a flusso libero x fattore(h) + 5 minuti di parcheggio. fattore(h) = mediana, sui sensori 5T con dati affidabili, di
    (velocita' media fra le 2 e le 5) / (velocita' all'ora h), feriale, da data/processed/velocita_5t.json: e' la stessa regola dello script 93, che alle 8 da' 1,2.
    Per le 17:30 si usa la media delle velocita' delle ore 17 e 18. Alle 8 il fattore deve restare quello di oggi entro 0,1, altrimenti ci si ferma.
  - F3 (25/10/2026): la stima principale e' quella aperta (comuni.TempiAutoAperti, §6.1 del piano). A ogni ora l'auto e' il percorso piu' veloce con le velocita'
    dei sensori 5T e delle sonde bus di quell'ora e 20 secondi per semaforo, piu' 5 minuti; il «fattore» di un percorso o di una coppia di zone e' tempo aperto /
    tempo a flusso libero (m93.StimaAperta). I sensori 5T restano come stima piu' favorevole all'auto. Campi: auto_stima_min e auto_favorevole_min.
    Nel JSON «limite_basso» = stima aperta, «limite_alto» = sensori.

Come si lancia
--------------
  python scripts/100_ore_del_giorno.py                    tutto (r5py: ore di calcolo; riprende da dove era arrivato, un file parziale per ora)
  python scripts/100_ore_del_giorno.py --campione 10      solo le 10 zone con piu' auto in uscita (per misurare la durata)
  python scripts/100_ore_del_giorno.py --prova            dati finti piccoli, scrive in una cartella temporanea
Prima servono gli script 93 (coppie, fattori), 94 (luoghi del R6) e 26 (velocita' 5T).

Uscite: data/processed/ore_del_giorno.json, docs/rapporti/RAPPORTO_ORE_DEL_GIORNO.txt (con --campione/--prova: file con suffisso o cartella temporanea)
"""
import argparse
import datetime as dt
import json
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
PROC = RADICE / "data" / "processed"
VELOCITA_5T = PROC / "velocita_5t.json"
TP_AUTO = PROC / "tp_contro_auto.json"
R6_BUS = PROC / "r6_bus_contro_auto.json"
OUT_JSON = PROC / "ore_del_giorno.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_ORE_DEL_GIORNO.txt"

# ora mostrata, partenza della finestra di 30 minuti (centrata sull'ora), ore dei sensori 5T da cui si legge la velocita'
ORE = [
    {"id": "08:00", "label": "8:00", "partenza": dt.time(7, 45), "ore_sensori": (8,)},
    {"id": "13:00", "label": "13:00", "partenza": dt.time(12, 45), "ore_sensori": (13,)},
    {"id": "17:30", "label": "17:30", "partenza": dt.time(17, 15), "ore_sensori": (17, 18)},
    {"id": "21:00", "label": "21:00", "partenza": dt.time(20, 45), "ore_sensori": (21,)},
]
ORE_NOTTE = (2, 3, 4)
TOLLERANZA_FATTORE_8 = 0.1
TOLLERANZA_TEMPO_MIN = 1.0       # alle 8 i tempi coi mezzi devono coincidere con quelli degli script 93 e 94 entro 1 minuto
COPPIE_SALVATE = 100             # le coppie con piu' auto con il loro tempo a ogni ora (servono alle gare delle schede)
PAREGGIO_MAX = 120


def fattore_ora(ore_sensori):
    """Mediana sui sensori 5T con dati affidabili di (velocita' media 2-5) / (velocita' alle ore indicate), feriale, arrotondata a 0,1.
    Come la funzione dello script 93; per piu' ore si usa la media delle velocita' affidabili."""
    d = json.loads(VELOCITA_5T.read_text(encoding="utf-8"))
    valori = []
    for v in d["sensori"].values():
        celle = v["celle"].get("0")
        if not celle:
            continue
        notte = [celle[str(h)]["v"] for h in ORE_NOTTE if str(h) in celle and celle[str(h)]["ok"] and celle[str(h)]["v"]]
        ora = [celle[str(h)]["v"] for h in ore_sensori if str(h) in celle and celle[str(h)]["ok"] and celle[str(h)]["v"]]
        if not notte or not ora:
            continue
        valori.append(float(np.mean(notte)) / float(np.mean(ora)))
    x = np.array(valori)
    q = np.percentile(x, [0, 25, 50, 75, 100])
    return round(float(q[2]), 1), {"sensori_usati": len(x), "minimo": round(float(q[0]), 2), "q1": round(float(q[1]), 2), "mediana": round(float(q[2]), 2),
                                   "q3": round(float(q[3]), 2), "massimo": round(float(q[4]), 2)}


class ModelloFinto:
    """Solo per --prova (dati finti): fattore fisso per ogni percorso e coppia."""

    def luogo(self, nome, ora="08:00"):
        return 1.8, True

    def coppia(self, da, a, libero_min, ora="08:00"):
        return 1.8, True


def mediana(v):
    v = sorted(x for x in v if x is not None)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def coppie_base(m93, zone, auto, t_auto):
    """Le coppie di zone con il loro tempo in auto a flusso libero (non dipende dall'ora) e le auto del mattino; come lo script 93."""
    torino = {k for k, z in zone.items() if z["nome"].startswith("Torino,")}

    def gruppo(a, b):
        n = (a in torino) + (b in torino)
        return "a" if n == 2 else ("b" if n == 1 else "c")

    base, intra, infiniti = [], 0.0, 0
    for a in sorted(zone):
        for b in sorted(zone):
            v = auto.get((a, b), 0.0)
            if a == b:
                intra += v
                continue
            secondi = m93.tempo_zone_auto(zone[a], zone[b], t_auto)
            if not np.isfinite(secondi):
                infiniti += 1
                continue
            base.append({"da": a, "a": b, "gruppo": gruppo(a, b), "auto": v, "libero_min": secondi / 60.0})
    return base, intra, infiniti


def elabora_ora(m93, cfg, f_alto, zone, base, T, pos, luoghi, nodi_extra, t_auto, modello):
    """Tutti i numeri di un'ora: i luoghi del R6 verso Piazza Castello e le coppie di zone.
    Stima aperta: col modello (m93.StimaAperta) il fattore del percorso o della coppia a quell'ora = tempo aperto / tempo a flusso libero."""
    ora_id = cfg["id"]
    fascia = comuni.fascia_di_ora(int(ora_id[:2]) + int(ora_id[3:]) / 60.0)
    out_luoghi = []
    for k, l in enumerate(luoghi):
        libero = t_auto[nodi_extra[k]] / 60.0
        tp = T[pos[f"NOTO{k}_A"], pos[f"NOTO{k}_B"]]
        tp_orario = round(float(tp), 1) if tp == tp else None
        tp = round(comuni.tempo_mezzi_corretto(float(tp), fascia), 1) if tp == tp else None     # L23: corretto con le misure della fascia (script 105)
        f_l, vero = modello.luogo(l["nome"], ora_id)
        auto_alto, auto_basso = round(m93.punta(libero, f_alto), 1), round(m93.punta(libero, f_l), 1)
        out_luoghi.append({"nome": l["nome"], "tipo": l["tipo"], "libero_min": round(libero, 1), "tp_min": tp, "tp_orario_min": tp_orario,
                           "fattore_basso": round(f_l, 2),
                           "auto_favorevole_min": auto_alto, "auto_stima_min": auto_basso,
                           "rapporto_alto": round(tp / auto_alto, 2) if tp else None, "rapporto_basso": round(tp / auto_basso, 2) if tp else None,
                           "pareggio_basso_min": round(max(0.0, tp - libero * f_l), 1) if tp else None,
                           "pareggio_alto_min": round(max(0.0, tp - libero * f_alto), 1) if tp else None})
    coppie, senza = [], []
    for p in base:
        tp, quota = m93.tempo_zone_tp(zone[p["da"]], p["da"], zone[p["a"]], p["a"], pos, T)
        if tp is None or quota < m93.QUOTA_MIN_COLLEGATA:
            senza.append(p)
            continue
        q = dict(p, tp_min=comuni.tempo_mezzi_corretto(tp, fascia), tp_orario_min=tp)
        tp = q["tp_min"]
        q["f_basso"], q["f_basso_vero"] = modello.coppia(p["da"], p["a"], p["libero_min"], ora_id)
        q["auto_favorevole_min"] = m93.punta(q["libero_min"], f_alto)
        q["auto_stima_min"] = m93.punta(q["libero_min"], q["f_basso"])
        q["rapporto"] = tp / q["auto_favorevole_min"]
        q["rapporto_basso"] = tp / q["auto_stima_min"]
        coppie.append(q)
    ab = [p for p in coppie if p["gruppo"] in ("a", "b")]
    senza_ab = [p for p in senza if p["gruppo"] in ("a", "b")]
    riepilogo = {"limite_alto": m93.riepilogo(ab, f_alto), "limite_basso": m93.riepilogo(ab, None), "limite_corretto": m93.riepilogo(ab, None, comuni.fattore_controllo()),
                 "auto_collegate": round(sum(p["auto"] for p in ab)),
                 "senza_collegamento": {"coppie": len(senza_ab), "auto": round(sum(p["auto"] for p in senza_ab))}}
    f_coppie_med = m93.mediana_fattore(ab) if ab else None
    f_luoghi_med = round(float(np.median([l["fattore_basso"] for l in out_luoghi])), 2) if out_luoghi else None
    top = sorted(ab, key=lambda p: -p["auto"])[:COPPIE_SALVATE]
    return {"ora": cfg["id"], "label": cfg["label"], "partenza": f"{cfg['partenza']:%H:%M}", "fattore_alto": f_alto, "fattore_basso": f_coppie_med, "fattore_basso_luoghi": f_luoghi_med,
            "luoghi": out_luoghi, "ab": riepilogo,
            "coppie": [{"da": p["da"], "a": p["a"], "auto": round(p["auto"], 1), "tp_min": round(p["tp_min"], 1), "libero_min": round(p["libero_min"], 1),
                        "auto_favorevole_min": round(p["auto_favorevole_min"], 1), "auto_stima_min": round(p["auto_stima_min"], 1),
                        "fattore_basso": round(p["f_basso"], 2)} for p in top],
            "_coppie_tutte": ab}


def controlli_ora(c, cfg, r, gruppo_dati):
    """Controlli bloccanti e avvisi su un'ora."""
    tutti = [x for l in r["luoghi"] for x in (l["libero_min"], l["auto_favorevole_min"], l["auto_stima_min"]) if x is not None]
    tp = [l["tp_min"] for l in r["luoghi"] if l["tp_min"] is not None]
    coppie = r["_coppie_tutte"]
    ok = (all(np.isfinite(x) and x > 0 for x in tutti) and all(np.isfinite(x) and x > 0 for x in tp)
          and all(np.isfinite(p["tp_min"]) and p["tp_min"] > 0 and p["libero_min"] > 0 for p in coppie))
    c(f"{cfg['label']}: nessun tempo nullo, negativo o infinito", ok, bloccante=True, dettaglio=f"{len(r['luoghi'])} luoghi, {len(coppie)} coppie")
    pv = [x for l in r["luoghi"] for x in (l["pareggio_basso_min"], l["pareggio_alto_min"]) if x is not None]
    c(f"{cfg['label']}: minuti di pareggio fra 0 e {PAREGGIO_MAX}", all(0 <= x <= PAREGGIO_MAX for x in pv), bloccante=True,
      dettaglio=f"da {min(pv):g} a {max(pv):g}" if pv else "nessun valore")
    n_senza = sum(1 for l in r["luoghi"] if l["tp_min"] is None)
    c(f"{cfg['label']}: luoghi senza collegamento coi mezzi entro 120 minuti (contati a parte)", True,
      dettaglio=f"{n_senza} su {len(r['luoghi'])}; coppie di zone senza collegamento: {r['ab']['senza_collegamento']['coppie']} ({r['ab']['senza_collegamento']['auto']:,} auto)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campione", type=int, default=0, help="usa solo le N zone con piu' auto in uscita (file con suffisso _campione)")
    ap.add_argument("--prova", action="store_true", help="dati finti piccoli, scrive in una cartella temporanea")
    ap.add_argument("--lotto", type=int, default=20, help="origini per chiamata r5py (e per salvataggio)")
    args = ap.parse_args()
    t_inizio = time.time()
    c = comuni.Controlli()

    def log(m):
        print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

    m93 = comuni.carica_script("93_tp_contro_auto.py")
    if args.prova:
        cartella = Path(tempfile.mkdtemp(prefix="ore_del_giorno_prova_"))
        out_json, rapporto = cartella / OUT_JSON.name, cartella / RAPPORTO.name
        log(f"PROVA con dati finti: uscite in {cartella}")
    else:
        suffisso = "_campione" if args.campione else ""
        out_json, rapporto = OUT_JSON.with_name(OUT_JSON.stem + suffisso + ".json"), RAPPORTO.with_name(RAPPORTO.stem + suffisso + ".txt")

    # ---- ingressi
    if args.prova:
        zone, auto, luoghi, f_alto0, f_google, t_auto, nodi_extra, tp_per_ora, spostati, fattori = dati_finti(m93)
        modello = ModelloFinto()
    else:
        for f in (TP_AUTO, R6_BUS, VELOCITA_5T):
            c(f"esiste {f.name} (lancia prima gli script 93, 94 e 26)", f.exists(), bloccante=True)
        t93 = json.loads(TP_AUTO.read_text(encoding="utf-8"))
        f_alto0 = t93["parametri"]["fattore_punta"]
        c("fattori letti dal JSON dello script 93 (calcolo completo, non prova)", not t93["parametri"].get("prova"),
          dettaglio=f"alto {f_alto0:g} (sensori)", bloccante=True)
        r94 = json.loads(R6_BUS.read_text(encoding="utf-8"))
        luoghi = [{"nome": l["nome"], "tipo": l["tipo"], "lat": l["lat"], "lon": l["lon"]} for l in r94["luoghi"]]
        zone = m93.carica_zone(False)
        auto = m93.carica_auto(zone)
        if args.campione:
            uscita = defaultdict(float)
            for (a, b), v in auto.items():
                if a != b:
                    uscita[a] += v
            tieni = set(sorted(uscita, key=lambda z: -uscita[z])[:args.campione])
            zone = {k: v for k, v in zone.items() if k in tieni}
            auto = m93.carica_auto(zone)
        extra = [(f"{l['nome']} → Piazza Castello", (l["lat"], l["lon"]), m93.CASTELLO) for l in luoghi]
        log(f"zone: {len(zone)}; luoghi del R6: {len(luoghi)}; auto del mattino fra le zone: {sum(auto.values()):,.0f}")
        log("tempi in auto a flusso libero sulla rete del modello del traffico ...")
        t_auto, nodi_extra, spostati = m93.matrice_auto(zone, extra)
        tp_per_ora = None
        fattori = {cfg["id"]: fattore_ora(cfg["ore_sensori"]) for cfg in ORE}
        modello = m93.StimaAperta(comuni.TempiAutoAperti(log=log), t_auto, zone, nodi_extra, [l["nome"] for l in luoghi])

    # ---- fattori
    f8 = fattori[ORE[0]["id"]][0]
    c("fattore alle 8 = quello di oggi (script 93) entro 0,1", abs(f8 - f_alto0) <= TOLLERANZA_FATTORE_8 + 1e-9, bloccante=True,
      dettaglio=f"ora {f8:g}, script 93 {f_alto0:g}")
    # F3: la stima principale e' quella aperta, per percorso e per ora (modello = m93.StimaAperta, o ModelloFinto in prova)

    base, intra, infiniti = coppie_base(m93, zone, auto, t_auto)
    c("nessun tempo infinito in auto fra zone", infiniti == 0, bloccante=True, dettaglio=f"{infiniti} coppie")

    # ---- mezzi pubblici e riepilogo ora per ora
    risultati = []
    for cfg in ORE:
        log(f"=== {cfg['label']} (partenza {cfg['partenza']:%H:%M}, finestra {m93.FINESTRA_MIN} minuti) ===")
        if args.prova:
            ids, T = tp_per_ora[cfg["id"]]
        else:
            m93.PARTENZA = cfg["partenza"]
            m93.PARZIALE = PROC / f"ore_del_giorno_parziale_{cfg['id'].replace(':', '')}{'_campione' if args.campione else ''}.npz"
            ids, T = m93.matrice_tp(zone, [(f"{l['nome']} → Piazza Castello", (l["lat"], l["lon"]), m93.CASTELLO) for l in luoghi], args.lotto, log)
        pos = {i: k for k, i in enumerate(ids)}
        r = elabora_ora(m93, cfg, fattori[cfg["id"]][0], zone, base, T, pos, luoghi, nodi_extra, t_auto, modello)
        log(f"  stima dei sensori {r['fattore_alto']:g}; stima aperta: fattore mediano {r['fattore_basso']:g} (coppie), {r['fattore_basso_luoghi']:g} (luoghi)")
        controlli_ora(c, cfg, r, None)
        risultati.append(r)

    # ---- confronto alle 8 con gli script 93 e 94 (solo calcolo completo)
    if not args.prova and not args.campione:
        r8 = risultati[0]
        v94 = {l["nome"]: l["tp_min"] for l in r94["luoghi"]}
        diff = [abs(l["tp_min"] - v94[l["nome"]]) for l in r8["luoghi"] if l["tp_min"] is not None and v94.get(l["nome"]) is not None]
        c(f"alle 8 i tempi coi mezzi dei luoghi = quelli dello script 94 entro {TOLLERANZA_TEMPO_MIN:g} minuto", bool(diff) and max(diff) <= TOLLERANZA_TEMPO_MIN,
          dettaglio=f"differenza massima {max(diff):.2f} min su {len(diff)} luoghi" if diff else "nessun confronto")
        v93 = {(p["da"], p["a"]): p["tp_min"] for p in t93["coppie"]}
        d93 = [abs(p["tp_min"] - v93[(p["da"], p["a"])]) for p in r8["_coppie_tutte"] if (p["da"], p["a"]) in v93]
        c(f"alle 8 i tempi coi mezzi delle coppie = quelli dello script 93 entro {TOLLERANZA_TEMPO_MIN:g} minuto (mediana delle differenze)",
          bool(d93) and float(np.median(d93)) <= TOLLERANZA_TEMPO_MIN,
          dettaglio=f"mediana {np.median(d93):.2f} min, massima {max(d93):.1f} min su {len(d93)} coppie" if d93 else "nessun confronto")
        ref = t93["gruppi"]["ab"]
        c("alle 8 il rapporto mediano = quello dello script 93 (entro 0,05)",
          abs(r8["ab"]["limite_basso"]["mediano"] - ref["limite_basso"]["mediano"]) <= 0.05 and abs(r8["ab"]["limite_alto"]["mediano"] - ref["limite_alto"]["mediano"]) <= 0.05,
          dettaglio=f"basso {r8['ab']['limite_basso']['mediano']:.2f} contro {ref['limite_basso']['mediano']:.2f}; alto {r8['ab']['limite_alto']['mediano']:.2f} contro {ref['limite_alto']['mediano']:.2f}")

    # ---- buon senso fra le ore (avvisi)
    r8, r13 = risultati[0], risultati[1]
    c("13:00: l'auto e' piu' veloce che alle 8 (fattore alto non superiore)", r13["fattore_alto"] <= r8["fattore_alto"], dettaglio=f"{r13['fattore_alto']:g} contro {r8['fattore_alto']:g}")
    r21 = risultati[-1]
    c("21:00: l'auto e' piu' veloce che alle 8 (fattore alto non superiore)", r21["fattore_alto"] <= r8["fattore_alto"], dettaglio=f"{r21['fattore_alto']:g} contro {r8['fattore_alto']:g}")
    tp_med = {r["ora"]: mediana([l["tp_min"] for l in r["luoghi"] if l["tipo"] == "punto_prioritario"]) for r in risultati}
    c("21:00: i mezzi dai punti prioritari non piu' veloci che alle 8 (mediana)", tp_med["21:00"] is not None and tp_med["08:00"] is not None and tp_med["21:00"] >= tp_med["08:00"],
      dettaglio=", ".join(f"{k} {v}" for k, v in tp_med.items()))

    # ---- uscite
    for r in risultati:
        r.pop("_coppie_tutte")
    out = {"stimato": True, "campione": args.campione or None, "prova": bool(args.prova),
           "parametri": {"giorno": str(m93.GIORNO), "finestra_min": m93.FINESTRA_MIN, "velocita_piedi_kmh": m93.VEL_PIEDI_KMH,
                         "minuti_parcheggio": m93.MIN_PARCHEGGIO, "fattore_alto_alle_8": f8, "seconda_stima_fonte": "stima aperta (comuni.TempiAutoAperti), per percorso e ora",
                         "ore": [{"id": o["id"], "partenza": f"{o['partenza']:%H:%M}", "ore_sensori": list(o["ore_sensori"])} for o in ORE],
                         "fattori_sensori": {k: v[1] | {"fattore": v[0]} for k, v in fattori.items()}, "punti_spostati": spostati},
           "regola_fattore_basso": "fattore = tempo della stima aperta all'ora / tempo a flusso libero, per ogni percorso e coppia di zone; auto = flusso libero x fattore + 5 minuti",
           "ore": risultati, "controlli": list(c.righe)}
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    def v(x, d=2):
        return "-" if x is None else f"{x:.{d}f}"
    r_ = ["RAPPORTO ORE DEL GIORNO: BUS CONTRO AUTO A 4 ORE (STIMATO)" + (" - CAMPIONE" if args.campione else "") + (" - PROVA CON DATI FINTI" if args.prova else ""),
          f"generato: {dt.datetime.now().isoformat(timespec='seconds')}", "",
          f"Giorno {m93.GIORNO} (feriale), finestra di {m93.FINESTRA_MIN} minuti attorno all'ora, mediana; cammino a {m93.VEL_PIEDI_KMH:g} km/h; auto = flusso libero x fattore + {m93.MIN_PARCHEGGIO:g} minuti.",
          "Stima dei sensori = rallentamento dei sensori 5T alle varie ore (solo traffico: la piu' favorevole all'auto). Stima aperta (principale) = percorso piu' veloce con "
          "sensori 5T, sonde bus e 20 secondi per semaforo, per percorso e ora (fattore = tempo aperto / flusso libero).", "",
          "FATTORI (stima aperta: mediana dei fattori applicati)", "  ora | stima dei sensori | stima aperta, coppie (luoghi) | sensori usati"]
    for r in risultati:
        r_.append(f"  {r['label']} | {r['fattore_alto']:g} | {r['fattore_basso']:g} ({r['fattore_basso_luoghi']:g}) | {fattori[r['ora']][1]['sensori_usati']}")
    r_ += ["", "COPPIE DI ZONE (Torino-Torino e Torino-cintura), rapporto = tempo coi mezzi / tempo in auto, mediano pesato per le auto del mattino",
           "  ora | rapporto mediano (stima aperta - sensori) | auto con rapporto oltre 2 (stima aperta - sensori) | auto collegate | senza collegamento (coppie, auto)"]
    for r in risultati:
        a = r["ab"]
        r_.append(f"  {r['label']} | {v(a['limite_basso']['mediano'])} - {v(a['limite_alto']['mediano'])} | "
                  f"{100 * a['limite_basso']['quota_oltre_2']:.0f}% - {100 * a['limite_alto']['quota_oltre_2']:.0f}% | {a['auto_collegate']:,} | "
                  f"{a['senza_collegamento']['coppie']}, {a['senza_collegamento']['auto']:,}")
    r_ += ["", "PUNTI PRIORITARI DEL R6 e INTERSCAMBI verso Piazza Castello: minuti coi mezzi, minuti in auto (sensori - stima aperta), minuti di pareggio (stima aperta - sensori)",
           "  luogo | tipo | " + " | ".join(r["label"] for r in risultati)]
    for k, l0 in enumerate(risultati[0]["luoghi"]):
        celle = []
        for r in risultati:
            l = r["luoghi"][k]
            celle.append(f"{v(l['tp_min'], 0)} / {l['auto_favorevole_min']:.0f}-{l['auto_stima_min']:.0f} / {v(l['pareggio_basso_min'], 0)}-{v(l['pareggio_alto_min'], 0)}")
        r_.append(f"  {l0['nome']} | {l0['tipo']} | " + " | ".join(celle))
    r_ += ["", "CONTROLLI"] + [f"  {x}" for x in c.righe]
    r_ += ["", "LIMITI: tempi coi mezzi da orario programmato, solo GTT (niente treni); il flusso libero non conta semafori e incroci, la stima aperta si; la stima aperta usa i sensori 5T e le sonde bus "
               "(feriali di ottobre 2026), non misura quel percorso; un solo giorno feriale (12/10) per il GTFS."]
    rapporto.write_text("\n".join(r_) + "\n", encoding="utf-8")
    log(f"scritto {out_json} e {rapporto} ({time.time() - t_inizio:.0f} s)")
    return 0


def dati_finti(m93):
    """Dati piccoli e inventati (seme fisso) nello stesso formato di quelli veri, per provare il calcolo senza r5py ne' rete stradale."""
    rng = np.random.default_rng(7)
    zone, nodo = {}, 0
    for i in range(6):
        punti = []
        for _ in range(2):
            punti.append({"lat": 45.0 + 0.01 * i, "lon": 7.6 + 0.01 * i, "nodo": nodo, "peso": 0.5})
            nodo += 1
        zone[f"Z{i}"] = {"nome": ("Torino, " if i < 4 else "") + f"Zona {i}", "punti": punti}
    auto = {(a, b): float(rng.integers(50, 500)) for a in zone for b in zone}
    luoghi = [{"nome": f"Luogo {k}", "tipo": "punto_prioritario" if k < 3 else "interscambio", "lat": 45.05 + 0.01 * k, "lon": 7.65} for k in range(5)]
    nodi = sorted(p["nodo"] for z in zone.values() for p in z["punti"])
    nodi_extra = [(nodo + 2 * k, nodo + 2 * k + 1) for k in range(len(luoghi))]
    tutti = sorted(set(nodi) | {n for c in nodi_extra for n in c})
    t_auto = {(a, b): float(rng.integers(300, 1800)) for a in tutti for b in tutti}
    ids = [f"{cod}_{k}" for cod, z in zone.items() for k in range(len(z["punti"]))]
    for k in range(len(luoghi)):
        ids += [f"NOTO{k}_A", f"NOTO{k}_B"]
    n = len(ids)
    base_T = rng.integers(10, 70, size=(n, n)).astype(float)
    tp_per_ora = {}
    for j, cfg in enumerate(ORE):
        T = base_T * (1.0 + 0.15 * j)
        T[rng.random((n, n)) < 0.03] = np.nan
        tp_per_ora[cfg["id"]] = (ids, T)
    # velocita' finte: stesso formato di velocita_5t.json non serve, si danno direttamente i fattori
    fattori = {"08:00": (1.2, {"sensori_usati": 0}), "13:00": (1.1, {"sensori_usati": 0}), "17:30": (1.3, {"sensori_usati": 0}), "21:00": (1.0, {"sensori_usati": 0})}
    return zone, auto, luoghi, 1.2, 2.1, t_auto, nodi_extra, tp_per_ora, {"n": 0, "su": 0, "max_m": 0.0}, fattori


if __name__ == "__main__":
    sys.exit(main())
