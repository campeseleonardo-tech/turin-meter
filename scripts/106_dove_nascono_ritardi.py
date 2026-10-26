# -*- coding: utf-8 -*-
"""
scripts/106_dove_nascono_ritardi.py - dove nascono i ritardi dei bus: i tratti fra due fermate dove il tempo in piu' si accumula (F3, regole §6.4 del piano).

Dati: i passaggi GPS validi (le stesse regole dello script 27), giorni feriali del PERIODO «gps» (comuni.PERIODO) e validi per lo script 27.
Tratto: due fermate CONSECUTIVE di una corsa, tutte e due con un passaggio valido; se una fermata manca, quel pezzo non si conta.
  Il tratto che arriva all'ultima fermata della corsa non si conta (sosta al capolinea); resta nella somma di controllo. Gli orari oltre le 24:00
  (linee notturne) sono giusti: orario e istante sono data e ora complete (mezzanotte del giorno di servizio piu' i secondi GTFS), non ore del giorno.
  tempo in piu' sul tratto di una corsa = (istante alla fermata k+1 - istante alla fermata k) - (orario k+1 - orario k)
Per ogni tratto (coppia di fermate, qualunque sia la linea) e fascia:
  minuti persi al giorno feriale = somma dei tempi in piu' POSITIVI / numero di giorni feriali;
  il tratto vale solo con almeno 50 corse osservate nella fascia.
Fasce: 7-9 (fascia dell'orario programmato alla prima fermata del tratto) e intera giornata.
Classifica: i 10 tratti con piu' minuti persi, nelle due fasce, con il nome «{Fermata A} → {Fermata B} (linee …)» e la via OSM piu' vicina al punto di mezzo.
Controllo: nelle corse senza fermate mancanti la somma dei tempi in piu' (con segno) = ritardo all'ultima fermata - ritardo alla prima, scarto sotto l'1%.

Uso:
  python scripts\\106_dove_nascono_ritardi.py            (tutti i giorni feriali del periodo)
  python scripts\\106_dove_nascono_ritardi.py --prova    (un giorno solo; scrive in una cartella temporanea)

Uscite: data/processed/dove_nascono_ritardi.json, docs/rapporti/RAPPORTO_DOVE_NASCONO_RITARDI.txt; i tratti per la mappa (D.ritardi_tratti) li scrive lo script 04.
Sola lettura sullo storico.
"""
import argparse
import datetime as dt
import json
import re
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
PROC = RADICE / "data" / "processed"
OUT_JSON = PROC / "dove_nascono_ritardi.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_DOVE_NASCONO_RITARDI.txt"
MIN_CORSE = 50
TOP = 10
TRATTI_MAPPA = 3000          # nella mappa i tratti con piu' minuti persi (il file dei dati della mappa resta leggero)
P_LINEA, P_DIR, P_STOP, P_SCHED, P_EST, P_RIT, P_FASCIA, P_SEQ, P_FONTE, P_TRIP = range(10)
FASCE = (("punta_mattina", "7-9"), ("giornata", "intera giornata"))


def nome_fermata(nome):
    """«Fermata 3360 - PLAVA» -> «PLAVA»."""
    return re.sub(r"^Fermata\s+\d+\s*-\s*", "", nome).strip()


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def sequenze(st):
    """tid -> lista ordinata delle stop_sequence della corsa (dal GTFS del giorno), calcolata una volta per versione."""
    if not hasattr(st, "seq_per_corsa"):
        seqs = defaultdict(list)
        for (tid, seq) in st.prog:
            seqs[tid].append(seq)
        for lista in seqs.values():
            lista.sort()
        st.seq_per_corsa = seqs
    return st.seq_per_corsa


class Tratto:
    __slots__ = ("n", "somma", "linee")

    def __init__(self):
        self.n = {"punta_mattina": 0, "giornata": 0}
        self.somma = {"punta_mattina": 0.0, "giornata": 0.0}
        self.linee = set()


