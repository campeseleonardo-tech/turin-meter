"""Risultato 8 (pubblico 4): traffico e mezzi pubblici."""
import json
import re
import statistics
from schede import comune
from schede.comune import circa, forma_base, leggi, migliaia, nome_pulito, num, ora, periodo_it, virgola, voce




# ---------------------------------------------------------------- Risultato 8

def nome_strada(n):
    """'unita d italia' -> 'Unità d'Italia' (i nomi del modello sono senza maiuscole e accenti)."""
    if n.startswith("di "):
        n = "strada " + n   # es. "di settimo" -> Strada di Settimo
    t = " ".join(w.capitalize() for w in n.split())
    t = re.sub(r" D (?=[A-Z])", " d'", t)
    for a, b in (("Unita ", "Unità "), (" Di ", " di "), (" Del ", " del ")):
        t = t.replace(a, b)
    return t




def testo_scelta_del_mezzo():
    """Limite sulla prova della scelta del mezzo (script 102, regola fissata prima, L13): se nella fascia 6-10 troppe poche coppie hanno abbastanza interviste, lo dice; se la relazione e' valutabile, per ora non si scrive."""
    try:
        sc = leggi("scelta_del_mezzo.json")
    except FileNotFoundError:
        return None
    if sc["regole"].get("prova"):
        return None
    coppie = sum(g["coppie"] for g in sc["gruppi"].values())
    if any(g.get("spearman") is not None for g in sc["gruppi"].values()):
        return None
    return (f"Prova sulla scelta del mezzo senza esito. Dalle 6 alle 10 di un feriale le coppie di zone con almeno "
            f"{sc['regole']['soglia_interviste']} interviste sono {coppie}.")


