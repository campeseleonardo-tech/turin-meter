# -*- coding: utf-8 -*-
"""
scripts/21_risultato1_vuoti.py - Risultato 1, fase A: dove mancano i servizi essenziali
(sola lettura di data/processed/accessibilita.json, nessun nuovo calcolo R5)

Domanda: quanti residenti NON hanno un servizio essenziale raggiungibile in 15 min a
piedi, e dove. Cinque gruppi trattati separatamente (nessun indice unico inventato):
scuole, salute, cibo, fermate, verde.

Due livelli di carenza per sezione, scelti con Leo il 12/10:
  zero       = il gruppo conta 0 destinazioni entro 15 min a piedi
               (coerente con la "citta' dei 15 minuti": zero accesso)
  pochissimo = sopra zero ma sotto il 10 percento piu' basso (--percentile)
               della distribuzione, pesata per residenti

Torino e cintura sono SEMPRE riportate separatamente per ogni gruppo (stesso
principio del rapporto di accessibilita'): confrontare "quanti residenti a
Torino" fra gruppi diversi deve sempre usare lo stesso ambito, altrimenti il
confronto e' falso (bug trovato e corretto il 12/10: la prima versione
confrontava fermate/verde calcolati su Torino+cintura con scuole/salute/cibo
calcolati solo su Torino).

Scelta dichiarata sull'ambito del PERCENTILE "pochissimo" (riguarda solo dove
si fissa la soglia, non dove si contano i residenti sotto soglia): per
scuole/salute/cibo il catalogo esiste solo dentro Torino (comune 1272); la
soglia si calcola quindi solo sulle sezioni di Torino. Per fermate e verde
(stessa fonte ovunque: GTFS e OSM) la soglia si calcola su tutte le 8.317
sezioni. In cintura, scuole/salute/cibo restano inoltre segnalati come "dato
non comparabile" (il catalogo comunale non c'e': zero e' spesso mancanza di
dato, non vero vuoto di servizio).

Uscite:
  data/processed/risultato1_vuoti.json  (soglie, numeri per gruppo e ambito,
                                          sezioni peggiori a Torino, flag
                                          "manca" per sezione per uso in mappa)
  docs/rapporti/RAPPORTO_RISULTATO1.txt          (i 3 numeri di testa + dettaglio)

VERSIONE 2 (vedi sviluppo/note_tecniche/R1_servizi.md): le uscite sopra restano uguali; il
JSON ha in piu' la sezione "v2" e il rapporto la sezione "VERSIONE 2" in fondo.
  - per sezione: n_mancanti = quanti dei 5 gruppi sono a "zero" (a Torino: piedi 15 min; in cintura, per scuole,
    salute e cibo, zero sia a piedi sia col mezzo pubblico entro 45 min alle 08 di un feriale);
  - densita' = residenti / km2 (superficie dal campo "a" di sezioni_torino.json): sotto SOGLIA_POCO_ABITATA
    (1.000 ab/km2, sensibilita' 500 e 2.000) la sezione e' "poco abitata", in grigio e fuori dal titolo;
  - titolo = residenti delle sezioni abitate di Torino con 3 o piu' servizi mancanti.

VERSIONE 3 (21/10/2026, Piano risultati A1): le uscite sopra restano uguali; il JSON ha in piu' la sezione "v3" e il
rapporto la sezione "VERSIONE 3" in fondo. Solo Torino, solo zone abitate (almeno 1.000 ab/km2, senza le zone "da
verificare"): residenti con tutti e 5 i servizi a 5, 10 e 15 minuti a piedi, e residenti per numero di servizi presenti
(0-5) a ogni soglia. Legge anche data/processed/accessibilita_piedi10.json e accessibilita_piedi5.json (script 18
con --solo-piedi, python scripts/rifai_tutto.py --solo accessibilita); se un file manca la soglia e' saltata e scritto nel rapporto.
Per circoscrizione solo se le sezioni hanno il campo; altrimenti salta e lo scrive.

Usage:
    python 21_risultato1_vuoti.py [--percentile 10]
"""

import argparse
import datetime as dt
import csv
import io
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni

RADICE = Path(__file__).resolve().parent.parent
ACCESS = RADICE / "data/processed/accessibilita.json"
OUT = RADICE / "data/processed/risultato1_vuoti.json"
RAPPORTO = RADICE / "docs/rapporti/RAPPORTO_RISULTATO1.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
SEZIONI_GEO = RADICE / "data/processed/sezioni_torino.json"   # campo "a" = superficie in km2

GRUPPI = ["scuole", "salute", "cibo", "fermate", "verde"]
SOLO_TORINO_PERCENTILE = {"scuole", "salute", "cibo"}  # dove si fissa la soglia "pochissimo"
NON_COMPARABILE_CINTURA = {"scuole", "salute", "cibo"}  # catalogo assente in cintura
COMUNE_TORINO_PREFIX = "1272"