def elabora_giorno(passaggi, st, tratti, controllo):
    """Aggiorna tratti {(stop_a, stop_b): Tratto} e il controllo della somma con i passaggi di un giorno."""
    per_corsa = defaultdict(dict)
    for pg in passaggi:
        per_corsa[pg[P_TRIP]][pg[P_SEQ]] = pg
    seqs_corsa = sequenze(st)
    for tid, validi in per_corsa.items():
        seqs = seqs_corsa.get(tid, [])
        somma_firmata = 0.0
        completa = len(seqs) >= 2 and all(s in validi for s in seqs)
        for s0, s1 in zip(seqs[:-1], seqs[1:]):
            a, b = validi.get(s0), validi.get(s1)
            if a is None or b is None:
                continue
            extra = ((b[P_EST] - a[P_EST]) - (b[P_SCHED] - a[P_SCHED])) / 60.0
            somma_firmata += extra
            if s1 == seqs[-1]:       # il tratto che arriva all'ultima fermata della corsa e' sosta al capolinea (o fine corsa), non traffico: non si conta
                controllo["tratti_ultima_fermata"] += 1
                continue
            t = tratti.get((a[P_STOP], b[P_STOP]))
            if t is None:
                t = tratti[(a[P_STOP], b[P_STOP])] = Tratto()
            t.linee.add(a[P_LINEA])
            for f in ("giornata", "punta_mattina") if a[P_FASCIA] == "punta_mattina" else ("giornata",):
                t.n[f] += 1
                if extra > 0:
                    t.somma[f] += extra
        if completa:
            prima, ultima = validi[seqs[0]], validi[seqs[-1]]
            controllo["corse"] += 1
            controllo["somma_tratti"] += somma_firmata
            controllo["ritardo_finale_meno_iniziale"] += ultima[P_RIT] - prima[P_RIT]
            controllo["scarto_max_min"] = max(controllo["scarto_max_min"], abs(somma_firmata - (ultima[P_RIT] - prima[P_RIT])))


