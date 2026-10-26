#!/usr/bin/env python3
"""
81_auto_di_passaggio.py  -  Risultato 6 (correzioni del 20/10/2026): quante auto in entrata a Torino al
mattino passano accanto a ogni luogo di fermata (segnale c4). Preparato da Claude, da lanciare sul PC.

Perche'
-------
Il vecchio segnale c2 dava a ogni zona le auto che la TOCCAVANO (partenza o arrivo): per i quartieri di
Torino contava le auto che ci ARRIVANO, cioe' le destinazioni. Un parcheggio di interscambio serve invece
dove le auto PASSANO prima di arrivare. Qui si fanno "guidare" le auto del mattino sulla rete stradale
(stesso metodo V0 del traffico, script 42) e per ogni luogo si legge il flusso della strada accanto.

Cosa fa
-------
1. Domanda (microdati IMQ 2022, solo AUTO = conducente 03 + car sharing 21, partenza 06:00-09:59):
   - M_cint = auto che entrano a Torino (partenza fuori dai quartieri Q, arrivo in un quartiere Q);
   - M_tor  = auto dai quartieri periferici di Torino (Q fuori da Q001-Q009) verso Q001-Q009;
   - f_mattino = auto di M_cint che poi proseguono con un mezzo pubblico (chi gia' oggi lascia l'auto);
   - quota_mattino = f_mattino / M_cint.
   Decisione: i torinesi entrano nella domanda se M_tor >= SOGLIA_TORINESI x M_cint (default 0,25).
2. Instradamento delle auto della domanda (percorso piu' veloce, tutto o niente) sulla rete di
   data/processed/traffico_c/rete/ con i punti delle zone di data/processed/traffico_c/punti.json.
3. c4 di ogni luogo = flusso piu' alto (due versi sommati) fra i tratti entro RAGGIO_STRADA_M (100 m).
   Lo stesso per ogni parcheggio aperto, entro RAGGIO_PARCHEGGIO_M (300 m): serve alla validazione.
   Ripiego (solo se il passo 2 non si puo' fare): c4 = auto che PARTONO dalla zona del luogo (zone Q = 0).

Cosa legge
----------
  data/processed/imq/spostamenti.csv
  data/processed/risultato6_v2/luoghi.json, parcheggi.json, segnali.json (solo per i nomi delle strade nel rapporto)
  data/processed/traffico_c/rete/ (rete_auto.npz, rete_auto_metadati.json), data/processed/traffico_c/punti.json
  scripts/42_instradamento.py (funzione carica_domanda_nodi), scripts/rete_osm.py

Cosa scrive
-----------
  data/processed/risultato6_v2/auto_passaggio.json   (numeri della domanda, decisione, c4 per luogo)
  data/processed/risultato6_v2/auto_passaggio.npz    (flusso per arco)
  docs/rapporti/RAPPORTO_R6_AUTO_PASSAGGIO.txt

Come si lancia
--------------
  python scripts\\81_auto_di_passaggio.py --prova          (solo 30 origini: controllo veloce)
  python scripts\\81_auto_di_passaggio.py                  (giro completo)
  python scripts\\81_auto_di_passaggio.py --ripiego        (salta l'instradamento, usa il ripiego)
  python scripts\\81_auto_di_passaggio.py --torinesi si    (forza la decisione: si / no / auto)
"""
import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
P = RADICE / "data" / "processed" / "risultato6_v2"
SPOSTAMENTI = RADICE / "data" / "processed" / "imq" / "spostamenti.csv"
LUOGHI = P / "luoghi.json"
PARCHEGGI = P / "parcheggi.json"
SEGNALI = P / "segnali.json"
RETE_DIR = RADICE / "data" / "processed" / "traffico_c" / "rete"
PUNTI = RADICE / "data" / "processed" / "traffico_c" / "punti.json"
OUT = P / "auto_passaggio.json"
OUT_NPZ = P / "auto_passaggio.npz"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6_AUTO_PASSAGGIO.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

