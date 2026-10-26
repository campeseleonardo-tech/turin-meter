# -*- coding: utf-8 -*-
"""
scripts/93_tp_contro_auto.py - Risultato 8, parte D (D1, D2, D3): dove il mezzo pubblico non conviene rispetto all'auto.

Sola lettura sui dati. Unita': le zone IMQ che hanno punti in data/processed/traffico_c/punti.json (script 41); le zone
rappresentate solo da una «porta» restano fuori. Per ogni zona si tengono fino a 5 punti, i piu' pesanti per
popolazione (pesi rinormalizzati). Il tempo fra due zone e' la media dei tempi fra i loro punti, pesata con i pesi dei punti.

D1 - tempi coi mezzi pubblici: r5py come lo script 18 (stesso GTFS, stessa rete OSM tagliata), giorno 2026-10-12,
     partenza dalle 7:45 con finestra di 30 minuti (fino alle 8:15), mediana dei tempi della finestra;
     TravelTimeMatrix, mezzi pubblici + cammino, tempo massimo 120 minuti. Una coppia di zone e' «senza
     collegamento» se meno della meta' del peso delle coppie di punti ha un collegamento entro 120 minuti.
D2 - tempi in auto: rete del modello del traffico (scripts/rete_osm.py), cammino minimo come nello script 42,
     tempo a flusso libero. Ora di punta = tempo x FATTORE (predefinito 1,5) + 5 minuti per parcheggiare e camminare.
     Sensibilita' con 1,3 e 1,8. Controllo: Piazza Castello -> Collegno nella fascia 20-35 minuti (Fase 5).
D3 - confronto: rapporto = tempo coi mezzi / tempo in auto (di punta). Auto della coppia = viaggi IMQ in auto come
     conducente (domanda_auto.json dello script 40), partenza dalle 6 alle 10 (ore 6-9), giorno feriale.
     Nessuna soglia di «convenienza»: titolo = rapporto mediano pesato per le auto; auto per fasce FISSE del
     rapporto (sotto 1,5, 1,5-2, 2-3, oltre 3). Tre gruppi di coppie: (a) Torino-Torino, (b) Torino-cintura,
     (c) cintura-cintura; il risultato principale usa (a)+(b): fuori Torino mancano treni e bus di altre aziende.
     Cammino a 4,8 km/h. Punti agganciati alla parte principale della rete stradale. I due calcoli precedenti
     (cammino a 3,6 km/h) restano nel JSON sotto «precedenti», segnati come superati.

Come si lancia
--------------
  python scripts\\93_tp_contro_auto.py --prova 10        (10 zone: scrive file con suffisso _prova)
  python scripts\\93_tp_contro_auto.py                   (tutte le zone; ripartibile: salva a tappe)
  Opzioni: --fattore 1.2 (limite alto; se manca, si calcola dai sensori 5T)   --lotto 20

Giro F3 (25/10/2026): la stima dell'auto e' quella APERTA (comuni.TempiAutoAperti, regole §6.1 del piano): velocita' dei sensori 5T dove ci sono,
altrimenti flusso libero x k(zona, ora) dalle sonde bus (script 107), piu' 20 secondi per incrocio con semaforo, piu' 5 minuti di parcheggio e cammino.
La stima dei sensori 5T (fattore unico 1,2, senza semafori) resta come «stima piu' favorevole all'auto». Campi: auto_stima_min e auto_favorevole_min.
Nel JSON «limite_basso» = stima aperta, «limite_alto» = stima favorevole (nomi storici); il «fattore» di una coppia = tempo aperto / tempo a flusso libero.

Uscite: data/processed/tp_contro_auto.json, docs/rapporti/RAPPORTO_TP_CONTRO_AUTO.txt
"""
import argparse
import datetime as dt
import importlib.util
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402
import rete_osm  # noqa: E402

RADICE = comuni.RADICE
PROC = RADICE / "data" / "processed"
TRAFFICO = PROC / "traffico_c"
OUT_JSON = PROC / "tp_contro_auto.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_TP_CONTRO_AUTO.txt"
RAPPORTO_STIMA = RADICE / "docs" / "rapporti" / "RAPPORTO_STIMA_AUTO.txt"
PARZIALE = PROC / "tp_contro_auto_parziale.npz"

GIORNO = dt.date(2026, 10, 12)
PARTENZA = dt.time(7, 45)
FINESTRA_MIN = 30
TEMPO_MAX_MIN = 120
PUNTI_PER_ZONA = 5
ORE_MATTINO = range(6, 10)          # partenza 06:00-09:59
VELOCITA_5T = PROC / "velocita_5t.json"
ORE_NOTTE = (2, 3, 4)               # strade libere: dalle 2 alle 5
ORA_PUNTA = 8
MIN_PARCHEGGIO = 5.0
SOGLIA_INTERVISTE = 30              # come SOGLIA_N dello script 14: una coppia si nomina in pagina solo con almeno 30 interviste (L9)
FASCE = (1.5, 2.0, 3.0)             # fasce fisse del rapporto TP/auto, scelte dopo le prime prove (il metodo e' cambiato 4 volte il 21/10)
VEL_PIEDI_KMH = 4.8                 # 80 m al minuto, come lo script 18 e tutto il progetto (r5py di serie: 3,6)
QUOTA_MIN_COLLEGATA = 0.5           # meta' del peso delle coppie di punti con collegamento

# percorsi noti (lat, lon), gli stessi dello script 50b; il primo e' il controllo della Fase 5
CASTELLO = (45.0703, 7.6869)
# tempi in auto controllati a mano su Google Maps, martedi' 20/10 alle 8:00, partendo da Piazza Castello (minuti).
# I 2 percorsi di CONTROLLO_GOOGLE non entrano mai nel fattore.
# Google Maps, 6 percorsi controllati a mano: usato solo per il limite basso della forbice (fattore = mediana di (tempo Google - 5) / flusso libero)
GOOGLE_AUTO_MIN = {"Piazza Castello → Collegno": 19, "Piazza Castello → Venaria Reale": 31,
                   "Piazza Castello → Settimo Torinese": 38, "Piazza Castello → Moncalieri": 34,
                   "Piazza Castello → Orbassano": 44, "Piazza Castello → Rivoli": 38}
# due percorsi in piu', solo per il controllo (Google, 21/10): mezzi pubblici (min, max) e auto
CONTROLLI_GOOGLE = {"Corso Racconigi → Piazza Castello": {"auto": 29, "mezzi": (30, 35), "mezzi_nota": "mezzi pubblici"},
                    "Moncalieri → Lingotto": {"auto": 14, "mezzi": (30, 35), "mezzi_nota": "solo GTT; col treno 19-23"}}
SOGLIA_AVVISO_GOOGLE = 0.25
NOTI = [("Piazza Castello → Collegno", CASTELLO, (45.0721, 7.5717)),
        ("Piazza Castello → Venaria Reale", CASTELLO, (45.1352, 7.6330)),
        ("Piazza Castello → Settimo Torinese", CASTELLO, (45.1395, 7.7703)),
        ("Piazza Castello → Moncalieri", CASTELLO, (45.0005, 7.6810)),
        ("Piazza Castello → Orbassano", CASTELLO, (45.0070, 7.5373)),
        ("Piazza Castello → Rivoli", CASTELLO, (45.0709, 7.5167)),
        ("Corso Racconigi → Piazza Castello", (45.0650, 7.6440), CASTELLO),
        ("Moncalieri → Lingotto", (45.0005, 7.6810), (45.0270, 7.6600))]