# ---- versione 2 (20/10/2026)
SOGLIA_POCO_ABITATA = 1000          # ab/km2: sotto, la sezione e' "poco abitata" (Leo, 20/10/2026)
SENSIBILITA_SOGLIA = (500, 2000)    # prove di sensibilita' sulla soglia
SOGLIA_TITOLO = 3                   # titolo = residenti abitati con almeno 3 servizi mancanti
ORA_TP = "08"                       # mezzo pubblico: alle 08 di un feriale (gia' calcolato da 18_accessibilita.py)
GRUPPI_TP_CINTURA = {"scuole", "salute", "cibo"}  # in cintura manca solo se zero a piedi E col mezzo pubblico
MAX_SENZA_SUPERFICIE = 10           # oltre, AVVISO
RAGGIO_FERMATA_SOSPETTA_M = 300     # sezione "da verificare": zero fermate a piedi ma una fermata GTT entro questo raggio (Leo, 20/10)
GTFS = RADICE / "data/raw/gtt_gtfs_20261003_224530.zip"   # stesso GTFS dello script 18 (sola lettura)

# ---- versione 3 (21/10/2026)
SOGLIE_PIEDI_MIN = (5, 10, 15)      # minuti a piedi; il 15 viene da accessibilita.json, 5 e 10 da script 18 --solo-piedi
FILE_PIEDI = {5: RADICE / "data/processed/accessibilita_piedi5.json",
              10: RADICE / "data/processed/accessibilita_piedi10.json"}
CAMPI_CIRCOSCRIZIONE = ("circoscrizione", "circ", "cir")   # nomi possibili del campo in sezioni_torino.json


def e_torino(sid):
    return str(sid).startswith(COMUNE_TORINO_PREFIX)


def percentile_pesato(coppie, p):
    """Valore sotto cui sta il p-esimo percento dei residenti (coppie pesate).
    coppie = [(valore, residenti)]. Ritorna la soglia (valore massimo incluso
    nella fascia "pochissimo"), o None se non calcolabile."""
    coppie = sorted((v, w) for v, w in coppie if w and w > 0)
    tot = sum(w for _, w in coppie)
    if tot <= 0:
        return None
    cum = 0.0
    for v, w in coppie:
        cum += w
        if cum / tot * 100.0 >= p:
            return v
    return coppie[-1][0] if coppie else None


def conta(sottoinsieme, g, soglia):
    """Residenti/sezioni a 'zero' e a 'pochissimo' (0 < v <= soglia) in un sottoinsieme."""
    res_zero = sez_zero = res_poco = sez_poco = 0
    for s in sottoinsieme:
        v = s["piedi"]["15"].get(g, 0)
        if v == 0:
            res_zero += s["res"]; sez_zero += 1
        elif soglia is not None and v <= soglia:
            res_poco += s["res"]; sez_poco += 1
    tot = sum(s["res"] for s in sottoinsieme)
    pct = lambda r: round(100.0 * r / tot, 1) if tot else None
    return {
        "residenti_totali_ambito": tot,
        "zero": {"residenti": res_zero, "sezioni": sez_zero, "quota_residenti": pct(res_zero)},
        "pochissimo": {"residenti": res_poco, "sezioni": sez_poco, "quota_residenti": pct(res_poco)},
    }


def carica_superfici():
    """{id sezione: superficie in km2} da sezioni_torino.json (campo "a"). Solo lettura."""
    return {str(s["id"]): s.get("a") for s in json.loads(SEZIONI_GEO.read_text(encoding="utf-8"))}


_FERMATE = []


def fermate_gtfs():
    """[(lat, lon)] delle fermate di stops.txt (solo location_type 0 o vuoto); lette una volta sola."""
    if not _FERMATE:
        with zipfile.ZipFile(GTFS) as z:
            testo = z.read("stops.txt").decode("utf-8-sig")
        for r in csv.DictReader(io.StringIO(testo)):
            if r.get("location_type", "") not in ("", "0"):
                continue
            try:
                _FERMATE.append((float(r["stop_lat"]), float(r["stop_lon"])))
            except (ValueError, KeyError):
                continue
    return _FERMATE


def fermata_piu_vicina_m(lat, lon):
    """Distanza in metri (linea d'aria) dalla fermata GTT piu' vicina, oppure None se non ci sono fermate."""
    return min((comuni.haversine_m(lat, lon, la, lo) for la, lo in fermate_gtfs()), default=None)


def da_verificare(s):
    """Ritorna la distanza (m) della fermata piu' vicina se la sezione e' "da verificare" (zero fermate a piedi in
    15 min ma una fermata entro RAGGIO_FERMATA_SOSPETTA_M in linea d'aria), altrimenti None."""
    if s["piedi"]["15"].get("fermate", 0) != 0:
        return None
    d = fermata_piu_vicina_m(s["lat"], s["lon"])
    return d if d is not None and d <= RAGGIO_FERMATA_SOSPETTA_M else None


def densita(sez, superfici):
    """residenti / km2, oppure None se la superficie manca o non e' positiva."""
    a = superfici.get(str(sez["id"]))
    return sez["res"] / a if a and a > 0 else None