def scheda_r8():
    r = leggi("risultato8_traffico_tp_v2.json")
    v = leggi("traffico_d/valutazione_fase5.json")
    var = r.get("variante_traffico", "v0")   # il modello scelto dalla regola fissata prima (script 63)
    sens = leggi(f"traffico_d/{var}/sensori.json")["sensori"]
    u, c, tar = r["universo_torino"], r["conteggi"], r["taratura"]
    km_poco = round(u["km"] - u["km_coperti_tp"], 1)
    err = v["varianti"][var]
    # strade con piu' traffico: per nome solo per mostrarle (il calcolo e' per asse e tratta)
    per_nome = {}
    for t in r["tratte"]:
        if not t["asse_con_sensore"]:   # solo strade con un sensore sull'asse: le altre classifiche sono poco credibili
            continue
        k = t["nome"]
        if k not in per_nome or t["veic_giorno"] > per_nome[k]["veic_giorno"]:
            per_nome[k] = t
    top = sorted(per_nome.values(), key=lambda t: -t["veic_giorno"])[:10]
    # stima leave-one-out per ogni sensore (stesso metodo della valutazione: fattore = somma misurati / somma modello degli altri)
    tot_mis, tot_mod = sum(s["misurato"] for s in sens), sum(s["modello_2v"] for s in sens)
    loo = [(s, s["modello_2v"] * (tot_mis - s["misurato"]) / (tot_mod - s["modello_2v"])) for s in sens]
    loo.sort(key=lambda x: -x[0]["misurato"])
    dg = {a["nome_principale"]: a for a in r["assi_da_guardare"]}
    rm = dg.get("regina margherita", {})
    acc = r["accordo_leo"]
    altri_assi = [a for a in r["assi_da_guardare"] if a["nome_principale"] != "regina margherita"]
    altro_tratto = (f" In più un tratto di {nome_strada(altri_assi[0]['nome_principale'])}, coperto solo per "
                    f"{round(100 * altri_assi[0]['copertura_tp_max'])}% della lunghezza.") if altri_assi else ""
    fascia50, fascia90 = round(tar["fascia_50"] * 100), round(tar["fascia_90"] * 100)
    return {
        "risultato": "8",
        "titolo": "Traffico sulle strade e trasporto pubblico",
        "tag": "STIMATO / MISURATO / PROGRAMMATO",
        "stato": "Fatto",
        "in_breve": "Quante auto passano sulle strade grandi di Torino? E dove c'è tanto traffico ma nessun bus, "
                    "tram o metro comodo, così che l'auto resta l'unica scelta?",
        "domanda": "Sulle strade grandi di Torino, dove c'è molto traffico e poco trasporto pubblico vicino?",
        "numero_chiave": {"valore": round(u["quota_km_coperta_tp"] * 100, 1), "unita": "%",
                          "testo": f"dei km di strade grandi di Torino hanno fermate frequenti a pochi passi "
                                   f"({virgola(u['km_coperti_tp'])} km su {virgola(u['km'])})"},
        "racconto": "Un primo calcolo trovava 23 strade \"con molto traffico e poco trasporto pubblico\". "
                    "Ricontrollando, quasi tutte erano un errore di misura: i bus si cercavano lungo la strada per "
                    "nome invece che per posizione delle fermate (Corso Cairoli risultava senza passaggi). Rifatto il "
                    "calcolo, la lista si è quasi svuotata: è questa la risposta.",
        "risposta": [
            f"Sulle {migliaia(u['n_tratte'])} tratte di strade grandi di Torino ({virgola(u['km'])} km), il "
            f"{virgola(u['quota_km_coperta_tp'] * 100)}% della lunghezza ha una fermata con almeno 4 passaggi "
            "all'ora entro 300 m, o la metro entro 600 m.",
            f"Le tratte con molto traffico (oltre {migliaia(round(u['soglie']['q66']))} veicoli al giorno) sono "
            f"{c['molto_traffico']}; quelle che hanno anche poco trasporto pubblico sono {c['da_guardare']}.",
            f"In pratica è un solo caso: Corso Regina Margherita verso ovest, il tratto a scorrimento veloce "
            f"(circa {migliaia(int(round(rm.get('veic_max', 0), -3)))} veicoli al giorno, nessuna fermata frequente "
            "entro 300 m)." + altro_tratto,
            f"I numeri di traffico sono stime: in metà dei casi l'errore è entro ±{fascia50}%. Servono a ordinare "
            "le strade, non a contare i veicoli.",
        ],
        "grafici": [
            {"tipo": "pila", "titolo": "Km di strade grandi di Torino: con o senza trasporto pubblico vicino",
             "unita": "km",
             "voci": [voce("con fermate frequenti vicine", round(u["km_coperti_tp"], 1), tono="verde"),
                      voce("con poco trasporto pubblico", km_poco, tono="rosso")]},
            {"tipo": "barre", "titolo": "Strade con un sensore: la tratta più carica (veicoli al giorno, 6-21)",
             "unita": "veicoli/giorno",
             "nota": "Solo strade con almeno un sensore sullo stesso asse: senza, il modello mette in cima anche strade "
                     "poco credibili. \"misurato\" = sensore sulla tratta; le altre sono stime. Corso Unione Sovietica è "
                     "probabilmente sovrastimato: dove c'è il sensore il modello dava quasi il triplo del misurato.",
             "voci": [voce(nome_strada(t["nome"]) + (" (misurato)" if t["misurato"] else ""), round(t["veic_giorno"]))
                      for t in top]},
            {"tipo": "barre", "titolo": f"Prova del modello sui {len(sens)} sensori: misurato e stimato",
             "unita": "veicoli/giorno",
             "nota": "Barra chiara = misurato dal sensore, barra scura = stima del modello senza usare quel sensore.",
             "voci": [voce(s["via"].replace("(TO)", "").replace("Unita' D'italia", "Unità d'Italia").strip(), round(st), prima=s["misurato"]) for s, st in loo]},
            {"tipo": "barre", "titolo": "Errore della stima su ogni sensore (%)", "unita": "%",
             "nota": "Errore = |stimato − misurato| / misurato. Metà dei sensori sotto il valore tipico, gli altri sopra.",
             "voci": [voce(s["via"].replace("(TO)", "").replace("Unita' D'italia", "Unità d'Italia").strip(),
                           round(100 * abs(st - s["misurato"]) / s["misurato"]), tono="rosso")
                      for s, st in sorted(loo, key=lambda x: abs(x[1] - x[0]["misurato"]) / x[0]["misurato"])]},
        ],
        "metodo": [
            "Domanda: gli spostamenti in auto dell'indagine sugli spostamenti 2022 (residenti, giorno feriale), assegnati alla "
            "strada più veloce sulla rete di OpenStreetMap.",
            f"Taratura su {err['n']} punti di misura dei sensori 5T: un solo fattore per tutta la città, provato "
            "togliendo un sensore alla volta e stimandolo con gli altri.",
            "Strade come assi: un corso che cambia nome o comune resta la stessa strada, tagliata in tratte da "
            "300 m a 1,5 km. Strade grandi = Torino, importanza alta o strade principali, almeno 300 m, senza "
            "tangenziale e raccordi.",
            "Trasporto pubblico per posizione delle fermate, mai per nome: una tratta è servita dove c'è una "
            "fermata con almeno 4 passaggi all'ora entro 300 m (orario ufficiale, mercoledì 14/10), o la metro "
            "entro 600 m. Poco trasporto pubblico = servita per metà della lunghezza o meno.",
            "Molto traffico = il terzo più alto delle tratte. " + (
                "Un modello più ricco (attrazioni, code, ZTL) è stato provato una volta e non ha migliorato l'ordine delle strade: si tiene quello semplice."
                if var == "v0" else
                f"Il modello è quello più ricco (attrazioni, code, ZTL): con i sensori di ottobre sbaglia meno di quello semplice "
                f"(errore tipico {round(100 * err['errore_mediano'])}% contro {round(100 * v['varianti']['v0']['errore_mediano'])}%), secondo una regola fissata prima."),
        ],
        "parametri": [["Strade grandi di Torino", f"{migliaia(u['n_tratte'])} tratte, {virgola(u['km'])} km"],
                      ["Errore tipico (metà dei casi)", f"±{fascia50}% (9 volte su 10 entro ±{fascia90}%)"],
                      ["Ordine giusto delle strade (Spearman)", f"{err['rho_loo']:.2f}".replace(".", ",")],
                      ["Validato tra", f"{migliaia(int(round(tar['intervallo_validato_measured'][0], -2)))} e "
                                       f"{migliaia(int(round(tar['intervallo_validato_measured'][1], -3)))} veicoli/giorno"],
                      ["Soglia 'molto traffico'", f"{migliaia(round(u['soglie']['q66']))} veicoli/giorno"],
                      ["Confronto con chi conosce la città", f"{acc['n_giuste_18']} strade su 18 nella fascia giusta, "
                                                             f"{acc['n_giusti_7']} confronti su 7 (solo controllo)"]],
        "limiti": [
            f"Stima debole: errore tipico ±{fascia50}% e intervallo d'incertezza largo (da {round(err['ic90'][0] * 100)}% "
            f"a {round(err['ic90'][1] * 100)}%). Alcune strade sono molto sbagliate (Corso Unione Sovietica, Corso "
            "Sebastopoli): buona per ordinare, non per contare.",
            f"Solo {err['n']} punti di misura, quasi tutti su corsi trafficati: sotto circa "
            f"{migliaia(int(round(tar['intervallo_validato_measured'][0], -3)))} veicoli al giorno la stima non è "
            "verificata.",
            "Solo i residenti tra 11 e 84 anni (indagine sugli spostamenti): mancano merci, turisti e chi viene da fuori. Il "
            "modello non sa fare le code: l'ora di punta non è verificata.",
            "Trasporto pubblico programmato: niente ritardi né affollamento. Il centro (ZTL, aree pedonali) non è "
            "stimato bene.",
            "Il valore è per i due versi: sulle poche vie a senso unico vero potrebbe essere il doppio del reale.",
            "Il tratto di Corso Moncalieri va controllato a mano: una fermata con 26 passaggi all'ora è a 40 m, "
            "ma copre solo un quarto della tratta.",
        ],
        "in_english": [
            "Question: on Turin's major roads, where is there a lot of traffic and little public transport nearby?",
            f"Of {u['n_tratte']:,} road sections on Turin's major roads ({u['km']:.1f} km), {u['quota_km_coperta_tp'] * 100:.1f}% of the length "
            "has a frequent stop (at least 4 departures an hour) within 300 m, or the metro within 600 m. Heavy-traffic "
            f"sections (over {round(u['soglie']['q66']):,} vehicles a day): {c['molto_traffico']}; of these, "
            f"{c['da_guardare']} also have little public transport.",
            "In practice this is one main case: Corso Regina Margherita westbound, a fast road with no frequent stop "
            "within 300 m, plus one stretch of Corso Moncalieri covered for only a quarter of its length.",
            f"Limits: traffic figures are estimates with a typical error of ±{fascia50}%; use them to rank the roads, not "
            "to count vehicles.",
        ],
        "mappa": {"id": "imq", "tema": "Spostamenti",
                  "nota": "Nella mappa, tema «Spostamenti»: quanti spostamenti partono da ogni zona e dove vanno (indagine 2022, feriale)."},
        "fonti": ["docs/en/METHODS.md",
                  "data/processed/risultato8_traffico_tp_v2.json"],
        "generato": ora(),
        "avviso": [
            "Traffico stimato, sensori 5T misurati, orari GTT programmati",
            f"Traffico stimato con un modello tarato su {err['n']} sensori: errore tipico ±{fascia50}%. "
            "Trasporto pubblico = fermate con almeno 4 passaggi all'ora entro 300 m o metro entro 600 m."
        ],
        "scenari": [{
            "nome": "Oggi",
            "numeri": [
                num("Km di strade grandi di Torino", round(u["km"], 1), "km"),
                num("Con fermate frequenti vicine", round(u["quota_km_coperta_tp"] * 100, 1), "%"),
                num("Tratte con molto traffico", c["molto_traffico"], "tratte"),
                num("Molto traffico e poco trasporto pubblico", c["da_guardare"], "tratte"),
                num("Errore tipico della stima", fascia50, "%"),
            ],
            "nota": "Le 5 tratte sono quasi tutte su Corso Regina Margherita ovest; una su Corso Moncalieri.",
        }],
    }




