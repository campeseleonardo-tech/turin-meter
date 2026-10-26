#!/usr/bin/env python3
"""
71_parcheggi_riempimento.py  -  Risultato 6 v2, PASSO 3/G4: ANTEPRIMA del riempimento.

Cosa fa
-------
Legge dal database le letture di occupazione dei parcheggi 5T (quanti posti liberi,
ogni pochi minuti) e costruisce, per ogni parcheggio, il profilo orario medio del
riempimento separato fra giorni feriali e fine settimana. Da quel profilo ricava una
"firma": pendolare / residenziale / destinazione / misto / dato_bloccato / nessun_dato.

NOVITA' DEL GIRO 2 (19/10/2026)
-------------------------------
- Le soglie delle firme si FISSANO (restano provvisorie, ma dichiarate): un parcheggio
  fermo e' "dato_bloccato" se l'ampiezza della giornata e' sotto 0,06 (prima 0,05: cosi'
  Venchi Unica, fermo al 51%, risulta bloccato). Tutte le soglie si possono cambiare da
  riga di comando.
- Nel rapporto c'e' una TABELLA DI SENSIBILITA': la stessa firma calcolata con nove
  combinazioni di soglie (bloccato 0,04 / 0,06 / 0,08 per pendolare 0,15 / 0,20 / 0,25),
  per vedere quali parcheggi sono "fragili", cioe' cambiano firma.
- I dati restano pochi: 2 giorni feriali validi. Il giro va rifatto quando
  i giorni feriali saranno almeno 5.

Cosa legge
----------
  data/storico_backup.sqlite (sola lettura): tabelle parcheggi_5t e occupazione_pk;
  se lo storico non c'e' (o con --riassunti) i riassunti dello script 97 (data/storico_riassunti/parcheggi_*.json.gz):
  stessi numeri

Cosa scrive
-----------
  data/processed/risultato6_v2/riempimento.json
  docs/rapporti/RAPPORTO_R6V2_RIEMPIMENTO.txt

Come si lancia
--------------
  python scripts\\71_parcheggi_riempimento.py
  python scripts\\71_parcheggi_riempimento.py --soglia-bloccato 0.06 --soglia-pendolare 0.20
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import riassunti_storico as rs  # noqa: E402  (riassunti dello storico, script 97)
import comuni  # noqa: E402  (PERIODO fisso dei dati)


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
DB = RADICE / "data" / "storico_backup.sqlite"
OUT = RADICE / "data" / "processed" / "risultato6_v2" / "riempimento.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6V2_RIEMPIMENTO.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

LETTURE_MINIME_GIORNO = 230     # su ~288 possibili (una ogni 5 minuti)
ORE_NOTTE = (2, 3, 4)           # N
ORE_GIORNO = (10, 11, 12, 13, 14, 15)   # G
ORE_MATTINA = (7, 8)            # M

# SOGLIE DELLE FIRME (giro 2, 19/10/2026 — valori predefiniti, cambiali da riga di comando)
SOGLIA_BLOCCATO = 0.06          # ampiezza sotto cui il dato e' "bloccato" (era 0,05 nel giro 1)
SOGLIA_PENDOLARE = 0.20         # G - N minimo per "pendolare"
SOGLIA_PENDOLARE_WEEKEND = 0.10  # G - W minimo per "pendolare"
SOGLIA_RESIDENZIALE = 0.10      # N - G minimo per "residenziale"
SOGLIA_PIENO = 0.85             # G minimo per il contrassegno "pieno"
SOGLIA_VUOTO = 0.15             # G massimo per il contrassegno "vuoto"
# griglia della tabella di sensibilita'
GRIGLIA_BLOCCATO = (0.04, 0.06, 0.08)
GRIGLIA_PENDOLARE = (0.15, 0.20, 0.25)


def leggi_riassunti(forza_riassunti):
    """(parcheggi [[id, nome, lat, lng, totale]], giorni {data: {celle, scartate, righe}}, sorgente).
    Dallo storico si riassume al volo con la stessa funzione dello script 97; senza storico si leggono i riassunti."""
    if DB.exists() and not forza_riassunti:
        c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        try:
            parcheggi = [list(x) for x in c.execute("select id, nome, lat, lng, totale from parcheggi_5t").fetchall()]
            giorni = rs.riassumi_parcheggi(c, {x[0]: x[4] for x in parcheggi})
        finally:
            c.close()
        return parcheggi, giorni, "storico SQLite"
    if not rs.esiste_parcheggi():
        sys.exit(f"Manca lo storico ({DB}) e non ci sono riassunti dei parcheggi in {rs.CARTELLA}: "
                 "lancia scripts/97_riassunti_storico.py (o scarica i dati con scripts/scarica_dati.py).")
    return rs.carica_anagrafica()["parcheggi"], rs.carica_parcheggi(), "riassunti dello storico (script 97)"


def firma_da(N, G, M, W, ampiezza, ha_weekend, ha_letture, giorni_feriali_validi,
             soglia_bloccato=None, soglia_pendolare=None):
    """Regole del piano con le soglie del giro 2 (costanti in cima, o da riga di comando)."""
    sb = SOGLIA_BLOCCATO if soglia_bloccato is None else soglia_bloccato
    sp = SOGLIA_PENDOLARE if soglia_pendolare is None else soglia_pendolare
    if not ha_letture:
        return "nessun_dato"
    if giorni_feriali_validi < 2:
        return "dati_insufficienti"
    if ampiezza < sb:
        return "dato_bloccato"
    if G - N >= sp and (not ha_weekend or G - W >= SOGLIA_PENDOLARE_WEEKEND):
        return "pendolare"
    if N - G >= SOGLIA_RESIDENZIALE:
        return "residenziale"
    if G - N >= sp and ha_weekend and G - W < SOGLIA_PENDOLARE_WEEKEND:
        return "destinazione"
    return "misto"


def stato_da(G):
    """In piu' rispetto alla firma: pieno / vuoto, in base al giorno feriale."""
    if G is None:
        return None
    if G >= SOGLIA_PIENO:
        return "pieno"
    if G < SOGLIA_VUOTO:
        return "vuoto"
    return None


