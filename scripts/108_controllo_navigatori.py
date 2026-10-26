# -*- coding: utf-8 -*-
"""
scripts/108_controllo_navigatori.py - controllo a mano della stima aperta dell'auto con i navigatori (F3, regole §6.2 del piano).

I percorsi sono 20, fissati in anticipo: i 12 punti prioritari del R6 -> Piazza Castello (script 94) e gli 8 viaggi in auto piu' frequenti del
mattino (coppie di zone IMQ con piu' auto, gruppi a e b dello script 93; fra i loro punti di calcolo, il piu' pesante di ogni zona).
Regola cambiata da Leo il 25/10/2026 (PIANO §2.4, §6.2): TomTom si usa da programma SOLO qui, per questo controllo (60 richieste, nessun dato TomTom nei file
pubblici, nessun uso nelle stime). Google Maps resta a mano e facoltativo.

  python scripts\\108_controllo_navigatori.py --elenco     scrive data/ref/controllo_navigatori.csv (percorsi, coordinate, link Google Maps) con le colonne da compilare:
                                                          google_min, google_max, tomtom_min, tomtom_max (minuti, «tempo tipico» minimo e massimo con
                                                          «Partenza: martedi' alle 8:00»), data_lettura. NON contiene la nostra stima: la lettura e' alla cieca.
  python scripts\\108_controllo_navigatori.py --tomtom      chiede a TomTom (Routing API, chiave in config_locale.json, campo tomtom_chiave) il tempo con traffico
                                                          previsto del martedi' prossimo alle 7:45, 8:00 e 8:15 per ognuno dei 20 percorsi e scrive
                                                          tomtom_min/tomtom_max (minimo e massimo dei tre) e data_lettura nel CSV privato.
  python scripts\\108_controllo_navigatori.py --calcola    legge il CSV compilato e scrive il riepilogo e la forma di pubblicazione scelta dalla regola.

Confronto: la stima aperta alle 8 SENZA i 5 minuti di parcheggio e cammino (i navigatori danno il tempo di guida). Errore = (stima aperta - centro della
forbice del navigatore) / centro. Con due navigatori il centro e' la media dei due centri, e «dentro la forbice» vuol dire dentro l'unione delle due forbici.
Regola di pubblicazione (mediana dell'errore assoluto):
  fino al 20%  e almeno 12 percorsi su 20 dentro la forbice -> la stima aperta come numero;
  dal 20 al 35% (o fino al 20% con meno di 12 dentro)          -> una forbice: stima aperta - stima piu' favorevole all'auto;
  oltre il 35%                                                 -> solo classi (mezzi piu' veloci / simili / piu' lenti dell'auto) e una nota.
Pubblico: solo il riepilogo data/processed/controllo_navigatori_riepilogo.json (mediana dell'errore, percorsi dentro la forbice, forma scelta).
Il CSV coi tempi letti e il rapporto restano privati.
"""
import argparse
import csv
import datetime as dt
import json
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
import zoneinfo
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
PROC = RADICE / "data" / "processed"
CSV = RADICE / "data" / "ref" / "controllo_navigatori.csv"
RIEPILOGO = PROC / "controllo_navigatori_riepilogo.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_CONTROLLO_NAVIGATORI.txt"
N_PUNTI, N_COPPIE = 12, 8
SOGLIA_NUMERO, SOGLIA_FORBICE = 0.20, 0.35
MIN_DENTRO = 12
COLONNE = ["id", "tipo", "nome", "da_lat", "da_lon", "a_lat", "a_lon", "link_google", "google_min", "google_max", "tomtom_min", "tomtom_max", "data_lettura", "nota"]
LEGGI = ["google_min", "google_max", "tomtom_min", "tomtom_max"]


def link_google(a, b):
    q = urllib.parse.urlencode({"api": 1, "origin": f"{a[0]:.5f},{a[1]:.5f}", "destination": f"{b[0]:.5f},{b[1]:.5f}", "travelmode": "driving"})
    return "https://www.google.com/maps/dir/?" + q


