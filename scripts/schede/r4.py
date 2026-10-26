"""Risultato 4 (pubblico 2): puntualita' e attese dei mezzi GTT (comprende il vecchio Risultato 9, l'attesa)."""
from schede.comune import circa, forma_base, nome_pulito, il, leggi, link_linea, migliaia, minuti_a_parole, num, ora, pct2, periodo_it, virgola, voce




# ---------------------------------------------------------------- Risultato 4

def fasce_r4():
    """Le fasce orarie (feriale) dal JSON dello script 27: (fascia, passaggi, % ritardo oltre 5 minuti)."""
    fasce = leggi("risultato4_regolarita.json")["fasce_feriale"]
    return [(f, v["passaggi"], v["ritardo"]) for f, v in fasce.items()]




# GTT: passaggi bus e tram in ritardo oltre 10 minuti nel 2025, 2,3% (rapporto di sostenibilita' GTT 2025, p. 128;
# cifra citata nel metodo, docs/en/METHODS.md). Costante: non esce da nessun calcolo del progetto.
GTT_RITARDO10_2025_PCT = 2.3


DEF_R4 = (("a", "a ogni fermata"), ("b", "solo alla prima fermata"), ("c", "solo a metà corsa"), ("d", "escluse le fasce 7-9 e 16-19"))




# copertura verificata su trip_update_gtt (ore 06-24 con almeno 50 minuti letti)
GIORNI_PARZIALI_R4 = ("sabato 10 dalle 15, lunedì 12 dalle 12, martedì 13 con buchi il pomeriggio e la sera, "
                      "domenica 18 fino alle 9:30 (poi guasto del feed GTT)")




