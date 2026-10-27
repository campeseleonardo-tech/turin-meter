/* Area che si espande: dove si arriva in N minuti da Piazza Castello, coi mezzi pubblici e in auto, alle 7:45 di un feriale.
   Due mappe di Torino fatte di quadratini (una per sezione di censimento): si colorano quando il tempo e' entro i minuti. Senza comandi: le due aree
   crescono da sole da 0 a 45 minuti (circa 13 secondi), con «N minuti» scritto grande e le quote di torinesi raggiunti accanto alle aree; poi una pausa
   di 3 secondi e si ricomincia (solo mentre si vede). Auto = stima del tempo in auto, parcheggio compreso. Con «riduci movimento» e' ferma a 30 minuti.
   Nessun numero e' scritto qui: tutto arriva da data/area_tempi.js (scritto dallo script delle schede, da scripts/99_area_tempi.py);
   i dati delle altre zone di Torino restano nel file ma questa pagina non li usa.

   Uso:  contenitore.innerHTML = Area.html({compatto: true|false});     (il disegno parte da solo quando il contenitore compare nella pagina) */
(function(){
  "use strict";
  var MAX_MIN = 45, MIN_FERMO = 30, SEC_TOTALI = 13.5, PAUSA_MS = 3000;
  var ridotto = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  var contatore = 0, caricamento = null;

  var TESTI = {
    it: {minuti: "minuti", minuto: "minuto", mezzi: "Coi mezzi pubblici", auto: "In auto", ab: "dei torinesi", caricamentoKo: "Dati non disponibili.",
         parlato: function(m, pm, pa){ return "Da Piazza Castello, entro " + m + " minuti: coi mezzi pubblici " + pm + "% dei torinesi, in auto " + pa + "%."; }},
    en: {minuti: "minutes", minuto: "minute", mezzi: "By public transport", auto: "By car", ab: "of residents", caricamentoKo: "Data not available.",
         parlato: function(m, pm, pa){ return "From Piazza Castello, within " + m + " minutes: by public transport " + pm + "% of residents, by car " + pa + "%."; }},
    de: {minuti: "Minuten", minuto: "Minute", mezzi: "Mit öffentlichen Verkehrsmitteln", auto: "Mit dem Auto", ab: "der Einwohner", caricamentoKo: "Daten nicht verfügbar.",
         parlato: function(m, pm, pa){ return "Von der Piazza Castello innerhalb von " + m + " Minuten: mit öffentlichen Verkehrsmitteln " + pm + " % der Einwohner, mit dem Auto " + pa + " %."; }}
  };
  function lingua(){ var l = (document.documentElement.lang || "it").slice(0, 2); return l === "en" || l === "de" ? l : "it"; }
  function T(){ return TESTI[lingua()]; }
  function n(v){ return window.Sito && Sito.formattaNumero ? Sito.formattaNumero(v) : String(v); }
  function esc(s){ return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function css(nome, ripiego){ var v = getComputedStyle(document.documentElement).getPropertyValue(nome).trim(); return v || ripiego; }

  function stile(){
    if(document.getElementById("area-stile")) return;
    var s = document.createElement("style"); s.id = "area-stile";
    s.textContent = ".area{margin:8px 0}.area .area-minuti{display:block;text-align:center;font:700 40px/1.1 var(--font-titoli,inherit);color:var(--accent,#0b2559);font-variant-numeric:tabular-nums;margin:2px 0 8px}"
      + ".area .area-mappe{display:grid;grid-template-columns:1fr 1fr;gap:10px}.area .area-mappa h6{margin:0 0 4px;font:700 15px/1.2 var(--font-titoli,inherit);text-transform:uppercase;letter-spacing:.02em}"
      + ".area canvas{display:block;width:100%;height:auto;background:var(--sunk,#f7f8fc);border-radius:8px}"
      + ".area .area-quota{font:700 26px/1.1 var(--font-titoli,inherit);margin-top:6px;font-variant-numeric:tabular-nums}.area .area-quota small{display:block;font:400 13px var(--font-testi,inherit);color:var(--muted,#4a5a7a)}"
      + ".area-mini{margin:0}.area-mini .area-minuti{font-size:24px;margin:0 0 4px}.area-mini .area-mappe{gap:6px}.area-mini .area-mappa h6{font-size:12px;margin:0 0 2px}"
      + ".area-mini .area-quota{font-size:18px;margin-top:2px}.area-mini .area-quota small{font-size:11px}";
    document.head.appendChild(s);
  }

  /* ---- dati: data/area_tempi.js, caricato la prima volta che serve ---- */
  function carica(poi, male){
    if(window.AREA_TEMPI) return poi(window.AREA_TEMPI);
    if(!caricamento){
      caricamento = new Promise(function(ok, ko){
        var s = document.createElement("script"); s.src = "data/area_tempi.js";
        s.onload = function(){ window.AREA_TEMPI ? ok(window.AREA_TEMPI) : ko(); }; s.onerror = ko; document.head.appendChild(s);
      });
    }
    caricamento.then(poi, male);
  }

  /* ---- geometria: stessa per le due mappe ---- */
  function geom(D){
    if(D._g) return D._g;
    var mx = 0, my = 0, N = D.x.length, i;
    for(i = 0; i < N; i++){ if(D.x[i] > mx) mx = D.x[i]; if(D.y[i] > my) my = D.y[i]; }
    var k = Math.cos(45.07 * Math.PI / 180), W = mx * k, H = my, tot = 0;
    for(i = 0; i < N; i++) tot += D.r[i];
    D._g = {mx: mx, my: my, k: k, W: W, H: H, tot: tot, N: N};
    return D._g;
  }

  /* tempi di ogni sezione da Piazza Castello: mezzi (D.c.m) e auto con il tempo in auto corretto col controllo (D.c.k); null = non raggiunta */
  function quota(D, t, minuto){
    var g = geom(D), s = 0;
    for(var i = 0; i < g.N; i++) if(t[i] !== null && t[i] <= minuto) s += D.r[i];
    return 100 * s / g.tot;
  }

  function disegna(cv, D, t, minuto, colore){
    var g = geom(D), w = cv.width, h = cv.height, ctx = cv.getContext("2d");
    var pad = 6, sc = Math.min((w - 2 * pad) / g.W, (h - 2 * pad) / g.H);
    var lato = Math.max(2, 0.95 * Math.sqrt((g.W * sc) * (g.H * sc) / g.N));
    ctx.clearRect(0, 0, w, h);
    var spento = css("--line", "#c9d2e4"), i, px, py;
    var ox = pad + (w - 2 * pad - g.W * sc) / 2, oy = pad + (h - 2 * pad - g.H * sc) / 2;
    ctx.globalAlpha = .55; ctx.fillStyle = spento;
    for(i = 0; i < g.N; i++){
      if(t[i] !== null && t[i] <= minuto) continue;
      px = ox + D.x[i] * g.k * sc; py = oy + (g.my - D.y[i]) * sc;
      ctx.fillRect(px - lato / 2, py - lato / 2, lato, lato);
    }
    ctx.globalAlpha = .95; ctx.fillStyle = colore;
    for(i = 0; i < g.N; i++){
      if(t[i] === null || t[i] > minuto) continue;
      px = ox + D.x[i] * g.k * sc; py = oy + (g.my - D.y[i]) * sc;
      ctx.fillRect(px - lato / 2, py - lato / 2, lato, lato);
    }
    ctx.globalAlpha = 1;
    px = ox + D.ox * g.k * sc; py = oy + (g.my - D.oy) * sc;      // Piazza Castello
    ctx.lineWidth = 2.2; ctx.strokeStyle = css("--ink", "#0b2559"); ctx.fillStyle = css("--card", "#fff");
    ctx.beginPath(); ctx.arc(px, py, Math.max(4, lato * 1.1), 0, 6.2832); ctx.fill(); ctx.stroke();
  }

  function dimensiona(cv, D, larghezzaCss){
    var g = geom(D), r = window.devicePixelRatio > 1 ? 2 : 1;
    var w = Math.max(120, Math.round(larghezzaCss * r));
    cv.width = w; cv.height = Math.round(w * g.H / g.W);
  }

  function costruisci(el, D){
    var t = T(), mini = el.classList.contains("area-mini"), cMezzi = css("--neu-blu", "#6f8fc7"), cAuto = css("--neu-arancio", "#c9a227");
    var tm = D.c.m, ta = D.c.k || D.c.b, stato = {minuto: ridotto ? MIN_FERMO : 0};
    el.innerHTML = '<span class="area-minuti" aria-hidden="true"></span>'
      + '<div class="area-mappe"><div class="area-mappa"><h6>' + esc(t.mezzi) + '</h6><canvas data-k="m" aria-hidden="true"></canvas><div class="area-quota" data-q="m"></div></div>'
      + '<div class="area-mappa"><h6>' + esc(t.auto) + '</h6><canvas data-k="a" aria-hidden="true"></canvas><div class="area-quota" data-q="a"></div></div></div>';
    var cvs = Array.prototype.slice.call(el.querySelectorAll("canvas"));
    var larg = (el.clientWidth || (mini ? 240 : 600)) / 2 - (mini ? 6 : 10);
    cvs.forEach(function(cv){ dimensiona(cv, D, larg); });
    function ridisegna(){
      var m = stato.minuto, pm = quota(D, tm, m), pa = quota(D, ta, m);
      var testoAuto = n(Math.round(pa));
      cvs.forEach(function(cv){ var mezzi = cv.getAttribute("data-k") === "m"; disegna(cv, D, mezzi ? tm : ta, m, mezzi ? cMezzi : cAuto); });
      el.querySelector("[data-q=m]").innerHTML = n(Math.round(pm)) + '%<small>' + esc(t.ab) + '</small>';
      el.querySelector("[data-q=a]").innerHTML = testoAuto + '%<small>' + esc(t.ab) + '</small>';
      el.querySelector(".area-minuti").textContent = n(m) + " " + (m === 1 ? t.minuto : t.minuti);
    }
    ridisegna();
    el.setAttribute("role", "img");
    el.setAttribute("aria-label", t.parlato(MIN_FERMO, n(Math.round(quota(D, tm, MIN_FERMO))), n(Math.round(quota(D, ta, MIN_FERMO)))));
    if(ridotto) return;

    /* da sola: 0 -> 45 minuti, pausa, di nuovo; si ferma quando non si vede */
    var giro = ++contatore, visibile = false;
    el._anim = giro;
    function corsa(){
      var t0 = null;
      function passo(ts){
        if(el._anim !== giro || !document.body.contains(el)) return;
        if(!visibile){ el._inattesa = true; return; }
        if(t0 === null) t0 = ts;
        var f = Math.min(1, (ts - t0) / 1000 / SEC_TOTALI);
        stato.minuto = Math.round(f * MAX_MIN); ridisegna();
        if(f < 1) requestAnimationFrame(passo);
        else setTimeout(function(){ if(el._anim === giro) corsa(); }, PAUSA_MS);
      }
      requestAnimationFrame(passo);
    }
    stato.minuto = 0; ridisegna();
    if("IntersectionObserver" in window) new IntersectionObserver(function(v){
      visibile = v[0].isIntersecting;
      if(visibile && el._inattesa){ el._inattesa = false; corsa(); }
    }).observe(el); else visibile = true;
    el._inattesa = true;
    el._ferma = function(){ el._anim = 0; };
  }

  function avvia(el){
    if(el._pronto) return; el._pronto = true;
    stile();
    carica(function(D){
      costruisci(el, D);
      window.addEventListener("lingua", function(){ if(el._ferma) el._ferma(); if(document.body.contains(el)) costruisci(el, D); });
    }, function(){ el.textContent = T().caricamentoKo; });
  }

  function html(opz){ var mini = !!(opz && opz.compatto); return '<div class="area' + (mini ? " area-mini" : "") + '" data-area="1"></div>'; }

  function scansiona(radice){
    var els = (radice.querySelectorAll ? radice.querySelectorAll("[data-area]") : []);
    for(var i = 0; i < els.length; i++) avvia(els[i]);
    if(radice.matches && radice.matches("[data-area]")) avvia(radice);
  }
  function avviaTutto(){
    scansiona(document);
    new MutationObserver(function(muts){
      muts.forEach(function(m){ m.addedNodes.forEach(function(nd){ if(nd.nodeType === 1) scansiona(nd); }); });
    }).observe(document.body, {childList: true, subtree: true});
  }
  if(document.body) avviaTutto(); else document.addEventListener("DOMContentLoaded", avviaTutto);

  window.Area = {html: html, avvia: avvia};
})();
