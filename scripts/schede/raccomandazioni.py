"""Numeri delle raccomandazioni («Cosa farei», §5.4 del piano): stesse frasi nella home e nella pagina del progetto, numeri dai file dei dati.

Li legge data/progetto.js (campo `raccomandazioni`); le frasi nelle tre lingue stanno in assets/sito.js (Sito.raccomandazioni).
Dove il numero dipende dalla stima dei tempi in auto e' una forbice: estremo A = stima aperta, estremo B = stima aperta corretta col fattore del controllo."""
import json

from schede import comune
from schede.comune import leggi
from schede.r6 import SOGLIA_BUS


def calcola():
    # 1. i 10 tratti peggiori nell'ora di punta (script 106): minuti persi ogni giorno feriale
    tr = leggi("dove_nascono_ritardi.json")["classifica"]["punta_mattina"][:10]
    tratti_min = sum(t["min_persi_giorno"] for t in tr)
    # 2. punti d'ingresso dove, lasciata l'auto, il bus arriva in centro in al piu' 1,5 volte il tempo dell'auto: forbice A-B; posti che mancano li'
    ba = json.loads((comune.PROC / "r6_bus_contro_auto.json").read_text(encoding="utf-8"))
    r6 = json.loads((comune.PROC / "risultato6_v2" / "mappa_r6.json").read_text(encoding="utf-8"))
    mancano = {p["nome"]: p["mancano"] for p in r6["punti_prioritari"]}
    fc = comune.fattore_controllo()
    n_punti = ba["riepilogo"]["n_punti"]
    conv_a, conv_b = [], []
    for l in ba["luoghi"][:n_punti]:
        if l.get("tp_min") is None:
            continue
        if l["tp_min"] / l["auto_stima_min"] <= SOGLIA_BUS:
            conv_a.append(l["nome"])
        if l["tp_min"] / comune.auto_corretta(l["auto_stima_min"], fc) <= SOGLIA_BUS:
            conv_b.append(l["nome"])
    posti = lambda nomi: sum(mancano.get(n, 0) for n in nomi)
    # 3. zone in doppio svantaggio (script 95) e chi ci abita
    e2 = leggi("case_fragilita_servizi.json")["e2_doppio_svantaggio"]
    # 4. il feed ufficiale dei ritardi contro il GPS (script 27)
    r4 = leggi("risultato4_regolarita.json")
    gps, feed = r4["citta"]["0"]["ritardo"], r4["confronto_feed"]["citta"]["0"]["ritardo"]
    return {
        "tratti_min": round(tratti_min, -1),
        "punti": {"da": len(conv_a), "a": len(conv_b), "su": n_punti, "posti_da": round(posti(conv_a), -1), "posti_a": round(posti(conv_b), -1)},
        "zone": {"n": len(e2["zone"]), "abitanti": round(e2["residenti_zone_doppio_svantaggio"], -3)},
        "feed_rapporto": round(gps / feed, 1) if feed else None,
    }