def scheda_r4():
    r = leggi("risultato4_regolarita.json")
    c = r["citta"]
    par = r["parametri"]
    nomi = {"0": "Feriale", "1": "Sabato", "2": "Domenica"}
    scenari = []
    for k in ("0", "1", "2"):
        x = c[k]
        scenari.append({
            "nome": f"{nomi[k]} ({r['giorni'][k]} {'giorno' if r['giorni'][k] == 1 else 'giorni'}, "
                    f"{migliaia(x['passaggi'])} passaggi)",
            "numeri": [
                num("Passaggi in ritardo oltre 5 min", x["ritardo"], "%"),
                num("Coppie di bus a grappolo o con un buco (linee frequenti)",
                    round(x["grappolo"] + x["buco"], 1), "%"),
                num("Ritardo mediano", x["mediana"], "min"),
                num("Passaggi in anticipo oltre 1 min", x["anticipo"], "%"),
                *([num("Passaggi in ritardo oltre 10 min", x["ritardo10"], "%")] if "ritardo10" in x else []),
            ],
        })
    scenari[0]["nota"] = ("Molti passaggi risultano in anticipo perché l'orario ufficiale ha margini; "
                          "un ritardo mediano negativo vuol dire 'di solito un po' prima'.")
    s = r["scarti"]
    fer = c["0"]
    # gli arrivi sono del GPS; il feed resta solo come confronto (JSON: confronto_feed, copertura_gps, regole_gps)
    cf = r["confronto_feed"]
    cf_fer = cf["citta"]["0"]
    cop_gps = r["copertura_gps"]["totale"]
    dist_gps = int(r["regole_gps"]["dist_gps_m"])
    linee = [(nome, v["0"]) for nome, v in r["linee"].items() if "0" in v]
    peggio_rit = sorted((x for x in linee if x[1]["passaggi"] >= par.get("min_passaggi_classifica", 2000) and str(x[0]).isdigit()),
                        key=lambda x: -x[1]["ritardo"])[:10]
    peggio_irr = sorted((x for x in linee if (x[1].get("coppie") or 0) >= par["min_coppie"] and str(x[0]).isdigit()),
                        key=lambda x: -(x[1]["grappolo"] + x[1]["buco"]))[:10]
    nomi_fasce = {"punta_mattina": "mattino (7-9)", "giorno": "giorno (9-16)",
                  "punta_sera": "sera (16-19)", "sera": "tarda sera (19-24)", "notte": "notte e primo mattino (fino alle 7, dati parziali)"}
    modi = r.get("modi") or {}
    tram_f, bus_f = (modi.get("tram") or {}).get("0"), (modi.get("bus") or {}).get("0")
    utili = (r.get("linee_utili") or {}).get("0")
    # classifica per ritardo a fine corsa (mediana, minuti); i minuti ogni 10 km restano nella nota
    fine_corsa = sorted(((x["fine_corsa"]["ritardo_mediana"], n, x) for n, x in linee
                         if x.get("fine_corsa") and x["fine_corsa"]["passaggi"] >= par.get("min_fine_corsa", 100)
                         and str(n).isdigit()), key=lambda t: (-t[0], -t[2]["fine_corsa"]["min_per_10km"]))[:10]
    rif10 = par.get("rif_gtt_ritardo10_pct")
    cg = r.get("confronto_gtt")      # B1: 4 definizioni di «oltre 10 minuti» (script 27), mai scritte a mano
    grafici_nuovi, righe_gtt, righe_gtt_en = [], [], []
    if cg:
        dd = cg["definizioni"]
        sett = {k: dd[k]["settimana"]["ritardo10_pct"] for k, _ in DEF_R4}
        basso, alto = min([GTT_RITARDO10_2025_PCT] + list(sett.values())), max(sett.values())
        righe_gtt = [
            "Non è la stessa misura: GTT fa la media dell'anno intero, estate e sere comprese, su tutte le linee, con un metodo che non pubblica; "
            "il GPS misura pochi giorni di ottobre, solo le linee urbane, dalle 5 a mezzanotte.",
            f"{'Il ritardo cresce lungo la corsa: ' if sett['b'] < sett['a'] else ''}alla prima fermata è {pct2(sett['b'])}%, "
            f"a metà corsa {pct2(sett['c'])}%, a ogni fermata {pct2(sett['a'])}%, escluse le fasce 7-9 e 16-19 {pct2(sett['d'])}% (media della settimana).",
            f"Tutte e due le misure dicono che i ritardi gravi sono una piccola parte dei passaggi: tra {virgola(basso)}% e {virgola(alto)}%.",
        ]
        righe_gtt_en = [
            f"Why our number differs from GTT's {GTT_RITARDO10_2025_PCT}% (more than 10 minutes late, 2025): GTT averages the whole year on all lines with "
            f"an unpublished method; we measure a few October days on urban lines. At the first stop of the trip we get {sett['b']:.2f}%, "
            f"at every stop {sett['a']:.2f}% (weekly average)."]
    if tram_f and bus_f:
        grafici_nuovi.append({
            "tipo": "barre", "titolo": "Tram contro bus (feriale)", "unita": "%",
            "nota": f"Tram: {migliaia(tram_f['passaggi'])} passaggi; bus: {migliaia(bus_f['passaggi'])}.",
            "voci": [voce("tram: in ritardo oltre 5 min", tram_f["ritardo"], tono="rosso"),
                     voce("bus: in ritardo oltre 5 min", bus_f["ritardo"], tono="rosso"),
                     voce("tram: in ritardo oltre 10 min", tram_f["ritardo10"], tono="rosso"),
                     voce("bus: in ritardo oltre 10 min", bus_f["ritardo10"], tono="rosso"),
                     voce("tram: a grappolo o con un buco", round(tram_f["grappolo"] + tram_f["buco"], 1)),
                     voce("bus: a grappolo o con un buco", round(bus_f["grappolo"] + bus_f["buco"], 1))]})
    if fine_corsa:
        grafici_nuovi.append({
            "tipo": "barre", "titolo": "Ritardo a fine corsa (feriale)", "unita": "min",
            "nota": f"Ritardo mediano alle ultime {par.get('fine_corsa_ultime_fermate', 3)} fermate della corsa, in minuti. "
                    f"Solo linee ordinarie con almeno {par.get('min_fine_corsa', 100)} passaggi di fine corsa. "
                    "I minuti ogni 10 km (ritardo diviso la lunghezza della corsa) sono nel rapporto: per km le linee corte vengono premiate. "
                    "Clicca una linea per vederla nella mappa: la mappa si apre alle 8 di un feriale.",
            "voci": [voce(f"linea {n} ({virgola(x['fine_corsa']['min_per_10km'])} min ogni 10 km)", val, tono="rosso", link=link_linea(n))
                     for val, n, x in fine_corsa]})
    if utili:
        grafici_nuovi.append({
            "tipo": "barre", "titolo": "Linee utili contro altre (feriale)", "unita": "%",
            "nota": f"Linee utili = le {r.get('n_linee_utili')} che toccano più delle zone dove arriva più gente per km² "
                    f"(Risultato 3). Passaggi: {migliaia(utili['utili']['passaggi'])} sulle utili, {migliaia(utili['altre']['passaggi'])} sulle altre.",
            "voci": [voce("linee utili: in ritardo oltre 5 min", utili["utili"]["ritardo"], tono="rosso"),
                     voce("altre linee: in ritardo oltre 5 min", utili["altre"]["ritardo"], tono="rosso"),
                     voce("linee utili: a grappolo o con un buco", utili["utili"]["grappolo_buco"]),
                     voce("altre linee: a grappolo o con un buco", utili["altre"]["grappolo_buco"])]})
    scheda = {
        "risultato": "4",
        "titolo": "Bus in ritardo e bus irregolari",
        "tag": "MISURATO",
        "stato": "Fatto",
        "in_breve": "L'orario alla fermata promette un passaggio ogni tot minuti. Quanto spesso i mezzi GTT "
                    "arrivano davvero in ritardo, o a coppie lasciando un buco?",
        "domanda": "Quanto spesso i mezzi GTT arrivano in ritardo, e quanto spesso sulle linee frequenti "
                   "arrivano a grappolo o lasciano buchi?",
        "numero_chiave": {"valore": fer["ritardo"], "unita": "%",
                          "testo": "dei passaggi nei giorni feriali arriva con più di 5 minuti di ritardo"},
        "racconto": "Una delle direzioni del progetto: confrontare l'orario promesso con quello reale, usando "
                    "le posizioni e i ritardi dei mezzi che il progetto raccoglie ogni minuto.",
        "risposta": [
            f"Nei giorni feriali {il(fer['ritardo'])}% dei passaggi arriva con più di 5 minuti di "
            f"ritardo; il sabato {il(c['1']['ritardo'])}%.",
            f"Sulle linee frequenti {il(fer['grappolo'] + fer['buco'])}% delle coppie di mezzi "
            "consecutivi arriva a grappolo o lascia un buco.",
            f"Il problema più comune è l'anticipo: {il(fer['anticipo'])}% dei passaggi feriali arriva "
            "più di un minuto prima dell'orario.",
            f"Il feed in tempo reale di GTT, usato in precedenza, dava il {virgola(cf_fer['ritardo'])}% in ritardo invece del "
            f"{virgola(fer['ritardo'])}%: smette di aggiornare la fermata all'orario previsto e così sottostima i ritardi.",
            *([f"Oltre 10 minuti: {pct2(fer['ritardo10'])}% nei feriali. GTT dichiara il {virgola(rif10)}% per il 2025: "
               "il suo metodo non è pubblicato; qui si misura a ogni fermata con il GPS, su pochi giorni."]
              if "ritardo10" in fer and rif10 is not None else []),
            *righe_gtt,
            *([f"Tram e bus: in ritardo oltre 5 minuti {il(tram_f['ritardo'])}% dei passaggi dei tram e {il(bus_f['ritardo'])}% "
               f"dei bus (feriale)."] if tram_f and bus_f else []),
            *([f"Linee utili (quelle che toccano più zone affollate): in ritardo oltre 5 minuti {il(utili['utili']['ritardo'])}% dei passaggi, "
               f"contro {il(utili['altre']['ritardo'])}% delle altre linee (feriale)."] if utili else []),
        ],
        "grafici": [
            {"tipo": "pila", "titolo": "Come arrivano i mezzi nei giorni feriali", "unita": "%",
             "voci": [voce("in anticipo (oltre 1 min)", fer["anticipo"]),
                      voce("puntuali (da -1 a +5 min)", fer["puntuale"], tono="verde"),
                      voce("in ritardo (oltre 5 min)", fer["ritardo"], tono="rosso")]},
            {"tipo": "barre", "titolo": "Passaggi in ritardo oltre 5 minuti, per fascia oraria (feriale)",
             "unita": "%", "voci": [voce(nomi_fasce.get(f, f), v, tono="rosso") for f, _, v in fasce_r4()]},
            {"tipo": "barre", "titolo": "Passaggi in ritardo oltre 5 minuti, per tipo di giorno",
             "unita": "%", "voci": [voce(nomi[k].lower(), c[k]["ritardo"], tono="rosso") for k in ("0", "1", "2")]},
            {"tipo": "barre", "titolo": "Le 10 linee più in ritardo (feriale)", "unita": "%",
             "nota": f"Solo linee ordinarie (nome di sole cifre) con almeno {par.get('min_passaggi_classifica', 2000)} passaggi osservati. "
                     "Clicca una linea per vederla nella mappa.",
             "voci": [voce(f"linea {n}", x["ritardo"], tono="rosso", link=link_linea(n)) for n, x in peggio_rit]},
            {"tipo": "barre", "titolo": "Le 10 linee più irregolari (feriale): grappolo + buco", "unita": "%",
             "nota": f"Solo linee frequenti (un mezzo ogni {int(par['freq_max_min'])} minuti o meno) con almeno "
                     f"{par['min_coppie']} coppie osservate. Clicca una linea per vederla nella mappa.",
             "voci": [voce(f"linea {n}", round(x["grappolo"] + x["buco"], 1), link=link_linea(n)) for n, x in peggio_irr]},
            *grafici_nuovi,
        ],
        "metodo": [
            "Il progetto registra ogni minuto le posizioni GPS dei mezzi GTT.",
            f"Per ogni corsa e fermata si prende l'istante in cui il GPS del mezzo passa a meno di {dist_gps} metri dalla "
            "fermata e lo si confronta con l'orario ufficiale (GTFS).",
            "Classi: in anticipo sotto -1 minuto, puntuale da -1 a +5, in ritardo oltre +5.",
            "Regolarità: per due mezzi consecutivi della stessa linea alla stessa fermata, \"grappolo\" se "
            "l'intervallo vero è meno della metà di quello previsto, \"buco\" se è più del doppio. Solo linee "
            "con un mezzo ogni 15 minuti o meno.",
        ],
        "parametri": [["Periodo", f"{r['periodo']['da']} - {r['periodo']['a']}"],
                      ["Passaggi con GPS valido", f"{migliaia(s['usati'])} ({virgola(cop_gps['copertura_pct'])}% di quelli programmati dalle corse viste)"],
                      ["Soglia ritardo", f"{virgola(par['soglia_ritardo_min'])} min"],
                      ["Soglia anticipo", f"{virgola(par['soglia_anticipo_min'])} min"],
                      ["Distanza dalla fermata", f"entro {dist_gps} m"]],
        "limiti": [
            f"Pochi giorni ({r['giorni']['0']} feriali, {r['giorni']['1']} sabati, {r['giorni']['2']} domeniche), "
            f"e non tutti interi: {GIORNI_PARZIALI_R4}. Ogni giorno conta con le ore che hanno dati.",
            "La raccolta si ferma a mezzanotte e riparte verso le 5: la notte non è misurata.",
            "Il GPS copre solo le linee urbane (circa 90): le extraurbane non ci sono mai. Anche sulle linee "
            "coperte alcune corse non sono mai viste dal GPS: se erano saltate davvero, la puntualità reale è peggiore "
            "e i buchi sono più di quelli contati.",
            f"Il GPS c'è per circa {il(round(cop_gps['copertura_pct']))}% dei passaggi delle corse viste; "
            "le corse mai viste dal GPS non si contano.",
            f"Distanza di {dist_gps} metri dalla fermata: un mezzo fermo poco prima conta come arrivato poco dopo.",
            "Dice quanto spesso c'è ritardo, non quante persone aspettano né quanto erano pieni i mezzi.",
        ],
        "in_english": [
            "Question: how often do GTT vehicles arrive late, and how often do frequent lines bunch together or leave "
            "gaps?",
            f"On weekdays {fer['ritardo']:.1f}% of departures arrive more than 5 minutes late; on Saturdays "
            f"{c['1']['ritardo']:.1f}%. On frequent lines {fer['grappolo'] + fer['buco']:.1f}% of consecutive pairs of "
            "vehicles bunch together or leave a gap.",
            f"The most common problem is early arrival: {fer['anticipo']:.1f}% of weekday departures arrive more than one "
            "minute before the timetable.",
            f"Limits: only {r['giorni']['0']} weekdays, {r['giorni']['1']} Saturdays and {r['giorni']['2']} Sundays of data, "
            "some of them partial; the night is not measured.",
            f"Arrivals are now measured with the vehicles' GPS; the GTT real-time feed we used before gave {cf_fer['ritardo']:.1f}% "
            f"late instead of {fer['ritardo']:.1f}% because it stops updating a stop at its scheduled time, so it underestimates delays.",
            *([f"More than 10 minutes late: {fer['ritardo10']:.2f}% of weekday departures. GTT reports {rif10}% for 2025: "
               "its method is not published; we measure at every stop with GPS, over a few days."]
              if "ritardo10" in fer and rif10 is not None else []),
            *righe_gtt_en,
            *([f"Trams vs buses (weekdays): {tram_f['ritardo']:.1f}% of tram departures and {bus_f['ritardo']:.1f}% of bus departures "
               "are more than 5 minutes late."] if tram_f and bus_f else []),
            *([f"Delay at the end of the trip (median, last stops): highest on line {fine_corsa[0][1]} ({fine_corsa[0][0]:.1f} minutes)."]
              if fine_corsa else []),
            *([f"Useful lines (touching the busiest zones per km2): {utili['utili']['ritardo']:.1f}% of departures more than 5 minutes late, "
               f"other lines {utili['altre']['ritardo']:.1f}% (weekdays)."] if utili else []),
        ],
        "mappa": {"id": "puntualita", "tema": "Puntualità delle linee",
                  "nota": "Nella mappa, tema «Puntualità delle linee»: ogni linea colorata per ritardo nell'ora scelta con il cursore."},
        "fonti": ["docs/en/METHODS.md", "scripts/27_risultato4_regolarita.py"],
        "generato": ora(),
        "avviso": [
            "Pochi giorni di dati",
            f"Arrivi misurati con il GPS dei mezzi GTT raccolto dal progetto, {r['periodo']['da']} - {r['periodo']['a']}: "
            f"il GPS c'è per il {round(cop_gps['copertura_pct'])}% dei passaggi programmati delle corse viste (prima si usava il feed GTT, "
            "che sottostima i ritardi: confronto nella scheda). Giorni non tutti interi e solo linee urbane viste dal GPS: vedi i limiti."
        ],
        "scenari": scenari,
    }
    r9 = scheda_r9()
    scheda["titolo"] = "Puntualità e attese"
    scheda["domanda"] = scheda["domanda"] + " E quanto si aspetta davvero alla fermata, rispetto a quello che promette l'orario?"
    scheda["risposta"] = scheda["risposta"] + ["Attesa: " + r9["risposta"][0]] + r9["risposta"][1:]
    for chiave in ("grafici", "scenari", "limiti"):
        scheda[chiave] = scheda.get(chiave, []) + r9.get(chiave, [])
    scheda["in_english"] = scheda.get("in_english", []) + r9.get("in_english", [])[1:]
    modi9 = (leggi("risultato9_attesa.json").get("modi") or {}).get("0") or {}
    if modi9.get("tram") and modi9.get("bus"):
        t9, b9 = modi9["tram"], modi9["bus"]
        scheda["risposta"] = scheda["risposta"] + [
            f"Attesa alla fermata sulle linee frequenti (feriale): tram, promessa {virgola(t9['promessa_min'])} min, in più "
            f"{virgola(t9['in_piu_min_bassa'])}-{virgola(t9['in_piu_min_alta'])} min; bus, promessa {virgola(b9['promessa_min'])} min, "
            f"in più {virgola(b9['in_piu_min_bassa'])}-{virgola(b9['in_piu_min_alta'])} min."]
        scheda["in_english"] = scheda["in_english"] + [
            f"Waiting time on frequent lines (weekdays): trams promise {t9['promessa_min']:.1f} min, {t9['in_piu_min_bassa']:.1f}-"
            f"{t9['in_piu_min_alta']:.1f} min more in reality; buses {b9['promessa_min']:.1f} min, {b9['in_piu_min_bassa']:.1f}-"
            f"{b9['in_piu_min_alta']:.1f} min more."]
    scheda["fonti"] = ["docs/en/METHODS.md"] + [f for f in scheda.get("fonti", []) + r9.get("fonti", []) if f != "docs/en/METHODS.md"]
    return scheda