N_NOTI_TARATURA = 6                 # i primi 6; gli altri sono solo controllo


def fattore_da_sensori():
    """Fattore di punta = mediana, sui sensori 5T con dati affidabili, di velocita' media fra le 2 e le 5 / velocita' alle 8
    (giorno feriale). Un sensore senza dati affidabili di notte o alle 8 resta fuori. Arrotondato a 0,1."""
    d = json.loads(VELOCITA_5T.read_text(encoding="utf-8"))
    valori = []
    for v in d["sensori"].values():
        celle = v["celle"].get("0")
        if not celle:
            continue
        notte = [celle[str(h)]["v"] for h in ORE_NOTTE if str(h) in celle and celle[str(h)]["ok"] and celle[str(h)]["v"]]
        punta8 = celle.get(str(ORA_PUNTA))
        if not notte or not punta8 or not punta8["ok"] or not punta8["v"]:
            continue
        valori.append(float(np.mean(notte)) / punta8["v"])
    x = np.array(valori)
    q = np.percentile(x, [0, 25, 50, 75, 100])
    stat = {"sensori_totali": len(d["sensori"]), "sensori_usati": len(x), "minimo": q[0], "q1": q[1], "mediana": q[2], "q3": q[3],
            "massimo": q[4], "periodo": d["periodo"], "giorni_feriali": d["giorni"]["0"]}
    return round(float(q[2]), 1), stat


def nome_zona(n):
    """'01 Torino- Mirafiori Nord' -> 'Torino, Mirafiori Nord'; 'RIVALTA DI TORINO' -> 'Rivalta di Torino'."""
    if n.startswith("01 Torino"):
        n = "Torino, " + n[len("01 Torino"):].strip(" -")
    return n.title().replace(" Di ", " di ").replace(", ", ", ")


def carica_zone(prova):
    punti = json.loads((TRAFFICO / "punti.json").read_text(encoding="utf-8"))["zone"]
    nomi = {z["cod"]: z["denom"] for z in json.loads((PROC / "imq_zone.json").read_text(encoding="utf-8"))}
    zone = {}
    for cod, elenco in punti.items():
        veri = [p for p in elenco if p["tipo"] != "porta"]
        if not veri:                                  # zona rappresentata solo da porte: fuori
            continue
        top = sorted(veri, key=lambda p: -p["peso"])[:PUNTI_PER_ZONA]
        tot = sum(p["peso"] for p in top)
        zone[cod] = {"nome": nome_zona(nomi.get(cod, cod)), "punti": [
            {"lat": p["lat"], "lon": p["lon"], "nodo": int(p["nodo"]), "peso": p["peso"] / tot} for p in top]}
    return zone


def carica_auto(zone):
    """auto della coppia (zona A, zona B) = viaggi IMQ in auto come conducente, ore 6-9, giorno feriale."""
    d = json.loads((TRAFFICO / "domanda_auto.json").read_text(encoding="utf-8"))
    coppie = defaultdict(float)
    for par, arr, ora, peso, _n in d["celle"]:
        if ora in ORE_MATTINO and par in zone and arr in zone:
            coppie[(par, arr)] += peso
    return coppie


def carica_interviste(zone):
    """Interviste IMQ dietro ogni coppia (zona A, zona B): numero di interviste della coppia, tutti i mezzi, giorno intero (imq_od.json dello script 14,
    modo «tot»: lo stesso numero da cui lo script 14 decide se la coppia e' affidabile, SOGLIA_N = 30). Le interviste dei soli conducenti in auto
    del mattino sono al massimo 21 per coppia: con quel conteggio nessuna coppia arriverebbe a 30. Serve a nominare una coppia in pagina (L9)."""
    d = json.loads((PROC / "imq_od.json").read_text(encoding="utf-8"))
    return {(a, b): n for a, b, _v, n, _aff in d["od"]["tot"] if a in zone and b in zone}


def matrice_auto(zone, extra):
    """Tempi in auto (secondi, flusso libero) fra tutti i nodi dei punti e dei punti extra. Dict (nodo_a, nodo_b) -> s."""
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import dijkstra
    rete = rete_osm.carica(TRAFFICO / "rete")
    xy, archi = rete["nodi_xy"], rete["archi"]
    N = len(xy)
    src, dst, w = archi[:, 0].astype(np.int64), archi[:, 1].astype(np.int64), archi[:, 2].astype(np.float64)
    chiave = src * N + dst
    ordine = np.lexsort((w, chiave))                  # fra i duplicati il piu' veloce viene per primo
    chiave_s = chiave[ordine]
    primo = np.concatenate(([True], chiave_s[1:] != chiave_s[:-1]))
    sel = ordine[primo]
    tieni = src[sel] != dst[sel]
    M = csr_matrix((w[sel][tieni], (src[sel][tieni], dst[sel][tieni])), shape=(N, N))

    # parte principale della rete = la piu' grande componente fortemente connessa; i punti fuori da essa si agganciano al nodo piu' vicino dentro
    from scipy.sparse.csgraph import connected_components
    _, etichette = connected_components(M, directed=True, connection="strong")
    principale = np.argmax(np.bincount(etichette))
    nodi_princ = np.nonzero(etichette == principale)[0]
    xy_princ = xy[nodi_princ]
    spostati = {"n": 0, "su": 0, "max_m": 0.0}

    def nodo_vicino(lat, lon):
        d2 = (xy_princ[:, 0] - lat) ** 2 + (xy_princ[:, 1] - lon) ** 2
        return int(nodi_princ[int(np.argmin(d2))])

    def aggancia(nodo, lat, lon):
        spostati["su"] += 1
        if etichette[nodo] == principale:
            return nodo
        nuovo = nodo_vicino(lat, lon)
        spostati["n"] += 1
        spostati["max_m"] = max(spostati["max_m"], float(rete_osm.haversine_m(lat, lon, *xy[nuovo])))
        return nuovo

    for z in zone.values():
        for p in z["punti"]:
            p["nodo"] = aggancia(p["nodo"], p["lat"], p["lon"])
    nodi_extra = [(aggancia(int(np.argmin((xy[:, 0] - a[0]) ** 2 + (xy[:, 1] - a[1]) ** 2)), a[0], a[1]),
                   aggancia(int(np.argmin((xy[:, 0] - b[0]) ** 2 + (xy[:, 1] - b[1]) ** 2)), b[0], b[1])) for _, a, b in extra]
    nodi = sorted({p["nodo"] for z in zone.values() for p in z["punti"]} | {n for c in nodi_extra for n in c})
    t = {}
    for i in range(0, len(nodi), 25):
        gruppo = nodi[i:i + 25]
        dist = dijkstra(M, indices=gruppo)[:, nodi]
        for k, a in enumerate(gruppo):
            for j, b in enumerate(nodi):
                t[(a, b)] = float(dist[k, j])
    return t, nodi_extra, spostati


