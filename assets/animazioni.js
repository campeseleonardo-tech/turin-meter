/* Animazioni delle schede dei risultati, le stesse in grande (scheda aperta) e in piccolo (riquadri della home).
   Ogni scheda porta in f.anima la sua descrizione (scritta da scripts/schede/*.py: tutti i numeri e i testi arrivano dai dati).
   Uso: contenitore.innerHTML = Anima.html(f.anima, {compatto: true|false}); l'animazione parte da sola quando compare nella pagina.
   Tipi: «cerchi» (servizi a piedi), «quadratini» (ritardi, anche per fascia oraria), «fermate» (forma di Torino con le fermate),
   «omini» (1 su N), «area» (assets/area.js, l'area che si espande), «gara» (assets/gara.js, che qui gira da sola da un luogo all'altro) e
   «contatori» (due costi in euro che salgono insieme, mese per mese: la scheda «Quanto costa muoversi»).
   Con «riduci movimento» si vede subito la figura finale, con i numeri scritti. */
(function(){
  "use strict";
  var ridotto = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  var NS = "http://www.w3.org/2000/svg";
  function esc(s){ return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function num(v, dec){ return window.Sito ? Sito.formattaNumero(dec ? Math.round(v * 10) / 10 : Math.round(v)) : String(Math.round(v)); }
  function morbido(x){ return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }   // parte e arriva piano
  function dopo(ms, el, fn){ var id = setTimeout(function(){ if(document.body.contains(el)) fn(); }, ms); (el._timer = el._timer || []).push(id); }
  function ferma(el){ (el._timer || []).forEach(clearTimeout); el._timer = []; el._giro = (el._giro || 0) + 1; }
  /* un valore che cambia piano da a a b in ms millisecondi; fn(v) a ogni passo, fine() alla fine */
  function scorri(el, a, b, ms, fn, fine){
    var id = el._giro, t0 = null;
    function passo(t){
      if(id !== el._giro || !document.body.contains(el)) return;
      if(t0 === null) t0 = t;
      var x = Math.min(1, (t - t0) / ms);
      fn(a + (b - a) * morbido(x));
      if(x < 1) requestAnimationFrame(passo); else if(fine) fine();
    }
    requestAnimationFrame(passo);
  }

  function stile(){
    if(document.getElementById("anima-stile")) return;
    var s = document.createElement("style"); s.id = "anima-stile";
    s.textContent = ".anima{margin:4px 0 14px}.anima svg{display:block;width:100%;height:auto}"
      + ".anima .an-testo{color:var(--ink);font-family:var(--font-testi);font-size:15px;overflow-wrap:anywhere}.anima .an-piccolo{fill:var(--muted);font-family:var(--font-testi);font-size:13px}"
      + ".anima .an-num{color:var(--accent);font-family:var(--font-titoli);font-weight:700;font-size:30px;line-height:1.1;font-variant-numeric:tabular-nums}"
      + ".anima .an-cer{display:flex;flex-wrap:wrap;align-items:center;gap:8px 22px}.anima .an-cer svg{flex:0 1 260px;width:260px;max-width:100%}"
      + ".anima .an-righe{flex:1 1 210px;min-width:0}.anima .an-riga{margin:0 0 10px}.anima .an-riga .an-num{display:block}"
      + ".anima.compatto .an-cer{flex-wrap:nowrap;gap:10px}.anima.compatto .an-cer svg{flex:0 1 120px;width:120px}.anima.compatto .an-righe{flex:1 1 auto}"
      + ".anima.compatto .an-riga{margin:0 0 4px;display:flex;align-items:baseline;gap:8px;white-space:nowrap}.anima.compatto .an-riga .an-num{display:inline;font-size:20px}.anima.compatto .an-riga .an-testo{font-size:14px;color:var(--muted)}"
      + ".anima .didascalia{margin:6px 0 0;font-size:14px;color:var(--muted);min-height:2.6em}"
      + ".anima .an-cerchio{fill:var(--vr-verde);stroke:var(--vr-verde);stroke-width:2}.anima .an-casa{fill:var(--ink)}"
      + ".anima .an-quadri{display:grid;grid-template-columns:repeat(20,1fr);gap:3px;max-width:520px}"
      + ".anima .an-quadri i{display:block;aspect-ratio:1;border-radius:2px;background:var(--traccia);transition:background-color .35s ease}"
      + ".anima .an-quadri i.r5{background:var(--vr-giallo)}.anima .an-quadri i.r10{background:var(--vr-rosso)}"
      + ".anima .an-fascia{display:flex;align-items:baseline;gap:10px;margin:0 0 6px;min-height:1.6em;font-size:15px}"
      + ".anima .an-fascia b{font:700 22px/1 var(--font-titoli);color:var(--accent);font-variant-numeric:tabular-nums;min-width:3.2ch}"
      + ".anima .an-legenda{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:8px;font-size:13.5px;color:var(--muted)}"
      + ".anima .an-legenda i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}"
      + ".anima .an-legenda b{color:var(--ink);font-variant-numeric:tabular-nums}"
      + ".anima .an-contorno{fill:var(--sunk);stroke:var(--line);stroke-width:3}"
      + ".anima .f0{fill:var(--vr-verde)}.anima .f1{fill:var(--vr-giallo)}.anima .f2{fill:var(--vr-rosso)}"
      + ".anima .an-prio{fill:none;stroke:var(--ink);stroke-width:4}"
      + ".anima .an-omini{display:flex;flex-wrap:wrap;gap:4px;align-items:flex-end}"
      + ".anima .an-omini svg{width:26px;height:52px;fill:var(--omino);transition:fill .5s ease,opacity .45s ease,transform .45s ease}"
      + ".anima .an-omini svg.nascosto{opacity:0;transform:translateY(6px)}.anima .an-omini svg.acceso{fill:var(--vr-rosso)}"
      + ".anima.compatto .didascalia{font-size:13px;min-height:0}.anima.compatto .an-omini svg{width:20px;height:40px}"
      + ".anima.compatto .an-fascia{font-size:13.5px}.anima.compatto .an-fascia b{font-size:19px}"
      + ".anima .an-cr{display:grid;grid-template-columns:minmax(76px,26%) 1fr 8ch;gap:8px;align-items:center;margin:0 0 8px}"
      + ".anima .an-traccia{display:block;height:16px;border-radius:3px;background:var(--traccia);overflow:hidden}.anima .an-traccia i{display:block;height:100%;width:0;background:var(--vr-rosso)}"
      + ".anima .an-traccia i.t-verde{background:var(--vr-verde)}"
      + ".anima .an-eur{font:700 20px/1.1 var(--font-titoli);color:var(--accent);text-align:right;font-variant-numeric:tabular-nums}"
      + ".anima.compatto .an-cr{margin:0 0 4px}.anima.compatto .an-eur{font-size:16px}";
    document.head.appendChild(s);
  }

  /* ---------------- servizi: tre cerchi intorno a una casa, 5 -> 10 -> 15 minuti a piedi ----------------
     Nel disegno SVG solo cerchi e casa; numeri e frasi sono HTML accanto (vanno a capo sotto il disegno se la scheda e' stretta). */
  function cerchi(el, a){
    var v = a.voci || [], R = [42, 84, 126], cx = 135, cy = 135, compatto = el.classList.contains("compatto");
    var rings = v.map(function(x, i){ return '<circle class="an-cerchio" cx="' + cx + '" cy="' + cy + '" r="' + R[i] + '" style="fill-opacity:' + (.08 + .06 * (2 - i)) + ';stroke-opacity:.8" data-r="' + R[i] + '"/>'; }).reverse().join("");
    var righe = v.map(function(x, i){
      return '<div class="an-riga" data-i="' + i + '"><b class="an-num" data-pct="' + x.pct + '">~' + num(x.pct) + '%</b>'
        + '<span class="an-testo">' + (compatto ? esc(x.min) + '′' : esc(x.testo)) + '</span></div>';
    }).join("");
    var casa = '<path class="an-casa" d="M' + (cx - 11) + ' ' + (cy + 10) + 'v-12l11-9 11 9v12h-7v-7h-8v7z"/>';
    el.innerHTML = '<div class="an-cer"><svg viewBox="0 0 270 270" role="img" aria-label="' + esc(a.didascalia) + '">' + rings + casa + '</svg>'
      + '<div class="an-righe">' + righe + '</div></div>'
      + (a.didascalia && !compatto ? '<p class="didascalia">' + esc(a.didascalia) + '</p>' : "");
    if(ridotto) return;
    var cs = Array.prototype.slice.call(el.querySelectorAll(".an-cerchio")).reverse(), rs = el.querySelectorAll(".an-riga");
    cs.forEach(function(c){ c.setAttribute("r", 0); });
    Array.prototype.forEach.call(rs, function(g){ g.style.opacity = 0; });
    function anello(i){
      if(i >= cs.length) return;
      var c = cs[i], r = parseFloat(c.getAttribute("data-r")), t = rs[i].querySelector(".an-num"), p = parseFloat(t.getAttribute("data-pct"));
      rs[i].style.transition = "opacity .5s"; rs[i].style.opacity = 1;
      scorri(el, 0, 1, 1500, function(x){ c.setAttribute("r", (r * x).toFixed(1)); t.textContent = "~" + num(p * x) + "%"; },
        function(){ t.textContent = "~" + num(p) + "%"; dopo(350, el, function(){ anello(i + 1); }); });
    }
    anello(0);
  }

  /* ---------------- ritardi: 100 quadratini; poi il giorno che scorre, fascia per fascia ---------------- */
  function quadratini(el, a){
    var tot = a.totale || 100;
    el.innerHTML = '<div class="an-fascia" aria-live="polite"><b></b><span></span></div>'
      + '<div class="an-quadri" role="img" aria-label="' + esc(a.didascalia) + '">' + new Array(tot + 1).join("<i></i>") + '</div>'
      + '<div class="an-legenda"><span><i style="background:var(--vr-giallo)"></i>' + esc(a.legenda5) + '</span><span><i style="background:var(--vr-rosso)"></i>' + esc(a.legenda10) + '</span></div>'
      + (a.didascalia && !el.classList.contains("compatto") ? '<p class="didascalia">' + esc(a.didascalia) + '</p>' : "");
    var q = el.querySelectorAll(".an-quadri i"), b = el.querySelector(".an-fascia b"), sp = el.querySelector(".an-fascia span");
    function colora(n5, n10){ for(var i = 0; i < q.length; i++) q[i].className = i < n10 ? "r10" : i < n5 ? "r5" : ""; }
    var n5 = Math.round(a.oltre5), n10 = Math.round(a.oltre10);
    function scrivi(fase, n){ b.textContent = num(n); sp.textContent = fase; }
    if(ridotto){ colora(n5, n10); scrivi(a.testo_tutto, n5); return; }
    scrivi(a.testo_tutto, 0);
    var k = 0;
    // 1) si accendono uno alla volta i passaggi oltre 5 minuti, poi i più gravi diventano scuri
    (function accendi(){
      if(k > n5){ dopo(500, el, function(){ var j = 0; (function scuri(){ if(j > n10){ dopo(2200, el, function(){ giorno(0); }); return; } colora(n5, j); j++; dopo(160, el, scuri); })(); }); return; }
      colora(k, 0); scrivi(a.testo_tutto, k); k++; dopo(110, el, accendi);
    })();
    // 2) il giorno: ogni fascia oraria col suo numero (solo oltre 5 minuti), poi di nuovo tutto il giorno
    function giorno(i){
      var f = a.fasi || [];
      if(!f.length) return;
      if(i >= f.length){ colora(n5, n10); scrivi(a.testo_tutto, n5); dopo(3500, el, function(){ giorno(0); }); return; }
      var n = Math.round(f[i].valore);
      colora(n, 0); scrivi(f[i].label, n);
      dopo(2300, el, function(){ giorno(i + 1); });
    }
  }

  /* ---------------- parcheggi: Torino con le fermate importanti che si colorano, poi i punti prioritari ---------------- */
  function fermate(el, a){
    var c = a.contorno, pts = a.punti || [], prio = a.prioritari || [], vb = c.vb, u = vb[2] / 1000;   // u = unità di disegno
    var punti = pts.map(function(p, i){ return '<circle class="f' + p[2] + '" cx="' + p[0] + '" cy="' + p[1] + '" r="' + (13 * u).toFixed(1) + '" data-i="' + i + '"/>'; }).join("");
    var anelli = prio.map(function(p){ return '<circle class="an-prio" cx="' + p[0] + '" cy="' + p[1] + '" r="' + (34 * u).toFixed(1) + '" style="stroke-width:' + (5 * u).toFixed(1) + '"/>'; }).join("");
    var leg = (a.legenda || []).map(function(l, i){ return '<span><i class="tono-' + esc(l.tono) + '"></i>' + esc(l.label) + ': <b data-n="' + l.n + '">' + num(l.n) + '</b></span>'; }).join("");
    el.innerHTML = '<svg viewBox="' + vb.join(" ") + '" role="img" aria-label="' + esc(a.didascalia) + '" style="max-width:' + (el.classList.contains("compatto") ? 230 : 420) + 'px;margin:0 auto">'
      + '<path class="an-contorno" d="' + esc(c.d) + '" style="stroke-width:' + (4 * u).toFixed(1) + '"/>' + '<g class="an-punti">' + punti + '</g><g class="an-anelli">' + anelli + '</g></svg>'
      + '<div class="an-legenda">' + leg + '</div>' + (a.didascalia && !el.classList.contains("compatto") ? '<p class="didascalia">' + esc(a.didascalia) + '</p>' : "");
    if(ridotto) return;
    var cc = el.querySelectorAll(".an-punti circle"), aa = el.querySelectorAll(".an-anelli circle"), bb = el.querySelectorAll(".an-legenda b");
    // le fermate compaiono dal centro verso fuori (ordine dato dai dati), i conteggi della legenda salgono insieme
    var ordine = Array.prototype.slice.call(cc).sort(function(x, y){ return pts[+x.getAttribute("data-i")][3] - pts[+y.getAttribute("data-i")][3]; });
    Array.prototype.forEach.call(cc, function(x){ x.style.opacity = 0; });
    Array.prototype.forEach.call(aa, function(x){ x.style.opacity = 0; });
    var cont = [0, 0, 0];
    function giro(){
      cont = [0, 0, 0]; Array.prototype.forEach.call(bb, function(b){ b.textContent = num(0); });
      Array.prototype.forEach.call(cc, function(x){ x.style.transition = "none"; x.style.opacity = 0; });
      Array.prototype.forEach.call(aa, function(x){ x.style.transition = "none"; x.style.opacity = 0; });
      var shown = 0;
      scorri(el, 0, ordine.length, 3200, function(v){
        var fino = Math.floor(v);
        for(; shown < fino; shown++){
          var x = ordine[shown]; x.style.transition = "opacity .3s"; x.style.opacity = 1;
          var k = pts[+x.getAttribute("data-i")][2]; cont[k]++; if(bb[k]) bb[k].textContent = num(cont[k]);
        }
      }, function(){
        Array.prototype.forEach.call(bb, function(b){ b.textContent = num(+b.getAttribute("data-n")); });
        Array.prototype.forEach.call(aa, function(x, i){ dopo(500 + i * 120, el, function(){ x.style.transition = "opacity .6s"; x.style.opacity = 1; }); });
        dopo(9000, el, giro);
      });
    }
    giro();
  }

  /* ---------------- 1 su N: gli omini compaiono uno alla volta, poi si accendono ---------------- */
  var OMINO = '<svg viewBox="0 0 24 48" aria-hidden="true"><circle cx="12" cy="7" r="6"/><path d="M5 17h14a3 3 0 0 1 3 3v14h-4v14h-5V34h-2v14H6V34H2V20a3 3 0 0 1 3-3z"/></svg>';
  function omini(el, a){
    var tot = Math.max(1, a.totale || 10), n = Math.max(0, Math.round(a.colorati || 0));
    el.innerHTML = '<div class="an-omini" role="img" aria-label="' + esc(a.didascalia) + '">' + new Array(tot + 1).join(OMINO) + '</div>'
      + (a.didascalia && !el.classList.contains("compatto") ? '<p class="didascalia">' + esc(a.didascalia) + '</p>' : "");
    var os = el.querySelectorAll(".an-omini svg");
    if(ridotto){ for(var i = 0; i < n; i++) os[i].classList.add("acceso"); return; }
    Array.prototype.forEach.call(os, function(o){ o.classList.add("nascosto"); });
    Array.prototype.forEach.call(os, function(o, i){ dopo(200 + i * 160, el, function(){ o.classList.remove("nascosto"); }); });
    dopo(200 + tot * 160 + 600, el, function(){ for(var i = 0; i < n; i++) os[i].classList.add("acceso"); });
  }

  /* ---------------- costi: due contatori in euro che salgono insieme, mese per mese; poi ricomincia ---------------- */
  function contatori(el, a){
    var righe = a.righe || [], mesi = Math.max(1, a.mesi || 12), max = 1;
    righe.forEach(function(r){ max = Math.max(max, r.mese * mesi); });
    el.innerHTML = '<div role="img" aria-label="' + esc(a.didascalia) + '"><p class="an-fascia"><b class="an-m">0</b><span>' + esc(a.etichetta || "") + '</span></p>'
      + righe.map(function(r){ return '<div class="an-cr"><span class="an-testo">' + esc(r.label) + '</span><span class="an-traccia"><i class="t-' + esc(r.tono || "") + '"></i></span><b class="an-eur"></b></div>'; }).join("")
      + '</div>' + (a.didascalia && !el.classList.contains("compatto") ? '<p class="didascalia">' + esc(a.didascalia) + '</p>' : "");
    var barre = el.querySelectorAll(".an-traccia i"), euro = el.querySelectorAll(".an-eur"), m = el.querySelector(".an-m");
    function disegna(v){
      m.textContent = Math.round(v);
      righe.forEach(function(r, i){ var e = r.mese * v; barre[i].style.width = (e / max * 100) + "%"; euro[i].textContent = "€ " + num(e); });
    }
    if(ridotto){ disegna(mesi); return; }
    (function ciclo(){ scorri(el, 0, mesi, 5200, disegna, function(){ dopo(3200, el, ciclo); }); })();
  }

  function gara(el, a, compatto){
    el.innerHTML = window.Gara ? Gara.html({luoghi: a.luoghi, scelto: a.scelto || 0, compatto: compatto, mini: compatto, giro: true}) : "";
    if(a.didascalia && !compatto) el.insertAdjacentHTML("beforeend", '<p class="didascalia">' + esc(a.didascalia) + '</p>');
  }

  /* area che si espande (assets/area.js): grande nella scheda, piccola e senza comandi nella home */
  function area(el, a){
    var compatto = el.classList.contains("compatto");
    el.innerHTML = (window.Area ? Area.html({compatto: compatto}) : "") + (a.didascalia && !compatto ? '<p class="didascalia">' + esc(a.didascalia) + '</p>' : "");
  }

  var TIPI = {cerchi: cerchi, quadratini: quadratini, fermate: fermate, omini: omini, area: area, contatori: contatori};

  function html(a, opz){
    if(!a || !a.tipo) return "";
    var compatto = !!(opz && opz.compatto);
    return '<div class="anima' + (compatto ? " compatto" : "") + '" data-anima="' + esc(JSON.stringify(a)) + '"></div>';
  }
  function avvia(el){
    if(el._pronto) return; el._pronto = true;
    var a; try { a = JSON.parse(el.getAttribute("data-anima")); } catch(e){ return; }
    stile();
    if(a.tipo === "gara"){ gara(el, a, el.classList.contains("compatto")); return; }
    var fn = TIPI[a.tipo]; if(!fn) return;
    // si disegna subito (figura ferma) e l'animazione parte quando la figura si vede
    if(ridotto || !("IntersectionObserver" in window)){ fn(el, a); return; }
    var io = new IntersectionObserver(function(voci){
      voci.forEach(function(v){ if(v.isIntersecting){ io.disconnect(); ferma(el); fn(el, a); } });
    }, {threshold: .35});
    el.style.minHeight = "40px";
    io.observe(el);
  }
  function scansiona(r){
    if(!r.querySelectorAll) return;
    if(r.matches && r.matches("[data-anima]")) avvia(r);
    r.querySelectorAll("[data-anima]").forEach(avvia);
  }
  function avviaTutto(){
    scansiona(document);
    new MutationObserver(function(m){ m.forEach(function(x){ x.addedNodes.forEach(function(nd){ if(nd.nodeType === 1) scansiona(nd); }); }); })
      .observe(document.body, {childList: true, subtree: true});
  }
  if(document.body) avviaTutto(); else document.addEventListener("DOMContentLoaded", avviaTutto);
  window.Anima = {html: html};
})();