def percorsi():
    """I 20 percorsi (id, tipo, nome, da, a) dai JSON degli script 94 e 93 e dalle zone dello script 93."""
    m93 = comuni.carica_script("93_tp_contro_auto.py")
    r94 = json.loads((PROC / "r6_bus_contro_auto.json").read_text(encoding="utf-8"))
    t93 = json.loads((PROC / "tp_contro_auto.json").read_text(encoding="utf-8"))
    out = []
    punti = [l for l in r94["luoghi"] if l["tipo"] == "punto_prioritario"][:N_PUNTI]
    if len(punti) != N_PUNTI:
        raise SystemExit(f"ERRORE: servono {N_PUNTI} punti prioritari in r6_bus_contro_auto.json, ne ho {len(punti)}")
    for k, l in enumerate(punti, 1):
        out.append((f"P{k:02d}", "punto_prioritario", f"{l['nome']} → Piazza Castello", (l["lat"], l["lon"]), m93.CASTELLO))
    zone = m93.carica_zone(False)
    coppie = sorted((p for p in t93["coppie"] if p["gruppo"] in ("a", "b") and p["da"] in zone and p["a"] in zone), key=lambda p: -p["auto"])[:N_COPPIE]
    for k, p in enumerate(coppie, 1):
        za, zb = zone[p["da"]], zone[p["a"]]
        pa = max(za["punti"], key=lambda x: x["peso"])
        pb = max(zb["punti"], key=lambda x: x["peso"])
        out.append((f"C{k:02d}", "coppia_imq", f"{za['nome']} → {zb['nome']}", (pa["lat"], pa["lon"]), (pb["lat"], pb["lon"])))
    return out


def elenco(forza):
    if CSV.exists() and not forza:
        compilato = any(r.get(c, "").strip() for r in csv.DictReader(CSV.open(encoding="utf-8")) for c in LEGGI)
        if compilato:
            raise SystemExit(f"ERRORE: {CSV} contiene gia' dei tempi letti a mano: non lo riscrivo (--forza per farlo lo stesso).")
    righe = [{"id": i, "tipo": t, "nome": n, "da_lat": f"{a[0]:.5f}", "da_lon": f"{a[1]:.5f}", "a_lat": f"{b[0]:.5f}", "a_lon": f"{b[1]:.5f}",
              "link_google": link_google(a, b), **{c: "" for c in ("google_min", "google_max", "tomtom_min", "tomtom_max", "data_lettura", "nota")}}
             for i, t, n, a, b in percorsi()]
    CSV.parent.mkdir(parents=True, exist_ok=True)
    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNE)
        w.writeheader()
        w.writerows(righe)
    print(f"Scritto {CSV} con {len(righe)} percorsi.")
    print("LEO: per ogni riga apri il link (Google Maps), imposta «Partenza: martedi' alle 8:00», leggi il tempo tipico minimo e massimo in minuti e scrivili in")
    print("google_min e google_max, con la data della lettura in data_lettura (AAAA-MM-GG). Se vuoi, fai lo stesso con il pianificatore web di TomTom (a mano) in")
    print("tomtom_min e tomtom_max. Niente letture automatiche. Poi: python scripts\\108_controllo_navigatori.py --calcola")


def prossimo_martedi():
    oggi = dt.date.today()
    return oggi + dt.timedelta(days=(1 - oggi.weekday()) % 7 or 7)


def chiave_tomtom():
    try:
        c = json.loads((RADICE / "config_locale.json").read_text(encoding="utf-8"))
    except OSError:
        c = {}
    return c.get("tomtom_chiave", "")


def tempo_tomtom(chiave, a, b, partenza):
    """Secondi di guida con traffico previsto (TomTom Routing API) da a a b, partendo a `partenza` (datetime con fuso)."""
    q = urllib.parse.urlencode({"key": chiave, "departAt": partenza.isoformat(timespec="seconds"), "traffic": "true", "travelMode": "car", "routeType": "fastest"})
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{a[0]:.5f},{a[1]:.5f}:{b[0]:.5f},{b[1]:.5f}/json?{q}"
    with urllib.request.urlopen(url, timeout=30) as r:
        j = json.loads(r.read().decode("utf-8"))
    return j["routes"][0]["summary"]["travelTimeInSeconds"]