def tempo_zone_auto(za, zb, t):
    """media pesata dei tempi (secondi) fra i punti delle due zone."""
    tot = 0.0
    for p in za["punti"]:
        for q in zb["punti"]:
            tot += p["peso"] * q["peso"] * t[(p["nodo"], q["nodo"])]
    return tot


class StimaAperta:
    """Adattatore fra comuni.TempiAutoAperti e il calcolo a «fattore»: per un percorso o una coppia di zone, fattore = tempo aperto all'ora / tempo a
    flusso libero della rete del modello. Cosi' punta(libero, fattore) = tempo aperto + 5 minuti, e il resto degli script non cambia.
    t_libero: dict (nodo, nodo) -> secondi di matrice_auto(); zone e nodi_extra/nomi come in matrice_auto()."""

    def __init__(self, aperto, t_libero, zone=None, nodi_extra=None, nomi=None):
        self.aperto, self.t_libero = aperto, t_libero
        self.nodi = sorted({a for a, _ in t_libero})
        self.zone = zone or {}
        self.nodi_extra = nodi_extra or []
        self.indice = {n: k for k, n in enumerate(nomi or [])}
        self._t = {}

    def tempi(self, ora):
        h = comuni.TempiAutoAperti._ora(ora)
        if h not in self._t:
            self._t[h] = self.aperto.tempi(self.nodi, h)
        return self._t[h]

    def luogo(self, nome, ora="08:00"):
        """(fattore, vero) del percorso «luogo -> Piazza Castello» indicato da nome (vero = sempre, il percorso e' calcolato)."""
        a, b = self.nodi_extra[self.indice[nome]]
        return self.tempi(ora)[(a, b)] / self.t_libero[(a, b)], True

    def percorso_controllo(self, nome, ora="08:00"):
        return self.luogo(nome, ora)[0]

    def coppia(self, da, a, libero_min, ora="08:00"):
        """(fattore, vero) della coppia di zone: media pesata dei tempi aperti / media pesata dei tempi liberi."""
        t = self.tempi(ora)
        return tempo_zone_auto(self.zone[da], self.zone[a], t) / tempo_zone_auto(self.zone[da], self.zone[a], self.t_libero), True


def controlli_stima_aperta(c, aperto, modello, t_auto, nodi_extra, noti, ab, prova):
    """Controlli di buon senso della stima aperta (§6.1 del piano) e sensibilita' ai semafori; scrive RAPPORTO_STIMA_AUTO.txt (non in prova).
    Ritorna il blocco «stima_aperta» del JSON."""
    nodi = modello.nodi
    sens = {s: aperto.tempi(nodi, 8, s) for s in (10, 20, 30)}
    # notte (21-6): entro il 25% del flusso libero con semafori
    libero_sem = aperto.tempi(nodi, "libero")
    fuori = []
    for h in list(range(21, 24)) + list(range(0, 7)):
        t_h = aperto.tempi(nodi, h)
        for k, n in enumerate(noti):
            a, b = nodi_extra[k]
            r = t_h[(a, b)] / libero_sem[(a, b)] - 1
            if abs(r) > 0.25:
                fuori.append(f"{h:02d}h {n['nome']} {100 * r:+.0f}%")
    c("di notte (21-6) il tempo resta entro il 25% di flusso libero + semafori sui percorsi noti", not fuori,
      dettaglio=("tutti i " + str(len(noti)) + " percorsi in tutte le ore") if not fuori else f"{len(fuori)} fuori: " + "; ".join(fuori[:6]))
    cast = noti[0]
    c("Piazza Castello → Collegno alle 8 fra 20 e 35 minuti (stima aperta con 5 minuti di parcheggio)", 20 <= cast["auto_stima_min"] <= 35,
      dettaglio=f"{cast['auto_stima_min']:.1f} minuti")
    k8, k3 = aperto.k_citta[8], aperto.k_citta[3]
    c("k di punta (8) minore di k di notte (3)", k8 < k3, dettaglio=f"k(8) = {k8:.2f}, k(3) = {k3:.2f}")
    # copertura: quota della lunghezza dei percorsi (noti) con un sensore o un k della propria zona
    lung = cop = 0.0
    sem_n = []
    for k, n in enumerate(noti):
        a, b = nodi_extra[k]
        p = aperto.percorso(a, b, 8)
        if p:
            lung += p["lunghezza_m"]
            cop += aperto.copertura(p["tratti"], 8) * p["lunghezza_m"]
            sem_n.append((n["nome"], p["semafori"], p["lunghezza_m"] / 1000.0, p["secondi"] / 60.0))
    quota = cop / lung if lung else 0.0
    c("almeno il 70% della lunghezza dei percorsi noti ha un sensore 5T o un k della propria zona", quota >= 0.70, dettaglio=f"{100 * quota:.0f}%")
    mediane = {s: float(np.median([sens[s][nodi_extra[k]] / 60.0 for k in range(len(noti))])) for s in sens}
    ore_med = {}
    for h in (3, 8, 13, 17, 21):
        t_h = aperto.tempi(nodi, h)
        ore_med[h] = float(np.median([t_h[nodi_extra[k]] / 60.0 for k in range(len(noti))]))
    out = {"semafori_s": aperto.semafori_s, "sensibilita_semafori_s": {str(s): round(m, 1) for s, m in mediane.items()},
           "mediana_percorsi_noti_min_per_ora": {str(h): round(m, 1) for h, m in ore_med.items()},
           "sensori_abbinati": int(aperto.n_sensori), "incroci_con_semaforo": int(aperto.sem["incroci"]), "nodi_osm_semaforo": int(aperto.sem["grezzi"]),
           "copertura_percorsi_noti": round(quota, 3), "k_citta": {str(h): round(float(aperto.k_citta[h]), 2) for h in range(24)},
           "zone_con_k_proprio": len(aperto.k_zone)}
    if not prova:
        r = ["RAPPORTO STIMA AUTO APERTA (F3, regole §6.1 del piano)", f"generato: {dt.datetime.now().isoformat(timespec='seconds')}", "",
             "Metodo: grafo OSM del modello del traffico; velocita' dei tratti all'ora h (feriale): sensore 5T affidabile entro 40 m se c'e', altrimenti flusso libero",
             "(limite OSM, al massimo 50 km/h nei quartieri di Torino) x k(zona, h) dalle sonde bus (script 107); +20 secondi per incrocio con semaforo (OSM, entro 50 m = uno);",
             f"+{MIN_PARCHEGGIO:g} minuti di parcheggio e cammino. Stima favorevole all'auto: sensori 5T con fattore unico, senza semafori.",
             f"Sensori abbinati ai tratti: {aperto.n_sensori}; incroci con semaforo: {aperto.sem['incroci']} (da {aperto.sem['grezzi']} nodi OSM); zone con k proprio: {len(aperto.k_zone)}.", "",
             "TEMPO MEDIANO DEGLI 8 PERCORSI NOTI (minuti, senza i 5 di parcheggio), per ora", "  ora | minuti"]
        r += [f"  {h:02d} | {m:.1f}" for h, m in ore_med.items()]
        r += ["", "SENSIBILITA' AI SEMAFORI (alle 8, mediana degli 8 percorsi noti, minuti)"] + [f"  {s} secondi per semaforo: {m:.1f}" for s, m in mediane.items()]
        r += ["", "PERCORSI NOTI ALLE 8: nome | semafori sul percorso | km | minuti (senza parcheggio)"]
        r += [f"  {n} | {s} | {km:.1f} | {mn:.1f}" for n, s, km, mn in sem_n]
        r += ["", "CONTROLLI DI BUON SENSO"] + [f"  {x}" for x in c.righe[-4:]]
        RAPPORTO_STIMA.write_text("\n".join(r) + "\n", encoding="utf-8")
    return out