SOGLIA_TORINESI = 0.25
RAGGIO_STRADA_M = 100.0
RAGGIO_PARCHEGGIO_M = 300.0       # un parcheggio di interscambio sta spesso un po' indietro dalla strada
PASSO_DENSO_M = 20.0
ORIGINI_PROVA = 30
# strade d'ingresso che ci si aspetta in cima (solo per un AVVISO, mai per scegliere)
INGRESSI_ATTESI = ("francia", "unione sovietica", "genova", "giulio cesare", "tangenziale", "stupinigi",
                   "settimo", "torino", "moncalieri", "orbassano", "allamano", "regina margherita")


def minuti(orario):
    try:
        h, m = (orario or "").strip().split(":")[:2]
        return int(h) * 60 + int(m)
    except ValueError:
        return None


def peso(x):
    try:
        return float((x.get("PESO") or "").replace(",", "."))
    except ValueError:
        return 0.0


def leggi_domanda():
    """Ritorna i numeri della domanda e le righe utili (cintura e torinesi)."""
    m0, m1 = comuni.MATTINO_MINUTI
    cint, tor = [], []
    n = defaultdict(float)
    k = defaultdict(int)
    per_zona = defaultdict(lambda: [0.0, 0])
    with SPOSTAMENTI.open(encoding="utf-8-sig") as fh:
        for x in csv.DictReader(fh, delimiter=";"):
            mezzo = (x.get("MEZZO1") or "").strip()
            if mezzo not in comuni.MODI_AUTO_PERSONE:
                continue
            mp = minuti(x.get("ORA_PAR"))
            if mp is None or not (m0 <= mp <= m1):
                continue
            par = (x.get("COD_PAR") or "").strip()
            arr = (x.get("COD_ARR") or "").strip()
            p = peso(x)
            if not par or not arr:
                continue
            e_cint = (not par.startswith("Q")) and arr.startswith("Q")
            e_tor = par.startswith("Q") and par not in comuni.ZONE_CENTRALI and arr in comuni.ZONE_CENTRALI
            if not (e_cint or e_tor):
                continue
            if mezzo == "04":                     # passeggero: persone, non auto
                n["persone_cint" if e_cint else "persone_tor"] += p
                continue
            n["persone_cint" if e_cint else "persone_tor"] += p
            successivi = [(x.get("MEZZO2") or "").strip(), (x.get("MEZZO3") or "").strip()]
            gia_cambia = any(m in comuni.MEZZI_PUBBLICI for m in successivi)
            cella = (par, arr, mp // 60, p, 1)
            if e_cint:
                n["M_cint"] += p
                k["M_cint"] += 1
                cint.append(cella)
                per_zona[par][0] += p
                per_zona[par][1] += 1
                if gia_cambia:
                    n["f_mattino"] += p
                    k["f_mattino"] += 1
            else:
                n["M_tor"] += p
                k["M_tor"] += 1
                tor.append(cella)
    return n, k, cint, tor, per_zona


def instrada(rete, origini, max_origini=0):
    """Percorso piu' veloce, tutto o niente: stesso metodo del ciclo di main() in 42_instradamento.py
    (albero dei cammini minimi per ogni nodo di origine, poi somma della domanda sui sottoalberi).
    Ritorna (flusso per arco orientato, peso perso perche' non raggiungibile)."""
    import scipy.sparse as sp
    from scipy.sparse.csgraph import dijkstra

    archi = rete["archi"]
    N = len(rete["nodi_xy"])
    n_archi = len(archi)
    src = archi[:, 0].astype(np.int64)
    dst = archi[:, 1].astype(np.int64)
    w = archi[:, 2].astype(np.float64)
    chiave = src * N + dst
    order = np.argsort(chiave, kind="stable")
    chiave_s = chiave[order]
    primo = np.concatenate(([True], chiave_s[1:] != chiave_s[:-1]))
    pos_primo = np.nonzero(primo)[0]
    idx_arco_unico = order[pos_primo].copy()
    fine = np.append(pos_primo[1:], len(chiave_s))
    for u, (a0, a1) in enumerate(zip(pos_primo, fine)):
        if a1 - a0 > 1:
            sotto = order[a0:a1]
            idx_arco_unico[u] = sotto[np.argmin(w[sotto])]
    chiavi_uni = chiave_s[primo]
    src_u = (chiavi_uni // N).astype(np.int64)
    dst_u = (chiavi_uni % N).astype(np.int64)
    w_u = w[idx_arco_unico]
    tieni = src_u != dst_u
    M = sp.csr_matrix((w_u[tieni], (src_u[tieni], dst_u[tieni])), shape=(N, N))

    flusso = np.zeros(n_archi, dtype=np.float64)
    perso = 0.0
    lista = sorted(origini)
    if max_origini:
        lista = lista[:max_origini]
    t0 = time.time()
    batch = 10
    for i in range(0, len(lista), batch):
        gruppo = lista[i:i + batch]
        dist, pred = dijkstra(M, indices=gruppo, return_predecessors=True)
        for kk, o in enumerate(gruppo):
            di, pr = dist[kk], pred[kk]
            dest, val = origini[o]
            finiti = np.isfinite(di[dest])
            perso += float(val[~finiti].sum())
            q = np.zeros(N, dtype=np.float64)
            np.add.at(q, dest[finiti], val[finiti])
            ok = np.nonzero(np.isfinite(di))[0]
            ord_ = ok[np.argsort(-di[ok])].tolist()
            ql = q.tolist()
            prl = pr.tolist()
            for nn in ord_:
                pp = prl[nn]
                if pp >= 0:
                    ql[pp] += ql[nn]
            s = np.asarray(ql, dtype=np.float64)
            nz = np.nonzero(s)[0]
            if len(nz):
                prn = pr[nz]
                buoni = prn >= 0
                nz = nz[buoni]
                prn = prn[buoni]
                ch = prn.astype(np.int64) * N + nz
                pos = np.clip(np.searchsorted(chiavi_uni, ch), 0, len(chiavi_uni) - 1)
                okk = chiavi_uni[pos] == ch
                ar = idx_arco_unico[pos[okk]]
                flusso += np.bincount(ar, weights=s[nz[okk]], minlength=n_archi)
        if (i // batch) % 20 == 0:
            print(f"    {min(i + batch, len(lista)):,}/{len(lista):,} origini ({time.time() - t0:.0f} s)")
    return flusso, perso, len(lista)


def punti_densi(rete):
    """Punti lungo ogni tratto (vertici + un punto ogni PASSO_DENSO_M), con l'indice del tratto."""
    off, pts = rete["edge_off"], rete["edge_pts"]
    xs, ys, ee = [], [], []
    for e in range(len(off) - 1):
        p = pts[int(off[e]):int(off[e + 1])]
        if len(p) == 0:
            continue
        x = p[:, 1] * comuni.M_GRADO * np.cos(np.radians(comuni.LAT_RIF))
        y = p[:, 0] * comuni.M_GRADO
        xs.append(x[:1]); ys.append(y[:1]); ee.append([e])
        for j in range(len(p) - 1):
            L = float(np.hypot(x[j + 1] - x[j], y[j + 1] - y[j]))
            k = max(1, int(L // PASSO_DENSO_M))
            t = np.arange(1, k + 1) / k
            xs.append(x[j] + (x[j + 1] - x[j]) * t)
            ys.append(y[j] + (y[j + 1] - y[j]) * t)
            ee.append([e] * k)
    return np.concatenate(xs), np.concatenate(ys), np.concatenate([np.asarray(v, dtype=np.int64) for v in ee])


def c4_per_punti(rete, flusso_archi, punti, raggio):
    """punti = lista di (id, lat, lon). Per ognuno il flusso (due versi) del tratto piu' trafficato entro raggio."""
    from scipy.spatial import cKDTree
    n_edge = len(rete["edge_a"])
    flusso_edge = np.bincount(rete["archi"][:, 3].astype(np.int64), weights=flusso_archi, minlength=n_edge)
    xs, ys, ee = punti_densi(rete)
    albero = cKDTree(np.column_stack([xs, ys]))
    out = {}
    for ident, lat, lon in punti:
        vicini = albero.query_ball_point(comuni.proietta(lat, lon), raggio)
        if not vicini:
            out[ident] = {"c4": 0, "tratto": None}
            continue
        edges = np.unique(ee[vicini])
        best = edges[np.argmax(flusso_edge[edges])]
        out[ident] = {"c4": int(round(float(flusso_edge[best]))), "tratto": int(best)}
    return out, flusso_edge


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true", help=f"instrada solo {ORIGINI_PROVA} origini")
    ap.add_argument("--ripiego", action="store_true", help="non instradare: c4 = auto che partono dalla zona")
    ap.add_argument("--torinesi", choices=("auto", "si", "no"), default="auto")
    ap.add_argument("--soglia-torinesi", type=float, default=SOGLIA_TORINESI)
    ap.add_argument("--raggio-strada", type=float, default=RAGGIO_STRADA_M)
    args = ap.parse_args()
    raggio = args.raggio_strada
    c = comuni.Controlli()
    t_inizio = time.time()

    for f in (SPOSTAMENTI, LUOGHI):
        c(f"esiste {f.name}", f.exists(), bloccante=True)
    luoghi = json.loads(LUOGHI.read_text(encoding="utf-8"))["luoghi"]
    nomi_strada = {}
    if SEGNALI.exists():
        nomi_strada = {s["id_luogo"]: s.get("a2_strada") for s in json.loads(SEGNALI.read_text(encoding="utf-8"))["luoghi"]}
    zona_di = {l["id_luogo"]: l.get("zona_imq") for l in luoghi}

    print("1. domanda del mattino dai microdati IMQ (solo auto: conducente + car sharing)...")
    n, k, cint, tor, per_zona = leggi_domanda()
    c("auto in entrata dalla cintura > 0", n["M_cint"] > 0, bloccante=True)
    quota = n["f_mattino"] / n["M_cint"]
    rapporto_tor = n["M_tor"] / n["M_cint"]
    if args.torinesi == "auto":
        torinesi = rapporto_tor >= args.soglia_torinesi
    else:
        torinesi = args.torinesi == "si"
    print(f"   M_cint {n['M_cint']:,.0f} auto ({k['M_cint']} interviste); persone in auto {n['persone_cint']:,.0f}")
    print(f"   M_tor  {n['M_tor']:,.0f} auto ({k['M_tor']} interviste) = {rapporto_tor:.0%} di M_cint")
    print(f"   f_mattino {n['f_mattino']:,.0f} ({k['f_mattino']} interviste); quota {quota:.1%}")
    print(f"   torinesi nella domanda: {'SI' if torinesi else 'NO'} (soglia {args.soglia_torinesi:.0%}, scelta {args.torinesi})")
    c("auto conducenti minori delle persone in auto", n["M_cint"] <= n["persone_cint"], bloccante=True)
    c("interviste di f_mattino almeno 30", k["f_mattino"] >= 30,
      dettaglio=f"{k['f_mattino']} interviste" + ("" if k["f_mattino"] >= 30 else ": quota su pochi dati"))
    celle = cint + (tor if torinesi else [])

    metodo = "instradamento"
    riepilogo_instr = {}
    c4 = {}
    c4_parcheggi = {}
    flusso_edge = None
    if args.ripiego:
        metodo = "ripiego"
    else:
        try:
            for f in (RETE_DIR / "rete_auto.npz", PUNTI):
                if not f.exists():
                    raise FileNotFoundError(f)
            print("2. instradamento sulla rete del traffico (metodo V0 dello script 42)...")
            m42 = comuni.carica_script("42_instradamento.py")
            import rete_osm
            rete = rete_osm.carica(RETE_DIR)
            punti = json.loads(PUNTI.read_text(encoding="utf-8"))
            N = len(rete["nodi_xy"])
            origini, peso_tot, perso_zone, perso_self, dett = m42.carica_domanda_nodi(N, punti, celle)
            flusso, perso_nr, n_orig = instrada(rete, origini, ORIGINI_PROVA if args.prova else 0)
            riepilogo_instr = {"peso_domanda": round(peso_tot, 1), "perso_stesso_nodo": round(perso_self, 1),
                               "perso_zona_senza_punti": round(perso_zone, 1),
                               "perso_non_raggiungibile": round(perso_nr, 1),
                               "origini": n_orig, "prova": args.prova}
            print(f"   domanda {peso_tot:,.0f}; perso: stesso nodo {perso_self:,.0f}, zona senza punti "
                  f"{perso_zone:,.0f}, non raggiungibile {perso_nr:,.0f}")
            if not args.prova:
                c("si perde meno del 15% della domanda", (perso_self + perso_zone + perso_nr) <= 0.15 * peso_tot,
                  dettaglio=f"perso {(perso_self + perso_zone + perso_nr) / peso_tot:.1%}")
            print("3. c4: flusso della strada piu' trafficata entro "
                  f"{raggio:.0f} m da ogni luogo...")
            c4, flusso_edge = c4_per_punti(rete, flusso, [(l["id_luogo"], l["lat"], l["lon"]) for l in luoghi], raggio)
            if PARCHEGGI.exists():
                pk = [p for p in json.loads(PARCHEGGI.read_text(encoding="utf-8"))["parcheggi"]
                      if p["tipo"] in ("interscambio_ufficiale", "garage_5t", "park_ride_osm", "osm_pubblico")]
                c4_parcheggi, _ = c4_per_punti(rete, flusso, [(p["id"], p["lat"], p["lon"]) for p in pk],
                                               RAGGIO_PARCHEGGIO_M)
            OUT_NPZ.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(OUT_NPZ, flusso_archi=flusso, flusso_edge=flusso_edge)
            if hasattr(m42, "verifica_networkx") and not args.prova:
                riepilogo_instr["nota_verifica"] = "per la verifica dei percorsi: 85_verifiche_correzioni.py"
        except Exception as ex:  # noqa: BLE001 - qualsiasi errore -> ripiego dichiarato
            print(f"   AVVISO: instradamento non riuscito ({type(ex).__name__}: {ex}): uso il ripiego")
            c("instradamento riuscito", False, dettaglio=f"{type(ex).__name__}: {ex}")
            metodo = "ripiego"
    if metodo == "ripiego":
        for l in luoghi:
            z = zona_di.get(l["id_luogo"])
            v = per_zona.get(z, [0.0, 0])[0] if z and not z.startswith("Q") else 0.0
            c4[l["id_luogo"]] = {"c4": int(round(v)), "tratto": None}

    # classifica dei luoghi eleggibili (fuori dalla zona centrale) per c4
    eleggibili = [l for l in luoghi if l.get("zona_imq") and l["zona_imq"] not in comuni.ZONE_CENTRALI]
    top = sorted(eleggibili, key=lambda l: -c4[l["id_luogo"]]["c4"])[:15]
    top_righe = [{"id_luogo": l["id_luogo"], "nome": l["nome"], "zona_imq": l["zona_imq"],
                  "strada": nomi_strada.get(l["id_luogo"]), "c4": c4[l["id_luogo"]]["c4"]} for l in top]
    trovati = [t for t in top_righe if any(a in (t["strada"] or "").lower() for a in INGRESSI_ATTESI)]
    c("in cima ci sono strade d'ingresso note (Francia, Unione Sovietica, Genova...)", len(trovati) > 0,
      dettaglio=f"{len(trovati)} su 15")
    c("nessun c4 negativo", all(v["c4"] >= 0 for v in c4.values()), bloccante=True)

    dati = {
        "generato": time.strftime("%d/%m/%Y %H:%M"),
        "parametri": {"modi_auto": list(comuni.MODI_AUTO), "mattino_minuti": list(comuni.MATTINO_MINUTI),
                      "zone_centrali": list(comuni.ZONE_CENTRALI), "soglia_torinesi": args.soglia_torinesi,
                      "scelta_torinesi": args.torinesi, "raggio_strada_m": raggio},
        "M_cint": round(n["M_cint"], 1), "M_cint_interviste": k["M_cint"],
        "persone_in_auto_cint": round(n["persone_cint"], 1),
        "M_tor": round(n["M_tor"], 1), "M_tor_interviste": k["M_tor"],
        "rapporto_torinesi": round(rapporto_tor, 4), "torinesi": torinesi,
        "f_mattino": round(n["f_mattino"], 1), "f_mattino_interviste": k["f_mattino"],
        "quota_mattino": round(quota, 4), "quota_dati_scarsi": k["f_mattino"] < 30,
        "auto_per_zona_origine": {z: {"auto": round(v[0], 1), "interviste": v[1]} for z, v in per_zona.items()},
        "c4_metodo": metodo, "instradamento": riepilogo_instr,
        "top15": top_righe,
        "luoghi": c4,
        "parcheggi": c4_parcheggi,
        "controlli": c.righe,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")

    r = ["RAPPORTO R6 - AUTO IN ENTRATA CHE PASSANO ACCANTO AI LUOGHI (script 81)",
         f"Generato il {dati['generato']}. Metodo per c4: {metodo}{' (PROVA: solo poche origini)' if args.prova else ''}.",
         "",
         "== Domanda del mattino (IMQ 2022, partenza 06:00-09:59, solo auto: conducente + car sharing) ==",
         f"  auto che entrano a Torino dalla cintura e da fuori (M_cint): {n['M_cint']:,.0f} ({k['M_cint']} interviste)".replace(",", "."),
         f"  persone in auto sugli stessi spostamenti (con i passeggeri): {n['persone_cint']:,.0f}".replace(",", "."),
         f"  auto dai quartieri periferici di Torino verso Q001-Q009 (M_tor): {n['M_tor']:,.0f} ({k['M_tor']} interviste)".replace(",", "."),
         f"  M_tor / M_cint = {rapporto_tor:.0%}; soglia {args.soglia_torinesi:.0%} -> torinesi nella domanda: {'SI' if torinesi else 'NO'}",
         f"  chi gia' oggi lascia l'auto per un mezzo pubblico (f_mattino): {n['f_mattino']:,.0f} ({k['f_mattino']} interviste)".replace(",", "."),
         f"  quota_mattino = f_mattino / M_cint = {quota:.1%}{' [DATI SCARSI]' if k['f_mattino'] < 30 else ''}",
         "",
         "== Instradamento ==",
         "  " + json.dumps(riepilogo_instr, ensure_ascii=False),
         "",
         "== I 15 luoghi fuori dalla zona centrale con piu' auto in entrata che passano accanto ==",
         ]
    for t in top_righe:
        r.append(f"  {t['c4']:8,d}  {t['nome'][:40]:40s} zona {t['zona_imq']:5s} strada {t['strada'] or '-'}".replace(",", "."))
    r += ["", "== Controlli ==", *("  " + x for x in c.righe), "",
          "== Limiti ==",
          "- Modello del traffico V0 (percorso piu' veloce, senza code): stima debole (C-DEBOLE, circa +-38%), solo ordine di grandezza.",
          "- Le stesse auto passano davanti a piu' fermate dello stesso corso: i numeri dei luoghi non si sommano.",
          "- Indagine IMQ campionaria; solo residenti 11-84 anni; nessun pendolare da fuori Piemonte."]
    RAPPORTO.write_text("\n".join(r) + "\n", encoding="utf-8")
    print(f"Scritto: {OUT}\nScritto: {RAPPORTO}\nDurata {time.time() - t_inizio:.0f} s; avvisi: {len(c.avvisi())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
