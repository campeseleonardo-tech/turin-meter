#!/usr/bin/env python3
"""
comuni.py  -  funzioni e costanti usate da piu' script (preparato da Claude il 20/10/2026).

Cosa c'e'
---------
  trova_radice()          cartella del progetto (quella che si chiama GTT)
  haversine_m()           distanza in metri fra due punti (lat, lon)
  proietta(lat, lon)      coordinate in metri (piano locale centrato su 45,07 gradi), per distanze veloci
  ora_locale(dt_utc)      ora italiana da un datetime UTC (ora legale: ultima domenica di marzo e di ottobre)
  percentile_rank(dict)   percentile 0-100, valori uguali -> stesso percentile (copia di quella dello script 75)
  soglia_quantile(lista, percentile)  valore alla posizione del percentile (stessa regola dello script 75)
  carica_script(nome)     carica uno script che inizia con un numero (es. "42_instradamento.py") come modulo
  Controlli               raccoglie i controlli: bloccanti (errori di struttura) o avvisi (numeri da guardare)
Costanti: ZONE_CENTRALI (Q001-Q009), MACRO_UNIVERSO, CENTRO_LAT/LON (Piazza Castello), FATTORE_PIEDI,
MODI_AUTO, MEZZI_PUBBLICI, MATTINO_MINUTI.

Come si prova
-------------
  python scripts\\comuni.py      (stampa 4 controlli: devono essere tutti OK)
"""
import importlib.util
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent

# zona centrale: per fermate E parcheggi (vedi sviluppo/note_tecniche/R6_parcheggi.md)
ZONE_CENTRALI = tuple(f"Q{n:03d}" for n in range(1, 10))
MACRO_UNIVERSO = ("01 Torino", "02 Cintura", "03 Resto CMTO")
CENTRO_LAT, CENTRO_LON = 45.0711, 7.6857          # Piazza Castello
LAT_RIF = 45.07
M_GRADO = 111000.0
FATTORE_PIEDI = 1.3                                # distanza a piedi = linea d'aria x 1,3
MODI_AUTO = ("03", "21")                           # auto da conducente, car sharing (04 = passeggero: persone, non auto)
MODI_AUTO_PERSONE = ("03", "04", "21")
MEZZI_PUBBLICI = ("06", "07", "08", "09", "12", "13", "19", "22")   # come lo script 73
MATTINO_MINUTI = (360, 599)                        # partenza 06:00-09:59


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def proietta(lat, lon):
    """(x, y) in metri; stessa formula degli script 80 e 69."""
    return (lon * M_GRADO * math.cos(math.radians(LAT_RIF)), lat * M_GRADO)


def _ultima_domenica(anno, mese):
    d = date(anno, mese, 31)
    while d.weekday() != 6:
        d -= timedelta(days=1)
    return d


def ora_locale(dt_utc):
    a = dt_utc.year
    inizio = datetime(a, 3, _ultima_domenica(a, 3).day, 1, tzinfo=timezone.utc)
    fine = datetime(a, 10, _ultima_domenica(a, 10).day, 1, tzinfo=timezone.utc)
    return dt_utc + timedelta(hours=2 if inizio <= dt_utc < fine else 1)


def percentile_rank(valori):
    """Percentile 0-100, valori uguali -> stesso percentile (copia della funzione dello script 75)."""
    chiavi = list(valori.keys())
    ordinati = sorted(chiavi, key=lambda k: valori[k])
    n = len(ordinati)
    if n <= 1:
        return {k: 100.0 for k in chiavi}
    rank = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and valori[ordinati[j + 1]] == valori[ordinati[i]]:
            j += 1
        for k in ordinati[i:j + 1]:
            rank[k] = (i + j) / 2
        i = j + 1
    return {k: 100.0 * rank[k] / (n - 1) for k in chiavi}


def soglia_quantile(valori, percentile):
    """Stessa regola di soglia_90 dello script 75, per un percentile qualsiasi (90 = il 10% piu' alto)."""
    v = sorted(valori)
    if not v:
        return None
    idx = max(0, min(len(v) - 1, round(percentile / 100 * (len(v) - 1))))
    return v[idx]


