// generato da scripts/schede_risultati.py - non modificare a mano
window.SCHEDE_RISULTATI = [
 {
  "risultato": "4",
  "titolo": "Puntualità e attese",
  "tag": "MISURATO",
  "stato": "Fatto",
  "in_breve": "L'orario alla fermata promette un passaggio ogni tot minuti. Quanto spesso i mezzi GTT arrivano davvero in ritardo, o a coppie lasciando un buco?",
  "domanda": "Quanto spesso i mezzi GTT arrivano in ritardo, e quanto spesso sulle linee frequenti arrivano a grappolo o lasciano buchi? E quanto si aspetta davvero alla fermata, rispetto a quello che promette l'orario?",
  "numero_chiave": {
   "valore": 16.7,
   "unita": "%",
   "testo": "dei passaggi nei giorni feriali arriva con più di 5 minuti di ritardo"
  },
  "racconto": "Una delle direzioni del progetto: confrontare l'orario promesso con quello reale, usando le posizioni e i ritardi dei mezzi che il progetto raccoglie ogni minuto.",
  "risposta": [
   "Nei giorni feriali il 16,7% dei passaggi arriva con più di 5 minuti di ritardo; il sabato il 17,5%.",
   "Sulle linee frequenti il 21,7% delle coppie di mezzi consecutivi arriva a grappolo o lascia un buco.",
   "Il problema più comune è l'anticipo: il 34,4% dei passaggi feriali arriva più di un minuto prima dell'orario.",
   "Il feed in tempo reale di GTT, usato in precedenza, dava il 6,2% in ritardo invece del 16,7%: smette di aggiornare la fermata all'orario previsto e così sottostima i ritardi.",
   "Oltre 10 minuti: 6,69% nei feriali. GTT dichiara il 2,3% per il 2025: il suo metodo non è pubblicato; qui si misura a ogni fermata con il GPS, su pochi giorni.",
   "Non è la stessa misura: GTT fa la media dell'anno intero, estate e sere comprese, su tutte le linee, con un metodo che non pubblica; il GPS misura pochi giorni di ottobre, solo le linee urbane, dalle 5 a mezzanotte.",
   "Il ritardo cresce lungo la corsa: alla prima fermata è 5,28%, a metà corsa 5,99%, a ogni fermata 6,44%, escluse le fasce 7-9 e 16-19 6,05% (media della settimana).",
   "Tutte e due le misure dicono che i ritardi gravi sono una piccola parte dei passaggi: tra 2,3% e 6,4%.",
   "Tram e bus: in ritardo oltre 5 minuti il 16,2% dei passaggi dei tram e il 16,8% dei bus (feriale).",
   "Linee utili (quelle che toccano più zone affollate): in ritardo oltre 5 minuti il 18,2% dei passaggi, contro il 13,8% delle altre linee (feriale).",
   "Attesa: Nei giorni feriali, sulle linee frequenti, l'orario promette un'attesa media di 4,8 minuti; quella reale è tra 6,4 e 6,5 minuti.",
   "Sono da 1,6 a 1,8 minuti in più a ogni attesa: almeno il 33% oltre la promessa.",
   "La linea con più attesa in più è la 61 (3,2 minuti in più, stima bassa).",
   "Attesa alla fermata sulle linee frequenti (feriale): tram, promessa 4,5 min, in più 1,7-1,7 min; bus, promessa 5,7 min, in più 1,1-2 min."
  ],
  "grafici": [
   {
    "tipo": "pila",
    "titolo": "Come arrivano i mezzi nei giorni feriali",
    "unita": "%",
    "voci": [
     {
      "label": "in anticipo (oltre 1 min)",
      "valore": 34.4
     },
     {
      "label": "puntuali (da -1 a +5 min)",
      "valore": 48.9,
      "tono": "verde"
     },
     {
      "label": "in ritardo (oltre 5 min)",
      "valore": 16.7,
      "tono": "rosso"
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Passaggi in ritardo oltre 5 minuti, per fascia oraria (feriale)",
    "unita": "%",
    "voci": [
     {
      "label": "mattino (7-9)",
      "valore": 16.2,
      "tono": "rosso"
     },
     {
      "label": "giorno (9-16)",
      "valore": 17.0,
      "tono": "rosso"
     },
     {
      "label": "sera (16-19)",
      "valore": 21.1,
      "tono": "rosso"
     },
     {
      "label": "tarda sera (19-24)",
      "valore": 18.8,
      "tono": "rosso"
     },
     {
      "label": "notte e primo mattino (fino alle 7, dati parziali)",
      "valore": 6.6,
      "tono": "rosso"
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Passaggi in ritardo oltre 5 minuti, per tipo di giorno",
    "unita": "%",
    "voci": [
     {
      "label": "feriale",
      "valore": 16.7,
      "tono": "rosso"
     },
     {
      "label": "sabato",
      "valore": 17.5,
      "tono": "rosso"
     },
     {
      "label": "domenica",
      "valore": 12.6,
      "tono": "rosso"
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Le 10 linee più in ritardo (feriale)",
    "unita": "%",
    "nota": "Solo linee ordinarie (nome di sole cifre) con almeno 2000 passaggi osservati. Clicca una linea per vederla nella mappa.",
    "voci": [
     {
      "label": "linea 17",
      "valore": 42.1,
      "link": "mappa_torino.html#tema=puntualita&linea=17&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 6",
      "valore": 40.4,
      "link": "mappa_torino.html#tema=puntualita&linea=6&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 19",
      "valore": 37.0,
      "link": "mappa_torino.html#tema=puntualita&linea=19&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 68",
      "valore": 31.2,
      "link": "mappa_torino.html#tema=puntualita&linea=68&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 66",
      "valore": 29.4,
      "link": "mappa_torino.html#tema=puntualita&linea=66&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 33",
      "valore": 26.7,
      "link": "mappa_torino.html#tema=puntualita&linea=33&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 4",
      "valore": 25.8,
      "link": "mappa_torino.html#tema=puntualita&linea=4&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 72",
      "valore": 24.6,
      "link": "mappa_torino.html#tema=puntualita&linea=72&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 42",
      "valore": 23.7,
      "link": "mappa_torino.html#tema=puntualita&linea=42&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 52",
      "valore": 23.7,
      "link": "mappa_torino.html#tema=puntualita&linea=52&ora=8",
      "tono": "rosso"
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Le 10 linee più irregolari (feriale): grappolo + buco",
    "unita": "%",
    "nota": "Solo linee frequenti (un mezzo ogni 15 minuti o meno) con almeno 100 coppie osservate. Clicca una linea per vederla nella mappa.",
    "voci": [
     {
      "label": "linea 14",
      "valore": 47.5,
      "link": "mappa_torino.html#tema=puntualita&linea=14&ora=8"
     },
     {
      "label": "linea 4",
      "valore": 40.5,
      "link": "mappa_torino.html#tema=puntualita&linea=4&ora=8"
     },
     {
      "label": "linea 45",
      "valore": 38.6,
      "link": "mappa_torino.html#tema=puntualita&linea=45&ora=8"
     },
     {
      "label": "linea 43",
      "valore": 34.8,
      "link": "mappa_torino.html#tema=puntualita&linea=43&ora=8"
     },
     {
      "label": "linea 17",
      "valore": 31.6,
      "link": "mappa_torino.html#tema=puntualita&linea=17&ora=8"
     },
     {
      "label": "linea 30",
      "valore": 31.2,
      "link": "mappa_torino.html#tema=puntualita&linea=30&ora=8"
     },
     {
      "label": "linea 12",
      "valore": 27.8,
      "link": "mappa_torino.html#tema=puntualita&linea=12&ora=8"
     },
     {
      "label": "linea 29",
      "valore": 26.5,
      "link": "mappa_torino.html#tema=puntualita&linea=29&ora=8"
     },
     {
      "label": "linea 63",
      "valore": 26.0,
      "link": "mappa_torino.html#tema=puntualita&linea=63&ora=8"
     },
     {
      "label": "linea 68",
      "valore": 26.0,
      "link": "mappa_torino.html#tema=puntualita&linea=68&ora=8"
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Tram contro bus (feriale)",
    "unita": "%",
    "nota": "Tram: 262.736 passaggi; bus: 986.502.",
    "voci": [
     {
      "label": "tram: in ritardo oltre 5 min",
      "valore": 16.2,
      "tono": "rosso"
     },
     {
      "label": "bus: in ritardo oltre 5 min",
      "valore": 16.8,
      "tono": "rosso"
     },
     {
      "label": "tram: in ritardo oltre 10 min",
      "valore": 6.48,
      "tono": "rosso"
     },
     {
      "label": "bus: in ritardo oltre 10 min",
      "valore": 6.74,
      "tono": "rosso"
     },
     {
      "label": "tram: a grappolo o con un buco",
      "valore": 26.7
     },
     {
      "label": "bus: a grappolo o con un buco",
      "valore": 18.4
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Ritardo a fine corsa (feriale)",
    "unita": "min",
    "nota": "Ritardo mediano alle ultime 3 fermate della corsa, in minuti. Solo linee ordinarie con almeno 100 passaggi di fine corsa. I minuti ogni 10 km (ritardo diviso la lunghezza della corsa) sono nel rapporto: per km le linee corte vengono premiate. Clicca una linea per vederla nella mappa: la mappa si apre alle 8 di un feriale.",
    "voci": [
     {
      "label": "linea 4 (4,1 min ogni 10 km)",
      "valore": 6.1,
      "link": "mappa_torino.html#tema=puntualita&linea=4&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 17 (2,8 min ogni 10 km)",
      "valore": 4.7,
      "link": "mappa_torino.html#tema=puntualita&linea=17&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 19 (7 min ogni 10 km)",
      "valore": 4.2,
      "link": "mappa_torino.html#tema=puntualita&linea=19&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 6 (7,8 min ogni 10 km)",
      "valore": 3.5,
      "link": "mappa_torino.html#tema=puntualita&linea=6&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 68 (2,9 min ogni 10 km)",
      "valore": 3.1,
      "link": "mappa_torino.html#tema=puntualita&linea=68&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 67 (2,4 min ogni 10 km)",
      "valore": 2.7,
      "link": "mappa_torino.html#tema=puntualita&linea=67&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 72 (2,4 min ogni 10 km)",
      "valore": 2.6,
      "link": "mappa_torino.html#tema=puntualita&linea=72&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 33 (2,2 min ogni 10 km)",
      "valore": 2.5,
      "link": "mappa_torino.html#tema=puntualita&linea=33&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 66 (1,9 min ogni 10 km)",
      "valore": 2.3,
      "link": "mappa_torino.html#tema=puntualita&linea=66&ora=8",
      "tono": "rosso"
     },
     {
      "label": "linea 42 (2,8 min ogni 10 km)",
      "valore": 2.2,
      "link": "mappa_torino.html#tema=puntualita&linea=42&ora=8",
      "tono": "rosso"
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Linee utili contro altre (feriale)",
    "unita": "%",
    "nota": "Linee utili = le 54 che toccano più delle zone dove arriva più gente per km² (Risultato 3). Passaggi: 820.786 sulle utili, 428.452 sulle altre.",
    "voci": [
     {
      "label": "linee utili: in ritardo oltre 5 min",
      "valore": 18.2,
      "tono": "rosso"
     },
     {
      "label": "altre linee: in ritardo oltre 5 min",
      "valore": 13.8,
      "tono": "rosso"
     },
     {
      "label": "linee utili: a grappolo o con un buco",
      "valore": 23.0
     },
     {
      "label": "altre linee: a grappolo o con un buco",
      "valore": 17.4
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Attesa media alla fermata per fascia oraria (feriale)",
    "unita": "min",
    "nota": "Barra chiara = attesa promessa, barra scura = attesa reale (stima bassa).",
    "voci": [
     {
      "label": "mattino (7-9)",
      "valore": 5.85,
      "prima": 4.53
     },
     {
      "label": "giorno (9-16)",
      "valore": 5.33,
      "prima": 3.88
     },
     {
      "label": "sera (16-19)",
      "valore": 6.53,
      "prima": 4.41
     },
     {
      "label": "tarda sera (19-24)",
      "valore": 9.99,
      "prima": 8.21
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Minuti in più di attesa, per fascia oraria (feriale)",
    "unita": "min",
    "forbice": true,
    "nota": "Barra chiara = stima bassa, barra scura = stima alta.",
    "voci": [
     {
      "label": "mattino (7-9)",
      "valore": 1.66,
      "prima": 1.31
     },
     {
      "label": "giorno (9-16)",
      "valore": 1.7,
      "prima": 1.46
     },
     {
      "label": "sera (16-19)",
      "valore": 1.98,
      "prima": 2.12
     },
     {
      "label": "tarda sera (19-24)",
      "valore": 1.71,
      "prima": 1.77
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Le 10 linee con più attesa in più (feriale, stima bassa)",
    "unita": "min",
    "nota": "Solo linee con almeno 30 intervalli osservati.",
    "voci": [
     {
      "label": "linea 61",
      "valore": 3.2
     },
     {
      "label": "linea 33",
      "valore": 2.3
     },
     {
      "label": "linea 4",
      "valore": 2.2
     },
     {
      "label": "linea 46",
      "valore": 1.9
     },
     {
      "label": "linea 16 CD",
      "valore": 1.6
     },
     {
      "label": "linea 56",
      "valore": 1.6
     },
     {
      "label": "linea 15",
      "valore": 1.4
     },
     {
      "label": "linea 2",
      "valore": 1.4
     },
     {
      "label": "linea 55",
      "valore": 1.3
     },
     {
      "label": "linea 3",
      "valore": 1.2
     }
    ]
   }
  ],
  "metodo": [
   "Il progetto registra ogni minuto le posizioni GPS dei mezzi GTT.",
   "Per ogni corsa e fermata si prende l'istante in cui il GPS del mezzo passa a meno di 60 metri dalla fermata e lo si confronta con l'orario ufficiale (GTFS).",
   "Classi: in anticipo sotto -1 minuto, puntuale da -1 a +5, in ritardo oltre +5.",
   "Regolarità: per due mezzi consecutivi della stessa linea alla stessa fermata, \"grappolo\" se l'intervallo vero è meno della metà di quello previsto, \"buco\" se è più del doppio. Solo linee con un mezzo ogni 15 minuti o meno."
  ],
  "parametri": [
   [
    "Periodo",
    "2026-10-10 - 2026-10-22"
   ],
   [
    "Passaggi con GPS valido",
    "1.605.045 (79,7% di quelli programmati dalle corse viste)"
   ],
   [
    "Soglia ritardo",
    "5 min"
   ],
   [
    "Soglia anticipo",
    "-1 min"
   ],
   [
    "Distanza dalla fermata",
    "entro 60 m"
   ]
  ],
  "limiti": [
   "Pochi giorni (7 feriali, 2 sabati, 1 domeniche), e non tutti interi: sabato 10 dalle 15, lunedì 12 dalle 12, martedì 13 con buchi il pomeriggio e la sera, domenica 18 fino alle 9:30 (poi guasto del feed GTT). Ogni giorno conta con le ore che hanno dati.",
   "La raccolta si ferma a mezzanotte e riparte verso le 5: la notte non è misurata.",
   "Il GPS copre solo le linee urbane (circa 90): le extraurbane non ci sono mai. Anche sulle linee coperte alcune corse non sono mai viste dal GPS: se erano saltate davvero, la puntualità reale è peggiore e i buchi sono più di quelli contati.",
   "Il GPS c'è per circa l'80% dei passaggi delle corse viste; le corse mai viste dal GPS non si contano.",
   "Distanza di 60 metri dalla fermata: un mezzo fermo poco prima conta come arrivato poco dopo.",
   "Dice quanto spesso c'è ritardo, non quante persone aspettano né quanto erano pieni i mezzi.",
   "Arrivi misurati con il GPS dei mezzi (a meno di 60 metri dalla fermata); il vecchio feed GTT, controllato col GPS, dava una differenza tipica di 0,5 minuti.",
   "Solo le linee urbane viste dal GPS; niente extraurbane e niente notte.",
   "Le corse mancanti rendono il risultato una forbice, non un numero solo.",
   "Vale per chi arriva alla fermata senza guardare orario o app: è il caso tipico delle linee frequenti, non di quelle rare (per quelle conta la puntualità, risultato 4).",
   "Pochi giorni (gli stessi del risultato 4, non tutti interi): va rifatto con più settimane di dati. La domenica le linee frequenti sono poche: troppo pochi dati per dare un numero."
  ],
  "in_english": [
   "Question: how often do GTT vehicles arrive late, and how often do frequent lines bunch together or leave gaps?",
   "On weekdays 16.7% of departures arrive more than 5 minutes late; on Saturdays 17.5%. On frequent lines 21.7% of consecutive pairs of vehicles bunch together or leave a gap.",
   "The most common problem is early arrival: 34.4% of weekday departures arrive more than one minute before the timetable.",
   "Limits: only 7 weekdays, 2 Saturdays and 1 Sundays of data, some of them partial; the night is not measured.",
   "Arrivals are now measured with the vehicles' GPS; the GTT real-time feed we used before gave 6.2% late instead of 16.7% because it stops updating a stop at its scheduled time, so it underestimates delays.",
   "More than 10 minutes late: 6.69% of weekday departures. GTT reports 2.3% for 2025: its method is not published; we measure at every stop with GPS, over a few days.",
   "Why our number differs from GTT's 2.3% (more than 10 minutes late, 2025): GTT averages the whole year on all lines with an unpublished method; we measure a few October days on urban lines. At the first stop of the trip we get 5.28%, at every stop 6.44% (weekly average).",
   "Trams vs buses (weekdays): 16.2% of tram departures and 16.8% of bus departures are more than 5 minutes late.",
   "Delay at the end of the trip (median, last stops): highest on line 4 (6.1 minutes).",
   "Useful lines (touching the busiest zones per km2): 18.2% of departures more than 5 minutes late, other lines 13.8% (weekdays).",
   "On weekdays the timetable promises an average wait of 4.8 minutes; the real one is between 6.4 and 6.5 minutes. That is 1.6 to 1.8 minutes more per wait, at least 33% above the promise.",
   "Limits: only 7 weekdays of data so far; real arrivals are measured with the vehicles' GPS (within 60 metres of the stop); the night is not included.",
   "Waiting time on frequent lines (weekdays): trams promise 4.5 min, 1.7-1.7 min more in reality; buses 5.7 min, 1.1-2.0 min more."
  ],
  "mappa": {
   "id": "puntualita",
   "tema": "Puntualità delle linee",
   "nota": "Nella mappa, tema «Puntualità delle linee»: ogni linea colorata per ritardo nell'ora scelta con il cursore."
  },
  "fonti": [
   "docs/en/METHODS.md",
   "scripts/27_risultato4_regolarita.py",
   "scripts/70_risultato9_attesa.py"
  ],
  "generato": "2026-10-26T14:06:29+00:00",
  "avviso": [
   "Pochi giorni di dati",
   "Arrivi misurati con il GPS dei mezzi GTT raccolto dal progetto, 2026-10-10 - 2026-10-22: il GPS c'è per il 80% dei passaggi programmati delle corse viste (prima si usava il feed GTT, che sottostima i ritardi: confronto nella scheda). Giorni non tutti interi e solo linee urbane viste dal GPS: vedi i limiti."
  ],
  "scenari": [
   {
    "nome": "Feriale (7 giorni, 1.249.238 passaggi)",
    "numeri": [
     {
      "label": "Passaggi in ritardo oltre 5 min",
      "prima": null,
      "dopo": 16.7,
      "unita": "%"
     },
     {
      "label": "Coppie di bus a grappolo o con un buco (linee frequenti)",
      "prima": null,
      "dopo": 21.7,
      "unita": "%"
     },
     {
      "label": "Ritardo mediano",
      "prima": null,
      "dopo": 0.2,
      "unita": "min"
     },
     {
      "label": "Passaggi in anticipo oltre 1 min",
      "prima": null,
      "dopo": 34.4,
      "unita": "%"
     },
     {
      "label": "Passaggi in ritardo oltre 10 min",
      "prima": null,
      "dopo": 6.69,
      "unita": "%"
     }
    ],
    "nota": "Molti passaggi risultano in anticipo perché l'orario ufficiale ha margini; un ritardo mediano negativo vuol dire 'di solito un po' prima'."
   },
   {
    "nome": "Sabato (2 giorni, 244.314 passaggi)",
    "numeri": [
     {
      "label": "Passaggi in ritardo oltre 5 min",
      "prima": null,
      "dopo": 17.5,
      "unita": "%"
     },
     {
      "label": "Coppie di bus a grappolo o con un buco (linee frequenti)",
      "prima": null,
      "dopo": 20.8,
      "unita": "%"
     },
     {
      "label": "Ritardo mediano",
      "prima": null,
      "dopo": 0.4,
      "unita": "min"
     },
     {
      "label": "Passaggi in anticipo oltre 1 min",
      "prima": null,
      "dopo": 32.7,
      "unita": "%"
     },
     {
      "label": "Passaggi in ritardo oltre 10 min",
      "prima": null,
      "dopo": 7.33,
      "unita": "%"
     }
    ]
   },
   {
    "nome": "Domenica (1 giorno, 111.493 passaggi)",
    "numeri": [
     {
      "label": "Passaggi in ritardo oltre 5 min",
      "prima": null,
      "dopo": 12.6,
      "unita": "%"
     },
     {
      "label": "Coppie di bus a grappolo o con un buco (linee frequenti)",
      "prima": null,
      "dopo": 18.4,
      "unita": "%"
     },
     {
      "label": "Ritardo mediano",
      "prima": null,
      "dopo": 0.0,
      "unita": "min"
     },
     {
      "label": "Passaggi in anticipo oltre 1 min",
      "prima": null,
      "dopo": 35.9,
      "unita": "%"
     },
     {
      "label": "Passaggi in ritardo oltre 10 min",
      "prima": null,
      "dopo": 4.31,
      "unita": "%"
     }
    ]
   },
   {
    "nome": "Feriale (7 giorni)",
    "numeri": [
     {
      "label": "Attesa media alla fermata, stima bassa",
      "prima": 4.78,
      "dopo": 6.39,
      "unita": "min"
     },
     {
      "label": "Attesa media alla fermata, stima alta",
      "prima": 4.78,
      "dopo": 6.54,
      "unita": "min"
     },
     {
      "label": "Corse programmate assenti dal GPS",
      "prima": null,
      "dopo": 7.7,
      "unita": "%"
     }
    ],
    "nota": "Prima = attesa promessa dall'orario, dopo = attesa reale stimata dai passaggi."
   },
   {
    "nome": "Sabato (2 giorni)",
    "numeri": [
     {
      "label": "Attesa media alla fermata, stima bassa",
      "prima": 4.75,
      "dopo": 6.9,
      "unita": "min"
     },
     {
      "label": "Attesa media alla fermata, stima alta",
      "prima": 4.75,
      "dopo": 6.98,
      "unita": "min"
     },
     {
      "label": "Corse programmate assenti dal GPS",
      "prima": null,
      "dopo": 7.8,
      "unita": "%"
     }
    ]
   }
  ],
  "forma": {
   "tipo_dato": "Tipo di dato: misurato, con la posizione GPS dei mezzi.",
   "titolo": "Circa 1 passaggio su 15 arriva con più di 10 minuti di ritardo",
   "domanda": "Quanto spesso i mezzi GTT arrivano in ritardo?",
   "numero": {
    "valore": 6.69,
    "unita": "%",
    "testo": "dei passaggi feriali arriva con oltre 10 minuti di ritardo",
    "breve": "dei passaggi in ritardo di oltre 10 minuti"
   },
   "principale": {
    "tipo": "pila100",
    "titolo": "Come arrivano i mezzi",
    "unita": "%",
    "nota": "Ogni barra è un tipo di giorno: 100% dei passaggi.",
    "righe": [
     {
      "label": "feriale",
      "voci": [
       {
        "label": "in anticipo (oltre 1 minuto)",
        "valore": 34.4,
        "tono": "blu"
       },
       {
        "label": "puntuali",
        "valore": 48.9,
        "tono": "verde"
       },
       {
        "label": "ritardo da 5 a 10 minuti",
        "valore": 10.01,
        "tono": "giallo"
       },
       {
        "label": "ritardo oltre 10 minuti",
        "valore": 6.69,
        "tono": "rosso"
       }
      ]
     },
     {
      "label": "sabato",
      "voci": [
       {
        "label": "in anticipo (oltre 1 minuto)",
        "valore": 32.7,
        "tono": "blu"
       },
       {
        "label": "puntuali",
        "valore": 49.8,
        "tono": "verde"
       },
       {
        "label": "ritardo da 5 a 10 minuti",
        "valore": 10.17,
        "tono": "giallo"
       },
       {
        "label": "ritardo oltre 10 minuti",
        "valore": 7.33,
        "tono": "rosso"
       }
      ]
     },
     {
      "label": "domenica",
      "voci": [
       {
        "label": "in anticipo (oltre 1 minuto)",
        "valore": 35.9,
        "tono": "blu"
       },
       {
        "label": "puntuali",
        "valore": 51.6,
        "tono": "verde"
       },
       {
        "label": "ritardo da 5 a 10 minuti",
        "valore": 8.29,
        "tono": "giallo"
       },
       {
        "label": "ritardo oltre 10 minuti",
        "valore": 4.31,
        "tono": "rosso"
       }
      ]
     }
    ]
   },
   "punti": [
    "1 passaggio su 6 supera i 5 minuti di ritardo; la linea peggiore è la 17 (~42%).",
    "I bus perdono più tempo tra Plava e Castello di Mirafiori: ~132 minuti ogni giorno feriale.",
    "Sulle linee frequenti si aspetta ~1 minuto e mezzo in più di quanto promette l'orario."
   ],
   "altri": [
    {
     "tipo": "barre",
     "titolo": "Dove i bus perdono tempo: i 10 tratti peggiori (7-9)",
     "unita": "minuti",
     "nota": "Minuti persi ogni giorno feriale sul tratto fra due fermate, con almeno 50 corse osservate. Ogni barra porta alla mappa.",
     "voci": [
      {
       "label": "Plava → Castello di Mirafiori (linea 4)",
       "valore": 132,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Abeti → Tigli (linea 4)",
       "valore": 79,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Carducci → Bramante (linea 17, 17/)",
       "valore": 62,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Chiesa Della Salute → Baldissera Nord (linea 11, 52, 77, 10N, N10)",
       "valore": 33,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Vittorio Veneto → Bonsignore (linea 13)",
       "valore": 30,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Caserma Monte Grappa → Fratelli Carle (linea 10)",
       "valore": 28,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Giardini Reali → Rossini (linea 3, 6, 18, 68, N08, 16 CD)",
       "valore": 27,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Cimitero Rivoli → San Paolo (linea 17, 36, 89, 17/)",
       "valore": 27,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Gran Madre → Vittorio Veneto (linea 56)",
       "valore": 26,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Guido Reni → Siracusa (linea 17, 55, 62, 17/)",
       "valore": 25,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      }
     ]
    },
    {
     "tipo": "linea",
     "titolo": "Ritardo oltre 5 minuti, per fascia oraria (feriale)",
     "unita": "%",
     "categorie": [
      "mattino (7-9)",
      "giorno (9-16)",
      "sera (16-19)",
      "tarda sera (19-24)"
     ],
     "serie": [
      {
       "label": "passaggi in ritardo",
       "valori": [
        16,
        17,
        21,
        19
       ]
      }
     ]
    },
    {
     "tipo": "linea",
     "titolo": "Velocità media dei bus, ora per ora (feriale)",
     "unita": "km/h",
     "nota": "Distanza percorsa divisa per il tempo, fermate e semafori compresi.",
     "categorie": [
      "5",
      "6",
      "7",
      "8",
      "9",
      "10",
      "11",
      "12",
      "13",
      "14",
      "15",
      "16",
      "17",
      "18",
      "19",
      "20",
      "21",
      "22",
      "23"
     ],
     "serie": [
      {
       "label": "velocità dei bus",
       "valori": [
        19,
        17,
        14,
        13,
        14,
        15,
        14,
        14,
        14,
        14,
        14,
        13,
        13,
        13,
        14,
        16,
        18,
        17,
        18
       ]
      }
     ]
    }
   ],
   "calcolo": [
    "Il progetto registra ogni minuto la posizione GPS dei mezzi GTT.",
    "Il passaggio è l'ultimo istante con il GPS a meno di 60 metri dalla fermata. L'orario ufficiale è di partenza.",
    "Il ritardo è quell'istante meno l'orario ufficiale.",
    "In anticipo oltre 1 minuto; in ritardo oltre 5 minuti.",
    "Una lettura al minuto: il ritardo vero è fino a un minuto più grande. Oltre 5 minuti 16,7-20,6%, oltre 10 minuti 6,7-7,9%, in anticipo 23,7-34,4% dei passaggi feriali.",
    "Tratto: due fermate consecutive di una corsa. Minuti persi: somma dei tempi in più sul tratto, diviso i giorni feriali. Solo tratti con almeno 50 corse osservate.",
    "Velocità dei bus: distanza fra posizioni GPS consecutive divisa per il tempo, fermate e semafori compresi. Media dei giorni feriali, pesata sui rilevamenti."
   ],
   "criteri": [
    [
     "Passaggi con GPS valido",
     "1.605.045 (79,7% di quelli programmati dalle corse viste)"
    ],
    [
     "Soglia ritardo",
     "5 min"
    ],
    [
     "Soglia anticipo",
     "-1 min"
    ],
    [
     "Distanza dalla fermata",
     "entro 60 m"
    ],
    [
     "Periodo dei dati",
     "dal 10/10/2026 al 22/10/2026"
    ]
   ],
   "limiti": [
    "Pochi giorni: 7 feriali, 2 sabati e 1 domenica, non tutti interi.",
    "Solo le linee urbane viste dal GPS, dalle 5 a mezzanotte.",
    "Il GPS copre circa l'80% dei passaggi programmati; le corse mai viste non si contano.",
    "Si conta quanto spesso c'è ritardo, non quante persone aspettano."
   ],
   "mappa": {
    "id": "puntualita",
    "nota": "Nella mappa, tema «Puntualità delle linee»: ogni linea colorata per ritardo nell'ora scelta con il cursore."
   },
   "fonti": [
    "GTT (posizioni GPS dei mezzi, dato in tempo reale e orari ufficiali)"
   ],
   "titolo_breve": "Ritardi dei mezzi",
   "anima": {
    "tipo": "quadratini",
    "totale": 100,
    "oltre5": 16.7,
    "oltre10": 6.69,
    "testo_tutto": "su 100 passaggi in un feriale arrivano con oltre 5 minuti di ritardo",
    "fasi": [
     {
      "label": "su 100 al mattino (7-9)",
      "valore": 16.2
     },
     {
      "label": "su 100 di giorno (9-16)",
      "valore": 17.0
     },
     {
      "label": "su 100 alla sera (16-19)",
      "valore": 21.1
     },
     {
      "label": "su 100 a tarda sera (19-24)",
      "valore": 18.8
     }
    ],
    "legenda5": "oltre 5 minuti",
    "legenda10": "oltre 10 minuti",
    "didascalia": "Su 100 passaggi feriali, circa 17 arrivano con più di 5 minuti di ritardo (16,7%); con più di 10 minuti circa 7. Poi il giorno, fascia per fascia."
   },
   "confronto": [
    "GTT dichiara il 2,3% oltre 10 minuti nel 2025: media dell'anno, tutte le linee, metodo non pubblicato.",
    "Il GPS misura pochi giorni di ottobre sulle linee urbane: 6,4% a ogni fermata, 5,3% alla partenza.",
    "Anche contando come GTT alla partenza si trova il 5,3%; il resto della differenza è stagione e metodo.",
    "Solo feriali: 6,69% a ogni fermata, 5,48% alla prima, 6,30% a metà corsa, 6,24% senza le fasce 7-9 e 16-19."
   ],
   "extra": {
    "titolo": "Quanto si aspetta alla fermata",
    "punto": "Sulle linee frequenti si aspetta ~1 minuto e mezzo in più di quanto promette l'orario.",
    "grafico": {
     "tipo": "barre",
     "titolo": "Quanto si aspetta in più di quanto dice l'orario",
     "unita": "min",
     "nota": "Ogni barra è una fascia del giorno feriale: i minuti di attesa in più rispetto all'orario. Fra parentesi l'attesa reale contro quella promessa.",
     "voci": [
      {
       "label": "mattino (7-9)",
       "valore": 1.3,
       "tono": "rosso",
       "testo": "+1,3 min (~6 invece di ~5)"
      },
      {
       "label": "giorno (9-16)",
       "valore": 1.5,
       "tono": "rosso",
       "testo": "+1,5 min (~5 invece di ~4)"
      },
      {
       "label": "sera (16-19)",
       "valore": 2.1,
       "tono": "rosso",
       "testo": "+2,1 min (~7 invece di ~4)"
      },
      {
       "label": "tarda sera (19-24)",
       "valore": 1.8,
       "tono": "rosso",
       "testo": "+1,8 min (~10 invece di ~8)"
      }
     ]
    }
   }
  },
  "forma_en": {
   "tipo_dato": "Type of data: measured, with the GPS position of the vehicles.",
   "titolo": "About 1 arrival in 15 is more than 10 minutes late",
   "domanda": "How often are GTT vehicles late?",
   "numero": {
    "valore": 6.69,
    "unita": "%",
    "testo": "of weekday arrivals are more than 10 minutes late",
    "breve": "of arrivals more than 10 minutes late"
   },
   "principale": {
    "tipo": "pila100",
    "titolo": "How vehicles arrive",
    "unita": "%",
    "nota": "Each bar is a type of day: 100% of arrivals.",
    "righe": [
     {
      "label": "weekday",
      "voci": [
       {
        "label": "early (more than 1 minute)",
        "valore": 34.4,
        "tono": "blu"
       },
       {
        "label": "on time",
        "valore": 48.9,
        "tono": "verde"
       },
       {
        "label": "5 to 10 minutes late",
        "valore": 10.01,
        "tono": "giallo"
       },
       {
        "label": "more than 10 minutes late",
        "valore": 6.69,
        "tono": "rosso"
       }
      ]
     },
     {
      "label": "Saturday",
      "voci": [
       {
        "label": "early (more than 1 minute)",
        "valore": 32.7,
        "tono": "blu"
       },
       {
        "label": "on time",
        "valore": 49.8,
        "tono": "verde"
       },
       {
        "label": "5 to 10 minutes late",
        "valore": 10.17,
        "tono": "giallo"
       },
       {
        "label": "more than 10 minutes late",
        "valore": 7.33,
        "tono": "rosso"
       }
      ]
     },
     {
      "label": "Sunday",
      "voci": [
       {
        "label": "early (more than 1 minute)",
        "valore": 35.9,
        "tono": "blu"
       },
       {
        "label": "on time",
        "valore": 51.6,
        "tono": "verde"
       },
       {
        "label": "5 to 10 minutes late",
        "valore": 8.29,
        "tono": "giallo"
       },
       {
        "label": "more than 10 minutes late",
        "valore": 4.31,
        "tono": "rosso"
       }
      ]
     }
    ]
   },
   "punti": [
    "1 arrival in 6 is more than 5 minutes late; the worst line is 17 (~42%).",
    "Buses lose the most time between Plava and Castello di Mirafiori: ~132 minutes every weekday.",
    "On frequent lines the wait is ~1 and a half minutes longer than the timetable promises."
   ],
   "altri": [
    {
     "tipo": "barre",
     "titolo": "Where buses lose time: the 10 worst segments (7-9)",
     "unita": "minutes",
     "nota": "Minutes lost every weekday on the segment between two stops, with at least 50 trips observed. Each bar leads to the map.",
     "voci": [
      {
       "label": "Plava → Castello di Mirafiori (line 4)",
       "valore": 132,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Abeti → Tigli (line 4)",
       "valore": 79,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Carducci → Bramante (line 17, 17/)",
       "valore": 62,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Chiesa Della Salute → Baldissera Nord (line 11, 52, 77, 10N, N10)",
       "valore": 33,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Vittorio Veneto → Bonsignore (line 13)",
       "valore": 30,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Caserma Monte Grappa → Fratelli Carle (line 10)",
       "valore": 28,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Giardini Reali → Rossini (line 3, 6, 18, 68, N08, 16 CD)",
       "valore": 27,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Cimitero Rivoli → San Paolo (line 17, 36, 89, 17/)",
       "valore": 27,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Gran Madre → Vittorio Veneto (line 56)",
       "valore": 26,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Guido Reni → Siracusa (line 17, 55, 62, 17/)",
       "valore": 25,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      }
     ]
    },
    {
     "tipo": "linea",
     "titolo": "Delay over 5 minutes, by time of day (weekday)",
     "unita": "%",
     "categorie": [
      "morning (7-9)",
      "daytime (9-16)",
      "evening (16-19)",
      "late evening (19-24)"
     ],
     "serie": [
      {
       "label": "late arrivals",
       "valori": [
        16,
        17,
        21,
        19
       ]
      }
     ]
    },
    {
     "tipo": "linea",
     "titolo": "Average bus speed, hour by hour (weekday)",
     "unita": "km/h",
     "nota": "Distance covered divided by time, stops and traffic lights included.",
     "categorie": [
      "5",
      "6",
      "7",
      "8",
      "9",
      "10",
      "11",
      "12",
      "13",
      "14",
      "15",
      "16",
      "17",
      "18",
      "19",
      "20",
      "21",
      "22",
      "23"
     ],
     "serie": [
      {
       "label": "bus speed",
       "valori": [
        19,
        17,
        14,
        13,
        14,
        15,
        14,
        14,
        14,
        14,
        14,
        13,
        13,
        13,
        14,
        16,
        18,
        17,
        18
       ]
      }
     ]
    }
   ],
   "calcolo": [
    "The project records the GPS position of GTT vehicles every minute.",
    "An arrival is the last moment the GPS is within 60 metres of the stop. The official timetable is a departure time.",
    "The delay is that moment minus the official timetable.",
    "Early: more than 1 minute; late: more than 5 minutes.",
    "One reading per minute: the real delay is up to one minute larger. Over 5 minutes 16.7-20.6%, over 10 minutes 6.7-7.9%, early 23.7-34.4% of weekday arrivals.",
    "Segment: two consecutive stops of a trip. Minutes lost: sum of the extra times on the segment, divided by the weekdays. Only segments with at least 50 trips observed.",
    "Bus speed: distance between consecutive GPS positions divided by time, stops and traffic lights included. Average of weekdays, weighted by readings."
   ],
   "criteri": [
    [
     "Arrivals with a valid GPS fix",
     "1,605,045 (79.7% of those scheduled for the trips seen)"
    ],
    [
     "Delay threshold",
     "5 min"
    ],
    [
     "Earliness threshold",
     "-1 min"
    ],
    [
     "Distance from the stop",
     "within 60 m"
    ],
    [
     "Data period",
     "from 10/10/2,026 to 22/10/2,026"
    ]
   ],
   "limiti": [
    "Few days: 7 weekdays, 2 Saturdays and 1 Sunday, not all complete.",
    "Urban lines seen by the GPS only, from 5 a.m. to midnight.",
    "GPS covers about 80% of the scheduled arrivals; trips never seen are not counted.",
    "The figure counts how often there is a delay, not how many people are waiting."
   ],
   "mappa": {
    "id": "puntualita",
    "nota": "Nella mappa, tema «Puntualità delle linee»: ogni linea colorata per ritardo nell'ora scelta con il cursore."
   },
   "fonti": [
    "GTT (GPS positions of vehicles, real-time feed and official timetables)"
   ],
   "titolo_breve": "Vehicle delays",
   "anima": {
    "tipo": "quadratini",
    "totale": 100,
    "oltre5": 16.7,
    "oltre10": 6.69,
    "testo_tutto": "in 100 weekday stop passages are more than 5 minutes late",
    "fasi": [
     {
      "label": "out of 100 in the morning (7-9)",
      "valore": 16.2
     },
     {
      "label": "in 100 during the day (9-16)",
      "valore": 17.0
     },
     {
      "label": "out of 100 in the evening (16-19)",
      "valore": 21.1
     },
     {
      "label": "out of 100 in the late evening (19-24)",
      "valore": 18.8
     }
    ],
    "legenda5": "over 5 minutes",
    "legenda10": "over 10 minutes",
    "didascalia": "Out of 100 weekday stop passages, about 17 are more than 5 minutes late (16.7%); about 7 more than 10 minutes. Then the day, time band by time band."
   },
   "confronto": [
    "GTT reports 2.3% over 10 minutes in 2025: yearly average, all lines, method not published.",
    "The GPS measures a few days of October on urban lines: 6.4% at every stop, 5.3% at departure.",
    "Even counting at departure like GTT, the figure is 5.3%; the rest of the difference is season and method.",
    "Weekdays only: 6.69% at every stop, 5.48% at the first, 6.30% mid-trip, 6.24% without the 7-9 and 16-19 bands."
   ],
   "extra": {
    "titolo": "How long you wait at the stop",
    "punto": "On frequent lines the wait is ~1 and a half minutes longer than the timetable promises.",
    "grafico": {
     "tipo": "barre",
     "titolo": "How much longer the wait is than the timetable says",
     "unita": "min",
     "nota": "Each bar is a time band of the weekday: the extra minutes of waiting compared with the timetable. In brackets, the real wait against the promised one.",
     "voci": [
      {
       "label": "morning (7-9)",
       "valore": 1.3,
       "tono": "rosso",
       "testo": "+1.3 min (~6 instead of ~5)"
      },
      {
       "label": "daytime (9-16)",
       "valore": 1.5,
       "tono": "rosso",
       "testo": "+1.5 min (~5 instead of ~4)"
      },
      {
       "label": "evening (16-19)",
       "valore": 2.1,
       "tono": "rosso",
       "testo": "+2.1 min (~7 instead of ~4)"
      },
      {
       "label": "late evening (19-24)",
       "valore": 1.8,
       "tono": "rosso",
       "testo": "+1.8 min (~10 instead of ~8)"
      }
     ]
    }
   }
  },
  "forma_de": {
   "tipo_dato": "Datenart: gemessen, mit der GPS-Position der Fahrzeuge.",
   "titolo": "Etwa 1 von 15 Abfahrten hat mehr als 10 Minuten Verspätung",
   "domanda": "Wie oft sind die GTT-Fahrzeuge verspätet?",
   "numero": {
    "valore": 6.69,
    "unita": "%",
    "testo": "der Abfahrten an Werktagen haben mehr als 10 Minuten Verspätung",
    "breve": "der Abfahrten mit mehr als 10 Minuten Verspätung"
   },
   "principale": {
    "tipo": "pila100",
    "titolo": "Wie die Fahrzeuge ankommen",
    "unita": "%",
    "nota": "Jeder Balken ist ein Tagestyp: 100% der Abfahrten.",
    "righe": [
     {
      "label": "Werktag",
      "voci": [
       {
        "label": "zu früh (mehr als 1 Minute)",
        "valore": 34.4,
        "tono": "blu"
       },
       {
        "label": "pünktlich",
        "valore": 48.9,
        "tono": "verde"
       },
       {
        "label": "5 bis 10 Minuten Verspätung",
        "valore": 10.01,
        "tono": "giallo"
       },
       {
        "label": "mehr als 10 Minuten Verspätung",
        "valore": 6.69,
        "tono": "rosso"
       }
      ]
     },
     {
      "label": "Samstag",
      "voci": [
       {
        "label": "zu früh (mehr als 1 Minute)",
        "valore": 32.7,
        "tono": "blu"
       },
       {
        "label": "pünktlich",
        "valore": 49.8,
        "tono": "verde"
       },
       {
        "label": "5 bis 10 Minuten Verspätung",
        "valore": 10.17,
        "tono": "giallo"
       },
       {
        "label": "mehr als 10 Minuten Verspätung",
        "valore": 7.33,
        "tono": "rosso"
       }
      ]
     },
     {
      "label": "Sonntag",
      "voci": [
       {
        "label": "zu früh (mehr als 1 Minute)",
        "valore": 35.9,
        "tono": "blu"
       },
       {
        "label": "pünktlich",
        "valore": 51.6,
        "tono": "verde"
       },
       {
        "label": "5 bis 10 Minuten Verspätung",
        "valore": 8.29,
        "tono": "giallo"
       },
       {
        "label": "mehr als 10 Minuten Verspätung",
        "valore": 4.31,
        "tono": "rosso"
       }
      ]
     }
    ]
   },
   "punti": [
    "1 von 6 Abfahrten hat mehr als 5 Minuten Verspätung; die schlechteste Linie ist die 17 (~42%).",
    "Die Busse verlieren die meiste Zeit zwischen Plava und Castello di Mirafiori: ~132 Minuten an jedem Werktag.",
    "Auf Linien mit dichtem Takt wartet man ~1 Minute und eine halbe länger, als der Fahrplan verspricht."
   ],
   "altri": [
    {
     "tipo": "barre",
     "titolo": "Wo die Busse Zeit verlieren: die 10 schlechtesten Abschnitte (7-9)",
     "unita": "Minuten",
     "nota": "Pro Werktag verlorene Minuten auf dem Abschnitt zwischen zwei Haltestellen, bei mindestens 50 beobachteten Fahrten. Jeder Balken führt zur Karte.",
     "voci": [
      {
       "label": "Plava → Castello di Mirafiori (Linie 4)",
       "valore": 132,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Abeti → Tigli (Linie 4)",
       "valore": 79,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Carducci → Bramante (Linie 17, 17/)",
       "valore": 62,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Chiesa Della Salute → Baldissera Nord (Linie 11, 52, 77, 10N, N10)",
       "valore": 33,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Vittorio Veneto → Bonsignore (Linie 13)",
       "valore": 30,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Caserma Monte Grappa → Fratelli Carle (Linie 10)",
       "valore": 28,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Giardini Reali → Rossini (Linie 3, 6, 18, 68, N08, 16 CD)",
       "valore": 27,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Cimitero Rivoli → San Paolo (Linie 17, 36, 89, 17/)",
       "valore": 27,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Gran Madre → Vittorio Veneto (Linie 56)",
       "valore": 26,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      },
      {
       "label": "Guido Reni → Siracusa (Linie 17, 55, 62, 17/)",
       "valore": 25,
       "link": "mappa_torino.html#tema=tratti",
       "tono": "rosso"
      }
     ]
    },
    {
     "tipo": "linea",
     "titolo": "Verspätung über 5 Minuten, nach Zeitfenster (Werktag)",
     "unita": "%",
     "categorie": [
      "morgens (7-9)",
      "tagsüber (9-16)",
      "abends (16-19)",
      "spätabends (19-24)"
     ],
     "serie": [
      {
       "label": "verspätete Abfahrten",
       "valori": [
        16,
        17,
        21,
        19
       ]
      }
     ]
    },
    {
     "tipo": "linea",
     "titolo": "Durchschnittsgeschwindigkeit der Busse, Stunde für Stunde (Werktag)",
     "unita": "km/h",
     "nota": "Zurückgelegte Strecke geteilt durch die Zeit, Haltestellen und Ampeln inklusive.",
     "categorie": [
      "5",
      "6",
      "7",
      "8",
      "9",
      "10",
      "11",
      "12",
      "13",
      "14",
      "15",
      "16",
      "17",
      "18",
      "19",
      "20",
      "21",
      "22",
      "23"
     ],
     "serie": [
      {
       "label": "Geschwindigkeit der Busse",
       "valori": [
        19,
        17,
        14,
        13,
        14,
        15,
        14,
        14,
        14,
        14,
        14,
        13,
        13,
        13,
        14,
        16,
        18,
        17,
        18
       ]
      }
     ]
    }
   ],
   "calcolo": [
    "Das Projekt zeichnet jede Minute die GPS-Position der GTT-Fahrzeuge auf.",
    "Die Abfahrt ist der letzte Moment, in dem das GPS weniger als 60 Meter von der Haltestelle entfernt ist. Die offizielle Fahrplanzeit ist eine Abfahrtszeit.",
    "Die Verspätung ist dieser Moment minus die offizielle Fahrplanzeit.",
    "Zu früh: mehr als 1 Minute; Verspätung: mehr als 5 Minuten.",
    "Eine Messung pro Minute: Die wahre Verspätung ist bis zu eine Minute größer. Über 5 Minuten 16,7-20,6%, über 10 Minuten 6,7-7,9%, zu früh 23,7-34,4% der Abfahrten an Werktagen.",
    "Abschnitt: zwei aufeinanderfolgende Haltestellen einer Fahrt. Verlorene Minuten: Summe der Zusatzzeiten auf dem Abschnitt, geteilt durch die Werktage. Nur Abschnitte mit mindestens 50 beobachteten Fahrten.",
    "Geschwindigkeit der Busse: Abstand zwischen aufeinanderfolgenden GPS-Positionen geteilt durch die Zeit, Haltestellen und Ampeln inklusive. Mittelwert der Werktage, gewichtet nach Messungen."
   ],
   "criteri": [
    [
     "Abfahrten mit gültigem GPS-Signal",
     "1.605.045 (79,7% der planmäßigen Abfahrten der beobachteten Fahrten)"
    ],
    [
     "Schwelle Verspätung",
     "5 Min."
    ],
    [
     "Schwelle zu früh",
     "-1 Min."
    ],
    [
     "Entfernung zur Haltestelle",
     "innerhalb von 60 m"
    ],
    [
     "Zeitraum der Daten",
     "vom 10.10.2026 bis zum 22.10.2026"
    ]
   ],
   "limiti": [
    "Wenige Tage: 7 Werktage, 2 Samstage und 1 Sonntag, nicht alle vollständig.",
    "Nur die vom GPS erfassten Stadtlinien, von 5 Uhr bis Mitternacht.",
    "Das GPS deckt etwa 80% der planmäßigen Abfahrten ab; Fahrten, die nie gesehen wurden, zählen nicht.",
    "Gezählt wird, wie oft es Verspätung gibt, nicht wie viele Menschen warten."
   ],
   "mappa": {
    "id": "puntualita",
    "nota": "Nella mappa, tema «Puntualità delle linee»: ogni linea colorata per ritardo nell'ora scelta con il cursore."
   },
   "fonti": [
    "GTT (GPS-Positionen der Fahrzeuge, Echtzeitdaten und offizielle Fahrpläne)"
   ],
   "titolo_breve": "Verspätungen der Fahrzeuge",
   "anima": {
    "tipo": "quadratini",
    "totale": 100,
    "oltre5": 16.7,
    "oltre10": 6.69,
    "testo_tutto": "von 100 Abfahrten an einem Werktag haben mehr als 5 Minuten Verspätung",
    "fasi": [
     {
      "label": "von 100 morgens (7-9)",
      "valore": 16.2
     },
     {
      "label": "von 100 tagsüber (9-16)",
      "valore": 17.0
     },
     {
      "label": "von 100 abends (16-19)",
      "valore": 21.1
     },
     {
      "label": "von 100 spätabends (19-24)",
      "valore": 18.8
     }
    ],
    "legenda5": "über 5 Minuten",
    "legenda10": "über 10 Minuten",
    "didascalia": "Von 100 Abfahrten an Werktagen haben etwa 17 mehr als 5 Minuten Verspätung (16,7%); mehr als 10 Minuten etwa 7. Danach der Tag, Zeitfenster für Zeitfenster."
   },
   "confronto": [
    "GTT gibt für 2025 2,3% über 10 Minuten an: Jahresmittel, alle Linien, Methode nicht veröffentlicht.",
    "Das GPS misst wenige Tage im Oktober auf den Stadtlinien: 6,4% an jeder Haltestelle, 5,3% an der Starthaltestelle.",
    "Auch bei Zählung an der Starthaltestelle wie bei GTT ergibt sich 5,3%; der Rest des Unterschieds ist Jahreszeit und Methode.",
    "Nur Werktage: 6,69% an jeder Haltestelle, 5,48% an der ersten, 6,30% in der Mitte der Fahrt, 6,24% ohne die Zeitfenster 7-9 und 16-19."
   ],
   "extra": {
    "titolo": "Wie lange man an der Haltestelle wartet",
    "punto": "Auf Linien mit dichtem Takt wartet man ~1 Minute und eine halbe länger, als der Fahrplan verspricht.",
    "grafico": {
     "tipo": "barre",
     "titolo": "Wie viel länger man wartet, als der Fahrplan sagt",
     "unita": "min",
     "nota": "Jeder Balken ist ein Zeitfenster des Werktags: die zusätzlichen Wartezeit-Minuten gegenüber dem Fahrplan. In Klammern die tatsächliche gegen die versprochene Wartezeit.",
     "voci": [
      {
       "label": "morgens (7-9)",
       "valore": 1.3,
       "tono": "rosso",
       "testo": "+1,3 Min. (~6 statt ~5)"
      },
      {
       "label": "tagsüber (9-16)",
       "valore": 1.5,
       "tono": "rosso",
       "testo": "+1,5 Min. (~5 statt ~4)"
      },
      {
       "label": "abends (16-19)",
       "valore": 2.1,
       "tono": "rosso",
       "testo": "+2,1 Min. (~7 statt ~4)"
      },
      {
       "label": "spätabends (19-24)",
       "valore": 1.8,
       "tono": "rosso",
       "testo": "+1,8 Min. (~10 statt ~8)"
      }
     ]
    }
   }
  },
  "numero_pubblico": 1,
  "gruppo": "vetrina",
  "_nome": "risultato4_riepilogo_mappa.json"
 },
 {
  "risultato": "6",
  "titolo": "Parcheggi per lasciare l'auto",
  "tag": "STIMATO / MISURATO (dati scarsi)",
  "stato": "Aggiornato al 26/10/2026",
  "in_breve": "Dove lasciare l'auto prima di entrare in città e proseguire con i mezzi pubblici: come funzionano gli interscambi che ci sono, e dove mancano posti per le auto che entrano ogni mattina.",
  "domanda": "Dove mancano posti per lasciare l'auto prima di entrare in città, vicino a una fermata importante, per le auto che ogni mattina entrano a Torino?",
  "numero_chiave": {
   "valore": 179,
   "unita": "fermate",
   "testo": "su 274 fermate importanti fuori dal centro non hanno abbastanza posti adatti entro 400 m a piedi per le auto in entrata che passano accanto"
  },
  "risposta": [
   "Gli interscambi che ci sono: nei giorni misurati Stura: sempre quasi pieno: 80% di notte, 91% di giorno; Caio Mario: il valore non cambia (1%): forse il contatore è fermo; Sofia: è più pieno di notte che di giorno: 52% di notte, 31% di giorno; Venchi Unica: sempre intorno al 55%; Fermi non trasmette il riempimento. Pieni di giorno: 1 su 5.",
   "Ogni mattina entrano a Torino circa 87.200 auto; oggi il 5,8% di chi arriva in auto prosegue con un mezzo pubblico.",
   "Delle 274 fermate importanti fuori dal centro, 179 non hanno abbastanza posti adatti entro 400 m a piedi per le auto da fermare (68 non ne hanno nessuno).",
   "I punti dove servirebbe di più un parcheggio (posti che mancano, ordine di grandezza): 1. Santa Rita (Santa Rita), 2. Metro Massaua (Parella), 3. Ponte Cavalieri Templari (Moncalieri)."
  ],
  "grafici": [
   {
    "tipo": "profilo",
    "titolo": "Stura (589 posti): sempre quasi pieno: 80% di notte, 91% di giorno",
    "unita": "",
    "nota": "8 giorni validi; linea piena feriale, tratteggiata weekend.",
    "serie": [
     {
      "label": "giorno feriale",
      "valori": [
       0.797,
       0.797,
       0.797,
       0.797,
       0.797,
       0.799,
       0.804,
       0.829,
       0.877,
       0.903,
       0.919,
       0.921,
       0.921,
       0.916,
       0.91,
       0.904,
       0.894,
       0.877,
       0.846,
       0.813,
       0.802,
       0.801,
       0.801,
       0.8
      ]
     },
     {
      "label": "weekend",
      "valori": [
       0.795,
       0.795,
       0.795,
       0.795,
       0.795,
       0.796,
       0.796,
       0.798,
       0.799,
       0.799,
       0.799,
       0.8,
       0.798,
       0.8,
       0.801,
       0.801,
       0.8,
       0.799,
       0.799,
       0.799,
       0.797,
       0.796,
       0.795,
       0.795
      ],
      "tratteggio": true
     }
    ]
   },
   {
    "tipo": "profilo",
    "titolo": "Venchi Unica (437 posti): sempre intorno al 55%",
    "unita": "",
    "nota": "8 giorni validi; linea piena feriale, tratteggiata weekend.",
    "serie": [
     {
      "label": "giorno feriale",
      "valori": [
       0.537,
       0.538,
       0.538,
       0.538,
       0.537,
       0.535,
       0.537,
       0.53,
       0.535,
       0.555,
       0.556,
       0.552,
       0.553,
       0.552,
       0.551,
       0.548,
       0.542,
       0.533,
       0.52,
       0.507,
       0.515,
       0.521,
       0.525,
       0.532
      ]
     },
     {
      "label": "weekend",
      "valori": [
       0.47,
       0.478,
       0.485,
       0.488,
       0.489,
       0.489,
       0.49,
       0.489,
       0.481,
       0.469,
       0.456,
       0.449,
       0.451,
       0.452,
       0.453,
       0.45,
       0.45,
       0.447,
       0.45,
       0.45,
       0.452,
       0.453,
       0.458,
       0.48
      ],
      "tratteggio": true
     }
    ]
   },
   {
    "tipo": "profilo",
    "titolo": "Caio Mario (418 posti): il valore non cambia (1%): forse il contatore è fermo",
    "unita": "",
    "nota": "8 giorni validi; linea piena feriale, tratteggiata weekend.",
    "serie": [
     {
      "label": "giorno feriale",
      "valori": [
       0.016,
       0.011,
       0.01,
       0.011,
       0.011,
       0.01,
       0.01,
       0.009,
       0.009,
       0.009,
       0.01,
       0.01,
       0.009,
       0.009,
       0.01,
       0.011,
       0.011,
       0.011,
       0.01,
       0.012,
       0.012,
       0.012,
       0.013,
       0.013
      ]
     },
     {
      "label": "weekend",
      "valori": [
       0.025,
       0.017,
       0.017,
       0.017,
       0.017,
       0.017,
       0.017,
       0.016,
       0.018,
       0.019,
       0.019,
       0.021,
       0.021,
       0.022,
       0.021,
       0.024,
       0.024,
       0.027,
       0.029,
       0.03,
       0.034,
       0.033,
       0.033,
       0.035
      ],
      "tratteggio": true
     }
    ]
   },
   {
    "tipo": "profilo",
    "titolo": "Sofia (272 posti): è più pieno di notte che di giorno: 52% di notte, 31% di giorno",
    "unita": "",
    "nota": "8 giorni validi; linea piena feriale, tratteggiata weekend.",
    "serie": [
     {
      "label": "giorno feriale",
      "valori": [
       0.516,
       0.517,
       0.519,
       0.519,
       0.519,
       0.51,
       0.488,
       0.44,
       0.4,
       0.36,
       0.31,
       0.292,
       0.3,
       0.308,
       0.309,
       0.31,
       0.31,
       0.338,
       0.378,
       0.42,
       0.449,
       0.465,
       0.487,
       0.5
      ]
     },
     {
      "label": "weekend",
      "valori": [
       0.507,
       0.51,
       0.512,
       0.514,
       0.516,
       0.513,
       0.504,
       0.489,
       0.471,
       0.44,
       0.403,
       0.385,
       0.394,
       0.396,
       0.396,
       0.393,
       0.394,
       0.395,
       0.407,
       0.416,
       0.43,
       0.436,
       0.446,
       0.495
      ],
      "tratteggio": true
     }
    ]
   },
   {
    "tipo": "pila",
    "titolo": "Fermate importanti e posti adatti",
    "unita": "fermate",
    "nota": "Posti adatti entro 400 m a piedi confrontati con le auto da fermare (auto che passano × 5,8%).",
    "voci": [
     {
      "label": "nessun parcheggio",
      "valore": 68,
      "tono": "rosso"
     },
     {
      "label": "posti insufficienti",
      "valore": 111,
      "tono": "arancio"
     },
     {
      "label": "posti sufficienti",
      "valore": 95,
      "tono": "verde"
     },
     {
      "label": "poche auto da fermare",
      "valore": 0
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "I punti dove mancano più posti",
    "unita": "posti",
    "nota": "Posti che mancano = auto da fermare − posti adatti vicini.",
    "voci": [
     {
      "label": "1. Santa Rita",
      "valore": 450,
      "tono": "rosso"
     },
     {
      "label": "2. Metro Massaua",
      "valore": 350,
      "tono": "rosso"
     },
     {
      "label": "3. Ponte Cavalieri Templari",
      "valore": 350,
      "tono": "rosso"
     },
     {
      "label": "4. Regina Margherita",
      "valore": 350,
      "tono": "rosso"
     },
     {
      "label": "5. Pasini",
      "valore": 250,
      "tono": "rosso"
     },
     {
      "label": "6. Leonardo Da Vinci",
      "valore": 200,
      "tono": "rosso"
     },
     {
      "label": "7. Drosso Cap",
      "valore": 200,
      "tono": "rosso"
     },
     {
      "label": "8. Stura Lazio",
      "valore": 200,
      "tono": "rosso"
     },
     {
      "label": "9. Marsè",
      "valore": 150,
      "tono": "rosso"
     },
     {
      "label": "10. Derna Est",
      "valore": 100,
      "tono": "rosso"
     }
    ]
   }
  ],
  "verifica": [
   {
    "nome": "Caio Mario",
    "fatto": "il valore non cambia (1%): forse il contatore è fermo; auto in entrata sulla strada accanto: circa 3.900",
    "esito": "non si può dire: il contatore sembra fermo"
   },
   {
    "nome": "Fermi",
    "fatto": "non trasmette il riempimento; auto in entrata sulla strada accanto: circa 1.000",
    "esito": "non si può dire: non trasmette il riempimento"
   },
   {
    "nome": "Sofia",
    "fatto": "è più pieno di notte che di giorno: 52% di notte, 31% di giorno; auto in entrata sulla strada accanto: circa 3.100",
    "esito": "da capire: accanto passano molte auto in entrata ma è poco usato (prezzo? posizione? collegamento?)"
   },
   {
    "nome": "Stura",
    "fatto": "sempre quasi pieno: 80% di notte, 91% di giorno; auto in entrata sulla strada accanto: circa 7.600",
    "esito": "coerente: pieno, su una strada con molte auto in entrata"
   },
   {
    "nome": "Venchi Unica",
    "fatto": "sempre intorno al 55%; auto in entrata sulla strada accanto: circa 7.100",
    "esito": "non si può dire: riempimento a metà"
   }
  ],
  "affidabilita": [
   {
    "voce": "Parcheggi trovati nei dati aperti",
    "valore": "5.205"
   },
   {
    "voce": "Aperti → fuori dal centro → con almeno 20 posti → adatti (non di destinazione)",
    "valore": "3.431 → 3.208 → 2.006 → 1.874"
   },
   {
    "voce": "Posti nei parcheggi adatti (dichiarati o stimati a 25 m² a posto)",
    "valore": "157.103"
   },
   {
    "voce": "Auto che entrano a Torino al mattino (solo conducenti)",
    "valore": "87.162"
   },
   {
    "voce": "Quota di chi già oggi lascia l'auto per un mezzo pubblico",
    "valore": "5,8% (64 interviste)"
   },
   {
    "voce": "Auto che passano accanto alle fermate",
    "valore": "modello del traffico (percorso più veloce, senza code): solo ordine di grandezza"
   },
   {
    "voce": "Quota di posti in mappa con riempimento misurato",
    "valore": "26,9%"
   },
   {
    "voce": "Giorni feriali di riempimento",
    "valore": "15/10, 16/10, 19/10, 20/10, 21/10, 22/10"
   },
   {
    "voce": "Non sappiamo",
    "valore": "se i parcheggi senza misura (es. Fermi e i gratuiti) sono pieni; i parcheggi che non sono in OpenStreetMap; i treni"
   }
  ],
  "immagini": [],
  "metodo": [
   "Fermate importanti: fra i luoghi di fermata della Città metropolitana, quelle fuori dal centro, con metro, stazione o capolinea oppure almeno 10 corse all'ora nelle ore dei pendolari, e con almeno 1.000 auto in entrata che passano accanto (centro = i quartieri centrali). Regola fissa; il punteggio (importanza della strada, corse, auto, metro o stazione, pesi uguali) serve solo per l'ordine.",
   "Auto in entrata che passano accanto: le auto che entrano a Torino al mattino (indagine sugli spostamenti 2022) fatte «guidare» sul percorso più veloce della rete stradale; si legge la strada più trafficata entro 100 m.",
   "Auto da fermare = auto che passano × 5,8% (chi già oggi lascia l'auto per un mezzo pubblico).",
   "Posti adatti: parcheggi aperti fuori dal centro, con almeno 20 posti, non di ospedali, università o centri commerciali, entro 400 m a piedi (linea d'aria × 1,3); posti dichiarati o stimati con 25 m² a posto.",
   "Punti prioritari (fino a 20, almeno 50 posti mancanti, uno per asse d'ingresso, oltre 3 km dal centro): fermate senza posti bastanti raggruppate entro 1 km, in ordine di posti che mancano."
  ],
  "parametri": [
   [
    "Centro escluso",
    "i quartieri centrali (fermate e parcheggi)"
   ],
   [
    "Fermate importanti",
    "metro, stazione o capolinea o almeno 10 corse all'ora, e almeno 1.000 auto che passano (274 su 3.898)"
   ],
   [
    "Distanza",
    "400 m a piedi (linea d'aria × 1,3)"
   ],
   [
    "Auto da fermare",
    "auto che passano × 5,8%"
   ],
   [
    "Posti stimati",
    "25 m² a posto (±30%)"
   ],
   [
    "Giorni feriali di riempimento",
    "15/10, 16/10, 19/10, 20/10, 21/10 e 22/10"
   ]
  ],
  "limiti": [
   "Auto che passano: modello del traffico (percorso più veloce, senza code), stima debole: solo ordine di grandezza. Le stesse auto passano davanti a più fermate dello stesso corso.",
   "Riempimento misurato su soli 6 giorni feriali e solo dove il 5T lo trasmette Fermi e i parcheggi gratuiti non sono misurati.",
   "Quota di chi lascia l'auto: indagine sugli spostamenti 2022, poche interviste.",
   "Controllo con i sensori 5T del mattino: il modello mette le strade d'ingresso in un ordine simile solo in parte (ρ = 0,46 su 24 luoghi); sottostima gli ingressi da nord-ovest.",
   "Parcheggi da OpenStreetMap incompleti; posti spesso stimati dalla superficie (±30%).",
   "Distanza a piedi stimata (linea d'aria × 1,3). Treni non considerati."
  ],
  "criteri": [
   {
    "nome": "Fermate importanti",
    "valore": "fuori dal centro, con metro, stazione o capolinea oppure almeno 10 corse all'ora nelle ore dei pendolari, e almeno 1.000 auto in entrata che passano accanto (274 fermate)",
    "perche": "un parcheggio per lasciare l'auto serve dove passa un mezzo frequente e passano molte auto in entrata",
    "effetto": "con N 10, M 500: 347 fermate; con N 10, M 2.000: 201 fermate; con N 15, M 1.000: 136 fermate"
   },
   {
    "nome": "Centro escluso",
    "valore": "quartieri Q001-Q009 (Centro, San Salvario, Crocetta, San Paolo, Cenisia, San Donato, Aurora, Vanchiglia, Nizza Millefonti)",
    "perche": "un parcheggio per lasciare l'auto serve prima di entrare nella città densa, non a due passi dalla destinazione",
    "effetto": "vale sia per le fermate sia per i parcheggi"
   },
   {
    "nome": "Parcheggi contati",
    "valore": "solo quelli adatti: aperti, fuori dal centro, almeno 20 posti, non di ospedali, università o centri commerciali (1.874)",
    "perche": "i posti di chi arriva a destinazione non servono a chi vuole lasciare l'auto prima",
    "effetto": "contando anche i parcheggi di destinazione: 174 fermate senza posti bastanti (invece di 179)"
   },
   {
    "nome": "Distanza",
    "valore": "400 m a piedi (linea d'aria × 1.3)",
    "perche": "chi lascia l'auto accetta di solito una camminata di qualche minuto",
    "effetto": "a 300 m: 209 fermate senza posti bastanti; a 500 m: 147 (a 400 m: 179)"
   },
   {
    "nome": "Auto da fermare",
    "valore": "auto in entrata che passano accanto × 5,8% (chi già oggi lascia l'auto per un mezzo pubblico)",
    "perche": "i posti servono se ci sono auto da fermare: niente soglia fissa di posti",
    "effetto": "con metà quota: 135 fermate senza posti bastanti; con quota doppia: 212"
   },
   {
    "nome": "Poche auto da fermare",
    "valore": "meno di 20 auto da fermare al mattino",
    "perche": "lì un parcheggio per lasciare l'auto non serve",
    "effetto": "0 fermate importanti in questa classe"
   },
   {
    "nome": "Aree",
    "valore": "celle di circa 2 km²; Critica ≥ 60%, Scarsa 30-59%, Buona < 30%; almeno 5 fermate, se no «Pochi dati»",
    "perche": "con una o due fermate la percentuale è 0% o 100% per caso",
    "effetto": "soglie 50/25: Critica 14, Scarsa 4, Buona 2, Pochi dati 42; soglie 66/33: Critica 10, Scarsa 7, Buona 3, Pochi dati 42"
   },
   {
    "nome": "Punti prioritari",
    "valore": "fino a 20: fermate senza posti bastanti raggruppate entro 1 km, in ordine di posti che mancano (almeno 50); uno per asse d'ingresso (niente punti a meno di 2 km, né sulla stessa strada a meno di 5 km); almeno 3 km da Piazza Castello",
    "perche": "risponde a «dove metterne uno o ingrandirlo»; due punti sullo stesso asse contano le stesse auto; vicino al centro si risparmia poca strada",
    "effetto": "candidati: parcheggi adatti con almeno 100 posti entro 600 m a piedi; scartati 38 gruppi su 53"
   },
   {
    "nome": "Riempimento",
    "valore": "misurato dal 5T dove c'è (6 giorni feriali, ore 10-16); pieno ≥ 85%",
    "perche": "un parcheggio pieno non serve",
    "effetto": "colora i parcheggi e mostra i profili; non cambia le classi delle fermate"
   }
  ],
  "mappa": {
   "id": "interscambio",
   "tema": "Parcheggi per lasciare l'auto",
   "nota": "Due domande nella mappa, nel menu «Cosa vedere»: dove ci sono parcheggi e dove servirebbe di più un parcheggio."
  },
  "fonti": [
   "docs/en/METHODS.md",
   "scripts/81_auto_di_passaggio.py",
   "scripts/82_parcheggi_adatti.py",
   "scripts/83_fermate_importanti.py",
   "scripts/84_risultato6_parcheggi.py",
   "data/processed/risultato6_v2/mappa_r6.json"
  ],
  "generato": "2026-10-26T14:06:29+00:00",
  "avviso": [
   "Riempimento dei parcheggi misurato dai sensori 5T su pochi giorni; auto e posti che mancano calcolati su dati veri, non misurati."
  ],
  "in_english": [
   "Question: where are park-and-ride spaces missing for the cars that enter Turin every morning, next to an important public transport stop outside the city centre?",
   "Existing park-and-ride car parks of the City: 4 of 5 report their occupancy; full during the day: 1 (measured, only a few days of data).",
   "About 87,200 cars enter Turin every morning (2022 travel survey) and 5.8% of these drivers already continue by public transport. 179 of 274 important stops outside the centre lack enough suitable parking within 400 m on foot for the cars passing by.",
   "Important stops: outside the centre, with a metro, train station or terminus or at least 10 departures per hour at commuting times, and at least 1,000 cars entering the city passing by.",
   "Limits: car flows come from a simple traffic model (order of magnitude only); occupancy is measured on few days and only where the city's 5T system reports it; trains are not included.",
   "Check against the 5T morning sensors: the model ranks the entry roads in a similar order only in part (rho = 0.46 over 24 places); it underestimates the entries from the north-west."
  ],
  "scenari": [
   {
    "nome": "Oggi",
    "numeri": [
     {
      "label": "Fermate importanti fuori dal centro",
      "prima": null,
      "dopo": 274,
      "unita": "fermate"
     },
     {
      "label": "Senza posti bastanti",
      "prima": null,
      "dopo": 179,
      "unita": "fermate"
     },
     {
      "label": "Senza nessun parcheggio adatto",
      "prima": null,
      "dopo": 68,
      "unita": "fermate"
     }
    ],
    "nota": "Stime: auto dal modello del traffico, posti da OpenStreetMap, Comune e 5T; riempimento da 5T."
   }
  ],
  "forma": {
   "tipo_dato": "Tipo di dato: calcolato da dati veri e in parte misurato, su pochi giorni di dati.",
   "titolo": "Circa 2 fermate importanti su 3 non hanno abbastanza posti per lasciare l'auto",
   "domanda": "Chi arriva in auto da fuori trova dove lasciarla vicino a una fermata importante, per proseguire coi mezzi?",
   "numero": {
    "valore": 179,
    "unita": "",
    "testo": "fermate importanti su 274 non hanno posti bastanti a 400 metri a piedi",
    "breve": "fermate importanti senza posti per l'auto"
   },
   "principale": {
    "tipo": "barre",
    "titolo": "I 12 punti d'ingresso, per bisogno di parcheggio",
    "unita": "posti",
    "nota": "Posti che mancano accanto a ogni barra: un ordine di grandezza. Il colore è il bisogno, a terzi.",
    "legenda": [
     {
      "tono": "rosso",
      "label": "bisogno alto"
     },
     {
      "tono": "arancio",
      "label": "bisogno medio"
     },
     {
      "tono": "giallo",
      "label": "bisogno basso"
     }
    ],
    "voci": [
     {
      "label": "Santa Rita",
      "valore": 450,
      "tono": "rosso",
      "testo": "~450"
     },
     {
      "label": "Parella (Metro Massaua)",
      "valore": 350,
      "tono": "rosso",
      "testo": "~350"
     },
     {
      "label": "Moncalieri (Ponte Cavalieri Templari)",
      "valore": 350,
      "tono": "rosso",
      "testo": "~350"
     },
     {
      "label": "Parella (Regina Margherita)",
      "valore": 350,
      "tono": "rosso",
      "testo": "~350"
     },
     {
      "label": "Madonna del Pilone",
      "valore": 250,
      "tono": "arancio",
      "testo": "~250"
     },
     {
      "label": "Grugliasco",
      "valore": 200,
      "tono": "arancio",
      "testo": "~200"
     },
     {
      "label": "Mirafiori Sud",
      "valore": 200,
      "tono": "arancio",
      "testo": "~200"
     },
     {
      "label": "Regio Parco",
      "valore": 200,
      "tono": "arancio",
      "testo": "~200"
     },
     {
      "label": "Moncalieri (Marsè)",
      "valore": 150,
      "tono": "giallo",
      "testo": "~150"
     },
     {
      "label": "Falchera",
      "valore": 100,
      "tono": "giallo",
      "testo": "~100"
     },
     {
      "label": "Beinasco",
      "valore": 80,
      "tono": "giallo",
      "testo": "~80"
     },
     {
      "label": "Borgo Po e Cavoretto",
      "valore": 60,
      "tono": "giallo",
      "testo": "~60"
     }
    ]
   },
   "punti": [
    "68 fermate importanti non hanno nessun parcheggio vicino, 111 troppo pochi.",
    "Il primo dei 12 punti d'ingresso dove servono posti è Santa Rita: ne mancano ~450.",
    "In 1–5 punti su 12, lasciata l'auto, il bus arriva in centro in al più 1,5 volte il tempo dell'auto."
   ],
   "altri": [
    {
     "tipo": "gara",
     "titolo": "La gara: bus e auto verso Piazza Castello, alle 8 di un feriale",
     "nota": "Bus e auto partono insieme da ogni parcheggio, uno dopo l'altro. L'auto ha un tempo con la forbice del controllo, parcheggio compreso.",
     "luoghi": [
      {
       "nome": "Santa Rita",
       "gruppo": "Punti prioritari",
       "bus": 38.7,
       "auto_min": 19.6,
       "auto_max": 24.1,
       "giudizio": "coi mezzi 1,6–2 volte il tempo dell'auto"
      },
      {
       "nome": "Parella (Metro Massaua)",
       "gruppo": "Punti prioritari",
       "bus": 27.3,
       "auto_min": 20.3,
       "auto_max": 25.0,
       "giudizio": "coi mezzi 1,1–1,3 volte il tempo dell'auto"
      },
      {
       "nome": "Moncalieri (Ponte Cavalieri Templari)",
       "gruppo": "Punti prioritari",
       "bus": 54.2,
       "auto_min": 23.1,
       "auto_max": 28.7,
       "giudizio": "coi mezzi 1,9–2,4 volte il tempo dell'auto"
      },
      {
       "nome": "Parella (Regina Margherita)",
       "gruppo": "Punti prioritari",
       "bus": 33.5,
       "auto_min": 18.0,
       "auto_max": 22.0,
       "giudizio": "coi mezzi 1,5–1,9 volte il tempo dell'auto"
      },
      {
       "nome": "Madonna del Pilone",
       "gruppo": "Punti prioritari",
       "bus": 30.4,
       "auto_min": 17.5,
       "auto_max": 21.3,
       "giudizio": "coi mezzi 1,4–1,7 volte il tempo dell'auto"
      },
      {
       "nome": "Grugliasco",
       "gruppo": "Punti prioritari",
       "bus": 62.5,
       "auto_min": 29.7,
       "auto_max": 37.3,
       "giudizio": "coi mezzi 1,7–2,1 volte il tempo dell'auto"
      },
      {
       "nome": "Mirafiori Sud",
       "gruppo": "Punti prioritari",
       "bus": 45.9,
       "auto_min": 25.4,
       "auto_max": 31.7,
       "giudizio": "coi mezzi 1,4–1,8 volte il tempo dell'auto"
      },
      {
       "nome": "Regio Parco",
       "gruppo": "Punti prioritari",
       "bus": 39.7,
       "auto_min": 21.4,
       "auto_max": 26.4,
       "giudizio": "coi mezzi 1,5–1,9 volte il tempo dell'auto"
      },
      {
       "nome": "Moncalieri (Marsè)",
       "gruppo": "Punti prioritari",
       "bus": 64.5,
       "auto_min": 29.5,
       "auto_max": 37.0,
       "giudizio": "coi mezzi 1,7–2,2 volte il tempo dell'auto"
      },
      {
       "nome": "Falchera",
       "gruppo": "Punti prioritari",
       "bus": 36.6,
       "auto_min": 20.3,
       "auto_max": 25.0,
       "giudizio": "coi mezzi 1,5–1,8 volte il tempo dell'auto"
      },
      {
       "nome": "Beinasco",
       "gruppo": "Punti prioritari",
       "bus": 52.1,
       "auto_min": 29.8,
       "auto_max": 37.4,
       "giudizio": "coi mezzi 1,4–1,8 volte il tempo dell'auto"
      },
      {
       "nome": "Borgo Po e Cavoretto",
       "gruppo": "Punti prioritari",
       "bus": 35.6,
       "auto_min": 16.7,
       "auto_max": 20.3,
       "giudizio": "coi mezzi 1,8–2,1 volte il tempo dell'auto"
      }
     ],
     "scelto": 0
    },
    {
     "tipo": "barre",
     "titolo": "I parcheggi di scambio che ci sono già: quanto sono pieni e quanto ci mette il bus al centro",
     "unita": "minuti",
     "nota": "Barra = minuti coi mezzi pubblici fino a Piazza Castello alle 8. A destra il tempo in auto, parcheggio compreso (traffico tipico), e quanto è pieno il parcheggio di giorno.",
     "voci": [
      {
       "label": "Stura",
       "valore": 42,
       "testo": "42 contro 27–34 in auto · pieno di giorno"
      },
      {
       "label": "Venchi Unica",
       "valore": 30,
       "testo": "30 contro 22–28 in auto · a metà"
      },
      {
       "label": "Caio Mario",
       "valore": 41,
       "testo": "41 contro 23–29 in auto · con posti liberi"
      },
      {
       "label": "Fermi",
       "valore": 34,
       "testo": "34 contro 26–33 in auto · riempimento non noto"
      },
      {
       "label": "Sofia",
       "valore": 36,
       "testo": "36 contro 20–25 in auto · con posti liberi"
      }
     ]
    }
   ],
   "calcolo": [
    "Fermate importanti: fuori dal centro, con metro, stazione o capolinea oppure 10 corse all'ora, e almeno 1.000 auto che passano.",
    "Le auto in entrata vengono dall'indagine sugli spostamenti 2022, assegnate al percorso più veloce.",
    "Auto da fermare: auto che passano per il 5,8% che già oggi lascia l'auto. Posti: parcheggi adatti entro 400 metri.",
    "Punti prioritari: fermate senza posti bastanti raggruppate entro 1 km, uno per asse d'ingresso. Fermate di riferimento: Santa Rita, Metro Massaua, Ponte Cavalieri Templari, Regina Margherita, Pasini, Leonardo Da Vinci. Drosso Cap, Stura Lazio, Marsè, Derna Est, Ferrara, Zara.",
    "Bus contro auto: minuti coi mezzi (corretti con le misure) verso Piazza Castello alle otto del mattino. Auto: stima aperta più 5 minuti, e la stessa corretta col fattore 1,3 del controllo con TomTom.",
    "Pareggio: minuti di parcheggio che rendono l'auto lenta quanto il bus, da 20 a 24 (mediana dei 12 punti).",
    "La classe si dà solo se è la stessa con la stima aperta e con quella corretta. Lo è in 8 punti su 12; negli altri dipende dal traffico."
   ],
   "criteri": [
    [
     "Fermate importanti",
     "metro, stazione o capolinea oppure 10 corse all'ora, e almeno 1.000 auto che passano"
    ],
    [
     "Distanza a piedi",
     "400 metri"
    ],
    [
     "Auto da fermare",
     "auto che passano × 5,8%"
    ],
    [
     "Periodo del riempimento dei parcheggi",
     "dal 15/10/2026 al 22/10/2026"
    ],
    [
     "Bus contro auto",
     "verso Piazza Castello alle 8; auto: stima aperta (fattore mediano 2) + 5 minuti, e la stessa corretta col controllo (× 1,3 sulla guida)"
    ]
   ],
   "limiti": [
    "Le auto che passano vengono da un modello del traffico. I posti sono spesso stimati: quelli che mancano sono un ordine di grandezza. Con metà o doppio di chi lascia l'auto, le fermate senza posti bastanti vanno da 135 a 212 su 274.",
    "I tempi coi mezzi sono solo GTT, senza treni.",
    "Tempi in auto da un modello aperto, non misurati sul singolo viaggio. Il controllo con TomTom su 20 percorsi li trova ottimistici: per questo c'è una forbice.",
    "Il costo del parcheggio non è nel calcolo: pesa come minuti in più. Si guarda un solo punto per luogo e una sola destinazione."
   ],
   "mappa": {
    "id": "interscambio",
    "nota": "Due domande nella mappa, nel menu «Cosa vedere»: dove ci sono parcheggi e dove servirebbe di più un parcheggio."
   },
   "fonti": [
    "GTT (orari ufficiali e posizioni dei mezzi)",
    "Comune di Torino (parcheggi)",
    "5T (sensori del traffico)",
    "Agenzia della mobilità piemontese (indagine sugli spostamenti 2022)",
    "OpenStreetMap",
    "TomTom (controllo dei tempi in auto su 20 percorsi)"
   ],
   "titolo_breve": "Dove lasciare l'auto",
   "anima": {
    "tipo": "fermate",
    "contorno": {
     "d": "M879 130l-33 35l-2 -35l22 -12l13 12zM452 11l123 41l18 -10l2 11l11 14l35 -6l42 -20l3 -17l6 -5l25 -3l34 9l-9 37l9 34l48 23l13 3l-8 28l46 93l43 29l-7 39l-27 21l-21 13l28 44l18 20l30 12l64 3l-8 11l3 8l10 6l12 -1l5 4l-90 145l-79 95l-39 49l-51 48l-40 17l-37 36l-129 15l-120 41l-18 59l-73 6l-70 -8l-19 1l-59 -16l-11 5l-87 -31l-14 -16l8 -25l8 -1l36 8l35 -80l-30 11l-67 -45l-44 -39l-10 -14l13 -18l32 -4l128 80l25 -39l45 -134l-1 -15l-33 5l-57 -11l9 -32l9 -4l6 -11l-20 -24l-25 -6l61 -129l13 -59l-19 -21l-12 -51l13 -8l30 2l12 -4l1 -39l122 13l40 -5l0 -15l-7 -11l-3 -50l9 -10l12 -31l-6 -29l2 -15l38 -36l7 -2l8 11z",
     "vb": [
      -40,
      -40,
      1080,
      1043
     ]
    },
    "punti": [
     [
      186,
      477,
      0,
      365
     ],
     [
      216,
      475,
      1,
      335
     ],
     [
      123,
      481,
      1,
      427
     ],
     [
      687,
      138,
      0,
      387
     ],
     [
      261,
      473,
      2,
      290
     ],
     [
      295,
      471,
      2,
      257
     ],
     [
      690,
      150,
      0,
      377
     ],
     [
      692,
      135,
      0,
      392
     ],
     [
      445,
      255,
      1,
      267
     ],
     [
      455,
      252,
      1,
      266
     ],
     [
      442,
      258,
      1,
      265
     ],
     [
      426,
      895,
      1,
      414
     ],
     [
      546,
      301,
      1,
      199
     ],
     [
      479,
      1008,
      0,
      513
     ],
     [
      369,
      154,
      0,
      390
     ],
     [
      342,
      1065,
      0,
      602
     ],
     [
      339,
      1063,
      0,
      601
     ],
     [
      393,
      817,
      0,
      354
     ],
     [
      574,
      300,
      1,
      201
     ],
     [
      576,
      299,
      1,
      203
     ],
     [
      476,
      1024,
      1,
      529
     ],
     [
      69,
      465,
      0,
      482
     ],
     [
      1237,
      976,
      0,
      836
     ],
     [
      401,
      839,
      0,
      370
     ],
     [
      241,
      917,
      1,
      519
     ],
     [
      346,
      682,
      2,
      273
     ],
     [
      257,
      746,
      2,
      383
     ],
     [
      680,
      145,
      0,
      378
     ],
     [
      356,
      671,
      2,
      259
     ],
     [
      268,
      738,
      1,
      369
     ],
     [
      175,
      791,
      1,
      475
     ],
     [
      221,
      475,
      1,
      330
     ],
     [
      290,
      854,
      1,
      439
     ],
     [
      136,
      480,
      1,
      414
     ],
     [
      185,
      787,
      2,
      464
     ],
     [
      259,
      896,
      1,
      491
     ],
     [
      245,
      754,
      1,
      397
     ],
     [
      264,
      887,
      2,
      481
     ],
     [
      279,
      871,
      2,
      459
     ],
     [
      248,
      754,
      1,
      395
     ],
     [
      592,
      599,
      2,
      108
     ],
     [
      270,
      882,
      2,
      474
     ],
     [
      204,
      782,
      2,
      446
     ],
     [
      253,
      900,
      1,
      498
     ],
     [
      200,
      782,
      2,
      449
     ],
     [
      236,
      762,
      1,
      409
     ],
     [
      240,
      648,
      1,
      344
     ],
     [
      727,
      514,
      1,
      178
     ],
     [
      299,
      840,
      1,
      423
     ],
     [
      233,
      762,
      1,
      411
     ],
     [
      743,
      510,
      1,
      193
     ],
     [
      325,
      699,
      1,
      300
     ],
     [
      311,
      828,
      1,
      406
     ],
     [
      269,
      652,
      1,
      319
     ],
     [
      375,
      748,
      0,
      304
     ],
     [
      337,
      685,
      2,
      282
     ],
     [
      10,
      488,
      1,
      540
     ],
     [
      784,
      403,
      1,
      253
     ],
     [
      390,
      729,
      0,
      279
     ],
     [
      345,
      687,
      2,
      277
     ],
     [
      334,
      799,
      0,
      369
     ],
     [
      313,
      825,
      0,
      402
     ],
     [
      353,
      776,
      1,
      339
     ],
     [
      331,
      804,
      0,
      375
     ],
     [
      293,
      721,
      1,
      339
     ],
     [
      706,
      332,
      0,
      229
     ],
     [
      1049,
      -566,
      0,
      1177
     ],
     [
      349,
      780,
      1,
      345
     ],
     [
      207,
      476,
      0,
      344
     ],
     [
      47,
      638,
      2,
      522
     ],
     [
      414,
      698,
      1,
      240
     ],
     [
      320,
      816,
      0,
      391
     ],
     [
      779,
      426,
      1,
      241
     ],
     [
      273,
      876,
      2,
      467
     ],
     [
      794,
      390,
      1,
      268
     ],
     [
      159,
      480,
      1,
      392
     ],
     [
      156,
      478,
      1,
      395
     ],
     [
      -57,
      492,
      2,
      607
     ],
     [
      260,
      901,
      1,
      495
     ],
     [
      647,
      229,
      2,
      288
     ],
     [
      672,
      177,
      1,
      345
     ],
     [
      632,
      261,
      0,
      253
     ],
     [
      663,
      197,
      0,
      323
     ],
     [
      223,
      647,
      1,
      359
     ],
     [
      256,
      650,
      1,
      330
     ],
     [
      268,
      650,
      1,
      319
     ],
     [
      399,
      717,
      2,
      264
     ],
     [
      856,
      357,
      1,
      338
     ],
     [
      507,
      999,
      1,
      501
     ],
     [
      722,
      316,
      0,
      252
     ],
     [
      674,
      534,
      2,
      129
     ],
     [
      95,
      482,
      1,
      455
     ],
     [
      553,
      300,
      1,
      200
     ],
     [
      432,
      675,
      2,
      211
     ],
     [
      607,
      268,
      0,
      239
     ],
     [
      324,
      812,
      0,
      385
     ],
     [
      393,
      348,
      2,
      219
     ],
     [
      380,
      377,
      2,
      210
     ],
     [
      936,
      265,
      0,
      452
     ],
     [
      429,
      679,
      2,
      216
     ],
     [
      778,
      469,
      2,
      230
     ],
     [
      532,
      729,
      1,
      230
     ],
     [
      315,
      828,
      1,
      403
     ],
     [
      927,
      309,
      1,
      423
     ],
     [
      516,
      367,
      1,
      137
     ],
     [
      -23,
      490,
      1,
      573
     ],
     [
      367,
      758,
      0,
      316
     ],
     [
      -19,
      489,
      1,
      569
     ],
     [
      620,
      561,
      1,
      93
     ],
     [
      404,
      716,
      2,
      261
     ],
     [
      510,
      359,
      1,
      147
     ],
     [
      294,
      841,
      1,
      426
     ],
     [
      365,
      760,
      0,
      319
     ],
     [
      287,
      718,
      1,
      342
     ],
     [
      750,
      286,
      2,
      293
     ],
     [
      292,
      602,
      2,
      277
     ],
     [
      284,
      660,
      1,
      310
     ],
     [
      333,
      473,
      1,
      219
     ],
     [
      307,
      515,
      1,
      243
     ],
     [
      337,
      464,
      1,
      216
     ],
     [
      281,
      656,
      1,
      311
     ],
     [
      402,
      713,
      2,
      259
     ],
     [
      -175,
      500,
      0,
      725
     ],
     [
      296,
      666,
      1,
      303
     ],
     [
      766,
      244,
      0,
      335
     ],
     [
      711,
      333,
      0,
      232
     ],
     [
      623,
      282,
      0,
      230
     ],
     [
      303,
      824,
      1,
      407
     ],
     [
      621,
      286,
      0,
      225
     ],
     [
      630,
      276,
      1,
      238
     ],
     [
      700,
      342,
      0,
      218
     ],
     [
      600,
      330,
      1,
      177
     ],
     [
      324,
      679,
      2,
      288
     ],
     [
      -178,
      498,
      0,
      728
     ],
     [
      -150,
      496,
      0,
      700
     ],
     [
      289,
      679,
      2,
      316
     ],
     [
      283,
      501,
      2,
      267
     ],
     [
      513,
      356,
      0,
      149
     ],
     [
      99,
      818,
      0,
      552
     ],
     [
      111,
      814,
      0,
      540
     ],
     [
      288,
      700,
      1,
      330
     ],
     [
      482,
      999,
      0,
      504
     ],
     [
      591,
      352,
      1,
      154
     ],
     [
      -257,
      504,
      0,
      807
     ],
     [
      103,
      818,
      0,
      549
     ],
     [
      122,
      811,
      2,
      529
     ],
     [
      444,
      252,
      1,
      270
     ],
     [
      555,
      262,
      2,
      238
     ],
     [
      -95,
      495,
      1,
      645
     ],
     [
      725,
      1084,
      2,
      610
     ],
     [
      588,
      358,
      2,
      147
     ],
     [
      533,
      260,
      2,
      241
     ],
     [
      428,
      266,
      1,
      264
     ],
     [
      688,
      357,
      0,
      199
     ],
     [
      422,
      290,
      2,
      246
     ],
     [
      284,
      56,
      0,
      518
     ],
     [
      312,
      806,
      0,
      388
     ],
     [
      411,
      310,
      2,
      235
     ],
     [
      539,
      366,
      0,
      134
     ],
     [
      -99,
      493,
      1,
      649
     ],
     [
      421,
      287,
      2,
      249
     ],
     [
      718,
      322,
      0,
      245
     ],
     [
      431,
      264,
      1,
      264
     ],
     [
      381,
      668,
      0,
      238
     ],
     [
      691,
      355,
      0,
      202
     ],
     [
      493,
      994,
      0,
      497
     ],
     [
      315,
      803,
      0,
      383
     ],
     [
      530,
      262,
      2,
      239
     ],
     [
      371,
      396,
      2,
      207
     ],
     [
      313,
      674,
      2,
      294
     ],
     [
      434,
      249,
      1,
      277
     ],
     [
      51,
      460,
      0,
      501
     ],
     [
      311,
      671,
      2,
      294
     ],
     [
      299,
      665,
      1,
      300
     ],
     [
      -221,
      501,
      0,
      771
     ],
     [
      302,
      546,
      2,
      252
     ],
     [
      -196,
      499,
      0,
      746
     ],
     [
      609,
      312,
      1,
      197
     ],
     [
      984,
      257,
      0,
      497
     ],
     [
      290,
      632,
      1,
      292
     ],
     [
      709,
      325,
      0,
      236
     ],
     [
      748,
      294,
      2,
      286
     ],
     [
      -224,
      503,
      0,
      774
     ],
     [
      788,
      288,
      2,
      319
     ],
     [
      813,
      284,
      2,
      340
     ],
     [
      360,
      719,
      0,
      290
     ],
     [
      575,
      378,
      1,
      125
     ],
     [
      619,
      304,
      0,
      208
     ],
     [
      598,
      335,
      1,
      172
     ],
     [
      611,
      307,
      1,
      202
     ],
     [
      1029,
      199,
      0,
      566
     ],
     [
      593,
      391,
      1,
      117
     ],
     [
      436,
      261,
      1,
      265
     ],
     [
      310,
      510,
      1,
      240
     ],
     [
      580,
      375,
      1,
      129
     ],
     [
      345,
      249,
      0,
      324
     ],
     [
      -151,
      501,
      0,
      701
     ],
     [
      576,
      384,
      2,
      119
     ],
     [
      265,
      645,
      1,
      320
     ],
     [
      287,
      774,
      0,
      380
     ],
     [
      766,
      291,
      2,
      301
     ],
     [
      600,
      270,
      2,
      235
     ],
     [
      293,
      571,
      2,
      267
     ],
     [
      614,
      410,
      0,
      110
     ],
     [
      651,
      387,
      0,
      152
     ],
     [
      428,
      675,
      1,
      213
     ],
     [
      296,
      566,
      2,
      262
     ],
     [
      677,
      370,
      1,
      182
     ],
     [
      247,
      761,
      1,
      400
     ],
     [
      667,
      377,
      1,
      170
     ],
     [
      266,
      628,
      2,
      312
     ],
     [
      626,
      435,
      1,
      100
     ],
     [
      423,
      214,
      1,
      313
     ],
     [
      442,
      891,
      1,
      406
     ],
     [
      412,
      205,
      0,
      326
     ],
     [
      522,
      365,
      0,
      138
     ],
     [
      391,
      714,
      1,
      267
     ],
     [
      411,
      953,
      0,
      474
     ],
     [
      562,
      371,
      0,
      130
     ],
     [
      442,
      692,
      0,
      220
     ],
     [
      -41,
      324,
      0,
      617
     ],
     [
      -16,
      321,
      1,
      594
     ],
     [
      387,
      177,
      2,
      362
     ],
     [
      374,
      946,
      0,
      479
     ],
     [
      423,
      230,
      2,
      298
     ],
     [
      234,
      551,
      2,
      320
     ],
     [
      403,
      980,
      1,
      502
     ],
     [
      419,
      201,
      0,
      326
     ],
     [
      353,
      1052,
      0,
      586
     ],
     [
      263,
      687,
      1,
      343
     ],
     [
      425,
      901,
      1,
      420
     ],
     [
      423,
      903,
      1,
      423
     ],
     [
      -93,
      327,
      0,
      666
     ],
     [
      -124,
      288,
      0,
      707
     ],
     [
      422,
      661,
      1,
      206
     ],
     [
      434,
      209,
      1,
      313
     ],
     [
      303,
      789,
      0,
      380
     ],
     [
      193,
      653,
      1,
      388
     ],
     [
      231,
      549,
      2,
      323
     ],
     [
      293,
      784,
      0,
      383
     ],
     [
      410,
      200,
      0,
      331
     ],
     [
      297,
      784,
      0,
      380
     ],
     [
      308,
      789,
      0,
      377
     ],
     [
      320,
      696,
      1,
      302
     ],
     [
      -160,
      269,
      0,
      747
     ],
     [
      507,
      348,
      0,
      158
     ],
     [
      379,
      833,
      2,
      374
     ],
     [
      373,
      852,
      2,
      394
     ],
     [
      381,
      837,
      2,
      377
     ],
     [
      486,
      262,
      1,
      246
     ],
     [
      518,
      255,
      2,
      247
     ],
     [
      362,
      908,
      1,
      449
     ],
     [
      153,
      527,
      0,
      398
     ],
     [
      69,
      552,
      0,
      484
     ],
     [
      92,
      552,
      1,
      461
     ],
     [
      50,
      547,
      0,
      502
     ],
     [
      338,
      167,
      1,
      395
     ],
     [
      1245,
      953,
      0,
      830
     ],
     [
      124,
      549,
      1,
      429
     ],
     [
      89,
      470,
      0,
      462
     ],
     [
      527,
      286,
      2,
      215
     ],
     [
      15,
      539,
      0,
      536
     ],
     [
      296,
      93,
      1,
      480
     ],
     [
      890,
      96,
      0,
      528
     ],
     [
      295,
      548,
      2,
      259
     ],
     [
      288,
      548,
      2,
      266
     ],
     [
      274,
      549,
      2,
      280
     ],
     [
      279,
      549,
      2,
      275
     ],
     [
      251,
      550,
      1,
      303
     ],
     [
      485,
      321,
      0,
      190
     ],
     [
      258,
      551,
      1,
      296
     ],
     [
      225,
      548,
      2,
      329
     ],
     [
      454,
      1043,
      0,
      551
     ],
     [
      64,
      463,
      0,
      487
     ]
    ],
    "prioritari": [
     [
      331,
      683
     ],
     [
      219,
      475
     ],
     [
      492,
      1012
     ],
     [
      381,
      374
     ],
     [
      778,
      469
     ],
     [
      47,
      638
     ],
     [
      262,
      891
     ],
     [
      755,
      291
     ],
     [
      725,
      1084
     ],
     [
      615,
      273
     ],
     [
      122,
      811
     ],
     [
      532,
      729
     ]
    ],
    "legenda": [
     {
      "label": "posti bastanti",
      "n": 95,
      "tono": "verde"
     },
     {
      "label": "pochi posti",
      "n": 111,
      "tono": "giallo"
     },
     {
      "label": "nessun parcheggio",
      "n": 68,
      "tono": "rosso"
     }
    ],
    "didascalia": "Ogni punto è una fermata importante, in Torino e in cintura; la linea è il confine di Torino. I cerchi neri sono i 12 punti dove servirebbero di più nuovi posti."
   },
   "pareggio": {
    "a": 24,
    "b": 20
   }
  },
  "forma_en": {
   "tipo_dato": "Type of data: calculated from real data and partly measured, over few days of data.",
   "titolo": "About 2 in 3 important stops lack enough spaces to leave the car",
   "domanda": "Can people driving in from outside find a place to leave the car near an important stop, and continue by public transport?",
   "numero": {
    "valore": 179,
    "unita": "",
    "testo": "important stops out of 274 lack enough parking within 400 metres on foot",
    "breve": "important stops without parking spaces"
   },
   "principale": {
    "tipo": "barre",
    "titolo": "The 12 entry points, by need for parking",
    "unita": "spaces",
    "nota": "Missing spaces next to each bar: an order of magnitude. The colour is the need, in thirds.",
    "legenda": [
     {
      "tono": "rosso",
      "label": "high need"
     },
     {
      "tono": "arancio",
      "label": "medium need"
     },
     {
      "tono": "giallo",
      "label": "low need"
     }
    ],
    "voci": [
     {
      "label": "Santa Rita",
      "valore": 450,
      "tono": "rosso",
      "testo": "~450"
     },
     {
      "label": "Parella (Metro Massaua)",
      "valore": 350,
      "tono": "rosso",
      "testo": "~350"
     },
     {
      "label": "Moncalieri (Ponte Cavalieri Templari)",
      "valore": 350,
      "tono": "rosso",
      "testo": "~350"
     },
     {
      "label": "Parella (Regina Margherita)",
      "valore": 350,
      "tono": "rosso",
      "testo": "~350"
     },
     {
      "label": "Madonna del Pilone",
      "valore": 250,
      "tono": "arancio",
      "testo": "~250"
     },
     {
      "label": "Grugliasco",
      "valore": 200,
      "tono": "arancio",
      "testo": "~200"
     },
     {
      "label": "Mirafiori Sud",
      "valore": 200,
      "tono": "arancio",
      "testo": "~200"
     },
     {
      "label": "Regio Parco",
      "valore": 200,
      "tono": "arancio",
      "testo": "~200"
     },
     {
      "label": "Moncalieri (Marsè)",
      "valore": 150,
      "tono": "giallo",
      "testo": "~150"
     },
     {
      "label": "Falchera",
      "valore": 100,
      "tono": "giallo",
      "testo": "~100"
     },
     {
      "label": "Beinasco",
      "valore": 80,
      "tono": "giallo",
      "testo": "~80"
     },
     {
      "label": "Borgo Po e Cavoretto",
      "valore": 60,
      "tono": "giallo",
      "testo": "~60"
     }
    ]
   },
   "punti": [
    "68 important stops have no car park nearby, 111 have too few.",
    "The first of the 12 entry points where spaces are needed is Santa Rita: ~450 are missing.",
    "In 1–5 points out of 12, once the car is left, the bus reaches the centre in at most 1.5 times the car's time."
   ],
   "altri": [
    {
     "tipo": "gara",
     "titolo": "The race: bus and car to Piazza Castello, at 8 a.m. on a weekday",
     "nota": "Bus and car leave together from each car park, one after the other. The car has a time with the range from the check, parking included.",
     "luoghi": [
      {
       "nome": "Santa Rita",
       "gruppo": "Priority points",
       "bus": 38.7,
       "auto_min": 19.6,
       "auto_max": 24.1,
       "giudizio": "by public transport 1.6–2 times the car's time"
      },
      {
       "nome": "Parella (Metro Massaua)",
       "gruppo": "Priority points",
       "bus": 27.3,
       "auto_min": 20.3,
       "auto_max": 25.0,
       "giudizio": "by public transport 1.1–1.3 times the car's time"
      },
      {
       "nome": "Moncalieri (Ponte Cavalieri Templari)",
       "gruppo": "Priority points",
       "bus": 54.2,
       "auto_min": 23.1,
       "auto_max": 28.7,
       "giudizio": "by public transport 1.9–2.4 times the car's time"
      },
      {
       "nome": "Parella (Regina Margherita)",
       "gruppo": "Priority points",
       "bus": 33.5,
       "auto_min": 18.0,
       "auto_max": 22.0,
       "giudizio": "by public transport 1.5–1.9 times the car's time"
      },
      {
       "nome": "Madonna del Pilone",
       "gruppo": "Priority points",
       "bus": 30.4,
       "auto_min": 17.5,
       "auto_max": 21.3,
       "giudizio": "by public transport 1.4–1.7 times the car's time"
      },
      {
       "nome": "Grugliasco",
       "gruppo": "Priority points",
       "bus": 62.5,
       "auto_min": 29.7,
       "auto_max": 37.3,
       "giudizio": "by public transport 1.7–2.1 times the car's time"
      },
      {
       "nome": "Mirafiori Sud",
       "gruppo": "Priority points",
       "bus": 45.9,
       "auto_min": 25.4,
       "auto_max": 31.7,
       "giudizio": "by public transport 1.4–1.8 times the car's time"
      },
      {
       "nome": "Regio Parco",
       "gruppo": "Priority points",
       "bus": 39.7,
       "auto_min": 21.4,
       "auto_max": 26.4,
       "giudizio": "by public transport 1.5–1.9 times the car's time"
      },
      {
       "nome": "Moncalieri (Marsè)",
       "gruppo": "Priority points",
       "bus": 64.5,
       "auto_min": 29.5,
       "auto_max": 37.0,
       "giudizio": "by public transport 1.7–2.2 times the car's time"
      },
      {
       "nome": "Falchera",
       "gruppo": "Priority points",
       "bus": 36.6,
       "auto_min": 20.3,
       "auto_max": 25.0,
       "giudizio": "by public transport 1.5–1.8 times the car's time"
      },
      {
       "nome": "Beinasco",
       "gruppo": "Priority points",
       "bus": 52.1,
       "auto_min": 29.8,
       "auto_max": 37.4,
       "giudizio": "by public transport 1.4–1.8 times the car's time"
      },
      {
       "nome": "Borgo Po e Cavoretto",
       "gruppo": "Priority points",
       "bus": 35.6,
       "auto_min": 16.7,
       "auto_max": 20.3,
       "giudizio": "by public transport 1.8–2.1 times the car's time"
      }
     ],
     "scelto": 0
    },
    {
     "tipo": "barre",
     "titolo": "Existing park-and-ride sites: how full they are and how long the bus takes to the centre",
     "unita": "minutes",
     "nota": "Bar = minutes by public transport to Piazza Castello at 8 a.m. On the right, the car time with parking included (typical traffic), and how full the car park is during the day.",
     "voci": [
      {
       "label": "Stura",
       "valore": 42,
       "testo": "42 against 27–34 by car · full during the day"
      },
      {
       "label": "Venchi Unica",
       "valore": 30,
       "testo": "30 against 22–28 by car · half full"
      },
      {
       "label": "Caio Mario",
       "valore": 41,
       "testo": "41 against 23–29 by car · with free spaces"
      },
      {
       "label": "Fermi",
       "valore": 34,
       "testo": "34 against 26–33 by car · occupancy unknown"
      },
      {
       "label": "Sofia",
       "valore": 36,
       "testo": "36 against 20–25 by car · with free spaces"
      }
     ]
    }
   ],
   "calcolo": [
    "Important stops: outside the centre, with a metro, station or terminus or 10 trips an hour, and at least 1,000 passing cars.",
    "Cars entering come from the 2022 travel survey, assigned to the fastest route.",
    "Cars to stop: passing cars times the 5.8% who already leave the car today. Spaces: suitable car parks within 400 metres.",
    "Priority points: stops without enough spaces grouped within 1 km, one per entry axis. Reference stops: Santa Rita, Metro Massaua, Ponte Cavalieri Templari, Regina Margherita, Pasini, Leonardo Da Vinci. Drosso Cap, Stura Lazio, Marsè, Derna Est, Ferrara, Zara.",
    "Bus against car: minutes by public transport (corrected with the measurements) to Piazza Castello at eight in the morning. Car: open estimate plus 5 minutes, and the same corrected with the factor 1.3 from the TomTom check.",
    "Break-even: minutes of parking that make the car as slow as the bus, from 20 to 24 (median of the 12 points).",
    "The class is given only if it is the same with the open estimate and the corrected one. It is the same in 8 points out of 12; in the others it depends on traffic."
   ],
   "criteri": [
    [
     "Important stops",
     "metro, station or terminus or 10 trips an hour, and at least 1,000 passing cars"
    ],
    [
     "Walking distance",
     "400 metres"
    ],
    [
     "Cars to stop",
     "passing cars × 5.8%"
    ],
    [
     "Car park occupancy period",
     "from 15/10/2,026 to 22/10/2,026"
    ],
    [
     "Bus against car",
     "to Piazza Castello at 8; car: open estimate (median factor 2) + 5 minutes, and the same corrected with the check (× 1.3 on driving)"
    ]
   ],
   "limiti": [
    "Passing cars come from a traffic model. Spaces are often estimated: the missing ones are an order of magnitude. With half or double the drivers who leave the car, stops without enough spaces go from 135 to 212 out of 274.",
    "Public transport times are GTT only, without trains.",
    "Car times come from an open model, not measured on the single trip. The TomTom check on 20 routes finds them optimistic: that is why there is a range.",
    "The cost of parking is not in the calculation: it weighs as extra minutes. One point per place and one destination only."
   ],
   "mappa": {
    "id": "interscambio",
    "nota": "Due domande nella mappa, nel menu «Cosa vedere»: dove ci sono parcheggi e dove servirebbe di più un parcheggio."
   },
   "fonti": [
    "GTT (official timetables and vehicle positions)",
    "City of Turin (car parks)",
    "5T (traffic sensors)",
    "Piedmont Mobility Agency (2022 travel survey)",
    "OpenStreetMap",
    "TomTom (check of car times on 20 routes)"
   ],
   "titolo_breve": "Where to leave cars",
   "anima": {
    "tipo": "fermate",
    "contorno": {
     "d": "M879 130l-33 35l-2 -35l22 -12l13 12zM452 11l123 41l18 -10l2 11l11 14l35 -6l42 -20l3 -17l6 -5l25 -3l34 9l-9 37l9 34l48 23l13 3l-8 28l46 93l43 29l-7 39l-27 21l-21 13l28 44l18 20l30 12l64 3l-8 11l3 8l10 6l12 -1l5 4l-90 145l-79 95l-39 49l-51 48l-40 17l-37 36l-129 15l-120 41l-18 59l-73 6l-70 -8l-19 1l-59 -16l-11 5l-87 -31l-14 -16l8 -25l8 -1l36 8l35 -80l-30 11l-67 -45l-44 -39l-10 -14l13 -18l32 -4l128 80l25 -39l45 -134l-1 -15l-33 5l-57 -11l9 -32l9 -4l6 -11l-20 -24l-25 -6l61 -129l13 -59l-19 -21l-12 -51l13 -8l30 2l12 -4l1 -39l122 13l40 -5l0 -15l-7 -11l-3 -50l9 -10l12 -31l-6 -29l2 -15l38 -36l7 -2l8 11z",
     "vb": [
      -40,
      -40,
      1080,
      1043
     ]
    },
    "punti": [
     [
      186,
      477,
      0,
      365
     ],
     [
      216,
      475,
      1,
      335
     ],
     [
      123,
      481,
      1,
      427
     ],
     [
      687,
      138,
      0,
      387
     ],
     [
      261,
      473,
      2,
      290
     ],
     [
      295,
      471,
      2,
      257
     ],
     [
      690,
      150,
      0,
      377
     ],
     [
      692,
      135,
      0,
      392
     ],
     [
      445,
      255,
      1,
      267
     ],
     [
      455,
      252,
      1,
      266
     ],
     [
      442,
      258,
      1,
      265
     ],
     [
      426,
      895,
      1,
      414
     ],
     [
      546,
      301,
      1,
      199
     ],
     [
      479,
      1008,
      0,
      513
     ],
     [
      369,
      154,
      0,
      390
     ],
     [
      342,
      1065,
      0,
      602
     ],
     [
      339,
      1063,
      0,
      601
     ],
     [
      393,
      817,
      0,
      354
     ],
     [
      574,
      300,
      1,
      201
     ],
     [
      576,
      299,
      1,
      203
     ],
     [
      476,
      1024,
      1,
      529
     ],
     [
      69,
      465,
      0,
      482
     ],
     [
      1237,
      976,
      0,
      836
     ],
     [
      401,
      839,
      0,
      370
     ],
     [
      241,
      917,
      1,
      519
     ],
     [
      346,
      682,
      2,
      273
     ],
     [
      257,
      746,
      2,
      383
     ],
     [
      680,
      145,
      0,
      378
     ],
     [
      356,
      671,
      2,
      259
     ],
     [
      268,
      738,
      1,
      369
     ],
     [
      175,
      791,
      1,
      475
     ],
     [
      221,
      475,
      1,
      330
     ],
     [
      290,
      854,
      1,
      439
     ],
     [
      136,
      480,
      1,
      414
     ],
     [
      185,
      787,
      2,
      464
     ],
     [
      259,
      896,
      1,
      491
     ],
     [
      245,
      754,
      1,
      397
     ],
     [
      264,
      887,
      2,
      481
     ],
     [
      279,
      871,
      2,
      459
     ],
     [
      248,
      754,
      1,
      395
     ],
     [
      592,
      599,
      2,
      108
     ],
     [
      270,
      882,
      2,
      474
     ],
     [
      204,
      782,
      2,
      446
     ],
     [
      253,
      900,
      1,
      498
     ],
     [
      200,
      782,
      2,
      449
     ],
     [
      236,
      762,
      1,
      409
     ],
     [
      240,
      648,
      1,
      344
     ],
     [
      727,
      514,
      1,
      178
     ],
     [
      299,
      840,
      1,
      423
     ],
     [
      233,
      762,
      1,
      411
     ],
     [
      743,
      510,
      1,
      193
     ],
     [
      325,
      699,
      1,
      300
     ],
     [
      311,
      828,
      1,
      406
     ],
     [
      269,
      652,
      1,
      319
     ],
     [
      375,
      748,
      0,
      304
     ],
     [
      337,
      685,
      2,
      282
     ],
     [
      10,
      488,
      1,
      540
     ],
     [
      784,
      403,
      1,
      253
     ],
     [
      390,
      729,
      0,
      279
     ],
     [
      345,
      687,
      2,
      277
     ],
     [
      334,
      799,
      0,
      369
     ],
     [
      313,
      825,
      0,
      402
     ],
     [
      353,
      776,
      1,
      339
     ],
     [
      331,
      804,
      0,
      375
     ],
     [
      293,
      721,
      1,
      339
     ],
     [
      706,
      332,
      0,
      229
     ],
     [
      1049,
      -566,
      0,
      1177
     ],
     [
      349,
      780,
      1,
      345
     ],
     [
      207,
      476,
      0,
      344
     ],
     [
      47,
      638,
      2,
      522
     ],
     [
      414,
      698,
      1,
      240
     ],
     [
      320,
      816,
      0,
      391
     ],
     [
      779,
      426,
      1,
      241
     ],
     [
      273,
      876,
      2,
      467
     ],
     [
      794,
      390,
      1,
      268
     ],
     [
      159,
      480,
      1,
      392
     ],
     [
      156,
      478,
      1,
      395
     ],
     [
      -57,
      492,
      2,
      607
     ],
     [
      260,
      901,
      1,
      495
     ],
     [
      647,
      229,
      2,
      288
     ],
     [
      672,
      177,
      1,
      345
     ],
     [
      632,
      261,
      0,
      253
     ],
     [
      663,
      197,
      0,
      323
     ],
     [
      223,
      647,
      1,
      359
     ],
     [
      256,
      650,
      1,
      330
     ],
     [
      268,
      650,
      1,
      319
     ],
     [
      399,
      717,
      2,
      264
     ],
     [
      856,
      357,
      1,
      338
     ],
     [
      507,
      999,
      1,
      501
     ],
     [
      722,
      316,
      0,
      252
     ],
     [
      674,
      534,
      2,
      129
     ],
     [
      95,
      482,
      1,
      455
     ],
     [
      553,
      300,
      1,
      200
     ],
     [
      432,
      675,
      2,
      211
     ],
     [
      607,
      268,
      0,
      239
     ],
     [
      324,
      812,
      0,
      385
     ],
     [
      393,
      348,
      2,
      219
     ],
     [
      380,
      377,
      2,
      210
     ],
     [
      936,
      265,
      0,
      452
     ],
     [
      429,
      679,
      2,
      216
     ],
     [
      778,
      469,
      2,
      230
     ],
     [
      532,
      729,
      1,
      230
     ],
     [
      315,
      828,
      1,
      403
     ],
     [
      927,
      309,
      1,
      423
     ],
     [
      516,
      367,
      1,
      137
     ],
     [
      -23,
      490,
      1,
      573
     ],
     [
      367,
      758,
      0,
      316
     ],
     [
      -19,
      489,
      1,
      569
     ],
     [
      620,
      561,
      1,
      93
     ],
     [
      404,
      716,
      2,
      261
     ],
     [
      510,
      359,
      1,
      147
     ],
     [
      294,
      841,
      1,
      426
     ],
     [
      365,
      760,
      0,
      319
     ],
     [
      287,
      718,
      1,
      342
     ],
     [
      750,
      286,
      2,
      293
     ],
     [
      292,
      602,
      2,
      277
     ],
     [
      284,
      660,
      1,
      310
     ],
     [
      333,
      473,
      1,
      219
     ],
     [
      307,
      515,
      1,
      243
     ],
     [
      337,
      464,
      1,
      216
     ],
     [
      281,
      656,
      1,
      311
     ],
     [
      402,
      713,
      2,
      259
     ],
     [
      -175,
      500,
      0,
      725
     ],
     [
      296,
      666,
      1,
      303
     ],
     [
      766,
      244,
      0,
      335
     ],
     [
      711,
      333,
      0,
      232
     ],
     [
      623,
      282,
      0,
      230
     ],
     [
      303,
      824,
      1,
      407
     ],
     [
      621,
      286,
      0,
      225
     ],
     [
      630,
      276,
      1,
      238
     ],
     [
      700,
      342,
      0,
      218
     ],
     [
      600,
      330,
      1,
      177
     ],
     [
      324,
      679,
      2,
      288
     ],
     [
      -178,
      498,
      0,
      728
     ],
     [
      -150,
      496,
      0,
      700
     ],
     [
      289,
      679,
      2,
      316
     ],
     [
      283,
      501,
      2,
      267
     ],
     [
      513,
      356,
      0,
      149
     ],
     [
      99,
      818,
      0,
      552
     ],
     [
      111,
      814,
      0,
      540
     ],
     [
      288,
      700,
      1,
      330
     ],
     [
      482,
      999,
      0,
      504
     ],
     [
      591,
      352,
      1,
      154
     ],
     [
      -257,
      504,
      0,
      807
     ],
     [
      103,
      818,
      0,
      549
     ],
     [
      122,
      811,
      2,
      529
     ],
     [
      444,
      252,
      1,
      270
     ],
     [
      555,
      262,
      2,
      238
     ],
     [
      -95,
      495,
      1,
      645
     ],
     [
      725,
      1084,
      2,
      610
     ],
     [
      588,
      358,
      2,
      147
     ],
     [
      533,
      260,
      2,
      241
     ],
     [
      428,
      266,
      1,
      264
     ],
     [
      688,
      357,
      0,
      199
     ],
     [
      422,
      290,
      2,
      246
     ],
     [
      284,
      56,
      0,
      518
     ],
     [
      312,
      806,
      0,
      388
     ],
     [
      411,
      310,
      2,
      235
     ],
     [
      539,
      366,
      0,
      134
     ],
     [
      -99,
      493,
      1,
      649
     ],
     [
      421,
      287,
      2,
      249
     ],
     [
      718,
      322,
      0,
      245
     ],
     [
      431,
      264,
      1,
      264
     ],
     [
      381,
      668,
      0,
      238
     ],
     [
      691,
      355,
      0,
      202
     ],
     [
      493,
      994,
      0,
      497
     ],
     [
      315,
      803,
      0,
      383
     ],
     [
      530,
      262,
      2,
      239
     ],
     [
      371,
      396,
      2,
      207
     ],
     [
      313,
      674,
      2,
      294
     ],
     [
      434,
      249,
      1,
      277
     ],
     [
      51,
      460,
      0,
      501
     ],
     [
      311,
      671,
      2,
      294
     ],
     [
      299,
      665,
      1,
      300
     ],
     [
      -221,
      501,
      0,
      771
     ],
     [
      302,
      546,
      2,
      252
     ],
     [
      -196,
      499,
      0,
      746
     ],
     [
      609,
      312,
      1,
      197
     ],
     [
      984,
      257,
      0,
      497
     ],
     [
      290,
      632,
      1,
      292
     ],
     [
      709,
      325,
      0,
      236
     ],
     [
      748,
      294,
      2,
      286
     ],
     [
      -224,
      503,
      0,
      774
     ],
     [
      788,
      288,
      2,
      319
     ],
     [
      813,
      284,
      2,
      340
     ],
     [
      360,
      719,
      0,
      290
     ],
     [
      575,
      378,
      1,
      125
     ],
     [
      619,
      304,
      0,
      208
     ],
     [
      598,
      335,
      1,
      172
     ],
     [
      611,
      307,
      1,
      202
     ],
     [
      1029,
      199,
      0,
      566
     ],
     [
      593,
      391,
      1,
      117
     ],
     [
      436,
      261,
      1,
      265
     ],
     [
      310,
      510,
      1,
      240
     ],
     [
      580,
      375,
      1,
      129
     ],
     [
      345,
      249,
      0,
      324
     ],
     [
      -151,
      501,
      0,
      701
     ],
     [
      576,
      384,
      2,
      119
     ],
     [
      265,
      645,
      1,
      320
     ],
     [
      287,
      774,
      0,
      380
     ],
     [
      766,
      291,
      2,
      301
     ],
     [
      600,
      270,
      2,
      235
     ],
     [
      293,
      571,
      2,
      267
     ],
     [
      614,
      410,
      0,
      110
     ],
     [
      651,
      387,
      0,
      152
     ],
     [
      428,
      675,
      1,
      213
     ],
     [
      296,
      566,
      2,
      262
     ],
     [
      677,
      370,
      1,
      182
     ],
     [
      247,
      761,
      1,
      400
     ],
     [
      667,
      377,
      1,
      170
     ],
     [
      266,
      628,
      2,
      312
     ],
     [
      626,
      435,
      1,
      100
     ],
     [
      423,
      214,
      1,
      313
     ],
     [
      442,
      891,
      1,
      406
     ],
     [
      412,
      205,
      0,
      326
     ],
     [
      522,
      365,
      0,
      138
     ],
     [
      391,
      714,
      1,
      267
     ],
     [
      411,
      953,
      0,
      474
     ],
     [
      562,
      371,
      0,
      130
     ],
     [
      442,
      692,
      0,
      220
     ],
     [
      -41,
      324,
      0,
      617
     ],
     [
      -16,
      321,
      1,
      594
     ],
     [
      387,
      177,
      2,
      362
     ],
     [
      374,
      946,
      0,
      479
     ],
     [
      423,
      230,
      2,
      298
     ],
     [
      234,
      551,
      2,
      320
     ],
     [
      403,
      980,
      1,
      502
     ],
     [
      419,
      201,
      0,
      326
     ],
     [
      353,
      1052,
      0,
      586
     ],
     [
      263,
      687,
      1,
      343
     ],
     [
      425,
      901,
      1,
      420
     ],
     [
      423,
      903,
      1,
      423
     ],
     [
      -93,
      327,
      0,
      666
     ],
     [
      -124,
      288,
      0,
      707
     ],
     [
      422,
      661,
      1,
      206
     ],
     [
      434,
      209,
      1,
      313
     ],
     [
      303,
      789,
      0,
      380
     ],
     [
      193,
      653,
      1,
      388
     ],
     [
      231,
      549,
      2,
      323
     ],
     [
      293,
      784,
      0,
      383
     ],
     [
      410,
      200,
      0,
      331
     ],
     [
      297,
      784,
      0,
      380
     ],
     [
      308,
      789,
      0,
      377
     ],
     [
      320,
      696,
      1,
      302
     ],
     [
      -160,
      269,
      0,
      747
     ],
     [
      507,
      348,
      0,
      158
     ],
     [
      379,
      833,
      2,
      374
     ],
     [
      373,
      852,
      2,
      394
     ],
     [
      381,
      837,
      2,
      377
     ],
     [
      486,
      262,
      1,
      246
     ],
     [
      518,
      255,
      2,
      247
     ],
     [
      362,
      908,
      1,
      449
     ],
     [
      153,
      527,
      0,
      398
     ],
     [
      69,
      552,
      0,
      484
     ],
     [
      92,
      552,
      1,
      461
     ],
     [
      50,
      547,
      0,
      502
     ],
     [
      338,
      167,
      1,
      395
     ],
     [
      1245,
      953,
      0,
      830
     ],
     [
      124,
      549,
      1,
      429
     ],
     [
      89,
      470,
      0,
      462
     ],
     [
      527,
      286,
      2,
      215
     ],
     [
      15,
      539,
      0,
      536
     ],
     [
      296,
      93,
      1,
      480
     ],
     [
      890,
      96,
      0,
      528
     ],
     [
      295,
      548,
      2,
      259
     ],
     [
      288,
      548,
      2,
      266
     ],
     [
      274,
      549,
      2,
      280
     ],
     [
      279,
      549,
      2,
      275
     ],
     [
      251,
      550,
      1,
      303
     ],
     [
      485,
      321,
      0,
      190
     ],
     [
      258,
      551,
      1,
      296
     ],
     [
      225,
      548,
      2,
      329
     ],
     [
      454,
      1043,
      0,
      551
     ],
     [
      64,
      463,
      0,
      487
     ]
    ],
    "prioritari": [
     [
      331,
      683
     ],
     [
      219,
      475
     ],
     [
      492,
      1012
     ],
     [
      381,
      374
     ],
     [
      778,
      469
     ],
     [
      47,
      638
     ],
     [
      262,
      891
     ],
     [
      755,
      291
     ],
     [
      725,
      1084
     ],
     [
      615,
      273
     ],
     [
      122,
      811
     ],
     [
      532,
      729
     ]
    ],
    "legenda": [
     {
      "label": "enough spaces",
      "n": 95,
      "tono": "verde"
     },
     {
      "label": "few spaces",
      "n": 111,
      "tono": "giallo"
     },
     {
      "label": "no car park",
      "n": 68,
      "tono": "rosso"
     }
    ],
    "didascalia": "Each dot is an important stop, in Turin and the surrounding towns; the line is the city boundary. The black circles are the 12 points where new spaces are most needed."
   },
   "pareggio": {
    "a": 24,
    "b": 20
   }
  },
  "forma_de": {
   "tipo_dato": "Datenart: berechnet aus echten Daten und zum Teil gemessen, über wenige Tage.",
   "titolo": "Etwa 2 von 3 wichtigen Haltestellen haben nicht genug Stellplätze, um das Auto stehen zu lassen",
   "domanda": "Finden Autofahrer von außerhalb einen Platz für ihr Auto nahe einer wichtigen Haltestelle, um mit öffentlichen Verkehrsmitteln weiterzufahren?",
   "numero": {
    "valore": 179,
    "unita": "",
    "testo": "wichtige Haltestellen von 274 haben nicht genug Stellplätze im Umkreis von 400 Metern zu Fuß",
    "breve": "wichtige Haltestellen ohne Stellplätze fürs Auto"
   },
   "principale": {
    "tipo": "barre",
    "titolo": "Die 12 Einfahrtspunkte, nach Bedarf an Parkplätzen",
    "unita": "Stellplätze",
    "nota": "Fehlende Stellplätze neben jedem Balken: eine Größenordnung. Die Farbe ist der Bedarf, in Dritteln.",
    "legenda": [
     {
      "tono": "rosso",
      "label": "hoher Bedarf"
     },
     {
      "tono": "arancio",
      "label": "mittlerer Bedarf"
     },
     {
      "tono": "giallo",
      "label": "geringer Bedarf"
     }
    ],
    "voci": [
     {
      "label": "Santa Rita",
      "valore": 450,
      "tono": "rosso",
      "testo": "~450"
     },
     {
      "label": "Parella (Metro Massaua)",
      "valore": 350,
      "tono": "rosso",
      "testo": "~350"
     },
     {
      "label": "Moncalieri (Ponte Cavalieri Templari)",
      "valore": 350,
      "tono": "rosso",
      "testo": "~350"
     },
     {
      "label": "Parella (Regina Margherita)",
      "valore": 350,
      "tono": "rosso",
      "testo": "~350"
     },
     {
      "label": "Madonna del Pilone",
      "valore": 250,
      "tono": "arancio",
      "testo": "~250"
     },
     {
      "label": "Grugliasco",
      "valore": 200,
      "tono": "arancio",
      "testo": "~200"
     },
     {
      "label": "Mirafiori Sud",
      "valore": 200,
      "tono": "arancio",
      "testo": "~200"
     },
     {
      "label": "Regio Parco",
      "valore": 200,
      "tono": "arancio",
      "testo": "~200"
     },
     {
      "label": "Moncalieri (Marsè)",
      "valore": 150,
      "tono": "giallo",
      "testo": "~150"
     },
     {
      "label": "Falchera",
      "valore": 100,
      "tono": "giallo",
      "testo": "~100"
     },
     {
      "label": "Beinasco",
      "valore": 80,
      "tono": "giallo",
      "testo": "~80"
     },
     {
      "label": "Borgo Po e Cavoretto",
      "valore": 60,
      "tono": "giallo",
      "testo": "~60"
     }
    ]
   },
   "punti": [
    "68 wichtige Haltestellen haben keinen Parkplatz in der Nähe, 111 zu wenige.",
    "Der erste der 12 Einfahrtspunkte, an denen Stellplätze gebraucht werden, ist Santa Rita: Es fehlen ~450.",
    "An 1–5 von 12 Punkten erreicht man das Zentrum nach dem Abstellen des Autos mit dem Bus in höchstens dem 1,5-Fachen der Autozeit."
   ],
   "altri": [
    {
     "tipo": "gara",
     "titolo": "Das Rennen: Bus und Auto zur Piazza Castello, um 8 Uhr an einem Werktag",
     "nota": "Bus und Auto fahren zusammen von jedem Parkplatz los, nacheinander. Für das Auto gibt es eine Zeit mit der Spanne aus der Kontrolle, Parken inklusive.",
     "luoghi": [
      {
       "nome": "Santa Rita",
       "gruppo": "Vorrangige Punkte",
       "bus": 38.7,
       "auto_min": 19.6,
       "auto_max": 24.1,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,6- bis 2-Fache der Autozeit"
      },
      {
       "nome": "Parella (Metro Massaua)",
       "gruppo": "Vorrangige Punkte",
       "bus": 27.3,
       "auto_min": 20.3,
       "auto_max": 25.0,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,1- bis 1,3-Fache der Autozeit"
      },
      {
       "nome": "Moncalieri (Ponte Cavalieri Templari)",
       "gruppo": "Vorrangige Punkte",
       "bus": 54.2,
       "auto_min": 23.1,
       "auto_max": 28.7,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,9- bis 2,4-Fache der Autozeit"
      },
      {
       "nome": "Parella (Regina Margherita)",
       "gruppo": "Vorrangige Punkte",
       "bus": 33.5,
       "auto_min": 18.0,
       "auto_max": 22.0,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,5- bis 1,9-Fache der Autozeit"
      },
      {
       "nome": "Madonna del Pilone",
       "gruppo": "Vorrangige Punkte",
       "bus": 30.4,
       "auto_min": 17.5,
       "auto_max": 21.3,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,4- bis 1,7-Fache der Autozeit"
      },
      {
       "nome": "Grugliasco",
       "gruppo": "Vorrangige Punkte",
       "bus": 62.5,
       "auto_min": 29.7,
       "auto_max": 37.3,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,7- bis 2,1-Fache der Autozeit"
      },
      {
       "nome": "Mirafiori Sud",
       "gruppo": "Vorrangige Punkte",
       "bus": 45.9,
       "auto_min": 25.4,
       "auto_max": 31.7,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,4- bis 1,8-Fache der Autozeit"
      },
      {
       "nome": "Regio Parco",
       "gruppo": "Vorrangige Punkte",
       "bus": 39.7,
       "auto_min": 21.4,
       "auto_max": 26.4,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,5- bis 1,9-Fache der Autozeit"
      },
      {
       "nome": "Moncalieri (Marsè)",
       "gruppo": "Vorrangige Punkte",
       "bus": 64.5,
       "auto_min": 29.5,
       "auto_max": 37.0,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,7- bis 2,2-Fache der Autozeit"
      },
      {
       "nome": "Falchera",
       "gruppo": "Vorrangige Punkte",
       "bus": 36.6,
       "auto_min": 20.3,
       "auto_max": 25.0,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,5- bis 1,8-Fache der Autozeit"
      },
      {
       "nome": "Beinasco",
       "gruppo": "Vorrangige Punkte",
       "bus": 52.1,
       "auto_min": 29.8,
       "auto_max": 37.4,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,4- bis 1,8-Fache der Autozeit"
      },
      {
       "nome": "Borgo Po e Cavoretto",
       "gruppo": "Vorrangige Punkte",
       "bus": 35.6,
       "auto_min": 16.7,
       "auto_max": 20.3,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,8- bis 2,1-Fache der Autozeit"
      }
     ],
     "scelto": 0
    },
    {
     "tipo": "barre",
     "titolo": "Die vorhandenen Park-and-Ride-Anlagen: wie voll sie sind und wie lange der Bus ins Zentrum braucht",
     "unita": "Minuten",
     "nota": "Balken = Minuten mit öffentlichen Verkehrsmitteln bis zur Piazza Castello um 8 Uhr. Rechts die Zeit mit dem Auto, Parken inklusive (typischer Verkehr), und wie voll der Parkplatz tagsüber ist.",
     "voci": [
      {
       "label": "Stura",
       "valore": 42,
       "testo": "42 gegen 27–34 mit dem Auto · tagsüber voll"
      },
      {
       "label": "Venchi Unica",
       "valore": 30,
       "testo": "30 gegen 22–28 mit dem Auto · halb voll"
      },
      {
       "label": "Caio Mario",
       "valore": 41,
       "testo": "41 gegen 23–29 mit dem Auto · mit freien Plätzen"
      },
      {
       "label": "Fermi",
       "valore": 34,
       "testo": "34 gegen 26–33 mit dem Auto · Belegung unbekannt"
      },
      {
       "label": "Sofia",
       "valore": 36,
       "testo": "36 gegen 20–25 mit dem Auto · mit freien Plätzen"
      }
     ]
    }
   ],
   "calcolo": [
    "Wichtige Haltestellen: außerhalb des Zentrums, mit Metro, Bahnhof oder Endhaltestelle oder 10 Fahrten pro Stunde, und mindestens 1.000 vorbeifahrenden Autos.",
    "Die einfahrenden Autos stammen aus der Mobilitätserhebung 2022 und sind der schnellsten Strecke zugeordnet.",
    "Zu stoppende Autos: vorbeifahrende Autos mal 5,8% derer, die das Auto heute schon stehen lassen. Plätze: geeignete Parkplätze im Umkreis von 400 Metern.",
    "Vorrangige Punkte: Haltestellen ohne genug Stellplätze, innerhalb von 1 km zusammengefasst, einer pro Einfallstraße. Bezugshaltestellen: Santa Rita, Metro Massaua, Ponte Cavalieri Templari, Regina Margherita, Pasini, Leonardo Da Vinci. Drosso Cap, Stura Lazio, Marsè, Derna Est, Ferrara, Zara.",
    "Bus gegen Auto: Minuten mit öffentlichen Verkehrsmitteln (mit den Messungen korrigiert) zur Piazza Castello um acht Uhr morgens. Auto: offene Schätzung plus 5 Minuten, und dieselbe Schätzung mit dem Faktor 1,3 aus der TomTom-Kontrolle korrigiert.",
    "Break-even: Parkminuten, bei denen das Auto so langsam ist wie der Bus, von 20 bis 24 (Median der 12 Punkte).",
    "Die Klasse wird nur angegeben, wenn sie mit der offenen und mit der korrigierten Schätzung gleich ist. Das ist an 8 von 12 Punkten der Fall; an den anderen hängt es vom Verkehr ab."
   ],
   "criteri": [
    [
     "Wichtige Haltestellen",
     "Metro, Bahnhof oder Endhaltestelle oder 10 Fahrten pro Stunde, und mindestens 1.000 vorbeifahrende Autos"
    ],
    [
     "Entfernung zu Fuß",
     "400 Meter"
    ],
    [
     "Zu stoppende Autos",
     "vorbeifahrende Autos × 5,8%"
    ],
    [
     "Zeitraum der Parkplatzbelegung",
     "vom 15.10.2026 bis zum 22.10.2026"
    ],
    [
     "Bus gegen Auto",
     "zur Piazza Castello um 8 Uhr; Auto: offene Schätzung (mittlerer Faktor 2) + 5 Minuten, und dieselbe mit der Kontrolle korrigiert (× 1,3 auf die Fahrt)"
    ]
   ],
   "limiti": [
    "Die vorbeifahrenden Autos stammen aus einem Verkehrsmodell. Die Stellplätze sind oft geschätzt: Die fehlenden sind eine Größenordnung. Bei halb so vielen oder doppelt so vielen Autofahrern, die das Auto stehen lassen, liegen die Haltestellen ohne genug Stellplätze zwischen 135 und 212 von 274.",
    "Die Zeiten mit öffentlichen Verkehrsmitteln sind nur GTT, ohne Züge.",
    "Die Autozeiten stammen aus einem offenen Modell und sind nicht auf der einzelnen Fahrt gemessen. Die TomTom-Kontrolle auf 20 Strecken findet sie optimistisch: Deshalb gibt es eine Spanne.",
    "Die Parkkosten sind nicht in der Rechnung: Sie zählen als zusätzliche Minuten. Betrachtet wird ein Punkt pro Ort und nur ein Ziel."
   ],
   "mappa": {
    "id": "interscambio",
    "nota": "Due domande nella mappa, nel menu «Cosa vedere»: dove ci sono parcheggi e dove servirebbe di più un parcheggio."
   },
   "fonti": [
    "GTT (offizielle Fahrpläne und Fahrzeugpositionen)",
    "Stadt Turin (Parkplätze)",
    "5T (Verkehrssensoren)",
    "Mobilitätsagentur des Piemont (Mobilitätserhebung 2022)",
    "OpenStreetMap",
    "TomTom (Kontrolle der Autozeiten auf 20 Strecken)"
   ],
   "titolo_breve": "Wo das Auto stehen lassen",
   "anima": {
    "tipo": "fermate",
    "contorno": {
     "d": "M879 130l-33 35l-2 -35l22 -12l13 12zM452 11l123 41l18 -10l2 11l11 14l35 -6l42 -20l3 -17l6 -5l25 -3l34 9l-9 37l9 34l48 23l13 3l-8 28l46 93l43 29l-7 39l-27 21l-21 13l28 44l18 20l30 12l64 3l-8 11l3 8l10 6l12 -1l5 4l-90 145l-79 95l-39 49l-51 48l-40 17l-37 36l-129 15l-120 41l-18 59l-73 6l-70 -8l-19 1l-59 -16l-11 5l-87 -31l-14 -16l8 -25l8 -1l36 8l35 -80l-30 11l-67 -45l-44 -39l-10 -14l13 -18l32 -4l128 80l25 -39l45 -134l-1 -15l-33 5l-57 -11l9 -32l9 -4l6 -11l-20 -24l-25 -6l61 -129l13 -59l-19 -21l-12 -51l13 -8l30 2l12 -4l1 -39l122 13l40 -5l0 -15l-7 -11l-3 -50l9 -10l12 -31l-6 -29l2 -15l38 -36l7 -2l8 11z",
     "vb": [
      -40,
      -40,
      1080,
      1043
     ]
    },
    "punti": [
     [
      186,
      477,
      0,
      365
     ],
     [
      216,
      475,
      1,
      335
     ],
     [
      123,
      481,
      1,
      427
     ],
     [
      687,
      138,
      0,
      387
     ],
     [
      261,
      473,
      2,
      290
     ],
     [
      295,
      471,
      2,
      257
     ],
     [
      690,
      150,
      0,
      377
     ],
     [
      692,
      135,
      0,
      392
     ],
     [
      445,
      255,
      1,
      267
     ],
     [
      455,
      252,
      1,
      266
     ],
     [
      442,
      258,
      1,
      265
     ],
     [
      426,
      895,
      1,
      414
     ],
     [
      546,
      301,
      1,
      199
     ],
     [
      479,
      1008,
      0,
      513
     ],
     [
      369,
      154,
      0,
      390
     ],
     [
      342,
      1065,
      0,
      602
     ],
     [
      339,
      1063,
      0,
      601
     ],
     [
      393,
      817,
      0,
      354
     ],
     [
      574,
      300,
      1,
      201
     ],
     [
      576,
      299,
      1,
      203
     ],
     [
      476,
      1024,
      1,
      529
     ],
     [
      69,
      465,
      0,
      482
     ],
     [
      1237,
      976,
      0,
      836
     ],
     [
      401,
      839,
      0,
      370
     ],
     [
      241,
      917,
      1,
      519
     ],
     [
      346,
      682,
      2,
      273
     ],
     [
      257,
      746,
      2,
      383
     ],
     [
      680,
      145,
      0,
      378
     ],
     [
      356,
      671,
      2,
      259
     ],
     [
      268,
      738,
      1,
      369
     ],
     [
      175,
      791,
      1,
      475
     ],
     [
      221,
      475,
      1,
      330
     ],
     [
      290,
      854,
      1,
      439
     ],
     [
      136,
      480,
      1,
      414
     ],
     [
      185,
      787,
      2,
      464
     ],
     [
      259,
      896,
      1,
      491
     ],
     [
      245,
      754,
      1,
      397
     ],
     [
      264,
      887,
      2,
      481
     ],
     [
      279,
      871,
      2,
      459
     ],
     [
      248,
      754,
      1,
      395
     ],
     [
      592,
      599,
      2,
      108
     ],
     [
      270,
      882,
      2,
      474
     ],
     [
      204,
      782,
      2,
      446
     ],
     [
      253,
      900,
      1,
      498
     ],
     [
      200,
      782,
      2,
      449
     ],
     [
      236,
      762,
      1,
      409
     ],
     [
      240,
      648,
      1,
      344
     ],
     [
      727,
      514,
      1,
      178
     ],
     [
      299,
      840,
      1,
      423
     ],
     [
      233,
      762,
      1,
      411
     ],
     [
      743,
      510,
      1,
      193
     ],
     [
      325,
      699,
      1,
      300
     ],
     [
      311,
      828,
      1,
      406
     ],
     [
      269,
      652,
      1,
      319
     ],
     [
      375,
      748,
      0,
      304
     ],
     [
      337,
      685,
      2,
      282
     ],
     [
      10,
      488,
      1,
      540
     ],
     [
      784,
      403,
      1,
      253
     ],
     [
      390,
      729,
      0,
      279
     ],
     [
      345,
      687,
      2,
      277
     ],
     [
      334,
      799,
      0,
      369
     ],
     [
      313,
      825,
      0,
      402
     ],
     [
      353,
      776,
      1,
      339
     ],
     [
      331,
      804,
      0,
      375
     ],
     [
      293,
      721,
      1,
      339
     ],
     [
      706,
      332,
      0,
      229
     ],
     [
      1049,
      -566,
      0,
      1177
     ],
     [
      349,
      780,
      1,
      345
     ],
     [
      207,
      476,
      0,
      344
     ],
     [
      47,
      638,
      2,
      522
     ],
     [
      414,
      698,
      1,
      240
     ],
     [
      320,
      816,
      0,
      391
     ],
     [
      779,
      426,
      1,
      241
     ],
     [
      273,
      876,
      2,
      467
     ],
     [
      794,
      390,
      1,
      268
     ],
     [
      159,
      480,
      1,
      392
     ],
     [
      156,
      478,
      1,
      395
     ],
     [
      -57,
      492,
      2,
      607
     ],
     [
      260,
      901,
      1,
      495
     ],
     [
      647,
      229,
      2,
      288
     ],
     [
      672,
      177,
      1,
      345
     ],
     [
      632,
      261,
      0,
      253
     ],
     [
      663,
      197,
      0,
      323
     ],
     [
      223,
      647,
      1,
      359
     ],
     [
      256,
      650,
      1,
      330
     ],
     [
      268,
      650,
      1,
      319
     ],
     [
      399,
      717,
      2,
      264
     ],
     [
      856,
      357,
      1,
      338
     ],
     [
      507,
      999,
      1,
      501
     ],
     [
      722,
      316,
      0,
      252
     ],
     [
      674,
      534,
      2,
      129
     ],
     [
      95,
      482,
      1,
      455
     ],
     [
      553,
      300,
      1,
      200
     ],
     [
      432,
      675,
      2,
      211
     ],
     [
      607,
      268,
      0,
      239
     ],
     [
      324,
      812,
      0,
      385
     ],
     [
      393,
      348,
      2,
      219
     ],
     [
      380,
      377,
      2,
      210
     ],
     [
      936,
      265,
      0,
      452
     ],
     [
      429,
      679,
      2,
      216
     ],
     [
      778,
      469,
      2,
      230
     ],
     [
      532,
      729,
      1,
      230
     ],
     [
      315,
      828,
      1,
      403
     ],
     [
      927,
      309,
      1,
      423
     ],
     [
      516,
      367,
      1,
      137
     ],
     [
      -23,
      490,
      1,
      573
     ],
     [
      367,
      758,
      0,
      316
     ],
     [
      -19,
      489,
      1,
      569
     ],
     [
      620,
      561,
      1,
      93
     ],
     [
      404,
      716,
      2,
      261
     ],
     [
      510,
      359,
      1,
      147
     ],
     [
      294,
      841,
      1,
      426
     ],
     [
      365,
      760,
      0,
      319
     ],
     [
      287,
      718,
      1,
      342
     ],
     [
      750,
      286,
      2,
      293
     ],
     [
      292,
      602,
      2,
      277
     ],
     [
      284,
      660,
      1,
      310
     ],
     [
      333,
      473,
      1,
      219
     ],
     [
      307,
      515,
      1,
      243
     ],
     [
      337,
      464,
      1,
      216
     ],
     [
      281,
      656,
      1,
      311
     ],
     [
      402,
      713,
      2,
      259
     ],
     [
      -175,
      500,
      0,
      725
     ],
     [
      296,
      666,
      1,
      303
     ],
     [
      766,
      244,
      0,
      335
     ],
     [
      711,
      333,
      0,
      232
     ],
     [
      623,
      282,
      0,
      230
     ],
     [
      303,
      824,
      1,
      407
     ],
     [
      621,
      286,
      0,
      225
     ],
     [
      630,
      276,
      1,
      238
     ],
     [
      700,
      342,
      0,
      218
     ],
     [
      600,
      330,
      1,
      177
     ],
     [
      324,
      679,
      2,
      288
     ],
     [
      -178,
      498,
      0,
      728
     ],
     [
      -150,
      496,
      0,
      700
     ],
     [
      289,
      679,
      2,
      316
     ],
     [
      283,
      501,
      2,
      267
     ],
     [
      513,
      356,
      0,
      149
     ],
     [
      99,
      818,
      0,
      552
     ],
     [
      111,
      814,
      0,
      540
     ],
     [
      288,
      700,
      1,
      330
     ],
     [
      482,
      999,
      0,
      504
     ],
     [
      591,
      352,
      1,
      154
     ],
     [
      -257,
      504,
      0,
      807
     ],
     [
      103,
      818,
      0,
      549
     ],
     [
      122,
      811,
      2,
      529
     ],
     [
      444,
      252,
      1,
      270
     ],
     [
      555,
      262,
      2,
      238
     ],
     [
      -95,
      495,
      1,
      645
     ],
     [
      725,
      1084,
      2,
      610
     ],
     [
      588,
      358,
      2,
      147
     ],
     [
      533,
      260,
      2,
      241
     ],
     [
      428,
      266,
      1,
      264
     ],
     [
      688,
      357,
      0,
      199
     ],
     [
      422,
      290,
      2,
      246
     ],
     [
      284,
      56,
      0,
      518
     ],
     [
      312,
      806,
      0,
      388
     ],
     [
      411,
      310,
      2,
      235
     ],
     [
      539,
      366,
      0,
      134
     ],
     [
      -99,
      493,
      1,
      649
     ],
     [
      421,
      287,
      2,
      249
     ],
     [
      718,
      322,
      0,
      245
     ],
     [
      431,
      264,
      1,
      264
     ],
     [
      381,
      668,
      0,
      238
     ],
     [
      691,
      355,
      0,
      202
     ],
     [
      493,
      994,
      0,
      497
     ],
     [
      315,
      803,
      0,
      383
     ],
     [
      530,
      262,
      2,
      239
     ],
     [
      371,
      396,
      2,
      207
     ],
     [
      313,
      674,
      2,
      294
     ],
     [
      434,
      249,
      1,
      277
     ],
     [
      51,
      460,
      0,
      501
     ],
     [
      311,
      671,
      2,
      294
     ],
     [
      299,
      665,
      1,
      300
     ],
     [
      -221,
      501,
      0,
      771
     ],
     [
      302,
      546,
      2,
      252
     ],
     [
      -196,
      499,
      0,
      746
     ],
     [
      609,
      312,
      1,
      197
     ],
     [
      984,
      257,
      0,
      497
     ],
     [
      290,
      632,
      1,
      292
     ],
     [
      709,
      325,
      0,
      236
     ],
     [
      748,
      294,
      2,
      286
     ],
     [
      -224,
      503,
      0,
      774
     ],
     [
      788,
      288,
      2,
      319
     ],
     [
      813,
      284,
      2,
      340
     ],
     [
      360,
      719,
      0,
      290
     ],
     [
      575,
      378,
      1,
      125
     ],
     [
      619,
      304,
      0,
      208
     ],
     [
      598,
      335,
      1,
      172
     ],
     [
      611,
      307,
      1,
      202
     ],
     [
      1029,
      199,
      0,
      566
     ],
     [
      593,
      391,
      1,
      117
     ],
     [
      436,
      261,
      1,
      265
     ],
     [
      310,
      510,
      1,
      240
     ],
     [
      580,
      375,
      1,
      129
     ],
     [
      345,
      249,
      0,
      324
     ],
     [
      -151,
      501,
      0,
      701
     ],
     [
      576,
      384,
      2,
      119
     ],
     [
      265,
      645,
      1,
      320
     ],
     [
      287,
      774,
      0,
      380
     ],
     [
      766,
      291,
      2,
      301
     ],
     [
      600,
      270,
      2,
      235
     ],
     [
      293,
      571,
      2,
      267
     ],
     [
      614,
      410,
      0,
      110
     ],
     [
      651,
      387,
      0,
      152
     ],
     [
      428,
      675,
      1,
      213
     ],
     [
      296,
      566,
      2,
      262
     ],
     [
      677,
      370,
      1,
      182
     ],
     [
      247,
      761,
      1,
      400
     ],
     [
      667,
      377,
      1,
      170
     ],
     [
      266,
      628,
      2,
      312
     ],
     [
      626,
      435,
      1,
      100
     ],
     [
      423,
      214,
      1,
      313
     ],
     [
      442,
      891,
      1,
      406
     ],
     [
      412,
      205,
      0,
      326
     ],
     [
      522,
      365,
      0,
      138
     ],
     [
      391,
      714,
      1,
      267
     ],
     [
      411,
      953,
      0,
      474
     ],
     [
      562,
      371,
      0,
      130
     ],
     [
      442,
      692,
      0,
      220
     ],
     [
      -41,
      324,
      0,
      617
     ],
     [
      -16,
      321,
      1,
      594
     ],
     [
      387,
      177,
      2,
      362
     ],
     [
      374,
      946,
      0,
      479
     ],
     [
      423,
      230,
      2,
      298
     ],
     [
      234,
      551,
      2,
      320
     ],
     [
      403,
      980,
      1,
      502
     ],
     [
      419,
      201,
      0,
      326
     ],
     [
      353,
      1052,
      0,
      586
     ],
     [
      263,
      687,
      1,
      343
     ],
     [
      425,
      901,
      1,
      420
     ],
     [
      423,
      903,
      1,
      423
     ],
     [
      -93,
      327,
      0,
      666
     ],
     [
      -124,
      288,
      0,
      707
     ],
     [
      422,
      661,
      1,
      206
     ],
     [
      434,
      209,
      1,
      313
     ],
     [
      303,
      789,
      0,
      380
     ],
     [
      193,
      653,
      1,
      388
     ],
     [
      231,
      549,
      2,
      323
     ],
     [
      293,
      784,
      0,
      383
     ],
     [
      410,
      200,
      0,
      331
     ],
     [
      297,
      784,
      0,
      380
     ],
     [
      308,
      789,
      0,
      377
     ],
     [
      320,
      696,
      1,
      302
     ],
     [
      -160,
      269,
      0,
      747
     ],
     [
      507,
      348,
      0,
      158
     ],
     [
      379,
      833,
      2,
      374
     ],
     [
      373,
      852,
      2,
      394
     ],
     [
      381,
      837,
      2,
      377
     ],
     [
      486,
      262,
      1,
      246
     ],
     [
      518,
      255,
      2,
      247
     ],
     [
      362,
      908,
      1,
      449
     ],
     [
      153,
      527,
      0,
      398
     ],
     [
      69,
      552,
      0,
      484
     ],
     [
      92,
      552,
      1,
      461
     ],
     [
      50,
      547,
      0,
      502
     ],
     [
      338,
      167,
      1,
      395
     ],
     [
      1245,
      953,
      0,
      830
     ],
     [
      124,
      549,
      1,
      429
     ],
     [
      89,
      470,
      0,
      462
     ],
     [
      527,
      286,
      2,
      215
     ],
     [
      15,
      539,
      0,
      536
     ],
     [
      296,
      93,
      1,
      480
     ],
     [
      890,
      96,
      0,
      528
     ],
     [
      295,
      548,
      2,
      259
     ],
     [
      288,
      548,
      2,
      266
     ],
     [
      274,
      549,
      2,
      280
     ],
     [
      279,
      549,
      2,
      275
     ],
     [
      251,
      550,
      1,
      303
     ],
     [
      485,
      321,
      0,
      190
     ],
     [
      258,
      551,
      1,
      296
     ],
     [
      225,
      548,
      2,
      329
     ],
     [
      454,
      1043,
      0,
      551
     ],
     [
      64,
      463,
      0,
      487
     ]
    ],
    "prioritari": [
     [
      331,
      683
     ],
     [
      219,
      475
     ],
     [
      492,
      1012
     ],
     [
      381,
      374
     ],
     [
      778,
      469
     ],
     [
      47,
      638
     ],
     [
      262,
      891
     ],
     [
      755,
      291
     ],
     [
      725,
      1084
     ],
     [
      615,
      273
     ],
     [
      122,
      811
     ],
     [
      532,
      729
     ]
    ],
    "legenda": [
     {
      "label": "genug Stellplätze",
      "n": 95,
      "tono": "verde"
     },
     {
      "label": "wenige Stellplätze",
      "n": 111,
      "tono": "giallo"
     },
     {
      "label": "kein Parkplatz",
      "n": 68,
      "tono": "rosso"
     }
    ],
    "didascalia": "Jeder Punkt ist eine wichtige Haltestelle, in Turin und im Umland; die Linie ist die Stadtgrenze. Die schwarzen Kreise sind die 12 Punkte, an denen neue Stellplätze am dringendsten gebraucht würden."
   },
   "pareggio": {
    "a": 24,
    "b": 20
   }
  },
  "numero_pubblico": 4,
  "gruppo": "approfondimento",
  "_nome": "risultato6_riepilogo_mappa.json"
 },
 {
  "risultato": "8",
  "titolo": "Traffico sulle strade e trasporto pubblico",
  "tag": "STIMATO / MISURATO / PROGRAMMATO",
  "stato": "Fatto",
  "in_breve": "Quante auto passano sulle strade grandi di Torino? E dove c'è tanto traffico ma nessun bus, tram o metro comodo, così che l'auto resta l'unica scelta?",
  "domanda": "Sulle strade grandi di Torino, dove c'è molto traffico e poco trasporto pubblico vicino?",
  "numero_chiave": {
   "valore": 95.6,
   "unita": "%",
   "testo": "dei km di strade grandi di Torino hanno fermate frequenti a pochi passi (356,3 km su 372,7)"
  },
  "racconto": "Un primo calcolo trovava 23 strade \"con molto traffico e poco trasporto pubblico\". Ricontrollando, quasi tutte erano un errore di misura: i bus si cercavano lungo la strada per nome invece che per posizione delle fermate (Corso Cairoli risultava senza passaggi). Rifatto il calcolo, la lista si è quasi svuotata: è questa la risposta.",
  "risposta": [
   "Sulle 611 tratte di strade grandi di Torino (372,7 km), il 95,6% della lunghezza ha una fermata con almeno 4 passaggi all'ora entro 300 m, o la metro entro 600 m.",
   "Le tratte con molto traffico (oltre 10.677 veicoli al giorno) sono 204; quelle che hanno anche poco trasporto pubblico sono 5.",
   "In pratica è un solo caso: Corso Regina Margherita verso ovest, il tratto a scorrimento veloce (circa 32.000 veicoli al giorno, nessuna fermata frequente entro 300 m). In più un tratto di Casale, coperto solo per 25% della lunghezza.",
   "I numeri di traffico sono stime: in metà dei casi l'errore è entro ±28%. Servono a ordinare le strade, non a contare i veicoli."
  ],
  "grafici": [
   {
    "tipo": "pila",
    "titolo": "Km di strade grandi di Torino: con o senza trasporto pubblico vicino",
    "unita": "km",
    "voci": [
     {
      "label": "con fermate frequenti vicine",
      "valore": 356.3,
      "tono": "verde"
     },
     {
      "label": "con poco trasporto pubblico",
      "valore": 16.4,
      "tono": "rosso"
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Strade con un sensore: la tratta più carica (veicoli al giorno, 6-21)",
    "unita": "veicoli/giorno",
    "nota": "Solo strade con almeno un sensore sullo stesso asse: senza, il modello mette in cima anche strade poco credibili. \"misurato\" = sensore sulla tratta; le altre sono stime. Corso Unione Sovietica è probabilmente sovrastimato: dove c'è il sensore il modello dava quasi il triplo del misurato.",
    "voci": [
     {
      "label": "Unità d'Italia",
      "valore": 52296
     },
     {
      "label": "Orbassano (misurato)",
      "valore": 50322
     },
     {
      "label": "Regina Margherita",
      "valore": 48739
     },
     {
      "label": "Unione Sovietica",
      "valore": 48567
     },
     {
      "label": "Francia",
      "valore": 39243
     },
     {
      "label": "Giulio Cesare",
      "valore": 37396
     },
     {
      "label": "Giovanni Agnelli",
      "valore": 34034
     },
     {
      "label": "Asse di Penetrazione Urbana di Corso Regina Margherita",
      "valore": 31205
     },
     {
      "label": "Strada di Settimo (misurato)",
      "valore": 29926
     },
     {
      "label": "Quattro Novembre",
      "valore": 25977
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Prova del modello sui 22 sensori: misurato e stimato",
    "unita": "veicoli/giorno",
    "nota": "Barra chiara = misurato dal sensore, barra scura = stima del modello senza usare quel sensore.",
    "voci": [
     {
      "label": "Corso Unità d'Italia",
      "valore": 54449,
      "prima": 81956
     },
     {
      "label": "Corso Trieste",
      "valore": 49617,
      "prima": 65424
     },
     {
      "label": "Corso Orbassano",
      "valore": 49916,
      "prima": 50322
     },
     {
      "label": "Corso Unità d'Italia",
      "valore": 48344,
      "prima": 47616
     },
     {
      "label": "Corso Orbassano",
      "valore": 46751,
      "prima": 41326
     },
     {
      "label": "R24 Raccordo Torino-Aeroporto Caselle",
      "valore": 27103,
      "prima": 39810
     },
     {
      "label": "Corso Giulio Cesare",
      "valore": 24579,
      "prima": 34548
     },
     {
      "label": "Corso Francia",
      "valore": 38311,
      "prima": 30938
     },
     {
      "label": "Ponte Amedeo VIII",
      "valore": 26625,
      "prima": 29926
     },
     {
      "label": "Corso Giulio Cesare",
      "valore": 36474,
      "prima": 29270
     },
     {
      "label": "Corso Francia",
      "valore": 39197,
      "prima": 28414
     },
     {
      "label": "Corso Regina Margherita",
      "valore": 30585,
      "prima": 28412
     },
     {
      "label": "Corso Orbassano",
      "valore": 44057,
      "prima": 27024
     },
     {
      "label": "Corso Vercelli",
      "valore": 9941,
      "prima": 25470
     },
     {
      "label": "Corso Agnelli",
      "valore": 31592,
      "prima": 22014
     },
     {
      "label": "SP8 di Druento",
      "valore": 10514,
      "prima": 20611
     },
     {
      "label": "Corso Regina Margherita",
      "valore": 25497,
      "prima": 19954
     },
     {
      "label": "Corso Unione Sovietica",
      "valore": 53830,
      "prima": 19202
     },
     {
      "label": "Corso Sebastopoli",
      "valore": 28273,
      "prima": 17424
     },
     {
      "label": "Strada Di Settimo",
      "valore": 12280,
      "prima": 16856
     },
     {
      "label": "SP1 delle Valli di Lanzo",
      "valore": 6438,
      "prima": 15097
     },
     {
      "label": "Corso Allamano",
      "valore": 11620,
      "prima": 12820
     }
    ]
   },
   {
    "tipo": "barre",
    "titolo": "Errore della stima su ogni sensore (%)",
    "unita": "%",
    "nota": "Errore = |stimato − misurato| / misurato. Metà dei sensori sotto il valore tipico, gli altri sopra.",
    "voci": [
     {
      "label": "Corso Orbassano",
      "valore": 1,
      "tono": "rosso"
     },
     {
      "label": "Corso Unità d'Italia",
      "valore": 2,
      "tono": "rosso"
     },
     {
      "label": "Corso Regina Margherita",
      "valore": 8,
      "tono": "rosso"
     },
     {
      "label": "Corso Allamano",
      "valore": 9,
      "tono": "rosso"
     },
     {
      "label": "Ponte Amedeo VIII",
      "valore": 11,
      "tono": "rosso"
     },
     {
      "label": "Corso Orbassano",
      "valore": 13,
      "tono": "rosso"
     },
     {
      "label": "Corso Francia",
      "valore": 24,
      "tono": "rosso"
     },
     {
      "label": "Corso Trieste",
      "valore": 24,
      "tono": "rosso"
     },
     {
      "label": "Corso Giulio Cesare",
      "valore": 25,
      "tono": "rosso"
     },
     {
      "label": "Strada Di Settimo",
      "valore": 27,
      "tono": "rosso"
     },
     {
      "label": "Corso Regina Margherita",
      "valore": 28,
      "tono": "rosso"
     },
     {
      "label": "Corso Giulio Cesare",
      "valore": 29,
      "tono": "rosso"
     },
     {
      "label": "R24 Raccordo Torino-Aeroporto Caselle",
      "valore": 32,
      "tono": "rosso"
     },
     {
      "label": "Corso Unità d'Italia",
      "valore": 34,
      "tono": "rosso"
     },
     {
      "label": "Corso Francia",
      "valore": 38,
      "tono": "rosso"
     },
     {
      "label": "Corso Agnelli",
      "valore": 44,
      "tono": "rosso"
     },
     {
      "label": "SP8 di Druento",
      "valore": 49,
      "tono": "rosso"
     },
     {
      "label": "SP1 delle Valli di Lanzo",
      "valore": 57,
      "tono": "rosso"
     },
     {
      "label": "Corso Vercelli",
      "valore": 61,
      "tono": "rosso"
     },
     {
      "label": "Corso Sebastopoli",
      "valore": 62,
      "tono": "rosso"
     },
     {
      "label": "Corso Orbassano",
      "valore": 63,
      "tono": "rosso"
     },
     {
      "label": "Corso Unione Sovietica",
      "valore": 180,
      "tono": "rosso"
     }
    ]
   }
  ],
  "metodo": [
   "Domanda: gli spostamenti in auto dell'indagine sugli spostamenti 2022 (residenti, giorno feriale), assegnati alla strada più veloce sulla rete di OpenStreetMap.",
   "Taratura su 22 punti di misura dei sensori 5T: un solo fattore per tutta la città, provato togliendo un sensore alla volta e stimandolo con gli altri.",
   "Strade come assi: un corso che cambia nome o comune resta la stessa strada, tagliata in tratte da 300 m a 1,5 km. Strade grandi = Torino, importanza alta o strade principali, almeno 300 m, senza tangenziale e raccordi.",
   "Trasporto pubblico per posizione delle fermate, mai per nome: una tratta è servita dove c'è una fermata con almeno 4 passaggi all'ora entro 300 m (orario ufficiale, mercoledì 14/10), o la metro entro 600 m. Poco trasporto pubblico = servita per metà della lunghezza o meno.",
   "Molto traffico = il terzo più alto delle tratte. Il modello è quello più ricco (attrazioni, code, ZTL): con i sensori di ottobre sbaglia meno di quello semplice (errore tipico 28% contro 38%), secondo una regola fissata prima."
  ],
  "parametri": [
   [
    "Strade grandi di Torino",
    "611 tratte, 372,7 km"
   ],
   [
    "Errore tipico (metà dei casi)",
    "±28% (9 volte su 10 entro ±62%)"
   ],
   [
    "Ordine giusto delle strade (Spearman)",
    "0,64"
   ],
   [
    "Validato tra",
    "9.000 e 107.000 veicoli/giorno"
   ],
   [
    "Soglia 'molto traffico'",
    "10.677 veicoli/giorno"
   ],
   [
    "Confronto con chi conosce la città",
    "11 strade su 18 nella fascia giusta, 5 confronti su 7 (solo controllo)"
   ]
  ],
  "limiti": [
   "Stima debole: errore tipico ±28% e intervallo d'incertezza largo (da 24% a 38%). Alcune strade sono molto sbagliate (Corso Unione Sovietica, Corso Sebastopoli): buona per ordinare, non per contare.",
   "Solo 22 punti di misura, quasi tutti su corsi trafficati: sotto circa 9.000 veicoli al giorno la stima non è verificata.",
   "Solo i residenti tra 11 e 84 anni (indagine sugli spostamenti): mancano merci, turisti e chi viene da fuori. Il modello non sa fare le code: l'ora di punta non è verificata.",
   "Trasporto pubblico programmato: niente ritardi né affollamento. Il centro (ZTL, aree pedonali) non è stimato bene.",
   "Il valore è per i due versi: sulle poche vie a senso unico vero potrebbe essere il doppio del reale.",
   "Il tratto di Corso Moncalieri va controllato a mano: una fermata con 26 passaggi all'ora è a 40 m, ma copre solo un quarto della tratta."
  ],
  "in_english": [
   "Question: on Turin's major roads, where is there a lot of traffic and little public transport nearby?",
   "Of 611 road sections on Turin's major roads (372.7 km), 95.6% of the length has a frequent stop (at least 4 departures an hour) within 300 m, or the metro within 600 m. Heavy-traffic sections (over 10,677 vehicles a day): 204; of these, 5 also have little public transport.",
   "In practice this is one main case: Corso Regina Margherita westbound, a fast road with no frequent stop within 300 m, plus one stretch of Corso Moncalieri covered for only a quarter of its length.",
   "Limits: traffic figures are estimates with a typical error of ±28%; use them to rank the roads, not to count vehicles."
  ],
  "mappa": {
   "id": "imq",
   "tema": "Spostamenti",
   "nota": "Nella mappa, tema «Spostamenti»: quanti spostamenti partono da ogni zona e dove vanno (indagine 2022, feriale)."
  },
  "fonti": [
   "docs/en/METHODS.md",
   "data/processed/risultato8_traffico_tp_v2.json"
  ],
  "generato": "2026-10-26T14:06:29+00:00",
  "avviso": [
   "Traffico stimato, sensori 5T misurati, orari GTT programmati",
   "Traffico stimato con un modello tarato su 22 sensori: errore tipico ±28%. Trasporto pubblico = fermate con almeno 4 passaggi all'ora entro 300 m o metro entro 600 m."
  ],
  "scenari": [
   {
    "nome": "Oggi",
    "numeri": [
     {
      "label": "Km di strade grandi di Torino",
      "prima": null,
      "dopo": 372.7,
      "unita": "km"
     },
     {
      "label": "Con fermate frequenti vicine",
      "prima": null,
      "dopo": 95.6,
      "unita": "%"
     },
     {
      "label": "Tratte con molto traffico",
      "prima": null,
      "dopo": 204,
      "unita": "tratte"
     },
     {
      "label": "Molto traffico e poco trasporto pubblico",
      "prima": null,
      "dopo": 5,
      "unita": "tratte"
     },
     {
      "label": "Errore tipico della stima",
      "prima": null,
      "dopo": 28,
      "unita": "%"
     }
    ],
    "nota": "Le 5 tratte sono quasi tutte su Corso Regina Margherita ovest; una su Corso Moncalieri."
   }
  ],
  "forma": {
   "tipo_dato": "Tipo di dato: calcolato da dati veri, con tempi in auto col traffico tipico, misure dei sensori e orari ufficiali dei mezzi.",
   "titolo": "Al mattino, coi mezzi pubblici si impiega da 1,9 a 2,4 volte il tempo dell'auto",
   "domanda": "Al mattino, quanto ci si mette in più coi mezzi pubblici che in auto?",
   "numero": {
    "valore": "1,9–2,4",
    "unita": "volte",
    "testo": "il tempo dell'auto, per i viaggi in auto del mattino fra zone diverse",
    "breve": "il tempo dell'auto, coi mezzi pubblici"
   },
   "principale": {
    "tipo": "barre",
    "titolo": "Auto del mattino, per quante volte i mezzi pubblici impiegano più dell'auto",
    "unita": "%",
    "max": 100,
    "nota": "Ogni barra è una fascia: coi mezzi pubblici si impiega quel multiplo del tempo in auto. Barra scura: stima aperta; barra chiara: la stessa stima corretta col controllo. Coppie Torino-Torino e Torino-cintura.",
    "voci": [
     {
      "label": "meno di 1,5 volte",
      "valore": 1,
      "prima": 5,
      "tono": "verde",
      "testo": "1–5% (2.321–10.933 auto)"
     },
     {
      "label": "da 1,5 a 2 volte",
      "valore": 12,
      "prima": 57,
      "tono": "giallo",
      "testo": "12–57% (27.510–125.901 auto)"
     },
     {
      "label": "da 2 a 3 volte",
      "valore": 81,
      "prima": 37,
      "tono": "arancio",
      "testo": "37–81% (81.062–177.478 auto)"
     },
     {
      "label": "oltre 3 volte",
      "valore": 6,
      "prima": 1,
      "tono": "rosso",
      "testo": "1–6% (2.411–12.997 auto)"
     }
    ]
   },
   "punti": [
    "Si risparmiano 14-19 minuti a viaggio, ma la sosta costa ~270 euro al mese. È come pagare il tempo 20-30 euro l'ora.",
    "Senza sosta da pagare, l'auto costa meno dell'abbonamento fino a ~7 km.",
    "Un tragitto frequente tipico: Crocetta → Centro, ~23 minuti coi mezzi contro 11–13 in auto."
   ],
   "altri": [
    {
     "tipo": "linea",
     "titolo": "Quante volte il tempo dell'auto, ora per ora",
     "unita": "volte",
     "nota": "Rapporto fra il tempo coi mezzi e il tempo in auto, pesato per le auto del mattino, alle 4 ore del giorno: stima aperta e stessa stima corretta col controllo.",
     "categorie": [
      "8:00",
      "13:00",
      "17:30",
      "21:00"
     ],
     "serie": [
      {
       "label": "stima aperta",
       "valori": [
        2.4,
        2.5,
        2.4,
        2.8
       ]
      },
      {
       "label": "corretta col controllo",
       "valori": [
        1.9,
        2.1,
        2.0,
        2.3
       ]
      }
     ]
    },
    {
     "tipo": "gara",
     "titolo": "I viaggi in auto più frequenti del mattino: bus contro auto",
     "luoghi": [
      {
       "nome": "Crocetta",
       "arrivo": "Centro",
       "bus": 22.8,
       "auto_min": 11.1,
       "auto_max": 13.0,
       "giudizio": "coi mezzi 1,8–2 volte il tempo dell'auto"
      },
      {
       "nome": "San Paolo",
       "arrivo": "Centro",
       "bus": 33.9,
       "auto_min": 15.0,
       "auto_max": 18.1,
       "giudizio": "coi mezzi 1,9–2,3 volte il tempo dell'auto"
      },
      {
       "nome": "Mirafiori Nord",
       "arrivo": "Santa Rita",
       "bus": 21.3,
       "auto_min": 10.4,
       "auto_max": 12.1,
       "giudizio": "coi mezzi 1,8–2 volte il tempo dell'auto"
      },
      {
       "nome": "Parella",
       "arrivo": "Centro",
       "bus": 27.0,
       "auto_min": 17.0,
       "auto_max": 20.7,
       "giudizio": "coi mezzi 1,3–1,6 volte il tempo dell'auto"
      },
      {
       "nome": "San Donato",
       "arrivo": "Centro",
       "bus": 20.8,
       "auto_min": 12.5,
       "auto_max": 14.8,
       "giudizio": "coi mezzi 1,4–1,7 volte il tempo dell'auto"
      },
      {
       "nome": "Barriera di Milano",
       "arrivo": "Falchera",
       "bus": 26.2,
       "auto_min": 13.1,
       "auto_max": 15.6,
       "giudizio": "coi mezzi 1,7–2 volte il tempo dell'auto"
      }
     ],
     "scelto": 0,
     "nota": "Bus e auto partono insieme, uno dopo l'altro, per i 6 viaggi in auto più frequenti del mattino. L'auto ha un tempo con la forbice del controllo, parcheggio compreso."
    },
    {
     "tipo": "barre_gruppi",
     "titolo": "Un mese di lavoro vicino al centro: quanto costa",
     "unita": "euro",
     "nota": "La barra chiara è il costo pieno dell'auto (ACI). Le tariffe agevolate sono quelle GTT per giovani e anziani, con certificato ISEE.",
     "gruppi": [
      {
       "label": "Auto, sosta pagata in strada",
       "voci": [
        {
         "label": "Carburante e sosta",
         "valore": 307,
         "prima": 404,
         "tono": "rosso",
         "testo": "307 (404 col costo pieno)"
        }
       ]
      },
      {
       "label": "Auto, parcheggio gratis al lavoro",
       "voci": [
        {
         "label": "Solo carburante",
         "valore": 35,
         "prima": 132,
         "tono": "rosso",
         "testo": "35 (132 col costo pieno)"
        }
       ]
      },
      {
       "label": "Mezzi pubblici",
       "voci": [
        {
         "label": "Biglietti (40 viaggi)",
         "valore": 80,
         "tono": "verde",
         "testo": "80"
        },
        {
         "label": "Abbonamento mensile",
         "valore": 38,
         "tono": "verde",
         "testo": "38"
        },
        {
         "label": "Abbonamento annuale, al mese",
         "valore": 26,
         "tono": "verde",
         "testo": "26"
        }
       ]
      }
     ]
    },
    {
     "tipo": "dispersione",
     "titolo": "Tempo in auto e tempo coi mezzi pubblici, una coppia di zone per punto",
     "xlabel": "minuti in auto (mattino, stima aperta)",
     "ylabel": "minuti coi mezzi pubblici",
     "punti": [
      [
       11.1,
       22.8,
       1355.3
      ],
      [
       15.0,
       33.9,
       1341.8
      ],
      [
       10.4,
       21.3,
       1324.4
      ],
      [
       17.0,
       27.0,
       1277.0
      ],
      [
       12.5,
       20.8,
       1269.4
      ],
      [
       13.1,
       26.2,
       1208.2
      ],
      [
       19.3,
       46.0,
       1149.2
      ],
      [
       15.9,
       40.2,
       1107.8
      ],
      [
       39.0,
       84.3,
       1081.8
      ],
      [
       9.6,
       17.2,
       1038.1
      ],
      [
       15.8,
       35.8,
       969.9
      ],
      [
       15.0,
       33.1,
       968.1
      ],
      [
       9.4,
       17.2,
       957.2
      ],
      [
       23.9,
       47.5,
       940.7
      ],
      [
       11.1,
       22.4,
       938.8
      ],
      [
       15.0,
       36.1,
       928.7
      ],
      [
       16.8,
       40.9,
       916.7
      ],
      [
       31.3,
       67.0,
       910.0
      ],
      [
       15.1,
       32.9,
       900.6
      ],
      [
       14.9,
       37.8,
       894.4
      ],
      [
       11.7,
       24.6,
       893.3
      ],
      [
       12.2,
       26.1,
       889.9
      ],
      [
       19.8,
       42.1,
       888.0
      ],
      [
       17.0,
       29.9,
       818.9
      ],
      [
       21.0,
       45.2,
       796.7
      ],
      [
       17.5,
       37.9,
       795.1
      ],
      [
       10.1,
       21.0,
       789.0
      ],
      [
       17.3,
       33.8,
       779.1
      ],
      [
       14.0,
       32.9,
       762.5
      ],
      [
       22.0,
       53.2,
       753.4
      ],
      [
       11.6,
       33.8,
       751.2
      ],
      [
       12.6,
       26.6,
       737.2
      ],
      [
       22.3,
       85.6,
       718.7
      ],
      [
       10.4,
       20.2,
       714.6
      ],
      [
       15.1,
       37.9,
       714.1
      ],
      [
       11.7,
       26.2,
       706.6
      ],
      [
       30.3,
       67.1,
       702.1
      ],
      [
       12.0,
       24.8,
       698.0
      ],
      [
       17.0,
       32.2,
       696.9
      ],
      [
       26.1,
       53.5,
       690.4
      ],
      [
       28.6,
       76.6,
       687.3
      ],
      [
       12.3,
       25.4,
       685.0
      ],
      [
       20.4,
       27.8,
       672.4
      ],
      [
       14.8,
       31.7,
       671.0
      ],
      [
       11.0,
       25.1,
       666.8
      ],
      [
       32.5,
       76.4,
       659.4
      ],
      [
       21.9,
       54.2,
       644.0
      ],
      [
       14.0,
       35.3,
       627.3
      ],
      [
       9.5,
       18.0,
       622.4
      ],
      [
       11.8,
       24.5,
       620.3
      ],
      [
       13.1,
       29.6,
       615.4
      ],
      [
       17.0,
       39.7,
       614.3
      ],
      [
       14.9,
       37.2,
       614.1
      ],
      [
       12.7,
       25.7,
       607.7
      ],
      [
       13.7,
       29.6,
       606.6
      ],
      [
       14.4,
       36.6,
       601.6
      ],
      [
       11.4,
       32.9,
       592.7
      ],
      [
       16.2,
       38.7,
       589.8
      ],
      [
       15.3,
       36.7,
       582.5
      ],
      [
       21.7,
       53.3,
       580.1
      ],
      [
       15.7,
       26.4,
       574.5
      ],
      [
       13.4,
       32.4,
       570.6
      ],
      [
       18.9,
       58.4,
       568.2
      ],
      [
       14.1,
       26.9,
       562.6
      ],
      [
       28.3,
       90.1,
       543.7
      ],
      [
       13.7,
       26.4,
       543.0
      ],
      [
       16.7,
       42.0,
       540.9
      ],
      [
       10.3,
       23.8,
       540.3
      ],
      [
       13.9,
       33.4,
       539.8
      ],
      [
       15.6,
       33.2,
       527.7
      ],
      [
       29.7,
       72.6,
       520.3
      ],
      [
       26.9,
       75.5,
       519.9
      ],
      [
       13.2,
       31.9,
       519.7
      ],
      [
       12.0,
       27.2,
       517.1
      ],
      [
       25.0,
       60.3,
       515.6
      ],
      [
       31.3,
       75.0,
       514.3
      ],
      [
       15.2,
       42.4,
       512.4
      ],
      [
       27.8,
       65.7,
       504.1
      ],
      [
       14.0,
       29.3,
       503.9
      ],
      [
       16.2,
       35.3,
       498.7
      ],
      [
       14.6,
       31.3,
       496.3
      ],
      [
       9.5,
       17.5,
       494.3
      ],
      [
       20.3,
       50.2,
       490.1
      ],
      [
       18.7,
       41.5,
       489.2
      ],
      [
       11.0,
       25.5,
       488.9
      ],
      [
       34.4,
       77.9,
       488.2
      ],
      [
       11.8,
       24.2,
       481.0
      ],
      [
       16.4,
       40.9,
       478.8
      ],
      [
       23.9,
       58.2,
       478.7
      ],
      [
       21.2,
       50.6,
       476.8
      ],
      [
       19.8,
       48.9,
       467.9
      ],
      [
       12.7,
       28.5,
       466.7
      ],
      [
       14.6,
       30.1,
       462.0
      ],
      [
       13.0,
       28.7,
       459.7
      ],
      [
       41.1,
       81.8,
       458.7
      ],
      [
       20.0,
       28.4,
       458.5
      ],
      [
       17.6,
       39.9,
       456.6
      ],
      [
       13.5,
       25.1,
       456.0
      ],
      [
       26.4,
       60.5,
       454.7
      ],
      [
       10.8,
       22.5,
       452.9
      ],
      [
       22.2,
       57.3,
       452.3
      ],
      [
       35.8,
       90.3,
       449.8
      ],
      [
       14.3,
       34.2,
       448.6
      ],
      [
       35.1,
       97.3,
       448.4
      ],
      [
       25.9,
       75.7,
       445.5
      ],
      [
       17.7,
       38.5,
       443.8
      ],
      [
       25.0,
       49.5,
       442.8
      ],
      [
       17.9,
       43.0,
       439.9
      ],
      [
       21.9,
       58.6,
       438.4
      ],
      [
       11.7,
       23.6,
       437.5
      ],
      [
       25.9,
       65.4,
       431.9
      ],
      [
       24.1,
       61.7,
       431.8
      ],
      [
       14.7,
       34.8,
       431.4
      ],
      [
       27.3,
       72.4,
       428.4
      ],
      [
       16.6,
       40.1,
       428.4
      ],
      [
       33.2,
       85.5,
       426.2
      ],
      [
       14.6,
       38.4,
       423.2
      ],
      [
       18.7,
       44.2,
       422.6
      ],
      [
       11.4,
       20.3,
       421.9
      ],
      [
       20.8,
       50.7,
       421.1
      ],
      [
       10.7,
       21.2,
       419.2
      ],
      [
       21.6,
       56.7,
       411.0
      ],
      [
       35.1,
       77.4,
       410.3
      ],
      [
       19.5,
       57.1,
       410.0
      ],
      [
       24.3,
       35.3,
       409.6
      ],
      [
       21.8,
       56.8,
       409.5
      ],
      [
       24.5,
       54.4,
       404.3
      ],
      [
       24.9,
       49.2,
       403.5
      ],
      [
       22.7,
       57.8,
       402.7
      ],
      [
       26.9,
       64.7,
       399.0
      ],
      [
       12.2,
       27.2,
       398.4
      ],
      [
       26.5,
       68.0,
       396.9
      ],
      [
       12.1,
       30.8,
       396.9
      ],
      [
       25.1,
       63.1,
       395.5
      ],
      [
       16.6,
       34.9,
       391.8
      ],
      [
       25.3,
       54.3,
       389.9
      ],
      [
       22.4,
       49.6,
       389.6
      ],
      [
       38.5,
       108.8,
       386.9
      ],
      [
       16.9,
       30.4,
       386.6
      ],
      [
       13.6,
       30.6,
       384.3
      ],
      [
       15.3,
       29.9,
       383.2
      ],
      [
       18.6,
       85.7,
       383.2
      ],
      [
       24.5,
       65.9,
       382.4
      ],
      [
       22.1,
       59.9,
       382.0
      ],
      [
       20.2,
       57.4,
       379.4
      ],
      [
       18.2,
       41.2,
       377.6
      ],
      [
       14.6,
       34.0,
       377.4
      ],
      [
       15.1,
       26.6,
       376.5
      ],
      [
       14.8,
       39.4,
       369.2
      ],
      [
       16.3,
       33.1,
       368.7
      ],
      [
       18.4,
       39.8,
       367.3
      ],
      [
       19.1,
       46.3,
       366.6
      ],
      [
       24.4,
       83.3,
       365.7
      ],
      [
       12.1,
       21.4,
       365.5
      ],
      [
       26.6,
       78.5,
       363.3
      ],
      [
       13.4,
       30.6,
       362.7
      ],
      [
       10.1,
       23.1,
       356.4
      ],
      [
       12.0,
       23.6,
       355.0
      ],
      [
       17.5,
       41.9,
       353.0
      ],
      [
       20.4,
       55.6,
       352.5
      ],
      [
       15.7,
       19.2,
       352.1
      ],
      [
       24.3,
       53.7,
       350.1
      ],
      [
       15.2,
       39.7,
       348.3
      ],
      [
       19.6,
       47.8,
       347.8
      ],
      [
       34.4,
       75.3,
       346.3
      ],
      [
       27.2,
       75.0,
       346.1
      ],
      [
       24.6,
       67.1,
       345.7
      ],
      [
       16.2,
       34.6,
       340.6
      ],
      [
       14.5,
       44.7,
       340.0
      ],
      [
       21.6,
       53.8,
       339.6
      ],
      [
       35.5,
       87.3,
       338.3
      ],
      [
       18.8,
       48.7,
       336.5
      ],
      [
       21.0,
       57.6,
       336.5
      ],
      [
       33.3,
       83.6,
       335.5
      ],
      [
       21.2,
       55.3,
       335.0
      ],
      [
       26.5,
       64.1,
       333.8
      ],
      [
       33.7,
       92.2,
       333.6
      ],
      [
       32.9,
       78.5,
       333.5
      ],
      [
       17.3,
       34.0,
       332.2
      ],
      [
       29.9,
       87.0,
       331.5
      ],
      [
       29.1,
       50.7,
       331.5
      ],
      [
       22.9,
       68.0,
       330.5
      ],
      [
       21.6,
       55.6,
       329.9
      ],
      [
       26.0,
       46.5,
       329.1
      ],
      [
       31.7,
       69.2,
       328.2
      ],
      [
       24.3,
       57.5,
       328.0
      ],
      [
       19.5,
       57.5,
       326.5
      ],
      [
       31.4,
       70.9,
       323.5
      ],
      [
       11.9,
       26.3,
       322.3
      ],
      [
       9.6,
       21.3,
       322.1
      ],
      [
       31.3,
       67.9,
       321.4
      ],
      [
       16.5,
       36.7,
       318.2
      ],
      [
       24.7,
       50.9,
       317.7
      ],
      [
       27.8,
       84.8,
       311.9
      ],
      [
       34.6,
       98.7,
       310.7
      ],
      [
       12.8,
       28.7,
       309.9
      ],
      [
       27.6,
       63.7,
       307.1
      ],
      [
       29.5,
       73.7,
       306.3
      ],
      [
       12.0,
       27.4,
       305.1
      ],
      [
       16.9,
       38.5,
       304.4
      ],
      [
       23.3,
       56.3,
       304.2
      ],
      [
       19.5,
       55.6,
       303.6
      ],
      [
       29.6,
       66.2,
       303.4
      ],
      [
       32.9,
       81.1,
       302.8
      ],
      [
       30.7,
       72.6,
       302.3
      ],
      [
       32.1,
       76.2,
       300.8
      ],
      [
       12.4,
       21.2,
       299.5
      ],
      [
       20.1,
       52.0,
       299.2
      ],
      [
       24.2,
       59.8,
       298.9
      ],
      [
       20.6,
       50.3,
       298.6
      ],
      [
       21.6,
       57.6,
       297.1
      ],
      [
       20.5,
       57.4,
       296.5
      ],
      [
       24.8,
       61.1,
       296.0
      ],
      [
       37.3,
       91.2,
       295.0
      ],
      [
       32.0,
       73.8,
       294.0
      ],
      [
       14.8,
       36.4,
       292.7
      ],
      [
       40.4,
       90.1,
       291.8
      ],
      [
       20.0,
       49.0,
       290.8
      ],
      [
       11.2,
       23.5,
       290.5
      ],
      [
       24.9,
       63.7,
       289.4
      ],
      [
       24.4,
       56.0,
       288.9
      ],
      [
       32.3,
       78.6,
       288.6
      ],
      [
       13.9,
       37.7,
       284.7
      ],
      [
       16.7,
       41.4,
       283.1
      ],
      [
       9.7,
       21.0,
       282.6
      ],
      [
       17.7,
       45.6,
       282.2
      ],
      [
       20.5,
       45.1,
       281.8
      ],
      [
       14.5,
       41.1,
       281.7
      ],
      [
       21.3,
       60.8,
       280.3
      ],
      [
       21.7,
       60.1,
       278.1
      ],
      [
       13.7,
       26.8,
       274.9
      ],
      [
       31.8,
       87.3,
       274.4
      ],
      [
       27.5,
       71.7,
       273.4
      ],
      [
       15.9,
       37.2,
       273.2
      ],
      [
       28.0,
       49.1,
       272.4
      ],
      [
       37.5,
       80.6,
       271.8
      ],
      [
       35.4,
       83.1,
       271.3
      ],
      [
       23.9,
       64.9,
       271.0
      ],
      [
       15.7,
       34.4,
       270.6
      ],
      [
       12.6,
       26.9,
       270.2
      ],
      [
       23.3,
       47.1,
       270.1
      ],
      [
       34.1,
       103.0,
       269.7
      ],
      [
       23.4,
       65.7,
       269.7
      ],
      [
       34.4,
       87.9,
       268.9
      ],
      [
       15.4,
       19.2,
       268.5
      ],
      [
       24.6,
       58.6,
       267.8
      ],
      [
       20.8,
       39.8,
       264.3
      ],
      [
       25.4,
       63.9,
       263.3
      ],
      [
       20.3,
       54.6,
       262.3
      ],
      [
       21.6,
       45.1,
       261.5
      ],
      [
       24.1,
       52.6,
       261.2
      ],
      [
       15.6,
       37.4,
       260.2
      ],
      [
       9.9,
       19.5,
       259.7
      ],
      [
       12.6,
       31.5,
       258.2
      ],
      [
       41.0,
       83.5,
       257.3
      ],
      [
       20.7,
       49.6,
       256.8
      ],
      [
       32.7,
       79.8,
       255.1
      ],
      [
       40.9,
       82.4,
       254.4
      ],
      [
       36.4,
       108.1,
       253.6
      ],
      [
       44.3,
       93.4,
       253.1
      ],
      [
       9.0,
       17.9,
       252.2
      ],
      [
       24.9,
       52.5,
       251.6
      ],
      [
       13.3,
       32.4,
       251.5
      ],
      [
       23.2,
       59.9,
       250.1
      ],
      [
       23.0,
       40.0,
       248.3
      ],
      [
       26.8,
       51.9,
       247.4
      ],
      [
       17.3,
       37.4,
       244.8
      ],
      [
       13.8,
       31.3,
       243.9
      ],
      [
       22.5,
       47.1,
       243.6
      ],
      [
       25.2,
       58.3,
       243.6
      ],
      [
       14.3,
       31.7,
       243.6
      ],
      [
       20.5,
       44.6,
       243.0
      ],
      [
       34.1,
       82.0,
       242.3
      ],
      [
       22.5,
       46.3,
       242.2
      ],
      [
       25.7,
       65.1,
       241.4
      ],
      [
       15.1,
       32.9,
       241.0
      ],
      [
       35.0,
       96.0,
       240.6
      ],
      [
       13.1,
       42.2,
       240.0
      ],
      [
       28.0,
       68.6,
       238.3
      ],
      [
       29.8,
       76.0,
       236.1
      ],
      [
       16.1,
       26.5,
       235.8
      ],
      [
       24.7,
       49.4,
       234.9
      ],
      [
       24.5,
       55.7,
       234.7
      ],
      [
       22.2,
       49.4,
       234.6
      ],
      [
       19.7,
       49.7,
       233.6
      ],
      [
       25.4,
       71.4,
       233.3
      ],
      [
       17.9,
       46.3,
       231.7
      ],
      [
       26.2,
       65.0,
       231.5
      ],
      [
       44.7,
       104.4,
       230.9
      ],
      [
       23.3,
       51.1,
       228.8
      ],
      [
       12.5,
       27.7,
       228.3
      ],
      [
       18.2,
       44.5,
       228.1
      ],
      [
       25.1,
       66.4,
       227.0
      ],
      [
       25.4,
       83.3,
       226.3
      ],
      [
       16.1,
       38.8,
       225.6
      ],
      [
       28.4,
       62.5,
       225.4
      ],
      [
       21.2,
       55.2,
       225.1
      ],
      [
       27.6,
       68.5,
       224.1
      ],
      [
       11.6,
       26.4,
       223.2
      ],
      [
       34.9,
       98.9,
       222.3
      ],
      [
       15.3,
       34.7,
       222.1
      ],
      [
       32.6,
       74.6,
       221.0
      ],
      [
       11.7,
       28.3,
       220.4
      ],
      [
       14.5,
       26.5,
       219.8
      ],
      [
       13.7,
       24.6,
       218.7
      ],
      [
       23.6,
       56.1,
       218.3
      ],
      [
       24.6,
       79.5,
       217.8
      ],
      [
       32.8,
       72.3,
       217.1
      ],
      [
       15.2,
       33.3,
       216.9
      ],
      [
       34.1,
       109.0,
       216.3
      ],
      [
       34.5,
       64.5,
       215.9
      ],
      [
       25.6,
       75.8,
       215.8
      ],
      [
       39.3,
       101.7,
       215.6
      ],
      [
       22.1,
       57.2,
       215.3
      ],
      [
       26.0,
       70.8,
       214.1
      ],
      [
       20.9,
       54.8,
       214.0
      ],
      [
       13.1,
       28.4,
       213.2
      ],
      [
       27.3,
       76.3,
       212.7
      ],
      [
       33.1,
       82.6,
       212.0
      ],
      [
       29.0,
       97.7,
       211.8
      ],
      [
       32.3,
       67.5,
       211.3
      ],
      [
       18.0,
       53.4,
       211.2
      ],
      [
       27.2,
       64.6,
       210.7
      ],
      [
       25.5,
       61.2,
       209.8
      ],
      [
       20.0,
       46.2,
       209.0
      ],
      [
       20.4,
       54.4,
       208.2
      ],
      [
       46.3,
       107.6,
       208.1
      ],
      [
       25.3,
       64.8,
       207.6
      ],
      [
       41.6,
       90.9,
       207.5
      ],
      [
       16.3,
       32.5,
       206.7
      ],
      [
       40.9,
       86.5,
       206.4
      ],
      [
       20.1,
       47.2,
       206.2
      ],
      [
       20.1,
       54.1,
       206.2
      ],
      [
       19.7,
       47.3,
       206.1
      ],
      [
       31.8,
       70.2,
       206.0
      ],
      [
       18.5,
       58.7,
       205.9
      ],
      [
       30.0,
       101.0,
       205.6
      ],
      [
       26.3,
       60.0,
       205.0
      ],
      [
       21.9,
       44.5,
       204.7
      ],
      [
       24.8,
       79.7,
       204.3
      ],
      [
       30.1,
       60.0,
       204.3
      ],
      [
       34.0,
       82.1,
       204.0
      ],
      [
       35.1,
       81.4,
       203.9
      ],
      [
       21.8,
       60.5,
       203.8
      ],
      [
       26.9,
       96.1,
       203.7
      ],
      [
       18.5,
       46.6,
       203.5
      ],
      [
       19.5,
       45.5,
       203.4
      ],
      [
       35.1,
       78.0,
       203.4
      ],
      [
       20.8,
       49.8,
       203.2
      ],
      [
       37.3,
       88.7,
       202.3
      ],
      [
       27.3,
       71.2,
       201.9
      ],
      [
       29.3,
       61.9,
       201.7
      ],
      [
       23.5,
       57.6,
       201.5
      ],
      [
       15.4,
       28.5,
       201.5
      ],
      [
       16.3,
       29.3,
       201.2
      ],
      [
       18.6,
       45.7,
       200.7
      ],
      [
       29.5,
       65.4,
       200.5
      ],
      [
       33.6,
       86.4,
       200.3
      ],
      [
       26.0,
       90.0,
       199.7
      ],
      [
       14.4,
       29.3,
       199.4
      ],
      [
       13.7,
       33.4,
       199.3
      ],
      [
       26.6,
       58.8,
       198.8
      ],
      [
       30.9,
       59.8,
       197.7
      ],
      [
       32.0,
       81.4,
       197.7
      ],
      [
       23.4,
       51.9,
       196.4
      ],
      [
       30.7,
       73.5,
       195.7
      ],
      [
       29.1,
       70.7,
       195.6
      ],
      [
       15.5,
       35.6,
       195.3
      ],
      [
       16.5,
       44.9,
       194.7
      ],
      [
       12.2,
       28.8,
       194.6
      ],
      [
       29.6,
       80.2,
       194.1
      ],
      [
       16.2,
       36.7,
       193.8
      ],
      [
       32.9,
       105.0,
       193.0
      ],
      [
       23.2,
       48.7,
       192.7
      ],
      [
       39.9,
       103.4,
       192.4
      ],
      [
       15.2,
       35.1,
       192.2
      ],
      [
       34.9,
       85.2,
       191.6
      ],
      [
       18.8,
       44.6,
       191.5
      ],
      [
       31.1,
       62.1,
       190.6
      ],
      [
       37.2,
       92.7,
       190.5
      ],
      [
       24.7,
       65.4,
       190.5
      ],
      [
       27.0,
       82.4,
       190.5
      ],
      [
       30.2,
       88.9,
       190.2
      ],
      [
       12.8,
       36.3,
       190.2
      ],
      [
       28.1,
       61.2,
       189.6
      ],
      [
       19.1,
       45.0,
       189.4
      ],
      [
       41.8,
       113.4,
       188.8
      ],
      [
       24.4,
       56.0,
       188.6
      ],
      [
       20.0,
       47.8,
       188.5
      ],
      [
       42.4,
       88.8,
       187.6
      ],
      [
       44.0,
       90.9,
       187.3
      ],
      [
       27.4,
       67.5,
       186.9
      ],
      [
       26.5,
       60.9,
       186.9
      ],
      [
       26.1,
       67.8,
       186.9
      ],
      [
       16.3,
       40.6,
       186.8
      ],
      [
       30.5,
       78.1,
       186.4
      ],
      [
       49.2,
       102.1,
       186.4
      ],
      [
       35.1,
       89.2,
       186.2
      ],
      [
       34.1,
       85.8,
       185.9
      ],
      [
       19.6,
       43.6,
       185.7
      ],
      [
       23.1,
       48.0,
       185.5
      ],
      [
       15.7,
       42.7,
       185.4
      ],
      [
       18.2,
       33.9,
       185.1
      ],
      [
       21.2,
       58.2,
       184.5
      ],
      [
       45.5,
       96.5,
       184.1
      ],
      [
       38.6,
       89.9,
       183.3
      ],
      [
       39.5,
       92.2,
       183.3
      ],
      [
       12.8,
       32.1,
       183.2
      ],
      [
       32.0,
       87.2,
       183.0
      ],
      [
       26.2,
       72.5,
       182.4
      ],
      [
       29.9,
       70.0,
       182.4
      ],
      [
       40.0,
       95.4,
       181.8
      ],
      [
       35.0,
       81.4,
       181.2
      ],
      [
       23.3,
       68.0,
       181.2
      ],
      [
       25.6,
       72.8,
       181.1
      ],
      [
       23.4,
       60.8,
       180.8
      ],
      [
       25.2,
       69.6,
       179.9
      ],
      [
       25.1,
       52.0,
       179.7
      ],
      [
       19.7,
       38.2,
       179.6
      ],
      [
       35.3,
       97.2,
       179.5
      ],
      [
       19.1,
       63.1,
       179.5
      ],
      [
       18.6,
       49.4,
       179.5
      ],
      [
       37.7,
       95.9,
       179.2
      ],
      [
       18.7,
       57.7,
       178.4
      ],
      [
       27.3,
       68.5,
       177.9
      ],
      [
       32.6,
       64.7,
       177.9
      ],
      [
       19.0,
       50.4,
       177.4
      ],
      [
       28.5,
       54.2,
       177.3
      ],
      [
       27.2,
       118.1,
       177.0
      ],
      [
       12.2,
       32.0,
       176.7
      ],
      [
       46.6,
       99.2,
       176.2
      ],
      [
       35.6,
       92.6,
       176.0
      ],
      [
       11.9,
       23.3,
       175.3
      ],
      [
       20.7,
       47.9,
       175.0
      ],
      [
       22.3,
       60.4,
       174.5
      ],
      [
       12.4,
       29.0,
       173.9
      ],
      [
       13.5,
       33.9,
       173.6
      ],
      [
       27.2,
       72.8,
       173.5
      ],
      [
       24.2,
       64.2,
       173.4
      ],
      [
       26.1,
       59.4,
       173.2
      ],
      [
       14.9,
       29.0,
       173.1
      ],
      [
       27.4,
       66.7,
       173.1
      ],
      [
       26.8,
       57.6,
       173.0
      ],
      [
       25.7,
       70.7,
       173.0
      ],
      [
       15.8,
       43.6,
       173.0
      ],
      [
       42.4,
       104.4,
       173.0
      ],
      [
       22.0,
       45.6,
       172.3
      ],
      [
       30.0,
       97.6,
       172.0
      ],
      [
       30.8,
       66.1,
       171.6
      ],
      [
       37.1,
       119.1,
       171.3
      ],
      [
       39.5,
       94.4,
       171.3
      ],
      [
       31.6,
       81.8,
       171.2
      ],
      [
       16.3,
       27.0,
       171.0
      ],
      [
       45.6,
       103.9,
       170.7
      ],
      [
       20.3,
       50.0,
       170.0
      ],
      [
       21.5,
       53.5,
       169.8
      ],
      [
       16.2,
       43.6,
       169.6
      ],
      [
       21.8,
       81.6,
       169.4
      ],
      [
       15.5,
       36.4,
       169.2
      ],
      [
       31.1,
       97.7,
       168.9
      ],
      [
       17.6,
       38.4,
       168.6
      ],
      [
       28.1,
       72.3,
       168.1
      ],
      [
       23.7,
       90.3,
       168.1
      ],
      [
       10.2,
       20.3,
       167.9
      ],
      [
       14.8,
       36.3,
       167.5
      ],
      [
       34.2,
       66.4,
       167.2
      ],
      [
       36.9,
       92.3,
       166.7
      ],
      [
       29.1,
       77.5,
       166.7
      ],
      [
       19.7,
       38.2,
       166.1
      ],
      [
       40.8,
       96.9,
       165.5
      ],
      [
       41.0,
       117.3,
       165.4
      ],
      [
       25.4,
       102.8,
       165.4
      ],
      [
       14.8,
       36.5,
       164.6
      ],
      [
       12.6,
       35.6,
       163.9
      ],
      [
       17.3,
       49.1,
       163.8
      ],
      [
       11.9,
       25.6,
       163.6
      ],
      [
       30.8,
       76.8,
       163.5
      ],
      [
       20.7,
       53.9,
       163.3
      ],
      [
       30.8,
       73.7,
       163.0
      ],
      [
       30.1,
       82.6,
       162.2
      ],
      [
       28.0,
       71.8,
       161.5
      ],
      [
       24.5,
       67.9,
       161.5
      ],
      [
       23.6,
       74.9,
       161.5
      ],
      [
       19.3,
       58.0,
       161.4
      ],
      [
       35.2,
       91.5,
       160.9
      ],
      [
       19.8,
       58.5,
       160.0
      ],
      [
       24.5,
       42.5,
       159.7
      ],
      [
       20.0,
       56.7,
       159.5
      ],
      [
       24.5,
       54.6,
       159.4
      ],
      [
       27.6,
       76.2,
       159.3
      ],
      [
       27.9,
       56.3,
       158.2
      ],
      [
       38.8,
       87.1,
       158.2
      ],
      [
       28.2,
       60.6,
       157.9
      ],
      [
       18.1,
       35.6,
       157.8
      ],
      [
       26.5,
       74.5,
       157.5
      ],
      [
       18.5,
       48.2,
       157.3
      ],
      [
       14.9,
       32.7,
       157.3
      ],
      [
       34.0,
       99.7,
       156.5
      ],
      [
       25.6,
       44.0,
       155.8
      ],
      [
       30.1,
       78.3,
       155.6
      ],
      [
       24.1,
       54.1,
       155.4
      ],
      [
       29.6,
       58.1,
       155.2
      ],
      [
       26.6,
       97.3,
       155.1
      ],
      [
       25.6,
       87.9,
       154.9
      ],
      [
       19.1,
       40.6,
       154.5
      ],
      [
       39.4,
       94.7,
       154.5
      ],
      [
       29.4,
       68.2,
       154.1
      ],
      [
       19.2,
       47.5,
       153.6
      ],
      [
       23.7,
       55.0,
       152.4
      ],
      [
       13.1,
       29.0,
       152.3
      ],
      [
       20.1,
       57.1,
       152.3
      ],
      [
       34.9,
       95.3,
       151.5
      ],
      [
       27.1,
       62.5,
       151.3
      ],
      [
       24.4,
       71.5,
       151.2
      ],
      [
       21.7,
       64.0,
       150.6
      ],
      [
       21.1,
       49.1,
       150.2
      ],
      [
       18.2,
       42.9,
       149.8
      ],
      [
       20.8,
       51.6,
       148.6
      ],
      [
       28.1,
       70.6,
       148.5
      ],
      [
       14.6,
       34.0,
       148.2
      ],
      [
       25.3,
       67.2,
       147.4
      ],
      [
       17.1,
       36.6,
       147.2
      ],
      [
       20.3,
       51.3,
       146.3
      ],
      [
       19.1,
       31.0,
       146.1
      ],
      [
       14.4,
       33.4,
       145.2
      ],
      [
       22.2,
       52.5,
       145.0
      ],
      [
       33.9,
       93.1,
       144.6
      ],
      [
       22.4,
       53.2,
       143.8
      ],
      [
       24.1,
       55.8,
       143.2
      ],
      [
       44.7,
       105.7,
       142.8
      ],
      [
       14.6,
       36.9,
       142.2
      ],
      [
       24.0,
       61.1,
       142.1
      ],
      [
       20.4,
       54.2,
       142.1
      ],
      [
       15.9,
       40.3,
       141.5
      ],
      [
       19.6,
       48.2,
       141.1
      ],
      [
       22.4,
       47.0,
       140.8
      ],
      [
       31.8,
       74.8,
       140.6
      ],
      [
       18.7,
       38.0,
       140.1
      ],
      [
       36.1,
       91.9,
       139.1
      ],
      [
       26.6,
       67.2,
       139.1
      ],
      [
       22.7,
       55.1,
       136.6
      ],
      [
       20.2,
       53.5,
       136.6
      ],
      [
       36.2,
       104.3,
       135.8
      ],
      [
       36.9,
       73.6,
       135.1
      ],
      [
       34.5,
       117.0,
       132.9
      ],
      [
       24.5,
       90.4,
       132.9
      ],
      [
       27.4,
       64.3,
       131.1
      ],
      [
       25.3,
       62.8,
       130.6
      ],
      [
       20.4,
       60.2,
       130.3
      ],
      [
       19.6,
       49.1,
       129.1
      ],
      [
       27.2,
       97.0,
       128.8
      ],
      [
       25.2,
       66.3,
       128.8
      ],
      [
       17.6,
       29.6,
       125.9
      ],
      [
       28.8,
       70.9,
       125.8
      ],
      [
       39.0,
       85.6,
       125.8
      ],
      [
       26.5,
       117.8,
       124.6
      ],
      [
       30.5,
       71.3,
       122.4
      ],
      [
       46.8,
       109.9,
       122.4
      ],
      [
       25.9,
       64.8,
       122.0
      ],
      [
       32.5,
       64.7,
       121.7
      ],
      [
       21.3,
       58.0,
       120.0
      ],
      [
       24.7,
       61.2,
       119.6
      ],
      [
       39.4,
       99.2,
       118.8
      ],
      [
       29.0,
       55.8,
       118.8
      ],
      [
       37.3,
       102.8,
       118.6
      ],
      [
       15.8,
       39.4,
       117.9
      ],
      [
       40.5,
       104.2,
       117.8
      ],
      [
       21.3,
       57.9,
       115.5
      ],
      [
       30.3,
       76.5,
       115.5
      ],
      [
       25.4,
       65.2,
       115.5
      ],
      [
       17.8,
       41.5,
       115.5
      ],
      [
       16.3,
       42.0,
       115.5
      ],
      [
       27.4,
       61.7,
       114.2
      ],
      [
       25.1,
       70.1,
       113.9
      ],
      [
       18.3,
       42.3,
       113.4
      ],
      [
       29.0,
       72.8,
       113.4
      ],
      [
       29.1,
       68.3,
       113.4
      ],
      [
       24.7,
       59.9,
       113.4
      ],
      [
       26.6,
       68.1,
       113.4
      ],
      [
       18.4,
       46.1,
       113.4
      ],
      [
       20.3,
       42.8,
       112.0
      ],
      [
       26.6,
       79.6,
       112.0
      ],
      [
       37.9,
       103.2,
       112.0
      ],
      [
       39.3,
       100.9,
       112.0
      ],
      [
       26.0,
       42.1,
       112.0
      ],
      [
       31.5,
       103.2,
       112.0
      ],
      [
       18.1,
       43.8,
       112.0
      ],
      [
       36.9,
       106.8,
       112.0
      ],
      [
       15.9,
       36.0,
       112.0
      ],
      [
       16.5,
       36.4,
       112.0
      ],
      [
       22.7,
       65.5,
       111.0
      ],
      [
       20.2,
       42.7,
       111.0
      ],
      [
       23.2,
       59.2,
       110.8
      ],
      [
       34.1,
       82.4,
       110.3
      ],
      [
       26.0,
       67.4,
       110.3
      ],
      [
       30.6,
       67.0,
       110.1
      ],
      [
       19.1,
       49.2,
       109.2
      ],
      [
       38.3,
       98.4,
       109.2
      ],
      [
       14.1,
       32.7,
       109.2
      ],
      [
       12.6,
       33.9,
       109.2
      ]
     ],
     "linee": [
      {
       "k": 1.5,
       "label": "1,5 volte"
      },
      {
       "k": 2.0,
       "label": "il doppio"
      }
     ],
     "nota": "Ogni punto è una coppia di zone, grande quanto le auto del mattino; sopra una linea i mezzi pubblici impiegano più di quel multiplo del tempo in auto."
    }
   ],
   "calcolo": [
    "Le zone sono quelle dell'indagine sugli spostamenti 2022 con punti di calcolo; ognuna ha fino a 5 punti.",
    "Mezzi pubblici: a piedi, bus, tram e metro, con partenza fra le 7:45 e le 8:15. Si prende la mediana. Il tempo da orario ha in più l'attesa alla fermata misurata (1,5 minuti). Il ritardo a bordo misurato (5,9 minuti ogni 100) vale per il 57% del tempo, quello passato a bordo. I cambi non si contano: stima prudente. Da orario il rapporto mediano è 2,2.",
    "Auto, stima aperta: percorso più veloce sulla rete stradale. Velocità da sensori e bus, 20 secondi per semaforo, più 5 minuti per parcheggiare.",
    "Controllo: in 20 percorsi su 20 la stima aperta è più veloce di TomTom (errore mediano 23,5%). I numeri sono una forbice: la stima aperta e la stessa stima corretta di un fattore 1,3.",
    "Rapporto = tempo coi mezzi diviso tempo in auto, in fasce fisse. Le auto di una coppia sono i viaggi in auto dell'indagine, dalle 6 alle 10 di un feriale. Il numero grande vale per il 47% delle auto del mattino (220.307). Il grafico a punti mostra le 600 coppie con più auto.",
    "Costi: prezzi del 24/10/2026 (carburante self entro 5 km da Piazza Castello, costo ACI 2026, tariffe GTT). Sosta: 1,7 euro l'ora per 8 ore e 20 giorni al mese.",
    "Valore del tempo: costo in più al mese con la sosta pagata, diviso i minuti in più a viaggio. Si contano 2 viaggi al giorno e 20 giorni, ai 5 euro; col costo pieno ACI circa 30 euro l'ora."
   ],
   "criteri": [
    [
     "Zone",
     "71 zone dell'indagine sugli spostamenti (23 di Torino), fino a 5 punti ciascuna"
    ],
    [
     "Mezzi pubblici",
     "partenza 07:45-8:15 di un feriale, mediana, cammino a 4,8 km/h, al massimo 120 minuti"
    ],
    [
     "Auto, stima aperta (A)",
     "percorso più veloce sulla rete stradale, con velocità di sensori e bus e 20 secondi per semaforo (fattore mediano 1,8) + 5 minuti"
    ],
    [
     "Auto, corretta col controllo (B)",
     "guida × 1,3 + 5 minuti: fattore unico dal controllo su 20 percorsi con TomTom"
    ],
    [
     "Periodo dei sensori",
     "dal 09/10/2026 al 22/10/2026"
    ],
    [
     "Fasce del rapporto",
     "sotto 1,5, 1,5-2, 2-3, oltre 3"
    ]
   ],
   "limiti": [
    "Fuori Torino mancano treni e altre aziende: le coppie fra comuni della cintura non sono nel numero. Senza i treni metropolitani, dove ci sono, i mezzi pubblici risultano più lenti del vero. L'orario è quello programmato, corretto con le attese e i ritardi misurati.",
    "Tempi in auto da un modello aperto, non misurati sul singolo viaggio. Il controllo con TomTom su 20 percorsi li trova ottimistici: per questo c'è una forbice.",
    "L'indagine è un campione. I viaggi dentro una zona e 653 coppie senza collegamento (5.616 auto) non sono nel confronto.",
    "Una Golf come auto di riferimento. La zona a traffico limitato e gli abbonamenti alla sosta non sono nel conto. I prezzi sono quelli di un giorno."
   ],
   "mappa": {
    "id": "imq",
    "nota": "Nella mappa, tema «Spostamenti»: quanti spostamenti partono da ogni zona e dove vanno (indagine 2022, feriale)."
   },
   "fonti": [
    "GTT (orari ufficiali)",
    "5T (sensori del traffico)",
    "Agenzia della mobilità piemontese (indagine sugli spostamenti 2022)",
    "OpenStreetMap",
    "Osservatorio prezzi carburanti (Ministero delle imprese e del made in Italy)",
    "ACI (tabelle dei costi chilometrici 2026)",
    "GTT (tariffe e sosta)",
    "TomTom (controllo dei tempi in auto su 20 percorsi)"
   ],
   "titolo_breve": "Bus contro auto",
   "anima": {
    "tipo": "area",
    "didascalia": "Da Piazza Castello, alle 7:45 di un feriale. In 30 minuti si raggiungono ~33% dei torinesi coi mezzi pubblici e 91-100% in auto (traffico tipico, parcheggio compreso)."
   }
  },
  "forma_en": {
   "tipo_dato": "Type of data: calculated from real data, with car times with typical traffic, sensor measurements and the official timetables of the vehicles.",
   "titolo": "In the morning, public transport takes 1.9 to 2.4 times as long as the car",
   "domanda": "In the morning, how much longer does it take by public transport than by car?",
   "numero": {
    "valore": "1.9–2.4",
    "unita": "times",
    "testo": "the car's travel time, for morning car trips between different zones",
    "breve": "the car's time, by public transport"
   },
   "principale": {
    "tipo": "barre",
    "titolo": "Morning cars, by how many times public transport takes longer than the car",
    "unita": "%",
    "max": 100,
    "nota": "Each bar is a band: by public transport it takes that multiple of the car time. Dark bar: open estimate; light bar: the same estimate corrected with the check. Turin-Turin and Turin-suburb pairs.",
    "voci": [
     {
      "label": "less than 1.5 times",
      "valore": 1,
      "prima": 5,
      "tono": "verde",
      "testo": "1–5% (2,321–10,933 cars)"
     },
     {
      "label": "1.5 to 2 times",
      "valore": 12,
      "prima": 57,
      "tono": "giallo",
      "testo": "12–57% (27,510–125,901 cars)"
     },
     {
      "label": "2 to 3 times",
      "valore": 81,
      "prima": 37,
      "tono": "arancio",
      "testo": "37–81% (81,062–177,478 cars)"
     },
     {
      "label": "more than 3 times",
      "valore": 6,
      "prima": 1,
      "tono": "rosso",
      "testo": "1–6% (2,411–12,997 cars)"
     }
    ]
   },
   "punti": [
    "You save 14-19 minutes per trip, but parking costs ~270 euros a month. It is like paying 20-30 euros an hour for the time.",
    "With no parking to pay, the car costs less than the pass up to ~7 km.",
    "A typical frequent trip: Crocetta → Centro, ~23 minutes by public transport against 11–13 by car."
   ],
   "altri": [
    {
     "tipo": "linea",
     "titolo": "How many times the car time, hour by hour",
     "unita": "times",
     "nota": "Ratio between public transport time and car time, weighted by the morning cars, at 4 times of the day: open estimate and the same estimate corrected with the check.",
     "categorie": [
      "8:00",
      "13:00",
      "17:30",
      "21:00"
     ],
     "serie": [
      {
       "label": "open estimate",
       "valori": [
        2.4,
        2.5,
        2.4,
        2.8
       ]
      },
      {
       "label": "corrected with the check",
       "valori": [
        1.9,
        2.1,
        2.0,
        2.3
       ]
      }
     ]
    },
    {
     "tipo": "gara",
     "titolo": "The most frequent morning car trips: bus versus car",
     "luoghi": [
      {
       "nome": "Crocetta",
       "arrivo": "Centro",
       "bus": 22.8,
       "auto_min": 11.1,
       "auto_max": 13.0,
       "giudizio": "by public transport 1.8–2 times the car's time"
      },
      {
       "nome": "San Paolo",
       "arrivo": "Centro",
       "bus": 33.9,
       "auto_min": 15.0,
       "auto_max": 18.1,
       "giudizio": "by public transport 1.9–2.3 times the car's time"
      },
      {
       "nome": "Mirafiori Nord",
       "arrivo": "Santa Rita",
       "bus": 21.3,
       "auto_min": 10.4,
       "auto_max": 12.1,
       "giudizio": "by public transport 1.8–2 times the car's time"
      },
      {
       "nome": "Parella",
       "arrivo": "Centro",
       "bus": 27.0,
       "auto_min": 17.0,
       "auto_max": 20.7,
       "giudizio": "by public transport 1.3–1.6 times the car's time"
      },
      {
       "nome": "San Donato",
       "arrivo": "Centro",
       "bus": 20.8,
       "auto_min": 12.5,
       "auto_max": 14.8,
       "giudizio": "by public transport 1.4–1.7 times the car's time"
      },
      {
       "nome": "Barriera di Milano",
       "arrivo": "Falchera",
       "bus": 26.2,
       "auto_min": 13.1,
       "auto_max": 15.6,
       "giudizio": "by public transport 1.7–2 times the car's time"
      }
     ],
     "scelto": 0,
     "nota": "Bus and car leave together, one after the other, for the 6 most frequent morning car trips. The car has a time with the range from the check, parking included."
    },
    {
     "tipo": "barre_gruppi",
     "titolo": "A month of work near the centre: what it costs",
     "unita": "euros",
     "nota": "The light bar is the full cost of the car (ACI). Concession fares are GTT's for young people and older people, with an ISEE certificate.",
     "gruppi": [
      {
       "label": "Car, street parking paid",
       "voci": [
        {
         "label": "Fuel and parking",
         "valore": 307,
         "prima": 404,
         "tono": "rosso",
         "testo": "307 (404 at full cost)"
        }
       ]
      },
      {
       "label": "Car, free parking at work",
       "voci": [
        {
         "label": "Fuel only",
         "valore": 35,
         "prima": 132,
         "tono": "rosso",
         "testo": "35 (132 at full cost)"
        }
       ]
      },
      {
       "label": "Public transport",
       "voci": [
        {
         "label": "Tickets (40 trips)",
         "valore": 80,
         "tono": "verde",
         "testo": "80"
        },
        {
         "label": "Monthly pass",
         "valore": 38,
         "tono": "verde",
         "testo": "38"
        },
        {
         "label": "Annual pass, per month",
         "valore": 26,
         "tono": "verde",
         "testo": "26"
        }
       ]
      }
     ]
    },
    {
     "tipo": "dispersione",
     "titolo": "Car time and public transport time, one pair of zones per point",
     "xlabel": "minutes by car (morning, open estimate)",
     "ylabel": "minutes by public transport",
     "punti": [
      [
       11.1,
       22.8,
       1355.3
      ],
      [
       15.0,
       33.9,
       1341.8
      ],
      [
       10.4,
       21.3,
       1324.4
      ],
      [
       17.0,
       27.0,
       1277.0
      ],
      [
       12.5,
       20.8,
       1269.4
      ],
      [
       13.1,
       26.2,
       1208.2
      ],
      [
       19.3,
       46.0,
       1149.2
      ],
      [
       15.9,
       40.2,
       1107.8
      ],
      [
       39.0,
       84.3,
       1081.8
      ],
      [
       9.6,
       17.2,
       1038.1
      ],
      [
       15.8,
       35.8,
       969.9
      ],
      [
       15.0,
       33.1,
       968.1
      ],
      [
       9.4,
       17.2,
       957.2
      ],
      [
       23.9,
       47.5,
       940.7
      ],
      [
       11.1,
       22.4,
       938.8
      ],
      [
       15.0,
       36.1,
       928.7
      ],
      [
       16.8,
       40.9,
       916.7
      ],
      [
       31.3,
       67.0,
       910.0
      ],
      [
       15.1,
       32.9,
       900.6
      ],
      [
       14.9,
       37.8,
       894.4
      ],
      [
       11.7,
       24.6,
       893.3
      ],
      [
       12.2,
       26.1,
       889.9
      ],
      [
       19.8,
       42.1,
       888.0
      ],
      [
       17.0,
       29.9,
       818.9
      ],
      [
       21.0,
       45.2,
       796.7
      ],
      [
       17.5,
       37.9,
       795.1
      ],
      [
       10.1,
       21.0,
       789.0
      ],
      [
       17.3,
       33.8,
       779.1
      ],
      [
       14.0,
       32.9,
       762.5
      ],
      [
       22.0,
       53.2,
       753.4
      ],
      [
       11.6,
       33.8,
       751.2
      ],
      [
       12.6,
       26.6,
       737.2
      ],
      [
       22.3,
       85.6,
       718.7
      ],
      [
       10.4,
       20.2,
       714.6
      ],
      [
       15.1,
       37.9,
       714.1
      ],
      [
       11.7,
       26.2,
       706.6
      ],
      [
       30.3,
       67.1,
       702.1
      ],
      [
       12.0,
       24.8,
       698.0
      ],
      [
       17.0,
       32.2,
       696.9
      ],
      [
       26.1,
       53.5,
       690.4
      ],
      [
       28.6,
       76.6,
       687.3
      ],
      [
       12.3,
       25.4,
       685.0
      ],
      [
       20.4,
       27.8,
       672.4
      ],
      [
       14.8,
       31.7,
       671.0
      ],
      [
       11.0,
       25.1,
       666.8
      ],
      [
       32.5,
       76.4,
       659.4
      ],
      [
       21.9,
       54.2,
       644.0
      ],
      [
       14.0,
       35.3,
       627.3
      ],
      [
       9.5,
       18.0,
       622.4
      ],
      [
       11.8,
       24.5,
       620.3
      ],
      [
       13.1,
       29.6,
       615.4
      ],
      [
       17.0,
       39.7,
       614.3
      ],
      [
       14.9,
       37.2,
       614.1
      ],
      [
       12.7,
       25.7,
       607.7
      ],
      [
       13.7,
       29.6,
       606.6
      ],
      [
       14.4,
       36.6,
       601.6
      ],
      [
       11.4,
       32.9,
       592.7
      ],
      [
       16.2,
       38.7,
       589.8
      ],
      [
       15.3,
       36.7,
       582.5
      ],
      [
       21.7,
       53.3,
       580.1
      ],
      [
       15.7,
       26.4,
       574.5
      ],
      [
       13.4,
       32.4,
       570.6
      ],
      [
       18.9,
       58.4,
       568.2
      ],
      [
       14.1,
       26.9,
       562.6
      ],
      [
       28.3,
       90.1,
       543.7
      ],
      [
       13.7,
       26.4,
       543.0
      ],
      [
       16.7,
       42.0,
       540.9
      ],
      [
       10.3,
       23.8,
       540.3
      ],
      [
       13.9,
       33.4,
       539.8
      ],
      [
       15.6,
       33.2,
       527.7
      ],
      [
       29.7,
       72.6,
       520.3
      ],
      [
       26.9,
       75.5,
       519.9
      ],
      [
       13.2,
       31.9,
       519.7
      ],
      [
       12.0,
       27.2,
       517.1
      ],
      [
       25.0,
       60.3,
       515.6
      ],
      [
       31.3,
       75.0,
       514.3
      ],
      [
       15.2,
       42.4,
       512.4
      ],
      [
       27.8,
       65.7,
       504.1
      ],
      [
       14.0,
       29.3,
       503.9
      ],
      [
       16.2,
       35.3,
       498.7
      ],
      [
       14.6,
       31.3,
       496.3
      ],
      [
       9.5,
       17.5,
       494.3
      ],
      [
       20.3,
       50.2,
       490.1
      ],
      [
       18.7,
       41.5,
       489.2
      ],
      [
       11.0,
       25.5,
       488.9
      ],
      [
       34.4,
       77.9,
       488.2
      ],
      [
       11.8,
       24.2,
       481.0
      ],
      [
       16.4,
       40.9,
       478.8
      ],
      [
       23.9,
       58.2,
       478.7
      ],
      [
       21.2,
       50.6,
       476.8
      ],
      [
       19.8,
       48.9,
       467.9
      ],
      [
       12.7,
       28.5,
       466.7
      ],
      [
       14.6,
       30.1,
       462.0
      ],
      [
       13.0,
       28.7,
       459.7
      ],
      [
       41.1,
       81.8,
       458.7
      ],
      [
       20.0,
       28.4,
       458.5
      ],
      [
       17.6,
       39.9,
       456.6
      ],
      [
       13.5,
       25.1,
       456.0
      ],
      [
       26.4,
       60.5,
       454.7
      ],
      [
       10.8,
       22.5,
       452.9
      ],
      [
       22.2,
       57.3,
       452.3
      ],
      [
       35.8,
       90.3,
       449.8
      ],
      [
       14.3,
       34.2,
       448.6
      ],
      [
       35.1,
       97.3,
       448.4
      ],
      [
       25.9,
       75.7,
       445.5
      ],
      [
       17.7,
       38.5,
       443.8
      ],
      [
       25.0,
       49.5,
       442.8
      ],
      [
       17.9,
       43.0,
       439.9
      ],
      [
       21.9,
       58.6,
       438.4
      ],
      [
       11.7,
       23.6,
       437.5
      ],
      [
       25.9,
       65.4,
       431.9
      ],
      [
       24.1,
       61.7,
       431.8
      ],
      [
       14.7,
       34.8,
       431.4
      ],
      [
       27.3,
       72.4,
       428.4
      ],
      [
       16.6,
       40.1,
       428.4
      ],
      [
       33.2,
       85.5,
       426.2
      ],
      [
       14.6,
       38.4,
       423.2
      ],
      [
       18.7,
       44.2,
       422.6
      ],
      [
       11.4,
       20.3,
       421.9
      ],
      [
       20.8,
       50.7,
       421.1
      ],
      [
       10.7,
       21.2,
       419.2
      ],
      [
       21.6,
       56.7,
       411.0
      ],
      [
       35.1,
       77.4,
       410.3
      ],
      [
       19.5,
       57.1,
       410.0
      ],
      [
       24.3,
       35.3,
       409.6
      ],
      [
       21.8,
       56.8,
       409.5
      ],
      [
       24.5,
       54.4,
       404.3
      ],
      [
       24.9,
       49.2,
       403.5
      ],
      [
       22.7,
       57.8,
       402.7
      ],
      [
       26.9,
       64.7,
       399.0
      ],
      [
       12.2,
       27.2,
       398.4
      ],
      [
       26.5,
       68.0,
       396.9
      ],
      [
       12.1,
       30.8,
       396.9
      ],
      [
       25.1,
       63.1,
       395.5
      ],
      [
       16.6,
       34.9,
       391.8
      ],
      [
       25.3,
       54.3,
       389.9
      ],
      [
       22.4,
       49.6,
       389.6
      ],
      [
       38.5,
       108.8,
       386.9
      ],
      [
       16.9,
       30.4,
       386.6
      ],
      [
       13.6,
       30.6,
       384.3
      ],
      [
       15.3,
       29.9,
       383.2
      ],
      [
       18.6,
       85.7,
       383.2
      ],
      [
       24.5,
       65.9,
       382.4
      ],
      [
       22.1,
       59.9,
       382.0
      ],
      [
       20.2,
       57.4,
       379.4
      ],
      [
       18.2,
       41.2,
       377.6
      ],
      [
       14.6,
       34.0,
       377.4
      ],
      [
       15.1,
       26.6,
       376.5
      ],
      [
       14.8,
       39.4,
       369.2
      ],
      [
       16.3,
       33.1,
       368.7
      ],
      [
       18.4,
       39.8,
       367.3
      ],
      [
       19.1,
       46.3,
       366.6
      ],
      [
       24.4,
       83.3,
       365.7
      ],
      [
       12.1,
       21.4,
       365.5
      ],
      [
       26.6,
       78.5,
       363.3
      ],
      [
       13.4,
       30.6,
       362.7
      ],
      [
       10.1,
       23.1,
       356.4
      ],
      [
       12.0,
       23.6,
       355.0
      ],
      [
       17.5,
       41.9,
       353.0
      ],
      [
       20.4,
       55.6,
       352.5
      ],
      [
       15.7,
       19.2,
       352.1
      ],
      [
       24.3,
       53.7,
       350.1
      ],
      [
       15.2,
       39.7,
       348.3
      ],
      [
       19.6,
       47.8,
       347.8
      ],
      [
       34.4,
       75.3,
       346.3
      ],
      [
       27.2,
       75.0,
       346.1
      ],
      [
       24.6,
       67.1,
       345.7
      ],
      [
       16.2,
       34.6,
       340.6
      ],
      [
       14.5,
       44.7,
       340.0
      ],
      [
       21.6,
       53.8,
       339.6
      ],
      [
       35.5,
       87.3,
       338.3
      ],
      [
       18.8,
       48.7,
       336.5
      ],
      [
       21.0,
       57.6,
       336.5
      ],
      [
       33.3,
       83.6,
       335.5
      ],
      [
       21.2,
       55.3,
       335.0
      ],
      [
       26.5,
       64.1,
       333.8
      ],
      [
       33.7,
       92.2,
       333.6
      ],
      [
       32.9,
       78.5,
       333.5
      ],
      [
       17.3,
       34.0,
       332.2
      ],
      [
       29.9,
       87.0,
       331.5
      ],
      [
       29.1,
       50.7,
       331.5
      ],
      [
       22.9,
       68.0,
       330.5
      ],
      [
       21.6,
       55.6,
       329.9
      ],
      [
       26.0,
       46.5,
       329.1
      ],
      [
       31.7,
       69.2,
       328.2
      ],
      [
       24.3,
       57.5,
       328.0
      ],
      [
       19.5,
       57.5,
       326.5
      ],
      [
       31.4,
       70.9,
       323.5
      ],
      [
       11.9,
       26.3,
       322.3
      ],
      [
       9.6,
       21.3,
       322.1
      ],
      [
       31.3,
       67.9,
       321.4
      ],
      [
       16.5,
       36.7,
       318.2
      ],
      [
       24.7,
       50.9,
       317.7
      ],
      [
       27.8,
       84.8,
       311.9
      ],
      [
       34.6,
       98.7,
       310.7
      ],
      [
       12.8,
       28.7,
       309.9
      ],
      [
       27.6,
       63.7,
       307.1
      ],
      [
       29.5,
       73.7,
       306.3
      ],
      [
       12.0,
       27.4,
       305.1
      ],
      [
       16.9,
       38.5,
       304.4
      ],
      [
       23.3,
       56.3,
       304.2
      ],
      [
       19.5,
       55.6,
       303.6
      ],
      [
       29.6,
       66.2,
       303.4
      ],
      [
       32.9,
       81.1,
       302.8
      ],
      [
       30.7,
       72.6,
       302.3
      ],
      [
       32.1,
       76.2,
       300.8
      ],
      [
       12.4,
       21.2,
       299.5
      ],
      [
       20.1,
       52.0,
       299.2
      ],
      [
       24.2,
       59.8,
       298.9
      ],
      [
       20.6,
       50.3,
       298.6
      ],
      [
       21.6,
       57.6,
       297.1
      ],
      [
       20.5,
       57.4,
       296.5
      ],
      [
       24.8,
       61.1,
       296.0
      ],
      [
       37.3,
       91.2,
       295.0
      ],
      [
       32.0,
       73.8,
       294.0
      ],
      [
       14.8,
       36.4,
       292.7
      ],
      [
       40.4,
       90.1,
       291.8
      ],
      [
       20.0,
       49.0,
       290.8
      ],
      [
       11.2,
       23.5,
       290.5
      ],
      [
       24.9,
       63.7,
       289.4
      ],
      [
       24.4,
       56.0,
       288.9
      ],
      [
       32.3,
       78.6,
       288.6
      ],
      [
       13.9,
       37.7,
       284.7
      ],
      [
       16.7,
       41.4,
       283.1
      ],
      [
       9.7,
       21.0,
       282.6
      ],
      [
       17.7,
       45.6,
       282.2
      ],
      [
       20.5,
       45.1,
       281.8
      ],
      [
       14.5,
       41.1,
       281.7
      ],
      [
       21.3,
       60.8,
       280.3
      ],
      [
       21.7,
       60.1,
       278.1
      ],
      [
       13.7,
       26.8,
       274.9
      ],
      [
       31.8,
       87.3,
       274.4
      ],
      [
       27.5,
       71.7,
       273.4
      ],
      [
       15.9,
       37.2,
       273.2
      ],
      [
       28.0,
       49.1,
       272.4
      ],
      [
       37.5,
       80.6,
       271.8
      ],
      [
       35.4,
       83.1,
       271.3
      ],
      [
       23.9,
       64.9,
       271.0
      ],
      [
       15.7,
       34.4,
       270.6
      ],
      [
       12.6,
       26.9,
       270.2
      ],
      [
       23.3,
       47.1,
       270.1
      ],
      [
       34.1,
       103.0,
       269.7
      ],
      [
       23.4,
       65.7,
       269.7
      ],
      [
       34.4,
       87.9,
       268.9
      ],
      [
       15.4,
       19.2,
       268.5
      ],
      [
       24.6,
       58.6,
       267.8
      ],
      [
       20.8,
       39.8,
       264.3
      ],
      [
       25.4,
       63.9,
       263.3
      ],
      [
       20.3,
       54.6,
       262.3
      ],
      [
       21.6,
       45.1,
       261.5
      ],
      [
       24.1,
       52.6,
       261.2
      ],
      [
       15.6,
       37.4,
       260.2
      ],
      [
       9.9,
       19.5,
       259.7
      ],
      [
       12.6,
       31.5,
       258.2
      ],
      [
       41.0,
       83.5,
       257.3
      ],
      [
       20.7,
       49.6,
       256.8
      ],
      [
       32.7,
       79.8,
       255.1
      ],
      [
       40.9,
       82.4,
       254.4
      ],
      [
       36.4,
       108.1,
       253.6
      ],
      [
       44.3,
       93.4,
       253.1
      ],
      [
       9.0,
       17.9,
       252.2
      ],
      [
       24.9,
       52.5,
       251.6
      ],
      [
       13.3,
       32.4,
       251.5
      ],
      [
       23.2,
       59.9,
       250.1
      ],
      [
       23.0,
       40.0,
       248.3
      ],
      [
       26.8,
       51.9,
       247.4
      ],
      [
       17.3,
       37.4,
       244.8
      ],
      [
       13.8,
       31.3,
       243.9
      ],
      [
       22.5,
       47.1,
       243.6
      ],
      [
       25.2,
       58.3,
       243.6
      ],
      [
       14.3,
       31.7,
       243.6
      ],
      [
       20.5,
       44.6,
       243.0
      ],
      [
       34.1,
       82.0,
       242.3
      ],
      [
       22.5,
       46.3,
       242.2
      ],
      [
       25.7,
       65.1,
       241.4
      ],
      [
       15.1,
       32.9,
       241.0
      ],
      [
       35.0,
       96.0,
       240.6
      ],
      [
       13.1,
       42.2,
       240.0
      ],
      [
       28.0,
       68.6,
       238.3
      ],
      [
       29.8,
       76.0,
       236.1
      ],
      [
       16.1,
       26.5,
       235.8
      ],
      [
       24.7,
       49.4,
       234.9
      ],
      [
       24.5,
       55.7,
       234.7
      ],
      [
       22.2,
       49.4,
       234.6
      ],
      [
       19.7,
       49.7,
       233.6
      ],
      [
       25.4,
       71.4,
       233.3
      ],
      [
       17.9,
       46.3,
       231.7
      ],
      [
       26.2,
       65.0,
       231.5
      ],
      [
       44.7,
       104.4,
       230.9
      ],
      [
       23.3,
       51.1,
       228.8
      ],
      [
       12.5,
       27.7,
       228.3
      ],
      [
       18.2,
       44.5,
       228.1
      ],
      [
       25.1,
       66.4,
       227.0
      ],
      [
       25.4,
       83.3,
       226.3
      ],
      [
       16.1,
       38.8,
       225.6
      ],
      [
       28.4,
       62.5,
       225.4
      ],
      [
       21.2,
       55.2,
       225.1
      ],
      [
       27.6,
       68.5,
       224.1
      ],
      [
       11.6,
       26.4,
       223.2
      ],
      [
       34.9,
       98.9,
       222.3
      ],
      [
       15.3,
       34.7,
       222.1
      ],
      [
       32.6,
       74.6,
       221.0
      ],
      [
       11.7,
       28.3,
       220.4
      ],
      [
       14.5,
       26.5,
       219.8
      ],
      [
       13.7,
       24.6,
       218.7
      ],
      [
       23.6,
       56.1,
       218.3
      ],
      [
       24.6,
       79.5,
       217.8
      ],
      [
       32.8,
       72.3,
       217.1
      ],
      [
       15.2,
       33.3,
       216.9
      ],
      [
       34.1,
       109.0,
       216.3
      ],
      [
       34.5,
       64.5,
       215.9
      ],
      [
       25.6,
       75.8,
       215.8
      ],
      [
       39.3,
       101.7,
       215.6
      ],
      [
       22.1,
       57.2,
       215.3
      ],
      [
       26.0,
       70.8,
       214.1
      ],
      [
       20.9,
       54.8,
       214.0
      ],
      [
       13.1,
       28.4,
       213.2
      ],
      [
       27.3,
       76.3,
       212.7
      ],
      [
       33.1,
       82.6,
       212.0
      ],
      [
       29.0,
       97.7,
       211.8
      ],
      [
       32.3,
       67.5,
       211.3
      ],
      [
       18.0,
       53.4,
       211.2
      ],
      [
       27.2,
       64.6,
       210.7
      ],
      [
       25.5,
       61.2,
       209.8
      ],
      [
       20.0,
       46.2,
       209.0
      ],
      [
       20.4,
       54.4,
       208.2
      ],
      [
       46.3,
       107.6,
       208.1
      ],
      [
       25.3,
       64.8,
       207.6
      ],
      [
       41.6,
       90.9,
       207.5
      ],
      [
       16.3,
       32.5,
       206.7
      ],
      [
       40.9,
       86.5,
       206.4
      ],
      [
       20.1,
       47.2,
       206.2
      ],
      [
       20.1,
       54.1,
       206.2
      ],
      [
       19.7,
       47.3,
       206.1
      ],
      [
       31.8,
       70.2,
       206.0
      ],
      [
       18.5,
       58.7,
       205.9
      ],
      [
       30.0,
       101.0,
       205.6
      ],
      [
       26.3,
       60.0,
       205.0
      ],
      [
       21.9,
       44.5,
       204.7
      ],
      [
       24.8,
       79.7,
       204.3
      ],
      [
       30.1,
       60.0,
       204.3
      ],
      [
       34.0,
       82.1,
       204.0
      ],
      [
       35.1,
       81.4,
       203.9
      ],
      [
       21.8,
       60.5,
       203.8
      ],
      [
       26.9,
       96.1,
       203.7
      ],
      [
       18.5,
       46.6,
       203.5
      ],
      [
       19.5,
       45.5,
       203.4
      ],
      [
       35.1,
       78.0,
       203.4
      ],
      [
       20.8,
       49.8,
       203.2
      ],
      [
       37.3,
       88.7,
       202.3
      ],
      [
       27.3,
       71.2,
       201.9
      ],
      [
       29.3,
       61.9,
       201.7
      ],
      [
       23.5,
       57.6,
       201.5
      ],
      [
       15.4,
       28.5,
       201.5
      ],
      [
       16.3,
       29.3,
       201.2
      ],
      [
       18.6,
       45.7,
       200.7
      ],
      [
       29.5,
       65.4,
       200.5
      ],
      [
       33.6,
       86.4,
       200.3
      ],
      [
       26.0,
       90.0,
       199.7
      ],
      [
       14.4,
       29.3,
       199.4
      ],
      [
       13.7,
       33.4,
       199.3
      ],
      [
       26.6,
       58.8,
       198.8
      ],
      [
       30.9,
       59.8,
       197.7
      ],
      [
       32.0,
       81.4,
       197.7
      ],
      [
       23.4,
       51.9,
       196.4
      ],
      [
       30.7,
       73.5,
       195.7
      ],
      [
       29.1,
       70.7,
       195.6
      ],
      [
       15.5,
       35.6,
       195.3
      ],
      [
       16.5,
       44.9,
       194.7
      ],
      [
       12.2,
       28.8,
       194.6
      ],
      [
       29.6,
       80.2,
       194.1
      ],
      [
       16.2,
       36.7,
       193.8
      ],
      [
       32.9,
       105.0,
       193.0
      ],
      [
       23.2,
       48.7,
       192.7
      ],
      [
       39.9,
       103.4,
       192.4
      ],
      [
       15.2,
       35.1,
       192.2
      ],
      [
       34.9,
       85.2,
       191.6
      ],
      [
       18.8,
       44.6,
       191.5
      ],
      [
       31.1,
       62.1,
       190.6
      ],
      [
       37.2,
       92.7,
       190.5
      ],
      [
       24.7,
       65.4,
       190.5
      ],
      [
       27.0,
       82.4,
       190.5
      ],
      [
       30.2,
       88.9,
       190.2
      ],
      [
       12.8,
       36.3,
       190.2
      ],
      [
       28.1,
       61.2,
       189.6
      ],
      [
       19.1,
       45.0,
       189.4
      ],
      [
       41.8,
       113.4,
       188.8
      ],
      [
       24.4,
       56.0,
       188.6
      ],
      [
       20.0,
       47.8,
       188.5
      ],
      [
       42.4,
       88.8,
       187.6
      ],
      [
       44.0,
       90.9,
       187.3
      ],
      [
       27.4,
       67.5,
       186.9
      ],
      [
       26.5,
       60.9,
       186.9
      ],
      [
       26.1,
       67.8,
       186.9
      ],
      [
       16.3,
       40.6,
       186.8
      ],
      [
       30.5,
       78.1,
       186.4
      ],
      [
       49.2,
       102.1,
       186.4
      ],
      [
       35.1,
       89.2,
       186.2
      ],
      [
       34.1,
       85.8,
       185.9
      ],
      [
       19.6,
       43.6,
       185.7
      ],
      [
       23.1,
       48.0,
       185.5
      ],
      [
       15.7,
       42.7,
       185.4
      ],
      [
       18.2,
       33.9,
       185.1
      ],
      [
       21.2,
       58.2,
       184.5
      ],
      [
       45.5,
       96.5,
       184.1
      ],
      [
       38.6,
       89.9,
       183.3
      ],
      [
       39.5,
       92.2,
       183.3
      ],
      [
       12.8,
       32.1,
       183.2
      ],
      [
       32.0,
       87.2,
       183.0
      ],
      [
       26.2,
       72.5,
       182.4
      ],
      [
       29.9,
       70.0,
       182.4
      ],
      [
       40.0,
       95.4,
       181.8
      ],
      [
       35.0,
       81.4,
       181.2
      ],
      [
       23.3,
       68.0,
       181.2
      ],
      [
       25.6,
       72.8,
       181.1
      ],
      [
       23.4,
       60.8,
       180.8
      ],
      [
       25.2,
       69.6,
       179.9
      ],
      [
       25.1,
       52.0,
       179.7
      ],
      [
       19.7,
       38.2,
       179.6
      ],
      [
       35.3,
       97.2,
       179.5
      ],
      [
       19.1,
       63.1,
       179.5
      ],
      [
       18.6,
       49.4,
       179.5
      ],
      [
       37.7,
       95.9,
       179.2
      ],
      [
       18.7,
       57.7,
       178.4
      ],
      [
       27.3,
       68.5,
       177.9
      ],
      [
       32.6,
       64.7,
       177.9
      ],
      [
       19.0,
       50.4,
       177.4
      ],
      [
       28.5,
       54.2,
       177.3
      ],
      [
       27.2,
       118.1,
       177.0
      ],
      [
       12.2,
       32.0,
       176.7
      ],
      [
       46.6,
       99.2,
       176.2
      ],
      [
       35.6,
       92.6,
       176.0
      ],
      [
       11.9,
       23.3,
       175.3
      ],
      [
       20.7,
       47.9,
       175.0
      ],
      [
       22.3,
       60.4,
       174.5
      ],
      [
       12.4,
       29.0,
       173.9
      ],
      [
       13.5,
       33.9,
       173.6
      ],
      [
       27.2,
       72.8,
       173.5
      ],
      [
       24.2,
       64.2,
       173.4
      ],
      [
       26.1,
       59.4,
       173.2
      ],
      [
       14.9,
       29.0,
       173.1
      ],
      [
       27.4,
       66.7,
       173.1
      ],
      [
       26.8,
       57.6,
       173.0
      ],
      [
       25.7,
       70.7,
       173.0
      ],
      [
       15.8,
       43.6,
       173.0
      ],
      [
       42.4,
       104.4,
       173.0
      ],
      [
       22.0,
       45.6,
       172.3
      ],
      [
       30.0,
       97.6,
       172.0
      ],
      [
       30.8,
       66.1,
       171.6
      ],
      [
       37.1,
       119.1,
       171.3
      ],
      [
       39.5,
       94.4,
       171.3
      ],
      [
       31.6,
       81.8,
       171.2
      ],
      [
       16.3,
       27.0,
       171.0
      ],
      [
       45.6,
       103.9,
       170.7
      ],
      [
       20.3,
       50.0,
       170.0
      ],
      [
       21.5,
       53.5,
       169.8
      ],
      [
       16.2,
       43.6,
       169.6
      ],
      [
       21.8,
       81.6,
       169.4
      ],
      [
       15.5,
       36.4,
       169.2
      ],
      [
       31.1,
       97.7,
       168.9
      ],
      [
       17.6,
       38.4,
       168.6
      ],
      [
       28.1,
       72.3,
       168.1
      ],
      [
       23.7,
       90.3,
       168.1
      ],
      [
       10.2,
       20.3,
       167.9
      ],
      [
       14.8,
       36.3,
       167.5
      ],
      [
       34.2,
       66.4,
       167.2
      ],
      [
       36.9,
       92.3,
       166.7
      ],
      [
       29.1,
       77.5,
       166.7
      ],
      [
       19.7,
       38.2,
       166.1
      ],
      [
       40.8,
       96.9,
       165.5
      ],
      [
       41.0,
       117.3,
       165.4
      ],
      [
       25.4,
       102.8,
       165.4
      ],
      [
       14.8,
       36.5,
       164.6
      ],
      [
       12.6,
       35.6,
       163.9
      ],
      [
       17.3,
       49.1,
       163.8
      ],
      [
       11.9,
       25.6,
       163.6
      ],
      [
       30.8,
       76.8,
       163.5
      ],
      [
       20.7,
       53.9,
       163.3
      ],
      [
       30.8,
       73.7,
       163.0
      ],
      [
       30.1,
       82.6,
       162.2
      ],
      [
       28.0,
       71.8,
       161.5
      ],
      [
       24.5,
       67.9,
       161.5
      ],
      [
       23.6,
       74.9,
       161.5
      ],
      [
       19.3,
       58.0,
       161.4
      ],
      [
       35.2,
       91.5,
       160.9
      ],
      [
       19.8,
       58.5,
       160.0
      ],
      [
       24.5,
       42.5,
       159.7
      ],
      [
       20.0,
       56.7,
       159.5
      ],
      [
       24.5,
       54.6,
       159.4
      ],
      [
       27.6,
       76.2,
       159.3
      ],
      [
       27.9,
       56.3,
       158.2
      ],
      [
       38.8,
       87.1,
       158.2
      ],
      [
       28.2,
       60.6,
       157.9
      ],
      [
       18.1,
       35.6,
       157.8
      ],
      [
       26.5,
       74.5,
       157.5
      ],
      [
       18.5,
       48.2,
       157.3
      ],
      [
       14.9,
       32.7,
       157.3
      ],
      [
       34.0,
       99.7,
       156.5
      ],
      [
       25.6,
       44.0,
       155.8
      ],
      [
       30.1,
       78.3,
       155.6
      ],
      [
       24.1,
       54.1,
       155.4
      ],
      [
       29.6,
       58.1,
       155.2
      ],
      [
       26.6,
       97.3,
       155.1
      ],
      [
       25.6,
       87.9,
       154.9
      ],
      [
       19.1,
       40.6,
       154.5
      ],
      [
       39.4,
       94.7,
       154.5
      ],
      [
       29.4,
       68.2,
       154.1
      ],
      [
       19.2,
       47.5,
       153.6
      ],
      [
       23.7,
       55.0,
       152.4
      ],
      [
       13.1,
       29.0,
       152.3
      ],
      [
       20.1,
       57.1,
       152.3
      ],
      [
       34.9,
       95.3,
       151.5
      ],
      [
       27.1,
       62.5,
       151.3
      ],
      [
       24.4,
       71.5,
       151.2
      ],
      [
       21.7,
       64.0,
       150.6
      ],
      [
       21.1,
       49.1,
       150.2
      ],
      [
       18.2,
       42.9,
       149.8
      ],
      [
       20.8,
       51.6,
       148.6
      ],
      [
       28.1,
       70.6,
       148.5
      ],
      [
       14.6,
       34.0,
       148.2
      ],
      [
       25.3,
       67.2,
       147.4
      ],
      [
       17.1,
       36.6,
       147.2
      ],
      [
       20.3,
       51.3,
       146.3
      ],
      [
       19.1,
       31.0,
       146.1
      ],
      [
       14.4,
       33.4,
       145.2
      ],
      [
       22.2,
       52.5,
       145.0
      ],
      [
       33.9,
       93.1,
       144.6
      ],
      [
       22.4,
       53.2,
       143.8
      ],
      [
       24.1,
       55.8,
       143.2
      ],
      [
       44.7,
       105.7,
       142.8
      ],
      [
       14.6,
       36.9,
       142.2
      ],
      [
       24.0,
       61.1,
       142.1
      ],
      [
       20.4,
       54.2,
       142.1
      ],
      [
       15.9,
       40.3,
       141.5
      ],
      [
       19.6,
       48.2,
       141.1
      ],
      [
       22.4,
       47.0,
       140.8
      ],
      [
       31.8,
       74.8,
       140.6
      ],
      [
       18.7,
       38.0,
       140.1
      ],
      [
       36.1,
       91.9,
       139.1
      ],
      [
       26.6,
       67.2,
       139.1
      ],
      [
       22.7,
       55.1,
       136.6
      ],
      [
       20.2,
       53.5,
       136.6
      ],
      [
       36.2,
       104.3,
       135.8
      ],
      [
       36.9,
       73.6,
       135.1
      ],
      [
       34.5,
       117.0,
       132.9
      ],
      [
       24.5,
       90.4,
       132.9
      ],
      [
       27.4,
       64.3,
       131.1
      ],
      [
       25.3,
       62.8,
       130.6
      ],
      [
       20.4,
       60.2,
       130.3
      ],
      [
       19.6,
       49.1,
       129.1
      ],
      [
       27.2,
       97.0,
       128.8
      ],
      [
       25.2,
       66.3,
       128.8
      ],
      [
       17.6,
       29.6,
       125.9
      ],
      [
       28.8,
       70.9,
       125.8
      ],
      [
       39.0,
       85.6,
       125.8
      ],
      [
       26.5,
       117.8,
       124.6
      ],
      [
       30.5,
       71.3,
       122.4
      ],
      [
       46.8,
       109.9,
       122.4
      ],
      [
       25.9,
       64.8,
       122.0
      ],
      [
       32.5,
       64.7,
       121.7
      ],
      [
       21.3,
       58.0,
       120.0
      ],
      [
       24.7,
       61.2,
       119.6
      ],
      [
       39.4,
       99.2,
       118.8
      ],
      [
       29.0,
       55.8,
       118.8
      ],
      [
       37.3,
       102.8,
       118.6
      ],
      [
       15.8,
       39.4,
       117.9
      ],
      [
       40.5,
       104.2,
       117.8
      ],
      [
       21.3,
       57.9,
       115.5
      ],
      [
       30.3,
       76.5,
       115.5
      ],
      [
       25.4,
       65.2,
       115.5
      ],
      [
       17.8,
       41.5,
       115.5
      ],
      [
       16.3,
       42.0,
       115.5
      ],
      [
       27.4,
       61.7,
       114.2
      ],
      [
       25.1,
       70.1,
       113.9
      ],
      [
       18.3,
       42.3,
       113.4
      ],
      [
       29.0,
       72.8,
       113.4
      ],
      [
       29.1,
       68.3,
       113.4
      ],
      [
       24.7,
       59.9,
       113.4
      ],
      [
       26.6,
       68.1,
       113.4
      ],
      [
       18.4,
       46.1,
       113.4
      ],
      [
       20.3,
       42.8,
       112.0
      ],
      [
       26.6,
       79.6,
       112.0
      ],
      [
       37.9,
       103.2,
       112.0
      ],
      [
       39.3,
       100.9,
       112.0
      ],
      [
       26.0,
       42.1,
       112.0
      ],
      [
       31.5,
       103.2,
       112.0
      ],
      [
       18.1,
       43.8,
       112.0
      ],
      [
       36.9,
       106.8,
       112.0
      ],
      [
       15.9,
       36.0,
       112.0
      ],
      [
       16.5,
       36.4,
       112.0
      ],
      [
       22.7,
       65.5,
       111.0
      ],
      [
       20.2,
       42.7,
       111.0
      ],
      [
       23.2,
       59.2,
       110.8
      ],
      [
       34.1,
       82.4,
       110.3
      ],
      [
       26.0,
       67.4,
       110.3
      ],
      [
       30.6,
       67.0,
       110.1
      ],
      [
       19.1,
       49.2,
       109.2
      ],
      [
       38.3,
       98.4,
       109.2
      ],
      [
       14.1,
       32.7,
       109.2
      ],
      [
       12.6,
       33.9,
       109.2
      ]
     ],
     "linee": [
      {
       "k": 1.5,
       "label": "1.5 times"
      },
      {
       "k": 2.0,
       "label": "twice as long"
      }
     ],
     "nota": "Each point is a pair of zones, sized by the morning cars; above a line public transport takes more than that multiple of the car's time."
    }
   ],
   "calcolo": [
    "Zones are those of the 2022 travel survey, with calculation points; each has up to 5 points.",
    "Public transport: on foot, bus, tram and metro, departing between 7:45 and 8:15. We take the median. The timetable time gets the measured extra wait at the stop (1.5 minutes). The measured delay on board (5.9 minutes per 100) applies to 57% of the time, the part spent on board. Transfers are not counted: a cautious estimate. By timetable the median ratio is 2.2.",
    "Car, open estimate: fastest route on the road network. Speeds from sensors and buses, 20 seconds per traffic light, plus 5 minutes to park.",
    "Check: on 20 routes out of 20 the open estimate is faster than TomTom (median error 23.5%). The numbers are a range: the open estimate and the same estimate corrected by a factor of 1.3.",
    "Ratio = public transport time divided by car time, in fixed bands. The cars of a pair are the car trips of the survey, from 6 to 10 on a weekday. The big number holds for 47% of morning cars (220,307). The scatter chart shows the 600 pairs with the most cars.",
    "Costs: prices of 24/10/2,026 (self-service fuel within 5 km of Piazza Castello, ACI cost 2,026, GTT fares). Parking: 1.7 euros an hour for 8 hours and 20 days a month.",
    "Value of time: extra cost per month with paid parking, divided by the extra minutes per trip. We count 2 trips a day and 20 days, at 5 euros; with the full ACI cost about 30 euros an hour."
   ],
   "criteri": [
    [
     "Zones",
     "71 travel-survey zones (23 in Turin), up to 5 points each"
    ],
    [
     "Public transport",
     "departure 07:45-8:15 on a weekday, median, walking at 4.8 km/h, at most 120 minutes"
    ],
    [
     "Car, open estimate (A)",
     "fastest route on the road network, with speeds from sensors and buses and 20 seconds per traffic light (median factor 1.8) + 5 minutes"
    ],
    [
     "Car, corrected with the check (B)",
     "driving × 1.3 + 5 minutes: single factor from the check on 20 routes with TomTom"
    ],
    [
     "Sensor period",
     "from 09/10/2,026 to 22/10/2,026"
    ],
    [
     "Ratio bands",
     "under 1.5, 1.5-2, 2-3, over 3"
    ]
   ],
   "limiti": [
    "Outside Turin, trains and other operators are missing: pairs between suburban towns are not in the number. Without metropolitan trains, where they exist, public transport looks slower than it is. The timetable is the scheduled one, corrected with the measured waits and delays.",
    "Car times come from an open model, not measured on the single trip. The TomTom check on 20 routes finds them optimistic: that is why there is a range.",
    "The survey is a sample. Trips within a zone and 653 pairs with no connection (5,616 cars) are not in the comparison.",
    "A Golf as the reference car. The limited traffic zone and parking subscriptions are not counted. The prices are those of one day."
   ],
   "mappa": {
    "id": "imq",
    "nota": "Nella mappa, tema «Spostamenti»: quanti spostamenti partono da ogni zona e dove vanno (indagine 2022, feriale)."
   },
   "fonti": [
    "GTT (official timetables)",
    "5T (traffic sensors)",
    "Piedmont Mobility Agency (2022 travel survey)",
    "OpenStreetMap",
    "Fuel price observatory (Ministry of Enterprises and Made in Italy)",
    "ACI (2026 cost-per-kilometre tables)",
    "GTT (fares and parking)",
    "TomTom (check of car times on 20 routes)"
   ],
   "titolo_breve": "Bus against car",
   "anima": {
    "tipo": "area",
    "didascalia": "From Piazza Castello, at 7:45 a.m. on a weekday. In 30 minutes you reach ~33% of Turin residents by public transport and 91-100% by car (typical traffic, parking included)."
   }
  },
  "forma_de": {
   "tipo_dato": "Datenart: berechnet aus echten Daten, mit Autozeiten bei typischem Verkehr, Sensormessungen und den offiziellen Fahrplänen der Fahrzeuge.",
   "titolo": "Morgens braucht man mit öffentlichen Verkehrsmitteln das 1,9- bis 2,4-Fache der Zeit des Autos",
   "domanda": "Wie viel länger braucht man morgens mit öffentlichen Verkehrsmitteln als mit dem Auto?",
   "numero": {
    "valore": "1,9–2,4",
    "unita": "Mal",
    "testo": "die Autozeit, für die Autofahrten am Morgen zwischen verschiedenen Zonen",
    "breve": "die Zeit des Autos, mit öffentlichen Verkehrsmitteln"
   },
   "principale": {
    "tipo": "barre",
    "titolo": "Autos am Morgen, nach dem Wievielfachen der Autozeit die öffentlichen Verkehrsmittel brauchen",
    "unita": "%",
    "max": 100,
    "nota": "Jeder Balken ist ein Bereich: Mit öffentlichen Verkehrsmitteln braucht man dieses Vielfache der Autozeit. Dunkler Balken: offene Schätzung; heller Balken: dieselbe Schätzung, mit der Kontrolle korrigiert. Paare Turin-Turin und Turin-Umland.",
    "voci": [
     {
      "label": "weniger als das 1,5-Fache",
      "valore": 1,
      "prima": 5,
      "tono": "verde",
      "testo": "1–5% (2.321–10.933 Autos)"
     },
     {
      "label": "das 1,5- bis 2-Fache",
      "valore": 12,
      "prima": 57,
      "tono": "giallo",
      "testo": "12–57% (27.510–125.901 Autos)"
     },
     {
      "label": "das 2- bis 3-Fache",
      "valore": 81,
      "prima": 37,
      "tono": "arancio",
      "testo": "37–81% (81.062–177.478 Autos)"
     },
     {
      "label": "mehr als das 3-Fache",
      "valore": 6,
      "prima": 1,
      "tono": "rosso",
      "testo": "1–6% (2.411–12.997 Autos)"
     }
    ]
   },
   "punti": [
    "Man spart 14-19 Minuten pro Fahrt, aber das Parken kostet ~270 Euro im Monat. Die Zeit kostet so 20-30 Euro pro Stunde.",
    "Ohne Parkgebühr ist das Auto bis ~7 km günstiger als die Monatskarte.",
    "Eine typische häufige Strecke: Crocetta → Centro, ~23 Minuten mit öffentlichen Verkehrsmitteln gegenüber 11–13 mit dem Auto."
   ],
   "altri": [
    {
     "tipo": "linea",
     "titolo": "Wie viel Mal die Autozeit, Stunde für Stunde",
     "unita": "Mal",
     "nota": "Verhältnis zwischen der Zeit mit öffentlichen Verkehrsmitteln und der Autozeit, gewichtet nach den Autos am Morgen, zu 4 Tageszeiten: offene Schätzung und dieselbe Schätzung, mit der Kontrolle korrigiert.",
     "categorie": [
      "8:00",
      "13:00",
      "17:30",
      "21:00"
     ],
     "serie": [
      {
       "label": "offene Schätzung",
       "valori": [
        2.4,
        2.5,
        2.4,
        2.8
       ]
      },
      {
       "label": "mit der Kontrolle korrigiert",
       "valori": [
        1.9,
        2.1,
        2.0,
        2.3
       ]
      }
     ]
    },
    {
     "tipo": "gara",
     "titolo": "Die häufigsten Autofahrten am Morgen: Bus gegen Auto",
     "luoghi": [
      {
       "nome": "Crocetta",
       "arrivo": "Centro",
       "bus": 22.8,
       "auto_min": 11.1,
       "auto_max": 13.0,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,8- bis 2-Fache der Autozeit"
      },
      {
       "nome": "San Paolo",
       "arrivo": "Centro",
       "bus": 33.9,
       "auto_min": 15.0,
       "auto_max": 18.1,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,9- bis 2,3-Fache der Autozeit"
      },
      {
       "nome": "Mirafiori Nord",
       "arrivo": "Santa Rita",
       "bus": 21.3,
       "auto_min": 10.4,
       "auto_max": 12.1,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,8- bis 2-Fache der Autozeit"
      },
      {
       "nome": "Parella",
       "arrivo": "Centro",
       "bus": 27.0,
       "auto_min": 17.0,
       "auto_max": 20.7,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,3- bis 1,6-Fache der Autozeit"
      },
      {
       "nome": "San Donato",
       "arrivo": "Centro",
       "bus": 20.8,
       "auto_min": 12.5,
       "auto_max": 14.8,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,4- bis 1,7-Fache der Autozeit"
      },
      {
       "nome": "Barriera di Milano",
       "arrivo": "Falchera",
       "bus": 26.2,
       "auto_min": 13.1,
       "auto_max": 15.6,
       "giudizio": "mit öffentlichen Verkehrsmitteln das 1,7- bis 2-Fache der Autozeit"
      }
     ],
     "scelto": 0,
     "nota": "Bus und Auto fahren zusammen los, nacheinander, für die 6 häufigsten Autofahrten am Morgen. Für das Auto gibt es eine Zeit mit der Spanne aus der Kontrolle, Parken inklusive."
    },
    {
     "tipo": "barre_gruppi",
     "titolo": "Ein Monat Arbeit nahe dem Zentrum: was er kostet",
     "unita": "Euro",
     "nota": "Der helle Balken sind die Vollkosten des Autos (ACI). Die ermäßigten Tarife sind die von GTT für Jugendliche und ältere Menschen, mit ISEE-Bescheinigung.",
     "gruppi": [
      {
       "label": "Auto, bezahltes Parken auf der Straße",
       "voci": [
        {
         "label": "Kraftstoff und Parken",
         "valore": 307,
         "prima": 404,
         "tono": "rosso",
         "testo": "307 (404 bei Vollkosten)"
        }
       ]
      },
      {
       "label": "Auto, kostenloser Parkplatz bei der Arbeit",
       "voci": [
        {
         "label": "Nur Kraftstoff",
         "valore": 35,
         "prima": 132,
         "tono": "rosso",
         "testo": "35 (132 bei Vollkosten)"
        }
       ]
      },
      {
       "label": "Öffentlicher Verkehr",
       "voci": [
        {
         "label": "Tickets (40 Fahrten)",
         "valore": 80,
         "tono": "verde",
         "testo": "80"
        },
        {
         "label": "Monatskarte",
         "valore": 38,
         "tono": "verde",
         "testo": "38"
        },
        {
         "label": "Jahreskarte, pro Monat",
         "valore": 26,
         "tono": "verde",
         "testo": "26"
        }
       ]
      }
     ]
    },
    {
     "tipo": "dispersione",
     "titolo": "Zeit mit dem Auto und mit öffentlichen Verkehrsmitteln, ein Zonenpaar pro Punkt",
     "xlabel": "Minuten mit dem Auto (morgens, offene Schätzung)",
     "ylabel": "Minuten mit öffentlichen Verkehrsmitteln",
     "punti": [
      [
       11.1,
       22.8,
       1355.3
      ],
      [
       15.0,
       33.9,
       1341.8
      ],
      [
       10.4,
       21.3,
       1324.4
      ],
      [
       17.0,
       27.0,
       1277.0
      ],
      [
       12.5,
       20.8,
       1269.4
      ],
      [
       13.1,
       26.2,
       1208.2
      ],
      [
       19.3,
       46.0,
       1149.2
      ],
      [
       15.9,
       40.2,
       1107.8
      ],
      [
       39.0,
       84.3,
       1081.8
      ],
      [
       9.6,
       17.2,
       1038.1
      ],
      [
       15.8,
       35.8,
       969.9
      ],
      [
       15.0,
       33.1,
       968.1
      ],
      [
       9.4,
       17.2,
       957.2
      ],
      [
       23.9,
       47.5,
       940.7
      ],
      [
       11.1,
       22.4,
       938.8
      ],
      [
       15.0,
       36.1,
       928.7
      ],
      [
       16.8,
       40.9,
       916.7
      ],
      [
       31.3,
       67.0,
       910.0
      ],
      [
       15.1,
       32.9,
       900.6
      ],
      [
       14.9,
       37.8,
       894.4
      ],
      [
       11.7,
       24.6,
       893.3
      ],
      [
       12.2,
       26.1,
       889.9
      ],
      [
       19.8,
       42.1,
       888.0
      ],
      [
       17.0,
       29.9,
       818.9
      ],
      [
       21.0,
       45.2,
       796.7
      ],
      [
       17.5,
       37.9,
       795.1
      ],
      [
       10.1,
       21.0,
       789.0
      ],
      [
       17.3,
       33.8,
       779.1
      ],
      [
       14.0,
       32.9,
       762.5
      ],
      [
       22.0,
       53.2,
       753.4
      ],
      [
       11.6,
       33.8,
       751.2
      ],
      [
       12.6,
       26.6,
       737.2
      ],
      [
       22.3,
       85.6,
       718.7
      ],
      [
       10.4,
       20.2,
       714.6
      ],
      [
       15.1,
       37.9,
       714.1
      ],
      [
       11.7,
       26.2,
       706.6
      ],
      [
       30.3,
       67.1,
       702.1
      ],
      [
       12.0,
       24.8,
       698.0
      ],
      [
       17.0,
       32.2,
       696.9
      ],
      [
       26.1,
       53.5,
       690.4
      ],
      [
       28.6,
       76.6,
       687.3
      ],
      [
       12.3,
       25.4,
       685.0
      ],
      [
       20.4,
       27.8,
       672.4
      ],
      [
       14.8,
       31.7,
       671.0
      ],
      [
       11.0,
       25.1,
       666.8
      ],
      [
       32.5,
       76.4,
       659.4
      ],
      [
       21.9,
       54.2,
       644.0
      ],
      [
       14.0,
       35.3,
       627.3
      ],
      [
       9.5,
       18.0,
       622.4
      ],
      [
       11.8,
       24.5,
       620.3
      ],
      [
       13.1,
       29.6,
       615.4
      ],
      [
       17.0,
       39.7,
       614.3
      ],
      [
       14.9,
       37.2,
       614.1
      ],
      [
       12.7,
       25.7,
       607.7
      ],
      [
       13.7,
       29.6,
       606.6
      ],
      [
       14.4,
       36.6,
       601.6
      ],
      [
       11.4,
       32.9,
       592.7
      ],
      [
       16.2,
       38.7,
       589.8
      ],
      [
       15.3,
       36.7,
       582.5
      ],
      [
       21.7,
       53.3,
       580.1
      ],
      [
       15.7,
       26.4,
       574.5
      ],
      [
       13.4,
       32.4,
       570.6
      ],
      [
       18.9,
       58.4,
       568.2
      ],
      [
       14.1,
       26.9,
       562.6
      ],
      [
       28.3,
       90.1,
       543.7
      ],
      [
       13.7,
       26.4,
       543.0
      ],
      [
       16.7,
       42.0,
       540.9
      ],
      [
       10.3,
       23.8,
       540.3
      ],
      [
       13.9,
       33.4,
       539.8
      ],
      [
       15.6,
       33.2,
       527.7
      ],
      [
       29.7,
       72.6,
       520.3
      ],
      [
       26.9,
       75.5,
       519.9
      ],
      [
       13.2,
       31.9,
       519.7
      ],
      [
       12.0,
       27.2,
       517.1
      ],
      [
       25.0,
       60.3,
       515.6
      ],
      [
       31.3,
       75.0,
       514.3
      ],
      [
       15.2,
       42.4,
       512.4
      ],
      [
       27.8,
       65.7,
       504.1
      ],
      [
       14.0,
       29.3,
       503.9
      ],
      [
       16.2,
       35.3,
       498.7
      ],
      [
       14.6,
       31.3,
       496.3
      ],
      [
       9.5,
       17.5,
       494.3
      ],
      [
       20.3,
       50.2,
       490.1
      ],
      [
       18.7,
       41.5,
       489.2
      ],
      [
       11.0,
       25.5,
       488.9
      ],
      [
       34.4,
       77.9,
       488.2
      ],
      [
       11.8,
       24.2,
       481.0
      ],
      [
       16.4,
       40.9,
       478.8
      ],
      [
       23.9,
       58.2,
       478.7
      ],
      [
       21.2,
       50.6,
       476.8
      ],
      [
       19.8,
       48.9,
       467.9
      ],
      [
       12.7,
       28.5,
       466.7
      ],
      [
       14.6,
       30.1,
       462.0
      ],
      [
       13.0,
       28.7,
       459.7
      ],
      [
       41.1,
       81.8,
       458.7
      ],
      [
       20.0,
       28.4,
       458.5
      ],
      [
       17.6,
       39.9,
       456.6
      ],
      [
       13.5,
       25.1,
       456.0
      ],
      [
       26.4,
       60.5,
       454.7
      ],
      [
       10.8,
       22.5,
       452.9
      ],
      [
       22.2,
       57.3,
       452.3
      ],
      [
       35.8,
       90.3,
       449.8
      ],
      [
       14.3,
       34.2,
       448.6
      ],
      [
       35.1,
       97.3,
       448.4
      ],
      [
       25.9,
       75.7,
       445.5
      ],
      [
       17.7,
       38.5,
       443.8
      ],
      [
       25.0,
       49.5,
       442.8
      ],
      [
       17.9,
       43.0,
       439.9
      ],
      [
       21.9,
       58.6,
       438.4
      ],
      [
       11.7,
       23.6,
       437.5
      ],
      [
       25.9,
       65.4,
       431.9
      ],
      [
       24.1,
       61.7,
       431.8
      ],
      [
       14.7,
       34.8,
       431.4
      ],
      [
       27.3,
       72.4,
       428.4
      ],
      [
       16.6,
       40.1,
       428.4
      ],
      [
       33.2,
       85.5,
       426.2
      ],
      [
       14.6,
       38.4,
       423.2
      ],
      [
       18.7,
       44.2,
       422.6
      ],
      [
       11.4,
       20.3,
       421.9
      ],
      [
       20.8,
       50.7,
       421.1
      ],
      [
       10.7,
       21.2,
       419.2
      ],
      [
       21.6,
       56.7,
       411.0
      ],
      [
       35.1,
       77.4,
       410.3
      ],
      [
       19.5,
       57.1,
       410.0
      ],
      [
       24.3,
       35.3,
       409.6
      ],
      [
       21.8,
       56.8,
       409.5
      ],
      [
       24.5,
       54.4,
       404.3
      ],
      [
       24.9,
       49.2,
       403.5
      ],
      [
       22.7,
       57.8,
       402.7
      ],
      [
       26.9,
       64.7,
       399.0
      ],
      [
       12.2,
       27.2,
       398.4
      ],
      [
       26.5,
       68.0,
       396.9
      ],
      [
       12.1,
       30.8,
       396.9
      ],
      [
       25.1,
       63.1,
       395.5
      ],
      [
       16.6,
       34.9,
       391.8
      ],
      [
       25.3,
       54.3,
       389.9
      ],
      [
       22.4,
       49.6,
       389.6
      ],
      [
       38.5,
       108.8,
       386.9
      ],
      [
       16.9,
       30.4,
       386.6
      ],
      [
       13.6,
       30.6,
       384.3
      ],
      [
       15.3,
       29.9,
       383.2
      ],
      [
       18.6,
       85.7,
       383.2
      ],
      [
       24.5,
       65.9,
       382.4
      ],
      [
       22.1,
       59.9,
       382.0
      ],
      [
       20.2,
       57.4,
       379.4
      ],
      [
       18.2,
       41.2,
       377.6
      ],
      [
       14.6,
       34.0,
       377.4
      ],
      [
       15.1,
       26.6,
       376.5
      ],
      [
       14.8,
       39.4,
       369.2
      ],
      [
       16.3,
       33.1,
       368.7
      ],
      [
       18.4,
       39.8,
       367.3
      ],
      [
       19.1,
       46.3,
       366.6
      ],
      [
       24.4,
       83.3,
       365.7
      ],
      [
       12.1,
       21.4,
       365.5
      ],
      [
       26.6,
       78.5,
       363.3
      ],
      [
       13.4,
       30.6,
       362.7
      ],
      [
       10.1,
       23.1,
       356.4
      ],
      [
       12.0,
       23.6,
       355.0
      ],
      [
       17.5,
       41.9,
       353.0
      ],
      [
       20.4,
       55.6,
       352.5
      ],
      [
       15.7,
       19.2,
       352.1
      ],
      [
       24.3,
       53.7,
       350.1
      ],
      [
       15.2,
       39.7,
       348.3
      ],
      [
       19.6,
       47.8,
       347.8
      ],
      [
       34.4,
       75.3,
       346.3
      ],
      [
       27.2,
       75.0,
       346.1
      ],
      [
       24.6,
       67.1,
       345.7
      ],
      [
       16.2,
       34.6,
       340.6
      ],
      [
       14.5,
       44.7,
       340.0
      ],
      [
       21.6,
       53.8,
       339.6
      ],
      [
       35.5,
       87.3,
       338.3
      ],
      [
       18.8,
       48.7,
       336.5
      ],
      [
       21.0,
       57.6,
       336.5
      ],
      [
       33.3,
       83.6,
       335.5
      ],
      [
       21.2,
       55.3,
       335.0
      ],
      [
       26.5,
       64.1,
       333.8
      ],
      [
       33.7,
       92.2,
       333.6
      ],
      [
       32.9,
       78.5,
       333.5
      ],
      [
       17.3,
       34.0,
       332.2
      ],
      [
       29.9,
       87.0,
       331.5
      ],
      [
       29.1,
       50.7,
       331.5
      ],
      [
       22.9,
       68.0,
       330.5
      ],
      [
       21.6,
       55.6,
       329.9
      ],
      [
       26.0,
       46.5,
       329.1
      ],
      [
       31.7,
       69.2,
       328.2
      ],
      [
       24.3,
       57.5,
       328.0
      ],
      [
       19.5,
       57.5,
       326.5
      ],
      [
       31.4,
       70.9,
       323.5
      ],
      [
       11.9,
       26.3,
       322.3
      ],
      [
       9.6,
       21.3,
       322.1
      ],
      [
       31.3,
       67.9,
       321.4
      ],
      [
       16.5,
       36.7,
       318.2
      ],
      [
       24.7,
       50.9,
       317.7
      ],
      [
       27.8,
       84.8,
       311.9
      ],
      [
       34.6,
       98.7,
       310.7
      ],
      [
       12.8,
       28.7,
       309.9
      ],
      [
       27.6,
       63.7,
       307.1
      ],
      [
       29.5,
       73.7,
       306.3
      ],
      [
       12.0,
       27.4,
       305.1
      ],
      [
       16.9,
       38.5,
       304.4
      ],
      [
       23.3,
       56.3,
       304.2
      ],
      [
       19.5,
       55.6,
       303.6
      ],
      [
       29.6,
       66.2,
       303.4
      ],
      [
       32.9,
       81.1,
       302.8
      ],
      [
       30.7,
       72.6,
       302.3
      ],
      [
       32.1,
       76.2,
       300.8
      ],
      [
       12.4,
       21.2,
       299.5
      ],
      [
       20.1,
       52.0,
       299.2
      ],
      [
       24.2,
       59.8,
       298.9
      ],
      [
       20.6,
       50.3,
       298.6
      ],
      [
       21.6,
       57.6,
       297.1
      ],
      [
       20.5,
       57.4,
       296.5
      ],
      [
       24.8,
       61.1,
       296.0
      ],
      [
       37.3,
       91.2,
       295.0
      ],
      [
       32.0,
       73.8,
       294.0
      ],
      [
       14.8,
       36.4,
       292.7
      ],
      [
       40.4,
       90.1,
       291.8
      ],
      [
       20.0,
       49.0,
       290.8
      ],
      [
       11.2,
       23.5,
       290.5
      ],
      [
       24.9,
       63.7,
       289.4
      ],
      [
       24.4,
       56.0,
       288.9
      ],
      [
       32.3,
       78.6,
       288.6
      ],
      [
       13.9,
       37.7,
       284.7
      ],
      [
       16.7,
       41.4,
       283.1
      ],
      [
       9.7,
       21.0,
       282.6
      ],
      [
       17.7,
       45.6,
       282.2
      ],
      [
       20.5,
       45.1,
       281.8
      ],
      [
       14.5,
       41.1,
       281.7
      ],
      [
       21.3,
       60.8,
       280.3
      ],
      [
       21.7,
       60.1,
       278.1
      ],
      [
       13.7,
       26.8,
       274.9
      ],
      [
       31.8,
       87.3,
       274.4
      ],
      [
       27.5,
       71.7,
       273.4
      ],
      [
       15.9,
       37.2,
       273.2
      ],
      [
       28.0,
       49.1,
       272.4
      ],
      [
       37.5,
       80.6,
       271.8
      ],
      [
       35.4,
       83.1,
       271.3
      ],
      [
       23.9,
       64.9,
       271.0
      ],
      [
       15.7,
       34.4,
       270.6
      ],
      [
       12.6,
       26.9,
       270.2
      ],
      [
       23.3,
       47.1,
       270.1
      ],
      [
       34.1,
       103.0,
       269.7
      ],
      [
       23.4,
       65.7,
       269.7
      ],
      [
       34.4,
       87.9,
       268.9
      ],
      [
       15.4,
       19.2,
       268.5
      ],
      [
       24.6,
       58.6,
       267.8
      ],
      [
       20.8,
       39.8,
       264.3
      ],
      [
       25.4,
       63.9,
       263.3
      ],
      [
       20.3,
       54.6,
       262.3
      ],
      [
       21.6,
       45.1,
       261.5
      ],
      [
       24.1,
       52.6,
       261.2
      ],
      [
       15.6,
       37.4,
       260.2
      ],
      [
       9.9,
       19.5,
       259.7
      ],
      [
       12.6,
       31.5,
       258.2
      ],
      [
       41.0,
       83.5,
       257.3
      ],
      [
       20.7,
       49.6,
       256.8
      ],
      [
       32.7,
       79.8,
       255.1
      ],
      [
       40.9,
       82.4,
       254.4
      ],
      [
       36.4,
       108.1,
       253.6
      ],
      [
       44.3,
       93.4,
       253.1
      ],
      [
       9.0,
       17.9,
       252.2
      ],
      [
       24.9,
       52.5,
       251.6
      ],
      [
       13.3,
       32.4,
       251.5
      ],
      [
       23.2,
       59.9,
       250.1
      ],
      [
       23.0,
       40.0,
       248.3
      ],
      [
       26.8,
       51.9,
       247.4
      ],
      [
       17.3,
       37.4,
       244.8
      ],
      [
       13.8,
       31.3,
       243.9
      ],
      [
       22.5,
       47.1,
       243.6
      ],
      [
       25.2,
       58.3,
       243.6
      ],
      [
       14.3,
       31.7,
       243.6
      ],
      [
       20.5,
       44.6,
       243.0
      ],
      [
       34.1,
       82.0,
       242.3
      ],
      [
       22.5,
       46.3,
       242.2
      ],
      [
       25.7,
       65.1,
       241.4
      ],
      [
       15.1,
       32.9,
       241.0
      ],
      [
       35.0,
       96.0,
       240.6
      ],
      [
       13.1,
       42.2,
       240.0
      ],
      [
       28.0,
       68.6,
       238.3
      ],
      [
       29.8,
       76.0,
       236.1
      ],
      [
       16.1,
       26.5,
       235.8
      ],
      [
       24.7,
       49.4,
       234.9
      ],
      [
       24.5,
       55.7,
       234.7
      ],
      [
       22.2,
       49.4,
       234.6
      ],
      [
       19.7,
       49.7,
       233.6
      ],
      [
       25.4,
       71.4,
       233.3
      ],
      [
       17.9,
       46.3,
       231.7
      ],
      [
       26.2,
       65.0,
       231.5
      ],
      [
       44.7,
       104.4,
       230.9
      ],
      [
       23.3,
       51.1,
       228.8
      ],
      [
       12.5,
       27.7,
       228.3
      ],
      [
       18.2,
       44.5,
       228.1
      ],
      [
       25.1,
       66.4,
       227.0
      ],
      [
       25.4,
       83.3,
       226.3
      ],
      [
       16.1,
       38.8,
       225.6
      ],
      [
       28.4,
       62.5,
       225.4
      ],
      [
       21.2,
       55.2,
       225.1
      ],
      [
       27.6,
       68.5,
       224.1
      ],
      [
       11.6,
       26.4,
       223.2
      ],
      [
       34.9,
       98.9,
       222.3
      ],
      [
       15.3,
       34.7,
       222.1
      ],
      [
       32.6,
       74.6,
       221.0
      ],
      [
       11.7,
       28.3,
       220.4
      ],
      [
       14.5,
       26.5,
       219.8
      ],
      [
       13.7,
       24.6,
       218.7
      ],
      [
       23.6,
       56.1,
       218.3
      ],
      [
       24.6,
       79.5,
       217.8
      ],
      [
       32.8,
       72.3,
       217.1
      ],
      [
       15.2,
       33.3,
       216.9
      ],
      [
       34.1,
       109.0,
       216.3
      ],
      [
       34.5,
       64.5,
       215.9
      ],
      [
       25.6,
       75.8,
       215.8
      ],
      [
       39.3,
       101.7,
       215.6
      ],
      [
       22.1,
       57.2,
       215.3
      ],
      [
       26.0,
       70.8,
       214.1
      ],
      [
       20.9,
       54.8,
       214.0
      ],
      [
       13.1,
       28.4,
       213.2
      ],
      [
       27.3,
       76.3,
       212.7
      ],
      [
       33.1,
       82.6,
       212.0
      ],
      [
       29.0,
       97.7,
       211.8
      ],
      [
       32.3,
       67.5,
       211.3
      ],
      [
       18.0,
       53.4,
       211.2
      ],
      [
       27.2,
       64.6,
       210.7
      ],
      [
       25.5,
       61.2,
       209.8
      ],
      [
       20.0,
       46.2,
       209.0
      ],
      [
       20.4,
       54.4,
       208.2
      ],
      [
       46.3,
       107.6,
       208.1
      ],
      [
       25.3,
       64.8,
       207.6
      ],
      [
       41.6,
       90.9,
       207.5
      ],
      [
       16.3,
       32.5,
       206.7
      ],
      [
       40.9,
       86.5,
       206.4
      ],
      [
       20.1,
       47.2,
       206.2
      ],
      [
       20.1,
       54.1,
       206.2
      ],
      [
       19.7,
       47.3,
       206.1
      ],
      [
       31.8,
       70.2,
       206.0
      ],
      [
       18.5,
       58.7,
       205.9
      ],
      [
       30.0,
       101.0,
       205.6
      ],
      [
       26.3,
       60.0,
       205.0
      ],
      [
       21.9,
       44.5,
       204.7
      ],
      [
       24.8,
       79.7,
       204.3
      ],
      [
       30.1,
       60.0,
       204.3
      ],
      [
       34.0,
       82.1,
       204.0
      ],
      [
       35.1,
       81.4,
       203.9
      ],
      [
       21.8,
       60.5,
       203.8
      ],
      [
       26.9,
       96.1,
       203.7
      ],
      [
       18.5,
       46.6,
       203.5
      ],
      [
       19.5,
       45.5,
       203.4
      ],
      [
       35.1,
       78.0,
       203.4
      ],
      [
       20.8,
       49.8,
       203.2
      ],
      [
       37.3,
       88.7,
       202.3
      ],
      [
       27.3,
       71.2,
       201.9
      ],
      [
       29.3,
       61.9,
       201.7
      ],
      [
       23.5,
       57.6,
       201.5
      ],
      [
       15.4,
       28.5,
       201.5
      ],
      [
       16.3,
       29.3,
       201.2
      ],
      [
       18.6,
       45.7,
       200.7
      ],
      [
       29.5,
       65.4,
       200.5
      ],
      [
       33.6,
       86.4,
       200.3
      ],
      [
       26.0,
       90.0,
       199.7
      ],
      [
       14.4,
       29.3,
       199.4
      ],
      [
       13.7,
       33.4,
       199.3
      ],
      [
       26.6,
       58.8,
       198.8
      ],
      [
       30.9,
       59.8,
       197.7
      ],
      [
       32.0,
       81.4,
       197.7
      ],
      [
       23.4,
       51.9,
       196.4
      ],
      [
       30.7,
       73.5,
       195.7
      ],
      [
       29.1,
       70.7,
       195.6
      ],
      [
       15.5,
       35.6,
       195.3
      ],
      [
       16.5,
       44.9,
       194.7
      ],
      [
       12.2,
       28.8,
       194.6
      ],
      [
       29.6,
       80.2,
       194.1
      ],
      [
       16.2,
       36.7,
       193.8
      ],
      [
       32.9,
       105.0,
       193.0
      ],
      [
       23.2,
       48.7,
       192.7
      ],
      [
       39.9,
       103.4,
       192.4
      ],
      [
       15.2,
       35.1,
       192.2
      ],
      [
       34.9,
       85.2,
       191.6
      ],
      [
       18.8,
       44.6,
       191.5
      ],
      [
       31.1,
       62.1,
       190.6
      ],
      [
       37.2,
       92.7,
       190.5
      ],
      [
       24.7,
       65.4,
       190.5
      ],
      [
       27.0,
       82.4,
       190.5
      ],
      [
       30.2,
       88.9,
       190.2
      ],
      [
       12.8,
       36.3,
       190.2
      ],
      [
       28.1,
       61.2,
       189.6
      ],
      [
       19.1,
       45.0,
       189.4
      ],
      [
       41.8,
       113.4,
       188.8
      ],
      [
       24.4,
       56.0,
       188.6
      ],
      [
       20.0,
       47.8,
       188.5
      ],
      [
       42.4,
       88.8,
       187.6
      ],
      [
       44.0,
       90.9,
       187.3
      ],
      [
       27.4,
       67.5,
       186.9
      ],
      [
       26.5,
       60.9,
       186.9
      ],
      [
       26.1,
       67.8,
       186.9
      ],
      [
       16.3,
       40.6,
       186.8
      ],
      [
       30.5,
       78.1,
       186.4
      ],
      [
       49.2,
       102.1,
       186.4
      ],
      [
       35.1,
       89.2,
       186.2
      ],
      [
       34.1,
       85.8,
       185.9
      ],
      [
       19.6,
       43.6,
       185.7
      ],
      [
       23.1,
       48.0,
       185.5
      ],
      [
       15.7,
       42.7,
       185.4
      ],
      [
       18.2,
       33.9,
       185.1
      ],
      [
       21.2,
       58.2,
       184.5
      ],
      [
       45.5,
       96.5,
       184.1
      ],
      [
       38.6,
       89.9,
       183.3
      ],
      [
       39.5,
       92.2,
       183.3
      ],
      [
       12.8,
       32.1,
       183.2
      ],
      [
       32.0,
       87.2,
       183.0
      ],
      [
       26.2,
       72.5,
       182.4
      ],
      [
       29.9,
       70.0,
       182.4
      ],
      [
       40.0,
       95.4,
       181.8
      ],
      [
       35.0,
       81.4,
       181.2
      ],
      [
       23.3,
       68.0,
       181.2
      ],
      [
       25.6,
       72.8,
       181.1
      ],
      [
       23.4,
       60.8,
       180.8
      ],
      [
       25.2,
       69.6,
       179.9
      ],
      [
       25.1,
       52.0,
       179.7
      ],
      [
       19.7,
       38.2,
       179.6
      ],
      [
       35.3,
       97.2,
       179.5
      ],
      [
       19.1,
       63.1,
       179.5
      ],
      [
       18.6,
       49.4,
       179.5
      ],
      [
       37.7,
       95.9,
       179.2
      ],
      [
       18.7,
       57.7,
       178.4
      ],
      [
       27.3,
       68.5,
       177.9
      ],
      [
       32.6,
       64.7,
       177.9
      ],
      [
       19.0,
       50.4,
       177.4
      ],
      [
       28.5,
       54.2,
       177.3
      ],
      [
       27.2,
       118.1,
       177.0
      ],
      [
       12.2,
       32.0,
       176.7
      ],
      [
       46.6,
       99.2,
       176.2
      ],
      [
       35.6,
       92.6,
       176.0
      ],
      [
       11.9,
       23.3,
       175.3
      ],
      [
       20.7,
       47.9,
       175.0
      ],
      [
       22.3,
       60.4,
       174.5
      ],
      [
       12.4,
       29.0,
       173.9
      ],
      [
       13.5,
       33.9,
       173.6
      ],
      [
       27.2,
       72.8,
       173.5
      ],
      [
       24.2,
       64.2,
       173.4
      ],
      [
       26.1,
       59.4,
       173.2
      ],
      [
       14.9,
       29.0,
       173.1
      ],
      [
       27.4,
       66.7,
       173.1
      ],
      [
       26.8,
       57.6,
       173.0
      ],
      [
       25.7,
       70.7,
       173.0
      ],
      [
       15.8,
       43.6,
       173.0
      ],
      [
       42.4,
       104.4,
       173.0
      ],
      [
       22.0,
       45.6,
       172.3
      ],
      [
       30.0,
       97.6,
       172.0
      ],
      [
       30.8,
       66.1,
       171.6
      ],
      [
       37.1,
       119.1,
       171.3
      ],
      [
       39.5,
       94.4,
       171.3
      ],
      [
       31.6,
       81.8,
       171.2
      ],
      [
       16.3,
       27.0,
       171.0
      ],
      [
       45.6,
       103.9,
       170.7
      ],
      [
       20.3,
       50.0,
       170.0
      ],
      [
       21.5,
       53.5,
       169.8
      ],
      [
       16.2,
       43.6,
       169.6
      ],
      [
       21.8,
       81.6,
       169.4
      ],
      [
       15.5,
       36.4,
       169.2
      ],
      [
       31.1,
       97.7,
       168.9
      ],
      [
       17.6,
       38.4,
       168.6
      ],
      [
       28.1,
       72.3,
       168.1
      ],
      [
       23.7,
       90.3,
       168.1
      ],
      [
       10.2,
       20.3,
       167.9
      ],
      [
       14.8,
       36.3,
       167.5
      ],
      [
       34.2,
       66.4,
       167.2
      ],
      [
       36.9,
       92.3,
       166.7
      ],
      [
       29.1,
       77.5,
       166.7
      ],
      [
       19.7,
       38.2,
       166.1
      ],
      [
       40.8,
       96.9,
       165.5
      ],
      [
       41.0,
       117.3,
       165.4
      ],
      [
       25.4,
       102.8,
       165.4
      ],
      [
       14.8,
       36.5,
       164.6
      ],
      [
       12.6,
       35.6,
       163.9
      ],
      [
       17.3,
       49.1,
       163.8
      ],
      [
       11.9,
       25.6,
       163.6
      ],
      [
       30.8,
       76.8,
       163.5
      ],
      [
       20.7,
       53.9,
       163.3
      ],
      [
       30.8,
       73.7,
       163.0
      ],
      [
       30.1,
       82.6,
       162.2
      ],
      [
       28.0,
       71.8,
       161.5
      ],
      [
       24.5,
       67.9,
       161.5
      ],
      [
       23.6,
       74.9,
       161.5
      ],
      [
       19.3,
       58.0,
       161.4
      ],
      [
       35.2,
       91.5,
       160.9
      ],
      [
       19.8,
       58.5,
       160.0
      ],
      [
       24.5,
       42.5,
       159.7
      ],
      [
       20.0,
       56.7,
       159.5
      ],
      [
       24.5,
       54.6,
       159.4
      ],
      [
       27.6,
       76.2,
       159.3
      ],
      [
       27.9,
       56.3,
       158.2
      ],
      [
       38.8,
       87.1,
       158.2
      ],
      [
       28.2,
       60.6,
       157.9
      ],
      [
       18.1,
       35.6,
       157.8
      ],
      [
       26.5,
       74.5,
       157.5
      ],
      [
       18.5,
       48.2,
       157.3
      ],
      [
       14.9,
       32.7,
       157.3
      ],
      [
       34.0,
       99.7,
       156.5
      ],
      [
       25.6,
       44.0,
       155.8
      ],
      [
       30.1,
       78.3,
       155.6
      ],
      [
       24.1,
       54.1,
       155.4
      ],
      [
       29.6,
       58.1,
       155.2
      ],
      [
       26.6,
       97.3,
       155.1
      ],
      [
       25.6,
       87.9,
       154.9
      ],
      [
       19.1,
       40.6,
       154.5
      ],
      [
       39.4,
       94.7,
       154.5
      ],
      [
       29.4,
       68.2,
       154.1
      ],
      [
       19.2,
       47.5,
       153.6
      ],
      [
       23.7,
       55.0,
       152.4
      ],
      [
       13.1,
       29.0,
       152.3
      ],
      [
       20.1,
       57.1,
       152.3
      ],
      [
       34.9,
       95.3,
       151.5
      ],
      [
       27.1,
       62.5,
       151.3
      ],
      [
       24.4,
       71.5,
       151.2
      ],
      [
       21.7,
       64.0,
       150.6
      ],
      [
       21.1,
       49.1,
       150.2
      ],
      [
       18.2,
       42.9,
       149.8
      ],
      [
       20.8,
       51.6,
       148.6
      ],
      [
       28.1,
       70.6,
       148.5
      ],
      [
       14.6,
       34.0,
       148.2
      ],
      [
       25.3,
       67.2,
       147.4
      ],
      [
       17.1,
       36.6,
       147.2
      ],
      [
       20.3,
       51.3,
       146.3
      ],
      [
       19.1,
       31.0,
       146.1
      ],
      [
       14.4,
       33.4,
       145.2
      ],
      [
       22.2,
       52.5,
       145.0
      ],
      [
       33.9,
       93.1,
       144.6
      ],
      [
       22.4,
       53.2,
       143.8
      ],
      [
       24.1,
       55.8,
       143.2
      ],
      [
       44.7,
       105.7,
       142.8
      ],
      [
       14.6,
       36.9,
       142.2
      ],
      [
       24.0,
       61.1,
       142.1
      ],
      [
       20.4,
       54.2,
       142.1
      ],
      [
       15.9,
       40.3,
       141.5
      ],
      [
       19.6,
       48.2,
       141.1
      ],
      [
       22.4,
       47.0,
       140.8
      ],
      [
       31.8,
       74.8,
       140.6
      ],
      [
       18.7,
       38.0,
       140.1
      ],
      [
       36.1,
       91.9,
       139.1
      ],
      [
       26.6,
       67.2,
       139.1
      ],
      [
       22.7,
       55.1,
       136.6
      ],
      [
       20.2,
       53.5,
       136.6
      ],
      [
       36.2,
       104.3,
       135.8
      ],
      [
       36.9,
       73.6,
       135.1
      ],
      [
       34.5,
       117.0,
       132.9
      ],
      [
       24.5,
       90.4,
       132.9
      ],
      [
       27.4,
       64.3,
       131.1
      ],
      [
       25.3,
       62.8,
       130.6
      ],
      [
       20.4,
       60.2,
       130.3
      ],
      [
       19.6,
       49.1,
       129.1
      ],
      [
       27.2,
       97.0,
       128.8
      ],
      [
       25.2,
       66.3,
       128.8
      ],
      [
       17.6,
       29.6,
       125.9
      ],
      [
       28.8,
       70.9,
       125.8
      ],
      [
       39.0,
       85.6,
       125.8
      ],
      [
       26.5,
       117.8,
       124.6
      ],
      [
       30.5,
       71.3,
       122.4
      ],
      [
       46.8,
       109.9,
       122.4
      ],
      [
       25.9,
       64.8,
       122.0
      ],
      [
       32.5,
       64.7,
       121.7
      ],
      [
       21.3,
       58.0,
       120.0
      ],
      [
       24.7,
       61.2,
       119.6
      ],
      [
       39.4,
       99.2,
       118.8
      ],
      [
       29.0,
       55.8,
       118.8
      ],
      [
       37.3,
       102.8,
       118.6
      ],
      [
       15.8,
       39.4,
       117.9
      ],
      [
       40.5,
       104.2,
       117.8
      ],
      [
       21.3,
       57.9,
       115.5
      ],
      [
       30.3,
       76.5,
       115.5
      ],
      [
       25.4,
       65.2,
       115.5
      ],
      [
       17.8,
       41.5,
       115.5
      ],
      [
       16.3,
       42.0,
       115.5
      ],
      [
       27.4,
       61.7,
       114.2
      ],
      [
       25.1,
       70.1,
       113.9
      ],
      [
       18.3,
       42.3,
       113.4
      ],
      [
       29.0,
       72.8,
       113.4
      ],
      [
       29.1,
       68.3,
       113.4
      ],
      [
       24.7,
       59.9,
       113.4
      ],
      [
       26.6,
       68.1,
       113.4
      ],
      [
       18.4,
       46.1,
       113.4
      ],
      [
       20.3,
       42.8,
       112.0
      ],
      [
       26.6,
       79.6,
       112.0
      ],
      [
       37.9,
       103.2,
       112.0
      ],
      [
       39.3,
       100.9,
       112.0
      ],
      [
       26.0,
       42.1,
       112.0
      ],
      [
       31.5,
       103.2,
       112.0
      ],
      [
       18.1,
       43.8,
       112.0
      ],
      [
       36.9,
       106.8,
       112.0
      ],
      [
       15.9,
       36.0,
       112.0
      ],
      [
       16.5,
       36.4,
       112.0
      ],
      [
       22.7,
       65.5,
       111.0
      ],
      [
       20.2,
       42.7,
       111.0
      ],
      [
       23.2,
       59.2,
       110.8
      ],
      [
       34.1,
       82.4,
       110.3
      ],
      [
       26.0,
       67.4,
       110.3
      ],
      [
       30.6,
       67.0,
       110.1
      ],
      [
       19.1,
       49.2,
       109.2
      ],
      [
       38.3,
       98.4,
       109.2
      ],
      [
       14.1,
       32.7,
       109.2
      ],
      [
       12.6,
       33.9,
       109.2
      ]
     ],
     "linee": [
      {
       "k": 1.5,
       "label": "1,5 Mal"
      },
      {
       "k": 2.0,
       "label": "doppelt so lange"
      }
     ],
     "nota": "Jeder Punkt ist ein Zonenpaar, so groß wie die Zahl der Autos am Morgen; über einer Linie brauchen die öffentlichen Verkehrsmittel mehr als dieses Vielfache der Autozeit."
    }
   ],
   "calcolo": [
    "Die Zonen stammen aus der Mobilitätserhebung 2022 mit Berechnungspunkten; jede hat bis zu 5 Punkte.",
    "Öffentlicher Verkehr: zu Fuß, Bus, Tram und Metro, Abfahrt zwischen 7:45 und 8:15 Uhr. Es gilt der Median. Zur Fahrplanzeit kommt die gemessene Wartezeit an der Haltestelle hinzu (1,5 Minuten). Die gemessene Verspätung an Bord (5,9 Minuten pro 100) gilt für 57% der Zeit, den Teil an Bord. Umstiege werden nicht gezählt: eine vorsichtige Schätzung. Nach Fahrplan liegt das mittlere Verhältnis bei 2,2.",
    "Auto, offene Schätzung: schnellste Strecke im Straßennetz. Geschwindigkeiten von Sensoren und Bussen, 20 Sekunden pro Ampel, plus 5 Minuten zum Parken.",
    "Kontrolle: auf 20 von 20 Strecken ist die offene Schätzung schneller als TomTom (mittlerer Fehler 23,5%). Die Zahlen sind eine Spanne: die offene Schätzung und dieselbe Schätzung, um den Faktor 1,3 korrigiert.",
    "Verhältnis = Zeit mit öffentlichen Verkehrsmitteln geteilt durch die Autozeit, in festen Bereichen. Die Autos eines Paares sind die Autofahrten der Erhebung, von 6 bis 10 Uhr an einem Werktag. Die große Zahl gilt für 47% der Autos am Morgen (220.307). Das Punktdiagramm zeigt die 600 Zonenpaare mit den meisten Autos.",
    "Kosten: Preise vom 24.10.2026 (Kraftstoff Selbstbedienung im Umkreis von 5 km um die Piazza Castello, ACI-Kosten 2026, GTT-Tarife). Parken: 1,7 Euro pro Stunde für 8 Stunden und 20 Tage im Monat.",
    "Wert der Zeit: Mehrkosten pro Monat bei bezahltem Parken, geteilt durch die zusätzlichen Minuten pro Fahrt. Gezählt werden 2 Fahrten pro Tag und 20 Tage, zu 5 Euro; mit den ACI-Vollkosten etwa 30 Euro pro Stunde."
   ],
   "criteri": [
    [
     "Zonen",
     "71 Zonen der Mobilitätserhebung (23 in Turin), bis zu 5 Punkte je Zone"
    ],
    [
     "Öffentlicher Verkehr",
     "Abfahrt 07:45-8:15 an einem Werktag, Median, Gehen mit 4,8 km/h, höchstens 120 Minuten"
    ],
    [
     "Auto, offene Schätzung (A)",
     "schnellste Strecke im Straßennetz, mit Geschwindigkeiten von Sensoren und Bussen und 20 Sekunden pro Ampel (mittlerer Faktor 1,8) + 5 Minuten"
    ],
    [
     "Auto, mit der Kontrolle korrigiert (B)",
     "Fahrt × 1,3 + 5 Minuten: einheitlicher Faktor aus der Kontrolle auf 20 Strecken mit TomTom"
    ],
    [
     "Zeitraum der Sensoren",
     "vom 09.10.2026 bis zum 22.10.2026"
    ],
    [
     "Bereiche des Verhältnisses",
     "unter 1,5, 1,5-2, 2-3, über 3"
    ]
   ],
   "limiti": [
    "Außerhalb von Turin fehlen Züge und andere Betreiber: Paare zwischen Gemeinden im Umland sind in der Zahl nicht enthalten. Ohne die Regionalzüge, wo es sie gibt, erscheinen die öffentlichen Verkehrsmittel langsamer, als sie sind. Die Zeit ist die planmäßige, korrigiert mit den gemessenen Wartezeiten und Verspätungen.",
    "Die Autozeiten stammen aus einem offenen Modell und sind nicht auf der einzelnen Fahrt gemessen. Die TomTom-Kontrolle auf 20 Strecken findet sie optimistisch: Deshalb gibt es eine Spanne.",
    "Die Erhebung ist eine Stichprobe. Fahrten innerhalb einer Zone und 653 Zonenpaare ohne Verbindung (5.616 Autos) sind im Vergleich nicht enthalten.",
    "Ein Golf als Referenzauto. Die Zone mit Verkehrsbeschränkung (ZTL) und Park-Abonnements sind nicht eingerechnet. Die Preise sind die eines einzelnen Tages."
   ],
   "mappa": {
    "id": "imq",
    "nota": "Nella mappa, tema «Spostamenti»: quanti spostamenti partono da ogni zona e dove vanno (indagine 2022, feriale)."
   },
   "fonti": [
    "GTT (offizielle Fahrpläne)",
    "5T (Verkehrssensoren)",
    "Mobilitätsagentur des Piemont (Mobilitätserhebung 2022)",
    "OpenStreetMap",
    "Preisbeobachtungsstelle für Kraftstoffe (Ministerium für Unternehmen und Made in Italy)",
    "ACI (Kilometerkosten-Tabellen 2026)",
    "GTT (Tarife und Parken)",
    "TomTom (Kontrolle der Autozeiten auf 20 Strecken)"
   ],
   "titolo_breve": "Bus gegen Auto",
   "anima": {
    "tipo": "area",
    "didascalia": "Ab Piazza Castello, um 7:45 Uhr an einem Werktag. In 30 Minuten erreicht man mit öffentlichen Verkehrsmitteln ~33% der Einwohner Turins und mit dem Auto 91-100% (typischer Verkehr, Parken inklusive)."
   }
  },
  "numero_pubblico": 2,
  "gruppo": "vetrina",
  "_nome": "risultato8_riepilogo_mappa.json"
 },
 {
  "risultato": "10",
  "titolo": "Case, servizi e fragilità",
  "tag": "STIMATO / CENSIMENTO",
  "stato": "Fatto",
  "in_breve": "Le case costano di più dove ci sono più servizi? E dove la fragilità sociale è alta e i servizi sono pochi?",
  "domanda": "Chi vive dove i servizi sono pochi e le difficoltà sociali sono alte?",
  "numero_chiave": {
   "valore": 79598,
   "unita": "",
   "testo": "residenti in sezioni con fragilità alta e pochi servizi (9,5% dei residenti)"
  },
  "racconto": "",
  "risposta": [],
  "grafici": [],
  "metodo": [],
  "limiti": [],
  "parametri": [],
  "mappa": {
   "id": "vulnerabilita",
   "vista": "doppio",
   "nota": "Vista «Doppio svantaggio» nel tema Fragilità sociale."
  },
  "fonti": [
   "docs/en/METHODS.md",
   "data/processed/case_fragilita_servizi.json"
  ],
  "generato": "2026-10-26T14:06:29+00:00",
  "avviso": [
   "Differenza fra zone, non effetto causale."
  ],
  "in_english": [],
  "scenari": [
   {
    "nome": "Oggi",
    "numeri": [
     {
      "label": "Residenti in sezioni con fragilità alta e pochi servizi",
      "prima": null,
      "dopo": 79598,
      "unita": "residenti"
     },
     {
      "label": "Quota dei residenti di Torino",
      "prima": null,
      "dopo": 9.5,
      "unita": "%"
     },
     {
      "label": "Zone in doppio svantaggio",
      "prima": null,
      "dopo": 5,
      "unita": "zone"
     },
     {
      "label": "Correlazione prezzo-servizi (Spearman)",
      "prima": null,
      "dopo": 0.614,
      "unita": ""
     }
    ],
    "nota": "Zone OMI di Torino; le sezioni si sommano nella zona, pesate per abitanti."
   }
  ],
  "forma": {
   "tipo_dato": "Tipo di dato: calcolato da dati veri, con gli abitanti del censimento 2021.",
   "titolo": "Circa 1 torinese su 10 vive in una zona con più difficoltà sociali e pochi servizi",
   "domanda": "Chi vive dove i servizi sono pochi e le difficoltà sociali sono alte?",
   "numero": {
    "valore": 79598,
    "unita": "",
    "testo": "residenti in zone con più difficoltà sociali e servizi bassi: il 9,5% dei residenti delle zone abitate. È 1,7 volte quanto ci si aspetterebbe per caso.",
    "breve": "residenti con pochi servizi e più difficoltà"
   },
   "principale": {
    "tipo": "dispersione",
    "titolo": "Fragilità sociale e servizi a piedi, una zona OMI per punto (46 zone)",
    "xlabel": "indice di fragilità sociale, 0-100",
    "ylabel": "punteggio «Tutti i servizi» a piedi, 0-100",
    "passo_x": 10,
    "passo_y": 20,
    "xnome": "fragilità",
    "ynome": "servizi",
    "punti": [
     [
      31.7,
      82.2,
      1093,
      "Roma"
     ],
     [
      24.6,
      79.2,
      10989,
      "Carlo Emanuele Ii"
     ],
     [
      31.5,
      77.4,
      2584,
      "Solferino"
     ],
     [
      29.0,
      73.9,
      4598,
      "Vinzaglio"
     ],
     [
      27.6,
      80.9,
      11934,
      "Garibaldi"
     ],
     [
      36.9,
      87.3,
      2369,
      "Castello"
     ],
     [
      32.0,
      79.0,
      4397,
      "Rocca"
     ],
     [
      33.3,
      67.7,
      7157,
      "San Salvario"
     ],
     [
      31.7,
      59.9,
      5486,
      "Valentino"
     ],
     [
      34.2,
      23.5,
      7729,
      "Michelotti"
     ],
     [
      35.5,
      35.0,
      7445,
      "Crimea"
     ],
     [
      39.1,
      69.0,
      894,
      "Duca D Aosta"
     ],
     [
      44.3,
      61.5,
      13406,
      "Porta Palazzo - Maria Ausiliatrice"
     ],
     [
      34.0,
      73.7,
      18276,
      "Vanchiglia - Borgo Rossini"
     ],
     [
      54.3,
      51.8,
      20157,
      "Aurora"
     ],
     [
      31.7,
      62.3,
      22925,
      "Dante"
     ],
     [
      42.8,
      29.8,
      16461,
      "Vanchiglietta"
     ],
     [
      37.3,
      70.5,
      10462,
      "Campidoglio - Martinetto"
     ],
     [
      27.4,
      73.3,
      11167,
      "Adriano - Bernini - Rivoli"
     ],
     [
      36.1,
      72.5,
      18643,
      "Cenisia"
     ],
     [
      38.7,
      64.1,
      29291,
      "San Paolo"
     ],
     [
      28.9,
      66.5,
      5190,
      "San Secondo"
     ],
     [
      35.3,
      59.6,
      7970,
      "Galileo Ferraris"
     ],
     [
      28.9,
      63.8,
      15343,
      "De Gasperi"
     ],
     [
      34.1,
      72.8,
      1405,
      "Politecnico"
     ],
     [
      30.2,
      81.0,
      14491,
      "Duchessa Jolanda"
     ],
     [
      41.3,
      64.6,
      22334,
      "San Donato"
     ],
     [
      56.5,
      46.7,
      71762,
      "Madonna Di Campagna"
     ],
     [
      47.8,
      44.5,
      4322,
      "Spina 4 - Docks Dora"
     ],
     [
      58.5,
      9.5,
      10584,
      "Barca - Bertolla"
     ],
     [
      44.3,
      37.8,
      26802,
      "Nizza Millefonti"
     ],
     [
      49.8,
      52.8,
      46558,
      "Filadelfia - Traiano"
     ],
     [
      40.9,
      62.4,
      56890,
      "Santa Rita"
     ],
     [
      54.5,
      43.9,
      40047,
      "Mirafiori Nord"
     ],
     [
      62.1,
      57.6,
      48588,
      "Barriera Di Milano"
     ],
     [
      64.9,
      33.4,
      28202,
      "Rebaudengo - Regio Parco"
     ],
     [
      63.1,
      15.4,
      25756,
      "Corona Nord"
     ],
     [
      65.9,
      21.3,
      31262,
      "Lucento - Vallette"
     ],
     [
      40.2,
      55.5,
      31541,
      "Parella"
     ],
     [
      47.6,
      39.5,
      32025,
      "Aeronautica - Lesna"
     ],
     [
      40.3,
      55.8,
      36080,
      "Pozzo Strada"
     ],
     [
      63.0,
      25.6,
      33481,
      "Mirafiori Sud"
     ],
     [
      36.9,
      40.2,
      11318,
      "Spina 3 - Eurotorino"
     ],
     [
      48.1,
      5.7,
      9568,
      "Collinare Villa Della Regina"
     ],
     [
      45.3,
      4.6,
      3563,
      "Collinare Superga"
     ],
     [
      40.7,
      6.0,
      5865,
      "Collinare Cavoretto"
     ]
    ],
    "retta": {
     "a": 107.82,
     "b": -1.323,
     "label": "tendenza"
    },
    "nota": "Ogni punto è una zona, grande quanto i suoi abitanti. La linea è la tendenza: più la fragilità è alta, meno servizi. Il legame regge anche a parità di distanza dal centro: correlazione −0,48 (da −0,66 a −0,23)."
   },
   "punti": [
    "Succede 1,7 volte più spesso di quanto ci si aspetterebbe per caso.",
    "A 15 minuti a piedi quasi tutti hanno i 5 servizi di base (~99%); a 5 minuti solo ~68%.",
    "Le zone più colpite: Mirafiori Sud, Lucento - Vallette, Rebaudengo - Regio Parco, Corona Nord, Barca - Bertolla. Ci abitano ~129 mila persone."
   ],
   "altri": [
    {
     "tipo": "barre",
     "titolo": "Residenti delle sezioni di Torino per condizione",
     "unita": "residenti",
     "nota": "Sezioni abitate di Torino, senza le zone quasi disabitate. Fragilità alta = indice sopra 57,7 su 100 (il 20% più alto); servizi bassi = punteggio fino a 34,4 su 100 (il 20% più basso).",
     "voci": [
      {
       "label": "fragilità alta e servizi bassi",
       "valore": 79598,
       "tono": "rosso",
       "testo": "79.598 (216 sezioni)"
      },
      {
       "label": "solo fragilità alta",
       "valore": 142406,
       "tono": "arancio",
       "testo": "142.406 (483 sezioni)"
      },
      {
       "label": "solo servizi bassi",
       "valore": 100600,
       "tono": "blu",
       "testo": "100.600 (489 sezioni)"
      },
      {
       "label": "nessuna delle due",
       "valore": 517053,
       "tono": "verde",
       "testo": "517.053 (2.332 sezioni)"
      }
     ]
    },
    {
     "tipo": "pila100",
     "titolo": "Servizi a 5, 10 e 15 minuti a piedi",
     "unita": "%",
     "nota": "Ogni barra è un tempo a piedi: 100% dei residenti delle zone abitate (almeno 1.000 abitanti per km²).",
     "righe": [
      {
       "label": "5 minuti",
       "voci": [
        {
         "label": "tutti e 5 i servizi",
         "valore": 68.3,
         "tono": "verde"
        },
        {
         "label": "4 servizi",
         "valore": 22.2,
         "tono": "giallo"
        },
        {
         "label": "3 o meno",
         "valore": 9.5,
         "tono": "rosso"
        }
       ]
      },
      {
       "label": "10 minuti",
       "voci": [
        {
         "label": "tutti e 5 i servizi",
         "valore": 96.8,
         "tono": "verde"
        },
        {
         "label": "4 servizi",
         "valore": 2.4,
         "tono": "giallo"
        },
        {
         "label": "3 o meno",
         "valore": 0.8,
         "tono": "rosso"
        }
       ]
      },
      {
       "label": "15 minuti",
       "voci": [
        {
         "label": "tutti e 5 i servizi",
         "valore": 99.2,
         "tono": "verde"
        },
        {
         "label": "4 servizi",
         "valore": 0.6,
         "tono": "giallo"
        },
        {
         "label": "3 o meno",
         "valore": 0.2,
         "tono": "rosso"
        }
       ]
      }
     ]
    }
   ],
   "calcolo": [
    "Unità: le 46 zone OMI di Torino con almeno 500 abitanti. Le sezioni si sommano nella zona, pesate per abitanti.",
    "Servizi: punteggio «Tutti i servizi» a piedi in 15 minuti. Fragilità: indice del censimento 2021 (lavoro, istruzione, case, anziani).",
    "Tendenza: retta dei minimi quadrati. Il legame fra fragilità e servizi si controlla a parità di distanza dal centro.",
    "Doppio svantaggio = fragilità nel 20% più alto e servizi nel 20% più basso. Soglie fissate prima dei numeri, per sezioni: 57,7 e 34,4; per zone: 49,8 e 33,4.",
    "Legami a parità di distanza dal centro: correlazione parziale sui ranghi, con intervallo al 95% per ricampionamento. Regge solo se l'intervallo non contiene lo zero."
   ],
   "criteri": [
    [
     "Zone",
     "46 zone OMI di Torino, almeno 500 abitanti"
    ],
    [
     "Fragilità alta",
     "indice sopra 57,7 su 100"
    ],
    [
     "Servizi bassi",
     "punteggio fino a 34,4 su 100"
    ],
    [
     "Legami a parità di distanza",
     "correlazione parziale sui ranghi, intervallo al 95%; distanza dal centro della zona a Piazza Castello"
    ]
   ],
   "limiti": [
    "L'indice di fragilità non è il reddito e non è un indice ufficiale ISTAT: misura lavoro, istruzione, affollamento e anziani.",
    "Si conta se un servizio c'è, non quanto è grande.",
    "Le zone OMI sono grandi: dentro una zona i servizi e la fragilità cambiano molto."
   ],
   "mappa": {
    "id": "vulnerabilita",
    "nota": "Vista «Doppio svantaggio» nel tema Fragilità sociale.",
    "vista": "doppio"
   },
   "fonti": [
    "Agenzia delle Entrate (quotazioni OMI)",
    "ISTAT (censimento 2021)",
    "Comune di Torino (servizi)",
    "OpenStreetMap",
    "GTT (orari ufficiali)"
   ],
   "titolo_breve": "Fragilità e servizi",
   "anima": {
    "tipo": "omini",
    "totale": 10,
    "colorati": 1,
    "didascalia": "Circa 1 torinese su 10 vive dove l'indice di fragilità sociale è alto e i servizi sono pochi (9,5% dei residenti delle zone abitate)."
   }
  },
  "forma_en": {
   "tipo_dato": "Type of data: calculated from real data, with the residents of the 2021 census.",
   "titolo": "About 1 Turin resident in 10 lives in an area with more social difficulties and few services",
   "domanda": "Who lives where services are few and social difficulties are high?",
   "numero": {
    "valore": 79598,
    "unita": "",
    "testo": "residents in zones with more social difficulty and few services: 9.5% of residents of inhabited zones. That is 1.7 times what you would expect by chance.",
    "breve": "residents with few services and more difficulties"
   },
   "principale": {
    "tipo": "dispersione",
    "titolo": "Social fragility and services on foot, one OMI zone per dot (46 zones)",
    "xlabel": "social fragility index, 0-100",
    "ylabel": "“All services” score on foot, 0-100",
    "passo_x": 10,
    "passo_y": 20,
    "xnome": "fragilità",
    "ynome": "servizi",
    "punti": [
     [
      31.7,
      82.2,
      1093,
      "Roma"
     ],
     [
      24.6,
      79.2,
      10989,
      "Carlo Emanuele Ii"
     ],
     [
      31.5,
      77.4,
      2584,
      "Solferino"
     ],
     [
      29.0,
      73.9,
      4598,
      "Vinzaglio"
     ],
     [
      27.6,
      80.9,
      11934,
      "Garibaldi"
     ],
     [
      36.9,
      87.3,
      2369,
      "Castello"
     ],
     [
      32.0,
      79.0,
      4397,
      "Rocca"
     ],
     [
      33.3,
      67.7,
      7157,
      "San Salvario"
     ],
     [
      31.7,
      59.9,
      5486,
      "Valentino"
     ],
     [
      34.2,
      23.5,
      7729,
      "Michelotti"
     ],
     [
      35.5,
      35.0,
      7445,
      "Crimea"
     ],
     [
      39.1,
      69.0,
      894,
      "Duca D Aosta"
     ],
     [
      44.3,
      61.5,
      13406,
      "Porta Palazzo - Maria Ausiliatrice"
     ],
     [
      34.0,
      73.7,
      18276,
      "Vanchiglia - Borgo Rossini"
     ],
     [
      54.3,
      51.8,
      20157,
      "Aurora"
     ],
     [
      31.7,
      62.3,
      22925,
      "Dante"
     ],
     [
      42.8,
      29.8,
      16461,
      "Vanchiglietta"
     ],
     [
      37.3,
      70.5,
      10462,
      "Campidoglio - Martinetto"
     ],
     [
      27.4,
      73.3,
      11167,
      "Adriano - Bernini - Rivoli"
     ],
     [
      36.1,
      72.5,
      18643,
      "Cenisia"
     ],
     [
      38.7,
      64.1,
      29291,
      "San Paolo"
     ],
     [
      28.9,
      66.5,
      5190,
      "San Secondo"
     ],
     [
      35.3,
      59.6,
      7970,
      "Galileo Ferraris"
     ],
     [
      28.9,
      63.8,
      15343,
      "De Gasperi"
     ],
     [
      34.1,
      72.8,
      1405,
      "Politecnico"
     ],
     [
      30.2,
      81.0,
      14491,
      "Duchessa Jolanda"
     ],
     [
      41.3,
      64.6,
      22334,
      "San Donato"
     ],
     [
      56.5,
      46.7,
      71762,
      "Madonna Di Campagna"
     ],
     [
      47.8,
      44.5,
      4322,
      "Spina 4 - Docks Dora"
     ],
     [
      58.5,
      9.5,
      10584,
      "Barca - Bertolla"
     ],
     [
      44.3,
      37.8,
      26802,
      "Nizza Millefonti"
     ],
     [
      49.8,
      52.8,
      46558,
      "Filadelfia - Traiano"
     ],
     [
      40.9,
      62.4,
      56890,
      "Santa Rita"
     ],
     [
      54.5,
      43.9,
      40047,
      "Mirafiori Nord"
     ],
     [
      62.1,
      57.6,
      48588,
      "Barriera Di Milano"
     ],
     [
      64.9,
      33.4,
      28202,
      "Rebaudengo - Regio Parco"
     ],
     [
      63.1,
      15.4,
      25756,
      "Corona Nord"
     ],
     [
      65.9,
      21.3,
      31262,
      "Lucento - Vallette"
     ],
     [
      40.2,
      55.5,
      31541,
      "Parella"
     ],
     [
      47.6,
      39.5,
      32025,
      "Aeronautica - Lesna"
     ],
     [
      40.3,
      55.8,
      36080,
      "Pozzo Strada"
     ],
     [
      63.0,
      25.6,
      33481,
      "Mirafiori Sud"
     ],
     [
      36.9,
      40.2,
      11318,
      "Spina 3 - Eurotorino"
     ],
     [
      48.1,
      5.7,
      9568,
      "Collinare Villa Della Regina"
     ],
     [
      45.3,
      4.6,
      3563,
      "Collinare Superga"
     ],
     [
      40.7,
      6.0,
      5865,
      "Collinare Cavoretto"
     ]
    ],
    "retta": {
     "a": 107.82,
     "b": -1.323,
     "label": "trend"
    },
    "nota": "Each dot is a zone, sized by its residents. The line is the trend: the higher the fragility, the fewer the services. The link holds even at equal distance from the centre: correlation −0.48 (from −0.66 to −0.23)."
   },
   "punti": [
    "It happens 1.7 times more often than you would expect by chance.",
    "Within 15 minutes on foot almost everyone has the 5 basic services (~99%); within 5 minutes only ~68%.",
    "The most affected zones: Mirafiori Sud, Lucento - Vallette, Rebaudengo - Regio Parco, Corona Nord, Barca - Bertolla. About 129 thousand people live there."
   ],
   "altri": [
    {
     "tipo": "barre",
     "titolo": "Residents of Turin's census sections by condition",
     "unita": "residents",
     "nota": "Inhabited sections of Turin, without the almost uninhabited areas. High fragility = index above 57.7 out of 100 (the highest 20%); low services = score up to 34.4 out of 100 (the lowest 20%).",
     "voci": [
      {
       "label": "high fragility and low services",
       "valore": 79598,
       "tono": "rosso",
       "testo": "79,598 (216 sections)"
      },
      {
       "label": "high fragility only",
       "valore": 142406,
       "tono": "arancio",
       "testo": "142,406 (483 sections)"
      },
      {
       "label": "low services only",
       "valore": 100600,
       "tono": "blu",
       "testo": "100,600 (489 sections)"
      },
      {
       "label": "neither",
       "valore": 517053,
       "tono": "verde",
       "testo": "517,053 (2,332 sections)"
      }
     ]
    },
    {
     "tipo": "pila100",
     "titolo": "Services within 5, 10 and 15 minutes on foot",
     "unita": "%",
     "nota": "Each bar is a walking time: 100% of residents of inhabited areas (at least 1,000 inhabitants per km²).",
     "righe": [
      {
       "label": "5 minutes",
       "voci": [
        {
         "label": "all 5 services",
         "valore": 68.3,
         "tono": "verde"
        },
        {
         "label": "4 services",
         "valore": 22.2,
         "tono": "giallo"
        },
        {
         "label": "3 or fewer",
         "valore": 9.5,
         "tono": "rosso"
        }
       ]
      },
      {
       "label": "10 minutes",
       "voci": [
        {
         "label": "all 5 services",
         "valore": 96.8,
         "tono": "verde"
        },
        {
         "label": "4 services",
         "valore": 2.4,
         "tono": "giallo"
        },
        {
         "label": "3 or fewer",
         "valore": 0.8,
         "tono": "rosso"
        }
       ]
      },
      {
       "label": "15 minutes",
       "voci": [
        {
         "label": "all 5 services",
         "valore": 99.2,
         "tono": "verde"
        },
        {
         "label": "4 services",
         "valore": 0.6,
         "tono": "giallo"
        },
        {
         "label": "3 or fewer",
         "valore": 0.2,
         "tono": "rosso"
        }
       ]
      }
     ]
    }
   ],
   "calcolo": [
    "Unit: the 46 OMI zones of Turin with at least 500 inhabitants. Sections are added up within the zone, weighted by inhabitants.",
    "Services: “All services” score within a 15-minute walk. Fragility: 2021 census index (work, education, housing, older people).",
    "Trend: least-squares line. The link between fragility and services is checked at equal distance from the centre.",
    "Double disadvantage = fragility in the highest 20% and services in the lowest 20%. Thresholds fixed before the numbers, for sections: 57.7 and 34.4; for zones: 49.8 and 33.4.",
    "Links at equal distance from the centre: partial rank correlation, with a 95% interval by resampling. It holds only if the interval does not contain zero."
   ],
   "criteri": [
    [
     "Zones",
     "46 OMI zones of Turin, at least 500 inhabitants"
    ],
    [
     "High fragility",
     "index above 57.7 out of 100"
    ],
    [
     "Low services",
     "score up to 34.4 out of 100"
    ],
    [
     "Links at equal distance",
     "partial rank correlation, 95% interval; distance from the centre of the zone to Piazza Castello"
    ]
   ],
   "limiti": [
    "The fragility index is not income and not an official ISTAT index: it measures work, education, crowding and older people.",
    "The count shows whether a service exists, not how big it is.",
    "OMI zones are large: within a zone, services and fragility vary a lot."
   ],
   "mappa": {
    "id": "vulnerabilita",
    "nota": "Vista «Doppio svantaggio» nel tema Fragilità sociale.",
    "vista": "doppio"
   },
   "fonti": [
    "Revenue Agency (OMI price quotes)",
    "ISTAT (2021 census)",
    "City of Turin (services)",
    "OpenStreetMap",
    "GTT (official timetables)"
   ],
   "titolo_breve": "Fragility and services",
   "anima": {
    "tipo": "omini",
    "totale": 10,
    "colorati": 1,
    "didascalia": "About 1 Turin resident in 10 lives where the social fragility index is high and services are few (9.5% of residents of inhabited areas)."
   }
  },
  "forma_de": {
   "tipo_dato": "Datenart: berechnet aus echten Daten, mit den Einwohnern des Zensus 2021.",
   "titolo": "Etwa 1 von 10 Einwohnern Turins lebt in einer Zone mit mehr sozialen Schwierigkeiten und wenigen Einrichtungen",
   "domanda": "Wer lebt dort, wo es wenige Einrichtungen und große soziale Schwierigkeiten gibt?",
   "numero": {
    "valore": 79598,
    "unita": "",
    "testo": "Einwohner in Zonen mit mehr sozialen Schwierigkeiten und wenigen Einrichtungen: 9,5% der Einwohner der bewohnten Gebiete. Das ist 1,7-mal so viel, wie man zufällig erwarten würde.",
    "breve": "Einwohner mit wenigen Einrichtungen und mehr Schwierigkeiten"
   },
   "principale": {
    "tipo": "dispersione",
    "titolo": "Soziale Benachteiligung und fußläufig erreichbare Einrichtungen, eine OMI-Zone pro Punkt (46 Zonen)",
    "xlabel": "Index der sozialen Benachteiligung, 0-100",
    "ylabel": "Wert „Alle Einrichtungen“ zu Fuß, 0-100",
    "passo_x": 10,
    "passo_y": 20,
    "xnome": "fragilità",
    "ynome": "servizi",
    "punti": [
     [
      31.7,
      82.2,
      1093,
      "Roma"
     ],
     [
      24.6,
      79.2,
      10989,
      "Carlo Emanuele Ii"
     ],
     [
      31.5,
      77.4,
      2584,
      "Solferino"
     ],
     [
      29.0,
      73.9,
      4598,
      "Vinzaglio"
     ],
     [
      27.6,
      80.9,
      11934,
      "Garibaldi"
     ],
     [
      36.9,
      87.3,
      2369,
      "Castello"
     ],
     [
      32.0,
      79.0,
      4397,
      "Rocca"
     ],
     [
      33.3,
      67.7,
      7157,
      "San Salvario"
     ],
     [
      31.7,
      59.9,
      5486,
      "Valentino"
     ],
     [
      34.2,
      23.5,
      7729,
      "Michelotti"
     ],
     [
      35.5,
      35.0,
      7445,
      "Crimea"
     ],
     [
      39.1,
      69.0,
      894,
      "Duca D Aosta"
     ],
     [
      44.3,
      61.5,
      13406,
      "Porta Palazzo - Maria Ausiliatrice"
     ],
     [
      34.0,
      73.7,
      18276,
      "Vanchiglia - Borgo Rossini"
     ],
     [
      54.3,
      51.8,
      20157,
      "Aurora"
     ],
     [
      31.7,
      62.3,
      22925,
      "Dante"
     ],
     [
      42.8,
      29.8,
      16461,
      "Vanchiglietta"
     ],
     [
      37.3,
      70.5,
      10462,
      "Campidoglio - Martinetto"
     ],
     [
      27.4,
      73.3,
      11167,
      "Adriano - Bernini - Rivoli"
     ],
     [
      36.1,
      72.5,
      18643,
      "Cenisia"
     ],
     [
      38.7,
      64.1,
      29291,
      "San Paolo"
     ],
     [
      28.9,
      66.5,
      5190,
      "San Secondo"
     ],
     [
      35.3,
      59.6,
      7970,
      "Galileo Ferraris"
     ],
     [
      28.9,
      63.8,
      15343,
      "De Gasperi"
     ],
     [
      34.1,
      72.8,
      1405,
      "Politecnico"
     ],
     [
      30.2,
      81.0,
      14491,
      "Duchessa Jolanda"
     ],
     [
      41.3,
      64.6,
      22334,
      "San Donato"
     ],
     [
      56.5,
      46.7,
      71762,
      "Madonna Di Campagna"
     ],
     [
      47.8,
      44.5,
      4322,
      "Spina 4 - Docks Dora"
     ],
     [
      58.5,
      9.5,
      10584,
      "Barca - Bertolla"
     ],
     [
      44.3,
      37.8,
      26802,
      "Nizza Millefonti"
     ],
     [
      49.8,
      52.8,
      46558,
      "Filadelfia - Traiano"
     ],
     [
      40.9,
      62.4,
      56890,
      "Santa Rita"
     ],
     [
      54.5,
      43.9,
      40047,
      "Mirafiori Nord"
     ],
     [
      62.1,
      57.6,
      48588,
      "Barriera Di Milano"
     ],
     [
      64.9,
      33.4,
      28202,
      "Rebaudengo - Regio Parco"
     ],
     [
      63.1,
      15.4,
      25756,
      "Corona Nord"
     ],
     [
      65.9,
      21.3,
      31262,
      "Lucento - Vallette"
     ],
     [
      40.2,
      55.5,
      31541,
      "Parella"
     ],
     [
      47.6,
      39.5,
      32025,
      "Aeronautica - Lesna"
     ],
     [
      40.3,
      55.8,
      36080,
      "Pozzo Strada"
     ],
     [
      63.0,
      25.6,
      33481,
      "Mirafiori Sud"
     ],
     [
      36.9,
      40.2,
      11318,
      "Spina 3 - Eurotorino"
     ],
     [
      48.1,
      5.7,
      9568,
      "Collinare Villa Della Regina"
     ],
     [
      45.3,
      4.6,
      3563,
      "Collinare Superga"
     ],
     [
      40.7,
      6.0,
      5865,
      "Collinare Cavoretto"
     ]
    ],
    "retta": {
     "a": 107.82,
     "b": -1.323,
     "label": "Trend"
    },
    "nota": "Jeder Punkt ist eine Zone, so groß wie ihre Einwohnerzahl. Die Linie ist der Trend: Je höher die Benachteiligung, desto weniger Einrichtungen. Der Zusammenhang besteht auch bei gleichem Abstand zum Zentrum: Korrelation −0,48 (von −0,66 bis −0,23)."
   },
   "punti": [
    "Das kommt 1,7-mal so oft vor, wie man zufällig erwarten würde.",
    "In 15 Minuten zu Fuß erreichen fast alle die 5 Basiseinrichtungen (~99%); in 5 Minuten nur ~68%.",
    "Die am stärksten betroffenen Zonen: Mirafiori Sud, Lucento - Vallette, Rebaudengo - Regio Parco, Corona Nord, Barca - Bertolla. Dort wohnen ~129 Tausend Menschen."
   ],
   "altri": [
    {
     "tipo": "barre",
     "titolo": "Einwohner der Turiner Zählsprengel nach Lage",
     "unita": "Einwohner",
     "nota": "Bewohnte Zählsprengel von Turin, ohne die fast unbewohnten Gebiete. Hohe Benachteiligung = Index über 57,7 von 100 (die obersten 20%); wenige Einrichtungen = Wert bis 34,4 von 100 (die untersten 20%).",
     "voci": [
      {
       "label": "hohe Benachteiligung und wenige Einrichtungen",
       "valore": 79598,
       "tono": "rosso",
       "testo": "79.598 (216 Zählsprengel)"
      },
      {
       "label": "nur hohe Benachteiligung",
       "valore": 142406,
       "tono": "arancio",
       "testo": "142.406 (483 Zählsprengel)"
      },
      {
       "label": "nur wenige Einrichtungen",
       "valore": 100600,
       "tono": "blu",
       "testo": "100.600 (489 Zählsprengel)"
      },
      {
       "label": "keines von beiden",
       "valore": 517053,
       "tono": "verde",
       "testo": "517.053 (2.332 Zählsprengel)"
      }
     ]
    },
    {
     "tipo": "pila100",
     "titolo": "Einrichtungen in 5, 10 und 15 Minuten zu Fuß",
     "unita": "%",
     "nota": "Jeder Balken ist eine Gehzeit: 100% der Einwohner der bewohnten Gebiete (mindestens 1.000 Einwohner pro km²).",
     "righe": [
      {
       "label": "5 Minuten",
       "voci": [
        {
         "label": "alle 5 Einrichtungen",
         "valore": 68.3,
         "tono": "verde"
        },
        {
         "label": "4 Einrichtungen",
         "valore": 22.2,
         "tono": "giallo"
        },
        {
         "label": "3 oder weniger",
         "valore": 9.5,
         "tono": "rosso"
        }
       ]
      },
      {
       "label": "10 Minuten",
       "voci": [
        {
         "label": "alle 5 Einrichtungen",
         "valore": 96.8,
         "tono": "verde"
        },
        {
         "label": "4 Einrichtungen",
         "valore": 2.4,
         "tono": "giallo"
        },
        {
         "label": "3 oder weniger",
         "valore": 0.8,
         "tono": "rosso"
        }
       ]
      },
      {
       "label": "15 Minuten",
       "voci": [
        {
         "label": "alle 5 Einrichtungen",
         "valore": 99.2,
         "tono": "verde"
        },
        {
         "label": "4 Einrichtungen",
         "valore": 0.6,
         "tono": "giallo"
        },
        {
         "label": "3 oder weniger",
         "valore": 0.2,
         "tono": "rosso"
        }
       ]
      }
     ]
    }
   ],
   "calcolo": [
    "Einheit: die 46 OMI-Zonen von Turin mit mindestens 500 Einwohnern. Die Zählsprengel werden in der Zone nach Einwohnern gewichtet addiert.",
    "Einrichtungen: Wert „Alle Einrichtungen“ innerhalb von 15 Minuten zu Fuß. Benachteiligung: Index aus dem Zensus 2021 (Arbeit, Bildung, Wohnen, ältere Menschen).",
    "Trend: Ausgleichsgerade nach der Methode der kleinsten Quadrate. Der Zusammenhang zwischen Benachteiligung und Einrichtungen wird bei gleichem Abstand zum Zentrum geprüft.",
    "Doppelte Benachteiligung = Benachteiligung in den obersten 20% und Einrichtungen in den untersten 20%. Schwellen vor den Zahlen festgelegt, für Zählsprengel: 57,7 und 34,4; für Zonen: 49,8 und 33,4.",
    "Zusammenhänge bei gleichem Abstand zum Zentrum: partielle Rangkorrelation, mit 95%-Intervall durch Resampling. Ein Zusammenhang gilt nur, wenn das Intervall die Null nicht enthält."
   ],
   "criteri": [
    [
     "Zonen",
     "46 OMI-Zonen von Turin, mindestens 500 Einwohner"
    ],
    [
     "Hohe Benachteiligung",
     "Index über 57,7 von 100"
    ],
    [
     "Wenige Einrichtungen",
     "Wert bis 34,4 von 100"
    ],
    [
     "Zusammenhänge bei gleichem Abstand",
     "partielle Rangkorrelation, 95%-Intervall; Abstand des Zonenzentrums zur Piazza Castello"
    ]
   ],
   "limiti": [
    "Der Index der Benachteiligung ist weder das Einkommen noch ein offizieller ISTAT-Index: Er misst Arbeit, Bildung, Wohnungsbelegung und ältere Menschen.",
    "Gezählt wird, ob es eine Einrichtung gibt, nicht wie groß sie ist.",
    "Die OMI-Zonen sind groß: Innerhalb einer Zone ändern sich Einrichtungen und Benachteiligung stark."
   ],
   "mappa": {
    "id": "vulnerabilita",
    "nota": "Vista «Doppio svantaggio» nel tema Fragilità sociale.",
    "vista": "doppio"
   },
   "fonti": [
    "Finanzverwaltung Agenzia delle Entrate (OMI-Preise)",
    "ISTAT (Zensus 2021)",
    "Stadt Turin (Einrichtungen)",
    "OpenStreetMap",
    "GTT (offizielle Fahrpläne)"
   ],
   "titolo_breve": "Benachteiligung und Einrichtungen",
   "anima": {
    "tipo": "omini",
    "totale": 10,
    "colorati": 1,
    "didascalia": "Etwa 1 von 10 Einwohnern Turins lebt dort, wo der Index der sozialen Benachteiligung hoch und die Einrichtungen wenige sind (9,5% der Einwohner der bewohnten Gebiete)."
   }
  },
  "numero_pubblico": 3,
  "gruppo": "vetrina",
  "_nome": "risultato10_riepilogo_mappa.json"
 }
];
window.SCHEDE_PERIODO = {"da": "2026-10-09", "a": "2026-10-22"};