# ---------------------------------------------------------------- Risultato 9

MIN_INTERVALLI_R9 = 2000   # sotto questa soglia un tipo di giorno non entra nella scheda (la domenica ne ha ~600)




def scheda_r9():
    r = leggi("risultato9_attesa.json")
    par = r["parametri"]
    nomi_tipo = {"0": "Feriale", "1": "Sabato", "2": "Domenica"}
    nomi_fasce = {"punta_mattina": "mattino (7-9)", "giorno": "giorno (9-16)",
                  "punta_sera": "sera (16-19)", "sera": "tarda sera (19-24)",
                  "notte": "primo mattino (fino alle 7)"}
    fer = r["citta"]["0"]
    gps = r["controllo_gps"] or {}
    linee = sorted(((v["in_piu_min_bassa"], k, v) for k, v in r["linee"].get("0", {}).items()
                    if v["intervalli_osservati"] >= par["min_intervalli_classifica"]), reverse=True)[:10]
    scenari = []
    for t in ("0", "1", "2"):
        c = r["citta"].get(t)
        if not c or c["intervalli_osservati"] < MIN_INTERVALLI_R9:  # domenica: poche linee frequenti
            continue
        scenari.append({"nome": f"{nomi_tipo[t]} ({r['giorni'][t]} {'giorno' if r['giorni'][t] == 1 else 'giorni'})",
                        "numeri": [num("Attesa media alla fermata, stima bassa", c["reale_min_bassa"], "min",
                                       prima=c["promessa_min"]),
                                   num("Attesa media alla fermata, stima alta", c["reale_min_alta"], "min",
                                       prima=c["promessa_min"]),
                                   num("Corse programmate assenti dal GPS", c["corse_assenti_feed_pct"], "%")]})
    scenari[0]["nota"] = "Prima = attesa promessa dall'orario, dopo = attesa reale stimata dai passaggi."
    sens = r["sensibilita_freq"]
    return {
        "risultato": "9",
        "titolo": "Quanto si aspetta davvero alla fermata",
        "tag": "MISURATO",
        "stato": "Fatto",
        "in_breve": "L'orario promette un bus ogni pochi minuti. Se però i bus arrivano a coppie e poi lasciano un "
                    "buco, alla fermata si aspetta di più, anche se in un'ora ne passano tanti quanti promessi.",
        "domanda": "Sulle linee frequenti, quanti minuti in più aspetta in media chi arriva alla fermata senza "
                   "guardare l'orario, rispetto a quanto promette l'orario?",
        "numero_chiave": {"valore": fer["in_piu_min_bassa"], "unita": "min",
                          "testo": f"in più di attesa alla fermata nei giorni feriali (fino a "
                                   f"{virgola(fer['in_piu_min_alta'])}), su {virgola(fer['promessa_min'])} promessi"},
        "racconto": "Il risultato 4 contava quante coppie di bus arrivano a grappolo o lasciano un buco. Questo "
                    "risultato traduce quei numeri in minuti persi alla fermata, con la misura che usano le grandi "
                    "aziende di trasporto (Londra la pubblica come \"attesa in eccesso\").",
        "risposta": [
            f"Nei giorni feriali, sulle linee frequenti, l'orario promette un'attesa media di "
            f"{virgola(fer['promessa_min'])} minuti; quella reale è tra {virgola(fer['reale_min_bassa'])} e "
            f"{virgola(fer['reale_min_alta'])} minuti.",
            f"Sono da {virgola(fer['in_piu_min_bassa'])} a {virgola(fer['in_piu_min_alta'])} minuti in più a ogni "
            f"attesa: almeno {il(round(fer['in_piu_pct_bassa']))}% oltre la promessa.",
            f"La linea con più attesa in più è la {linee[0][1]} ({virgola(linee[0][0])} minuti in più, stima bassa)."
            if linee else "",
        ],
        "grafici": [
            {"tipo": "barre", "titolo": "Attesa media alla fermata per fascia oraria (feriale)", "unita": "min",
             "nota": "Barra chiara = attesa promessa, barra scura = attesa reale (stima bassa).",
             "voci": [voce(nomi_fasce[f], r["citta_fascia"]["0"][f]["reale_min_bassa"],
                           prima=r["citta_fascia"]["0"][f]["promessa_min"])
                      for f in ("punta_mattina", "giorno", "punta_sera", "sera") if r["citta_fascia"]["0"].get(f)]},
            {"tipo": "barre", "titolo": "Minuti in più di attesa, per fascia oraria (feriale)", "unita": "min",
             "forbice": True,
             "nota": "Barra chiara = stima bassa, barra scura = stima alta.",
             "voci": [voce(nomi_fasce[f], r["citta_fascia"]["0"][f]["in_piu_min_alta"],
                           prima=r["citta_fascia"]["0"][f]["in_piu_min_bassa"])
                      for f in ("punta_mattina", "giorno", "punta_sera", "sera") if r["citta_fascia"]["0"].get(f)]},
            {"tipo": "barre", "titolo": "Le 10 linee con più attesa in più (feriale, stima bassa)", "unita": "min",
             "nota": f"Solo linee con almeno {par['min_intervalli_classifica']} intervalli osservati.",
             "voci": [voce(f"linea {k}", round(v, 1)) for v, k, _ in linee]},
        ],
        "metodo": [
            "Per chi arriva alla fermata a caso, l'attesa media dipende da quanto sono regolari i passaggi: con gli "
            "intervalli h1, h2, ... è (h1² + h2² + ...) / (2 × (h1 + h2 + ...)). Bus ogni 10 minuti esatti: 5 minuti. "
            "Stessi due bus all'ora ma con intervalli di 2 e 18 minuti: 8,2 minuti.",
            "Attesa promessa = la formula sugli orari ufficiali (GTFS). Attesa reale = la formula sugli arrivi misurati "
            "con il GPS dei mezzi (stessa misura del risultato 4).",
            f"Solo linee frequenti: intervallo programmato medio di {int(par['freq_max_min'])} minuti o meno, per "
            "fermata, linea, verso e fascia oraria. Solo nelle ore in cui il progetto stava raccogliendo.",
            "Corse che non compaiono nel GPS: non si sa se sono saltate o solo non trasmesse, quindi due stime. "
            "Bassa: si usano solo i tratti senza corse mancanti. Alta: una corsa assente dal GPS "
            "conta come saltata.",
            "Media della città pesata sul numero di intervalli programmati (non ci sono dati sui passeggeri).",
        ],
        "parametri": [["Periodo", f"{r['periodo']['da']} - {r['periodo']['a']}"],
                      ["Linea frequente", f"intervallo medio ≤ {int(par['freq_max_min'])} min"],
                      ["Intervalli osservati (feriale)", migliaia(fer["intervalli_osservati"])],
                      ["Esclusi per dati scarsi", f"linea-fascia con più del {int(par['max_mancanti'] * 100)}% di corse assenti"],
                      ["Controllo del feed col GPS", f"{gps.get('passaggi_confrontati', '-')} passaggi delle linee "
                                            f"{', '.join(gps.get('linee', []))}: differenza tipica "
                                            f"{virgola(gps.get('differenza_assoluta_mediana_min') or 0)} min"],
                      ["Soglia 10 / 15 min", f"in più {virgola(sens['10']['in_piu_min_bassa'])} / "
                                             f"{virgola(sens['15']['in_piu_min_bassa'])} min (stima bassa)"]],
        "limiti": [
            "Arrivi misurati con il GPS dei mezzi (a meno di 60 metri dalla fermata); il vecchio feed GTT, controllato col GPS, "
            f"dava una differenza tipica di {virgola(gps.get('differenza_assoluta_mediana_min') or 0)} minuti.",
            "Solo le linee urbane viste dal GPS; niente extraurbane e niente notte.",
            "Le corse mancanti rendono il risultato una forbice, non un numero solo.",
            "Vale per chi arriva alla fermata senza guardare orario o app: è il caso tipico delle linee frequenti, "
            "non di quelle rare (per quelle conta la puntualità, risultato 4).",
            "Pochi giorni (gli stessi del risultato 4, non tutti interi): va rifatto con più settimane di dati. "
            "La domenica le linee frequenti sono poche: troppo pochi dati per dare un numero.",
        ],
        "in_english": [
            "Question: on frequent lines, how many more minutes does a passenger who arrives at the stop without checking "
            "the timetable wait on average, compared with what the timetable promises?",
            f"On weekdays the timetable promises an average wait of {fer['promessa_min']:.1f} minutes; the real one is "
            f"between {fer['reale_min_bassa']:.1f} and {fer['reale_min_alta']:.1f} minutes. That is "
            f"{fer['in_piu_min_bassa']:.1f} to {fer['in_piu_min_alta']:.1f} minutes more per wait, at least "
            f"{round(fer['in_piu_pct_bassa']):,}% above the promise.",
            f"Limits: only {r['giorni']['0']} weekdays of data so far; real arrivals are measured with the vehicles' GPS "
            "(within 60 metres of the stop); the night is not included.",
        ],
        "mappa": None,
        "fonti": ["docs/en/METHODS.md", "scripts/70_risultato9_attesa.py"],
        "generato": ora(),
        "avviso": [
            "Forbice per le corse mancanti",
            "Arrivi misurati con il GPS dei mezzi raccolto dal progetto, solo linee urbane frequenti e ore con raccolta "
            "attiva. Stima bassa = solo tratti senza corse mancanti; stima alta = corse assenti dal GPS "
            "contate come saltate."
        ],
        "scenari": scenari,
    }




