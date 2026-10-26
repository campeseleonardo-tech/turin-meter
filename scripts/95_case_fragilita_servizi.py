#!/usr/bin/env python3
"""95_case_fragilita_servizi.py - Risultato E: prezzo delle case x fragilita' x servizi, solo Torino. SOLA LETTURA.

Unita' = zona OMI di Torino. Le sezioni di censimento si aggregano nella zona con media pesata per abitanti.
Domande (sviluppo/piani/PIANO_RISULTATI.md, parte E):
  E1  Si paga per i servizi? Spearman fra prezzo e servizi (una zona = un punto), retta di tendenza, residui:
      le 5 zone piu' care e le 5 piu' convenienti rispetto ai servizi.
  E2  Doppio svantaggio: zone con fragilita' nel 20% piu' alto E servizi nel 20% piu' basso. Lo stesso conto per
      sezione (quintili delle sezioni di Torino abitate, fuori le zone grigie sotto 1.000 ab/km2, come la mappa).
  E4  (giro L9) Correlazione PARZIALE sui ranghi a parita' di distanza da Piazza Castello, per prezzo-servizi, fragilita'-servizi e
      prezzo-fragilita', con intervallo al 95% (ricampionamento delle zone, seme fisso): «regge» solo se l'intervallo non contiene lo 0.
      E in E2: il doppio svantaggio confrontato col caso (quanto ci si aspetterebbe se fragilita' alta e servizi bassi fossero indipendenti).
  E3  Il valore della metro: zone con una fermata M1 entro 600 m dal centro della zona contro le altre, a pari
      distanza da Piazza Castello (fasce di 2 km). Differenza fra zone, NON effetto causale.

Regole fissate PRIMA di vedere i numeri (qui sotto, in COSTANTI): zone con meno di 500 abitanti fuori; soglie 80%/20%;
metro entro 600 m; fasce di 2 km. Mai la nazionalita': non entra in nessun dato.

Input (sola lettura): data/processed/sezioni_torino.json (05), vulnerabilita.json (19), accessibilita.json (18),
omi_zone.json (08), data/raw/gtt_gtfs_*.zip (fermate con route_type = 1, la metropolitana).
Uscite: data/processed/case_fragilita_servizi.json, docs/rapporti/RAPPORTO_CASE_FRAGILITA_SERVIZI.txt.

Uso:
  python scripts\\95_case_fragilita_servizi.py
  python scripts\\95_case_fragilita_servizi.py --prova            (dati finti nello stesso formato, in una cartella temporanea)
  python scripts\\95_case_fragilita_servizi.py --radice CARTELLA  (altra radice con data/ e docs/: per le prove)
"""
import argparse
import bisect
import csv
import io
import json
import math
import random
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402

PRO_COM_TORINO = 1272
GRUPPI = ("scuole", "salute", "cibo", "fermate", "verde")
MIN_ABITANTI_ZONA = 500          # zone piu' piccole fuori
QUANTILE_ALTO, QUANTILE_BASSO = 0.8, 0.2   # fragilita' nel 20% piu' alto, servizi nel 20% piu' basso
DENS_MIN = 1000                  # come la mappa: sotto questi abitanti per km2 la sezione e' grigia
RAGGIO_METRO_M = 600
FASCIA_M = 2000
TIPOLOGIA_PREZZO = "ab"          # abitazioni civili; prezzo = centro della forbice di acquisto (cmin, cmax)
AVVISO_SENZA_ZONA = 0.01         # quota di sezioni senza zona OMI oltre la quale c'e' un AVVISO
SEME = 95


# ---------------------------------------------------------------- statistica semplice
def quantile_soglia(valori, q):
    """Stessa regola delle soglie della mappa: v[min(n-1, floor(q*n))] sui valori ordinati."""
    v = sorted(valori)
    return v[min(len(v) - 1, int(q * len(v)))] if v else None