# Indirizzi del progetto pubblicato (decisione 11 del piano): il sito e il repository pubblico. Un solo posto, usato da pagine, immagini e README.
SITO_URL = "https://campeseleonardo-tech.github.io/turin-meter/"
REPO_URL = "https://github.com/campeseleonardo-tech/turin-meter"
NOME_SITO = "Turin Meter"


# Periodo fisso dei dati (giri L9 e L9b, 24/10/2026): SOLO GIORNI INTERI. Regola: il PERIODO non contiene mai il giorno della copia dello storico
# (quel giorno e' a meta': i numeri non si riprodurrebbero). Gli script 24, 26, 27, 33, 69, 70, 71, 88 e 04_genera_mappa.py lo leggono: i dati
# arrivati dopo non entrano nei risultati finche' non si cambia qui a mano (lavoro P8). Estremi inclusi, giorni locali.
PERIODO = {
    "sensori": ("2026-10-09", "2026-10-22"),     # sensori 5T (velocita_5t.json): script 24, 26, e da li' 33 e 88
    "gps": ("2026-10-10", "2026-10-22"),         # passaggi dei mezzi (start_date dello storico): script 27, 70 e velocita' della mappa
    "parcheggi": ("2026-10-15", "2026-10-22"),   # riempimento dei parcheggi 5T: script 69 e 71
}


def _iso(giorno):
    """'2026-10-09', '20261009' o date -> 'AAAA-MM-GG'."""
    t = giorno.isoformat() if hasattr(giorno, "isoformat") else str(giorno)
    return t if "-" in t else f"{t[:4]}-{t[4:6]}-{t[6:8]}"


def nel_periodo(giorno, chiave):
    """True se il giorno sta nel periodo fisso PERIODO[chiave]."""
    da, a = PERIODO[chiave]
    return da <= _iso(giorno)[:10] <= a


# File derivati da IMQ 2022 e OMI: ricopiano le celle o le quotazioni della fonte, quindi (giro L12, 24/10/2026) non stanno in git.
# Se mancano, gli script si fermano con un messaggio che dice cosa scaricare e da dove (docs/en/METHODS.md).
def _come_rifare(nome):
    n = Path(nome).name
    if n.startswith("imq_") or Path(nome).parent.name == "imq":
        return ("IMQ 2022 (Agenzia della mobilita' piemontese: dati aperti e zone di campionamento)",
                "scarica i dati IMQ nella cartella data/raw/IMQ2022_opendata_web, poi python scripts/14_prepara_imq.py, 15_prepara_zone_imq.py e 16_prepara_imq_mappa.py")
    if n == "omi_zone.json":
        return ("OMI (Agenzia delle Entrate: quotazioni e perimetri delle zone)",
                "scarica quotazioni e KML OMI in data/raw/omi_2025_2, poi python scripts/08_prepara_omi.py")
    if n.startswith("domanda") or "domanda_" in n:
        return ("IMQ 2022 (matrice di domanda per coppia di zone)",
                "con i file IMQ al loro posto: python scripts/rifai_tutto.py --da traffico")
    return (None, None)


def richiedi_fonte(*percorsi):
    """Si ferma con un messaggio chiaro se manca uno dei file derivati da IMQ/OMI (o un altro file); ritorna i percorsi se ci sono tutti."""
    for p in percorsi:
        if not Path(p).exists():
            fonte, come = _come_rifare(p)
            if fonte is None:
                raise SystemExit(f"ERRORE: manca {p}")
            raise SystemExit(f"ERRORE: manca {Path(p).name} ({p}).\n  Deriva da {fonte} e non sta in git (licenza non chiara).\n"
                             f"  Come rifarlo: {come}.\n  Indirizzi delle fonti: docs/en/METHODS.md. Spiegazione: README, «Dati».")
    return percorsi