def area_tempi_js():
    """Scrive data/area_tempi.js (dati dell'«area che si espande», letti da assets/area.js) dal file dello script 99 e ritorna il grafico della scheda;
    None se il file dello script 99 non c'e' ancora (la scheda esce senza il grafico). L'auto e' solo la stima corretta col controllo (decisione 16 di §2)."""
    f = comune.PROC / "area_tempi.json"
    if not f.is_file():
        print("AVVISO: data/processed/area_tempi.json non c'e' (script 99): la scheda 4 esce senza l'area che si espande")
        return None
    a = json.loads(f.read_text(encoding="utf-8"))
    if a.get("finto") or a["parametri"].get("prova"):
        print("AVVISO: area_tempi.json e' una prova o ha tempi finti: la scheda 4 esce senza l'area che si espande")
        return None
    p, s, z = a["parametri"], a["sezioni"], a["zone"]
    la0, lo0 = p["origine"]
    dati = {"soglie": p["soglie"],
            "ox": round((p["punto_coord"][1] - lo0) * p["scala_coordinate"]), "oy": round((p["punto_coord"][0] - la0) * p["scala_coordinate"]),
            "x": s["x"], "y": s["y"], "r": s["res"], "z": s["zona"],
            "c": {"m": a["castello"]["mezzi"], "k": a["castello"]["auto_corretta_min"]},
            "zn": [n.replace("Torino, ", "") for n in z["nomi"]], "zm": z["mezzi"], "zk": z["auto_corretta_min"]}
    (comune.RADICE / "data" / "area_tempi.js").write_text(
        "// generato da scripts/schede_risultati.py (dati: scripts/99_area_tempi.py) - non modificare a mano\nwindow.AREA_TEMPI = "
        + json.dumps(dati, separators=(",", ":")) + ";\n", encoding="utf-8")
    q = a["quote_residenti"]
    return {"tipo": "area", "titolo": "L'area che si espande: dove si arriva in 10, 20, 30 e 45 minuti",
            "nota": f"Da Piazza Castello, alle 7:45 di un feriale. In 30 minuti si raggiungono {circa(q['mezzi']['30'], '%')} dei torinesi coi mezzi pubblici "
                    f"e {round(q['auto_corretta_min']['30'])}% in auto (traffico tipico, parcheggio compreso)."}


