#!/usr/bin/env python3
"""
84_risultato6_parcheggi.py  -  Risultato 6 corretto (20/10/2026): dove mancano posti per lasciare l'auto
PRIMA di entrare in citta'. Preparato da Claude, da lanciare sul PC. Prende il posto dello script 80 nella
catena (80 resta per confronto e per le sue funzioni, che qui si riusano: esagoni, profili, nomi).

Domanda
-------
Dove, vicino a una fermata importante (fuori dal centro), passano molte auto in entrata al mattino che
potrebbero lasciare l'auto, e non ci sono abbastanza posti adatti per farlo?

Regole (costanti qui sotto e opzioni da riga di comando; valori in sviluppo/note_tecniche/R6_parcheggi.md)
------
  - Fermate importanti: quelle dello script 83 (punteggio corretto, fuori da Q001-Q009).
  - Parcheggi: solo quelli ADATTI dello script 82 (aperti, fuori dal centro, >= 20 posti, non di destinazione).
  - Distanza a piedi = linea d'aria x 1,3; un parcheggio "serve" una fermata entro 400 m a piedi.
  - Auto da fermare a una fermata (potenziale) = auto in entrata che passano accanto (c4, script 81)
    x quota_mattino (quota di chi gia' oggi lascia l'auto per un mezzo pubblico, script 81).
  - Classe della fermata, nell'ordine:
      «Poche auto da fermare»  potenziale < MIN_AUTO_DA_FERMARE (20): non serve un interscambio;
      «Nessun parcheggio»      0 posti adatti entro 400 m a piedi;
      «Posti insufficienti»    posti < potenziale;
      «Posti sufficienti»      posti >= potenziale.
    Niente soglia fissa di posti (prima: 50): i posti si confrontano con le auto che passano.
  - Aree: esagoni (lato 900 m); quota senza = (nessun + insufficienti) / fermate valutate (senza «poche auto»);
    Critica >= 60%, Scarsa 30-59%, Buona < 30%; con meno di 5 fermate valutate: «Pochi dati».
  - Punti prioritari (fino a 20, almeno 50 posti mancanti): fermate «nessun» o «insufficienti» raggruppate entro 1 km; posti che mancano del gruppo =
    potenziale piu' alto del gruppo - posti adatti che servono il gruppo; in ordine di posti che mancano.
    Un punto per asse (Leo, 20/10 sera): si tiene il gruppo con piu' posti mancanti e si scartano quelli a meno di
    2 km o sulla stessa strada a meno di 5 km (sono in gran parte le stesse auto); niente punti a meno di 3 km da Piazza
    Castello (fermare li' un'auto fa risparmiare poca strada). I posti che mancano si mostrano arrotondati
    (ordine di grandezza: quota da poche interviste x stima del traffico).
    Candidati ad ampliarsi: parcheggi adatti >= 100 posti entro 600 m a piedi dal centro del punto.
  - Parcheggi in mappa: adatti con >= 100 posti entro 400 m (linea d'aria) da una fermata importante o da un
    nodo forte, piu' tutti gli interscambi ufficiali e i park&ride di OpenStreetMap.
  - Riempimento: solo misura 5T (media feriale 10-16, >= 2 giorni validi); colora i parcheggi, non le classi.
  - Validazione: i 5 interscambi ufficiali confrontati con le auto che passano accanto (sezione nel rapporto
    e nella scheda; solo fatti misurati). Le osservazioni di Leo solo come controllo a posteriori nel rapporto.
  - Direzioni d'ingresso (8 settori): solo riferimento, quota coerente (quota_mattino) e posti adatti.

Cosa legge
----------
  data/processed/risultato6_v2/fermate_importanti.json (83), parcheggi.json (69), parcheggi_adatti.json (82),
  riempimento.json (71), nodi.json (72), luoghi.json (68), auto_passaggio.json (81)
  data/processed/imq_zone.json, imq_zone_geo.json; data/ref/parcheggi_osservazioni.json (solo a posteriori)
  scripts/80_porte_interscambio.py (funzioni)

Cosa scrive
-----------
  data/processed/risultato6_v2/porte.json   (stesso nome di prima: lo legge lo script 79)
  docs/rapporti/RAPPORTO_R6_PARCHEGGI.txt

Come si lancia
--------------
  python scripts\\84_risultato6_parcheggi.py
  python scripts\\84_risultato6_parcheggi.py --raggio-piedi 400 --min-auto 20 --soglie-aree 60,30
"""
import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

m80 = comuni.carica_script("80_porte_interscambio.py")

RADICE = comuni.RADICE
P = RADICE / "data" / "processed" / "risultato6_v2"
IMPORTANTI = P / "fermate_importanti.json"
PARCHEGGI = P / "parcheggi.json"
ADATTI = P / "parcheggi_adatti.json"
RIEMPIMENTO = P / "riempimento.json"
NODI = P / "nodi.json"
LUOGHI = P / "luoghi.json"
PASSAGGIO = P / "auto_passaggio.json"
ZONE = RADICE / "data" / "processed" / "imq_zone.json"
ZONE_GEO = RADICE / "data" / "processed" / "imq_zone_geo.json"
OSSERVAZIONI = RADICE / "data" / "ref" / "parcheggi_osservazioni.json"
OUT = P / "porte.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6_PARCHEGGI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

FATTORE_PIEDI = comuni.FATTORE_PIEDI
RAGGIO_PIEDI_M = 400.0
RAGGIO_CANDIDATI_PIEDI_M = 600.0
MIN_AUTO_DA_FERMARE = 20
MIN_POSTI_MOSTRATO = 100
RAGGIO_MOSTRATO_M = 400.0          # linea d'aria, solo per scegliere cosa disegnare
SOGLIE_AREE = (60.0, 30.0)
MIN_FERMATE_AREA = 5
DIAMETRO_PUNTI_M = 1000.0
DIST_MIN_CENTRO_KM = 3.0           # niente punti prioritari piu' vicini a Piazza Castello
DIST_STESSO_ASSE_M = 2000.0        # due punti piu' vicini di cosi' contano in gran parte le stesse auto
DIST_STESSA_STRADA_M = 5000.0      # stessa strada e piu' vicini di cosi': stesso asse (il nome da solo non basta:
                                   # «strada Torino» c'e' in molti comuni)