def n_mancanti_sezione(s, ora_tp=ORA_TP):
    """Ritorna (n_mancanti con la regola v2, n_mancanti solo a piedi, tp_disponibile, maschera di bit dei gruppi
    mancanti con la regola v2: scuole=1, salute=2, cibo=4, fermate=8, verde=16).
    Torino: gruppo mancante = zero a piedi in 15 min. Cintura: per scuole/salute/cibo mancante solo se zero a piedi
    E zero col mezzo pubblico entro il cutoff TP all'ora ora_tp; fermate e verde come Torino."""
    tp = (s.get("tp") or {}).get(ora_tp)
    torino = e_torino(s["id"])
    n_v2 = n_piedi = m = 0
    for i, g in enumerate(GRUPPI):
        a_zero = s["piedi"]["15"].get(g, 0) == 0
        n_piedi += a_zero
        if torino or g not in GRUPPI_TP_CINTURA or tp is None:
            manca = a_zero
        else:
            manca = a_zero and tp.get(g, 0) == 0
        n_v2 += manca
        m |= int(manca) << i
    return n_v2, n_piedi, tp is not None, m


def riepilogo_ambito(righe_sez, soglia):
    """righe_sez = [{"res", "n", "dens"}]: residenti per n_mancanti 0..5, separati abitate / poco abitate.
    Le sezioni senza superficie (dens None) contano come abitate (dichiarato nel rapporto)."""
    per = {"abitate": {str(k): 0 for k in range(6)}, "poco_abitate": {str(k): 0 for k in range(6)},
           "da_verificare": {str(k): 0 for k in range(6)}}
    sez_poco = sez_verif = 0
    for r in righe_sez:   # ordine degli stati: poco abitata, poi da verificare, poi abitata
        poco = r["dens"] is not None and r["dens"] < soglia
        verif = bool(r.get("verif")) and not poco
        per["poco_abitate" if poco else "da_verificare" if verif else "abitate"][str(r["n"])] += r["res"]
        sez_poco += poco
        sez_verif += verif
    tot_ab = sum(per["abitate"].values())
    tot_poco = sum(per["poco_abitate"].values())
    tot_verif = sum(per["da_verificare"].values())
    return {
        "soglia_ab_km2": soglia,
        "per_n_mancanti": per,
        "residenti_abitate": tot_ab,
        "residenti_poco_abitate": tot_poco,
        "sezioni_poco_abitate": sez_poco,
        "residenti_da_verificare": tot_verif,
        "sezioni_da_verificare": sez_verif,
        "abitate_con_3_o_piu_mancanti": sum(per["abitate"][str(k)] for k in range(SOGLIA_TITOLO, 6)),
        "abitate_con_1_o_piu_mancanti": sum(per["abitate"][str(k)] for k in range(1, 6)),
        "abitate_tutti_5_mancanti": per["abitate"]["5"],
        "tutte_le_zone_tutti_5_mancanti": per["abitate"]["5"] + per["poco_abitate"]["5"],
    }