def via_vicina(rete, medi, lat, lon):
    """Nome della via OSM piu' vicina al punto (entro 60 m), o None."""
    import rete_osm
    d, e = rete_osm.tratto_piu_vicino(rete, lat, lon, medi)
    if e is None or d > 60:
        return None
    return rete["meta"]["nomi"][e]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prova", action="store_true", help="un solo giorno; uscite in una cartella temporanea")
    args = ap.parse_args()
    t0 = time.time()
    c = comuni.Controlli()
    m27 = comuni.carica_script("27_risultato4_regolarita.py")
    gtfs = m27.GtfsPerGiorno(True)
    sorg = m27.apri_sorgente(False)
    giorni = [g for g in sorg.giorni() if comuni.nel_periodo(g, "gps")]
    giorni, esclusi = m27.giorni_gps_validi(sorg, giorni, lambda g: gtfs.stato(g).trip_info)
    feriali = [g for g in giorni if m27.tipo_giorno_data(datetime.strptime(g, "%Y%m%d").date()) == 0]
    if args.prova:
        feriali = feriali[:1]
    log(f"giorni validi {len(giorni)}, feriali {len(feriali)}: {feriali}")
    tratti = {}
    controllo = {"corse": 0, "somma_tratti": 0.0, "ritardo_finale_meno_iniziale": 0.0, "scarto_max_min": 0.0, "tratti_ultima_fermata": 0}
    fermate_note = {}
    for n, giorno in enumerate(feriali, 1):
        st = gtfs.stato(giorno)
        fermate_note.update(st.fermate)
        passaggi, cop = sorg.passaggi_gps(giorno, st.ctx, st.fermate)
        log(f"[{n}/{len(feriali)}] {giorno}: {len(passaggi):,} passaggi validi su {cop['programmati']:,} programmati")
        elabora_giorno(passaggi, st, tratti, controllo)
        del passaggi
    sorg.chiudi()
    nf = len(feriali)
    c("almeno un giorno feriale", nf >= 1, bloccante=True, dettaglio=f"{nf} giorni")
    scarto = abs(controllo["somma_tratti"] - controllo["ritardo_finale_meno_iniziale"])
    rif = max(abs(controllo["ritardo_finale_meno_iniziale"]), 1e-9)
    c("corse complete: somma dei tempi in piu' = ritardo finale - ritardo iniziale (scarto sotto l'1%)", scarto / rif < 0.01,
      dettaglio=f"{controllo['corse']:,} corse; somma {controllo['somma_tratti']:.1f} contro {controllo['ritardo_finale_meno_iniziale']:.1f} minuti (scarto {100 * scarto / rif:.4f}%)")

    # classifica e mappa
    def riga(chiave, tr, f):
        a, b = chiave
        return {"stop_a": a, "stop_b": b, "da": nome_fermata(fermate_note[a][0]), "a": nome_fermata(fermate_note[b][0]), "linee": sorted(tr.linee, key=lambda x: (len(x), x)),
                "min_persi_giorno": round(tr.somma[f] / nf, 2), "corse": tr.n[f], "lat_a": fermate_note[a][1], "lon_a": fermate_note[a][2],
                "lat_b": fermate_note[b][1], "lon_b": fermate_note[b][2], "extra_medio_s": round(60 * tr.somma[f] / max(tr.n[f], 1), 1)}

    validi = {f: [(k, t) for k, t in tratti.items() if t.n[f] >= MIN_CORSE and k[0] in fermate_note and k[1] in fermate_note] for f, _ in FASCE}
    classifica = {}
    for f, _nome in FASCE:
        ordinati = sorted(validi[f], key=lambda kt: -kt[1].somma[f])
        classifica[f] = [riga(k, t, f) for k, t in ordinati[:TOP]]
    c("ci sono tratti con almeno 50 corse in tutte e due le fasce", all(len(validi[f]) >= TOP for f, _ in FASCE),
      dettaglio=", ".join(f"{nome}: {len(validi[f])}" for f, nome in FASCE))
    import rete_osm
    rete = rete_osm.carica(PROC / "traffico_c" / "rete")
    medi = rete_osm.punti_medi(rete)
    for f, _ in FASCE:
        for r in classifica[f]:
            r["via"] = via_vicina(rete, medi, (r["lat_a"] + r["lat_b"]) / 2, (r["lon_a"] + r["lon_b"]) / 2)
    mappa = sorted(validi["giornata"], key=lambda kt: -kt[1].somma["giornata"])[:TRATTI_MAPPA]
    da, a = comuni.PERIODO["gps"]
    tratti_mappa = {"meta": {"periodo": {"da": da, "a": a}, "min_corse": MIN_CORSE, "giorni_feriali": nf},
                    "tratti": [{"a": nome_fermata(fermate_note[k[0]][0]), "b": nome_fermata(fermate_note[k[1]][0]), "l": sorted(t.linee, key=lambda x: (len(x), x))[:6],
                                "g": [[round(fermate_note[k[0]][1], 5), round(fermate_note[k[0]][2], 5)], [round(fermate_note[k[1]][1], 5), round(fermate_note[k[1]][2], 5)]],
                                "m": round(t.somma["giornata"] / nf, 1), "n": t.n["giornata"]} for k, t in mappa]}
    out = {"stimato": False, "prova": bool(args.prova), "periodo": {"da": da, "a": a}, "giorni_feriali": feriali,
           "regole": {"min_corse": MIN_CORSE, "fasce": {f: nome for f, nome in FASCE},
                      "tratto": "due fermate consecutive di una corsa con passaggio GPS valido a tutte e due",
                      "minuti_persi": "somma dei tempi in piu' positivi / giorni feriali"},
           "tratti_totali": len(tratti), "tratti_validi": {f: len(validi[f]) for f, _ in FASCE},
           "controllo_somma": {**{k: round(v, 3) for k, v in controllo.items()}, "scarto_pct": round(100 * scarto / rif, 5)},
           "classifica": classifica, "tratti_mappa": tratti_mappa, "controlli": list(c.righe)}
    cartella = Path(tempfile.mkdtemp(prefix="dove_nascono_prova_")) if args.prova else None
    out_json = (cartella / OUT_JSON.name) if cartella else OUT_JSON
    rapporto = (cartella / RAPPORTO.name) if cartella else RAPPORTO
    out_json.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    r = ["RAPPORTO DOVE NASCONO I RITARDI (script 106)" + (" - PROVA" if args.prova else ""), f"generato: {dt.datetime.now().isoformat(timespec='seconds')}", "",
         f"Periodo GPS {da} - {a}, giorni feriali usati: {nf}. Tratti con almeno un passaggio: {len(tratti):,}; con almeno {MIN_CORSE} corse: "
         + ", ".join(f"{nome} {len(validi[f]):,}" for f, nome in FASCE) + ".",
         "Minuti persi al giorno feriale = somma dei tempi in piu' positivi sul tratto / giorni feriali. Tratto = due fermate consecutive di una corsa."]
    for f, nome in FASCE:
        r += ["", f"I {TOP} TRATTI CON PIU' MINUTI PERSI - {nome}", "  tratto (linee) | via OSM | minuti persi al giorno | corse | secondi in piu' per corsa"]
        for x in classifica[f]:
            r.append(f"  {x['da']} → {x['a']} (linee {', '.join(x['linee'])}) | {x['via'] or '-'} | {x['min_persi_giorno']:.1f} | {x['corse']} | {x['extra_medio_s']:.0f}")
    r += ["", "CONTROLLI"] + [f"  {x}" for x in c.righe]
    rapporto.write_text("\n".join(r) + "\n", encoding="utf-8")
    log(f"scritto {out_json} e {rapporto} ({time.time() - t0:.0f} s)")
    print("\n".join(r[:30]))


if __name__ == "__main__":
    main()