SOGLIA_INTERVISTE = 30   # L9: una coppia si nomina in pagina solo con almeno 30 interviste (SOGLIA_N dello script 14; l'elenco filtrato lo scrive lo script 93)


def forma_r8(s):
    """Scheda R8: tempo coi mezzi pubblici contro tempo in auto (script 93). L'auto e' solo la stima corretta col controllo con TomTom (decisione 16 di §2);
    il numero grande e' la media delle 4 ore del giorno (comune.rapporto_medio_giorno); in coda la copertura delle strade."""
    t = json.loads((comune.PROC / "tp_contro_auto.json").read_text(encoding="utf-8"))
    sens5t = leggi("velocita_5t.json")
    par, ti = t["parametri"], t["titolo"]
    scelta_testo = None   # L23: la prova sulla scelta del mezzo (senza esito) esce dai limiti della scheda; resta nelle note tecniche e nel rapporto dello script 102
    # L23: tempi coi mezzi corretti con le misure (script 105): attesa in piu', ritardo a bordo per minuto, quota a bordo; il valore da orario va nel calcolo
    cz = None
    try:
        cz = leggi("correzione_tempi_mezzi.json")
    except FileNotFoundError:
        pass
    testi_correzione = []
    if cz and ti.get("da_orario"):
        fz = cz["per_fascia"]["punta_mattina"]
        testi_correzione = [f"Il tempo da orario ha in più l'attesa alla fermata misurata ({virgola(fz['attesa_in_piu_min'])} minuti).",
                            f"Il ritardo a bordo misurato ({virgola(round(100 * fz['ritardo_per_minuto'], 1))} minuti ogni 100) vale per il {round(100 * cz['quota_a_bordo']['mediana'])}% del tempo, quello passato a bordo.",
                            f"I cambi non si contano: stima prudente. Da orario il rapporto mediano è {virgola(round(ti['da_orario']['mediano_basso'], 1))}."]
    ab = t["gruppi"]["ab"]
    # tempo in auto = stima aperta corretta col fattore unico del controllo con TomTom (la stima aperta e' piu' veloce in tutti i percorsi controllati)
    fc = comune.fattore_controllo()
    cor = ab["limite_corretto"]
    ctr = leggi("controllo_navigatori_riepilogo.json")
    medio = comune.rapporto_medio_giorno()          # media delle 4 ore del giorno; None se manca ore_del_giorno.json: allora vale il valore delle 8
    x = medio if medio is not None else round(ti["mediano_corretto"], 1)
    f1, f2, f3 = par["fasce"]
    coppie_ab = [p for p in t["coppie"] if p["gruppo"] in ("a", "b")]
    ordinate = sorted(coppie_ab, key=lambda p: -p["auto"])[:600]
    nomi_fasce = [f"meno di {virgola(f1)} volte", f"da {virgola(f1)} a {virgola(f2)} volte", f"da {virgola(f2)} a {virgola(f3)} volte", f"oltre {virgola(f3)} volte"]
    toni = ["verde", "giallo", "arancio", "rosso"]

    principale = {"tipo": "barre", "titolo": "Auto del mattino, per quante volte i mezzi pubblici impiegano più dell'auto", "unita": "%", "max": 100,
                  "nota": "Ogni barra è una fascia: coi mezzi pubblici si impiega quel multiplo del tempo in auto. Coppie Torino-Torino e Torino-cintura.",
                  "voci": [{"label": n, "valore": round(b["pct"]), "tono": tn, "testo": f"{round(b['pct'])}%"}
                           for n, b, tn in zip(nomi_fasce, cor["fasce"], toni)]}
    disp = {"tipo": "dispersione", "titolo": "Tempo in auto e tempo coi mezzi pubblici, una coppia di zone per punto",
            "xlabel": "minuti in auto (mattino)", "ylabel": "minuti coi mezzi pubblici",
            "punti": [[round(comune.auto_corretta(p["auto_stima_min"], fc), 1), p["tp_min"], p["auto"]] for p in ordinate],
            "linee": [{"k": f1, "label": f"{virgola(f1)} volte"}, {"k": f2, "label": "il doppio"}],
            "nota": "Ogni punto è una coppia di zone, grande quanto le auto del mattino; sopra una linea i mezzi pubblici impiegano più di quel multiplo del tempo in auto."}
    # gara (Leo, 23/10; 24/10: sempre alle 8, cambia solo il luogo): viaggi tipici del mattino fra zone, le coppie con più auto, una partenza diversa per corsa
    od = comune.ore_del_giorno()
    nomi_z = {z["zona"]: z["nome"] for z in t["per_zona"]}
    for p in t["peggiori"]:
        nomi_z.setdefault(p["da"], p["da_nome"]); nomi_z.setdefault(p["a"], p["a_nome"])
    corto = lambda c: nome_pulito(nomi_z.get(c, c).replace("Torino, ", ""))
    viste, viaggi = set(), []
    for p in sorted(coppie_ab, key=lambda p: -p["auto"]):
        if p["da"] in viste or p["da"] == p["a"] or p["da"] not in nomi_z or p["a"] not in nomi_z or p["interviste"] < SOGLIA_INTERVISTE:
            continue
        viste.add(p["da"])
        a_b = comune.auto_corretta(p["auto_stima_min"], fc)
        v = {"nome": corto(p["da"]), "arrivo": corto(p["a"]), "bus": p["tp_min"], "auto_min": round(a_b, 1),
             "giudizio": f"coi mezzi {virgola(round(p['tp_min'] / a_b, 1))} volte il tempo dell'auto"}
        viaggi.append(v)
        if len(viaggi) == 6:
            break
    gara = {"tipo": "gara", "titolo": "I viaggi in auto più frequenti del mattino: bus contro auto", "luoghi": viaggi, "scelto": 0,
            "nota": f"Bus e auto partono insieme, uno dopo l'altro, per i {len(viaggi)} viaggi in auto più frequenti del mattino. Il tempo in auto comprende il parcheggio."}
    ore_linea = None
    if od:
        ore_linea = {"tipo": "linea", "titolo": "Quante volte il tempo dell'auto, ora per ora", "unita": "volte",
                     "nota": f"Rapporto fra il tempo coi mezzi e il tempo in auto, pesato per le auto del mattino, alle {len(od['ore'])} ore del giorno.",
                     "categorie": [o["label"] for o in od["ore"]],
                     "serie": [{"label": "rapporto", "valori": [round(o["ab"]["limite_corretto"]["mediano"], 1) for o in od["ore"]]}]}
    # costi (script 103) e valore del tempo (§6.6): v = costo in piu' al mese con la sosta pagata / (minuti in piu' a viaggio x 2 x 20 / 60), ai 5 euro
    cj = leggi("costo_del_viaggio.json")
    rj, reg_c, pr_c = cj["riepilogo"], cj["regole"], cj["prezzi"]
    ba = leggi("r6_bus_contro_auto.json")
    punti_tp = [l for l in ba["luoghi"] if l["tipo"] == "punto_prioritario" and l.get("tp_min") is not None]
    m_b = round(statistics.median(l["tp_min"] - comune.auto_corretta(l["auto_stima_min"], fc) for l in punti_tp), 1)
    e_mese = rj["differenza_mese_sente_mediana"]
    ore_mese = reg_c["giorni_mese"] * 2 / 60.0
    v_b = 5 * round(e_mese / (m_b * ore_mese) / 5)
    v_pieno = 5 * round(rj["differenza_mese_pieno_mediana"] / (m_b * ore_mese) / 5)
    mz = rj["mese"]["mezzi"]
    sp, pg = rj["mese"]["sosta_pagata"], rj["mese"]["parcheggio_gratis"]

    def voce_auto(label, sente, pieno):
        return {"label": label, "valore": round(sente), "prima": round(pieno), "tono": "rosso", "testo": f"{round(sente)} € ({round(pieno)} € col costo pieno)"}

    def voce_mezzi(label, euro_mese):
        return {"label": label, "valore": round(euro_mese), "tono": "verde", "testo": f"{round(euro_mese)} €"}
    graf_mese = {"tipo": "barre_gruppi", "titolo": "Un mese di lavoro vicino al centro: quanto costa", "unita": "euro",
                 "nota": "La barra chiara è il costo pieno dell'auto (ACI).",
                 "gruppi": [{"label": "Auto, sosta pagata in strada", "voci": [voce_auto("Carburante e sosta", sp["sente"], sp["pieno"])]},
                            {"label": "Auto, parcheggio gratis al lavoro", "voci": [voce_auto("Solo carburante", pg["sente"], pg["pieno"])]},
                            {"label": "Mezzi pubblici", "voci": [voce_mezzi(f"Biglietti ({reg_c['viaggi_abbonamento']} viaggi)", mz["biglietti"]),
                                                              voce_mezzi("Abbonamento mensile", mz["mensile"]),
                                                              voce_mezzi("Abbonamento annuale, al mese", mz["annuale_su_12"])]}]}
    area = area_tempi_js()
    anima = {"tipo": "area", "didascalia": area["nota"]} if area else None   # l'animazione principale della scheda (e della home): l'area che si espande
    senza_ab = ab["senza_collegamento"]
    par_crit = [["Zone", f"{par['n_zone']} zone dell'indagine sugli spostamenti ({par['n_zone_torino']} di Torino), fino a {par['punti_per_zona']} punti ciascuna"],
                ["Mezzi pubblici", f"partenza {par['partenza']}-8:15 di un feriale, mediana, cammino a {virgola(par['velocita_piedi_kmh'])} km/h, al massimo {par['tempo_max_min']} minuti"],
                ["Auto", f"guida × {virgola(round(fc, 2))} + {virgola(par['minuti_parcheggio'])} minuti: fattore unico dal controllo su {ctr['percorsi']} percorsi con TomTom"],
                ["Periodo dei sensori", periodo_it(sens5t["periodo"]["da"], sens5t["periodo"]["a"])],
                ["Fasce del rapporto", f"sotto {virgola(f1)}, {virgola(f1)}-{virgola(f2)}, {virgola(f2)}-{virgola(f3)}, oltre {virgola(f3)}"]]
    return forma_base(
        s,
        (f"Coi mezzi pubblici si impiega in media {virgola(x)} volte il tempo dell'auto" if medio is not None
         else f"Al mattino, coi mezzi pubblici si impiega {virgola(x)} volte il tempo dell'auto"),
        ("Quanto ci si mette in più coi mezzi pubblici che in auto?" if medio is not None
         else "Al mattino, quanto ci si mette in più coi mezzi pubblici che in auto?"),
        {"valore": x, "unita": "volte",
         "testo": ("il tempo dell'auto, per i viaggi in auto fra zone diverse" if medio is not None
                   else "il tempo dell'auto, per i viaggi in auto del mattino fra zone diverse"),
         "breve": "il tempo dell'auto, coi mezzi pubblici"},
        principale,
        [f"Si risparmiano {circa(m_b)} minuti a viaggio, ma la sosta costa {circa(round(e_mese, -1))} € al mese. È come pagare il tempo {v_b} € l'ora.",
         f"Senza sosta da pagare, l'auto costa meno dell'abbonamento fino a {circa(rj['soglia_km_senza_sosta'], ' km')}."],
        ([ore_linea] if ore_linea else []) + [gara, graf_mese, disp],
        ["Le zone sono quelle dell'indagine sugli spostamenti 2022 con punti di calcolo; ognuna ha fino a 5 punti.",
         " ".join(["Mezzi pubblici: a piedi, bus, tram e metro, con partenza fra le 7:45 e le 8:15. Si prende la mediana."] + testi_correzione),
         "Auto: percorso più veloce sulla rete stradale. Velocità da sensori e bus, 20 secondi per semaforo, più 5 minuti per parcheggiare.",
         f"Tempi in auto da un modello aperto, corretti con un fattore unico ({virgola(round(fc, 2))}). Il fattore è misurato su {ctr['percorsi']} percorsi con TomTom: la stima aperta era più veloce in {ctr['percorsi']} su {ctr['percorsi']}.",
         f"Rapporto = tempo coi mezzi diviso tempo in auto, in fasce fisse. Le auto di una coppia sono i viaggi in auto dell'indagine, dalle 6 alle 10 di un feriale. "
         f"Il grafico per fasce vale per il {round(100 * ti['auto_collegate'] / t['totale_auto_zone'])}% delle auto del mattino ({migliaia(ti['auto_collegate'])}). Il grafico a punti mostra le {len(ordinate)} coppie con più auto.",
         f"Costi: prezzi del {cj['consultato'][8:10]}/{cj['consultato'][5:7]}/{cj['consultato'][:4]} (carburante self entro 5 km da Piazza Castello, costo ACI 2026, tariffe GTT). Sosta: {virgola(pr_c['sosta_ordinaria_ora'])} euro l'ora per {reg_c['ore_sosta_lavoro']} ore e {reg_c['giorni_mese']} giorni al mese.",
         f"Valore del tempo: costo in più al mese con la sosta pagata, diviso i minuti in più a viaggio. Si contano 2 viaggi al giorno e {reg_c['giorni_mese']} giorni, ai 5 euro; col costo pieno ACI circa {v_pieno} euro l'ora."],
        par_crit,
        ["Fuori Torino mancano treni e altre aziende: le coppie fra comuni della cintura non sono nel numero. Senza i treni metropolitani, dove ci sono, i mezzi pubblici risultano più lenti del vero. L'orario è quello programmato, corretto con le attese e i ritardi misurati.",
         f"Tempi in auto da un modello aperto, non misurati sul singolo viaggio. Il controllo con TomTom su {ctr['percorsi']} percorsi li trova ottimistici: per questo sono corretti con un fattore unico.",
         f"L'indagine è un campione. I viaggi dentro una zona e {migliaia(senza_ab['coppie'])} coppie senza collegamento ({migliaia(senza_ab['auto'])} auto) non sono nel confronto.",
         "Una Golf come auto di riferimento. La zona a traffico limitato e gli abbonamenti alla sosta non sono nel conto. I prezzi sono quelli di un giorno."]
        + ([scelta_testo] if scelta_testo else []),
        None,
        **({"anima": anima} if anima else {}))