def calcola_v2(sezioni, superfici):
    """Sezione "v2" del JSON: Torino e cintura sempre separate; ritorna (dict, lista di controlli (esito, testo))."""
    righe = {"torino": [], "cintura": [], "cintura_regola_di_oggi": []}
    per_sez = []
    senza_sup = senza_tp = 0
    negative = 0
    critiche = []
    verificare = []
    bit_errati = 0
    for s in sezioni:
        n2, n_piedi, tp_ok, m = n_mancanti_sezione(s)
        d = densita(s, superfici)
        dist_f = da_verificare(s)
        verif = dist_f is not None
        senza_sup += d is None
        negative += d is not None and d < 0
        amb = "torino" if e_torino(s["id"]) else "cintura"
        if amb == "cintura":
            senza_tp += not tp_ok
            righe["cintura_regola_di_oggi"].append({"res": s["res"], "n": n_piedi, "dens": d, "verif": verif})
        righe[amb].append({"res": s["res"], "n": n2, "dens": d, "verif": verif})
        poco = d is not None and d < SOGLIA_POCO_ABITATA
        bit_errati += bin(m).count("1") != n2
        per_sez.append({"id": s["id"], "n_mancanti": n2, "densita": None if d is None else round(d, 1),
                        "m": m, "poco": poco, "verif": verif and not poco})
        voce = {"id": s["id"], "res": s["res"], "densita": None if d is None else round(d, 1),
                "n_mancanti": n2, "mancano": [g for i, g in enumerate(GRUPPI) if m >> i & 1]}
        if verif and not poco:
            verificare.append({**voce, "ambito": amb, "fermata_m": round(dist_f)})
        elif amb == "torino" and not poco and n2 >= SOGLIA_TITOLO:
            critiche.append(voce)
    critiche.sort(key=lambda c: -c["res"])
    verificare.sort(key=lambda c: -c["res"])

    soglie = [SOGLIA_POCO_ABITATA] + [x for x in SENSIBILITA_SOGLIA if x != SOGLIA_POCO_ABITATA]
    ambiti = {amb: {str(x): riepilogo_ambito(righe[amb], x) for x in sorted(soglie)}
              for amb in ("torino", "cintura", "cintura_regola_di_oggi")}
    ref = ambiti["torino"][str(SOGLIA_POCO_ABITATA)]
    v2 = {
        "soglia_poco_abitata_ab_km2": SOGLIA_POCO_ABITATA,
        "soglia_titolo_n_mancanti": SOGLIA_TITOLO,
        "sensibilita_ab_km2": list(SENSIBILITA_SOGLIA),
        "ora_tp_cintura": ORA_TP,
        "regola": ("Torino: servizio mancante = zero destinazioni entro 15 min a piedi. Cintura: per scuole, salute e "
                   "cibo mancante solo se zero a piedi (15 min) E zero col mezzo pubblico (entro 45 min, alle 08 di "
                   "un feriale); fermate e verde come Torino. Tabelle sempre separate."),
        "titolo": {"residenti_abitati_con_3_o_piu_mancanti": ref["abitate_con_3_o_piu_mancanti"],
                   "residenti_torino": ref["residenti_abitate"] + ref["residenti_poco_abitate"] + ref["residenti_da_verificare"],
                   "residenti_poco_abitate": ref["residenti_poco_abitate"],
                   "residenti_da_verificare": ref["residenti_da_verificare"],
                   "residenti_tutti_5_mancanti": ref["tutte_le_zone_tutti_5_mancanti"]},
        "sezioni_senza_superficie": senza_sup,
        "sezioni_cintura_senza_tp": senza_tp,
        "torino": ambiti["torino"],
        "cintura": ambiti["cintura"],
        "cintura_regola_di_oggi": ambiti["cintura_regola_di_oggi"],
        "ordine_bit": GRUPPI,
        "sezioni_critiche_torino": critiche,
        "raggio_fermata_sospetta_m": RAGGIO_FERMATA_SOSPETTA_M,
        "sezioni_da_verificare": verificare,
        "sezioni": per_sez,
    }
    controlli = []
    controlli.append(("OK" if bit_errati == 0 else "AVVISO",
                      f"maschera di bit: sezioni dove i bit accesi != n_mancanti: {bit_errati}"))
    somma_crit = sum(c["res"] for c in critiche)
    tit = v2["titolo"]["residenti_abitati_con_3_o_piu_mancanti"]
    controlli.append(("OK" if somma_crit == tit else "AVVISO",
                      f"sezioni critiche di Torino: {len(critiche)}, somma residenti {somma_crit:,} "
                      f"(titolo {tit:,})"))
    for amb in ("torino", "cintura"):
        tot = sum(s["res"] for s in sezioni if (e_torino(s["id"])) == (amb == "torino"))
        for x, r in ambiti[amb].items():
            somma = r["residenti_abitate"] + r["residenti_poco_abitate"] + r["residenti_da_verificare"]
            controlli.append(("OK" if somma == tot else "AVVISO",
                              f"{amb}, soglia {x}: somma residenti per n_mancanti = {somma:,} (residenti ambito {tot:,})"))
    controlli.append(("OK" if negative == 0 else "AVVISO", f"densita' negative: {negative}"))
    controlli.append(("OK" if senza_sup <= MAX_SENZA_SUPERFICIE else "AVVISO",
                      f"sezioni senza superficie: {senza_sup} (contate come abitate; AVVISO se piu' di {MAX_SENZA_SUPERFICIE})"))
    controlli.append(("OK" if senza_tp == 0 else "AVVISO",
                      f"sezioni di cintura senza mezzo pubblico alle {ORA_TP}: {senza_tp} (per loro vale solo il piedi)"))
    return v2, controlli