N_PUNTI = 20                       # al massimo
MIN_MANCANO_PUNTO = 50             # sotto: non e' una priorita' (Claude, 20/10 sera: c'erano punti con 0-23 posti mancanti)
SOGLIA_PIENO, SOGLIA_LIBERO = 0.85, 0.50
MIN_GIORNI_VALIDI = 2
QUOTA_TOP_VALIDAZIONE = 0.20       # "strada con molte auto": nel 20% piu' alto dei luoghi eleggibili
CLASSI = ("Nessun parcheggio", "Posti insufficienti", "Posti sufficienti", "Poche auto da fermare")
CAT_AREA = ("Critica", "Scarsa", "Buona", "Pochi dati")
TIPO_TESTO = {"interscambio_ufficiale": "interscambio del Comune", "garage_5t": "garage (5T)",
              "park_ride_osm": "park & ride (OpenStreetMap)", "osm_pubblico": "parcheggio aperto (OpenStreetMap)"}


def posti_rec(p):
    if p.get("posti_dichiarati"):
        return int(p["posti_dichiarati"])
    return int(p.get("posti_stimati") or 0)


def classe_di(potenziale, posti, min_auto):
    if potenziale < min_auto:
        return CLASSI[3]
    if posti <= 0:
        return CLASSI[0]
    if posti < potenziale:
        return CLASSI[1]
    return CLASSI[2]


def categoria_area(quota, n_valutate, soglie, min_fermate):
    if n_valutate < min_fermate:
        return CAT_AREA[3]
    if quota >= soglie[0] / 100:
        return CAT_AREA[0]
    if quota >= soglie[1] / 100:
        return CAT_AREA[1]
    return CAT_AREA[2]


def arrotonda_cento(x):
    return int(round(x / 100.0) * 100)


def arrotonda_mancano(x):
    """Posti che mancano come ordine di grandezza: decine sotto 100, cinquantine sotto 1.000, centinaia sopra."""
    passo = 10 if x < 100 else 50 if x < 1000 else 100
    return int(round(x / passo) * passo)


def stesso_asse(p, q, dist_asse_m=DIST_STESSO_ASSE_M, dist_strada_m=DIST_STESSA_STRADA_M):
    d = comuni.haversine_m(p["centro"][0], p["centro"][1], q["centro"][0], q["centro"][1])
    return d < dist_asse_m or (bool(p.get("strada")) and p.get("strada") == q.get("strada") and d < dist_strada_m)