def controlla_copia_storico(db):
    """AVVISO se il giorno (locale) dell'ultimo cambio della copia dello storico e' dentro un PERIODO: sarebbe un giorno a meta'."""
    import datetime as _dt
    giorno = _dt.datetime.fromtimestamp(Path(db).stat().st_mtime).date().isoformat()
    for k, (da, a) in PERIODO.items():
        if da <= giorno <= a:
            print(f"AVVISO: il giorno della copia dello storico ({giorno}) e' dentro il periodo fisso '{k}' ({da} - {a}): giorno a meta', ritira l'estremo")


def testo_periodo(chiave):
    """«dal 09/10/2026 al 22/10/2026», per le schede."""
    da, a = PERIODO[chiave]
    it = lambda t: f"{t[8:10]}/{t[5:7]}/{t[:4]}"
    return f"dal {it(da)} al {it(a)}"


def controlla_periodo(periodo_json, chiave):
    """AVVISO (stampato) se il periodo scritto in un JSON non e' quello fisso."""
    p = (periodo_json or {})
    if (p.get("da"), p.get("a")) != PERIODO[chiave]:
        print(f"AVVISO: il periodo dei dati ({p.get('da')} - {p.get('a')}) non e' quello fisso {PERIODO[chiave][0]} - {PERIODO[chiave][1]} (comuni.PERIODO): rilancia lo script che scrive il JSON")