def righe_rapporto_v2(v2, controlli):
    """Sezione "VERSIONE 2" in fondo al rapporto (aggiunta: il testo della versione 1 resta uguale)."""
    t = v2["titolo"]
    ref = str(v2["soglia_poco_abitata_ab_km2"])
    out = ["", "=" * 78, "VERSIONE 2 (20/10/2026): servizi mancanti per sezione, zone poco abitate a parte",
           f"regola: {v2['regola']}",
           f"soglia 'poco abitata': sotto {v2['soglia_poco_abitata_ab_km2']:,} ab/km2 (sensibilita': "
           + ", ".join(f"{x:,}" for x in v2["sensibilita_ab_km2"]) + ")",
           "",
           f"TITOLO: {t['residenti_abitati_con_3_o_piu_mancanti']:,} residenti di Torino, in zone abitate, "
           f"senza {SOGLIA_TITOLO} o piu' dei 5 servizi (su {t['residenti_torino']:,} residenti di Torino)",
           f"  tutti e 5 mancanti (tutte le zone): {t['residenti_tutti_5_mancanti']:,} residenti (non fa titolo)",
           f"  residenti nelle zone poco abitate (a parte): {t['residenti_poco_abitate']:,}",
           f"  residenti nelle zone da verificare (a parte): {t['residenti_da_verificare']:,}",
           ""]
    for amb, nome in (("torino", "TORINO"), ("cintura", "CINTURA (regola v2: piedi 15 min o mezzo pubblico 45 min alle "
                                                         f"{v2['ora_tp_cintura']}; scuole/salute/cibo non comparabili con Torino)"),
                      ("cintura_regola_di_oggi", "CINTURA con la regola di oggi (solo a piedi), per confronto")):
        out.append(f"{nome}: residenti per numero di servizi mancanti (soglia {ref} ab/km2)")
        r = v2[amb][ref]["per_n_mancanti"]
        for k in range(6):
            out.append(f"  {k} mancanti: abitate {r['abitate'][str(k)]:,}   poco abitate {r['poco_abitate'][str(k)]:,}")
        out.append("  sensibilita' della soglia (poco abitate / abitate con 3+ mancanti / abitate con 1+ mancanti):")
        for x in sorted(v2[amb], key=int):
            q = v2[amb][x]
            out.append(f"    {int(x):>5} ab/km2: {q['residenti_poco_abitate']:,} / "
                       f"{q['abitate_con_3_o_piu_mancanti']:,} / {q['abitate_con_1_o_piu_mancanti']:,}")
        out.append("")
    out.append("CONTROLLI:")
    out += [f"  {esito}: {testo}" for esito, testo in controlli]
    crit = v2["sezioni_critiche_torino"]
    out += ["", "SEZIONI CRITICHE DI TORINO (abitate, 3+ mancanti)"]
    for c in crit:
        dens = "n.d." if c["densita"] is None else f"{c['densita']:,.0f}"
        out.append(f"  {c['id']}: {c['res']:,} residenti, {dens} ab/km2, mancano: {', '.join(c['mancano'])}")
    out.append(f"  ({len(crit)} sezioni) da guardare a mano con Leo (lavoro 7)")
    ver = v2["sezioni_da_verificare"]
    out += ["", f"SEZIONI DA VERIFICARE (zero fermate a 15 min a piedi, ma una fermata GTT entro "
                f"{v2['raggio_fermata_sospetta_m']} m in linea d'aria; escluse da titolo e candidati)"]
    for c in ver:
        dens = "n.d." if c["densita"] is None else f"{c['densita']:,.0f}"
        out.append(f"  {c['id']} ({c['ambito']}): {c['res']:,} residenti, {dens} ab/km2, fermata a {c['fermata_m']} m, "
                   f"mancano: {', '.join(c['mancano']) or 'nessuno'}")
    out.append(f"  ({len(ver)} sezioni, {sum(c['res'] for c in ver):,} residenti) da correggere nello script 18 "
               "(SEZIONI_FUORI_RETE) al prossimo calcolo completo dell'accessibilita'.")
    out.append("LIMITI v2: capienza di ospedali, presidi e scuole non nota (un ospedale grande e un ambulatorio "
               "contano uguale); orario programmato; catalogo diverso fra Torino e cintura; sezioni senza "
               "superficie contate come abitate.")
    return out


# ---------------------------------------------------------------- versione 3: copertura a 5, 10 e 15 minuti

def carica_piedi_per_soglia(soglia, sezioni_15):
    """{id sezione: {gruppo: destinazioni}} per una soglia a piedi, oppure (None, motivo) se non disponibile."""
    if soglia == 15:
        return {str(s["id"]): s["piedi"]["15"] for s in sezioni_15}, None
    f = FILE_PIEDI[soglia]
    if not f.is_file():
        return None, f"manca {f.name} (lancia python scripts/rifai_tutto.py --solo accessibilita)"
    d = json.loads(f.read_text(encoding="utf-8"))
    if d.get("parametri", {}).get("cutoff_piedi_min") != soglia:
        return None, f"{f.name} e' stato calcolato a {d.get('parametri', {}).get('cutoff_piedi_min')} minuti, non {soglia}"
    return {str(s["id"]): s["piedi"][str(soglia)] for s in d["sezioni"]}, None


def carica_circoscrizioni():
    """{id sezione: circoscrizione} se sezioni_torino.json ha il campo, altrimenti {}."""
    out = {}
    for s in json.loads(SEZIONI_GEO.read_text(encoding="utf-8")):
        for campo in CAMPI_CIRCOSCRIZIONE:
            if s.get(campo) not in (None, ""):
                out[str(s["id"])] = str(s[campo])
                break
    return out


def conteggi_soglia(base, piedi):
    """base = [{"id","res","circ"}]; piedi = {id: {gruppo: n}}. Ritorna residenti per numero di servizi presenti (0-5),
    quota con tutti e 5, residenti senza il servizio per gruppo. Un servizio c'e' se il gruppo ha almeno 1 destinazione."""
    per_n = {str(k): 0 for k in range(6)}
    senza = {g: 0 for g in GRUPPI}
    for b in base:
        p = piedi[b["id"]]
        presenti = sum(1 for g in GRUPPI if p.get(g, 0) > 0)
        per_n[str(presenti)] += b["res"]
        for g in GRUPPI:
            if p.get(g, 0) == 0:
                senza[g] += b["res"]
    tot = sum(per_n.values())
    return {"residenti": tot, "per_n_servizi": per_n, "tutti_5": per_n["5"],
            "quota_tutti_5": round(100.0 * per_n["5"] / tot, 2) if tot else None, "senza_servizio": senza}


