#!/usr/bin/env python3
"""
scripts/105_correzione_tempi_mezzi.py - correzione dei tempi coi mezzi pubblici con le misure (giro L23, regola 4).

I tempi coi mezzi degli script 93, 94 e 100 vengono dall'orario programmato (r5py). Questo script misura tre cose e le scrive in
data/processed/correzione_tempi_mezzi.json; gli script 93, 94 e 100 le applicano (comuni.tempo_mezzi_corretto):

  tempo corretto = tempo da orario + attesa in piu' + ritardo per minuto x quota a bordo x tempo da orario

  1. attesa in piu': quella misurata dallo script 70 (risultato9_attesa.json) nella fascia oraria, feriale, linee frequenti: media fra stima bassa e alta,
     una volta per viaggio. I cambi non si contano (stima prudente).
  2. ritardo guadagnato a bordo, per minuto: dal GPS (script 27), mediana sulle corse feriali che partono nella fascia di
     (ritardo all'ultima fermata vista - ritardo alla prima fermata vista) / minuti programmati fra le due.
  3. quota a bordo: r5py DetailedItineraries su un campione fisso di 200 coppie di zone dello script 93 (seme fisso), alle 8 del giorno di 93:
     mediana della quota del tempo passato su bus, tram o metro sul tempo totale (attese e cammino compresi).

Le regole (fasce, mediane, 200 coppie, seme 20261025) sono fissate prima dei numeri (PIANO_GRAFICA, giro L23). La fascia 7-9 e' quella della regola; le
altre fasce (giorno, sera, tarda sera) servono allo script 100, che calcola anche 13:00, 17:30 e 21:00: stesso metodo, fascia per fascia.

Uso:  python scripts\\105_correzione_tempi_mezzi.py            (lancia prima 27 e 70; ~10 minuti)
      python scripts\\105_correzione_tempi_mezzi.py --senza-quota   (salta r5py: tiene la quota gia' scritta nel file)
"""
import datetime as dt
import importlib.util
import json
import random
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

PROC = comuni.RADICE / "data" / "processed"
OUT = PROC / "correzione_tempi_mezzi.json"
RAPPORTO = comuni.RADICE / "docs" / "rapporti" / "RAPPORTO_CORREZIONE_TEMPI_MEZZI.txt"
N_COPPIE, SEME = 200, 20261025
LOTTO, TIMEOUT_BLOCCO_S = 10, 900   # coppie per blocco; un blocco che non finisce in 15 minuti si scarta (la rete r5py si costruisce a ogni blocco)
BUDGET_QUOTA_S = 5 * 3600      # F3: DetailedItineraries costa ~40 secondi a coppia (200 coppie = oltre 2 ore): tempo massimo totale 5 ore, poi si tengono le coppie fatte
N_USATE = 200                   # F3: tutte le 200 coppie del campione fisso (il giro L23 ne usava 40)
MIN_MINUTI_CORSA = 5.0          # corse con meno di 5 minuti fra prima e ultima fermata viste: troppo corte per un ritardo per minuto
MIN_CORSE = 200                 # sotto questo numero di corse la fascia non ha ritardo misurato (0 e AVVISO)
MODI_A_BORDO = ("BUS", "TRAM", "SUBWAY", "RAIL", "FERRY", "CABLE_CAR", "GONDOLA", "FUNICULAR", "TRANSIT")