def main():
    global SOGLIA_BLOCCATO, SOGLIA_PENDOLARE, SOGLIA_PENDOLARE_WEEKEND
    global SOGLIA_RESIDENZIALE, SOGLIA_PIENO, SOGLIA_VUOTO
    ap = argparse.ArgumentParser(description="Riempimento dei parcheggi 5T (anteprima)")
    ap.add_argument("--soglia-bloccato", type=float, default=SOGLIA_BLOCCATO,
                    help=f"ampiezza sotto cui il dato e' bloccato (default {SOGLIA_BLOCCATO})")
    ap.add_argument("--soglia-pendolare", type=float, default=SOGLIA_PENDOLARE,
                    help=f"G-N minimo per 'pendolare' (default {SOGLIA_PENDOLARE})")
    ap.add_argument("--soglia-pendolare-weekend", type=float, default=SOGLIA_PENDOLARE_WEEKEND,
                    help=f"G-W minimo per 'pendolare' (default {SOGLIA_PENDOLARE_WEEKEND})")
    ap.add_argument("--soglia-residenziale", type=float, default=SOGLIA_RESIDENZIALE,
                    help=f"N-G minimo per 'residenziale' (default {SOGLIA_RESIDENZIALE})")
    ap.add_argument("--soglia-pieno", type=float, default=SOGLIA_PIENO,
                    help=f"G minimo per 'pieno' (default {SOGLIA_PIENO})")
    ap.add_argument("--soglia-vuoto", type=float, default=SOGLIA_VUOTO,
                    help=f"G massimo per 'vuoto' (default {SOGLIA_VUOTO})")
    ap.add_argument("--riassunti", action="store_true",
                    help="legge i riassunti dello storico (script 97) anche se lo storico c'e'")
    args = ap.parse_args()
    SOGLIA_BLOCCATO = args.soglia_bloccato
    SOGLIA_PENDOLARE = args.soglia_pendolare
    SOGLIA_PENDOLARE_WEEKEND = args.soglia_pendolare_weekend
    SOGLIA_RESIDENZIALE = args.soglia_residenziale
    SOGLIA_PIENO = args.soglia_pieno
    SOGLIA_VUOTO = args.soglia_vuoto

    parcheggi, giorni_dati, sorgente = leggi_riassunti(args.riassunti)
    giorni_dati = {d: g for d, g in giorni_dati.items() if comuni.nel_periodo(d, "parcheggi")}   # periodo fisso (L9): comuni.PERIODO
    n_righe = sum(g["righe"] for g in giorni_dati.values())
    print(f"sorgente: {sorgente}; parcheggi 5T: {len(parcheggi)}; righe di occupazione: {n_righe}")

    dati = {}
    for pid, nome, lat, lng, totale in parcheggi:
        dati[pid] = {"id_5t": pid, "nome": nome, "lat": lat, "lon": lng,
                     "totale_db": totale, "giorni": {}, "n_letture": 0}
    scartate = sum(g["scartate"] for g in giorni_dati.values())
    for giorno_txt, g in giorni_dati.items():
        giorno = datetime.strptime(giorno_txt, "%Y-%m-%d").date()
        for pid, ore in g["celle"].items():
            if pid in dati:
                dati[pid]["giorni"][giorno] = {int(h): c for h, c in ore.items()}   # ora -> [letture, somma occupazione]
                dati[pid]["n_letture"] += sum(c[0] for c in ore.values())
    print(f"letture scartate (stato 0 o liberi nulli): {scartate}")

    risultati = []
    for pid, d in dati.items():
        per_giorno = d["giorni"]     # data -> {ora: [letture, somma dell'occupazione]}
        giorni_validi = sorted(g for g, ore in per_giorno.items()
                               if sum(c[0] for c in ore.values()) >= LETTURE_MINIME_GIORNO)

        def media_ore(ore, weekend):
            n = s = 0
            for g in giorni_validi:
                if (g.weekday() >= 5) == weekend:
                    for h in ore:
                        if h in per_giorno[g]:
                            n += per_giorno[g][h][0]
                            s += per_giorno[g][h][1]
            return s / n if n else None

        def profilo(weekend):
            prof = {}
            for h in range(24):
                n = s = 0
                for g in giorni_validi:
                    if (g.weekday() >= 5) == weekend and h in per_giorno[g]:
                        n += per_giorno[g][h][0]
                        s += per_giorno[g][h][1]
                if n:
                    prof[h] = s / n
            return prof

        prof_f = profilo(False)
        prof_w = profilo(True)
        N = media_ore(ORE_NOTTE, False)
        G = media_ore(ORE_GIORNO, False)
        M = media_ore(ORE_MATTINA, False)
        W = media_ore(ORE_GIORNO, True)
        feriali_validi = [g for g in giorni_validi if g.weekday() < 5]
        weekend_validi = [g for g in giorni_validi if g.weekday() >= 5]
        ampiezza = (max(prof_f.values()) - min(prof_f.values())) if len(prof_f) >= 2 else 0.0
        firma = firma_da(N, G, M, W, ampiezza, bool(weekend_validi),
                         d["n_letture"] > 0, len(feriali_validi))
        stato = stato_da(G)
        griglia = {}
        for sb in GRIGLIA_BLOCCATO:
            for sp in GRIGLIA_PENDOLARE:
                griglia[f"bloccato{sb:.2f}_pendolare{sp:.2f}"] = firma_da(
                    N, G, M, W, ampiezza, bool(weekend_validi), d["n_letture"] > 0,
                    len(feriali_validi), soglia_bloccato=sb, soglia_pendolare=sp)
        risultati.append({
            "id_5t": pid, "nome": d["nome"], "lat": d["lat"], "lon": d["lon"],
            "totale_posti": d["totale_db"],
            "n_letture": d["n_letture"],
            "giorni_validi": [str(g) for g in giorni_validi],
            "profilo_feriale": {str(h): round(v, 4) for h, v in sorted(prof_f.items())},
            "profilo_weekend": {str(h): round(v, 4) for h, v in sorted(prof_w.items())},
            "N_notte_feriale": round(N, 4) if N is not None else None,
            "G_giorno_feriale": round(G, 4) if G is not None else None,
            "M_mattina_feriale": round(M, 4) if M is not None else None,
            "W_giorno_weekend": round(W, 4) if W is not None else None,
            "ampiezza": round(ampiezza, 4),
            "firma": firma, "stato": stato,
            "sensibilita": griglia,
            "fragile": len(set(griglia.values())) > 1,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "anteprima": True,
        "periodo": {"da": comuni.PERIODO["parcheggi"][0], "a": comuni.PERIODO["parcheggi"][1]},
        "etichetta": "ANTEPRIMA",
        "letture_minime_giorno": LETTURE_MINIME_GIORNO,
        "soglie": {"bloccato": SOGLIA_BLOCCATO, "pendolare": SOGLIA_PENDOLARE,
                   "pendolare_weekend": SOGLIA_PENDOLARE_WEEKEND,
                   "residenziale": SOGLIA_RESIDENZIALE,
                   "pieno": SOGLIA_PIENO, "vuoto": SOGLIA_VUOTO},
        "parcheggi": risultati,
    }, ensure_ascii=False), encoding="utf-8")

    # --- rapporto ---
    giorni_tutti = sorted({g for r in risultati for g in r["giorni_validi"]})
    feriali = [g for g in giorni_tutti if datetime.strptime(g, "%Y-%m-%d").weekday() < 5]
    weekend = [g for g in giorni_tutti if datetime.strptime(g, "%Y-%m-%d").weekday() >= 5]
    righe = []
    righe.append("RAPPORTO R6 v2 — RIEMPIMENTO DEI PARCHEGGI 5T (Passo 3 / G4, giro 2)")
    righe.append(f"ANTEPRIMA [DATI SCARSI]: {len(feriali)} giorni feriali validi "
                 f"({', '.join(feriali) or '-'}), {len(weekend)} giorni di fine settimana "
                 f"({', '.join(weekend) or '-'})")
    righe.append(f"giorni validi in tutto (feriali + fine settimana): {', '.join(giorni_tutti) or '-'}")
    righe.append("il 14/10/2026 la raccolta e' iniziata a meta' pomeriggio, quindi quel giorno "
                 "non raggiunge le letture minime e non conta")
    righe.append(f"ogni parcheggio ha letture ogni ~5 minuti; un giorno conta se ha almeno "
                 f"{LETTURE_MINIME_GIORNO} letture")
    righe.append("SOGLIE DI QUESTO GIRO (fissate il 19/10 con i dati che ci sono, da rifare con "
                 "almeno 5 giorni feriali):")
    righe.append(f"  dato_bloccato: ampiezza < {SOGLIA_BLOCCATO:.2f} (era 0,05: cosi' Venchi Unica, "
                 f"fermo al 51%, risulta bloccato)")
    righe.append(f"  pendolare: G-N >= {SOGLIA_PENDOLARE:.2f} e (W assente o G-W >= "
                 f"{SOGLIA_PENDOLARE_WEEKEND:.2f})")
    righe.append(f"  residenziale: N-G >= {SOGLIA_RESIDENZIALE:.2f}")
    righe.append(f"  destinazione: G-N >= {SOGLIA_PENDOLARE:.2f} con W presente e G-W < "
                 f"{SOGLIA_PENDOLARE_WEEKEND:.2f}")
    righe.append(f"  pieno: G >= {SOGLIA_PIENO:.2f}; vuoto: G < {SOGLIA_VUOTO:.2f}")
    righe.append("")
    righe.append("== Firma per parcheggio ==")
    righe.append("  formato: occupazione % ogni 2 ore (feriale), poi la firma")
    ordine = {"pendolare": 0, "residenziale": 1, "destinazione": 2, "misto": 3,
              "dato_bloccato": 4, "dati_insufficienti": 5, "nessun_dato": 6}
    for r in sorted(risultati, key=lambda r: (ordine.get(r["firma"], 9), r["nome"])):
        coppie = []
        for h in range(0, 24, 2):
            vals = [r["profilo_feriale"].get(str(hh)) for hh in (h, h + 1)]
            vals = [v for v in vals if v is not None]
            coppie.append(f"{round(100 * sum(vals) / len(vals)):3d}" if vals else "  -")
        stato = f" [{r['stato']}]" if r["stato"] else ""
        righe.append(f"  {r['nome'][:22]:22s} {' '.join(coppie)}  -> {r['firma']}{stato}")
    righe.append("")
    righe.append("== Valori chiave per parcheggio ==")
    righe.append("  N = notte feriale 02-05, G = giorno feriale 10-16, M = mattina feriale 07-09,"
                 " W = giorno weekend, amp = ampiezza della giornata feriale")
    for r in sorted(risultati, key=lambda r: r["nome"]):
        def pct(v):
            return f"{100 * v:5.1f}" if v is not None else "  n.d."
        righe.append(f"  {r['nome'][:22]:22s} N={pct(r['N_notte_feriale'])} G={pct(r['G_giorno_feriale'])} "
                     f"M={pct(r['M_mattina_feriale'])} W={pct(r['W_giorno_weekend'])} amp={r['ampiezza']:.2f} "
                     f"giorni={len(r['giorni_validi'])} -> {r['firma']}")
    righe.append("")
    righe.append("== TABELLA DI SENSIBILITA': la firma con nove combinazioni di soglie ==")
    righe.append("  righe = parcheggio con dati; colonne = bloccato 0,04 / 0,06 / 0,08 "
                 "x pendolare 0,15 / 0,20 / 0,25")
    righe.append("  legenda firme: P=pendoLare, R=residenziale, D=destinazione, M=misto, "
                 "B=dato_bloccato, S=dati_insufficienti, N=nessun_dato")
    lettere = {"pendolare": "P", "residenziale": "R", "destinazione": "D", "misto": "M",
               "dato_bloccato": "B", "dati_insufficienti": "S", "nessun_dato": "N"}
    righe.append("  " + " " * 24 + "  b0.04        b0.06        b0.08")
    righe.append("  " + " " * 24 + "  p.15 .20 .25  p.15 .20 .25  p.15 .20 .25")
    for r in sorted(risultati, key=lambda r: r["nome"]):
        if not r["giorni_validi"]:
            continue
        celle = []
        for sb in GRIGLIA_BLOCCATO:
            for sp in GRIGLIA_PENDOLARE:
                celle.append(lettere.get(r["sensibilita"][f"bloccato{sb:.2f}_pendolare{sp:.2f}"], "?"))
        testo = " ".join(celle[:3]) + "  " + " ".join(celle[3:6]) + "  " + " ".join(celle[6:])
        righe.append(f"  {r['nome'][:22]:22s}  {testo}")
    fragili = [r for r in risultati if r.get("fragile")]
    righe.append("")
    righe.append(f"== Parcheggi 'fragili' (la firma cambia al variare delle soglie): {len(fragili)} ==")
    for r in sorted(fragili, key=lambda r: r["nome"]):
        valori = sorted(set(r["sensibilita"].values()))
        righe.append(f"  {r['nome'][:22]:22s} firme possibili: {', '.join(valori)}")
    RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")

    print(f"Scritto: {OUT}")
    print(f"Scritto: {RAPPORTO}")
    from collections import Counter
    print("firme:", dict(Counter(r["firma"] for r in risultati)))
    for nome in ("FERMI", "RACCONIGI", "UNIONE SOVIETICA", "V PADIGLIONE", "VENCHI UNICA",
                 "SOFIA", "PORTA SUSA FS", "CAIO MARIO", "STURA"):
        r = next((x for x in risultati if x["nome"] == nome), None)
        if r:
            print(f"  {nome:20s} {r['firma']:18s} {r['stato']} N={r['N_notte_feriale']} G={r['G_giorno_feriale']}")


if __name__ == "__main__":
    sys.exit(main())