def tomtom():
    chiave = chiave_tomtom()
    if not chiave:
        raise SystemExit("ERRORE: manca tomtom_chiave in config_locale.json (il file non e' in git; la chiave non si stampa mai)")
    if not CSV.exists():
        raise SystemExit(f"ERRORE: manca {CSV}: lancia prima --elenco")
    righe = list(csv.DictReader(CSV.open(encoding="utf-8")))
    giorno = prossimo_martedi()
    fuso = zoneinfo.ZoneInfo("Europe/Rome")
    orari = [dt.datetime.combine(giorno, dt.time(h, m), tzinfo=fuso) for h, m in ((7, 45), (8, 0), (8, 15))]
    for r in righe:
        a, b = (float(r["da_lat"]), float(r["da_lon"])), (float(r["a_lat"]), float(r["a_lon"]))
        try:
            minuti = [tempo_tomtom(chiave, a, b, o) / 60.0 for o in orari]
        except urllib.error.HTTPError as e:
            raise SystemExit(f"ERRORE TomTom {e.code} su {r['id']}: controlla la chiave e i limiti (le righe dopo questa non sono state scritte)")
        r["tomtom_min"], r["tomtom_max"] = f"{min(minuti):.1f}", f"{max(minuti):.1f}"
        r["data_lettura"] = dt.date.today().isoformat()
        r["nota"] = (r.get("nota") or "") + f" TomTom Routing API, partenza {giorno.isoformat()} 7:45-8:15"
        print(f"{r['id']}: {r['tomtom_min']}-{r['tomtom_max']} min")
    with CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNE)
        w.writeheader()
        w.writerows(righe)
    print(f"Scritto {CSV}. Ora: python scripts\\108_controllo_navigatori.py --calcola")


def numero(s):
    s = (s or "").strip().replace(",", ".")
    return float(s) if s else None


def stime_aperte(righe):
    """Per ogni riga: (stima aperta alle 8 senza parcheggio, stima favorevole senza parcheggio) in minuti."""
    m93 = comuni.carica_script("93_tp_contro_auto.py")
    extra = [(r["nome"], (float(r["da_lat"]), float(r["da_lon"])), (float(r["a_lat"]), float(r["a_lon"]))) for r in righe]
    t93 = json.loads((PROC / "tp_contro_auto.json").read_text(encoding="utf-8"))
    f_alto = t93["parametri"]["fattore_punta"]
    t_libero, nodi_extra, _sp = m93.matrice_auto({}, extra)
    aperto = comuni.TempiAutoAperti()
    t8 = aperto.tempi(sorted({a for a, _ in t_libero}), 8)
    return [(t8[nodi_extra[k]] / 60.0, t_libero[nodi_extra[k]] / 60.0 * f_alto) for k in range(len(righe))]