def velocita_bus():
    """Velocità dei bus dal GPS (script 104, E4): (km/h alle 8, grafico a linea ora per ora, riga del calcolo) oppure None se il file manca."""
    try:
        v = leggi("velocita_bus.json")
    except FileNotFoundError:
        return None
    bus = v["velocita"]["bus"]
    ore = [int(o) for o in bus]
    linea = {"tipo": "linea", "titolo": "Velocità media dei bus, ora per ora (feriale)", "unita": "km/h",
             "nota": "Distanza percorsa divisa per il tempo, fermate e semafori compresi.",
             "categorie": [str(o) for o in ore], "serie": [{"label": "velocità dei bus", "valori": [round(bus[str(o)]["kmh"]) for o in ore]}]}
    calcolo = ("Velocità dei bus: distanza fra posizioni GPS consecutive divisa per il tempo, fermate e semafori compresi. "
               "Media dei giorni feriali, pesata sui rilevamenti.")
    return bus["8"]["kmh"], linea, calcolo


def forma_r4(s):
    r = leggi("risultato4_regolarita.json")
    c, par = r["citta"], r["parametri"]
    fer = c["0"]
    dd = r["confronto_gtt"]["definizioni"]
    a_fer, b_fer = dd["a"]["per_tipo"]["0"]["ritardo10_pct"], dd["b"]["per_tipo"]["0"]["ritardo10_pct"]
    a_set, b_set = dd["a"]["settimana"]["ritardo10_pct"], dd["b"]["settimana"]["ritardo10_pct"]
    nomi = {"0": "feriale", "1": "sabato", "2": "domenica"}
    pila = {"tipo": "pila100", "titolo": "Come arrivano i mezzi", "unita": "%",
            "nota": "Ogni barra è un tipo di giorno: 100% dei passaggi.",
            "righe": [{"label": nomi[k], "voci": [
                voce("in anticipo (oltre 1 minuto)", c[k]["anticipo"], tono="blu"),
                voce("puntuali", c[k]["puntuale"], tono="verde"),
                voce("ritardo da 5 a 10 minuti", round(c[k]["ritardo"] - c[k]["ritardo10"], 2), tono="giallo"),
                voce("ritardo oltre 10 minuti", c[k]["ritardo10"], tono="rosso")]} for k in ("0", "1", "2")]}
    fasce = [(f, v) for f, _, v in fasce_r4() if f != "notte"]
    nomi_f = {"punta_mattina": "mattino (7-9)", "giorno": "giorno (9-16)", "punta_sera": "sera (16-19)", "sera": "tarda sera (19-24)"}
    nomi_anima = {"punta_mattina": "su 100 al mattino (7-9)", "giorno": "su 100 di giorno (9-16)",
                  "punta_sera": "su 100 alla sera (16-19)", "sera": "su 100 a tarda sera (19-24)"}
    linea = {"tipo": "linea", "titolo": "Ritardo oltre 5 minuti, per fascia oraria (feriale)", "unita": "%",
             "categorie": [nomi_f[f] for f, _ in fasce], "serie": [{"label": "passaggi in ritardo", "valori": [round(v) for _, v in fasce]}]}
    linee = [(n, v["0"]) for n, v in r["linee"].items() if "0" in v]
    peggio = max((x for x in linee if x[1]["passaggi"] >= par.get("min_passaggi_classifica", 2000) and str(x[0]).isdigit()),
                 key=lambda x: x[1]["ritardo"])
    dist = int(r["regole_gps"]["dist_gps_m"])
    gg = r["giorni"]
    a9 = leggi("risultato9_attesa.json")
    fer9, per_fascia = a9["citta"]["0"], a9["citta_fascia"]["0"]
    in_piu = (fer9["in_piu_min_bassa"] + fer9["in_piu_min_alta"]) / 2
    ordine_f = [f for f in ("punta_mattina", "giorno", "punta_sera", "sera") if per_fascia.get(f)]
    extra = {"titolo": "Quanto si aspetta alla fermata",
             "punto": f"Sulle linee frequenti si aspetta {minuti_a_parole(in_piu)} in più di quanto promette l'orario.",
             "grafico": {"tipo": "barre", "titolo": "Quanto si aspetta in più di quanto dice l'orario", "unita": "min",
                         "nota": "Ogni barra è una fascia del giorno feriale: i minuti di attesa in più rispetto all'orario. Fra parentesi l'attesa reale contro quella promessa.",
                         "voci": [{"label": nomi_f[f], "valore": round(per_fascia[f]["in_piu_min_bassa"], 1), "tono": "rosso",
                                   "testo": f"+{virgola(round(per_fascia[f]['in_piu_min_bassa'], 1))} min ({circa(per_fascia[f]['reale_min_bassa'])} invece di {circa(per_fascia[f]['promessa_min'])})"}
                                  for f in ordine_f]}}
    vb = velocita_bus()
    # forbice dovuta alla lettura al minuto (§6.3): il numero grande e' quello a 0 secondi, la forbice [0 s, +60 s] sta nel calcolo; il punto sull'anticipo solo se passa la regola
    fb = r["forbice_lettura"]
    if not fb.get("scritta"):
        raise SystemExit("Risultato 4: manca forbice_lettura in risultato4_regolarita.json: lancia scripts/27 con --sposta-secondi 30 e 60 e poi senza opzioni")
    rf, af = fb["ritardo_forbice"], fb["anticipo_forbice"]["feriale_pct"]
    tr = leggi("dove_nascono_ritardi.json")
    classifica = tr["classifica"]["punta_mattina"][:10]
    primo = classifica[0]
    graf_tratti = {"tipo": "barre", "titolo": "Dove i bus perdono tempo: i 10 tratti peggiori (7-9)", "unita": "minuti",
                   "nota": "Minuti persi ogni giorno feriale sul tratto fra due fermate, con almeno 50 corse osservate. Ogni barra porta alla mappa.",
                   "voci": [voce(f"{nome_pulito(t['da'])} → {nome_pulito(t['a'])} (linea {', '.join(t['linee'])})", round(t["min_persi_giorno"]), tono="rosso",
                                 link="mappa_torino.html#tema=tratti") for t in classifica]}
    n5 = round(100 / fer["ritardo"])
    return forma_base(
        s,
        f"Circa 1 passaggio su {round(100 / fer['ritardo10'])} arriva con più di 10 minuti di ritardo",
        "Quanto spesso i mezzi GTT arrivano in ritardo?",
        {"valore": a_fer, "unita": "%", "testo": "dei passaggi feriali arriva con oltre 10 minuti di ritardo", "breve": "dei passaggi in ritardo di oltre 10 minuti"},
        pila,
        [f"1 passaggio su {n5} supera i 5 minuti di ritardo; la linea peggiore è la {peggio[0]} ({circa(peggio[1]['ritardo'], '%')}).",
         f"I bus perdono più tempo tra {nome_pulito(primo['da'])} e {nome_pulito(primo['a'])}: {circa(primo['min_persi_giorno'], ' minuti')} ogni giorno feriale.",
         extra["punto"]],
        [graf_tratti, linea] + ([vb[1]] if vb else []),
        ["Il progetto registra ogni minuto la posizione GPS dei mezzi GTT.",
         f"Il passaggio è l'ultimo istante con il GPS a meno di {dist} metri dalla fermata. L'orario ufficiale è di partenza.",
         "Il ritardo è quell'istante meno l'orario ufficiale.",
         f"In anticipo oltre {virgola(abs(par['soglia_anticipo_min']))} minuto; in ritardo oltre {virgola(par['soglia_ritardo_min'])} minuti.",
         f"Una lettura al minuto: il ritardo vero è fino a un minuto più grande. Oltre 5 minuti {virgola(rf['feriale_oltre5_pct'][0])}-{virgola(rf['feriale_oltre5_pct'][1])}%, "
         f"oltre 10 minuti {virgola(rf['feriale_oltre10_pct'][0])}-{virgola(rf['feriale_oltre10_pct'][1])}%, in anticipo {virgola(af[0])}-{virgola(af[1])}% dei passaggi feriali.",
         "Tratto: due fermate consecutive di una corsa. Minuti persi: somma dei tempi in più sul tratto, diviso i giorni feriali. Solo tratti con almeno 50 corse osservate."]
        + ([vb[2]] if vb else []),
        [list(p) for p in s["parametri"] if p[0] != "Periodo"] + [["Periodo dei dati", periodo_it(r["periodo"]["da"], r["periodo"]["a"])]],   # L24 (T8): una riga sola per il periodo
        [f"Pochi giorni: {gg['0']} feriali, {gg['1']} sabati e {gg['2']} {'domenica' if gg['2'] == 1 else 'domeniche'}, non tutti interi.",
         "Solo le linee urbane viste dal GPS, dalle 5 a mezzanotte.",
         f"Il GPS copre circa {il(round(r['copertura_gps']['totale']['copertura_pct']))}% dei passaggi programmati; le corse mai viste non si contano.",
         "Si conta quanto spesso c'è ritardo, non quante persone aspettano."],
        None,
        anima={"tipo": "quadratini", "totale": 100, "oltre5": fer["ritardo"], "oltre10": fer["ritardo10"],
               "testo_tutto": "su 100 passaggi in un feriale arrivano con oltre 5 minuti di ritardo",
               "fasi": [{"label": nomi_anima[f], "valore": v} for f, v in fasce],
               "legenda5": "oltre 5 minuti", "legenda10": "oltre 10 minuti",
               "didascalia": f"Su 100 passaggi feriali, circa {round(fer['ritardo'])} arrivano con più di 5 minuti di ritardo ({virgola(fer['ritardo'])}%); "
                             f"con più di 10 minuti circa {round(fer['ritardo10'])}. Poi il giorno, fascia per fascia."},
        confronto=[f"GTT dichiara il {virgola(GTT_RITARDO10_2025_PCT)}% oltre 10 minuti nel 2025: media dell'anno, tutte le linee, metodo non pubblicato.",
                   f"Il GPS misura pochi giorni di ottobre sulle linee urbane: {virgola(a_set)}% a ogni fermata, {virgola(b_set)}% alla partenza.",
                   f"Anche contando come GTT alla partenza si trova il {virgola(b_set)}%; il resto della differenza è stagione e metodo.",
                   f"Solo feriali: {pct2(a_fer)}% a ogni fermata, {pct2(b_fer)}% alla prima, {pct2(dd['c']['per_tipo']['0']['ritardo10_pct'])}% a metà corsa, "
                   f"{pct2(dd['d']['per_tipo']['0']['ritardo10_pct'])}% senza le fasce 7-9 e 16-19."],
        extra=extra)
