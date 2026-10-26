/* La storia del progetto in dieci tappe (§5.4 del piano), in prima persona: testo a sinistra, disegno a destra che cambia a ogni parte
   (su telefono il disegno sta sopra il testo). Progetto.monta(elemento) scrive testi (italiano, inglese e tedesco) e disegni nell'elemento
   e li fa seguire lo scorrimento. Tutti i numeri vengono da data/progetto.js e dalle schede (data/schede_risultati.js): qui non c'e' scritto
   nessun numero. Con «riduci movimento» i disegni sono fermi. Gli stili stanno in assets/progetto.css. */
(function(){
  "use strict";

  /* ---- testi: x(it, en, de) scrive i tre testi di un elemento; {chiave} diventa un numero dei dati (vedi numeri()) ---- */
  function att(s){ return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;"); }
  function seg(s){ return s.replace(/\{([a-z0-9_.]+)\}/g, '<span data-n="$1"></span>'); }
  function x(it, en, de){ return 'data-en="' + att(seg(en)) + '" data-de="' + att(seg(de)) + '"'; }
  function p(it, en, de){ return '<p ' + x(it, en, de) + '>' + seg(it) + '</p>'; }
  function parte(n, fig, id, nome, titolo, corpo){
    return '<section data-fig="' + fig + '" id="' + id + '" aria-labelledby="h' + n + 'p">' +
      '<p class="num-parte" ' + x(n + " · " + nome[0], n + " · " + nome[1], n + " · " + nome[2]) + '>' + n + " · " + nome[0] + '</p>' +
      '<h2 id="h' + n + 'p" ' + x(titolo[0], titolo[1], titolo[2]) + '>' + seg(titolo[0]) + '</h2>' + corpo + '</section>';
  }
  function bottone(href, it, en, de, cls){ return '<a class="btn' + (cls ? " " + cls : "") + '" href="' + href + '" ' + x(it, en, de) + '>' + it + '</a>'; }
  function riquadri(voci){
    return '<ul class="decisioni">' + voci.map(function(v){
      return '<li><b ' + x(v[0][0], v[0][1], v[0][2]) + '>' + v[0][0] + '</b><span ' + x(v[1][0], v[1][1], v[1][2]) + '>' + seg(v[1][0]) + '</span></li>';
    }).join("") + '</ul>';
  }
  function figura(id, vb, it, en, de){
    return '<figure class="fig' + (id === "fN" ? " attiva" : "") + '" id="' + id + '"><svg viewBox="' + vb + '" preserveAspectRatio="xMidYMid meet"></svg>' +
      '<figcaption ' + x(it, en, de) + '>' + it + '</figcaption></figure>';
  }

  var D_LAB = {d: ["Domanda", "Question", "Frage"], c: ["Dati raccolti", "Data collected", "Erfasste Daten"], k: ["Criterio fissato prima", "Criterion set beforehand", "Vorab festgelegtes Kriterium"], r: ["Risposta", "Answer", "Antwort"]};
  /* un riquadro «domanda, dati, criterio, risposta» con il link alla scheda */
  function dq(id, fig, v){
    var righe = ["d", "c", "k", "r"].map(function(k, i){
      var t = v[i];
      return '<dt ' + x(D_LAB[k][0], D_LAB[k][1], D_LAB[k][2]) + '>' + D_LAB[k][0] + '</dt><dd ' + x(t[0], t[1], t[2]) + '>' + seg(t[0]) + '</dd>';
    }).join("");
    return '<div class="dq" data-fig="' + fig + '"><dl>' + righe + '</dl><a class="btn" href="index.html#r' + id + '" data-ris="' + id + '">Scheda</a></div>';
  }

  var MARKUP =
  '<div class="colfig"><div class="sticky" aria-hidden="true">' +
    figura("fN", "0 0 400 300", "Turin Meter in numeri, tutti dai dati.", "Turin Meter in numbers, all from the data.", "Turin Meter in Zahlen, alle aus den Daten.") +
    figura("fP", "0 0 400 300", "2020: un'idea sulla carta. Oggi: dati che arrivano ogni minuto.", "2020: an idea on paper. Today: data that arrive every minute.", "2020: eine Idee auf dem Papier. Heute: Daten, die jede Minute eintreffen.") +
    figura("fS", "0 0 400 420", "Dalle fonti aperte alle pagine che si leggono.", "From the open sources to the pages you read.", "Von den offenen Quellen zu den Seiten, die man liest.") +
    figura("fG", "0 0 400 300", "Quota di passaggi di bus e tram con oltre 5 minuti di ritardo, per fonte.", "Share of bus and tram departures more than 5 minutes late, by source.", "Anteil der Bus- und Tramabfahrten mit mehr als 5 Minuten Verspätung, nach Quelle.") +
    figura("fR", "0 0 400 300", "Spostamenti del mattino: mezzi pubblici contro auto (l'auto è 1).", "Morning trips: public transport compared with the car (the car is 1).", "Fahrten am Morgen: öffentlicher Verkehr im Vergleich zum Auto (das Auto ist 1).") +
    figura("fD", "0 0 1000 963", "In rosso: le zone dove fragilità alta e pochi servizi coincidono.", "In red: the zones where high vulnerability and few services go together.", "In Rot: die Gebiete, in denen hohe Benachteiligung und wenige Einrichtungen zusammentreffen.") +
    figura("fQ", "0 0 400 300", "Fermate importanti, per posti vicini dove lasciare l'auto.", "Major stops, by nearby spaces to leave the car.", "Wichtige Haltestellen nach Stellplätzen in der Nähe.") +
    figura("fF", "0 0 400 300", "Tre decisioni, coi numeri dei dati.", "Three decisions, with the numbers from the data.", "Drei Entscheidungen, mit den Zahlen aus den Daten.") +
    figura("fM", "0 0 400 300", "Tre dati che non sono aperti.", "Three datasets that are not open.", "Drei Daten, die nicht offen verfügbar sind.") +
  '</div></div><div class="testi">' +

  parte(1, "fN", "inbreve", ["Il progetto", "The project", "Das Projekt"],
    ["Come si muove Torino", "How Turin moves", "Wie sich Turin bewegt"],
    p("Turin Meter misura come si muove Torino. Dal {sistema.inizio} raccoglie ogni minuto la posizione di bus e tram e i dati dei sensori del traffico, e li incrocia con censimento, indagine sugli spostamenti e mappe aperte: quattro risposte a domande concrete sulla mobilità.",
      "Turin Meter measures how Turin moves. Since {sistema.inizio} it collects, every minute, the position of buses and trams and the traffic sensor data, and combines them with census, travel survey and open maps: four answers to concrete questions about mobility.",
      "Turin Meter misst, wie sich Turin bewegt. Seit dem {sistema.inizio} erfasst es jede Minute die Position von Bussen und Straßenbahnen und die Daten der Verkehrssensoren und verknüpft sie mit Volkszählung, Mobilitätserhebung und offenen Karten: vier Antworten auf konkrete Fragen zur Mobilität.")) +

  parte(2, "fP", "domanda", ["La domanda", "The question", "Die Frage"],
    ["Cosa dicono i dati veri?", "What do real data say?", "Was sagen die echten Daten?"],
    p("La tesi del 2020 su Industry 4.0 e smart city prometteva che sensori e dati avrebbero cambiato le città. Qui la promessa è messa alla prova sui dati di Torino.",
      "A 2020 thesis on Industry 4.0 and smart cities promised that sensors and data would change cities. Here the promise is put to the test on data from Turin.",
      "Eine Abschlussarbeit von 2020 über Industrie 4.0 und Smart Cities versprach, dass Sensoren und Daten die Städte verändern würden. Hier wird das Versprechen an Daten aus Turin geprüft.")) +

  '<section id="dati" aria-labelledby="h3p">' +
    '<p class="num-parte" ' + x("3 · Quattro domande, quattro risposte", "3 · Four questions, four answers", "3 · Vier Fragen, vier Antworten") + '>3 · Quattro domande, quattro risposte</p>' +
    '<h2 id="h3p" ' + x("Domande, dati, criteri, risposte", "Questions, data, criteria, answers", "Fragen, Daten, Kriterien, Antworten") + '>Domande, dati, criteri, risposte</h2>' +
    dq(4, "fG", [
      ["Quanto spesso bus e tram arrivano in ritardo, e dove nasce il ritardo?", "How often are buses and trams late, and where does the delay start?", "Wie oft sind Busse und Straßenbahnen verspätet, und wo entsteht die Verspätung?"],
      ["GPS dei mezzi ogni minuto, {d1.giorni} giorni feriali.", "Vehicle GPS every minute, {d1.giorni} weekdays.", "GPS der Fahrzeuge jede Minute, {d1.giorni} Werktage."],
      ["Ritardo oltre 10 minuti, in forbice per la lettura al minuto; tratti con almeno {d1.corse} corse, capolinea esclusi.", "Delay of more than 10 minutes, as a range because of the one-minute reading; segments with at least {d1.corse} trips, terminals excluded.", "Verspätung über 10 Minuten, als Spanne wegen der Messung im Minutentakt; Abschnitte mit mindestens {d1.corse} Fahrten, ohne Endhaltestellen."],
      ["{d1.forbice}% dei passaggi; il tratto peggiore è {d1.primo}.", "{d1.forbice}% of departures; the worst segment is {d1.primo}.", "{d1.forbice}% der Abfahrten; der schlechteste Abschnitt ist {d1.primo}."]]) +
    dq(8, "fR", [
      ["Al mattino, quanto tempo in più chiede il mezzo pubblico rispetto all'auto?", "In the morning, how much more time does public transport take than the car?", "Wie viel mehr Zeit braucht der öffentliche Verkehr morgens im Vergleich zum Auto?"],
      ["Orari e ritardi misurati; auto da un modello aperto, controllato con TomTom su {controllo.percorsi} percorsi.", "Timetables and measured delays; car times from an open model, checked with TomTom on {controllo.percorsi} routes.", "Fahrpläne und gemessene Verspätungen; Auto aus einem offenen Modell, mit TomTom auf {controllo.percorsi} Strecken geprüft."],
      ["Viaggi del mattino fra zone diverse (indagine IMQ); forbice fra stima aperta e corretta.", "Morning trips between different zones (IMQ survey); a range between open and corrected estimate.", "Fahrten am Morgen zwischen verschiedenen Zonen (Erhebung IMQ); Spanne zwischen offener und korrigierter Schätzung."],
      ["{muoversi.volte} volte il tempo dell'auto.", "{muoversi.volte} times the car's time.", "Das {muoversi.volte}-Fache der Autozeit."]]) +
    dq(10, "fD", [
      ["Chi vive dove fragilità sociale e pochi servizi si sommano?", "Who lives where social vulnerability and few services add up?", "Wer lebt dort, wo soziale Benachteiligung und wenige Einrichtungen zusammenkommen?"],
      ["Censimento 2021, servizi aperti, tempi a piedi.", "2021 census, open service data, walking times.", "Volkszählung 2021, offene Daten zu Einrichtungen, Gehzeiten."],
      ["Indice costruito solo con dati di censimento; servizi a 15 minuti a piedi.", "Index built from census data only; services within 15 minutes on foot.", "Index nur aus Volkszählungsdaten; Einrichtungen in 15 Gehminuten."],
      ["{doppio.residenti} residenti, il {doppio.quota}% delle zone abitate: {d3.volte} volte il caso.", "{doppio.residenti} residents, {doppio.quota}% of inhabited areas: {d3.volte} times chance.", "{doppio.residenti} Einwohner, {doppio.quota}% der bewohnten Gebiete: {d3.volte}-mal so viel wie zufällig."]]) +
    dq(6, "fQ", [
      ["Chi arriva in auto trova dove lasciarla vicino a una fermata importante?", "Can people arriving by car find a place to leave it near a major stop?", "Finden Autofahrer nahe einer wichtigen Haltestelle einen Platz fürs Auto?"],
      ["Parcheggi (Comune, OpenStreetMap, 5T), fermate importanti.", "Car parks (City, OpenStreetMap, 5T) and major stops.", "Parkplätze (Stadt, OpenStreetMap, 5T) und wichtige Haltestellen."],
      ["Posti entro {d4.raggio} m a piedi, con una soglia minima.", "Spaces within {d4.raggio} metres on foot, with a minimum threshold.", "Stellplätze im Umkreis von {d4.raggio} Metern zu Fuß, mit einer Mindestschwelle."],
      ["{d4.senza} fermate su {d4.fermate} non hanno posti bastanti.", "{d4.senza} of {d4.fermate} stops do not have enough spaces.", "{d4.senza} von {d4.fermate} Haltestellen haben nicht genug Stellplätze."]]) +
  '</section>' +

  parte(4, "fS", "sistema", ["Come funziona", "How it works", "Wie es funktioniert"],
    ["Dalla raccolta alle pagine", "From collection to pages", "Von der Erfassung zu den Seiten"],
    p("Un Raspberry Pi a casa raccoglie ogni minuto i dati aperti di GTT e 5T e li salva in un archivio. Script Python li uniscono a censimento, indagine IMQ 2022 e OpenStreetMap; un motore di percorsi calcola i tempi coi mezzi. Pagine leggere, senza server.",
      "A Raspberry Pi at home collects the open data of GTT and 5T every minute and saves them in an archive. Python scripts combine them with the census, the IMQ 2022 survey and OpenStreetMap; a routing engine computes the public transport times. Light pages, no server.",
      "Ein Raspberry Pi zu Hause erfasst jede Minute die offenen Daten von GTT und 5T und speichert sie in einem Archiv. Python-Skripte verknüpfen sie mit Volkszählung, Erhebung IMQ 2022 und OpenStreetMap; eine Routing-Engine berechnet die Fahrzeiten im öffentlichen Verkehr. Leichte Seiten, ohne Server.")) +

  parte(5, "fG", "metodo", ["Scelte di metodo", "Choices of method", "Methodische Entscheidungen"],
    ["Cinque scelte", "Five choices", "Fünf Entscheidungen"],
    riquadri([
      [["Ritardi dal GPS", "Delays from GPS", "Verspätungen per GPS"],
       ["Il feed ufficiale li sottostimava di circa {ritardi.rapporto} volte: si misura dal GPS dei mezzi.",
        "The official feed understated them by about {ritardi.rapporto} times, so delays are measured from vehicle GPS.",
        "Der offizielle Feed unterschätzte sie etwa um das {ritardi.rapporto}-Fache, deshalb wird per Fahrzeug-GPS gemessen."]],
      [["Regole scritte prima", "Rules written first", "Regeln vorab festgelegt"],
       ["Regole scritte prima di calcolare; per i tempi in auto la forma dei numeri è cambiata dopo il controllo.",
        "Rules written before calculating; for car times, the form of the numbers changed after the check.",
        "Regeln vor der Berechnung festgelegt; bei den Autozeiten änderte sich die Form der Zahlen nach der Kontrolle."]],
      [["Tempi in auto aperti", "Open car times", "Offene Autozeiten"],
       ["Modello aperto, controllato con TomTom su {controllo.percorsi} percorsi: risulta ottimista, quindi i numeri sono una forbice.",
        "Open model, checked with TomTom on {controllo.percorsi} routes: it comes out optimistic, so the numbers are a range.",
        "Offenes Modell, mit TomTom auf {controllo.percorsi} Strecken geprüft: zu optimistisch, daher sind die Zahlen eine Spanne."]],
      [["Solo dati aperti", "Only open data", "Nur offene Daten"],
       ["Licenze controllate fonte per fonte; se incerte, solo valori riassunti.",
        "Licences checked source by source; if unclear, only summary values.",
        "Lizenzen Quelle für Quelle geprüft; bei Unklarheit nur zusammengefasste Werte."]],
      [["Controlli automatici", "Automatic checks", "Automatische Kontrollen"],
       ["Controlli automatici a ogni consegna: se un numero non torna, non si pubblica.",
        "Automatic checks on every delivery: if a number does not add up, nothing is published.",
        "Automatische Kontrollen bei jeder Lieferung: Stimmt eine Zahl nicht, wird nicht veröffentlicht."]]
    ])) +

  parte(6, "fG", "fiducia", ["Quanto fidarsi", "How far to trust it", "Wie weit man vertrauen kann"],
    ["I dati vanno controllati", "The data must be checked", "Die Daten müssen geprüft werden"],
    p("Un mezzo trasmette con l'orologio tre anni avanti, il 18 ottobre il feed si è fermato una mattina. Ogni scheda dice come nasce il numero e dove sono i limiti.",
      "One vehicle transmits with its clock three years ahead, on 18 October the feed stopped for a morning. Every finding says how its number is calculated and where the limits are.",
      "Ein Fahrzeug sendet mit einer um drei Jahre vorgehenden Uhr, am 18. Oktober blieb der Feed einen Morgen lang stehen. Jedes Ergebnis sagt, wie seine Zahl berechnet wird und wo die Grenzen liegen.")) +

  parte(7, "fF", "farei", ["Tre decisioni per Torino", "Three decisions for Turin", "Drei Entscheidungen für Turin"],
    ["Da dove cominciare", "Where to start", "Womit man anfängt"],
    '<div class="cosa-farei"><ol class="farei" id="fareiPagina"></ol></div>' +
    p("Ipotesi da verificare con chi gestisce la città: i dati dicono dove guardare, non quanto costa.",
      "Hypotheses to check with the people who run the city: the data say where to look, not what it costs.",
      "Hypothesen, die mit den Verantwortlichen der Stadt zu prüfen sind: Die Daten zeigen, wo man hinschauen muss, nicht, was es kostet.")) +

  parte(8, "fM", "mancano", ["Tre dati che mancano", "Three missing datasets", "Drei fehlende Daten"],
    ["Con questi le domande diventerebbero moltissime", "With these, the possible questions would multiply", "Damit gäbe es sehr viel mehr mögliche Fragen"],
    '<ul class="fatti">' +
      '<li ' + x("Passeggeri per corsa e fermata: chi subisce ogni ritardo, dove servono corse.", "Passengers per trip and stop: who suffers each delay, where trips are needed.", "Fahrgäste je Fahrt und Haltestelle: wen jede Verspätung trifft, wo Fahrten fehlen.") + '>Passeggeri per corsa e fermata: chi subisce ogni ritardo, dove servono corse.</li>' +
      '<li ' + x("Costi di esercizio per linea e chilometro: quanto costa un minuto perso, quanto rende una corsia.", "Operating costs per line and per kilometre: what a lost minute costs, what a bus lane returns.", "Betriebskosten je Linie und Kilometer: was eine verlorene Minute kostet, was eine Busspur bringt.") + '>Costi di esercizio per linea e chilometro: quanto costa un minuto perso, quanto rende una corsia.</li>' +
      '<li ' + x("Flussi reali da un luogo all'altro (telefoni, veicoli connessi): tempi in auto misurati invece che stimati.", "Real flows from place to place (phones, connected vehicles): car times measured instead of estimated.", "Echte Ströme von Ort zu Ort (Telefone, vernetzte Fahrzeuge): gemessene statt geschätzte Autozeiten.") + '>Flussi reali da un luogo all\'altro (telefoni, veicoli connessi): tempi in auto misurati invece che stimati.</li>' +
    '</ul>' +
    p("Il prossimo passo del progetto: i treni (servizio ferroviario metropolitano) e la logistica delle merci in città.",
      "The project's next step: trains (the metropolitan rail service) and freight logistics in the city.",
      "Der nächste Schritt des Projekts: die Züge (S-Bahn-Dienst) und die Güterlogistik in der Stadt.")) +

  parte(9, "fN", "ai", ["Lavoro con l'AI", "Working with AI", "Arbeit mit KI"],
    ["L'AI come acceleratore", "AI as an accelerator", "KI als Beschleuniger"],
    p("Con l'AI un lavoro da piccolo team è stato fatto in {sistema.settimane} settimane: prototipi in ore, controlli sui dati mentre si lavorava. Le domande, i criteri e le soglie, il controllo dei numeri e le scelte su cosa pubblicare sono miei; la raccolta dei dati e parte delle analisi in Python le ho scritte io. Costi: Claude {lavoro.claude} € al mese, opencode {lavoro.opencode} € al mese, circa {lavoro.pi} € di hardware.",
      "With AI, work that usually takes a small team was done in {sistema.settimane} weeks: prototypes in hours, checks on the data while working. The questions, the criteria and thresholds, the checking of the numbers and the choices on what to publish are mine; I wrote the data collection and part of the Python analyses myself. Costs: Claude €{lavoro.claude} a month, opencode €{lavoro.opencode} a month, about €{lavoro.pi} of hardware.",
      "Mit KI wurde eine Arbeit, für die man sonst ein kleines Team braucht, in {sistema.settimane} Wochen erledigt: Prototypen in Stunden, Prüfungen an den Daten während der Arbeit. Die Fragen, die Kriterien und Schwellenwerte, die Kontrolle der Zahlen und die Entscheidung, was veröffentlicht wird, stammen von mir; die Datenerfassung und einen Teil der Python-Analysen habe ich selbst geschrieben. Kosten: Claude {lavoro.claude} € im Monat, opencode {lavoro.opencode} € im Monat, rund {lavoro.pi} € für Hardware.")) +

  parte(10, "", "chisono", ["Chi sono", "About me", "Über mich"],
    ["Leonardo Campese", "Leonardo Campese", "Leonardo Campese"],
    p("Turin Meter è un progetto personale, costruito solo su dati aperti. Per domande o idee, scrivimi.",
      "Turin Meter is a personal project, built on open data only. For questions or ideas, write to me.",
      "Turin Meter ist ein persönliches Projekt, nur auf offenen Daten gebaut. Für Fragen oder Ideen schreib mir.") +
    '<div class="finale-bottoni"><a class="btn primario" href="https://www.linkedin.com/in/leocampese/">LinkedIn</a><a class="btn" href="mailto:campese.leonardo@gmail.com">campese.leonardo@gmail.com</a></div>') +
  '</div>';

  function monta(scena){
    document.documentElement.classList.add("js");
    scena.innerHTML = MARKUP;
    if(window.Sito && Sito.traduci) Sito.traduci(scena);   // testi fissi nella lingua scelta (i numeri li scrive numeri(), dopo)
    var P = window.PROGETTO, S = Array.isArray(window.SCHEDE_RISULTATI) ? window.SCHEDE_RISULTATI : [];
    var T = Sito.T, num = Sito.formattaNumero, NS = "http://www.w3.org/2000/svg";
    function svg(id){ return document.querySelector("#" + id + " svg"); }
    function el(tag, att, testo){ var e = document.createElementNS(NS, tag); for(var k in att) e.setAttribute(k, att[k]); if(testo != null) e.textContent = testo; return e; }
    function scheda(id){ return S.filter(function(s){ return s && String(s.risultato) === String(id) && s.forma; })[0]; }   // id interno (campo «risultato»), mai il numero in pagina
    var forma = Sito.forma;
    function valoreScheda(n){ var s = scheda(n); return s ? String(forma(s).numero.valore) : null; }
    function elenco(v){ return v.length < 2 ? v.join("") : v.slice(0, -1).join(", ") + T(" e ", " and ", " und ") + v[v.length - 1]; }

    /* ---- numeri del testo: tutto arriva dai dati (data/progetto.js e le schede), niente scritto a mano ---- */
    function numeri(){
      var c = P && P.contatore, r = P && P.ritardi, n = P && P.in_numeri, k = P && P.controllo_auto, l = P && P.lavoro_ai, dm = P && P.domande, d = P && P.doppio;
      var lg = Sito.lingua(), inizio = c && c.inizio_raccolta ? new Date(c.inizio_raccolta + "T12:00:00").toLocaleDateString(lg === "en" ? "en-GB" : lg === "de" ? "de-DE" : "it-IT", {day: "numeric", month: "long", year: "numeric"}) : null;
      var milioni = c && c.passaggi >= 1e6;
      var v = {
        "sistema.inizio": inizio,
        "d1.giorni": dm && num(dm.d1.giorni_feriali), "d1.corse": dm && num(dm.d1.min_corse), "d1.forbice": dm && Sito.intervallo(dm.d1.oltre10_pct[0], dm.d1.oltre10_pct[1]),
        "d1.primo": dm && (dm.d1.primo_tratto[0] + " → " + dm.d1.primo_tratto[1]), "d3.volte": dm && num(dm.d3.volte_il_caso),
        "d4.senza": dm && num(dm.d4.senza_posti), "d4.fermate": dm && num(dm.d4.fermate), "d4.raggio": dm && num(dm.d4.raggio_m),
        "doppio.residenti": d && num(d.residenti), "doppio.quota": d && num(d.quota), "muoversi.volte": valoreScheda(8),
        "sistema.settimane": n && num(n.settimane), "sistema.commit": n && num(n.commit),
        "sistema.giorni": c && num(Sito.giorniRaccolta(c)),
        "sistema.sensori": P && num(P.sensori_5t),
        "sistema.passaggi": c && (milioni ? "~" + num(Math.round(c.passaggi / 1e5) / 10) + T(" milioni", " million", " Mio.") : num(c.passaggi)),
        "ritardi.feed": r && num(r.feed_pct), "ritardi.gps": r && num(r.gps_pct), "ritardi.rapporto": r && num(r.rapporto),
        "controllo.percorsi": k && num(k.percorsi), "controllo.errore": k && num(Math.round(k.errore_pct)),
        "lavoro.claude": l && num(l.claude_eur_mese), "lavoro.opencode": l && num(l.opencode_eur_mese), "lavoro.pi": l && num(l.raspberry_eur)
      };
      document.querySelectorAll("[data-ris]").forEach(function(e){   // «Scheda N»: il numero e l'indirizzo vengono dai dati
        var sc = scheda(e.getAttribute("data-ris")), nn = sc && sc.numero_pubblico != null ? sc.numero_pubblico : null;
        e.textContent = nn != null ? Sito.etichetta(nn) : T("Scheda", "Finding", "Ergebnis");
        if(nn != null) e.setAttribute("href", "index.html#p" + nn);
      });
      document.querySelectorAll("[data-n]").forEach(function(e){ var x = v[e.getAttribute("data-n")]; e.textContent = (x == null || x === "") ? "…" : x; });
      var f = document.getElementById("fareiPagina");
      if(f) f.innerHTML = P && P.raccomandazioni ? Sito.raccomandazioni(P.raccomandazioni).map(function(q){ return "<li>" + Sito.esc(q) + "</li>"; }).join("") : "";
    }

    /* ---- disegni ---- */
    function fN(){
      var s = svg("fN"); s.innerHTML = "";
      var n = P && P.in_numeri; if(!n) return;
      var c = P.contatore;
      var righe = [
        [n.passaggi ? "~" + num(Math.round(n.passaggi / 1e5) / 10) + " " + T("milioni", "million", "Mio.") : "", T("passaggi misurati col GPS", "departures measured by GPS", "per GPS gemessene Abfahrten")],
        [num(n.sensori), T("sensori del traffico", "traffic sensors", "Verkehrssensoren")],
        [num(n.sezioni), T("sezioni di censimento", "census sections", "Zählsprengel")],
        ["~" + num(n.fonti), T("fonti di dati aperti", "open data sources", "offene Datenquellen")],
        [num(n.settimane), T("settimane di lavoro", "weeks of work", "Arbeitswochen")]
      ];
      righe.forEach(function(r, i){
        var y = 10 + i * 56;
        s.appendChild(el("rect", {x: 20, y: y, width: 360, height: 46, rx: 9, "class": "d-scatola" + (i === 0 ? " acc" : "")}));
        s.appendChild(el("text", {x: 34, y: y + 32, "class": "d-grande"}, r[0]));
        s.appendChild(el("text", {x: 366, y: y + 28, "text-anchor": "end", "class": "d-testo"}, r[1]));
      });
    }

    function fP(){
      var s = svg("fP"); s.innerHTML = "";
      var cols = 9, righe = 6, x0 = 30, y0 = 70, dx = 40, dy = 36;
      s.appendChild(el("text", {x: 30, y: 36, "class": "d-titolo"}, "2020"));
      s.appendChild(el("text", {x: 370, y: 36, "class": "d-titolo", "text-anchor": "end"}, T("oggi", "today", "heute")));
      s.appendChild(el("text", {x: 30, y: 54, "class": "d-piccolo"}, T("la promessa", "the promise", "das Versprechen")));
      s.appendChild(el("text", {x: 370, y: 54, "class": "d-piccolo", "text-anchor": "end"}, T("la verifica", "the check", "die Überprüfung")));
      for(var j = 0; j < righe; j++) for(var i = 0; i < cols; i++){
        var vera = i >= 5 || (i === 4 && j % 2 === 0), c = el("circle", {cx: x0 + i * dx, cy: y0 + j * dy, r: vera ? 7 : 6, "class": vera ? "d-acceso a-accendi" : "d-spento"});
        if(vera) c.style.animationDelay = (0.05 * ((i - 4) * righe + j) + 0.15) + "s";
        s.appendChild(c);
      }
      s.appendChild(el("text", {x: 30, y: 296, "class": "d-piccolo"}, T("letteratura, nessun dato", "literature, no data", "Literatur, keine Daten")));
      s.appendChild(el("text", {x: 370, y: 296, "class": "d-piccolo", "text-anchor": "end"}, T("dati veri di Torino", "real data from Turin", "echte Daten aus Turin")));
    }

    function fQ(){
      var s = svg("fQ"); s.innerHTML = "";
      var d = P && P.domande && P.domande.d4; if(!d) return;
      var ok = d.fermate - d.senza_posti, pochi = d.senza_posti - d.nessun_parcheggio;
      var parti = [[d.nessun_parcheggio, T("nessun parcheggio vicino", "no car park nearby", "kein Parkplatz in der Nähe"), "d-rosso"], [pochi, T("troppo pochi posti", "too few spaces", "zu wenige Stellplätze"), "d-oro"], [ok, T("posti bastanti", "enough spaces", "genug Stellplätze"), "d-blu"]];
      s.appendChild(el("text", {x: 30, y: 36, "class": "d-titolo"}, T("Fermate importanti", "Major stops", "Wichtige Haltestellen") + " · " + num(d.fermate)));
      var W = 340, x0 = 30, tot = d.fermate;
      parti.forEach(function(q){
        var w = q[0] / tot * W; s.appendChild(el("rect", {x: x0, y: 60, width: w, height: 40, "class": q[2] + " a-cresci d-barra"})); x0 += w;
      });
      parti.forEach(function(q, i){
        var y = 150 + i * 46;
        s.appendChild(el("rect", {x: 30, y: y - 16, width: 16, height: 16, rx: 3, "class": q[2]}));
        s.appendChild(el("text", {x: 56, y: y - 2, "class": "d-testo"}, q[1]));
        s.appendChild(el("text", {x: 370, y: y - 1, "text-anchor": "end", "class": "d-grande"}, num(q[0])));
      });
    }

    function fM(){
      var s = svg("fM"); s.innerHTML = "";
      var righe = [T("Passeggeri per corsa e fermata", "Passengers per trip and stop", "Fahrgäste je Fahrt und Haltestelle"), T("Costi di esercizio per linea", "Operating costs per line", "Betriebskosten je Linie"), T("Flussi reali da luogo a luogo", "Real flows from place to place", "Echte Ströme von Ort zu Ort")];
      righe.forEach(function(t, i){
        var y = 20 + i * 90;
        s.appendChild(el("rect", {x: 20, y: y, width: 360, height: 70, rx: 12, "class": "d-livello manca"}));
        s.appendChild(el("text", {x: 48, y: y + 46, "class": "d-grande"}, "?"));
        s.appendChild(el("text", {x: 90, y: y + 42, "class": "d-testo"}, t));
      });
    }

    function fS(){
      var s = svg("fS"); s.innerHTML = "";
      var c = P && P.contatore;
      var passi = [
        ["Raspberry Pi", T("legge Torino ogni minuto", "reads Turin every minute", "liest Turin jede Minute")],
        [T("Archivio SQLite", "SQLite archive", "SQLite-Archiv"), c ? T(Sito.giorniRaccolta(c) + " giorni di dati", Sito.giorniRaccolta(c) + " days of data", Sito.giorniRaccolta(c) + " Tage Daten") : ""],
        [T("Script Python + motore di percorsi", "Python scripts + routing engine", "Python-Skripte + Routing-Engine"), T("calcoli, controlli, risultati", "calculations, checks, results", "Berechnungen, Kontrollen, Ergebnisse")],
        [T("Pagine HTML", "HTML pages", "HTML-Seiten"), T("mappa e schede, senza server", "map and findings, no server", "Karte und Ergebnisse, ohne Server")]
      ];
      var fonti = [["GTT", 30], ["5T", 76], ["ISTAT", 196], ["IMQ 2022", 242], ["OpenStreetMap", 288]];
      fonti.forEach(function(f){
        var verso = f[1] < 120 ? 14 + 31 : 14 + 2 * 98 + 31;
        s.appendChild(el("line", {x1: 112, x2: 140, y1: f[1] + 15, y2: verso, "class": "d-filo"}));
        s.appendChild(el("rect", {x: 8, y: f[1], width: 104, height: 30, rx: 15, "class": "d-scatola"}));
        s.appendChild(el("text", {x: 60, y: f[1] + 20, "text-anchor": "middle", "class": "d-testo"}, f[0]));
      });
      passi.forEach(function(q, i){
        var y = 14 + i * 98;
        s.appendChild(el("rect", {x: 140, y: y, width: 252, height: 62, rx: 10, "class": "d-scatola" + (i === 0 ? " acc" : "")}));
        s.appendChild(el("text", {x: 154, y: y + 26, "class": "d-testo", "font-weight": 700}, q[0]));
        s.appendChild(el("text", {x: 154, y: y + 47, "class": "d-piccolo"}, q[1]));
        if(i < passi.length - 1){
          s.appendChild(el("line", {x1: 266, x2: 266, y1: y + 64, y2: y + 96, "class": "d-filo"}));
          var d = el("circle", {cx: 266, cy: y + 64, r: 5, "class": "d-punto a-scorri"}); d.style.animationDelay = (i * 0.35) + "s";
          s.appendChild(d);
        }
      });
    }

    function fD(){
      var s = svg("fD"); s.innerHTML = "";
      if(!P){ return; }
      var g = el("g", {}), i = 0;
      P.zone.forEach(function(z){ g.appendChild(el("path", {d: z.d, "class": "d-zona" + (z.doppio ? " doppio" : ""), style: z.doppio ? "transition-delay:" + (0.25 + 0.2 * (i++)) + "s" : ""})); });
      s.appendChild(g);
      s.appendChild(el("path", {d: P.contorno.d, "class": "d-contorno"}));
      var etic = el("g", {}); s.appendChild(etic);
      // etichette al centro del riquadro di ogni zona in doppio svantaggio (calcolate dopo che le forme sono in pagina)
      requestAnimationFrame(function(){
        var paths = g.querySelectorAll(".doppio"), k = 0, messe = [];
        P.zone.forEach(function(z){
          if(!z.doppio) return;
          var b = paths[k++].getBBox(), x = b.x + b.width / 2, y = b.y + b.height / 2;
          messe.forEach(function(m){ if(Math.abs(m.y - y) < 30 && Math.abs(m.x - x) < 190) y = m.y + 32; });   // etichette che si sovrappongono: la seconda scende
          messe.push({x: x, y: y});
          etic.appendChild(el("text", {x: x, y: y, "text-anchor": "middle", "class": "d-etichetta"}, z.nome));
        });
      });
    }

    function fR(){
      var s = svg("fR"); s.innerHTML = "";
      var v = valoreScheda(8), m = v && /^(\d+(?:[.,]\d+)?)(?:\s*[–-]\s*(\d+(?:[.,]\d+)?))?$/.exec(v);
      if(!m){ s.appendChild(el("text", {x: 200, y: 150, "text-anchor": "middle", "class": "d-testo"}, v || "")); return; }
      var a = parseFloat(m[1].replace(",", ".")), b = m[2] ? parseFloat(m[2].replace(",", ".")) : a;
      var lo = Math.min(a, b), hi = Math.max(a, b), W = 300, u = W / Math.max(hi, 1) * 0.92;
      s.appendChild(el("text", {x: 30, y: 36, "class": "d-titolo"}, T("In auto", "By car", "Mit dem Auto")));
      s.appendChild(el("rect", {x: 30, y: 46, width: u, height: 30, rx: 5, "class": "d-oro a-cresci d-barra"}));
      s.appendChild(el("text", {x: 30 + u + 8, y: 67, "class": "d-grande"}, "1"));
      s.appendChild(el("text", {x: 30, y: 134, "class": "d-titolo"}, T("Coi mezzi pubblici", "By public transport", "Mit öffentlichen Verkehrsmitteln")));
      if(hi > lo) s.appendChild(el("rect", {x: 30, y: 144, width: u * hi, height: 30, rx: 5, "class": "d-blu a-cresci d-barra", opacity: .4}));
      s.appendChild(el("rect", {x: 30, y: 144, width: u * lo, height: 30, rx: 5, "class": "d-blu a-cresci d-barra"}));
      s.appendChild(el("text", {x: 30, y: 214, "class": "d-grande"}, v + " " + T("volte", "times", "Mal")));
      s.appendChild(el("text", {x: 30, y: 236, "class": "d-piccolo"}, T("il tempo dell'auto (traffico tipico, mediana)", "the car's time (typical traffic, median)", "die Fahrzeit des Autos (typischer Verkehr, Median)")));
      s.appendChild(el("text", {x: 30, y: 254, "class": "d-piccolo"}, T("da stima aperta a stima corretta col controllo", "from open estimate to estimate corrected by the check", "von offener Schätzung bis zur durch die Kontrolle korrigierten")));
    }

    function fG(){
      var s = svg("fG"); s.innerHTML = "";
      var r = P && P.ritardi; if(!r) return;
      var max = Math.max(r.gps_pct, r.feed_pct) * 1.15, H = 150, base = 200, w = 70;
      [[r.feed_pct, 90, T("Feed ufficiale", "Official feed", "Offizieller Feed"), "d-oro"], [r.gps_pct, 240, T("GPS dei mezzi", "Vehicle GPS", "Fahrzeug-GPS"), "d-blu"]].forEach(function(b){
        var h = b[0] / max * H, bar = el("rect", {x: b[1], y: base - h, width: w, height: h, rx: 5, "class": b[3]});
        bar.setAttribute("class", b[3] + " a-su");
        s.appendChild(bar);
        s.appendChild(el("text", {x: b[1] + w / 2, y: base - h - 8, "text-anchor": "middle", "class": "d-grande"}, num(b[0]) + "%"));
        s.appendChild(el("text", {x: b[1] + w / 2, y: base + 20, "text-anchor": "middle", "class": "d-testo"}, b[2]));
      });
      s.appendChild(el("line", {x1: 30, x2: 370, y1: base, y2: base, stroke: "var(--line)", "stroke-width": 1.5}));
      s.appendChild(el("text", {x: 200, y: 30, "text-anchor": "middle", "class": "d-titolo"}, T("Oltre 5 minuti di ritardo", "More than 5 minutes late", "Über 5 Minuten Verspätung")));
      s.appendChild(el("text", {x: 200, y: 274, "text-anchor": "middle", "class": "d-piccolo"}, T("sottostimato di " + num(r.rapporto) + " volte", "understated by " + num(r.rapporto) + " times", "um das " + num(r.rapporto) + "-Fache unterschätzt")));
    }

    function fF(){
      var s = svg("fF"); s.innerHTML = "";
      var R = P && P.raccomandazioni; if(!R) return;
      var righe = [
        ["bus", "~" + num(R.tratti_min), T("minuti persi dai bus ogni giorno feriale", "minutes lost by buses every weekday", "Minuten, die Busse pro Werktag verlieren")],
        ["P", Sito.intervallo(R.punti.da, R.punti.a) + "/" + num(R.punti.su), T("punti d'ingresso dove il mezzo è veloce", "entry points where public transport is fast", "Einfahrtspunkte, an denen der ÖV schnell ist")],
        ["casa", "~" + num(R.zone.abitanti), T("persone nelle zone a doppio svantaggio", "people in the double-disadvantage zones", "Menschen in den Zonen mit doppelter Benachteiligung")]
      ];
      righe.forEach(function(q, i){
        var y = 14 + i * 94;
        s.appendChild(el("rect", {x: 20, y: y, width: 360, height: 80, rx: 12, "class": "d-scatola" + (i === 0 ? " acc" : "")}));
        var ix = 38, iy = y + 20;
        if(q[0] === "bus"){
          s.appendChild(el("rect", {x: ix, y: iy, width: 52, height: 30, rx: 6, "class": "d-blu"}));
          s.appendChild(el("circle", {cx: ix + 12, cy: iy + 34, r: 5, "class": "d-oro"})); s.appendChild(el("circle", {cx: ix + 40, cy: iy + 34, r: 5, "class": "d-oro"}));
        } else if(q[0] === "P"){
          s.appendChild(el("circle", {cx: ix + 26, cy: iy + 20, r: 24, "class": "d-blu"}));
          s.appendChild(el("text", {x: ix + 26, y: iy + 30, "text-anchor": "middle", "class": "d-grande d-su-blu"}, "P"));
        } else {
          s.appendChild(el("path", {d: "M" + ix + " " + (iy + 20) + "l26 -22 l26 22 v26 h-52 z", "class": "d-blu"}));
          s.appendChild(el("rect", {x: ix + 21, y: iy + 28, width: 10, height: 18, "class": "d-oro"}));
        }
        s.appendChild(el("text", {x: 108, y: y + 38, "class": "d-grande"}, q[1]));
        s.appendChild(el("text", {x: 108, y: y + 60, "class": "d-piccolo"}, q[2]));
      });
    }

    function tutto(){ numeri(); fN(); fP(); fS(); fG(); fR(); fD(); fQ(); fF(); fM(); }
    tutto();
    window.addEventListener("lingua", function(){ if(document.body.contains(scena)) tutto(); });

    /* ---- il disegno è sempre quello della parte che sta più vicina al centro dello schermo (anche scorrendo veloce e all'indietro); senza disegno per «Chi sono» ---- */
    var figure = scena.querySelectorAll(".fig"), sezioni = scena.querySelectorAll(".testi [data-fig]"), attesa = false, ultima = null;
    function mostra(id){ if(id === ultima) return; ultima = id; figure.forEach(function(f){ f.classList.toggle("attiva", f.id === id); }); }
    function sincronizza(){
      attesa = false;
      var centro = (window.innerHeight || document.documentElement.clientHeight) / 2, best = null, dmin = 1e9;
      sezioni.forEach(function(e){
        var rc = e.getBoundingClientRect(), d = centro < rc.top ? rc.top - centro : centro > rc.bottom ? centro - rc.bottom : 0;
        if(d < dmin){ dmin = d; best = e; }
      });
      mostra(best ? best.getAttribute("data-fig") : "");
    }
    function richiedi(){ if(!attesa){ attesa = true; requestAnimationFrame(sincronizza); } }
    window.addEventListener("scroll", richiedi, {passive: true});
    window.addEventListener("resize", richiedi);
    sincronizza();
  }

  window.Progetto = {monta: monta};
})();