class TempiAutoAperti:
    """Stima aperta dei tempi in auto (F3, regole §6.1 del piano): rete OSM di rete_osm.py, velocita' dei tratti per ora, semafori.
    Velocita' di un tratto all'ora h (giorno feriale):
      (a) tratto abbinato (entro 40 m) a un sensore 5T con dato affidabile all'ora h: la velocita' mediana misurata (velocita_5t.json);
      (b) altrimenti flusso libero x k(zona, h): flusso libero = limite OSM (o valore della classe), al massimo 50 km/h nei quartieri di Torino
          (tranne autostrade e tangenziali); k(zona, h) dalle sonde bus (script 107), con ripiego sul k di tutta la citta'.
    Ogni incrocio con semaforo (OSM highway=traffic_signals, quelli entro 50 m contano uno) aggiunge semafori_s secondi (20) a tutte le ore.
    Il tempo ritornato e' quello della corsa: i 5 minuti di parcheggio e cammino li aggiunge chi chiama.
    ora: intero o «HH:MM»; il valore speciale «libero» = flusso libero con semafori, senza traffico (k = 1, nessun sensore)."""

    SEMAFORI_S = 20.0
    DIST_SENSORE_M = 40.0
    MAX_URBANO_KMH = 50.0
    MIN_KMH = 3.0

    def __init__(self, semafori_s=None, log=print):
        import numpy as np
        import rete_osm
        self.np = np
        self.semafori_s = self.SEMAFORI_S if semafori_s is None else float(semafori_s)
        cartella = RADICE / "data" / "processed" / "traffico_c" / "rete"
        self.rete = rete_osm.carica(cartella)
        meta = self.rete["meta"]
        self.sem = rete_osm.carica_semafori(cartella, log=log)
        self.E = len(self.rete["edge_a"])
        self.N = len(self.rete["nodi_xy"])
        self.lunghezza = self.rete["edge_len"]
        self.alta_via = np.array([h.startswith(("motorway", "trunk")) for h in meta["highway"]])
        v = np.array(meta["vel_kmh"], dtype=float)
        # zona di ogni tratto (punto di mezzo) e quartieri di Torino
        sb = carica_script("107_sonde_bus.py")
        off = self.rete["edge_off"]
        mid = self.rete["edge_pts"][(off[:-1] + (off[1:] - off[:-1]) // 2).astype(int)]
        albero, poligoni, codici = sb.zone_poligoni()
        self.zona_tratto = sb.zona_dei_punti(albero, poligoni, codici, mid[:, 0], mid[:, 1])
        torino = np.array([z is not None and str(z).startswith("Q") for z in self.zona_tratto])
        self.libero_kmh = np.where(torino & ~self.alta_via, np.minimum(v, self.MAX_URBANO_KMH), v)
        # k(zona, ora): sonde bus
        sonde = json.loads((RADICE / "data" / "processed" / "sonde_bus.json").read_text(encoding="utf-8"))
        if sonde.get("prova"):
            raise SystemExit("ERRORE: data/processed/sonde_bus.json e' di prova: rilancia scripts/107_sonde_bus.py")
        self.k_citta = np.array([sonde["citta"][str(h)]["k"] for h in range(24)])
        self.k_zone = {cod: {int(h): c["k"] for h, c in z["ore"].items()} for cod, z in sonde["zone"].items()}
        self.k_tratto = np.empty((24, self.E))
        self.k_proprio = np.zeros((24, self.E), dtype=bool)
        for h in range(24):
            self.k_tratto[h] = self.k_citta[h]
        for cod, ore in self.k_zone.items():
            idx = np.nonzero(self.zona_tratto == cod)[0]
            for h, k in ore.items():
                self.k_tratto[h, idx] = k
                self.k_proprio[h, idx] = True
        # sensori 5T abbinati ai tratti (per posizione)
        self.v_sensore = np.full((24, self.E), np.nan)
        self.n_sensori = self._abbina_sensori()
        self.semafori_nodo = np.zeros(self.N, dtype=bool)
        self.semafori_nodo[self.sem["nodi"]] = True
        self.semafori_tratto = np.zeros(self.E, dtype=bool)
        self.semafori_tratto[self.sem["tratti"]] = True
        self._cache = {}

    def _abbina_sensori(self):
        import rete_osm
        from scipy.spatial import cKDTree
        np = self.np
        d = json.loads((RADICE / "data" / "processed" / "velocita_5t.json").read_text(encoding="utf-8"))
        pts = self.rete["edge_pts"]
        tratto_di_punto = np.repeat(np.arange(self.E), np.diff(self.rete["edge_off"]))
        albero = cKDTree(rete_osm._proietta(pts[:, 0], pts[:, 1]))
        somma = np.zeros((24, self.E))
        conta = np.zeros((24, self.E))
        usati = 0
        for s in d["sensori"].values():
            celle = s["celle"].get("0")
            if not celle:
                continue
            dist, i = albero.query(rete_osm._proietta([s["lat"]], [s["lon"]])[0])
            if dist > self.DIST_SENSORE_M:
                continue
            e = int(tratto_di_punto[int(i)])
            dato = False
            for h, c in celle.items():
                if c.get("ok") and c.get("v"):
                    somma[int(h), e] += c["v"]
                    conta[int(h), e] += 1
                    dato = True
            usati += dato
        with np.errstate(invalid="ignore", divide="ignore"):
            self.v_sensore = np.where(conta > 0, somma / np.maximum(conta, 1), np.nan)
        return usati

    @staticmethod
    def _ora(ora):
        if ora == "libero":
            return "libero"
        if isinstance(ora, str):
            return int(ora[:2])
        return int(ora)

    def velocita(self, ora):
        """km/h di ogni tratto all'ora (o «libero»)."""
        np = self.np
        h = self._ora(ora)
        if h == "libero":
            return self.libero_kmh.copy()
        v = np.where(np.isnan(self.v_sensore[h]), self.libero_kmh * self.k_tratto[h], self.v_sensore[h])
        return np.maximum(v, self.MIN_KMH)

    def matrice_pesi(self, ora, semafori_s=None):
        """(M, sel, archi): grafo dei tempi (secondi) per l'ora, con i semafori; sel = indici degli archi tenuti (il piu' veloce fra i duplicati)."""
        from scipy.sparse import csr_matrix
        np = self.np
        sem = self.semafori_s if semafori_s is None else float(semafori_s)
        h = self._ora(ora)
        chiave = (h, sem)
        if chiave in self._cache:
            return self._cache[chiave]
        archi = self.rete["archi"]
        src, dst, e = archi[:, 0].astype(np.int64), archi[:, 1].astype(np.int64), archi[:, 3].astype(np.int64)
        t_tratto = self.lunghezza / (self.velocita(ora) / 3.6)
        w = t_tratto[e] + sem * (self.semafori_nodo[dst] | self.semafori_tratto[e])
        k = src * self.N + dst
        ordine = np.lexsort((w, k))
        ks = k[ordine]
        primo = np.concatenate(([True], ks[1:] != ks[:-1]))
        sel = ordine[primo]
        sel = sel[src[sel] != dst[sel]]
        M = csr_matrix((w[sel], (src[sel], dst[sel])), shape=(self.N, self.N))
        if len(self._cache) > 8:
            self._cache.clear()
        self._cache[chiave] = (M, sel, archi)
        return self._cache[chiave]

    def tempi(self, nodi, ora, semafori_s=None):
        """Dict (nodo_a, nodo_b) -> secondi fra tutti i nodi dati."""
        from scipy.sparse.csgraph import dijkstra
        M = self.matrice_pesi(ora, semafori_s)[0]
        nodi = sorted(set(nodi))
        out = {}
        for i in range(0, len(nodi), 25):
            gruppo = nodi[i:i + 25]
            dist = dijkstra(M, indices=gruppo)[:, nodi]
            for k, a in enumerate(gruppo):
                for j, b in enumerate(nodi):
                    out[(a, b)] = float(dist[k, j])
        return out

    def percorso(self, a, b, ora, semafori_s=None):
        """Percorso piu' veloce da a a b: {'secondi', 'tratti': [indici], 'semafori': n, 'lunghezza_m'} (o None se non esiste)."""
        from scipy.sparse.csgraph import dijkstra
        np = self.np
        M, sel, archi = self.matrice_pesi(ora, semafori_s)
        dist, pred = dijkstra(M, indices=a, return_predecessors=True)
        if not np.isfinite(dist[b]):
            return None
        da_arco = {(int(archi[i, 0]), int(archi[i, 1])): int(archi[i, 3]) for i in sel}
        tratti, v, sem = [], b, 0
        while v != a:
            u = int(pred[v])
            e = da_arco[(u, v)]
            tratti.append(e)
            sem += int(self.semafori_nodo[v] or self.semafori_tratto[e])
            v = u
        tratti.reverse()
        return {"secondi": float(dist[b]), "tratti": tratti, "semafori": sem, "lunghezza_m": float(self.lunghezza[tratti].sum()) if tratti else 0.0}

    def copertura(self, tratti, ora):
        """Quota della lunghezza dei tratti con un sensore 5T all'ora o un k della propria zona."""
        np = self.np
        h = self._ora(ora)
        if h == "libero" or not tratti:
            return 0.0
        t = np.array(tratti)
        coperto = ~np.isnan(self.v_sensore[h][t]) | self.k_proprio[h][t]
        return float(self.lunghezza[t][coperto].sum() / max(self.lunghezza[t].sum(), 1e-9))


_CORREZIONE = {}


def fascia_di_ora(ore):
    """Fascia oraria dei risultati (come lo script 27) per un'ora locale, anche con i decimali (17.5 = 17:30)."""
    for da, a, nome in ((7, 9, "punta_mattina"), (9, 16, "giorno"), (16, 19, "punta_sera"), (19, 24, "sera")):
        if da <= ore < a:
            return nome
    return "notte"


def correzione_tempi_mezzi():
    """data/processed/correzione_tempi_mezzi.json (script 105) o None se non c'e' ancora."""
    if "j" not in _CORREZIONE:
        p = RADICE / "data" / "processed" / "correzione_tempi_mezzi.json"
        _CORREZIONE["j"] = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    return _CORREZIONE["j"]


def fattore_controllo():
    """f = 1 / (1 + mediana dell'errore con segno del controllo con TomTom, script 108): la stima aperta e' piu' veloce di TomTom, l'auto vera e' piu' lenta (§6.2).
    Se il riepilogo non c'e' (primo giro), 1: nessuna correzione."""
    f = RADICE / "data" / "processed" / "controllo_navigatori_riepilogo.json"
    if not f.is_file():
        return 1.0
    return 1.0 / (1.0 + json.loads(f.read_text(encoding="utf-8"))["mediana_errore_con_segno_pct"] / 100.0)


def tempo_mezzi_corretto(tp_orario_min, fascia="punta_mattina"):
    """Tempo coi mezzi corretto con le misure (giro L23, script 105): tempo da orario + attesa in piu' + ritardo per minuto x quota a bordo x tempo da orario.
    Senza il file dello script 105 ritorna il tempo da orario (e chi chiama lo dice)."""
    j = correzione_tempi_mezzi()
    if not j or tp_orario_min is None:
        return tp_orario_min
    f = j["per_fascia"][fascia]
    return tp_orario_min + f["attesa_in_piu_min"] + f["ritardo_per_minuto"] * f["quota_a_bordo"] * tp_orario_min


def imposta_java(jdk=None):
    """Java per r5py (serve 21 o piu'): JAVA_HOME gia' impostato non si tocca; altrimenti la cartella data/otp/jdk-... se esiste
    (setdefault), altrimenti il Java del sistema (PATH). Se non c'e' nessuno dei due, si ferma con un messaggio chiaro."""
    import os
    import shutil
    if jdk is not None:
        cartelle = [Path(jdk), *sorted(Path(jdk).parent.glob("jdk-*"))]
        trovata = next((c for c in cartelle if c.is_dir()), None)
        if trovata:
            os.environ.setdefault("JAVA_HOME", str(trovata))
    if not os.environ.get("JAVA_HOME") and not shutil.which("java"):
        sys.exit("ERRORE: Java non trovato. r5py ha bisogno di Java 21 o piu': installalo (es. Temurin 21) oppure metti un JRE in data/otp/ "
                 "e imposta JAVA_HOME.")


def carica_script(nome_file):
    """Carica scripts/<nome_file> come modulo (serve per i nomi che iniziano con un numero)."""
    percorso = AQUI / nome_file
    if str(AQUI) not in sys.path:
        sys.path.insert(0, str(AQUI))
    spec = importlib.util.spec_from_file_location(Path(nome_file).stem.replace("-", "_"), percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class Controlli:
    """Controlli di uno script. bloccante=True solo per errori di struttura (file vuoti, somme che non
    tornano, valori negativi): allora lo script si ferma. Tutto il resto e' un AVVISO: si stampa, si
    scrive nel rapporto e lo script continua."""

    def __init__(self):
        self.righe = []

    def __call__(self, nome, ok, bloccante=False, dettaglio=""):
        stato = "OK" if ok else ("ERRORE" if bloccante else "AVVISO")
        riga = f"{stato:6s} {nome}" + (f" — {dettaglio}" if dettaglio else "")
        self.righe.append(riga)
        print("  " + riga)
        if not ok and bloccante:
            sys.exit(f"ERRORE BLOCCANTE: {nome} {dettaglio}")
        return ok

    def avvisi(self):
        return [r for r in self.righe if r.startswith("AVVISO")]


if __name__ == "__main__":
    c = Controlli()
    d = haversine_m(45.06120, 7.67780, 45.07158, 7.66586)
    c("haversine Porta Nuova - Porta Susa circa 1.487 m", abs(d - 1487) < 5, dettaglio=f"{d:.0f} m")
    t1 = ora_locale(datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc))
    t2 = ora_locale(datetime(2026, 10, 25, 1, 30, tzinfo=timezone.utc))
    c("ora legale: 25/10 00:30 UTC e 01:30 UTC = 02:30 italiane", t1.strftime("%H:%M") == t2.strftime("%H:%M") == "02:30")
    p = percentile_rank({"a": 1, "b": 2, "c": 2, "d": 3})
    c("percentile di [1,2,2,3] = 0, 50, 50, 100", [round(p[k]) for k in "abcd"] == [0, 50, 50, 100])
    c("zone centrali Q001-Q009", ZONE_CENTRALI[0] == "Q001" and ZONE_CENTRALI[-1] == "Q009" and len(ZONE_CENTRALI) == 9)
    print("avvisi:", len(c.avvisi()))