def carica(nome_file, nome):
    spec = importlib.util.spec_from_file_location(nome, AQUI / nome_file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def ritardo_per_minuto():
    """Per fascia: mediana su corse feriali di (ritardo ultima - ritardo prima)/minuti programmati; ritorna ({fascia: {...}}, giorni usati)."""
    r4 = carica("27_risultato4_regolarita.py", "r4")
    gtfs = r4.GtfsPerGiorno(True)
    sorg = r4.apri_sorgente(False)
    giorni = [g for g in sorg.giorni() if comuni.nel_periodo(g, "gps")]
    giorni, _esclusi = r4.giorni_gps_validi(sorg, giorni, lambda g: gtfs.stato(g).trip_info)
    per_fascia = {f: [] for f in r4.FASCE}
    usati = []
    for g in giorni:
        d = datetime.strptime(g, "%Y%m%d").date()
        if r4.tipo_giorno_data(d) != 0:
            continue
        st = gtfs.stato(g)
        passaggi, _cop = sorg.passaggi_gps(g, (st.trip_info, st.nome_linea, st.prog), st.fermate)
        corse = {}
        for p in passaggi:
            corse.setdefault(p[r4.P_TRIP], []).append(p)
        for lista in corse.values():
            if len(lista) < 2:
                continue
            lista.sort(key=lambda p: p[r4.P_SEQ])
            a, b = lista[0], lista[-1]
            minuti = (b[r4.P_SCHED] - a[r4.P_SCHED]) / 60.0
            if minuti < MIN_MINUTI_CORSA:
                continue
            ora = r4.a_roma(datetime.fromtimestamp(a[r4.P_SCHED], dt.timezone.utc)).hour
            per_fascia[r4.fascia_oraria(ora)].append((b[r4.P_RIT] - a[r4.P_RIT]) / minuti)
        usati.append(g)
        log(f"  {g}: corse con ritardo misurato finora {sum(len(v) for v in per_fascia.values())}")
    sorg.chiudi()
    out = {}
    for f, v in per_fascia.items():
        out[f] = {"corse": len(v), "ritardo_per_minuto": round(statistics.median(v), 4) if len(v) >= MIN_CORSE else 0.0,
                  "p25": round(sorted(v)[len(v) // 4], 4) if v else None, "p75": round(sorted(v)[3 * len(v) // 4], 4) if v else None}
    return out, usati


def attesa_in_piu():
    j = json.loads((PROC / "risultato9_attesa.json").read_text(encoding="utf-8"))
    out = {}
    for f, c in j["citta_fascia"]["0"].items():
        out[f] = round((c["in_piu_min_bassa"] + c["in_piu_min_alta"]) / 2, 2) if c else 0.0
    return out


def campione_fisso():
    """(m93, zone, campione): le prime N_USATE coppie del campione fisso di N_COPPIE coppie di zone dello script 93 (seme fisso), in ordine."""
    m93 = carica("93_tp_contro_auto.py", "m93")
    t93 = json.loads((PROC / "tp_contro_auto.json").read_text(encoding="utf-8"))
    zone = m93.carica_zone(0)
    coppie = sorted((p["da"], p["a"]) for p in t93["coppie"] if p["da"] in zone and p["a"] in zone)
    campione = sorted(random.Random(SEME).sample(coppie, min(N_COPPIE, len(coppie)))[:N_USATE])   # prime N_USATE del campione fisso di 200
    return m93, zone, campione, len(coppie)


def quote_blocco(i0, i1):
    """Quota a bordo (r5py DetailedItineraries alle 8) delle coppie i0..i1 del campione. Gira in un processo a parte (vedi quota_a_bordo)."""
    m93, zone, campione, _n = campione_fisso()
    m18, rete, gpd = m93.avvia_r5py()
    import pandas as pd
    from r5py import DetailedItineraries
    from r5py import TransportMode as TM
    quando = dt.datetime.combine(m93.GIORNO, dt.time(8, 0))
    blocco = list(enumerate(campione))[i0:i1]

    def punti_coppie(quale):
        righe = []
        for k, (a, b) in blocco:
            z = a if quale == 0 else b
            p = max(zone[z]["punti"], key=lambda q: q["peso"])
            righe.append({"id": str(k), "lat": p["lat"], "lon": p["lon"]})
        df = pd.DataFrame(righe)
        return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")
    it = pd.DataFrame(DetailedItineraries(rete, origins=punti_coppie(0), destinations=punti_coppie(1), departure=quando,
                                          departure_time_window=dt.timedelta(minutes=5), transport_modes=[TM.TRANSIT, TM.WALK],
                                          speed_walking=m93.VEL_PIEDI_KMH, max_time=dt.timedelta(minutes=m93.TEMPO_MAX_MIN)))
    quote = []
    for (da_id, a_id), g0 in it.groupby(["from_id", "to_id"]):
        if str(da_id) != str(a_id):          # origine k -> destinazione k (stessa lunghezza: r5py le abbina a coppie)
            continue
        migliore = None
        for _opt, g in (g0.groupby("option") if "option" in g0.columns else [(0, g0)]):
            tot = (g["travel_time"].dt.total_seconds() + g["wait_time"].dt.total_seconds().fillna(0)).sum()
            if migliore is None or tot < migliore[0]:
                migliore = (tot, g)
        tot, g = migliore
        a_bordo = g[g["transport_mode"].astype(str).str.split(".").str[-1].str.upper().isin(MODI_A_BORDO)]["travel_time"].dt.total_seconds().sum()
        if tot > 0:
            quote.append(a_bordo / tot)
    return quote


def quota_a_bordo(log_):
    """Mediana della quota a bordo su un campione fisso di coppie di zone dello script 93 (seme fisso).
    Ogni blocco di coppie gira in un processo a parte con un tempo massimo: r5py a volte si pianta su una coppia (e finisce la memoria Java),
    cosi' il blocco si scarta e si va avanti. Tempo massimo totale BUDGET_QUOTA_S."""
    import subprocess
    _m93, _zone, campione, n_coppie = campione_fisso()
    log_(f"quota a bordo: {len(campione)} coppie su {n_coppie}, seme {SEME}")
    quote, scartati, t0 = [], 0, time.time()
    for i in range(0, len(campione), LOTTO):
        if time.time() - t0 > BUDGET_QUOTA_S:
            log_(f"  tempo massimo ({BUDGET_QUOTA_S // 60} minuti) raggiunto")
            scartati += len(campione) - i
            break
        try:
            r = subprocess.run([sys.executable, str(AQUI / "105_correzione_tempi_mezzi.py"), "--blocco", f"{i}:{min(i + LOTTO, len(campione))}"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT_BLOCCO_S)
            riga = next((x for x in r.stdout.splitlines() if x.startswith("QUOTE:")), None)
            if riga is None:
                raise RuntimeError((r.stderr or r.stdout)[-120:].replace("\n", " "))
            nuove = json.loads(riga[6:])
        except Exception as e:
            scartati += min(LOTTO, len(campione) - i)
            log_(f"  blocco {i}-{min(i + LOTTO, len(campione))} scartato: {type(e).__name__} {str(e)[:100]}")
            continue
        quote += nuove
        log_(f"  {min(i + LOTTO, len(campione))}/{len(campione)} coppie, {len(quote)} con percorso")
    return {"coppie_campione": len(campione), "coppie_usate": len(quote), "senza_percorso_o_scartate": scartati,
            "mediana": round(statistics.median(quote), 4) if quote else None,
            "p25": round(sorted(quote)[len(quote) // 4], 4) if quote else None, "p75": round(sorted(quote)[3 * len(quote) // 4], 4) if quote else None}


def main():
    if "--blocco" in sys.argv:       # processo di lavoro di quota_a_bordo: stampa le quote del blocco e basta
        i0, i1 = (int(x) for x in sys.argv[sys.argv.index("--blocco") + 1].split(":"))
        print("QUOTE:" + json.dumps(quote_blocco(i0, i1)), flush=True)
        return
    senza_quota = "--senza-quota" in sys.argv
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    attesa = attesa_in_piu()
    log("ritardo per minuto dal GPS ...")
    rit, giorni = ritardo_per_minuto()
    quota = None
    if senza_quota and OUT.exists():
        quota = json.loads(OUT.read_text(encoding="utf-8")).get("quota_a_bordo")
    if not quota:
        quota = quota_a_bordo(log)
    q = quota["mediana"]
    fasce = {f: {"attesa_in_piu_min": attesa.get(f, 0.0), **rit[f], "quota_a_bordo": q} for f in rit if f != "notte"}
    out = {"generato": comuni.ora() if hasattr(comuni, "ora") else time.strftime("%Y-%m-%d %H:%M"),
           "formula": "tempo corretto = tempo da orario + attesa in piu' + ritardo per minuto x quota a bordo x tempo da orario",
           "regole": {"coppie_campione": N_COPPIE, "seme": SEME, "min_minuti_corsa": MIN_MINUTI_CORSA, "min_corse_fascia": MIN_CORSE,
                      "attesa": "script 70, feriale, linee frequenti, media di stima bassa e alta, una volta per viaggio; i cambi non si contano",
                      "ritardo": "GPS (script 27), corse feriali: (ritardo all'ultima fermata vista - ritardo alla prima) / minuti programmati, mediana per fascia",
                      "quota": f"r5py DetailedItineraries alle 8, mediana su {N_USATE} coppie (prime del campione fisso di {N_COPPIE}, per tempo); la stessa per tutte le fasce"},
           "giorni_gps": giorni, "quota_a_bordo": quota, "per_fascia": fasce}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    righe = ["CORREZIONE DEI TEMPI COI MEZZI PUBBLICI (script 105, giro L23)", out["formula"], "",
             f"Quota a bordo (mediana, {quota['coppie_usate']} coppie su {quota['coppie_campione']}): {q} (da {quota['p25']} a {quota['p75']})",
             f"Giorni feriali del GPS: {len(giorni)}", "", "fascia | attesa in piu' (min) | ritardo per minuto | corse | quota a bordo"]
    for f, v in fasce.items():
        righe.append(f"{f:<14} | {v['attesa_in_piu_min']:>8} | {v['ritardo_per_minuto']:>8} (da {v['p25']} a {v['p75']}) | {v['corse']:>6} | {v['quota_a_bordo']}")
    righe += ["", "Esempio (fascia 7-9, 30 minuti da orario): " + str(round(comuni.tempo_mezzi_corretto(30.0, "punta_mattina"), 1)) + " minuti corretti"]
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))
    for f, v in fasce.items():
        if v["corse"] < MIN_CORSE:
            print(f"AVVISO: fascia {f}: {v['corse']} corse (< {MIN_CORSE}): ritardo per minuto messo a 0")


if __name__ == "__main__":
    main()
