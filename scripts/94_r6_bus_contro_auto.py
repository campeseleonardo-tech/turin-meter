# -*- coding: utf-8 -*-
"""
scripts/94_r6_bus_contro_auto.py - Risultato 6, parte C (C1, C2, C3): dal parcheggio al centro, il mezzo pubblico conviene all'auto?

Sola lettura sui dati. Per ogni punto prioritario del R6 (script 84, porte.json) e per ogni interscambio esistente del
Comune si confronta il viaggio verso Piazza Castello:
  - mezzi pubblici: r5py come lo script 93 (funzioni importate da li'), giorno 2026-10-12, partenza 7:45 con
    finestra di 30 minuti, mediana, cammino a 4,8 km/h;
  - auto: stima aperta (comuni.TempiAutoAperti, §6.1 del piano) del percorso «luogo -> Piazza Castello» alle 8 + 5 minuti per parcheggiare;
    sensori 5T con fattore unico (la stima piu' favorevole all'auto) da tp_contro_auto.json. Campi: auto_stima_min e auto_favorevole_min.

Regola di classe. Rapporto = tempo coi mezzi / tempo in auto. Fino a L7 le classi erano tre (conviene / dipende dal traffico / non conviene)
con due stime dell'auto. Dal giro L8 (24/10/2026, decisione di Leo) la stima dell'auto e' UNA (dal giro F3: la stima aperta, non piu' un servizio esterno);
la regola (rapporto massimo 1,5, 5 minuti di parcheggio) e' quella di prima, ma le classi sono due:
  - «il bus conviene»:      rapporto <= 1,5 con la stima aperta;
  - «il bus non conviene»:  rapporto oltre 1,5 (anche se i mezzi non arrivano entro 120 minuti).
«dipende dal traffico» sparisce. La stima dei sensori 5T (fattore unico, la piu' favorevole all'auto) resta nel JSON come sensibilita'
(rapporto_alto, pareggio_alto_min). I punti non si tolgono dall'elenco del R6: si aggiunge solo la classe.

Minuti di pareggio (misura principale della scheda, senza soglie scelte da noi): quanti minuti si devono perdere in
centro per parcheggiare perche' il tempo in auto sia uguale al tempo coi mezzi, cioe'
  tempo coi mezzi = flusso libero x fattore + minuti  ->  minuti = tempo coi mezzi - flusso libero x fattore.
Con i due fattori viene una forbice per luogo (fattore basso = auto lenta = meno minuti). Sotto 0 vale 0: il bus e' gia'
piu' veloce. Classi e sensibilita' 5/10/15 restano nel JSON per confronto.

Come si lancia
--------------
  python scripts\\94_r6_bus_contro_auto.py
Prima servono gli script 84 (punti) e 93 (fattori).

Uscite: data/processed/r6_bus_contro_auto.json, docs/rapporti/RAPPORTO_R6_BUS_CONTRO_AUTO.txt
"""
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
PROC = RADICE / "data" / "processed"
PORTE = PROC / "risultato6_v2" / "porte.json"
TP_AUTO = PROC / "tp_contro_auto.json"
OUT_JSON = PROC / "r6_bus_contro_auto.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6_BUS_CONTRO_AUTO.txt"
PARZIALE = PROC / "r6_bus_contro_auto_parziale.npz"      # diverso da quello dello script 93: non si sovrascrivono

MINUTI_SENSIBILITA = (5, 10, 15)                          # minuti per parcheggiare in centro; la classe ufficiale e' quella con 5
PAREGGIO_MAX = 120                                        # controllo: minuti di pareggio oltre questo valore = errore
SOGLIA = 1.5                                              # rapporto massimo perche' il bus «convenga»
CLASSI = {"conviene": "il bus conviene", "non_conviene": "il bus non conviene"}
INTERSCAMBI_POCO_PIENI = ("SOFIA", "VENCHI UNICA")


def classe_di(r_stima):
    """Classe con la sola stima aperta: conviene se il rapporto non supera 1,5."""
    return "conviene" if r_stima is not None and r_stima <= SOGLIA else "non_conviene"


