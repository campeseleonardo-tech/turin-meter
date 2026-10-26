#!/usr/bin/env python3
"""
97_riassunti_storico.py  -  riassunti dello storico della raccolta (sola lettura sullo storico).

Lo storico SQLite del Raspberry Pi (data/storico_backup.sqlite, GB e in crescita) non va in git. Questo script ne ricava
riassunti piccoli, in data/storico_riassunti/ (si tengono in git), con cui gli script 27, 70, 26 e 71 danno gli stessi
numeri quando lo storico non c'e' (lo dicono: «Sorgente dei dati: riassunti»). Formato: scripts/riassunti_storico.py.

Cosa scrive
-----------
  passaggi_AAAA-MM.zip       (script 27 e 70) per ogni giorno GTFS: i passaggi alle fermate misurati con il GPS (e quelli del feed dei
                             ritardi, per il confronto), le corse viste, la copertura, le ore con la raccolta attiva.
                             Per passaggio: corsa, fermata (stop_sequence) e istante in millisecondi: il resto viene dal GTFS.
  sensori5t_AAAA-MM.json.gz  (script 26) per giorno locale, sensore e ora: somme di flusso e velocita' delle letture affidabili.
  parcheggi_AAAA-MM.json.gz  (script 71) per giorno locale, parcheggio e ora: letture valide e somma dell'occupazione.
  anagrafica.json            sensori e parcheggi (nome, posizione, posti).
  ora_tipica.json            posizioni di tutti i mezzi in un feriale tipico fra le 7:30 e le 8:30, una ogni 30 secondi
                             (per l'animazione della home); al massimo 300 KB.

Come si lancia
--------------
  python scripts/97_riassunti_storico.py                   tutto, solo i mesi nuovi o incompleti (gli ultimi 2 giorni si rifanno sempre)
  python scripts/97_riassunti_storico.py --mese 2026-10    solo quel mese (prima prova consigliata: un mese)
  python scripts/97_riassunti_storico.py --solo passaggi|5t|parcheggi|ora
  python scripts/97_riassunti_storico.py --rifai           rifa anche i giorni e i mesi gia' scritti
  python scripts/97_riassunti_storico.py --riassunti-in CARTELLA   scrive altrove (default data/storico_riassunti)
  python scripts/97_riassunti_storico.py --prova           storico FINTO piccolo in una cartella temporanea (per provarlo nel cloud)
Controlli (AVVISO, o ERRORE se la struttura e' rotta): righe lette e scritte che tornano, nessun valore negativo, date dentro la raccolta.
"""
import argparse
import json
import sys
import tempfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402
import riassunti_storico as rs  # noqa: E402

RADICE = comuni.RADICE
LIMITE_ORA_TIPICA = 300_000      # byte
FINESTRA_ORA_TIPICA = (7.5, 8.5)  # ore locali
PASSO_S = 30
GAP_MAX_S = 180
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = 44.7, 45.4, 7.3, 8.1     # Torino e cintura: posizioni fuori da qui = errore GPS


