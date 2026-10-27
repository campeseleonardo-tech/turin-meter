/* Funzioni comuni delle pagine del sito: lingua IT/EN/DE, numeri, numeri che salgono, data dei dati nel piè di pagina. */
"use strict";
(function(){
  function esc(s){ return String(s==null?"":s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

  /* ---- lingua: italiano (default), inglese o tedesco. Prima ?lang=, poi la scelta salvata, poi il browser (it → IT, de → DE, altrimenti EN) */
  var LINGUE = ["it", "en", "de"];
  var lang = "it";
  function leggiLingua(){
    var q = /[?&]lang=(it|en|de)\b/.exec(location.search);
    if(q) return q[1];
    try { var s = localStorage.getItem("tm_lingua"); if(LINGUE.indexOf(s) >= 0) return s; } catch(e){}
    var n = (navigator.language || "it").toLowerCase();
    return n.indexOf("it") === 0 ? "it" : n.indexOf("de") === 0 ? "de" : "en";
  }
  /* T(it, en, de): il testo nella lingua scelta; senza il tedesco ripiega sull'inglese */
  function T(it, en, de){ return lang === "it" ? it : lang === "de" && de !== undefined ? de : en; }
  /* testi fissi della pagina: l'elemento ha l'italiano dentro, l'inglese in data-en e il tedesco in data-de (aria-label: data-en-label, data-de-label) */
  function traduciStatico(radice){
    var r = radice || document;      // con «radice» solo i testi di quel pezzo di pagina (per i pezzi scritti dal codice, es. le tappe del progetto)
    if(!radice) document.documentElement.lang = lang;
    r.querySelectorAll("[data-en]").forEach(function(el){
      if(el.dataset.it === undefined) el.dataset.it = el.innerHTML;
      el.innerHTML = lang === "it" ? el.dataset.it : (lang === "de" && el.dataset.de !== undefined ? el.dataset.de : el.dataset.en);
    });
    r.querySelectorAll("[data-en-label]").forEach(function(el){
      if(el.dataset.itLabel === undefined) el.dataset.itLabel = el.getAttribute("aria-label") || "";
      el.setAttribute("aria-label", lang === "it" ? el.dataset.itLabel : (lang === "de" && el.dataset.deLabel !== undefined ? el.dataset.deLabel : el.dataset.enLabel));
    });
    if(radice) return;
    document.querySelectorAll(".lingua button").forEach(function(b){ b.setAttribute("aria-pressed", b.dataset.l === lang ? "true" : "false"); });
    var tit = document.querySelector("title");
    if(tit){
      if(tit.dataset.it === undefined) tit.dataset.it = tit.textContent;
      if(tit.dataset.en) tit.textContent = lang === "it" ? tit.dataset.it : (lang === "de" && tit.dataset.de ? tit.dataset.de : tit.dataset.en);
    }
  }
  function impostaLingua(l){
    if(LINGUE.indexOf(l) < 0 || l === lang) return;
    lang = l;
    try { localStorage.setItem("tm_lingua", l); } catch(e){}
    traduciStatico();
    dataAggiornamento();
    window.dispatchEvent(new Event("lingua"));
  }
  lang = leggiLingua();

  /* numero: italiano e tedesco (1.234,5) o inglese (1,234.5), al massimo una cifra decimale */
  function formattaNumero(n){
    if(typeof n !== "number" || !Number.isFinite(n)) return esc(String(n));
    var mig = lang === "en" ? "," : ".";
    if(Number.isInteger(n)) return (n < 0 ? "−" : "") + String(Math.abs(n)).replace(/\B(?=(\d{3})+(?!\d))/g, mig);
    return n.toLocaleString(lang === "en" ? "en-GB" : lang === "de" ? "de-DE" : "it-IT", {maximumFractionDigits:1});
  }
  /* data da «2026-10-22»: IT 22/10/2026, DE 22.10.2026, EN 22 Oct 2026 */
  var MESI_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function formattaData(iso){
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || "");
    if(!m) return "";
    if(lang === "en") return parseInt(m[3], 10) + " " + MESI_EN[parseInt(m[2], 10) - 1] + " " + m[1];
    return m[3] + (lang === "de" ? "." : "/") + m[2] + (lang === "de" ? "." : "/") + m[1];
  }

  var ridotto = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);

  /* il numero sale da 0 al valore in circa 2,6 secondi, partendo e arrivando piano, UNA volta sola, quando l'elemento appare.
     Durante la corsa solo numeri interi, senza virgola né %: il testo finale (decimali, %) compare solo all'arrivo.
     L'elemento ha già il testo finale: data-valore = il numero, oppure data-forbice = "21,28" (due numeri che salgono insieme).
     La larghezza resta quella del testo finale, così niente intorno si sposta. Senza animazione resta il testo finale. */
  function contaSu(el){
    if(!el || el.dataset.fatto) return;
    var fb = (el.dataset.forbice || "").split(",").map(parseFloat).filter(Number.isFinite);
    var fine = fb.length === 2 ? fb : [parseFloat(el.dataset.valore)];
    el.dataset.fatto = "1";
    if(!Number.isFinite(fine[0]) || ridotto || !window.requestAnimationFrame) return;
    var testoFinale = el.textContent, t0 = null, DUR = 2600, ultimo = "";
    el.style.display = "inline-block";
    el.style.minWidth = el.getBoundingClientRect().width + "px";
    function morbido(x){ return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
    function testo(f){ return fine.map(function(v){ return formattaNumero(Math.floor(v * f)); }).join("–"); }
    function passo(t){
      if(t0 === null) t0 = t;
      var x = Math.min(1, (t - t0) / DUR), s = x >= 1 ? testoFinale : testo(morbido(x));
      if(s !== ultimo){ el.textContent = s; ultimo = s; }
      if(x < 1) requestAnimationFrame(passo);
    }
    el.textContent = testo(0);
    requestAnimationFrame(passo);
  }
  function osserva(radice){
    var els = (radice || document).querySelectorAll("[data-valore],[data-forbice]");
    if(!("IntersectionObserver" in window)){ return; }
    var io = new IntersectionObserver(function(voci){
      voci.forEach(function(v){ if(v.isIntersecting){ io.unobserve(v.target); contaSu(v.target); } });
    }, {threshold:.3});
    els.forEach(function(e){ if(!e.dataset.fatto) io.observe(e); });
  }

  /* «Dati dal 09/10/2026 al 22/10/2026»: il periodo fisso dei dati (comuni.PERIODO, scritto da scripts/schede_risultati.py in data/schede_risultati.js) */
  function dataAggiornamento(){
    var el = document.getElementById("datiAggiornati");
    var p = window.SCHEDE_PERIODO;
    if(!el || !p || !formattaData(p.da) || !formattaData(p.a)) return;
    el.textContent = T("Dati dal ", "Data from ", "Daten vom ") + formattaData(p.da) + T(" al ", " to ", " bis ") + formattaData(p.a) + ".";
  }

  /* giorni dalla raccolta: dal primo giorno (INIZIO_RACCOLTA, nel contatore dei dati) a oggi; la stessa regola per home e progetto */
  function giorniRaccolta(c){
    var m = c && /^(\d{4})-(\d{2})-(\d{2})$/.exec(c.inizio_raccolta || c.dal || "");
    if(!m) return null;
    var oggi = new Date(), d0 = new Date(+m[1], +m[2] - 1, +m[3]);
    return Math.max(1, Math.floor((new Date(oggi.getFullYear(), oggi.getMonth(), oggi.getDate()) - d0) / 864e5) + 1);
  }

  /* la forma di una scheda nella lingua scelta: forma_de, poi forma_en, poi l'italiana */
  function forma(s){
    return (lang === "de" && s.forma_de) || (lang !== "it" && s.forma_en) || s.forma;
  }
  /* «Risultato 2» / «Finding 2» / «Ergebnis 2» */
  function etichetta(n){ return T("Risultato ", "Finding ", "Ergebnis ") + n; }

  /* i risultati in due gruppi (campo «gruppo» delle schede, scritto da scripts/schede_risultati.py): la vetrina (3 risultati) e l'approfondimento (1).
     voce(scheda, posizione) scrive il riquadro di una scheda; classe = classe CSS del contenitore dei riquadri. La home usa lo stesso codice. */
  var GRUPPI = [
    {id: "vetrina", it: "Risultati principali", en: "Key findings", de: "Wichtigste Ergebnisse"},
    {id: "approfondimento", it: "Approfondimento", en: "Deep dive", de: "Vertiefung"}
  ];
  function perGruppi(schede, voce, classe){
    return GRUPPI.map(function(g, k){
      var righe = schede.map(function(s, i){
        var suo = s.gruppo === g.id || (k === 0 && !GRUPPI.some(function(x){ return x.id === s.gruppo; }));
        return suo ? voce(s, i) : "";
      }).join("");
      var titolo = esc(T(g.it, g.en, g.de));
      return righe ? '<section class="gruppo" aria-label="' + titolo + '"><h2 class="gruppo-titolo">' + titolo + '</h2><div class="' + classe + '">' + righe + '</div></section>' : "";
    }).join("");
  }

  function avvia(){
    document.querySelectorAll(".lingua button").forEach(function(b){ b.addEventListener("click", function(){ impostaLingua(b.dataset.l); }); });
    traduciStatico();
  }
  /* «Tre decisioni per Torino»: le stesse tre righe nella home e nella pagina del progetto (§5.0 del piano). I numeri vengono da R = window.PROGETTO.raccomandazioni
     (scritto da scripts/schede/raccomandazioni.py). Ritorna tre frasi nella lingua scelta. */
  function intervallo(a, b, pre){
    pre = pre || "";
    return a === b ? pre + formattaNumero(a) : pre + formattaNumero(Math.min(a, b)) + "–" + formattaNumero(Math.max(a, b));
  }
  function raccomandazioni(R){
    var tratti = R ? "~" + formattaNumero(R.tratti_min) : "…", p = R && R.punti, z = R && R.zone;
    var da = R && R.tratti_fascia ? R.tratti_fascia : ["…", "…"];
    var punti = p ? formattaNumero(p.n) : "…", su = p ? formattaNumero(p.su) : "…";
    var pmin = p ? "~" + formattaNumero(p.posti_min) : "…", pmax = p ? "~" + formattaNumero(p.posti_max) : "…", uno = p && p.posti_min === p.posti_max;
    var nz = z ? formattaNumero(z.n) : "…", ab = z ? "~" + formattaNumero(z.abitanti) : "…";
    return [
      T("Priorità ai bus nei 10 tratti dove perdono più tempo: " + tratti + " minuti persi in media ogni giorno feriale, fra le " + da[0] + " e le " + da[1] + ".",
        "Priority for buses on the 10 segments where they lose the most time: " + tratti + " minutes lost on average every weekday, between " + da[0] + " and " + da[1] + " a.m.",
        "Vorrang für Busse auf den 10 Abschnitten, auf denen sie am meisten Zeit verlieren: " + tratti + " Minuten gehen im Schnitt an jedem Werktag zwischen " + da[0] + " und " + da[1] + " Uhr verloren."),
      T("Parcheggi di scambio dove il mezzo è veloce (" + punti + " punti d'ingresso su " + su + "): lì mancano " + (uno ? pmin : "da " + pmin + " a " + pmax) + " posti per parcheggio.",
        "Park-and-ride where public transport is fast (" + punti + " of " + su + " entry points): there, " + (uno ? pmin : pmin + " to " + pmax) + " spaces per car park are missing.",
        "Park-and-Ride dort, wo der öffentliche Verkehr schnell ist (" + punti + " von " + su + " Einfahrtspunkten): Dort fehlen " + (uno ? pmin : pmin + " bis " + pmax) + " Stellplätze pro Parkplatz."),
      T("Servizi di prossimità nelle " + nz + " zone a doppio svantaggio, dove vivono " + ab + " persone.",
        "Local services in the " + nz + " zones of double disadvantage, home to " + ab + " people.",
        "Wohnortnahe Angebote in den " + nz + " Zonen mit doppelter Benachteiligung, in denen " + ab + " Menschen leben.")
    ];
  }

  window.Sito = {raccomandazioni: raccomandazioni, intervallo: intervallo, esc: esc, formattaNumero: formattaNumero, formattaData: formattaData, contaSu: contaSu, osserva: osserva, perGruppi: perGruppi, dataAggiornamento: dataAggiornamento,
                 giorniRaccolta: giorniRaccolta, ridotto: ridotto, forma: forma, etichetta: etichetta,
                 T: T, traduci: traduciStatico, lingua: function(){ return lang; }, impostaLingua: impostaLingua, avvia: avvia};
})();