def main():
    t0 = time.time()
    m93 = comuni.carica_script("93_tp_contro_auto.py")
    m93.PARZIALE = PARZIALE
    c = comuni.Controlli()

    def log(m):
        print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

    c(f"esistono {PORTE.name} e {TP_AUTO.name} (lancia prima gli script 84 e 93)", PORTE.exists() and TP_AUTO.exists(), bloccante=True)
    t93 = json.loads(TP_AUTO.read_text(encoding="utf-8"))
    f_alto, f_basso = t93["parametri"]["fattore_punta"], t93["parametri"]["fattore_basso_google"]
    # F3: per i punti verso Piazza Castello la stima principale e' quella aperta, calcolata per ogni percorso alle 8 (comuni.TempiAutoAperti).
    # f_basso: numero riassuntivo (mediana dei fattori dei luoghi).
    fonte_basso = "stima aperta: sensori 5T e sonde bus, 20 secondi per semaforo, percorso «luogo -> Piazza Castello» alle 8"
    c("fattori letti dal JSON dello script 93 (calcolo completo, non prova)", not t93["parametri"].get("prova"),
      dettaglio=f"sensori {f_alto:g}; stima aperta per percorso", bloccante=True)
    porte = json.loads(PORTE.read_text(encoding="utf-8"))

    luoghi = [{"nome": p["nome"], "tipo": "punto_prioritario", "lat": p["centro"][0], "lon": p["centro"][1], "mancano": p["mancano"],
               "dist_centro_km": p["dist_centro_km"]} for p in porte["punti_prioritari"]]
    n_punti = len(luoghi)
    for p in porte["parcheggi"]:
        if p["tipo"] == "interscambio_ufficiale":
            luoghi.append({"nome": p["nome"], "tipo": "interscambio", "lat": p["lat"], "lon": p["lon"], "posti": p["posti"],
                           "stato": p["stato"], "riempimento_giorno": p.get("riempimento_giorno"), "descrizione": p.get("descrizione"),
                           "auto_passaggio_txt": p.get("auto_passaggio_txt")})
    c("tutti i 12 punti prioritari del R6 e i 5 interscambi presenti", n_punti == len(porte["punti_prioritari"]) == 12 and len(luoghi) - n_punti == 5,
      dettaglio=f"{n_punti} punti + {len(luoghi) - n_punti} interscambi", bloccante=True)
    extra = [(f"{l['nome']} → Piazza Castello", (l["lat"], l["lon"]), m93.CASTELLO) for l in luoghi]

    log("tempi in auto sulla rete del modello del traffico ...")
    t_auto, nodi_extra, spostati = m93.matrice_auto({}, extra)
    log(f"  punti agganciati alla parte principale della rete: {spostati['n']} su {spostati['su']}")
    modello = m93.StimaAperta(comuni.TempiAutoAperti(log=log), t_auto, {}, nodi_extra, [l["nome"] for l in luoghi])
    log("tempi coi mezzi pubblici (r5py, cammino a 4,8 km/h) ...")
    ids, T = m93.matrice_tp({}, extra, 20, log)
    pos = {i: k for k, i in enumerate(ids)}

    for k, l in enumerate(luoghi):
        libero = t_auto[nodi_extra[k]] / 60.0
        tp = T[pos[f"NOTO{k}_A"], pos[f"NOTO{k}_B"]]
        l["libero_min"] = round(libero, 1)
        f_l, _ = modello.luogo(l["nome"], "08:00")
        l["fattore_basso"] = round(f_l, 2)
        l["auto_favorevole_min"] = round(m93.punta(libero, f_alto), 1)
        l["auto_stima_min"] = round(m93.punta(libero, f_l), 1)
        # L23: tempo coi mezzi corretto con le misure (script 105); quello da orario resta in tp_orario_min
        l["tp_orario_min"] = round(float(tp), 1) if tp == tp else None
        l["tp_min"] = round(comuni.tempo_mezzi_corretto(float(tp), "punta_mattina"), 1) if tp == tp else None
        if l["tp_min"] is None:
            l["rapporto_alto"] = l["rapporto_basso"] = None
            l["nota"] = "nessun collegamento coi mezzi entro 120 minuti"
            l["classe"] = "non_conviene"
        else:
            l["rapporto_alto"] = round(l["tp_min"] / l["auto_favorevole_min"], 2)
            l["rapporto_basso"] = round(l["tp_min"] / l["auto_stima_min"], 2)
            l["classe"] = classe_di(l["rapporto_basso"])
        l["classe_testo"] = CLASSI[l["classe"]]
        # minuti di pareggio: parcheggio in centro che rende l'auto lenta quanto il bus (forbice dei due fattori)
        if l["tp_min"] is None:
            l["pareggio_basso_min"] = l["pareggio_alto_min"] = None
        else:
            l["pareggio_basso_min"] = round(max(0.0, l["tp_min"] - libero * f_l), 1)
            l["pareggio_alto_min"] = round(max(0.0, l["tp_min"] - libero * f_alto), 1)
        # sensibilita': stessa regola con 5, 10 e 15 minuti di parcheggio al posto dei 5 predefiniti
        l["classi_sensibilita"] = {}
        for m in MINUTI_SENSIBILITA:
            if l["tp_min"] is None:
                l["classi_sensibilita"][str(m)] = "non_conviene"
            else:
                l["classi_sensibilita"][str(m)] = classe_di(l["tp_min"] / (libero * f_l + m))

    punti, inter = luoghi[:n_punti], luoghi[n_punti:]
    f_basso = round(float(np.median([l["fattore_basso"] for l in luoghi])), 2)     # numero riassuntivo: mediana dei fattori dei 17 luoghi
    conta = {k: sum(1 for l in punti if l["classe"] == k) for k in CLASSI}
    conta_i = {k: sum(1 for l in inter if l["classe"] == k) for k in CLASSI}

    def mediana(v):
        v = sorted(x for x in v if x is not None)
        if not v:
            return None
        n = len(v)
        return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2

    pareggio = {"punti": {"mediana_basso_min": mediana(l["pareggio_basso_min"] for l in punti),
                          "mediana_alto_min": mediana(l["pareggio_alto_min"] for l in punti)},
                "interscambi": {"mediana_basso_min": mediana(l["pareggio_basso_min"] for l in inter),
                                "mediana_alto_min": mediana(l["pareggio_alto_min"] for l in inter)}}
    pv = [x for l in luoghi for x in (l["pareggio_basso_min"], l["pareggio_alto_min"]) if x is not None]
    c(f"minuti di pareggio fra 0 e {PAREGGIO_MAX}", all(0 <= x <= PAREGGIO_MAX for x in pv),
      dettaglio=f"da {min(pv):g} a {max(pv):g}" if pv else "nessun valore", bloccante=True)
    c("mediana dei punti: con la stima dei sensori >= con quella aperta",
      pareggio["punti"]["mediana_alto_min"] is not None and pareggio["punti"]["mediana_alto_min"] >= pareggio["punti"]["mediana_basso_min"],
      dettaglio=f"basso {pareggio['punti']['mediana_basso_min']}, alto {pareggio['punti']['mediana_alto_min']}", bloccante=True)

    sens = {}
    for m in MINUTI_SENSIBILITA:
        sens[str(m)] = {"punti": {k: sum(1 for l in punti if l["classi_sensibilita"][str(m)] == k) for k in CLASSI},
                        "interscambi": {k: sum(1 for l in inter if l["classi_sensibilita"][str(m)] == k) for k in CLASSI}}
    c("la sensibilita' con 5 minuti coincide con la classe ufficiale", sens["5"]["punti"] == conta and sens["5"]["interscambi"] == conta_i and
      all(l["classi_sensibilita"]["5"] == l["classe"] for l in luoghi), bloccante=True)
    c("nessun tempo nullo, negativo o infinito", all(np.isfinite(l["libero_min"]) and l["libero_min"] > 0 and l["auto_stima_min"] > 0
                                                       and (l["tp_min"] is None or l["tp_min"] > 0) for l in luoghi), bloccante=True)
    c("tutti i punti del R6 hanno una classe", all(l["classe"] in CLASSI for l in punti) and len(punti) == len(porte["punti_prioritari"]), bloccante=True)
    c("il rapporto con la stima aperta non supera quello con i sensori", all(l["rapporto_basso"] <= l["rapporto_alto"] for l in luoghi if l["tp_min"] is not None),
      dettaglio="l'auto piu' lenta (stima aperta) rende il rapporto piu' basso")
    c("senza collegamento coi mezzi", True, dettaglio=f"{sum(1 for l in luoghi if l['tp_min'] is None)} luoghi")

    # ---- paragrafo sugli interscambi esistenti
    def virgola(x, dec=1):
        return f"{x:.{dec}f}".replace(".", ",")

    def riga_i(l):
        if l["tp_min"] is None:
            return f"{l['nome']}: i mezzi non arrivano a Piazza Castello entro 120 minuti; {l['classe_testo']}."
        return (f"{l['nome']} ({l['stato'].replace('_', ' ')}): {l['tp_min']:.0f} minuti coi mezzi contro {l['auto_stima_min']:.0f} in auto con la stima aperta "
                f"({l['auto_favorevole_min']:.0f} con quella dei sensori; rapporto {virgola(l['rapporto_basso'])}); {l['classe_testo']}.")
    par_inter = "Interscambi esistenti del Comune, stesso test. " + " ".join(riga_i(l) for l in inter)
    poco_pieni = [l for l in inter if l["nome"] in INTERSCAMBI_POCO_PIENI]
    if poco_pieni:
        par_inter += " Quelli poco pieni: " + "; ".join(f"da {l['nome']} {l['classe_testo']}" for l in poco_pieni) + "."

    out = {"stimato": True,
           "parametri": {"destinazione": "Piazza Castello", "giorno": str(m93.GIORNO), "partenza": f"{m93.PARTENZA:%H:%M}", "finestra_min": m93.FINESTRA_MIN,
                         "velocita_piedi_kmh": m93.VEL_PIEDI_KMH, "minuti_parcheggio": m93.MIN_PARCHEGGIO, "fattore_alto": f_alto,
                         "fattore_basso": f_basso, "fonte_basso": fonte_basso, "soglia_rapporto": SOGLIA, "punti_spostati": spostati},
           "regola": {"conviene": "rapporto <= 1,5 con la stima aperta", "non_conviene": "rapporto oltre 1,5 con la stima aperta",
                      "nota": "dal giro L8 le classi sono due (era: conviene / dipende / non conviene con due stime); la stima dei sensori resta come sensibilita'"},
           "pareggio": pareggio,
           "sensibilita_parcheggio": sens,
           "riepilogo": {"punti": conta, "interscambi": conta_i, "n_punti": len(punti), "n_interscambi": len(inter)},
           "luoghi": luoghi, "paragrafo_interscambi": par_inter, "controlli": list(c.righe)}
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    r = ["RAPPORTO R6: IL BUS CONTRO L'AUTO VERSO PIAZZA CASTELLO (Risultato 6, parte C, STIMATO)",
         f"generato: {dt.datetime.now().isoformat(timespec='seconds')}", "",
         f"Mezzi pubblici: r5py, giorno {m93.GIORNO}, partenza 7:45-8:15, mediana, cammino a {m93.VEL_PIEDI_KMH:g} km/h.",
         f"Auto: flusso libero x fattore di punta + {m93.MIN_PARCHEGGIO:.0f} minuti. Stima principale: {fonte_basso} (fattore mediano {f_basso:g}). Sensibilita': sensori 5T, fattore {f_alto:g} (solo traffico: la piu' favorevole all'auto).",
         "Rapporto = tempo coi mezzi / tempo in auto. Regola della classe (rapporto massimo 1,5; dal giro L8 due classi, con la sola stima aperta):",
         "  il bus conviene: rapporto <= 1,5; il bus non conviene: oltre 1,5.", "",
         f"PUNTI PRIORITARI DEL R6: {conta['conviene']} il bus conviene, {conta['non_conviene']} il bus non conviene (su {len(punti)})",
         "  luogo | mancano | mezzi min | auto min (sensori - stima aperta) | rapporto (stima aperta - sensori) | classe"]
    for l in punti:
        rap = f"{l['rapporto_basso']:.2f}-{l['rapporto_alto']:.2f}" if l["tp_min"] is not None else "nessun collegamento"
        r.append(f"  {l['nome']} | {l['mancano']} | {l['tp_min'] if l['tp_min'] is not None else '-'} | {l['auto_favorevole_min']:.1f}-{l['auto_stima_min']:.1f} | {rap} | {l['classe_testo']}")
    r += ["", f"INTERSCAMBI ESISTENTI: {conta_i['conviene']} il bus conviene, {conta_i['non_conviene']} non conviene (su {len(inter)})",
          "  luogo | stato | mezzi min | auto min (sensori - stima aperta) | rapporto (stima aperta - sensori) | classe"]
    for l in inter:
        rap = f"{l['rapporto_basso']:.2f}-{l['rapporto_alto']:.2f}" if l["tp_min"] is not None else "nessun collegamento"
        r.append(f"  {l['nome']} | {l['stato']} | {l['tp_min'] if l['tp_min'] is not None else '-'} | {l['auto_favorevole_min']:.1f}-{l['auto_stima_min']:.1f} | {rap} | {l['classe_testo']}")
    r += ["", "MINUTI DI PAREGGIO: minuti per parcheggiare in centro che rendono l'auto lenta quanto il bus (stima aperta - sensori; 0 = il bus e' gia' piu' veloce)",
          f"  mediana dei punti prioritari: {pareggio['punti']['mediana_basso_min']} - {pareggio['punti']['mediana_alto_min']} minuti",
          f"  mediana degli interscambi:    {pareggio['interscambi']['mediana_basso_min']} - {pareggio['interscambi']['mediana_alto_min']} minuti",
          "  luogo | tipo | stato | minuti di pareggio (stima aperta - sensori)"]
    for l in sorted(luoghi, key=lambda l: (l["tipo"], l["pareggio_basso_min"] if l["pareggio_basso_min"] is not None else 999)):
        mp = f"{l['pareggio_basso_min']:g} - {l['pareggio_alto_min']:g}" if l["pareggio_basso_min"] is not None else "nessun collegamento"
        r.append(f"  {l['nome']} | {l['tipo']} | {l.get('stato', '-')} | {mp}")
    r += ["", "SENSIBILITA': MINUTI PER PARCHEGGIARE IN CENTRO (la classe ufficiale e' quella con 5; stima aperta)",
          "  minuti | punti: conviene / non conviene | interscambi: conviene / non conviene"]
    for m in MINUTI_SENSIBILITA:
        sp, si = sens[str(m)]["punti"], sens[str(m)]["interscambi"]
        r.append(f"  {m} | {sp['conviene']} / {sp['non_conviene']} | {si['conviene']} / {si['non_conviene']}")
    r.append("  luogo: classe con 5 | 10 | 15 minuti")
    for l in luoghi:
        r.append(f"  {l['nome']}: " + " | ".join(CLASSI[l['classi_sensibilita'][str(m)]] for m in MINUTI_SENSIBILITA))
    r += ["", par_inter, "", "CONTROLLI"] + [f"  {x}" for x in c.righe]
    r += ["", "LIMITI: tempi coi mezzi da orario programmato, solo GTT (niente treni: i luoghi fuori Torino possono risultare peggiori del vero); "
              "il tempo dell'auto e' una stima (sensori 5T, sonde bus e 20 secondi per semaforo: non un tempo misurato su quel percorso); un solo punto per luogo (centro delle fermate importanti per i punti prioritari); "
              "la destinazione e' sempre Piazza Castello."]
    RAPPORTO.write_text("\n".join(r) + "\n", encoding="utf-8")
    log(f"scritto {OUT_JSON.relative_to(RADICE)} e {RAPPORTO.relative_to(RADICE)} ({time.time() - t0:.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
