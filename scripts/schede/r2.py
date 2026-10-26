"""Risultato 2 (metro di notte, in pausa): arricchimento del riepilogo scritto dallo script 29."""
from schede.comune import il, leggi, migliaia, minuti, virgola, voce




# ---------------------------------------------------------------- Risultato 2

def arricchisci_r2(s):
    r2 = leggi("risultato2_metro_notte.json")
    da, a = r2["finestra"].split("-")
    totale_res = sum(x["res"] for x in r2["notte15"]["dettaglio"])
    n15, n30 = r2["notte15"], r2["notte30"]
    # testi dello script 29 scritti senza accenti: solo per la pagina, il JSON di R2 resta com'e'
    accenti = lambda x: x.replace("piu'", "più").replace(" li'", " lì") if isinstance(x, str) else x
    s["domanda"] = accenti(s["domanda"])
    for sc in s["scenari"]:
        sc["nota"] = accenti(sc.get("nota"))
        for n in sc["numeri"]:
            n["label"] = accenti(n["label"])
    s.update({
        "tag": "PROGRAMMATO / STIMATO",
        "stato": "Chiuso",
        "in_breve": f"La metro M1 non passa dalle {da} alle {a}: in quelle ore restano solo i bus notturni.",
        # numero in grande: quello severo (almeno +soglia_quota di servizi)
        "numero_chiave": ({"valore": n15["residenti_migliorati_quota"], "unita": "residenti",
                           "testo": f"raggiungerebbero almeno il {round(100 * n15['soglia_quota'])}% di servizi in più "
                                    "di notte con una metro ogni 15 minuti"}
                          if "residenti_migliorati_quota" in n15 else
                          {"valore": n15["residenti_migliorati"], "unita": "residenti",
                           "testo": "raggiungerebbero più servizi di notte con una metro ogni 15 minuti"}),
        "racconto": "Uno dei problemi notati all'inizio del progetto: la metro chiude la sera. Dopo l'ultima corsa "
                    f"arriva un bus sostitutivo, poi dalle {da} alle {a} non c'è più niente sulla linea.",
        "risposta": [
            f"Con una metro ogni 15 minuti nel buco notturno, {migliaia(n15['residenti_migliorati'])} residenti "
            f"di Torino e cintura (su {migliaia(totale_res)}) raggiungerebbero più servizi entro 45 minuti.",
            f"Con una corsa ogni 30 minuti sarebbero {migliaia(n30['residenti_migliorati'])}: metà delle corse, "
            f"ma {il(round(100 * n30['residenti_migliorati'] / n15['residenti_migliorati']))}% dei residenti che ci guadagnano.",
            f"L'attesa media teorica alla fermata sarebbe di {virgola(n15['attesa_media_minuti'])} minuti nel primo "
            f"caso e {virgola(n30['attesa_media_minuti'])} nel secondo.",
        ] + ([f"Contando solo chi ha un miglioramento netto (almeno il {round(100 * n15['soglia_quota'])}% di servizi "
              f"raggiungibili in più di notte): {migliaia(n15['residenti_migliorati_quota'])} residenti con la metro ogni "
              f"15 minuti, {migliaia(n30['residenti_migliorati_quota'])} ogni 30."]
             if "residenti_migliorati_quota" in n15 else []),
        "grafici": [
            {"tipo": "orario", "titolo": "La metro M1 nelle 24 ore (giorno feriale)",
             "nota": "Il buco senza metro né bus sostitutivo è quello che lo scenario riempie con corse finte.",
             "righe": [
                 {"label": "Metro M1", "tono": "pieno", "tratti": [[minuti("05:22"), minuti("22:02")]]},
                 {"label": "Bus sostitutivo", "tono": "medio",
                  "tratti": [[minuti("21:35"), 1440], [0, minuti(da)]]},
                 {"label": "Nessun servizio sulla linea", "tono": "vuoto", "tratti": [[minuti(da), minuti(a)]]},
             ]},
            {"tipo": "barre", "titolo": "Residenti che raggiungono più servizi di notte",
             "unita": "residenti",
             "voci": [voce("una corsa ogni 15 minuti", n15["residenti_migliorati"]),
                      voce("una corsa ogni 30 minuti", n30["residenti_migliorati"])]
                     + ([voce(f"ogni 15 minuti, almeno +{round(100 * n15['soglia_quota'])}%", n15["residenti_migliorati_quota"]),
                         voce(f"ogni 30 minuti, almeno +{round(100 * n15['soglia_quota'])}%", n30["residenti_migliorati_quota"])]
                        if "residenti_migliorati_quota" in n15 else [])},
            {"tipo": "barre", "titolo": "Sezioni di censimento migliorate", "unita": "sezioni",
             "nota": f"Su {migliaia(len(n15['dettaglio']))} sezioni di Torino e cintura.",
             "voci": [voce("una corsa ogni 15 minuti", n15["sezioni_migliorate"]),
                      voce("una corsa ogni 30 minuti", n30["sezioni_migliorate"])]},
        ],
        "metodo": [
            f"Dal GTFS ufficiale GTT (giorno feriale del {r2['giorno']}) si trova il buco reale: metro "
            f"05:22-22:02, bus sostitutivo fino alle 00:50, poi niente fino alle 05:22.",
            "Si costruiscono due orari finti, uguali a quello vero più corse della metro nel buco: una ogni 15 "
            "minuti oppure una ogni 30, copiando i tempi dell'ultima corsa vera.",
            "Per ogni sezione di censimento di Torino e cintura si contano i servizi raggiungibili in 45 minuti "
            "(a piedi + trasporto pubblico) alle ore 01, 02, 03 e 04, con e senza le corse finte (motore R5).",
            "Una sezione è \"migliorata\" se il numero di servizi raggiungibili aumenta anche di poco: a Torino "
            "nessuna zona è mai del tutto scoperta di notte, perché ci sono già i bus notturni.",
        ],
        "parametri": [["Finestra", f"{da} - {a}"], ["Ore calcolate", "01, 02, 03, 04"],
                      ["Tempo massimo di viaggio", "45 minuti"],
                      ["Sezioni migliorate (15')", migliaia(n15["sezioni_migliorate"])],
                      ["Sezioni migliorate (30')", migliaia(n30["sezioni_migliorate"])]],
        "limiti": [
            "Orario programmato: niente traffico, ritardi, capienza dei mezzi o passeggeri reali.",
            "\"Servizi raggiungibili\" è un conteggio di destinazioni, non una stima di quante persone "
            "userebbero la metro di notte.",
            "Le corse finte non hanno tempi di sosta alle fermate e non tengono conto di costi e manutenzione notturna.",
            "Non dice quante auto in meno ci sarebbero: serve un metodo a parte.",
        ],
        "in_english": [
            f"Question: if the metro ran through the night gap between {da} and {a} (simulated extra runs), how many residents "
            "would reach more services?",
            f"With a metro every 15 minutes in the gap, {n15['residenti_migliorati']:,} residents of Turin and the belt "
            f"(out of {totale_res:,}) would reach more services within 45 minutes. With a run every 30 minutes, "
            f"{n30['residenti_migliorati']:,} would."
            + (f" Counting only a clear gain (at least {round(100 * n15['soglia_quota'])}% more reachable services at "
               f"night): {n15['residenti_migliorati_quota']:,} and {n30['residenti_migliorati_quota']:,} residents."
               if "residenti_migliorati_quota" in n15 else ""),
            f"The average theoretical wait at the stop would be {n15['attesa_media_minuti']:.1f} minutes in the first "
            f"case and {n30['attesa_media_minuti']:.1f} in the second.",
            "Limits: scheduled timetable only, with no traffic, delays, vehicle capacity or real passengers; the count is "
            "of reachable destinations, not of people using the metro.",
        ],
        "mappa": {"id": "accessibilita", "tema": "Accessibilità ai servizi",
                  "nota": "La mappa mostra la situazione di oggi ora per ora (tema \"Accessibilità ai servizi\", "
                          "cursore dell'ora sulla notte); lo scenario con la metro non è ancora in mappa."},
        "fonti": ["docs/en/METHODS.md",
                  "scripts/28_scenario_metro_notte.py", "scripts/29_risultato2_metro_notte.py"],
    })
    return s