def calcola(forma_scelta=None):
    if not CSV.exists():
        raise SystemExit(f"ERRORE: manca {CSV}: lancia prima --elenco")
    righe = list(csv.DictReader(CSV.open(encoding="utf-8")))
    c = comuni.Controlli()
    letti = []
    for r in righe:
        g = (numero(r["google_min"]), numero(r["google_max"]))
        t = (numero(r["tomtom_min"]), numero(r["tomtom_max"]))
        forbici = [f for f in (g, t) if f[0] is not None and f[1] is not None]
        if forbici:
            if any(lo > hi or lo <= 0 for lo, hi in forbici):
                raise SystemExit(f"ERRORE: {r['id']}: minimo maggiore del massimo o tempo non positivo")
            letti.append((r, forbici))
    c("percorsi letti a mano (su 20)", len(letti) >= 12, dettaglio=f"{len(letti)} su {len(righe)}", bloccante=len(letti) == 0)
    stime = stime_aperte([r for r, _ in letti])
    dati, errori, dentro = [], [], 0
    for (r, forbici), (stima, favorevole) in zip(letti, stime):
        centro = statistics.mean((lo + hi) / 2 for lo, hi in forbici)
        err = (stima - centro) / centro
        in_forbice = any(lo <= stima <= hi for lo, hi in forbici) or (min(lo for lo, _ in forbici) <= stima <= max(hi for _, hi in forbici))
        dentro += in_forbice
        errori.append(err)
        dati.append({"id": r["id"], "nome": r["nome"], "stima_min": round(stima, 1), "favorevole_min": round(favorevole, 1), "centro_min": round(centro, 1),
                     "forbici": forbici, "errore_pct": round(100 * err, 1), "dentro": bool(in_forbice), "data_lettura": r["data_lettura"]})
    mediana = statistics.median(abs(e) for e in errori)
    # la forma di pubblicazione
    if mediana <= SOGLIA_NUMERO and dentro >= MIN_DENTRO:
        forma = "numero"
    elif mediana <= SOGLIA_FORBICE:
        forma = "forbice"
    else:
        forma = "classi"
    forma_regola = forma
    if forma_scelta:   # decisione di Leo (25/10/2026): scarto sistematico, niente correzione, solo classi
        forma = forma_scelta
    usa_tomtom = any(numero(r["tomtom_min"]) is not None for r, _ in letti)
    segno = statistics.median(errori)
    date = sorted({d["data_lettura"] for d in dati if d["data_lettura"]})
    riepilogo = {"percorsi": len(letti), "dentro_la_forbice": int(dentro), "mediana_errore_assoluto_pct": round(100 * mediana, 1), "mediana_errore_con_segno_pct": round(100 * segno, 1),
                 "forma": forma, "forma_per_regola": forma_regola, "scarto_sistematico": bool(all(e < 0 for e in errori) or all(e > 0 for e in errori)),
                 "nota": ("la stima aperta e' piu' veloce del navigatore in tutti i percorsi: l'auto reale e' piu' lenta di come la stimiamo, quindi il vantaggio dei mezzi pubblici "
                          "e' probabilmente sottostimato; per questo i numeri sono una forbice fra la stima aperta e la stessa stima corretta col fattore del controllo" if statistics.median(errori) < 0 else ""),
                 "navigatori": (["Google Maps (a mano)"] if any(numero(r["google_min"]) is not None for r, _ in letti) else []) + (["TomTom (Routing API, interrogato da programma solo per questo controllo)"] if usa_tomtom else []),
                 "partenza": "martedì, fra le 7:45 e le 8:15", "date_lettura": [date[0], date[-1]] if date else None,
                 "regola": f"mediana errore assoluto fino al {SOGLIA_NUMERO:.0%} e almeno {MIN_DENTRO} percorsi dentro la forbice: numero; fino al {SOGLIA_FORBICE:.0%}: forbice; oltre: classi",
                 "controllo": "tempo di guida previsto dai navigatori (senza i 5 minuti di parcheggio)", "calcolato": dt.date.today().isoformat()}
    c(f"forma di pubblicazione: {forma}", True, dettaglio=f"mediana dell'errore {100 * mediana:.1f}%, {dentro} su {len(letti)} dentro la forbice")
    RIEPILOGO.write_text(json.dumps(riepilogo, ensure_ascii=False, indent=1), encoding="utf-8")
    r_ = ["CONTROLLO A MANO COI NAVIGATORI (script 108) - rapporto PRIVATO", f"generato: {dt.datetime.now().isoformat(timespec='seconds')}", "",
          f"Percorsi letti: {len(letti)} su {len(righe)}. Navigatori: {', '.join(riepilogo['navigatori'])}. Mediana dell'errore assoluto: {100 * mediana:.1f}% "
          f"(con segno {100 * segno:+.1f}%: positivo = la stima aperta e' piu' lenta del navigatore). Dentro la forbice: {dentro} su {len(letti)}.",
          f"FORMA DI PUBBLICAZIONE: {forma}", "",
          "  id | percorso | stima aperta | favorevole | centro navigatore | forbice/i | errore | dentro"]
    for d in dati:
        r_.append(f"  {d['id']} | {d['nome']} | {d['stima_min']} | {d['favorevole_min']} | {d['centro_min']} | {d['forbici']} | {d['errore_pct']:+.1f}% | {'si' if d['dentro'] else 'no'}")
    r_ += ["", "CONTROLLI"] + [f"  {x}" for x in c.righe]
    RAPPORTO.write_text("\n".join(r_) + "\n", encoding="utf-8")
    print("\n".join(r_))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--elenco", action="store_true", help="scrive il CSV dei 20 percorsi da compilare a mano")
    g.add_argument("--tomtom", action="store_true", help="compila tomtom_min/tomtom_max chiedendo a TomTom (serve tomtom_chiave in config_locale.json)")
    g.add_argument("--calcola", action="store_true", help="legge il CSV compilato e scrive il riepilogo")
    ap.add_argument("--forma", choices=["numero", "forbice", "classi"], help="con --calcola: forma di pubblicazione scelta da Leo al posto di quella della regola")
    ap.add_argument("--forza", action="store_true", help="con --elenco: riscrive anche se il CSV ha gia' dei tempi")
    args = ap.parse_args()
    if args.elenco:
        elenco(args.forza)
    elif args.tomtom:
        tomtom()
    else:
        calcola(args.forma)


if __name__ == "__main__":
    main()