def un_punto_per_asse(punti, dist_min_km):
    """punti gia' in ordine di importanza -> tenuti, scartati. Si scarta un punto troppo vicino al centro, o sullo
    stesso asse di un punto gia' tenuto (vicino, o sulla stessa strada non lontano): le stesse auto che passano."""
    tenuti, scartati = [], []
    for p in punti:
        if p["dist_centro_km"] < dist_min_km:
            scartati.append((p, "vicino al centro"))
            continue
        simile = next((q for q in tenuti if stesso_asse(p, q)), None)
        if simile is not None:
            simile.setdefault("stesse_auto", []).append(p["nome"])
            scartati.append((p, f"stesso asse di {simile['nome']}"))
            continue
        tenuti.append(p)
    return tenuti, scartati


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raggio-piedi", type=float, default=RAGGIO_PIEDI_M)
    ap.add_argument("--min-auto", type=float, default=MIN_AUTO_DA_FERMARE)
    ap.add_argument("--soglie-aree", default="60,30")
    ap.add_argument("--min-fermate-area", type=int, default=MIN_FERMATE_AREA)
    args = ap.parse_args()
    soglie = tuple(float(x) for x in args.soglie_aree.split(","))
    raggio_aria = args.raggio_piedi / FATTORE_PIEDI
    cand_aria = RAGGIO_CANDIDATI_PIEDI_M / FATTORE_PIEDI
    c = comuni.Controlli()
    t0 = time.time()

    for f in (IMPORTANTI, PARCHEGGI, ADATTI, RIEMPIMENTO, NODI, LUOGHI, PASSAGGIO, ZONE, ZONE_GEO):
        c(f"esiste {f.name}", f.exists(), bloccante=True)
    imp = json.loads(IMPORTANTI.read_text(encoding="utf-8"))
    tutti = json.loads(PARCHEGGI.read_text(encoding="utf-8"))["parcheggi"]
    ad = json.loads(ADATTI.read_text(encoding="utf-8"))
    info_ad = {r["id"]: r for r in ad["parcheggi"]}
    riemp = json.loads(RIEMPIMENTO.read_text(encoding="utf-8"))
    riemp_5t = {r["id_5t"]: r for r in riemp["parcheggi"]}
    nodi_forti = [n for n in json.loads(NODI.read_text(encoding="utf-8"))["luoghi"] if n.get("nodo_forte")]
    luoghi_all = {l["id_luogo"]: l for l in json.loads(LUOGHI.read_text(encoding="utf-8"))["luoghi"]}
    pas = json.loads(PASSAGGIO.read_text(encoding="utf-8"))
    zone_info = {z["cod"]: z for z in json.loads(ZONE.read_text(encoding="utf-8"))}
    geo = json.loads(ZONE_GEO.read_text(encoding="utf-8"))
    quota = float(pas["quota_mattino"])
    c4_di = {i: (v or {}).get("c4", 0) for i, v in pas["luoghi"].items()}
    print(f"quota_mattino {quota:.1%}; c4 col metodo {pas.get('c4_metodo')}")

    def zona_nome(cod):
        return m80.nome_normale(zone_info.get(cod, {}).get("denom", "")) if cod else ""

    # ---- parcheggi adatti ----
    adatti = [p for p in tutti if info_ad.get(p["id"], {}).get("adatto")]
    posti = np.array([posti_rec(p) for p in adatti], dtype=float)
    print(f"parcheggi adatti {len(adatti)} ({int(posti.sum()):,} posti)")
    c("ci sono parcheggi adatti", len(adatti) > 0, bloccante=True)

    def stato_di(p):
        r = riemp_5t.get(p.get("id_5t")) if p.get("id_5t") else None
        if r and r.get("G_giorno_feriale") is not None and len(r.get("giorni_validi", [])) >= MIN_GIORNI_VALIDI:
            g = float(r["G_giorno_feriale"])
            return ("pieno" if g >= SOGLIA_PIENO else "libero" if g < SOGLIA_LIBERO else "a_meta"), round(g, 4)
        return "non_misurato", None

    # ---- fermate importanti e classi ----
    fermate_in = imp["importanti"]
    c("ci sono fermate importanti", len(fermate_in) > 0, bloccante=True)
    D = m80.dist_matrix(adatti, fermate_in)                    # parcheggi x fermate, metri in linea d'aria

    def classi(fermate_l, raggio_a=raggio_aria, quota_v=quota, posti_v=posti, Dm=None):
        Dm = m80.dist_matrix(adatti, fermate_l) if Dm is None else Dm
        pn = (Dm <= raggio_a).T @ posti_v
        out = []
        for j, f in enumerate(fermate_l):
            pot = c4_di.get(f["id_luogo"], 0) * quota_v
            out.append((classe_di(pot, pn[j], args.min_auto), float(pn[j]), pot))
        return out

    base = classi(fermate_in, Dm=D)
    fermate = []
    for j, f in enumerate(fermate_in):
        cl, pn, pot = base[j]
        sel = np.nonzero(D[:, j] <= raggio_aria)[0]
        vic = sorted(((adatti[i], float(D[i, j])) for i in sel), key=lambda x: x[1])
        fermate.append({
            "id": f["id_luogo"], "nome": f["nome"], "lat": round(f["lat"], 5), "lon": round(f["lon"], 5),
            "zona": f["zona_imq"], "zona_nome": zona_nome(f["zona_imq"]), "posizione": f["posizione"],
            "punteggio": f["punteggio"], "strada": f.get("strada"),
            "auto_passaggio": int(c4_di.get(f["id_luogo"], 0)),
            "auto_passaggio_txt": arrotonda_cento(c4_di.get(f["id_luogo"], 0)),
            "potenziale": int(round(pot)), "posti_adatti": int(pn), "mancano": int(max(0, round(pot - pn)))
            if cl in CLASSI[:2] else 0,
            "classe": cl,
            "parcheggi": [{"id": p["id"], "nome": p["nome"], "dist_piedi_m": round(d * FATTORE_PIEDI),
                           "posti": posti_rec(p), "stato": stato_di(p)[0]} for p, d in vic[:6]],
            "_j": j,
        })
    conta = Counter(f["classe"] for f in fermate)
    print("  classi:", dict(conta))

    # ---- aree esagonali ----
    xy = [m80.proietta(f["lat"], f["lon"]) for f in fermate]
    gruppi = {}
    for k, (x, y) in enumerate(xy):
        gruppi.setdefault(m80.cella_di(x, y), []).append(k)
    aree = []
    for (q, r), membri in gruppi.items():
        val = [k for k in membri if fermate[k]["classe"] != CLASSI[3]]
        nes = sum(1 for k in val if fermate[k]["classe"] == CLASSI[0])
        ins = sum(1 for k in val if fermate[k]["classe"] == CLASSI[1])
        quota_s = (nes + ins) / len(val) if val else 0.0
        park = sorted(set(np.nonzero((D[:, [fermate[k]["_j"] for k in membri]] <= raggio_aria).any(axis=1))[0].tolist()))
        pieni = sorted([{"nome": adatti[i]["nome"], "posti": int(posti[i])} for i in park if stato_di(adatti[i])[0] == "pieno"],
                       key=lambda x: -x["posti"])
        zn = Counter(fermate[k]["zona_nome"] for k in membri if fermate[k]["zona_nome"]).most_common(2)
        clat, clon = m80.inverti(*m80.centro_cella(q, r))
        cat = categoria_area(quota_s, len(val), soglie, args.min_fermate_area)
        senza = sorted([fermate[k] for k in val if fermate[k]["classe"] in CLASSI[:2]], key=lambda f: -f["mancano"])[:5]
        aree.append({
            "id": f"c{q}_{r}", "centro": [round(clat, 5), round(clon, 5)], "poligono": m80.vertici_cella(q, r),
            "n_fermate": len(membri), "n_valutate": len(val), "nessun": nes, "insufficienti": ins,
            "sufficienti": len(val) - nes - ins, "poche_auto": len(membri) - len(val),
            "quota_senza": round(quota_s, 3), "categoria": cat, "pochi_dati": cat == CAT_AREA[3],
            "zone_principali": [z for z, _ in zn], "posti_adatti": int(sum(posti[i] for i in park)),
            "parcheggi_pieni": pieni,
            "fermate_senza": [{"nome": m80.nome_fermata(f["nome"]), "mancano": f["mancano"]} for f in senza],
        })
    aree.sort(key=lambda a: (a["pochi_dati"], -a["quota_senza"], -a["n_fermate"]))
    migliore = {}
    for a in aree:
        a["etichetta"] = a["zone_principali"][0] if a["zone_principali"] else None
        if not a["etichetta"] or a["pochi_dati"]:
            continue
        cur = migliore.get(a["etichetta"])
        if cur is None or (a["n_fermate"], a["centro"][0]) > (cur["n_fermate"], cur["centro"][0]):
            migliore[a["etichetta"]] = a
    for a in aree:
        a["mostra_etichetta"] = bool(a["etichetta"]) and migliore.get(a["etichetta"]) is a
    cat_aree = Counter(a["categoria"] for a in aree)
    print("  aree:", dict(cat_aree))
    c("ogni fermata in una sola area", sum(a["n_fermate"] for a in aree) == len(fermate), bloccante=True)

    # ---- 20 punti ----
    from scipy.cluster.hierarchy import fcluster, linkage
    idx = [k for k, f in enumerate(fermate) if f["classe"] in CLASSI[:2]]
    punti = []
    if idx:
        pts = np.array([xy[k] for k in idx])
        lab = fcluster(linkage(pts, method="complete"), DIAMETRO_PUNTI_M, "distance") if len(idx) >= 2 else np.ones(1, int)
        gr = {}
        for k, g in zip(idx, lab):
            gr.setdefault(int(g), []).append(k)
        for membri in gr.values():
            cols = [fermate[k]["_j"] for k in membri]
            serv = np.nonzero((D[:, cols] <= raggio_aria).any(axis=1))[0]
            posti_g = int(sum(posti[i] for i in serv))
            pot_g = max(fermate[k]["potenziale"] for k in membri)
            capo = max(membri, key=lambda k: (fermate[k]["potenziale"], fermate[k]["punteggio"], fermate[k]["id"]))   # spareggio fisso
            cx_ = float(np.mean([xy[k][0] for k in membri]))
            cy_ = float(np.mean([xy[k][1] for k in membri]))
            clat, clon = m80.inverti(cx_, cy_)
            dc = m80.haversine_vettore(clat, clon, np.array([p["lat"] for p in adatti]), np.array([p["lon"] for p in adatti]))
            cand = sorted([i for i in np.nonzero((dc <= cand_aria) & (posti >= MIN_POSTI_MOSTRATO))[0]], key=lambda i: dc[i])
            punti.append({
                "nome": m80.nome_fermata(fermate[capo]["nome"]), "zona_nome": fermate[capo]["zona_nome"],
                "centro": [round(clat, 5), round(clon, 5)], "n_fermate": len(membri),
                "nessun": sum(1 for k in membri if fermate[k]["classe"] == CLASSI[0]),
                "insufficienti": sum(1 for k in membri if fermate[k]["classe"] == CLASSI[1]),
                "auto_passaggio": max(fermate[k]["auto_passaggio"] for k in membri),
                "auto_passaggio_txt": arrotonda_cento(max(fermate[k]["auto_passaggio"] for k in membri)),
                "potenziale": int(pot_g), "posti_adatti": posti_g, "mancano": int(max(0, pot_g - posti_g)),
                "dist_centro_km": round(comuni.haversine_m(clat, clon, comuni.CENTRO_LAT, comuni.CENTRO_LON) / 1000, 1),
                "strada": fermate[capo].get("strada"),
                "candidati": [{"nome": adatti[i]["nome"], "dist_piedi_m": round(float(dc[i]) * FATTORE_PIEDI),
                               "posti": int(posti[i]), "stato": stato_di(adatti[i])[0],
                               "gia_pieno": stato_di(adatti[i])[0] == "pieno"} for i in cand[:8]],
                "fermate": [{"nome": m80.nome_fermata(fermate[k]["nome"]), "classe": fermate[k]["classe"],
                             "mancano": fermate[k]["mancano"]} for k in sorted(membri, key=lambda k: -fermate[k]["mancano"])],
                "_somma_punteggio": sum(fermate[k]["punteggio"] for k in membri),
            })
    punti.sort(key=lambda p: (-p["mancano"], -p["_somma_punteggio"], p["centro"]))   # spareggio fisso
    n_gruppi = len(punti)
    punti, scartati = un_punto_per_asse(punti, DIST_MIN_CENTRO_KM)
    pochi = [p for p in punti if p["mancano"] < MIN_MANCANO_PUNTO]
    punti = [p for p in punti if p["mancano"] >= MIN_MANCANO_PUNTO]
    scartati_in_cima = [(p, motivo) for p, motivo in scartati if p["mancano"] >= (punti[N_PUNTI - 1]["mancano"] if len(punti) >= N_PUNTI else 0)]
    punti = punti[:N_PUNTI]
    for k, p in enumerate(punti):
        p["ordine"] = k + 1
        p.pop("_somma_punteggio")
        p["mancano_stima"] = p["mancano"]
        p["mancano"] = arrotonda_mancano(p["mancano"])
        for f in p["fermate"]:
            f["mancano"] = arrotonda_mancano(f["mancano"])
    for a in aree:
        for f in a["fermate_senza"]:
            f["mancano"] = arrotonda_mancano(f["mancano"])
    print(f"  punti prioritari: {len(punti)} (gruppi {n_gruppi}; con meno di {MIN_MANCANO_PUNTO} posti mancanti: {len(pochi)}; scartati perche' stesso asse o vicini al centro: "
          f"{len(scartati)}, di cui {len(scartati_in_cima)} con piu' posti mancanti dell'ultimo tenuto)")

    # ---- parcheggi in mappa ----
    tutti_aperti = [p for p in tutti if p["tipo"] in TIPO_TESTO]
    da_mostrare = []
    D_f_all = m80.dist_matrix(tutti_aperti, fermate_in)
    D_n_all = m80.dist_matrix(tutti_aperti, nodi_forti) if nodi_forti else np.full((len(tutti_aperti), 1), np.inf)
    for i, p in enumerate(tutti_aperti):
        r_ad = info_ad.get(p["id"], {})
        ufficiale = p["tipo"] in ("interscambio_ufficiale", "park_ride_osm")
        grande_vicino = r_ad.get("adatto") and posti_rec(p) >= MIN_POSTI_MOSTRATO and \
            (D_f_all[i].min() <= RAGGIO_MOSTRATO_M or D_n_all[i].min() <= RAGGIO_MOSTRATO_M)
        in_centro = info_ad.get(p["id"], {}).get("zona_imq") in comuni.ZONE_CENTRALI and \
            (posti_rec(p) >= MIN_POSTI_MOSTRATO or p["tipo"] == "garage_5t")
        if not (ufficiale or grande_vicino or in_centro):
            continue
        st, g = stato_di(p)
        r5 = riemp_5t.get(p.get("id_5t")) if p.get("id_5t") else None
        pf = m80._profilo(r5.get("profilo_feriale")) if r5 else None
        pw = m80._profilo(r5.get("profilo_weekend")) if r5 else None
        descr = m80.descrivi_profilo(pf, pw)[1] if pf else None
        vic_n = [nodi_forti[j] for j in np.nonzero(D_n_all[i] <= RAGGIO_MOSTRATO_M)[0]] if nodi_forti else []
        nodo = ("metro" if any(n.get("metro") for n in vic_n) else "treno" if any(n.get("ferro") for n in vic_n)
                else "capolinea" if any(n.get("capolinea") for n in vic_n) else "frequente" if vic_n else "nessuno")
        da_mostrare.append({
            "id": p["id"], "nome": p["nome"], "lat": round(p["lat"], 5), "lon": round(p["lon"], 5),
            "tipo": p["tipo"], "tipo_testo": TIPO_TESTO[p["tipo"]], "adatto": bool(r_ad.get("adatto")),
            "motivo_non_adatto": None if r_ad.get("adatto") else r_ad.get("motivo"),
            "posti": posti_rec(p),
            "posti_origine": "dichiarati" if p.get("posti_dichiarati") else
            ("stimati (25 m² a posto, ±30%)" if p.get("posti_stimati") else "nessuno"),
            "a_pagamento": p.get("a_pagamento"), "stato": st, "riempimento_giorno": g,
            "dist_fermata_importante_piedi_m": round(float(D_f_all[i].min()) * FATTORE_PIEDI),
            "nodo_vicino": nodo, "profilo_feriale": pf, "profilo_weekend": pw, "descrizione": descr,
            "auto_passaggio_txt": arrotonda_cento((pas.get("parcheggi", {}).get(p["id"]) or {}).get("c4", 0)),
            "in_centro": bool(in_centro),
        })
    da_mostrare.sort(key=lambda x: -x["posti"])
    print(f"  parcheggi in mappa: {len(da_mostrare)}")

    # ---- profili (parcheggi in mappa con dati 5T) ----
    profili = []
    for p in da_mostrare:
        if not p["profilo_feriale"]:
            continue
        regola, testo = m80.descrivi_profilo(p["profilo_feriale"], p["profilo_weekend"])
        r5 = riemp_5t.get(next((x.get("id_5t") for x in tutti if x["id"] == p["id"]), None)) or {}
        profili.append({"nome": p["nome"], "posti": p["posti"], "tipo": p["tipo"], "regola": regola,
                        "descrizione": testo, "giorni_validi": len(r5.get("giorni_validi", [])),
                        "profilo_feriale": p["profilo_feriale"], "profilo_weekend": p["profilo_weekend"]})

    # ---- validazione sugli interscambi ufficiali ----
    eleggibili_c4 = sorted([c4_di.get(i, 0) for i, l in luoghi_all.items()
                            if l.get("zona_imq") and l["zona_imq"] not in comuni.ZONE_CENTRALI
                            and zone_info.get(l["zona_imq"], {}).get("macro") in comuni.MACRO_UNIVERSO], reverse=True)
    soglia_molte = eleggibili_c4[int(len(eleggibili_c4) * QUOTA_TOP_VALIDAZIONE)] if eleggibili_c4 else 0
    validazione = []
    for p in [x for x in tutti if x["tipo"] == "interscambio_ufficiale"]:
        r5 = riemp_5t.get(p.get("id_5t")) if p.get("id_5t") else None
        st, g = stato_di(p)
        c4v = (pas.get("parcheggi", {}).get(p["id"]) or {}).get("c4", 0)   # strada piu' trafficata entro 300 m
        molte = c4v >= soglia_molte
        pf = m80._profilo(r5.get("profilo_feriale")) if r5 else None
        regola = m80.descrivi_profilo(pf, m80._profilo(r5.get("profilo_weekend")))[0] if pf else None
        if st == "non_misurato":
            esito = "non si può dire: non trasmette il riempimento"
        elif regola in ("fermo",):
            esito = "non si può dire: il contatore sembra fermo"
        elif st == "pieno":
            esito = "coerente: pieno, su una strada con molte auto in entrata" if molte else \
                "non coerente: pieno, ma accanto passano poche auto in entrata (forse lo usano i residenti o chi arriva da altre strade)"
        elif st == "libero":
            esito = "da capire: accanto passano molte auto in entrata ma è poco usato (prezzo? posizione? collegamento?)" if molte else \
                "coerente: poco usato, e accanto passano poche auto in entrata"
        else:
            esito = "non si può dire: riempimento a metà"
        x, y = m80.proietta(p["lat"], p["lon"])
        cella = m80.cella_di(x, y)
        area = next((a for a in aree if a["id"] == f"c{cella[0]}_{cella[1]}"), None)
        d_imp = m80.haversine_vettore(p["lat"], p["lon"], np.array([f["lat"] for f in fermate_in]),
                                      np.array([f["lon"] for f in fermate_in]))
        validazione.append({
            "nome": p["nome"], "posti": posti_rec(p), "adatto": bool(info_ad.get(p["id"], {}).get("adatto")),
            "stato": st, "G_giorno": g,
            "N_notte": r5.get("N_notte_feriale") if r5 else None, "M_mattina": r5.get("M_mattina_feriale") if r5 else None,
            "descrizione": m80.descrivi_profilo(pf, m80._profilo(r5.get("profilo_weekend")))[1] if pf else "non trasmette",
            "auto_passaggio_txt": arrotonda_cento(c4v), "molte_auto": bool(molte),
            "dist_fermata_importante_piedi_m": round(float(d_imp.min()) * FATTORE_PIEDI) if len(d_imp) else None,
            "area": area["categoria"] if area else "fuori dalle aree", "esito": esito,
        })
    c("trovati i 5 interscambi ufficiali", len(validazione) == 5, dettaglio=f"{len(validazione)}")

    # ---- osservazioni di Leo: SOLO controllo a posteriori (non entra nei dati pubblici) ----
    a_posteriori = []
    if OSSERVAZIONI.exists():
        for o in json.loads(OSSERVAZIONI.read_text(encoding="utf-8")).get("osservazioni", []):
            dd = m80.haversine_vettore(o["lat"], o["lon"], np.array([p["lat"] for p in adatti]), np.array([p["lon"] for p in adatti]))
            dentro = np.nonzero(dd <= o["raggio_m"])[0]
            gratis = [i for i in dentro if adatti[i].get("a_pagamento") is False]
            misurati = [i for i in dentro if stato_di(adatti[i])[0] != "non_misurato"]
            if not misurati:
                esito = "non può confermare: nessun parcheggio adatto nel raggio trasmette il riempimento"
            else:
                pieni = [i for i in misurati if stato_di(adatti[i])[0] == "pieno"]
                esito = ("conferma" if len(pieni) == len(misurati) else "non conferma" if not pieni else "conferma in parte")
            a_posteriori.append({"nome": o.get("nome_per_leggere", o.get("id")), "nota": o.get("nota") or o.get("testo"),
                                 "raggio_m": o["raggio_m"], "adatti_nel_raggio": int(len(dentro)),
                                 "posti_adatti": int(sum(posti[i] for i in dentro)),
                                 "gratuiti": len(gratis), "posti_gratuiti": int(sum(posti[i] for i in gratis)),
                                 "esito": esito})

    # ---- direzioni d'ingresso (solo riferimento) ----
    centroidi = {}
    for g in geo:
        pts_ = [q for an in m80._anelli_geo(g["g"]) for q in an]
        if pts_:
            centroidi[g["cod"]] = (sum(q[0] for q in pts_) / len(pts_), sum(q[1] for q in pts_) / len(pts_))
    zona_or = pas.get("auto_per_zona_origine", {})
    direzioni = []
    for k in range(8):
        zk = sorted([(z, v["auto"]) for z, v in zona_or.items() if z in centroidi and m80.settore_di(*centroidi[z]) == k],
                    key=lambda t: -t[1])
        auto_k = sum(v for _, v in zk)
        dom = auto_k * quota
        posti_k = float(sum(posti[i] for i, p in enumerate(adatti) if m80.settore_di(p["lat"], p["lon"]) == k))
        cop = posti_k / dom if dom > 0 else None
        direzioni.append({"codice": k, "nome": m80.SETTORI_NOMI[k], "comuni_principali": [zona_nome(z) for z, _ in zk[:3]],
                          "auto_in_entrata": round(auto_k), "domanda": round(dom), "posti_adatti": int(posti_k),
                          "copertura": round(cop, 3) if cop is not None else None, "categoria": m80.categoria_dir(cop)})

    # ---- sensibilita' ----
    print("sensibilita'...")

    def conta_cl(lst):
        cc = Counter(x[0] for x in lst)
        return {"nessun": cc[CLASSI[0]], "insufficienti": cc[CLASSI[1]], "sufficienti": cc[CLASSI[2]], "poche_auto": cc[CLASSI[3]]}

    sens = {"raggio_piedi": {}, "quota": {}, "regola_50_posti": {}, "senza_filtro_destinazioni": {},
            "senza_soglia_posti": {}, "soglia_fermate": {}, "soglie_aree": {}}
    for rp in (300.0, 400.0, 500.0):
        sens["raggio_piedi"][str(int(rp))] = conta_cl(classi(fermate_in, raggio_a=rp / FATTORE_PIEDI, Dm=D))
    for fq in (0.5, 1.0, 2.0):
        sens["quota"][f"x{fq:g}"] = conta_cl(classi(fermate_in, quota_v=quota * fq, Dm=D))
    pn_base = np.array([x[1] for x in base])
    sens["regola_50_posti"] = {"senza_50_posti": int(np.sum(pn_base < 50)), "con_50_posti": int(np.sum(pn_base >= 50))}
    for chiave, motivi in (("senza_filtro_destinazioni", ("destinazione_",)), ("senza_soglia_posti", ("pochi_posti",))):
        extra = [p for p in tutti if any((info_ad.get(p["id"], {}).get("motivo") or "").startswith(m) for m in motivi)]
        if extra:
            p_ext = np.concatenate([posti, np.array([posti_rec(p) for p in extra], dtype=float)])
            D_ext = np.vstack([D, m80.dist_matrix(extra, fermate_in)])
            pn = (D_ext <= raggio_aria).T @ p_ext
            sens[chiave] = conta_cl([(classe_di(c4_di.get(f["id_luogo"], 0) * quota, pn[j], args.min_auto),) for j, f in enumerate(fermate_in)])
        else:
            sens[chiave] = conta_cl(base)
    for pc, ids in imp.get("alternative", {}).items():
        lst = [{"id_luogo": i, "lat": luoghi_all[i]["lat"], "lon": luoghi_all[i]["lon"]} for i in ids if i in luoghi_all]
        sens["soglia_fermate"][pc] = {"fermate": len(lst), **(conta_cl(classi(lst)) if lst else {})}
    for s_alt in ((50, 25), (66, 33)):
        cc = Counter(categoria_area(a["quota_senza"], a["n_valutate"], s_alt, args.min_fermate_area) for a in aree)
        sens["soglie_aree"][f"{s_alt[0]}/{s_alt[1]}"] = {k: cc.get(k, 0) for k in CAT_AREA}

    # ---- controlli ----
    c("nessuna fermata importante in zona centrale", not any(f["zona"] in comuni.ZONE_CENTRALI for f in fermate), bloccante=True)
    c(f"nessun punto prioritario a meno di {DIST_MIN_CENTRO_KM:g} km dal centro",
      not any(p["dist_centro_km"] < DIST_MIN_CENTRO_KM for p in punti), bloccante=True)
    c("un punto per asse: nessuna coppia di punti sullo stesso asse",
      not any(stesso_asse(p, q) for i, p in enumerate(punti) for q in punti[i + 1:]), bloccante=True)
    c("nessun parcheggio adatto in zona centrale", not any(info_ad[p["id"]]["zona_imq"] in comuni.ZONE_CENTRALI for p in adatti),
      bloccante=True)
    c("nessun valore negativo", all(f["mancano"] >= 0 and f["posti_adatti"] >= 0 for f in fermate), bloccante=True)
    c("somma auto delle direzioni = auto in entrata con zona nota",
      abs(sum(d["auto_in_entrata"] for d in direzioni) - sum(v["auto"] for z, v in zona_or.items() if z in centroidi)) <= 8)
    c(f"punti prioritari: da 1 a {N_PUNTI}", 1 <= len(punti) <= N_PUNTI, dettaglio=f"{len(punti)}")
    c("almeno un'area con categoria (non «Pochi dati»)", any(not a["pochi_dati"] for a in aree))

    # ---- riepilogo, criteri, affidabilita' ----
    giorni = sorted({d for r in riemp["parcheggi"] for d in r.get("giorni_validi", [])
                     if datetime.strptime(d, "%Y-%m-%d").weekday() < 5})
    misurati = [p for p in da_mostrare if p["stato"] != "non_misurato"]
    posti_mostrati = sum(p["posti"] for p in da_mostrare) or 1
    catena = ad["catena"]
    n_imp = len(fermate)
    senza = conta[CLASSI[0]] + conta[CLASSI[1]]
    riepilogo = {
        "fermate_importanti": n_imp, "fermate_nessun_parcheggio": conta[CLASSI[0]],
        "fermate_insufficienti": conta[CLASSI[1]], "fermate_sufficienti": conta[CLASSI[2]],
        "fermate_poche_auto": conta[CLASSI[3]], "fermate_senza_posti_bastanti": senza,
        "aree_per_categoria": {k: cat_aree.get(k, 0) for k in CAT_AREA}, "n_aree": len(aree),
        "parcheggi_catena": catena, "posti_adatti": int(posti.sum()),
        "parcheggi_mostrati": len(da_mostrare), "quota_posti_misurati": round(100 * sum(p["posti"] for p in misurati) / posti_mostrati, 1),
        "giorni_feriali_validi": giorni,
        "quota_mattino": round(quota, 4), "quota_dati_scarsi": pas.get("quota_dati_scarsi"),
        "M_cint": pas["M_cint"], "M_tor": pas["M_tor"], "torinesi": pas["torinesi"], "f_mattino": pas["f_mattino"],
        "c4_metodo": pas.get("c4_metodo"), "n_eleggibili": imp["n_eleggibili"], "regola_fermate": imp["parametri"]["regola"],
        "mancano_totale_20_punti": int(sum(p["mancano_stima"] for p in punti)),
        "riferimento_direzioni": direzioni, "validazione": validazione,
        "profili_ufficiali": [p for p in profili if p["tipo"] == "interscambio_ufficiale"],
    }
    affidabilita = [
        {"voce": "Parcheggi trovati nei dati aperti", "valore": m80.it(catena["trovati"])},
        {"voce": "Aperti → fuori dal centro → con almeno 20 posti → adatti (non di destinazione)",
         "valore": f"{m80.it(catena['aperti'])} → {m80.it(catena['fuori_centro'])} → {m80.it(catena['con_almeno_posti_minimi'])} → {m80.it(catena['adatti'])}"},
        {"voce": "Posti nei parcheggi adatti (dichiarati o stimati a 25 m² a posto)", "valore": m80.it(int(posti.sum()))},
        {"voce": "Auto che entrano a Torino al mattino (solo conducenti)", "valore": f"{m80.it(pas['M_cint'])} (IMQ 2022, {pas['M_cint_interviste']} interviste)"},
        {"voce": "Quota di chi già oggi lascia l'auto per un mezzo pubblico", "valore": f"{m80.it(quota * 100, 1)}% ({pas['f_mattino_interviste']} interviste{', DATI SCARSI' if pas.get('quota_dati_scarsi') else ''})"},
        {"voce": "Auto che passano accanto alle fermate", "valore": "modello del traffico (percorso più veloce, senza code): solo ordine di grandezza"
         if pas.get("c4_metodo") == "instradamento" else "ripiego: auto che partono dalla zona della fermata"},
        {"voce": "Quota di posti in mappa con riempimento misurato", "valore": f"{m80.it(riepilogo['quota_posti_misurati'], 1)}%"},
        {"voce": "Giorni feriali di riempimento", "valore": ", ".join(d[8:10] + "/" + d[5:7] for d in giorni) or "nessuno"},
        {"voce": "Non sappiamo", "valore": "se i parcheggi senza misura (es. Fermi e i gratuiti) sono pieni; i parcheggi che non sono in OpenStreetMap; i treni"},
    ]
    sr = sens["raggio_piedi"]
    sq = sens["quota"]
    regola = imp["parametri"]["regola"]        # N e M dallo script 83 (None solo con la vecchia regola a percentuale)
    varianti_regola = {k: {"n": int(k.split("_")[0][1:]), "m": int(k.split("_")[1][1:])} for k in imp.get("alternative", {})}
    criteri = [
        {"nome": "Fermate importanti",
         "valore": f"fuori dal centro, con metro, stazione o capolinea oppure almeno {regola['n_corse']} corse all'ora nelle ore dei pendolari, "
                   f"e almeno {m80.it(regola['m_auto'])} auto in entrata che passano accanto ({n_imp} fermate)",
         "perche": "un parcheggio per lasciare l'auto serve dove passa un mezzo frequente e passano molte auto in entrata",
         "effetto": "; ".join(f"con N {v['n']}, M {m80.it(v['m'])}: {sens['soglia_fermate'].get(k, {}).get('fermate', 'n.d.')} fermate"
                              for k, v in varianti_regola.items())},
        {"nome": "Centro escluso", "valore": "quartieri Q001-Q009 (Centro, San Salvario, Crocetta, San Paolo, Cenisia, San Donato, Aurora, Vanchiglia, Nizza Millefonti)",
         "perche": "un parcheggio per lasciare l'auto serve prima di entrare nella città densa, non a due passi dalla destinazione",
         "effetto": "vale sia per le fermate sia per i parcheggi"},
        {"nome": "Parcheggi contati", "valore": f"solo quelli adatti: aperti, fuori dal centro, almeno 20 posti, non di ospedali, università o centri commerciali ({m80.it(catena['adatti'])})",
         "perche": "i posti di chi arriva a destinazione non servono a chi vuole lasciare l'auto prima",
         "effetto": f"contando anche i parcheggi di destinazione: {sens['senza_filtro_destinazioni']['nessun'] + sens['senza_filtro_destinazioni']['insufficienti']} fermate senza posti bastanti (invece di {senza})"},
        {"nome": "Distanza", "valore": f"{args.raggio_piedi:g} m a piedi (linea d'aria × {FATTORE_PIEDI:g})",
         "perche": "chi lascia l'auto accetta di solito una camminata di qualche minuto",
         "effetto": f"a 300 m: {sr['300']['nessun'] + sr['300']['insufficienti']} fermate senza posti bastanti; a 500 m: {sr['500']['nessun'] + sr['500']['insufficienti']} (a {args.raggio_piedi:g} m: {senza})"},
        {"nome": "Auto da fermare", "valore": f"auto in entrata che passano accanto × {m80.it(quota * 100, 1)}% (chi già oggi lascia l'auto per un mezzo pubblico)",
         "perche": "i posti servono se ci sono auto da fermare: niente soglia fissa di posti",
         "effetto": f"con metà quota: {sq['x0.5']['nessun'] + sq['x0.5']['insufficienti']} fermate senza posti bastanti; con quota doppia: {sq['x2']['nessun'] + sq['x2']['insufficienti']}"},
        {"nome": "Poche auto da fermare", "valore": f"meno di {args.min_auto:g} auto da fermare al mattino",
         "perche": "lì un parcheggio per lasciare l'auto non serve", "effetto": f"{conta[CLASSI[3]]} fermate importanti in questa classe"},
        {"nome": "Aree", "valore": f"celle di circa 2 km²; Critica ≥ {soglie[0]:g}%, Scarsa {soglie[1]:g}-{soglie[0] - 1:g}%, Buona < {soglie[1]:g}%; almeno {args.min_fermate_area} fermate, se no «Pochi dati»",
         "perche": "con una o due fermate la percentuale è 0% o 100% per caso",
         "effetto": "; ".join(f"soglie {k}: " + ", ".join(f"{a} {b}" for a, b in v.items()) for k, v in sens["soglie_aree"].items())},
        {"nome": "Punti prioritari", "valore": f"fino a {N_PUNTI}: fermate senza posti bastanti raggruppate entro 1 km, in ordine di posti che mancano (almeno {MIN_MANCANO_PUNTO}); uno per asse d'ingresso (niente punti a meno di {DIST_STESSO_ASSE_M / 1000:g} km, né sulla stessa strada a meno di {DIST_STESSA_STRADA_M / 1000:g} km); almeno {DIST_MIN_CENTRO_KM:g} km da Piazza Castello",
         "perche": "risponde a «dove metterne uno o ingrandirlo»; due punti sullo stesso asse contano le stesse auto; vicino al centro si risparmia poca strada",
         "effetto": f"candidati: parcheggi adatti con almeno 100 posti entro 600 m a piedi; scartati {len(scartati)} gruppi su {n_gruppi}"},
        {"nome": "Riempimento", "valore": f"misurato dal 5T dove c'è ({len(giorni)} giorni feriali, ore 10-16); pieno ≥ 85%",
         "perche": "un parcheggio pieno non serve", "effetto": "colora i parcheggi e mostra i profili; non cambia le classi delle fermate"},
    ]

    for f in fermate:
        f.pop("_j")
    dati = {"generato": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "parametri": {"raggio_piedi_m": args.raggio_piedi, "fattore_piedi": FATTORE_PIEDI, "min_auto": args.min_auto,
                          "soglie_aree": list(soglie), "min_fermate_area": args.min_fermate_area,
                          "quota_mattino": quota, "zone_centrali": list(comuni.ZONE_CENTRALI)},
            "soglia_aree": list(soglie), "classi": list(CLASSI),
            "fonti": [str(x.relative_to(RADICE)).replace("\\", "/") for x in (IMPORTANTI, ADATTI, PASSAGGIO, PARCHEGGI, RIEMPIMENTO)],
            "aree": aree, "punti_prioritari": punti, "fermate": fermate, "parcheggi": da_mostrare,
            "profili": profili, "sensibilita": sens, "criteri": criteri, "riepilogo": riepilogo,
            "affidabilita": affidabilita, "a_posteriori": a_posteriori, "controlli": c.righe}
    OUT.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")

    # ---- rapporto ----
    rr = ["RAPPORTO R6 - PARCHEGGI PER LASCIARE L'AUTO PRIMA DI ENTRARE IN CITTA' (script 84)",
          f"Generato il {dati['generato']}.", "",
          "== Fermate importanti ==",
          f"  {n_imp} fermate (fuori da Q001-Q009): nessun parcheggio {conta[CLASSI[0]]}, posti insufficienti {conta[CLASSI[1]]}, "
          f"posti sufficienti {conta[CLASSI[2]]}, poche auto da fermare {conta[CLASSI[3]]}",
          f"  quota_mattino {quota:.1%}; auto da fermare = auto che passano x quota; raggio {args.raggio_piedi:g} m a piedi", "",
          "== Aree ==", f"  {dict(cat_aree)}",
          *(f"  {a['id']:12s} {a['categoria']:10s} fermate {a['n_fermate']:3d} (valutate {a['n_valutate']}) "
            f"senza {a['quota_senza']:.0%}  {', '.join(a['zone_principali'])}" for a in aree), "",
          f"== Punti prioritari ({len(punti)}; al massimo {N_PUNTI}, con almeno {MIN_MANCANO_PUNTO} posti mancanti) ==",
          *(f"  {p['ordine']:2d}. {p['nome'][:30]:30s} {p['zona_nome'][:22]:22s} {p['dist_centro_km']:5.1f} km dal centro; "
            f"auto che passano ~{p['auto_passaggio_txt']}; da fermare {p['potenziale']}; posti {p['posti_adatti']}; "
            f"mancano circa {p['mancano']} (calcolo {p['mancano_stima']})"
            + (f"; stesso asse: {', '.join(p['stesse_auto'])}" if p.get("stesse_auto") else "")
            for p in punti),
          f"  Scartati {len(scartati)} gruppi su {n_gruppi} (stesso asse di un punto tenuto o a meno di {DIST_MIN_CENTRO_KM:g} km dal centro);",
          "  quelli con piu' posti mancanti dell'ultimo punto tenuto:",
          *(f"    {p['nome'][:30]:30s} mancano {p['mancano']}: {motivo}" for p, motivo in scartati_in_cima), "",
          "== Validazione sugli interscambi del Comune (solo fatti misurati) ==",
          "  Cosa ci si aspetta, PRIMA di guardare: un interscambio pieno dovrebbe stare su una strada con molte auto in entrata",
          f"  (nel {QUOTA_TOP_VALIDAZIONE:.0%} piu' alto dei luoghi, cioe' almeno {soglia_molte} auto); uno vuoto, su una strada con poche.",
          *(f"  {v['nome'][:20]:20s} {v['posti']:5d} posti  stato {v['stato']:12s} {v['descrizione']}; auto sulla strada piu' trafficata entro 300 m ~{v['auto_passaggio_txt']}"
            f" -> {v['esito']}" for v in validazione), "",
          "== Controllo a posteriori con le osservazioni di Leo (NON entra nei dati mostrati) ==",
          *(f"  {o['nome']}: {o['nota']} | adatti nel raggio {o['adatti_nel_raggio']} ({o['posti_adatti']} posti), "
            f"gratuiti {o['gratuiti']} ({o['posti_gratuiti']} posti) -> {o['esito']}" for o in a_posteriori), "",
          "== Direzioni d'ingresso (solo riferimento) ==",
          *(f"  {d['nome']:10s} auto {d['auto_in_entrata']:7d} da fermare {d['domanda']:6d} posti adatti {d['posti_adatti']:7d} {d['categoria']}"
            for d in direzioni), "",
          "== Sensibilita' ==", *(f"  {k}: {v}" for k, v in sens.items()), "",
          "== Controlli ==", *("  " + x for x in c.righe), "",
          "== Limiti ==",
          "- Auto che passano: modello del traffico V0 (stima debole, ±38%): solo ordine di grandezza.",
          "- Le stesse auto passano davanti a piu' fermate dello stesso corso: i numeri delle fermate non si sommano.",
          "- Quota di chi lascia l'auto: indagine IMQ 2022, poche interviste.",
          "- Posti stimati dalla superficie (25 m² a posto; meta' dei parcheggi fra 14 e 33 m²).",
          "- Riempimento misurato su pochi giorni e solo dove il 5T lo trasmette.",
          "- Distanza a piedi stimata (linea d'aria x 1,3). Treni non considerati."]
    RAPPORTO.write_text("\n".join(rr) + "\n", encoding="utf-8")
    print(f"Scritto: {OUT}\nScritto: {RAPPORTO}\nDurata {time.time() - t0:.0f} s; avvisi: {len(c.avvisi())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