# ---------------------------------------------------------------- passaggi
def riassumi_passaggi(db, r9, c, mese, rifai, giorni_tutti, gtfs):
    """gtfs: r4.GtfsPerGiorno, il GTFS valido in ogni giorno."""
    r4 = r9.r4
    presenti = rs.giorni_passaggi_presenti(c.cartella_out)
    ultimi = set(giorni_tutti[-2:])      # il giorno in corso e quello appena finito possono essere incompleti
    daf = [g for g in giorni_tutti if (not mese or rs.mese_da_giorno(g) == mese)]
    daf = [g for g in daf if rifai or g not in presenti or g in ultimi]
    print(f"\n[passaggi] giorni da riassumere: {len(daf)} su {len(giorni_tutti)} ({', '.join(daf[:6])}{'...' if len(daf) > 6 else ''})")
    tot = {"gps": 0, "feed": 0}
    for n, giorno in enumerate(daf, 1):
        print(f"  [{n}/{len(daf)}] {giorno}...", flush=True)
        st = gtfs.stato(giorno)
        trip_info, ctx, fermate, gtfs_nome = st.trip_info, st.ctx, st.fermate, Path(st.path).name
        base = r4.mezzanotte_utc(giorno).timestamp()
        pf, sc, tipo, es, n_letti = db.passaggi_feed(giorno, ctx)
        pg, cop = db.passaggi_gps(giorno, ctx, fermate)
        corse_f, cols_f = rs.colonne_passaggi(pf, base, True, r4.P_TRIP, r4.P_SEQ, r4.P_EST, r4.P_FONTE, r4.P_SCHED)
        corse_g, cols_g = rs.colonne_passaggi(pg, base, False, r4.P_TRIP, r4.P_SEQ, r4.P_EST, r4.P_FONTE, r4.P_SCHED)
        corse_gps = sorted(t for t in db.corse_gps(giorno) if t in trip_info)
        meta = {"versione": rs.VERSIONE, "giorno": giorno, "tipo": tipo, "base": base, "gtfs": gtfs_nome,
                "corse_gps_passaggi": corse_g, "corse_feed": corse_f, "cop": cop, "scarti": sc, "letti": n_letti, "esempi": es,
                "corse_gps": corse_gps, "ore_minuti": {str(h): m for h, m in db.ore_minuti(giorno).items()},
                "generato": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        if giorno == r9.GIORNO_PROVA:
            meta["controllo_gps"] = r9.controllo_gps_giorno(db, giorno, ctx, fermate)
        # controlli del giorno: le colonne devono avere tante righe quanti i passaggi, le corse indicate devono esistere
        c(f"{giorno}: passaggi GPS scritti = letti ({len(pg)})", len(cols_g["trip"]) // 4 == len(pg) and len(cols_g["rit"]) // 4 == len(pg))
        c(f"{giorno}: passaggi feed scritti = letti ({len(pf)})", len(cols_f["trip"]) // 4 == len(pf))
        c(f"{giorno}: copertura plausibile (validi <= programmati)", cop["validi"] <= max(cop["programmati"], cop["validi"]) and cop["validi"] >= 0)
        rs.salva_giorno_passaggi(giorno, meta, cols_g, cols_f, c.cartella_out)
        tot["gps"] += len(pg)
        tot["feed"] += len(pf)
    peso = sum(rs.giorni_passaggi_presenti(c.cartella_out).values())
    print(f"[passaggi] scritti {tot['gps']} passaggi GPS e {tot['feed']} del feed; peso totale degli zip {peso / 1e6:.1f} MB "
          f"({peso / max(1, len(rs.giorni_passaggi_presenti(c.cartella_out))) / 1e6:.2f} MB per giorno)")


# ---------------------------------------------------------------- 5T e parcheggi
def mesi_fra(primo_iso, ultimo_iso):
    """['2026-10', ...] fra due date ISO (stringhe che iniziano con AAAA-MM-GG), estremi inclusi."""
    a = date.fromisoformat(primo_iso[:10]).replace(day=1)
    b = date.fromisoformat(ultimo_iso[:10]).replace(day=1)
    out = []
    while a <= b:
        out.append(f"{a.year}-{a.month:02d}")
        a = (a.replace(day=28) + timedelta(days=4)).replace(day=1)
    return out


def limiti_mese(mese):
    """Limiti UTC con un giorno di margine: tutti i giorni locali del mese sono interi dentro."""
    a = date.fromisoformat(mese + "-01")
    b = (a.replace(day=28) + timedelta(days=4)).replace(day=1)
    return (a - timedelta(days=1)).isoformat(), (b + timedelta(days=1)).isoformat()


def controlla_celle(c, nome, giorni, primo_loc, ultimo_loc, negativi):
    c(f"{nome}: nessun valore negativo", negativi == 0, dettaglio=f"{negativi} negativi" if negativi else "")
    fuori = [d for d in giorni if not (primo_loc <= d <= ultimo_loc)]
    c(f"{nome}: tutte le date dentro la raccolta ({primo_loc} - {ultimo_loc})", not fuori, dettaglio=", ".join(fuori[:3]))


def riassumi_5t(db, c, mese, rifai):
    con = db.con
    r = con.execute("SELECT MIN(generato_utc), MAX(generato_utc) FROM flussi_5t").fetchone()
    if not r[0]:
        print("\n[5T] nessuna lettura nella tabella flussi_5t: salto")
        return
    primo_loc = comuni.ora_locale(datetime.fromisoformat(r[0].replace("Z", "+00:00")).astimezone(timezone.utc)).date().isoformat()
    ultimo_loc = comuni.ora_locale(datetime.fromisoformat(r[1].replace("Z", "+00:00")).astimezone(timezone.utc)).date().isoformat()
    mesi = mesi_fra(primo_loc, ultimo_loc)
    ultimo_mese = mesi[-1]
    mesi = [m for m in mesi if (not mese or m == mese) and (rifai or m == ultimo_mese or not (rs.cartella(c.cartella_out) / f"sensori5t_{m}.json.gz").exists())]
    print(f"\n[5T] mesi da riassumere: {mesi}")
    for m in mesi:
        dal, al = limiti_mese(m)
        giorni = rs.riassumi_5t(con, dal, al, solo_mese=m)
        n_scritte = sum(cc[0] for g in giorni.values() for ore in g["celle"].values() for cc in ore.values())
        n_lette = con.execute(
            "SELECT COUNT(*) FROM flussi_5t f JOIN accuratezza_5t a ON a.generato_utc = f.generato_utc AND a.lcd1 = f.lcd1 "
            "WHERE a.accuratezza > 0 AND f.flusso IS NOT NULL AND f.generato_utc >= ? AND f.generato_utc < ?", (dal, al)).fetchone()[0]
        # le righe del margine (giorni dei mesi vicini) non contano: le righe lette si contano sui giorni tenuti
        giorni_mese_iso = [d for d in giorni]
        neg = sum(1 for g in giorni.values() for ore in g["celle"].values() for cc in ore.values() if cc[1] < 0 or cc[3] < 0 or cc[0] < 0)
        c(f"5T {m}: righe lette >= righe scritte ({n_lette} lette nel margine, {n_scritte} scritte)", n_scritte <= n_lette)
        controlla_celle(c, f"5T {m}", giorni_mese_iso, primo_loc, ultimo_loc, neg)
        rs.salva_5t_mese(m, giorni, c.cartella_out)
        print(f"  {m}: {len(giorni)} giorni, {n_scritte} letture affidabili")
    sensori = {lcd1: [nome, direzione, lat, lng] for lcd1, nome, direzione, lat, lng in con.execute(
        "SELECT lcd1, nome_strada, direzione, lat, lng FROM sensori_5t")}
    return sensori


def riassumi_parcheggi(db, c, mese, rifai):
    con = db.con
    parcheggi = [list(x) for x in con.execute("SELECT id, nome, lat, lng, totale FROM parcheggi_5t").fetchall()]
    r = con.execute("SELECT MIN(generato_utc), MAX(generato_utc) FROM occupazione_pk").fetchone()
    if not r[0]:
        print("\n[parcheggi] nessuna lettura nella tabella occupazione_pk: salto")
        return parcheggi
    primo_loc = comuni.ora_locale(datetime.strptime(r[0][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)).date().isoformat()
    ultimo_loc = comuni.ora_locale(datetime.strptime(r[1][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)).date().isoformat()
    mesi = mesi_fra(primo_loc, ultimo_loc)
    ultimo_mese = mesi[-1]
    mesi = [m for m in mesi if (not mese or m == mese) and (rifai or m == ultimo_mese or not (rs.cartella(c.cartella_out) / f"parcheggi_{m}.json.gz").exists())]
    print(f"\n[parcheggi] mesi da riassumere: {mesi}")
    totali = {x[0]: x[4] for x in parcheggi}
    for m in mesi:
        dal, al = limiti_mese(m)
        giorni = rs.riassumi_parcheggi(con, totali, dal, al, solo_mese=m)
        righe_scritte = sum(g["righe"] for g in giorni.values())
        n_valide = sum(cc[0] for g in giorni.values() for ore in g["celle"].values() for cc in ore.values())
        scartate = sum(g["scartate"] for g in giorni.values())
        righe_lette = con.execute("SELECT COUNT(*) FROM occupazione_pk WHERE generato_utc >= ? AND generato_utc < ?", (dal, al)).fetchone()[0]
        neg = sum(1 for g in giorni.values() for ore in g["celle"].values() for cc in ore.values() if cc[1] < 0 or cc[0] < 0)
        c(f"parcheggi {m}: righe scritte <= righe lette nel margine ({righe_scritte} <= {righe_lette})", righe_scritte <= righe_lette)
        c(f"parcheggi {m}: valide + scartate <= righe ({n_valide} + {scartate} <= {righe_scritte})", n_valide + scartate <= righe_scritte)
        controlla_celle(c, f"parcheggi {m}", list(giorni), primo_loc, ultimo_loc, neg)
        rs.salva_parcheggi_mese(m, giorni, c.cartella_out)
        print(f"  {m}: {len(giorni)} giorni, {n_valide} letture valide, {scartate} scartate")
    return parcheggi


# ---------------------------------------------------------------- ora tipica (animazione della home)
def costruisci_ora_tipica(db, r4, giorni_tutti, modo_linea, trip_info):
    """Posizioni dei mezzi di un feriale tipico fra le 7:30 e le 8:30, una ogni 30 s. Il giorno e' quello feriale con la
    copertura migliore del GPS in quella finestra. Coordinate in interi (1e-5 gradi): la prima assoluta, poi le differenze."""
    feriali = [g for g in giorni_tutti if r4.tipo_giorno_data(datetime.strptime(g, "%Y%m%d").date()) == 0]
    if not feriali:
        return None, "nessun giorno feriale"
    finestra = {}

    def righe_finestra(giorno):
        base = r4.mezzanotte_utc(giorno).timestamp()
        da = datetime.fromtimestamp(base + FINESTRA_ORA_TIPICA[0] * 3600 - 300, timezone.utc).isoformat()
        a = datetime.fromtimestamp(base + FINESTRA_ORA_TIPICA[1] * 3600 + 300, timezone.utc).isoformat()
        return base, db.con.execute(
            "SELECT corsa, linea, ts_feed, lat, lng FROM mezzi_gtt WHERE letto_utc BETWEEN ? AND ? AND corsa <> '' AND ts_feed AND lat AND lng",
            (da, a))

    copertura = {}
    for g in feriali:
        base, it = righe_finestra(g)
        corse, passi_coperti = set(), set()
        t_ini = base + FINESTRA_ORA_TIPICA[0] * 3600
        for r in it:
            corse.add(r[0])
            passi_coperti.add(int((r[2] - t_ini) // PASSO_S))
        finestra[g] = len(corse)
        copertura[g] = len([k for k in passi_coperti if 0 <= k <= int((FINESTRA_ORA_TIPICA[1] - FINESTRA_ORA_TIPICA[0]) * 3600 // PASSO_S)])
    # il giorno con la copertura migliore (passi da 30 s con almeno una posizione): il GPS arriva a ondate e in alcuni giorni resta fermo per minuti;
    # a pari copertura, quello con piu' corse viste
    giorno = max(feriali, key=lambda g: (copertura[g], finestra[g], g))
    print("[ora tipica] copertura dei passi da 30 s nella finestra, per giorno feriale: " + ", ".join(f"{g}: {copertura[g]}" for g in feriali))
    base, it = righe_finestra(giorno)
    punti = defaultdict(set)
    linea_di = {}
    for corsa, linea, ts, lat, lng in it:
        punti[corsa].add((ts, lat, lng))
        linea_di[corsa] = linea
    t0 = base + FINESTRA_ORA_TIPICA[0] * 3600
    n_passi = int((FINESTRA_ORA_TIPICA[1] - FINESTRA_ORA_TIPICA[0]) * 3600 // PASSO_S) + 1
    entrate = []
    for corsa in sorted(punti):
        pts = sorted(punti[corsa])
        segmenti, corrente = [], [pts[0]]
        for a, b in zip(pts, pts[1:]):
            if b[0] - a[0] > GAP_MAX_S:
                segmenti.append(corrente)
                corrente = [b]
            else:
                corrente.append(b)
        segmenti.append(corrente)
        for seg in segmenti:
            if len(seg) < 2:
                continue
            k = max(0, int(-(-(seg[0][0] - t0) // PASSO_S)))
            ks, posizioni, j = None, [], 0
            while k < n_passi and t0 + k * PASSO_S <= seg[-1][0]:
                tt = t0 + k * PASSO_S
                while j < len(seg) - 2 and seg[j + 1][0] < tt:
                    j += 1
                (ta, la, oa), (tb, lb, ob) = seg[j], seg[j + 1]
                f = 0.0 if tb == ta else max(0.0, min(1.0, (tt - ta) / (tb - ta)))
                posizioni.append((round((la + f * (lb - la)) * 1e5), round((oa + f * (ob - oa)) * 1e5)))
                ks = k if ks is None else ks
                k += 1
            if len(posizioni) < 2:
                continue
            p = [posizioni[0][0], posizioni[0][1]]
            for (x0, y0), (x1, y1) in zip(posizioni, posizioni[1:]):
                p += [x1 - x0, y1 - y0]
            linea = linea_di.get(corsa) or ""
            entrate.append({"l": linea, "m": modo_linea.get(linea, "bus"), "t": ks, "p": p})
    totale = len(entrate)

    def serializza(lista):
        return json.dumps({"versione": 1, "giorno": f"{giorno[:4]}-{giorno[4:6]}-{giorno[6:]}", "inizio": "07:30", "passo_s": PASSO_S,
                           "passi": n_passi, "coordinate": "interi in 1e-5 gradi: [lat, lon] della prima posizione, poi le differenze",
                           "mezzi_totali": totale, "mezzi_inclusi": len(lista), "mezzi": lista},
                          ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    passo, lista = 1, entrate
    dati = serializza(lista)
    while len(dati) > LIMITE_ORA_TIPICA and passo < 50:
        passo += 1
        lista = entrate[::passo]       # un mezzo ogni «passo»: il campione resta distribuito su tutte le linee
        dati = serializza(lista)
    info = {"giorno": giorno, "corse_viste_nel_giorno": finestra[giorno], "mezzi_totali": totale, "mezzi_inclusi": len(lista),
            "passo_campione": passo, "byte": len(dati), "passi": n_passi}
    return (dati, lista, info), ""


def controlla_ora_tipica(c, dati, lista, info):
    c(f"ora tipica: dimensione {info['byte']} byte <= {LIMITE_ORA_TIPICA}", info["byte"] <= LIMITE_ORA_TIPICA)
    ok = True
    for m in lista:
        lat, lon = m["p"][0] / 1e5, m["p"][1] / 1e5
        n = (len(m["p"]) - 2) // 2 + 1
        la, lo = m["p"][0], m["p"][1]
        for i in range(2, len(m["p"]), 2):
            la += m["p"][i]
            lo += m["p"][i + 1]
        ok = ok and LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX and LAT_MIN <= la / 1e5 <= LAT_MAX and LON_MIN <= lo / 1e5 <= LON_MAX
        ok = ok and 0 <= m["t"] and m["t"] + n - 1 < info["passi"]
    c("ora tipica: posizioni dentro Torino e passi dentro la finestra", ok)
    c("ora tipica: ha almeno 50 mezzi", len(lista) >= 50, dettaglio=f"{len(lista)} mezzi")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Riassunti dello storico (sola lettura sullo storico)")
    ap.add_argument("--mese", help="solo questo mese, AAAA-MM")
    ap.add_argument("--solo", choices=("passaggi", "5t", "parcheggi", "ora"), help="solo questa parte")
    ap.add_argument("--rifai", action="store_true", help="rifa anche giorni e mesi gia' scritti")
    ap.add_argument("--db", help="storico SQLite (default data/storico_backup.sqlite)")
    ap.add_argument("--gtfs", help="zip del GTFS (default quello dello script 27)")
    ap.add_argument("--riassunti-in", help="cartella di uscita (default data/storico_riassunti)")
    ap.add_argument("--prova", action="store_true", help="storico finto in una cartella temporanea")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    r9 = comuni.carica_script("70_risultato9_attesa.py")     # porta con se' il 27 (r9.r4)
    r4 = r9.r4
    c = comuni.Controlli()
    if args.prova:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "prove"))
        import storico_finto
        tmp = Path(tempfile.mkdtemp(prefix="riassunti_prova_"))
        finto = storico_finto.crea(tmp)
        r4.DB, r4.GTFS = finto["db"], finto["gtfs"]
        r4.GTFS_ARCHIVIO = None      # la prova usa solo il GTFS finto
        r9.GIORNO_PROVA = finto["giorno_controllo"]
        cart_out = tmp / "storico_riassunti"
        print(f"PROVA: storico finto in {tmp}")
    else:
        cart_out = Path(args.riassunti_in) if args.riassunti_in else rs.CARTELLA
    if args.db:
        r4.DB = Path(args.db)
    if args.gtfs:
        r4.GTFS = Path(args.gtfs)
        r4.GTFS_ARCHIVIO = None      # un GTFS scelto a mano vale per tutti i giorni
    if not Path(r4.DB).exists():
        sys.exit(f"ERRORE: non trovo lo storico {r4.DB}. Questo script gira sul PC di Leo (o con --prova nel cloud).")
    c.cartella_out = cart_out
    rs.CARTELLA = cart_out
    print(f"Storico (sola lettura): {r4.DB}\nUscita: {cart_out}")

    db = r4.SorgenteDb(r4.DB)
    try:
        giorni_tutti = db.giorni()
        c("lo storico ha almeno un giorno di ritardi (trip_update_gtt)", len(giorni_tutti) > 0, bloccante=True)
        sensori = parcheggi = None
        parti = [args.solo] if args.solo else ["passaggi", "5t", "parcheggi", "ora"]
        if "passaggi" in parti or "ora" in parti:
            gtfs = r4.GtfsPerGiorno(True)    # il GTFS valido in ogni giorno (data/gtfs_archivio); con uno solo e' sempre lo stesso
            modo_linea = {}
            for p_ in sorted({r4.gtfs_del_giorno(g) for g in giorni_tutti}, key=str):
                modo_linea.update(r4.modi_linea(p_))
        if "passaggi" in parti:
            riassumi_passaggi(db, r9, c, args.mese, args.rifai, giorni_tutti, gtfs)
        if "5t" in parti:
            sensori = riassumi_5t(db, c, args.mese, args.rifai)
        if "parcheggi" in parti:
            parcheggi = riassumi_parcheggi(db, c, args.mese, args.rifai)
        if sensori is not None or parcheggi is not None:
            vecchia = rs.carica_anagrafica(cart_out) or {"sensori": {}, "parcheggi": []}
            if sensori is None:
                sensori = vecchia["sensori"] or {lcd1: [n, d, la, lo] for lcd1, n, d, la, lo in db.con.execute(
                    "SELECT lcd1, nome_strada, direzione, lat, lng FROM sensori_5t")}
            if parcheggi is None:
                parcheggi = vecchia["parcheggi"] or [list(x) for x in db.con.execute("SELECT id, nome, lat, lng, totale FROM parcheggi_5t")]
            rs.salva_anagrafica(sensori, parcheggi, cart_out)
            print(f"\nAnagrafica: {len(sensori)} sensori, {len(parcheggi)} parcheggi")
        if "ora" in parti:
            ris, errore = costruisci_ora_tipica(db, r4, giorni_tutti, modo_linea, None)
            if ris is None:
                c(f"ora tipica: {errore}", False)
            else:
                dati, lista, info = ris
                controlla_ora_tipica(c, dati, lista, info)
                rs.scrivi_atomico(cart_out / "ora_tipica.json", dati)
                print(f"\n[ora tipica] giorno {info['giorno']} ({info['corse_viste_nel_giorno']} corse viste, giorno con la copertura migliore), "
                      f"{info['mezzi_inclusi']} mezzi su {info['mezzi_totali']} (1 ogni {info['passo_campione']}), {info['byte'] / 1000:.0f} KB")
    finally:
        db.chiudi()

    print("\nPesi dei file scritti:")
    tot = 0
    for p in sorted(Path(cart_out).glob("*")):
        tot += p.stat().st_size
        print(f"  {p.name:36s} {p.stat().st_size / 1e6:8.2f} MB")
    print(f"  {'totale':36s} {tot / 1e6:8.2f} MB")
    print(f"avvisi: {len(c.avvisi())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