def calcola_v3(sezioni, superfici, v2):
    """Sezione "v3" del JSON: Torino, zone abitate (>= SOGLIA_POCO_ABITATA ab/km2; le sezioni senza superficie contano
    come abitate; le zone "da verificare" della v2 restano fuori finche' l'accessibilita' a 15 minuti non e' rifatta con
    la correzione dei centroidi). Ritorna (dict, controlli [(esito, testo)])."""
    verif = {c["id"] for c in v2["sezioni_da_verificare"]}
    circ = carica_circoscrizioni()
    base, fuori_verif = [], 0
    for s in sezioni:
        if not e_torino(s["id"]):
            continue
        d = densita(s, superfici)
        if d is not None and d < SOGLIA_POCO_ABITATA:
            continue
        if s["id"] in verif:
            fuori_verif += s["res"]
            continue
        base.append({"id": str(s["id"]), "res": s["res"], "circ": circ.get(str(s["id"]))})
    tot_base = sum(b["res"] for b in base)
    controlli = []
    soglie, non_calcolate = {}, {}
    piedi_per_soglia = {}
    for m in SOGLIE_PIEDI_MIN:
        piedi, motivo = carica_piedi_per_soglia(m, sezioni)
        if piedi is not None:
            mancanti = [b["id"] for b in base if b["id"] not in piedi]
            if mancanti:
                piedi, motivo = None, f"{len(mancanti)} sezioni abitate di Torino senza dati a {m} minuti"
        if piedi is None:
            non_calcolate[str(m)] = motivo
            continue
        piedi_per_soglia[m] = piedi
        r = conteggi_soglia(base, piedi)
        soglie[str(m)] = r
        controlli.append(("OK" if r["residenti"] == tot_base and sum(r["per_n_servizi"].values()) == tot_base else "ERRORE",
                          f"{m} minuti: somma dei residenti per numero di servizi = {sum(r['per_n_servizi'].values()):,} "
                          f"(zone abitate {tot_base:,})"))
    for k, motivo in non_calcolate.items():
        controlli.append(("AVVISO", f"{k} minuti non calcolato: {motivo}"))
    disponibili = sorted(int(k) for k in soglie)
    for a, b in zip(disponibili, disponibili[1:]):
        ok = soglie[str(a)]["tutti_5"] <= soglie[str(b)]["tutti_5"]
        controlli.append(("OK" if ok else "ERRORE",
                          f"copertura {a} min {soglie[str(a)]['tutti_5']:,} <= {b} min {soglie[str(b)]['tutti_5']:,} residenti"))
        n_viol = sum(1 for x in base if sum(1 for g in GRUPPI if piedi_per_soglia[a][x["id"]].get(g, 0) > 0)
                     > sum(1 for g in GRUPPI if piedi_per_soglia[b][x["id"]].get(g, 0) > 0))
        controlli.append(("OK" if n_viol == 0 else "AVVISO",
                          f"sezioni con piu' servizi a {a} minuti che a {b}: {n_viol}"))
    v3 = {
        "ambito": "Torino, zone abitate",
        "soglia_poco_abitata_ab_km2": SOGLIA_POCO_ABITATA,
        "minuti_a_piedi": disponibili,
        "soglie_non_calcolate": non_calcolate,
        "residenti_zone_abitate": tot_base,
        "sezioni_zone_abitate": len(base),
        "residenti_da_verificare_esclusi": fuori_verif,
        "regola": ("Un servizio c'e' se il gruppo ha almeno una destinazione entro i minuti indicati a piedi (80 m/min). "
                   "Zone abitate = almeno 1.000 ab/km2; le zone da verificare (v2) restano fuori finche' l'accessibilita' "
                   "a 15 minuti non e' rifatta con la correzione dei centroidi di via Chieti."),
        "soglie": soglie,
    }
    if circ:
        per_circ = {}
        for c in sorted({b["circ"] for b in base if b["circ"] is not None}):
            sotto = [b for b in base if b["circ"] == c]
            per_circ[c] = {m: conteggi_soglia(sotto, piedi_per_soglia[int(m)]) for m in soglie}
        v3["circoscrizioni"] = per_circ
        somma = sum(r["residenti"] for c in per_circ.values() for r in list(c.values())[:1])
        controlli.append(("OK" if somma == sum(b["res"] for b in base if b["circ"] is not None) else "ERRORE",
                          f"circoscrizioni: somma dei residenti {somma:,}"))
    else:
        v3["circoscrizioni"] = None
        v3["nota_circoscrizioni"] = ("Per circoscrizione saltato: le sezioni di sezioni_torino.json non hanno il campo "
                                     f"({', '.join(CAMPI_CIRCOSCRIZIONE)}).")
    return v3, controlli