def avvia_r5py():
    spec = importlib.util.spec_from_file_location("acc18", AQUI / "18_accessibilita.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rete, gpd = m.avvia_rete()
    return m, rete, gpd


def matrice_tp(zone, extra, lotto, log):
    """Tempi TP (minuti, mediana nella finestra 7:45-8:15) fra tutti i punti. Ripartibile.
    Ritorna (ids, T) con T[i, j] in minuti, nan = nessun collegamento entro 120 minuti."""
    import pandas as pd
    elenco = []                                       # (id, lat, lon)
    for cod, z in zone.items():
        for k, p in enumerate(z["punti"]):
            elenco.append((f"{cod}_{k}", p["lat"], p["lon"]))
    for k, (_, a, b) in enumerate(extra):
        elenco.append((f"NOTO{k}_A", a[0], a[1]))
        elenco.append((f"NOTO{k}_B", b[0], b[1]))
    ids = [e[0] for e in elenco]
    firma = f"{len(ids)}-{round(sum(e[1] + e[2] for e in elenco), 5)}-{GIORNO}-{PARTENZA}-{FINESTRA_MIN}-{TEMPO_MAX_MIN}-piedi{VEL_PIEDI_KMH}"
    n = len(ids)
    T = np.full((n, n), np.nan)
    fatti = np.zeros(n, dtype=bool)
    if PARZIALE.is_file():
        z = np.load(PARZIALE, allow_pickle=True)
        if str(z["firma"]) == firma:
            T, fatti = z["T"], z["fatti"]
            log(f"ripresa: {int(fatti.sum())} origini su {n} gia' calcolate")
        else:
            log("file parziale di un altro calcolo: lo ignoro")
    m18, rete, gpd = avvia_r5py()
    from r5py import TransportMode as TM
    from r5py import TravelTimeMatrix
    df = pd.DataFrame({"id": ids, "lat": [e[1] for e in elenco], "lon": [e[2] for e in elenco]})
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")
    quando = dt.datetime.combine(GIORNO, PARTENZA)
    posizione = {i: k for k, i in enumerate(ids)}
    da_fare = [k for k in range(n) if not fatti[k]]
    t0 = time.time()
    for i in range(0, len(da_fare), lotto):
        blocco = da_fare[i:i + lotto]
        orig = gdf.iloc[blocco]
        mat = TravelTimeMatrix(rete, origins=orig, destinations=gdf, departure=quando,
                               departure_time_window=dt.timedelta(minutes=FINESTRA_MIN),
                               transport_modes=[TM.TRANSIT, TM.WALK], speed_walking=VEL_PIEDI_KMH,
                               max_time=dt.timedelta(minutes=TEMPO_MAX_MIN))
        mat = pd.DataFrame(mat)
        col = "travel_time" if "travel_time" in mat.columns else "travel_time_p50"
        v = mat[col]
        if str(v.dtype).startswith("timedelta"):
            v = v.dt.total_seconds() / 60.0
        for a, b, x in zip(mat["from_id"], mat["to_id"], v):
            T[posizione[a], posizione[b]] = float(x) if x == x else np.nan
        fatti[blocco] = True
        np.savez_compressed(PARZIALE, T=T, fatti=fatti, firma=firma)
        log(f"  TP: {int(fatti.sum())}/{n} origini ({time.time() - t0:.0f} s)")
    return ids, T


def tempo_zone_tp(za, ca, zb, cb, ids_pos, T):
    """media pesata dei tempi TP (minuti) sulle coppie di punti raggiungibili; (tempo, quota di peso collegata)."""
    somma = peso = tot = 0.0
    for k, p in enumerate(za["punti"]):
        for h, q in enumerate(zb["punti"]):
            w = p["peso"] * q["peso"]
            tot += w
            x = T[ids_pos[f"{ca}_{k}"], ids_pos[f"{cb}_{h}"]]
            if x == x:
                somma += w * x
                peso += w
    return (somma / peso if peso else None), (peso / tot if tot else 0.0)


def mediana_pesata(coppie, f, corr=1.0):
    """mediana del rapporto TP/auto pesata per le auto (fattore di punta f)."""
    v = sorted((p["tp_min"] / punta(p["libero_min"], fp(p, f), corr), p["auto"]) for p in coppie)
    tot = sum(w for _, w in v)
    if not v or tot <= 0:
        return None
    acc = 0.0
    for r, w in v:
        acc += w
        if acc >= tot / 2:
            return r
    return v[-1][0]


def punta(libero, f, corr=1.0):
    """Tempo in auto: guida (flusso libero x fattore x correzione del controllo con TomTom, §6.2) + parcheggio. corr=1 = stima aperta (A)."""
    return libero * f * corr + MIN_PARCHEGGIO


def fp(p, f):
    """Fattore di una coppia: se f e' None, quello della coppia stessa (stima aperta, per coppia); altrimenti f."""
    return p["f_basso"] if f is None else f


def mediana_fattore(coppie):
    """Mediana, pesata per le auto, dei fattori applicati alle coppie (stima aperta): serve solo come numero riassuntivo."""
    v = sorted((p["f_basso"], p["auto"]) for p in coppie)
    tot = sum(w for _, w in v)
    acc = 0.0
    for f, w in v:
        acc += w
        if acc >= tot / 2:
            return round(f, 2)
    return round(v[-1][0], 2)


def fasce(coppie, f, corr=1.0):
    """auto e coppie per fascia FISSA di rapporto (scelte dopo le prime prove)."""
    tot = sum(p["auto"] for p in coppie)
    estremi = [0.0, *FASCE, float("inf")]
    out = []
    for lo, hi in zip(estremi[:-1], estremi[1:]):
        sel = [p for p in coppie if lo <= p["tp_min"] / punta(p["libero_min"], fp(p, f), corr) < hi]
        a = sum(p["auto"] for p in sel)
        out.append({"da": lo, "a": (None if hi == float("inf") else hi), "auto": round(a), "coppie": len(sel),
                    "pct": (100 * a / tot if tot else 0.0)})
    return out


def quota_oltre(coppie, f, soglia, corr=1.0):
    tot = sum(p["auto"] for p in coppie)
    return sum(p["auto"] for p in coppie if p["tp_min"] / punta(p["libero_min"], fp(p, f), corr) >= soglia) / tot if tot else 0.0


def riepilogo(coppie, f, corr=1.0):
    return {"fattore": (mediana_fattore(coppie) if f is None and coppie else f), "auto": round(sum(p["auto"] for p in coppie)), "coppie": len(coppie),
            "mediano": mediana_pesata(coppie, f, corr), "fasce": fasce(coppie, f, corr), "quota_oltre_2": quota_oltre(coppie, f, 2.0, corr)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", type=int, default=0, help="usa solo le N zone con piu' auto in uscita")
    ap.add_argument("--fattore", type=float, default=None, help="fattore di punta (se manca: dai sensori 5T)")
    ap.add_argument("--lotto", type=int, default=20, help="origini per chiamata r5py (e per salvataggio)")
    args = ap.parse_args()
    comuni.richiedi_fonte(PROC / "imq_zone.json", PROC / "imq_od.json")      # L12: derivati da IMQ, fuori da git
    t_inizio = time.time()
    c = comuni.Controlli()
    fattore_sensori, stat_sensori = fattore_da_sensori()
    if args.fattore is None:
        args.fattore = fattore_sensori

    def log(m):
        print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

    zone = carica_zone(args.prova)
    auto = carica_auto(zone)
    interviste = carica_interviste(zone)
    totale_zone = sum(auto.values())
    if args.prova:
        uscita = defaultdict(float)
        for (a, b), v in auto.items():
            if a != b:
                uscita[a] += v
        tieni = set(sorted(uscita, key=lambda z: -uscita[z])[:args.prova])
        zone = {k: v for k, v in zone.items() if k in tieni}
        auto = carica_auto(zone)
        totale_zone = sum(auto.values())
    torino = {k for k, z in zone.items() if z["nome"].startswith("Torino,")}   # regola controllata sul file vero: coincide con i codici Q e con la macro «01 Torino»
    log(f"zone: {len(zone)} con punti ({len(torino)} di Torino); auto del mattino fra le zone incluse: {totale_zone:,.0f}")

    log("D2: tempi in auto sulla rete del modello del traffico ...")
    t_auto, nodi_extra, spostati = matrice_auto(zone, NOTI)
    log(f"  punti agganciati alla parte principale della rete: {spostati['n']} su {spostati['su']} spostati (distanza massima {spostati['max_m']:.0f} m)")
    # fattore del limite basso: Google Maps, 6 percorsi controllati a mano; usato solo per il limite basso della forbice
    liberi = [t_auto[(nodi_extra[k][0], nodi_extra[k][1])] / 60.0 for k in range(len(NOTI))]
    fattori_google = {nome: (GOOGLE_AUTO_MIN[nome] - MIN_PARCHEGGIO) / liberi[k] for k, (nome, _, _) in enumerate(NOTI) if nome in GOOGLE_AUTO_MIN}
    f_google = round(float(np.median(list(fattori_google.values()))), 1)
    # F3 (25/10/2026): la stima principale e' quella aperta (comuni.TempiAutoAperti), per coppia; i 6 percorsi di Google a mano restano come controllo.
    # La chiave JSON resta «fattore_basso_google» (nome storico): ora e' la mediana dei fattori della stima aperta.
    aperto = comuni.TempiAutoAperti(log=log)
    modello = StimaAperta(aperto, t_auto, zone, nodi_extra, [n for n, _, _ in NOTI])
    f_basso = f_google
    fonte_basso = "stima aperta: sensori 5T e sonde bus, 20 secondi per semaforo (comuni.TempiAutoAperti)"
    log(f"  stima dei sensori 5T: fattore {args.fattore:g}; stima principale: {fonte_basso}; Google a mano {f_google:g}")
    if not comuni.correzione_tempi_mezzi():
        log("AVVISO: manca data/processed/correzione_tempi_mezzi.json (script 105): i tempi coi mezzi restano da orario")
    log("D1: tempi coi mezzi pubblici (r5py, cammino a 4,8 km/h) ...")
    ids, T = matrice_tp(zone, NOTI, args.lotto, log)
    pos = {i: k for k, i in enumerate(ids)}

    # ---- tempi per coppia di zone, in tre gruppi: (a) Torino-Torino, (b) Torino-cintura e cintura-Torino, (c) cintura-cintura
    def gruppo(a, b):
        n = (a in torino) + (b in torino)
        return "a" if n == 2 else ("b" if n == 1 else "c")

    cod = sorted(zone)
    coppie, senza_link = [], []
    intra = 0.0
    infiniti = 0
    for a in cod:
        for b in cod:
            v = auto.get((a, b), 0.0)
            if a == b:
                intra += v
                continue
            secondi = tempo_zone_auto(zone[a], zone[b], t_auto)
            if not np.isfinite(secondi):
                infiniti += 1
                continue
            ta = secondi / 60.0
            tp, quota = tempo_zone_tp(zone[a], a, zone[b], b, pos, T)
            tp_orario = tp                                    # L23: il tempo da orario resta nel file; il resto del calcolo usa quello corretto con le misure
            tp = comuni.tempo_mezzi_corretto(tp, "punta_mattina")
            g = gruppo(a, b)
            if tp is None or quota < QUOTA_MIN_COLLEGATA:
                senza_link.append({"da": a, "a": b, "gruppo": g, "auto": v, "auto_libero_min": round(ta, 1), "quota_collegata": round(quota, 2)})
                continue
            coppie.append({"da": a, "a": b, "gruppo": g, "auto": v, "tp_min": tp, "tp_orario_min": tp_orario, "libero_min": ta, "quota_collegata": quota,
                           "interviste": int(interviste.get((a, b), 0))})
    f_alto = args.fattore                      # sensori 5T: auto piu' veloce, rapporto TP/auto piu' alto
    for p in coppie:
        p["auto_favorevole_min"] = punta(p["libero_min"], f_alto)
        p["rapporto"] = p["tp_min"] / p["auto_favorevole_min"]
        p["f_basso"], p["f_basso_vero"] = modello.coppia(p["da"], p["a"], p["libero_min"], "08:00")
        p["auto_stima_min"] = punta(p["libero_min"], p["f_basso"])
        p["rapporto_basso"] = p["tp_min"] / p["auto_stima_min"]

    ab = [p for p in coppie if p["gruppo"] in ("a", "b")]
    f_basso = mediana_fattore(ab)                 # numero riassuntivo: mediana, pesata per le auto, dei fattori applicati
    log(f"  fattore mediano della stima aperta (coppie a+b, pesato per le auto): {f_basso:g}")
    gruppi = {}
    nomi_gruppi = {"a": "Torino-Torino", "b": "Torino-cintura (e cintura-Torino)", "c": "cintura-cintura",
                   "ab": "principale: Torino-Torino e Torino-cintura"}
    for g, elenco in (("a", [p for p in coppie if p["gruppo"] == "a"]), ("b", [p for p in coppie if p["gruppo"] == "b"]),
                      ("c", [p for p in coppie if p["gruppo"] == "c"]), ("ab", ab)):
        ss = [s for s in senza_link if (s["gruppo"] in g)]
        gruppi[g] = {"nome": nomi_gruppi[g], "auto": round(sum(p["auto"] for p in elenco)), "coppie": len(elenco),
                     "senza_collegamento": {"coppie": len(ss), "auto": round(sum(s["auto"] for s in ss))},
                     "limite_alto": riepilogo(elenco, f_alto), "limite_basso": riepilogo(elenco, None),
                     "limite_corretto": riepilogo(elenco, None, comuni.fattore_controllo())}   # B: stima aperta corretta col controllo (§6.2)
        if g == "c":
            gruppi[g]["nota"] = "dati del mezzo pubblico incompleti: mancano treni e bus di altre aziende"
    base = gruppi["ab"]
    # le coppie peggiori si scelgono col fattore basso (auto piu' lenta): quelle con rapporto oltre 2, in ordine di auto
    # L9: una coppia si nomina solo con almeno SOGLIA_INTERVISTE interviste, altrimenti passa la successiva
    peggiori = sorted((p for p in ab if p["rapporto_basso"] >= 2.0 and p["interviste"] >= SOGLIA_INTERVISTE), key=lambda p: -p["auto"])[:15]
    per_zona = []
    for a in cod:
        mie = [p for p in ab if p["da"] == a]
        tot = sum(p["auto"] for p in mie)
        oltre_alto = sum(p["auto"] for p in mie if p["rapporto"] >= 2.0)
        oltre_basso = sum(p["auto"] for p in mie if p["rapporto_basso"] >= 2.0)
        per_zona.append({"zona": a, "nome": zone[a]["nome"], "auto_uscita": round(tot),
                         "quota_oltre_2_alto": (oltre_alto / tot if tot else None), "quota_oltre_2_basso": (oltre_basso / tot if tot else None)})
    per_zona.sort(key=lambda z: -(z["quota_oltre_2_basso"] or 0))

    # ---- controllo di buon senso: percorsi noti
    noti = []
    for k, (nome, a, b) in enumerate(NOTI):
        libero = liberi[k]
        tp = T[pos[f"NOTO{k}_A"], pos[f"NOTO{k}_B"]]
        fb = modello.percorso_controllo(nome, "08:00")
        noti.append({"nome": nome, "auto_libero_min": libero, "auto_favorevole_min": punta(libero, f_alto),
                     "auto_stima_min": punta(libero, fb), "fattore_basso_percorso": round(fb, 2),
                     "tp_min": (float(tp) if tp == tp else None), "controllo": k >= N_NOTI_TARATURA,
                     "google_auto_min": (GOOGLE_AUTO_MIN.get(nome) or CONTROLLI_GOOGLE.get(nome, {}).get("auto")),
                     "google_mezzi_min": (list(CONTROLLI_GOOGLE[nome]["mezzi"]) if nome in CONTROLLI_GOOGLE else None),
                     "google_mezzi_nota": (CONTROLLI_GOOGLE[nome]["mezzi_nota"] if nome in CONTROLLI_GOOGLE else None)})

    # ---- stima aperta: controlli di buon senso (§6.1) e sensibilita' ai semafori; rapporto RAPPORTO_STIMA_AUTO.txt
    stima_aperta = controlli_stima_aperta(c, aperto, modello, t_auto, nodi_extra, noti, ab, args.prova)

    # ---- controlli
    c("nessun tempo negativo o nullo fra zone diverse",
      all(p["tp_min"] > 0 and p["libero_min"] > 0 for p in coppie), bloccante=True)
    c("nessun tempo infinito in auto fra zone", infiniti == 0 and all(np.isfinite(n["auto_libero_min"]) for n in noti),
      dettaglio=f"{infiniti} coppie di zone, {sum(1 for n in noti if not np.isfinite(n['auto_libero_min']))} percorsi noti; punti spostati: {spostati['n']} su {spostati['su']}",
      bloccante=True)
    auto_senza = sum(s["auto"] for s in senza_link)
    c("coppie senza collegamento coi mezzi entro 120 minuti (contate a parte, per gruppo)", True,
      dettaglio="; ".join(f"{g}: {gruppi[g]['senza_collegamento']['coppie']} coppie, {gruppi[g]['senza_collegamento']['auto']:,} auto" for g in "abc"))
    auto_coll = sum(p["auto"] for p in coppie)
    somma = auto_coll + auto_senza + intra
    c("somma delle auto = totale IMQ 06-10 delle zone incluse", abs(somma - totale_zone) < 1e-6 * max(totale_zone, 1),
      dettaglio=f"{somma:,.0f} / {totale_zone:,.0f} (collegate {auto_coll:,.0f}, senza collegamento {auto_senza:,.0f}, dentro la zona {intra:,.0f})",
      bloccante=True)
    cast = noti[0]
    c("Piazza Castello → Collegno in auto di punta nella fascia 20-35 minuti, con tutti e due i fattori",
      20 <= cast["auto_favorevole_min"] <= 35 and 20 <= cast["auto_stima_min"] <= 35,
      dettaglio=f"{cast['auto_libero_min']:.1f} minuti a flusso libero; di punta {cast['auto_favorevole_min']:.1f} (fattore {f_alto:g}) e {cast['auto_stima_min']:.1f} (fattore {f_basso:g})")

    # ---- confronto con Google Maps: i 6 percorsi servono al fattore del limite basso della forbice; i 2 di controllo no
    con_google = [n for n in noti if n["google_auto_min"] and n["nome"] in GOOGLE_AUTO_MIN]
    diff = [n["auto_favorevole_min"] - n["google_auto_min"] for n in con_google]
    diff_media = float(np.mean(diff))
    diff_basso = float(np.mean([n["auto_stima_min"] - n["google_auto_min"] for n in con_google]))
    sotto = [n["nome"] for n in con_google if (n["google_auto_min"] - n["auto_favorevole_min"]) / n["google_auto_min"] > SOGLIA_AVVISO_GOOGLE]
    sotto_basso = [n["nome"] for n in con_google if (n["google_auto_min"] - n["auto_stima_min"]) / n["google_auto_min"] > SOGLIA_AVVISO_GOOGLE]
    c(f"fattore alto (sensori): tempo di punta non sotto Google di oltre il {int(SOGLIA_AVVISO_GOOGLE * 100)}% in piu' di meta' dei percorsi",
      len(sotto) <= len(con_google) / 2,
      dettaglio=f"differenza media {diff_media:+.1f} minuti (nostro meno Google); percorsi molto sotto: {len(sotto)} su {len(con_google)} (atteso: e' la stima piu' favorevole all'auto)")
    c(f"stima aperta: tempo di punta non sotto Google di oltre il {int(SOGLIA_AVVISO_GOOGLE * 100)}% in piu' di meta' dei percorsi",
      len(sotto_basso) <= len(con_google) / 2,
      dettaglio=f"differenza media {diff_basso:+.1f} minuti; percorsi molto sotto: {len(sotto_basso)} su {len(con_google)}")

    nomi = {k: v["nome"] for k, v in zone.items()}
    titolo = {"mediano_alto": base["limite_alto"]["mediano"], "mediano_basso": base["limite_basso"]["mediano"],
              "quota_oltre_2_alto": base["limite_alto"]["quota_oltre_2"], "quota_oltre_2_basso": base["limite_basso"]["quota_oltre_2"],
              "mediano_corretto": base["limite_corretto"]["mediano"], "quota_oltre_2_corretto": base["limite_corretto"]["quota_oltre_2"],
              "auto_collegate": base["auto"]}
    # L23: gli stessi numeri col tempo da orario, senza la correzione con le misure (vanno nel calcolo della scheda)
    ab_orario = [dict(p, tp_min=p["tp_orario_min"]) for p in ab]
    r_alto, r_basso = riepilogo(ab_orario, f_alto), riepilogo(ab_orario, None)
    titolo["da_orario"] = {"mediano_alto": r_alto["mediano"], "mediano_basso": r_basso["mediano"],
                           "quota_oltre_2_alto": r_alto["quota_oltre_2"], "quota_oltre_2_basso": r_basso["quota_oltre_2"]}
    prova = bool(args.prova)
    suff = "_prova" if prova else ""
    precedenti = None
    if OUT_JSON.is_file() and not prova:
        vecchio = json.loads(OUT_JSON.read_text(encoding="utf-8"))
        if "gruppi" not in vecchio:                    # primo calcolo (cammino a 3,6 km/h): si conserva una volta sola
            precedenti = {"nota": "calcolati con cammino a 3,6 km/h: superati",
                          "soglie_1_5_e_2": vecchio["precedenti"], "soglie_2_5_e_3_5": {"soglie": vecchio["parametri"]["soglie"], "base": vecchio["base"], "sensibilita": vecchio["sensibilita"]},
                          "noti": vecchio["noti"]}
        elif "fattori_sensibilita" not in vecchio["parametri"] and "fattore_basso_google" not in vecchio["parametri"]:
            precedenti = {**(vecchio.get("precedenti") or {}),
                          "fattore_1_5_fisso": {"nota": "fattore di punta 1,5 scelto a mano, prima della taratura sui sensori 5T",
                                                "gruppo_ab": vecchio["gruppi"]["ab"], "noti": vecchio["noti"]}}
        elif "fattore_basso_google" not in vecchio["parametri"]:   # versione con il solo fattore dei sensori e sensibilita' +-0,3
            precedenti = {**(vecchio.get("precedenti") or {}),
                          "fattore_sensori_con_sensibilita": {"nota": "solo fattore dei sensori 5T con sensibilita' +-0,3: sostituita dalla forbice",
                                                              "gruppo_ab": vecchio["gruppi"]["ab"], "noti": vecchio["noti"]}}
        else:
            precedenti = vecchio.get("precedenti")
    out = {
        "stimato": True,
        "parametri": {"giorno": str(GIORNO), "partenza": f"{PARTENZA:%H:%M}", "finestra_min": FINESTRA_MIN,
                      "tempo_max_min": TEMPO_MAX_MIN, "velocita_piedi_kmh": VEL_PIEDI_KMH, "punti_per_zona": PUNTI_PER_ZONA,
                      "ore_auto": list(ORE_MATTINO), "fattore_punta": f_alto, "fattore_basso_google": f_basso, "fattore_google_manuale": f_google,
                      "fonte_basso": fonte_basso, "stima_aperta": stima_aperta,
                      "forbice": {"limite_alto": {"fattore": f_alto, "fonte": "sensori 5T (stima piu' favorevole all'auto)"},
                                  "limite_basso": {"fattore": f_basso, "fonte": fonte_basso, "nota": "fattore = mediana, pesata per le auto, dei fattori applicati"}},
                      "fattore_sensori": stat_sensori, "fattori_google_per_percorso": fattori_google,
                      "minuti_parcheggio": MIN_PARCHEGGIO,
                      "correzione_tempi_mezzi": (comuni.correzione_tempi_mezzi() or {}).get("per_fascia", {}).get("punta_mattina"),
                      "quota_a_bordo": ((comuni.correzione_tempi_mezzi() or {}).get("quota_a_bordo") or {}).get("mediana"),
                      "fasce": list(FASCE), "n_zone": len(zone), "n_zone_torino": len(torino), "punti_spostati": spostati, "prova": prova},
        "titolo": titolo, "gruppi": gruppi,
        "peggiori": [{"da": p["da"], "a": p["a"], "da_nome": nomi[p["da"]], "a_nome": nomi[p["a"]], "gruppo": p["gruppo"], "auto": round(p["auto"]),
                      "tp_min": round(p["tp_min"], 1), "tp_orario_min": round(p["tp_orario_min"], 1), "auto_favorevole_min": round(p["auto_favorevole_min"], 1),
                      "auto_stima_min": round(p["auto_stima_min"], 1),
                      "rapporto": round(p["rapporto"], 2), "rapporto_basso": round(p["rapporto_basso"], 2), "fattore_basso": round(p["f_basso"], 2),
                      "interviste": p["interviste"]} for p in peggiori],
        "per_zona": per_zona,
        "coppie": [{"da": p["da"], "a": p["a"], "gruppo": p["gruppo"], "auto": round(p["auto"], 1), "tp_min": round(p["tp_min"], 1), "tp_orario_min": round(p["tp_orario_min"], 1),
                    "libero_min": round(p["libero_min"], 2),
                    "auto_favorevole_min": round(p["auto_favorevole_min"], 1), "rapporto": round(p["rapporto"], 2),
                    "auto_stima_min": round(p["auto_stima_min"], 1), "rapporto_basso": round(p["rapporto_basso"], 2),
                    "fattore_basso": round(p["f_basso"], 2), "interviste": p["interviste"]}
                   for p in sorted(coppie, key=lambda p: -p["auto"])],
        "senza_collegamento": [{**s, "auto": round(s["auto"], 1)} for s in senza_link], "dentro_zona_auto": round(intra),
        "noti": noti, "google": {"data": "martedì 20/10/2026 ore 8:00", "differenza_media_min": diff_media, "differenza_media_basso_min": diff_basso,
                                 "percorsi_molto_sotto": sotto, "percorsi_molto_sotto_basso": sotto_basso},
        "totale_auto_zone": round(totale_zone),
        "controlli": list(c.righe),
    }
    if precedenti:
        out["precedenti"] = precedenti
    dest_json = OUT_JSON.with_name(OUT_JSON.stem + suff + ".json")
    dest_json.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    def riga_fasce(rr):
        return "; ".join(f"{('sotto ' + format(f['a'], 'g')) if f['da'] == 0 else (('oltre ' + format(f['da'], 'g')) if f['a'] is None else format(f['da'], 'g') + '-' + format(f['a'], 'g'))}: "
                         f"{f['auto']:,} auto ({f['pct']:.1f}%)" for f in rr["fasce"])

    r = [f"RAPPORTO TP CONTRO AUTO (Risultato 8, parte D, STIMATO){' - PROVA' if prova else ''}",
         f"generato: {dt.datetime.now().isoformat(timespec='seconds')}", "",
         f"Zone IMQ con punti: {len(zone)} (zone solo «porta» escluse; {len(torino)} di Torino); fino a {PUNTI_PER_ZONA} punti per zona, i piu' pesanti.",
         f"Tempi coi mezzi: r5py, giorno {GIORNO}, mediana delle partenze 7:45-8:15, mezzi pubblici + cammino a {VEL_PIEDI_KMH:g} km/h, massimo {TEMPO_MAX_MIN} minuti.",
         f"Tempi in auto: rete del modello del traffico, flusso libero x fattore di punta + {MIN_PARCHEGGIO:.0f} minuti (parcheggio e cammino). La stima principale e' quella aperta (giro F3: sensori 5T e sonde bus, 20 secondi per semaforo); quella dei sensori con fattore unico e' la piu' favorevole all'auto:",
         f"  stima con il rallentamento dei sensori = fattore dei sensori 5T, {f_alto:g} (solo traffico, senza semafori e incroci: la piu' favorevole all'auto): mediana di (velocita' media 2-5 / velocita' alle 8, feriale) su {stat_sensori['sensori_usati']} sensori "
         f"con dati affidabili (su {stat_sensori['sensori_totali']}; periodo {stat_sensori['periodo']['da']} - {stat_sensori['periodo']['a']}, {stat_sensori['giorni_feriali']} giorni feriali);",
         f"    distribuzione fra sensori: minimo {stat_sensori['minimo']:.2f}, 1° quartile {stat_sensori['q1']:.2f}, mediana {stat_sensori['mediana']:.2f}, "
         f"3° quartile {stat_sensori['q3']:.2f}, massimo {stat_sensori['massimo']:.2f}.",
         f"  stima principale = {fonte_basso}; fattore mediano applicato {f_basso:g} (tempo aperto / nostro flusso libero, pesato per le auto). "
         + f"Google Maps a mano: mediana di (tempo Google - 5) / tempo a flusso libero sui 6 percorsi ({', '.join(format(x, '.2f') for x in fattori_google.values())}) = {f_google:g}.",
         f"Punti agganciati alla parte principale della rete: {spostati['n']} su {spostati['su']} spostati (distanza massima {spostati['max_m']:.0f} m).",
         f"Auto: viaggi IMQ in auto conducente, partenza 6-10, feriale. Totale fra le zone incluse: {totale_zone:,.0f}.",
         "Gruppi: (a) Torino-Torino, (b) Torino-cintura e cintura-Torino, (c) cintura-cintura. Il risultato principale usa (a)+(b).",
         f"Fasce fisse del rapporto (tempo coi mezzi / tempo in auto), scelte dopo le prime prove (il metodo e' cambiato 4 volte il 21/10): sotto {FASCE[0]:g}, {FASCE[0]:g}-{FASCE[1]:g}, {FASCE[1]:g}-{FASCE[2]:g}, oltre {FASCE[2]:g}.",
         "", "TITOLO (gruppi a+b): stima aperta e stima dei sensori",
         f"  al mattino, coi mezzi pubblici si impiega {titolo['mediano_basso']:.2f} volte il tempo dell'auto con la stima aperta (rapporto mediano pesato per le auto; fattore mediano {f_basso:g}) e {titolo['mediano_alto']:.2f} con quella dei sensori ({f_alto:g})",
         f"  quota di auto con rapporto oltre 2: da {100 * titolo['quota_oltre_2_basso']:.1f}% a {100 * titolo['quota_oltre_2_alto']:.1f}% di {titolo['auto_collegate']:,} auto",
         "", "FASCE E MEDIANA PER GRUPPO (stima aperta | stima dei sensori)"]
    for g in ("a", "b", "ab", "c"):
        gg = gruppi[g]
        r.append(f"  ({g}) {gg['nome']}: {gg['coppie']} coppie, {gg['auto']:,} auto" + (f" - {gg['nota']}" if g == "c" else ""))
        for nome_l, chiave in (("stima aperta", "limite_basso"), ("stima dei sensori", "limite_alto")):
            rr = gg[chiave]
            r.append(f"      {nome_l}, fattore {rr['fattore']:g}: mediano {rr['mediano']:.2f}; oltre 2: {100 * rr['quota_oltre_2']:.1f}%")
            r.append(f"         {riga_fasce(rr)}")
        r.append(f"      senza collegamento entro {TEMPO_MAX_MIN} minuti (a parte): {gg['senza_collegamento']['coppie']} coppie, {gg['senza_collegamento']['auto']:,} auto")
    r += ["", f"LE 15 COPPIE PEGGIORI PER AUTO COINVOLTE (rapporto oltre 2 con la stima aperta, fattore mediano {f_basso:g}; solo gruppi a e b e coppie con almeno 30 interviste)",
          "  da → a | auto | TP min | auto di punta min (basso-alto) | rapporto (basso-alto)"]
    for p in out["peggiori"]:
        r.append(f"  {p['da_nome']} → {p['a_nome']} | {p['auto']:,} | {p['tp_min']:.0f} | {p['auto_stima_min']:.0f}-{p['auto_favorevole_min']:.0f} | {p['rapporto_basso']:.1f}-{p['rapporto']:.1f}")
    r += ["", "PER ZONA: quota delle auto in uscita con rapporto oltre 2, stima aperta - stima dei sensori (prime 15, gruppi a+b)"]
    for z in per_zona[:15]:
        r.append(f"  {z['nome']}: {100 * (z['quota_oltre_2_basso'] or 0):.0f}% - {100 * (z['quota_oltre_2_alto'] or 0):.0f}% di {z['auto_uscita']:,} auto")
    r += ["", "NOI CONTRO GOOGLE MAPS (martedì 20/10 alle 8:00; per la stima aperta si usa il tempo di ogni percorso)",
          f"  percorso | flusso libero | nostro di punta, sensori (fattore {f_alto:g}) | nostro di punta, stima aperta | Google auto | differenza alto / basso (nostro - Google) | mezzi pubblici nostri"]
    for n in noti:
        if not n["google_auto_min"]:
            continue
        r.append(f"  {n['nome']}{' (solo controllo)' if n['controllo'] else ''} | {n['auto_libero_min']:.1f} | {n['auto_favorevole_min']:.1f} | {n['auto_stima_min']:.1f} | {n['google_auto_min']} | "
                 f"{n['auto_favorevole_min'] - n['google_auto_min']:+.1f} / {n['auto_stima_min'] - n['google_auto_min']:+.1f} | "
                 + (f"{n['tp_min']:.0f}" if n["tp_min"] is not None else "nessun collegamento")
                 + (f" (Google {n['google_mezzi_min'][0]}-{n['google_mezzi_min'][1]}, {n['google_mezzi_nota']})" if n["google_mezzi_min"] else ""))
    r.append(f"  differenza media sui 6 percorsi: sensori {diff_media:+.1f} minuti, stima aperta {diff_basso:+.1f} minuti")
    r += ["", "CONTROLLI"] + [f"  {x}" for x in c.righe]
    r += ["", "LIMITI: tempi TP da orario programmato (ottimisti); fuori Torino mancano treni e altre aziende (gruppo c a parte, gruppo b da leggere con cautela); "
              "il flusso libero non conta semafori e incroci; la stima aperta li conta (20 secondi l'uno) e usa i sensori 5T e le sonde bus (traffico di un feriale di ottobre 2026), con la stima dei sensori come la piu' favorevole all'auto, piu' 5 minuti per parcheggiare; "
              "il centro di ogni zona e' una media di punti; IMQ e' un'indagine campionaria."]
    dest_rapp = RAPPORTO.with_name(RAPPORTO.stem + suff + ".txt")
    dest_rapp.write_text("\n".join(r) + "\n", encoding="utf-8")
    log(f"scritto {dest_json.relative_to(RADICE)} e {dest_rapp.relative_to(RADICE)} ({time.time() - t_inizio:.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