def ranghi(v):
    """Ranghi medi (1..n), i pari merito dividono la posizione."""
    ordine = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(ordine):
        j = i
        while j + 1 < len(ordine) and v[ordine[j + 1]] == v[ordine[i]]:
            j += 1
        for k in range(i, j + 1):
            r[ordine[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def spearman(x, y):
    return pearson(ranghi(x), ranghi(y))


def parziale(x, y, z):
    """Correlazione parziale sui ranghi (Spearman) fra x e y a parita' di z: (r_xy - r_xz r_yz) / sqrt((1 - r_xz^2)(1 - r_yz^2))."""
    rxy, rxz, ryz = spearman(x, y), spearman(x, z), spearman(y, z)
    if None in (rxy, rxz, ryz):
        return None
    den = math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    return (rxy - rxz * ryz) / den if den else None


def ic_parziale(x, y, z, n_boot=2000):
    """Intervallo al 95% della correlazione parziale, ricampionando le zone (seme fisso)."""
    rnd = random.Random(SEME)
    n = len(x)
    ris = []
    for _ in range(n_boot):
        idx = [rnd.randrange(n) for _ in range(n)]
        r = parziale([x[i] for i in idx], [y[i] for i in idx], [z[i] for i in idx])
        if r is not None:
            ris.append(r)
    ris.sort()
    return (ris[int(0.025 * len(ris))], ris[min(len(ris) - 1, int(0.975 * len(ris)))]) if ris else (None, None)


def retta(x, y):
    """Minimi quadrati: y = a + b*x."""
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx if sxx else 0.0
    return my - b * mx, b


def ic_bootstrap(x, y, n_boot=2000):
    """Intervallo al 95% del rho di Spearman, ricampionando le zone (seme fisso)."""
    rnd = random.Random(SEME)
    n = len(x)
    ris = []
    for _ in range(n_boot):
        idx = [rnd.randrange(n) for _ in range(n)]
        r = spearman([x[i] for i in idx], [y[i] for i in idx])
        if r is not None:
            ris.append(r)
    ris.sort()
    return (ris[int(0.025 * len(ris))], ris[min(len(ris) - 1, int(0.975 * len(ris)))]) if ris else (None, None)


# ---------------------------------------------------------------- geometria
def punto_in_anello(lat, lon, anello):
    dentro = False
    j = len(anello) - 1
    for i in range(len(anello)):
        yi, xi = anello[i]
        yj, xj = anello[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro


def area_anello(anello):
    """Area col metodo dei lacci (gradi quadrati: serve solo per confrontare anelli)."""
    s = 0.0
    for i in range(len(anello)):
        y1, x1 = anello[i]
        y2, x2 = anello[(i + 1) % len(anello)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def centroide_anello(anello):
    a = 0.0
    cx = cy = 0.0
    for i in range(len(anello)):
        y1, x1 = anello[i]
        y2, x2 = anello[(i + 1) % len(anello)]
        f = x1 * y2 - x2 * y1
        a += f
        cx += (x1 + x2) * f
        cy += (y1 + y2) * f
    if a == 0:
        return (sum(p[0] for p in anello) / len(anello), sum(p[1] for p in anello) / len(anello))
    return (cy / (3 * a), cx / (3 * a))   # (lat, lon)


def centro_sezione(rings):
    lat = [p[0] for a in rings for p in a]
    lon = [p[1] for a in rings for p in a]
    return ((min(lat) + max(lat)) / 2, (min(lon) + max(lon)) / 2)


# ---------------------------------------------------------------- lettura dati
def leggi_json(percorso):
    if not percorso.is_file():
        comuni.richiedi_fonte(percorso)      # omi_zone.json: fuori da git (L12), il messaggio dice dove scaricare la fonte
        sys.exit(f"Manca {percorso}")
    return json.loads(percorso.read_text(encoding="utf-8"))


def ultimo_gtfs(raw):
    trovati = sorted(raw.glob("gtt_gtfs_*.zip"))
    if not trovati:
        sys.exit(f"GTFS non trovato in {raw} (gtt_gtfs_*.zip)")
    return trovati[-1]


def fermate_metro(percorso_zip):
    """Coordinate (lat, lon) delle fermate servite da linee con route_type = 1 (metropolitana)."""
    with zipfile.ZipFile(percorso_zip) as zf:
        def righe(nome):
            with zf.open(nome) as f:
                yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
        rotte = {r["route_id"] for r in righe("routes.txt") if r["route_type"] == "1"}
        viaggi = {r["trip_id"] for r in righe("trips.txt") if r["route_id"] in rotte}
        ferme = {r["stop_id"] for r in righe("stop_times.txt") if r["trip_id"] in viaggi}
        return [(float(r["stop_lat"]), float(r["stop_lon"])) for r in righe("stops.txt") if r["stop_id"] in ferme]


def punteggio_servizi(sezioni, acc):
    """«Tutti i servizi» a piedi come la mappa: per ogni gruppo il percentile a posizione media fra le sezioni di
    Torino abitate (valore mancante = 0), poi media dei 5 percentili x 100."""
    val = {g: {s["id"]: acc.get(s["id"], {}).get(g) or 0 for s in sezioni} for g in GRUPPI}
    perc = {}
    for g in GRUPPI:
        ordinati = sorted(val[g].values())
        n = len(ordinati)
        perc[g] = {sid: (bisect.bisect_left(ordinati, x) + bisect.bisect_right(ordinati, x)) / 2 / n for sid, x in val[g].items()}
    return {s["id"]: 100.0 * sum(perc[g][s["id"]] for g in GRUPPI) / len(GRUPPI) for s in sezioni}


# ---------------------------------------------------------------- calcolo
def calcola(radice, c):
    P = radice / "data" / "processed"
    sez_tutte = leggi_json(P / "sezioni_torino.json")
    vuln = leggi_json(P / "vulnerabilita.json")
    acc_data = leggi_json(P / "accessibilita.json")
    omi = leggi_json(P / "omi_zone.json")
    metro = fermate_metro(ultimo_gtfs(radice / "data" / "raw"))

    torino = [s for s in sez_tutte if s["c"] == PRO_COM_TORINO and s["p"] > 0]
    c("ci sono sezioni di Torino abitate", len(torino) > 0, bloccante=True, dettaglio=f"{len(torino)}")
    tot_ab = sum(s["p"] for s in torino)
    v_sez = {x["id"]: x["v"] for x in vuln["sezioni"] if x.get("v") is not None and x.get("tipo", "residenziale") == "residenziale"}
    con_serv = sum(1 for x in vuln["sezioni"] if "serv" in (x.get("c") or {}) or "verde" in (x.get("c") or {}))
    c("l'indice di vulnerabilita' e' solo censimento (senza servizi e verde: altrimenti il confronto con i servizi e' circolare)",
      con_serv <= 0.01 * max(1, len(vuln["sezioni"])), dettaglio=f"{con_serv} sezioni con serv/verde nell'indice")
    acc = {x["id"]: (x.get("piedi", {}) or {}).get("15", {}) or {} for x in acc_data.get("sezioni", [])}
    punt = punteggio_servizi(torino, acc)

    # --- zone OMI di Torino con prezzo
    zone = []
    senza_prezzo = []
    for gruppo in omi:
        if gruppo.get("c") != PRO_COM_TORINO:
            continue
        for z in gruppo["zone"]:
            ab = (z.get("v") or {}).get(TIPOLOGIA_PREZZO)
            rings = [r for r in z.get("g", []) if len(r) >= 3]
            if not rings:
                continue
            if not ab or ab[0] is None or ab[1] is None:
                senza_prezzo.append(z["z"])
                prezzo = None
            else:
                prezzo = (ab[0] + ab[1]) / 2
            zone.append({"cod": z["z"], "nome": f'{z["z"]} {z.get("n", "")}'.strip(), "prezzo": prezzo, "rings": rings,
                         "area": {i: area_anello(r) for i, r in enumerate(rings)}})
    c("ci sono zone OMI di Torino", len(zone) > 0, bloccante=True, dettaglio=f"{len(zone)}")

    # --- sezione -> zona: centro della sezione dentro il poligono (a parita', la zona con l'anello piu' piccolo)
    assegn = {}
    senza_zona = []
    for s in torino:
        la, lo = centro_sezione(s["g"])
        migliori = []
        for k, z in enumerate(zone):
            for i, r in enumerate(z["rings"]):
                if punto_in_anello(la, lo, r):
                    migliori.append((z["area"][i], k))
        if migliori:
            assegn[s["id"]] = min(migliori)[1]
        else:
            senza_zona.append(s["id"])
    quota_senza = len(senza_zona) / len(torino)
    c("sezioni senza zona OMI sotto l'1%", quota_senza <= AVVISO_SENZA_ZONA,
      dettaglio=f"{len(senza_zona)} su {len(torino)} ({quota_senza * 100:.2f}%)")

    # --- valori di zona (medie pesate per abitanti)
    for z in zone:
        z["ab"] = 0
        z["_pv"] = z["_wv"] = z["_ps"] = 0.0
    for s in torino:
        k = assegn.get(s["id"])
        if k is None:
            continue
        z = zone[k]
        z["ab"] += s["p"]
        z["_ps"] += s["p"] * punt[s["id"]]
        if s["id"] in v_sez:
            z["_pv"] += s["p"] * v_sez[s["id"]]
            z["_wv"] += s["p"]
    ab_assegnati = sum(z["ab"] for z in zone)
    c("gli abitanti delle zone + quelli delle sezioni senza zona = abitanti di Torino",
      ab_assegnati + sum(s["p"] for s in torino if s["id"] in set(senza_zona)) == tot_ab, bloccante=True,
      dettaglio=f"{ab_assegnati:,} + senza zona = {tot_ab:,}")
    for z in zone:
        z["servizi"] = z["_ps"] / z["ab"] if z["ab"] else None
        z["fragilita"] = z["_pv"] / z["_wv"] if z["_wv"] else None
    piccole = [z for z in zone if z["ab"] < MIN_ABITANTI_ZONA]
    c_prezzo = [z for z in zone if z["ab"] >= MIN_ABITANTI_ZONA and z["prezzo"] is None]
    c("zone con almeno 500 abitanti senza prezzo OMI (escluse)", not c_prezzo, dettaglio=", ".join(z["cod"] for z in c_prezzo) or "nessuna")
    ok = [z for z in zone if z["ab"] >= MIN_ABITANTI_ZONA and z["prezzo"] is not None and z["fragilita"] is not None]
    c("nessun prezzo nullo nelle zone usate", all(z["prezzo"] and z["prezzo"] > 0 for z in ok), bloccante=True, dettaglio=f"{len(ok)} zone usate")
    c("abbastanza zone per una correlazione (almeno 10)", len(ok) >= 10, bloccante=True)
    c("servizi e fragilita' di zona fra 0 e 100", all(0 <= z["servizi"] <= 100 and 0 <= z["fragilita"] <= 100 for z in ok), bloccante=True)
    ab_usati = sum(z["ab"] for z in ok)
    for z in ok:      # centro della zona (anello piu' grande) e distanza da Piazza Castello: servono alla correlazione parziale (E4) e alla metro (E3)
        z["centro"] = centroide_anello(z["rings"][max(z["area"], key=z["area"].get)])
        z["d_castello"] = comuni.haversine_m(z["centro"][0], z["centro"][1], comuni.CENTRO_LAT, comuni.CENTRO_LON)

    # --- E1
    x = [z["servizi"] for z in ok]
    y = [z["prezzo"] for z in ok]
    rho = spearman(x, y)
    lo_ic, hi_ic = ic_bootstrap(x, y)
    a, b = retta(x, y)
    for z in ok:
        z["prezzo_atteso"] = a + b * z["servizi"]
        z["residuo"] = z["prezzo"] - z["prezzo_atteso"]
    per_res = sorted(ok, key=lambda z: z["residuo"])
    riga = lambda z: {"zona": z["nome"], "abitanti": z["ab"], "prezzo": round(z["prezzo"]), "servizi": round(z["servizi"], 1),
                      "prezzo_atteso": round(z["prezzo_atteso"]), "residuo": round(z["residuo"])}
    e1 = {"n_zone": len(ok), "spearman": round(rho, 3) if rho is not None else None,
          "spearman_ic95": [round(lo_ic, 3), round(hi_ic, 3)] if lo_ic is not None else None,
          "retta": {"intercetta_eur_m2": round(a, 1), "pendenza_eur_m2_per_punto_servizi": round(b, 2)},
          "piu_care_dei_servizi": [riga(z) for z in reversed(per_res[-5:])],
          "piu_convenienti_dei_servizi": [riga(z) for z in per_res[:5]]}

    # --- E4: legami a parita' di distanza dal centro (L9): correlazione parziale sui ranghi, intervallo al 95%, «regge» se l'intervallo non contiene lo 0
    dist = [z["d_castello"] for z in ok]
    var = {"prezzo": [z["prezzo"] for z in ok], "servizi": [z["servizi"] for z in ok], "fragilita": [z["fragilita"] for z in ok]}
    e4 = {"controllo": "distanza dal centro di zona a Piazza Castello (m)", "n_zone": len(ok),
          "regola": "correlazione parziale sui ranghi (Spearman) a parita' di distanza da Piazza Castello; intervallo al 95% per ricampionamento delle zone (2.000 volte, seme 95); regge solo se l'intervallo non contiene lo 0",
          "legami": []}
    for nome, a_, b_ in (("prezzo-servizi", "prezzo", "servizi"), ("fragilita-servizi", "fragilita", "servizi"), ("prezzo-fragilita", "prezzo", "fragilita")):
        s_ = spearman(var[a_], var[b_])
        s_lo, s_hi = ic_bootstrap(var[a_], var[b_])
        p_ = parziale(var[a_], var[b_], dist)
        p_lo, p_hi = ic_parziale(var[a_], var[b_], dist)
        e4["legami"].append({"legame": nome, "spearman": round(s_, 3), "spearman_ic95": [round(s_lo, 3), round(s_hi, 3)], "regge_semplice": bool(s_lo > 0 or s_hi < 0),
                             "parziale": round(p_, 3), "parziale_ic95": [round(p_lo, 3), round(p_hi, 3)], "regge": bool(p_lo > 0 or p_hi < 0)})
    a_fs, b_fs = retta(var["fragilita"], var["servizi"])        # L9b: retta di tendenza del grafico principale della scheda 5 (servizi = a + b x fragilita')
    e4["retta_fragilita_servizi"] = {"intercetta_servizi": round(a_fs, 2), "pendenza_servizi_per_punto_fragilita": round(b_fs, 3)}
    c("la correlazione semplice prezzo-servizi dell'E4 coincide con quella dell'E1", abs(e4["legami"][0]["spearman"] - e1["spearman"]) < 1e-9, bloccante=True)

    # --- E2 per zona (soglie fissate sulle zone usate)
    s_frag = quantile_soglia([z["fragilita"] for z in ok], QUANTILE_ALTO)
    s_serv = quantile_soglia([z["servizi"] for z in ok], QUANTILE_BASSO)
    doppie = [z for z in ok if z["fragilita"] > s_frag and z["servizi"] <= s_serv]
    doppie.sort(key=lambda z: -z["ab"])
    # per sezione: quintili sulle sezioni di Torino abitate con indice, fuori le zone grigie
    ref = [s for s in torino if s["id"] in v_sez and s["p"] / max(s.get("a", 0), 0.0005) >= DENS_MIN]
    sf = quantile_soglia([v_sez[s["id"]] for s in ref], QUANTILE_ALTO)
    ss = quantile_soglia([punt[s["id"]] for s in ref], QUANTILE_BASSO)
    classi = {"tutte_e_due": [0, 0], "solo_fragilita": [0, 0], "solo_servizi": [0, 0], "nessuna": [0, 0]}
    for s in ref:
        f_alta = v_sez[s["id"]] > sf
        s_bassi = punt[s["id"]] <= ss
        k = "tutte_e_due" if f_alta and s_bassi else "solo_fragilita" if f_alta else "solo_servizi" if s_bassi else "nessuna"
        classi[k][0] += 1
        classi[k][1] += s["p"]
    c("le 4 classi delle sezioni sommano alle sezioni di riferimento",
      sum(v[0] for v in classi.values()) == len(ref) and sum(v[1] for v in classi.values()) == sum(s["p"] for s in ref), bloccante=True)
    # confronto col caso (L9): se fragilita' alta e servizi bassi fossero indipendenti, la quota attesa sarebbe il prodotto delle due quote (pesate per abitanti)
    tot_ref = sum(s["p"] for s in ref)
    p_f = sum(s["p"] for s in ref if v_sez[s["id"]] > sf) / tot_ref
    p_s = sum(s["p"] for s in ref if punt[s["id"]] <= ss) / tot_ref
    osservata = classi["tutte_e_due"][1] / tot_ref
    caso = {"regola": "quota attesa per caso = (quota di residenti con fragilita' alta) x (quota con servizi bassi), se le due condizioni fossero indipendenti",
            "quota_fragilita_alta": round(p_f, 4), "quota_servizi_bassi": round(p_s, 4), "quota_attesa_per_caso": round(p_f * p_s, 4),
            "quota_osservata": round(osservata, 4), "volte_il_caso": round(osservata / (p_f * p_s), 2)}
    e2 = {"soglie_fissate": {"fragilita_sopra": round(s_frag, 2), "servizi_fino_a": round(s_serv, 2),
                              "regola": "fragilita' nel 20% piu' alto e servizi nel 20% piu' basso (sulle zone usate); per sezione: quintili delle sezioni di Torino con almeno 1.000 ab/km2"},
          "zone": [{"zona": z["nome"], "abitanti": z["ab"], "fragilita": round(z["fragilita"], 1), "servizi": round(z["servizi"], 1),
                    "prezzo": round(z["prezzo"])} for z in doppie],
          "residenti_zone_doppio_svantaggio": sum(z["ab"] for z in doppie),
          "quota_residenti_zone_usate": round(sum(z["ab"] for z in doppie) / ab_usati, 4),
          "sezioni": {"soglia_fragilita_sopra": round(sf, 2), "soglia_servizi_fino_a": round(ss, 2),
                      "sezioni_di_riferimento": len(ref), "residenti_di_riferimento": sum(s["p"] for s in ref),
                      "classi": {k: {"sezioni": v[0], "residenti": v[1]} for k, v in classi.items()},
                      "residenti_doppio_svantaggio": classi["tutte_e_due"][1],
                      "quota_residenti_di_riferimento": round(classi["tutte_e_due"][1] / sum(s["p"] for s in ref), 4),
                      "confronto_col_caso": caso}}

    # --- E3: metro
    c("fermate della metropolitana trovate nel GTFS (la M1 ne ha circa 23)", len(metro) >= 15, dettaglio=f"{len(metro)}")
    for z in ok:
        la, lo = z["centro"]
        z["d_metro"] = min((comuni.haversine_m(la, lo, m[0], m[1]) for m in metro), default=None)
        z["metro"] = z["d_metro"] is not None and z["d_metro"] < RAGGIO_METRO_M
        z["fascia"] = int(z["d_castello"] // FASCIA_M)
    fasce = []
    for f in sorted({z["fascia"] for z in ok}):
        zf = [z for z in ok if z["fascia"] == f]
        con = [z for z in zf if z["metro"]]
        senza = [z for z in zf if not z["metro"]]
        media = lambda zz: round(sum(z["prezzo"] for z in zz) / len(zz)) if zz else None
        fasce.append({"fascia_km": f"{f * FASCIA_M // 1000}-{(f + 1) * FASCIA_M // 1000}", "con_metro": {"zone": len(con), "prezzo_medio": media(con)},
                      "senza_metro": {"zone": len(senza), "prezzo_medio": media(senza)},
                      "differenza": (media(con) - media(senza)) if con and senza else None})
    e3 = {"regola": f"zone con una fermata M1 a meno di {RAGGIO_METRO_M} m dal centro della zona (centroide dell'anello piu' grande), "
                    f"confronto a pari distanza da Piazza Castello, fasce di {FASCIA_M // 1000} km; prezzo medio = media semplice fra zone",
          "zone_con_metro": sorted(z["nome"] for z in ok if z["metro"]),
          "fasce": fasce,
          "avvertenza": "differenza fra zone, non effetto causale (un solo semestre OMI, zone grandi, quotazioni e non compravendite)"}

    zone_out = [{"zona": z["nome"], "abitanti": z["ab"], "prezzo": round(z["prezzo"]), "servizi": round(z["servizi"], 1),
                 "fragilita": round(z["fragilita"], 1), "residuo": round(z["residuo"]),
                 "distanza_castello_m": round(z["d_castello"]), "distanza_metro_m": round(z["d_metro"]) if z["d_metro"] is not None else None,
                 "metro_600m": z["metro"]} for z in sorted(ok, key=lambda z: z["nome"])]
    return {
        "generato_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "unita": "zona OMI di Torino; media pesata per abitanti delle sezioni (centro della sezione dentro la zona)",
        "fonti": "OMI 2025/2 (abitazioni civili, centro della forbice di acquisto), censimento ISTAT 2021, indice di vulnerabilita' (script 19), servizi a piedi 15' (script 18), GTFS GTT",
        "avvertenze": ["OMI = quotazioni, non compravendite; zone grandi; un solo semestre", "correlazione, non causa",
                       "l'indice di vulnerabilita' non e' una misura di reddito"],
        "regole_fissate_prima": {"abitanti_minimi_zona": MIN_ABITANTI_ZONA, "quantili": [QUANTILE_BASSO, QUANTILE_ALTO],
                                 "metro_m": RAGGIO_METRO_M, "fascia_m": FASCIA_M},
        "conteggi": {"sezioni_torino": len(torino), "abitanti_torino": tot_ab, "zone_omi": len(zone), "zone_usate": len(ok),
                     "abitanti_zone_usate": ab_usati, "zone_sotto_500": [z["nome"] for z in piccole], "zone_senza_prezzo": senza_prezzo,
                     "sezioni_senza_zona": len(senza_zona), "fermate_metro": len(metro)},
        "e1_si_paga_per_i_servizi": e1, "e2_doppio_svantaggio": e2, "e3_valore_metro": e3, "e4_a_parita_di_distanza": e4, "zone": zone_out,
    }


def rapporto(ris, righe_controlli):
    n = ris["conteggi"]
    e1, e2, e3 = ris["e1_si_paga_per_i_servizi"], ris["e2_doppio_svantaggio"], ris["e3_valore_metro"]
    L = ["RAPPORTO CASE x FRAGILITA' x SERVIZI (script 95), solo Torino, unita' = zona OMI", f"generato {ris['generato_utc']}", "",
         f"Torino: {n['sezioni_torino']:,} sezioni abitate, {n['abitanti_torino']:,} abitanti; zone OMI {n['zone_omi']}, usate {n['zone_usate']} "
         f"({n['abitanti_zone_usate']:,} abitanti). Escluse (sotto 500 abitanti o senza prezzo): {', '.join(n['zone_sotto_500'] + n['zone_senza_prezzo']) or 'nessuna'}.",
         "Avvertenze: " + "; ".join(ris["avvertenze"]) + ".", "", "E1  SI PAGA PER I SERVIZI?"]
    ic = e1["spearman_ic95"]
    L.append(f"  Spearman prezzo-servizi = {e1['spearman']} su {e1['n_zone']} zone" + (f" (intervallo 95%: {ic[0]} / {ic[1]})" if ic else ""))
    L.append(f"  retta: prezzo = {e1['retta']['intercetta_eur_m2']} + {e1['retta']['pendenza_eur_m2_per_punto_servizi']} x punteggio servizi  (euro/m2)")
    for titolo, chiave in (("5 zone piu' care dei servizi (sopra la retta)", "piu_care_dei_servizi"), ("5 zone piu' convenienti (sotto la retta)", "piu_convenienti_dei_servizi")):
        L.append("  " + titolo + ":")
        for z in e1[chiave]:
            L.append(f"    {z['zona']:<28} prezzo {z['prezzo']:>6} atteso {z['prezzo_atteso']:>6} residuo {z['residuo']:>+6}  servizi {z['servizi']:>5}  abitanti {z['abitanti']:,}")
    L += ["", "E2  DOPPIO SVANTAGGIO (soglie fissate: fragilita' nel 20% piu' alto e servizi nel 20% piu' basso)",
          f"  zone: fragilita' > {e2['soglie_fissate']['fragilita_sopra']} e servizi <= {e2['soglie_fissate']['servizi_fino_a']}"]
    for z in e2["zone"]:
        L.append(f"    {z['zona']:<28} abitanti {z['abitanti']:>7,}  fragilita' {z['fragilita']:>5}  servizi {z['servizi']:>5}  prezzo {z['prezzo']:>6}")
    L.append(f"  residenti nelle zone in doppio svantaggio: {e2['residenti_zone_doppio_svantaggio']:,} ({e2['quota_residenti_zone_usate'] * 100:.1f}% dei residenti delle zone usate)")
    s = e2["sezioni"]
    L.append(f"  per sezione (quintili: fragilita' > {s['soglia_fragilita_sopra']}, servizi <= {s['soglia_servizi_fino_a']}; {s['sezioni_di_riferimento']:,} sezioni, "
             f"{s['residenti_di_riferimento']:,} residenti, fuori le zone grigie):")
    nomi = {"tutte_e_due": "tutte e due", "solo_fragilita": "solo fragilita' alta", "solo_servizi": "solo servizi bassi", "nessuna": "nessuna"}
    for k, v in s["classi"].items():
        L.append(f"    {nomi[k]:<22} {v['sezioni']:>5} sezioni  {v['residenti']:>8,} residenti")
    L.append(f"  torinesi in sezioni con entrambe le condizioni: {s['residenti_doppio_svantaggio']:,} ({s['quota_residenti_di_riferimento'] * 100:.1f}%)")
    cc = s["confronto_col_caso"]
    L.append(f"  confronto col caso: fragilita' alta {cc['quota_fragilita_alta'] * 100:.1f}% x servizi bassi {cc['quota_servizi_bassi'] * 100:.1f}% = {cc['quota_attesa_per_caso'] * 100:.2f}% attesi se fossero indipendenti; "
             f"osservati {cc['quota_osservata'] * 100:.2f}%: {cc['volte_il_caso']:.2f} volte il caso")
    e4 = ris["e4_a_parita_di_distanza"]
    L += ["", "E4  LEGAMI A PARITA' DI DISTANZA DAL CENTRO (correlazione parziale sui ranghi; intervallo 95% per ricampionamento, seme 95; regge solo se l'intervallo non contiene lo 0)",
          f"  controllo: {e4['controllo']}; {e4['n_zone']} zone"]
    for g in e4["legami"]:
        L.append(f"    {g['legame']:<18} Spearman {g['spearman']:+.3f} ({g['spearman_ic95'][0]:+.3f} / {g['spearman_ic95'][1]:+.3f})  |  a parita' di distanza {g['parziale']:+.3f} "
                 f"({g['parziale_ic95'][0]:+.3f} / {g['parziale_ic95'][1]:+.3f})  ->  {'REGGE' if g['regge'] else 'NON REGGE (l intervallo contiene lo 0)'}")
    L += ["", "E3  IL VALORE DELLA METRO", "  " + e3["regola"], "  zone con metro: " + (", ".join(e3["zone_con_metro"]) or "nessuna")]
    for f in e3["fasce"]:
        cm, sm = f["con_metro"], f["senza_metro"]
        L.append(f"    {f['fascia_km']:>5} km  con metro: {cm['zone']:>2} zone, {cm['prezzo_medio'] if cm['prezzo_medio'] is not None else '-':>6}  |  senza: {sm['zone']:>2} zone, "
                 f"{sm['prezzo_medio'] if sm['prezzo_medio'] is not None else '-':>6}  |  differenza {f['differenza'] if f['differenza'] is not None else '-'}")
    L += ["  DIFFERENZA FRA ZONE, NON EFFETTO CAUSALE.", "", "CONTROLLI"] + ["  " + r for r in righe_controlli]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- dati finti (--prova)
def dati_finti(radice):
    """Scrive in `radice` file nello stesso formato di quelli veri: griglia 30x30 di sezioni, 5x4 zone OMI, 5 fermate metro."""
    rnd = random.Random(SEME)
    P = radice / "data" / "processed"
    (radice / "data" / "raw").mkdir(parents=True, exist_ok=True)
    P.mkdir(parents=True, exist_ok=True)
    lat0, lon0, dl, dn = 45.03, 7.62, 0.0033, 0.0046
    sezioni, vuln, acc = [], [], []
    for i in range(30):
        for j in range(30):
            la, lo = lat0 + i * dl, lon0 + j * dn
            sid = f"1272{i:02d}{j:02d}"
            centro = math.hypot((la - 45.0711) / 0.04, (lo - 7.6857) / 0.06)
            serv = max(0.0, 1.0 - centro / 1.5 + rnd.uniform(-0.1, 0.1))
            blocco_vuoto = (i >= 22 and j < 5)   # una zona quasi disabitata: resta sotto i 500 abitanti
            p = rnd.randint(2, 6) if blocco_vuoto else rnd.randint(200, 1400)
            sezioni.append({"id": sid, "c": 1272, "p": p, "a": 0.05, "g": [[[la, lo], [la, lo + dn], [la + dl, lo + dn], [la + dl, lo], [la, lo]]]})
            vuln.append({"id": sid, "comune": 1272, "res": p, "v": round(100 * min(1, max(0, 0.9 - serv * 0.7 + rnd.uniform(-0.2, 0.2))), 1),
                         "c": {"occ": 0.5, "ist": 0.5, "aff": 0.5, "anz": 0.5}, "tipo": "residenziale"})
            acc.append({"id": sid, "piedi": {"15": {g: int(serv * k + rnd.uniform(0, 3)) for g, k in zip(GRUPPI, (12, 8, 40, 30, 6))}}})
    (P / "sezioni_torino.json").write_text(json.dumps(sezioni), encoding="utf-8")
    (P / "vulnerabilita.json").write_text(json.dumps({"origine": "CENSIMENTO", "sezioni": vuln}), encoding="utf-8")
    (P / "accessibilita.json").write_text(json.dumps({"sezioni": acc}), encoding="utf-8")
    zone = []
    for zi in range(4):
        for zj in range(6):
            la, lo = lat0 + zi * 7.5 * dl, lon0 + zj * 5 * dn
            la2, lo2 = la + 7.5 * dl, lo + 5 * dn
            centro = math.hypot((la + la2) / 2 - 45.0711, (lo + lo2) / 2 - 7.6857)
            prezzo = 4200 - 22000 * centro + rnd.uniform(-300, 300)
            v = {} if (zi, zj) == (3, 5) else {"ab": [round(prezzo * 0.85), round(prezzo * 1.15), 10.0, 14.0]}
            zone.append({"z": f"B{zi}{zj}", "n": "FINTA", "f": "B", "g": [[[la, lo], [la, lo2], [la2, lo2], [la2, lo], [la, lo]]], "v": v})
    (P / "omi_zone.json").write_text(json.dumps([{"c": 1272, "zone": zone}]), encoding="utf-8")
    ferme = [(45.0711 + k * 0.004, 7.62 + 0.0046 * 6 + k * 0.012) for k in range(-3, 4)]
    with zipfile.ZipFile(radice / "data" / "raw" / "gtt_gtfs_prova.zip", "w") as zf:
        zf.writestr("routes.txt", "route_id,route_type\nM1,1\nB1,3\n")
        zf.writestr("trips.txt", "route_id,trip_id\nM1,t1\nB1,t2\n")
        zf.writestr("stop_times.txt", "trip_id,stop_id\n" + "".join(f"t1,m{k}\n" for k in range(len(ferme))) + "t2,b0\n")
        zf.writestr("stops.txt", "stop_id,stop_lat,stop_lon\n" + "".join(f"m{k},{la},{lo}\n" for k, (la, lo) in enumerate(ferme)) + "b0,45.05,7.60\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true", help="dati finti nello stesso formato, in una cartella temporanea")
    ap.add_argument("--radice", help="radice alternativa con data/ e docs/ (le uscite vanno li')")
    args = ap.parse_args()
    if args.prova:
        radice = Path(tempfile.mkdtemp(prefix="gtt_prova95_"))
        dati_finti(radice)
        print(f"PROVA con dati finti in {radice}")
    else:
        radice = Path(args.radice) if args.radice else comuni.RADICE
    c = comuni.Controlli()
    ris = calcola(radice, c)
    out_json = radice / "data" / "processed" / "case_fragilita_servizi.json"
    out_txt = radice / "docs" / "rapporti" / "RAPPORTO_CASE_FRAGILITA_SERVIZI.txt"
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(ris, ensure_ascii=False, indent=1), encoding="utf-8")
    testo = rapporto(ris, c.righe)
    out_txt.write_text(testo, encoding="utf-8")
    print(testo)
    print(f"Scritto {out_json}\nScritto {out_txt}")
    if c.avvisi():
        print(f"\n{len(c.avvisi())} AVVISO/I: vedi sopra")


if __name__ == "__main__":
    main()