def righe_rapporto_v3(v3, controlli):
    """Sezione "VERSIONE 3" in fondo al rapporto (aggiunta: il testo delle versioni 1 e 2 resta uguale)."""
    out = ["", "=" * 78,
           "VERSIONE 3 (21/10/2026): copertura a 5, 10 e 15 minuti a piedi, Torino, zone abitate",
           f"regola: {v3['regola']}",
           f"zone abitate: {v3['residenti_zone_abitate']:,} residenti in {v3['sezioni_zone_abitate']:,} sezioni "
           f"(esclusi {v3['residenti_da_verificare_esclusi']:,} residenti delle zone da verificare)", ""]
    nomi = {"scuole": "scuole", "salute": "salute", "cibo": "negozi", "fermate": "fermate", "verde": "verde"}
    for m in v3["minuti_a_piedi"]:
        r = v3["soglie"][str(m)]
        out.append(f"A {m} MINUTI: tutti e 5 i servizi per {r['tutti_5']:,} residenti ({r['quota_tutti_5']}%)")
        out.append("  residenti per numero di servizi presenti: "
                   + "   ".join(f"{k}: {r['per_n_servizi'][str(k)]:,}" for k in range(6)))
        out.append("  residenti senza il servizio: " + ", ".join(f"{nomi[g]} {r['senza_servizio'][g]:,}" for g in GRUPPI))
    for k, motivo in v3["soglie_non_calcolate"].items():
        out.append(f"A {k} MINUTI: NON CALCOLATO - {motivo}")
    if v3["circoscrizioni"]:
        out += ["", "PER CIRCOSCRIZIONE (tutti e 5 i servizi)"]
        for c, per in v3["circoscrizioni"].items():
            out.append(f"  {c}: " + "   ".join(f"{m} min {r['tutti_5']:,}/{r['residenti']:,} ({r['quota_tutti_5']}%)"
                                               for m, r in per.items()))
    else:
        out += ["", v3["nota_circoscrizioni"]]
    out += ["", "CONTROLLI v3:"] + [f"  {e}: {t}" for e, t in controlli]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--percentile", type=float, default=10.0,
                     help="soglia della fascia 'pochissimo', in percento di residenti (default 10)")
    args = ap.parse_args()
    p = args.percentile

    access = json.loads(ACCESS.read_text(encoding="utf-8"))
    sezioni = access["sezioni"]
    taglio = access["parametri"]["cutoff_piedi_min"]
    print(f"Sezioni: {len(sezioni)}  cutoff a piedi: {taglio} min")

    torino = [s for s in sezioni if e_torino(s["id"])]
    cintura = [s for s in sezioni if not e_torino(s["id"])]
    print(f"Torino: {len(torino)}  cintura: {len(cintura)}")

    gruppi_esito = {}
    per_sezione_manca = {s["id"]: {} for s in sezioni}

    for g in GRUPPI:
        ambito_soglia = torino if g in SOLO_TORINO_PERCENTILE else sezioni
        soglia = percentile_pesato(
            [(s["piedi"]["15"].get(g, 0), s["res"]) for s in ambito_soglia], p)

        # il flag per-sezione (per la mappa) usa sempre la stessa soglia, su tutte le sezioni
        for s in sezioni:
            v = s["piedi"]["15"].get(g, 0)
            if v == 0:
                per_sezione_manca[s["id"]][g] = "zero"
            elif soglia is not None and v <= soglia:
                per_sezione_manca[s["id"]][g] = "pochissimo"

        peggiori_torino = sorted(
            [s for s in torino if s["piedi"]["15"].get(g, 0) == 0],
            key=lambda s: -s["res"])[:15]

        gruppi_esito[g] = {
            "ambito_percentile": "torino" if g in SOLO_TORINO_PERCENTILE else "torino+cintura",
            "soglia_pochissimo": soglia,
            "torino": conta(torino, g, soglia),
            "cintura": conta(cintura, g, soglia),
            "cintura_comparabile": g not in NON_COMPARABILE_CINTURA,
            "sezioni_peggiori_zero_torino": [
                {"id": s["id"], "res": s["res"], "lat": s["lat"], "lon": s["lon"]}
                for s in peggiori_torino],
        }
        if g in NON_COMPARABILE_CINTURA:
            gruppi_esito[g]["nota_cintura"] = (
                "catalogo comunale solo per Torino: in cintura 'zero'/'pochissimo' e' quasi "
                "sempre mancanza di dato, non assenza di servizio. Numeri riportati ma NON "
                "comparabili con Torino.")

    # 3 numeri di testa: tutti calcolati SOLO su Torino, confrontabili tra loro.
    res_torino_tot = sum(s["res"] for s in torino)
    almeno_uno_zero_torino = sum(
        s["res"] for s in torino if any(s["piedi"]["15"].get(g, 0) == 0 for g in GRUPPI))
    gruppo_peggiore = max(GRUPPI, key=lambda g: gruppi_esito[g]["torino"]["zero"]["residenti"])

    esito = {
        "generato": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "fonte": "data/processed/accessibilita.json (giro completo 12/10/2026,)",
        "percentile_pochissimo": p,
        "nota_ambito_percentile": ("La SOGLIA 'pochissimo' per scuole/salute/cibo e' fissata solo "
                         "su Torino (catalogo comunale); per fermate/verde su Torino+cintura "
                         "(fonte uniforme). I CONTEGGI di residenti/sezioni sotto soglia sono "
                         "invece sempre riportati separati per Torino e cintura, per ogni gruppo."),
        "numeri_di_testa": {
            "residenti_torino": res_torino_tot,
            "residenti_torino_senza_almeno_un_servizio_essenziale_a_zero": almeno_uno_zero_torino,
            "quota_residenti_torino": round(100.0 * almeno_uno_zero_torino / res_torino_tot, 1) if res_torino_tot else None,
            "gruppo_piu_carente_a_torino": gruppo_peggiore,
        },
        "gruppi": gruppi_esito,
        "sezioni_manca": [
            {"id": sid, "manca": v} for sid, v in per_sezione_manca.items() if v],
    }
    v2, controlli_v2 = calcola_v2(sezioni, carica_superfici())
    esito["v2"] = v2
    for esito_c, testo_c in controlli_v2:
        print(f"  v2 {esito_c}: {testo_c}")
    v3, controlli_v3 = calcola_v3(sezioni, carica_superfici(), v2)
    esito["v3"] = v3
    for esito_c, testo_c in controlli_v3:
        print(f"  v3 {esito_c}: {testo_c}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(esito, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Scritto {OUT} ({OUT.stat().st_size/1e3:.0f} KB)")

    # ---- rapporto leggibile
    righe = [
        "RAPPORTO RISULTATO 1 - fase A: dove mancano i servizi essenziali (STIMATO, a piedi)",
        f"generato: {esito['generato']}",
        f"fonte: {esito['fonte']}",
        f"cutoff a piedi: {taglio} min   soglia 'pochissimo': sotto il {p:.0f}% dei residenti",
        "",
        "I 3 NUMERI (tutti su Torino, confrontabili tra loro):",
        f"  1) Residenti a Torino SENZA ALMENO UN servizio essenziale entro {taglio} min a piedi: "
        f"{almeno_uno_zero_torino:,} su {res_torino_tot:,} ({esito['numeri_di_testa']['quota_residenti_torino']}%)",
        f"  2) Gruppo piu' carente a Torino (piu' residenti a zero, a Torino): {gruppo_peggiore}",
        "  3) Vedi dettaglio: la cintura ha percentuali di 'zero' molto piu' alte, ma per "
        "scuole/salute/cibo NON sono comparabili con Torino (manca il catalogo, non il servizio)",
        "",
        "DETTAGLIO PER GRUPPO (Torino e cintura sempre separate):",
    ]
    for g in GRUPPI:
        d = gruppi_esito[g]
        righe.append(f"  {g}  (soglia 'pochissimo' = {d['soglia_pochissimo']}, "
                      f"fissata su: {d['ambito_percentile']}):")
        t = d["torino"]
        righe.append(f"    Torino:   zero {t['zero']['residenti']:,} res / {t['zero']['sezioni']} sez "
                      f"({t['zero']['quota_residenti']}%)   pochissimo {t['pochissimo']['residenti']:,} res / "
                      f"{t['pochissimo']['sezioni']} sez ({t['pochissimo']['quota_residenti']}%)")
        c = d["cintura"]
        etichetta = "cintura" if d["cintura_comparabile"] else "cintura (NON comparabile)"
        righe.append(f"    {etichetta}: zero {c['zero']['residenti']:,} res / {c['zero']['sezioni']} sez "
                      f"({c['zero']['quota_residenti']}%)   pochissimo {c['pochissimo']['residenti']:,} res / "
                      f"{c['pochissimo']['sezioni']} sez ({c['pochissimo']['quota_residenti']}%)")
        if "nota_cintura" in d:
            righe.append(f"      -> {d['nota_cintura']}")
    righe += [
        "",
        "LIMITI: ORARIO PROGRAMMATO (nessun ritardo/capienza/domanda reale); "
        "il gruppo 'cibo' usa tutte le attivita' del catalogo senza distinguere categoria; "
        "cintura su scuole/salute/cibo non comparabile con Torino (fonte diversa); "
        "le soglie DM 1444/1968 non sono state applicate qui (sono standard di superficie per "
        "comune, non di raggiungibilita' a piedi per sezione): citate come riferimento nella "
        "scheda finale, non calcolate.",
    ]
    righe += righe_rapporto_v2(v2, controlli_v2)
    righe += righe_rapporto_v3(v3, controlli_v3)
    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(righe), encoding="utf-8")
    print(f"Scritto {RAPPORTO}")
    if any(e == "ERRORE" for e, _ in controlli_v3):
        sys.exit("ERRORE nei controlli della versione 3 (vedi il rapporto): i numeri v3 non vanno usati")


if __name__ == "__main__":
    main()
