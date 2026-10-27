"""Numeri delle raccomandazioni («Cosa farei», §5.4 del piano): stesse frasi nella home e nella pagina del progetto, numeri dai file dei dati.

Li legge data/progetto.js (campo `raccomandazioni`); le frasi nelle tre lingue stanno in assets/sito.js (Sito.raccomandazioni).
I tempi in auto sono quelli corretti col fattore del controllo (una sola stima, decisione 16 di §2)."""
import json

from schede import comune
from schede.comune import leggi
from schede.r6 import SOGLIA_BUS


def calcola():
    # 1. i 10 tratti peggiori nell'ora di punta (script 106): minuti persi ogni giorno feriale
    dr = leggi("dove_nascono_ritardi.json")
    tratti_min = sum(t["min_persi_giorno"] for t in dr["classifica"]["punta_mattina"][:10])     # media per giorno feriale, solo nella fascia di punta
    fascia = [int(x) for x in dr["regole"]["fasce"]["punta_mattina"].split("-")]                # «7-9»
    # 2. punti d'ingresso dove, lasciata l'auto, il bus arriva in centro in al piu' 1,5 volte il tempo dell'auto (tempo in auto corretto col controllo); posti che mancano li'
    ba = json.loads((comune.PROC / "r6_bus_contro_auto.json").read_text(encoding="utf-8"))
    r6 = json.loads((comune.PROC / "risultato6_v2" / "mappa_r6.json").read_text(encoding="utf-8"))
    mancano = {p["nome"]: p["mancano"] for p in r6["punti_prioritari"]}
    fc = comune.fattore_controllo()
    n_punti = ba["riepilogo"]["n_punti"]
    conv = [l["nome"] for l in ba["luoghi"][:n_punti]
            if l.get("tp_min") is not None and l["tp_min"] / comune.auto_corretta(l["auto_stima_min"], fc) <= SOGLIA_BUS]
    posti = [mancano.get(n, 0) for n in conv]      # posti che mancano in ciascun parcheggio
    # 3. zone in doppio svantaggio (script 95) e chi ci abita
    e2 = leggi("case_fragilita_servizi.json")["e2_doppio_svantaggio"]
    # 4. il feed ufficiale dei ritardi contro il GPS (script 27)
    r4 = leggi("risultato4_regolarita.json")
    gps, feed = r4["citta"]["0"]["ritardo"], r4["confronto_feed"]["citta"]["0"]["ritardo"]
    return {
        "tratti_min": round(tratti_min, -1), "tratti_fascia": fascia,
        "punti": {"n": len(conv), "su": n_punti, "posti_min": round(min(posti), -1) if posti else 0, "posti_max": round(max(posti), -1) if posti else 0},
        "zone": {"n": len(e2["zone"]), "abitanti": round(e2["residenti_zone_doppio_svantaggio"], -3)},
        "feed_rapporto": round(gps / feed, 1) if feed else None,
    }
