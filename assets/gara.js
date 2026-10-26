/* Gara bus contro auto: un bus e un'auto partono insieme da un luogo e corrono verso l'arrivo (di solito Piazza Castello).
   La durata e' proporzionale ai minuti veri (1 minuto vero = 0,15 secondi). Nessun numero e' scritto qui: tutto arriva dai dati.

   Nessun comando: le corse vanno da sole una dopo l'altra (un luogo solo = sempre la stessa), col nome del luogo sopra (nome lungo: «...», nome intero nel title),
   un'auto sola (auto_min: tempo in auto, parcheggio compreso); all'arrivo i minuti, il distacco e la frase di esito. Con «riduci movimento» tutte le corse ferme, una sotto l'altra.
   Schede dei risultati e pannello della mappa usano lo stesso componente.

   Uso:
     contenitore.innerHTML = Gara.html({luoghi: [{nome, arrivo, bus, auto_min, giudizio}]});
   Il disegno parte da solo quando il contenitore compare nella pagina (MutationObserver), quindi basta inserire l'html. */
(function(){
  "use strict";
  var SEC_PER_MIN = 0.15, VIA = 8, FINE = 396, LARG_VEICOLO = 40;
  var ridotto = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  var contatore = 0;

  var TESTI = {
    it: {centro: "Piazza Castello", bus: "Bus", auto: "Auto", min: "min", un: ["minuto", "minuti"],
         parlato: function(l){ return "Da " + l.nome + " a " + (l.arrivo || "Piazza Castello") + ": bus " + n(l.bus) + " " + mm(l.bus, "it") + ", auto " + n(l.auto_min) + " " + mm(l.auto_min, "it") + ", parcheggio compreso." + (l.giudizio ? " " + l.giudizio + "." : ""); }},
    en: {centro: "Piazza Castello", bus: "Bus", auto: "Car", min: "min", un: ["minute", "minutes"],
         parlato: function(l){ return "From " + l.nome + " to " + (l.arrivo || "Piazza Castello") + ": bus " + n(l.bus) + " " + mm(l.bus, "en") + ", car " + n(l.auto_min) + " " + mm(l.auto_min, "en") + ", parking included." + (l.giudizio ? " " + l.giudizio + "." : ""); }},
    de: {centro: "Piazza Castello", bus: "Bus", auto: "Auto", min: "Min.", un: ["Minute", "Minuten"],
         parlato: function(l){ return "Von " + l.nome + " nach " + (l.arrivo || "Piazza Castello") + ": Bus " + n(l.bus) + " " + mm(l.bus, "de") + ", Auto " + n(l.auto_min) + " " + mm(l.auto_min, "de") + ", Parken inklusive." + (l.giudizio ? " " + l.giudizio + "." : ""); }}
  };
  function mm(v, l){ return TESTI[l].un[Math.round(v) === 1 ? 0 : 1]; }
  function lingua(){ var l = (document.documentElement.lang || "it").slice(0, 2); return l === "en" || l === "de" ? l : "it"; }
  function T(){ return TESTI[lingua()]; }
  function n(v){ return window.Sito && Sito.formattaNumero ? Sito.formattaNumero(Math.round(v)) : String(Math.round(v)); }
  function esc(s){ return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }

  /* icone semplici, 40 x 20, origine in alto a sinistra; il davanti e' a destra */
  var BUS = '<rect x="0" y="1" width="40" height="15" rx="3.5"/><rect x="4" y="4" width="7" height="5" rx="1" class="gv-vetro"/><rect x="13" y="4" width="7" height="5" rx="1" class="gv-vetro"/>'
          + '<rect x="22" y="4" width="7" height="5" rx="1" class="gv-vetro"/><rect x="31" y="4" width="6" height="8" rx="1" class="gv-vetro"/><circle cx="9" cy="17" r="3"/><circle cx="31" cy="17" r="3"/>';
  var AUTO = '<path d="M1 14V10.5c0-1.6 1-2.7 2.600-3L11 5.500c1.500-2.600 3.200-4 5.500-4h6c2.500 0 4.300 1.400 5.800 3.800L35 7.500c2.600.5 4 1.800 4 4V14z"/>'
           + '<path d="M13 6.500c1-1.800 2-2.700 3.600-2.700H21V7.500H12z" class="gv-vetro"/><path d="M23.500 3.800h1.400c1.300 0 2.300.8 3.200 2.200l.6 1.500h-5.200z" class="gv-vetro"/><circle cx="10" cy="15" r="3.200"/><circle cx="30" cy="15" r="3.200"/>';

  function stile(){
    if(document.getElementById("gara-stile")) return;
    var s = document.createElement("style"); s.id = "gara-stile";
    s.textContent = ".gara{margin:8px 0}.gara svg{display:block;width:100%;height:auto}"
      + ".gara .gv{fill:var(--neu-blu,#6f8fc7)}.gara .gv.auto{fill:var(--neu-arancio,#c9a227)}.gara .gv-vetro{fill:var(--card,#fff);opacity:.85}"
      + ".gara .gara-strada{stroke:var(--line,#c9d1e3);stroke-width:1.5;stroke-dasharray:5 5}.gara .gara-arrivo{stroke:var(--vr-rosso,#a61e33);stroke-width:2}"
      + ".gara text{font-family:inherit;fill:var(--muted,#5b6578);font-size:13px}.gara text.gara-da{fill:var(--ink,#1b2433);font-weight:700;font-size:14px}"
      + ".gara text.gara-min{fill:var(--ink,#1b2433);font-size:15px;font-weight:700;opacity:0}"
      + ".gara .barra-ferma{fill:var(--neu-blu,#6f8fc7)}.gara .barra-ferma.auto{fill:var(--neu-arancio,#c9a227)}";
    document.head.appendChild(s);
  }

  function corri(el, fine){
    var carri = Array.prototype.slice.call(el.querySelectorAll(".gara-svg g.gv"));
    var etich = Array.prototype.slice.call(el.querySelectorAll(".gara-svg text.gara-min"));
    var id = ++contatore; el._corsa = id;
    var t0 = null;
    function y(g){ return g.getAttribute("transform").split(" ")[1].replace(")", ""); }
    function passo(ts){
      if(el._corsa !== id || !document.body.contains(el)) return;
      if(t0 === null) t0 = ts;
      var sec = Math.max(0, (ts - t0) / 1000), finito = true;
      carri.forEach(function(g, j){
        var dur = parseFloat(g.getAttribute("data-min")) * SEC_PER_MIN, f = Math.min(1, sec / dur);
        g.setAttribute("transform", "translate(" + (VIA + f * (FINE - VIA - LARG_VEICOLO)).toFixed(1) + " " + y(g) + ")");
        etich[j].style.opacity = f >= 1 ? 1 : 0;
        if(f < 1) finito = false;
      });
      if(!finito) requestAnimationFrame(passo); else if(fine) fine();
    }
    requestAnimationFrame(passo);
  }

  /* ---------------- modo «giro» (schede): senza comandi, una corsa dopo l'altra ---------------- */
  var GA = {passo: 50};
  function taglia(testo, maxCar){ return testo.length > maxCar ? testo.slice(0, Math.max(1, maxCar - 1)).trim() + "…" : testo; }
  /* il disegno di un luogo: nome sopra (e arrivo a destra), due corsie (bus, auto) con il distacco all'arrivo, frase di esito sotto.
     statico = true (riduci movimento): i mezzi sono gia' all'arrivo e i minuti scritti */
  function svgGiro(l, statico){
    var t = T(), arrivo = l.arrivo || t.centro;
    /* telefono (sotto 560 px): il disegno e' largo quanto la colonna, cosi' i caratteri restano di almeno 12 px; l'arrivo va su una seconda riga */
    var tel = window.innerWidth < 560, W = tel ? Math.max(280, Math.min(480, window.innerWidth - 104)) : 480, off = tel ? 18 : 0;
    FINE = tel ? W - 76 : 396;
    var maxArrivo = 22, arrivoT = taglia(arrivo, maxArrivo);
    var spazio = tel ? Math.floor((W - 2 * VIA) / 9) : Math.floor((FINE - VIA - arrivoT.length * 7.2 - 18) / 9.6);    // caratteri del nome a 17 px (circa 9,6 px l'uno)
    var nomeT = taglia(l.nome, Math.max(8, spazio));
    var cs = [{k: "bus", nome: t.bus, min: l.bus, forma: BUS}, {k: "auto", nome: t.auto, min: l.auto_min, forma: AUTO}];
    var maxMin = Math.max(cs[0].min, cs[1].min), distacco = Math.round(maxMin) - Math.round(Math.min(cs[0].min, cs[1].min));
    var H = 44 + off + cs.length * GA.passo + (l.giudizio ? 26 : 8);
    var righe = cs.map(function(c, j){
      var y = 50 + off + j * GA.passo;
      var scia = distacco >= 1 && c.min === maxMin ? '<tspan class="gara-distacco" x="' + (FINE + 8) + '" dy="16" style="font-size:13px;font-weight:700">+' + n(distacco) + ' ' + t.min + '</tspan>' : "";
      var base = '<text x="' + VIA + '" y="' + (y - 4) + '">' + esc(c.nome) + '</text><line class="gara-strada" x1="' + VIA + '" x2="' + FINE + '" y1="' + (y + 28) + '" y2="' + (y + 28) + '"/>';
      var tx = '<text class="gara-min" x="' + (FINE + 8) + '" y="' + (y + 18) + '"' + (statico ? ' style="opacity:1"' : "") + '>' + n(c.min) + ' ' + t.min + scia + '</text>';
      if(statico){
        var w = Math.max(6, c.min / maxMin * (FINE - VIA));
        return base + '<rect class="barra-ferma' + (c.k === "auto" ? " auto" : "") + '" x="' + VIA + '" y="' + (y + 4) + '" width="' + w.toFixed(1) + '" height="18" rx="3"/>' + tx;
      }
      return base + '<g class="gv ' + c.k + '" data-min="' + c.min + '" transform="translate(' + VIA + ' ' + (y + 2) + ')">' + c.forma + '</g>' + tx;
    }).join("");
    var esito = l.giudizio ? '<text class="gara-esito" x="' + VIA + '" y="' + (H - 8) + '" style="font-size:14px;fill:var(--ink,#1b2433);' + (statico ? "" : "opacity:0") + '">' + esc(l.giudizio.charAt(0).toUpperCase() + l.giudizio.slice(1)) + '</text>' : "";
    return '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(t.parlato(l)) + '">'
      + '<line class="gara-arrivo" x1="' + (FINE + 2) + '" x2="' + (FINE + 2) + '" y1="' + (28 + off) + '" y2="' + (H - 30) + '"/>'
      + '<text x="' + VIA + '" y="20" class="gara-da" style="font-size:17px">' + esc(nomeT) + (nomeT !== l.nome ? '<title>' + esc(l.nome) + '</title>' : "") + '</text>'
      + (tel ? '<text x="' + VIA + '" y="38" style="font-size:13px">\u2192 ' + esc(arrivoT) + (arrivoT !== arrivo ? '<title>' + esc(arrivo) + '</title>' : "") + '</text>'
             : '<text x="' + (FINE + 2) + '" y="20" text-anchor="end" style="font-size:13px">' + esc(arrivoT) + (arrivoT !== arrivo ? '<title>' + esc(arrivo) + '</title>' : "") + '</text>')
      + righe + esito + '</svg>';
  }
  function avviaGiro(el, dati){
    stile();
    var luoghi = dati.luoghi;
    if(ridotto){
      el.innerHTML = luoghi.map(function(l){ return '<div class="gara-svg">' + svgGiro(l, true) + '</div>'; }).join("");
      return;
    }
    el.innerHTML = '<div class="gara-svg"></div>';
    var cont = el.querySelector(".gara-svg"), i = 0, visibile = true, attesa = false;
    function corsa(){
      cont.innerHTML = svgGiro(luoghi[i], false);
      var esito = cont.querySelector(".gara-esito");
      corri(el, function(){
        if(esito) esito.style.opacity = 1;
        setTimeout(prossima, 2200);
      });
    }
    function prossima(){
      if(!document.body.contains(el)) return;
      if(!visibile){ attesa = true; return; }
      i = (i + 1) % luoghi.length;
      corsa();
    }
    if("IntersectionObserver" in window) new IntersectionObserver(function(v){
      visibile = v[0].isIntersecting;
      if(visibile && attesa){ attesa = false; prossima(); }
    }).observe(el);
    corsa();
  }

  function html(dati){
    var base = (dati.luoghi || []).filter(function(l){ return typeof l.bus === "number" && typeof l.auto_min === "number"; });
    if(!base.length) return "";
    return '<div class="gara" data-gara="' + esc(JSON.stringify({luoghi: base})) + '"></div>';
  }

  function avvia(el){
    if(el._pronto) return; el._pronto = true;
    var dati; try { dati = JSON.parse(el.getAttribute("data-gara")); } catch(e){ return; }
    avviaGiro(el, dati);
  }

  function scansiona(radice){
    var els = (radice.querySelectorAll ? radice.querySelectorAll("[data-gara]") : []);
    for(var i = 0; i < els.length; i++) avvia(els[i]);
    if(radice.matches && radice.matches("[data-gara]")) avvia(radice);
  }
  function avviaTutto(){
    scansiona(document);
    new MutationObserver(function(muts){
      muts.forEach(function(m){ m.addedNodes.forEach(function(nd){ if(nd.nodeType === 1) scansiona(nd); }); });
    }).observe(document.body, {childList: true, subtree: true});
  }
  if(document.body) avviaTutto(); else document.addEventListener("DOMContentLoaded", avviaTutto);

  window.Gara = {html: html, avvia: avvia};
})();
