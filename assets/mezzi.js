/* Home: i mezzi di Torino in movimento, in un'ora tipica (feriale, 7:30-8:30), con i dati veri del GPS raccolti dal progetto.
   Dati: window.HOME_MEZZI (data/home_mezzi.js, scritto da scripts/schede_risultati.py): contorno di Torino, posizioni dei mezzi ogni 30 secondi, contatore.
   L'ora reale (i minuti con dati, di solito circa 60) scorre in circa 20 secondi e poi ricomincia. Si ferma se la scheda del browser non si vede o se il riquadro e' fuori schermo;
   al massimo 30 fotogrammi al secondo. Con «riduci movimento»: un fotogramma fermo. Senza i dati la pagina resta valida (solo il testo). */
(function(){
  "use strict";
  var DURATA_S = 20, FPS_MAX = 30, SCIA_PASSI = 3;
  var COLORI = ["#8fb0ea", "#e3bf55", "#32cfc2"];   // bus, tram, metro (sul fondo scuro dell'eroe)
  var H = window.HOME_MEZZI, canvas = document.getElementById("cMezzi"), eroe = document.getElementById("eroe");
  var ridotto = !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);

  /* ---- contatore sotto il titolo: i numeri vengono dai dati, qui solo la frase */
  function fraseContatore(){
    var el = document.getElementById("contatore"); if(!el) return;
    var c = H && H.contatore; if(!c){ el.hidden = true; return; }
    var lg = window.Sito ? Sito.lingua() : "it";
    // frase con la data di inizio della raccolta (dal contatore dei dati): la stessa dell'eroe di §5.2 del piano
    if(!c.inizio_raccolta){ el.hidden = true; return; }
    var d = new Date(c.inizio_raccolta + "T12:00:00"), data = d.toLocaleDateString(lg === "en" ? "en-GB" : lg === "de" ? "de-DE" : "it-IT", {day: "numeric", month: "long", year: "numeric"});
    el.textContent = lg === "en" ? "Since " + data + " the project has collected open data on Turin's buses, trams and traffic every minute."
                   : lg === "de" ? "Seit dem " + data + " erfasst das Projekt jede Minute offene Daten zu Bussen, Straßenbahnen und Verkehr in Turin."
                   : "Dal " + data + " il progetto raccoglie ogni minuto i dati aperti di bus, tram e traffico di Torino.";
    el.hidden = false;
    if(window.Sito && Sito.osserva) Sito.osserva(el);
  }
  fraseContatore();
  window.addEventListener("lingua", fraseContatore);

  if(!H || !H.ora_tipica || !H.contorno || !canvas || !canvas.getContext){ if(eroe) eroe.classList.add("senza-mezzi"); return; }

  /* ---- decodifica: per ogni mezzo, posizioni (x, y) nel disegno del contorno, un passo ogni 30 secondi */
  var C = H.contorno, OT = H.ora_tipica, DA = OT.da || 0, A = (OT.a != null ? OT.a : OT.passi - 1);   // passi con dati: fuori da DA..A il GPS non ha posizioni
  var tracciati = OT.mezzi.map(function(m){
    var p = m[2], n = p.length / 2, xs = new Float32Array(n), ys = new Float32Array(n), lat = p[0], lon = p[1];
    for(var i = 0; i < n; i++){
      if(i > 0){ lat += p[2 * i]; lon += p[2 * i + 1]; }
      xs[i] = (lon / 1e5 - C.lon_min) * C.k * C.scala;
      ys[i] = (C.lat_max - lat / 1e5) * C.scala;
    }
    return {modo: m[0], t: m[1], n: n, x: xs, y: ys};
  });
  var contorno = new Path2D(C.d);
  var orologio = document.getElementById("orologio");
  var ctx = canvas.getContext("2d"), W = 0, Hh = 0, dpr = 1, sc = 1, ox = 0, oy = 0;

  function misura(){
    var r = eroe.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2); W = Math.max(1, Math.round(r.width)); Hh = Math.max(1, Math.round(r.height));
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(Hh * dpr);
    sc = Math.min(Hh * 0.9 / C.altezza, W * 0.95 / C.larghezza);
    var largo = W > 760;   // computer: la città a destra, il testo a sinistra; telefono: la città dietro il testo
    ox = largo ? W - C.larghezza * sc - Math.max(16, (W - 1040) / 2 + 16) : (W - C.larghezza * sc) / 2;
    oy = (Hh - C.altezza * sc) / 2;
  }

  /* posizione del mezzo a un passo qualsiasi (anche frazionario): null se in quel momento non e' in servizio */
  function posizione(t, s, out){
    var i = s - t.t; if(i < 0 || i > t.n - 1) return false;
    var a = Math.floor(i), f = i - a, b = Math.min(t.n - 1, a + 1);
    out[0] = t.x[a] + f * (t.x[b] - t.x[a]); out[1] = t.y[a] + f * (t.y[b] - t.y[a]); return true;
  }

  var pa = [0, 0], pb = [0, 0];
  function disegna(s){
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, Hh);
    ctx.save(); ctx.translate(ox, oy); ctx.scale(sc, sc);
    ctx.fillStyle = "rgba(143,176,234,.09)"; ctx.fill(contorno);
    ctx.lineWidth = 1.6 / sc; ctx.strokeStyle = "rgba(227,191,85,.55)"; ctx.stroke(contorno);
    ctx.lineCap = "round";
    for(var m = 0; m < 3; m++){
      ctx.strokeStyle = COLORI[m]; ctx.fillStyle = COLORI[m];
      // scie corte: un tratto semitrasparente dagli ultimi passi alla posizione attuale
      ctx.globalAlpha = .38; ctx.lineWidth = 2.2 / sc; ctx.beginPath();
      for(var i = 0; i < tracciati.length; i++){
        var t = tracciati[i]; if(t.modo !== m || !posizione(t, s, pb)) continue;
        if(!posizione(t, Math.max(t.t, s - SCIA_PASSI), pa)) continue;
        ctx.moveTo(pa[0], pa[1]); ctx.lineTo(pb[0], pb[1]);
      }
      ctx.stroke();
      ctx.globalAlpha = .95; ctx.beginPath();
      var r = (m === 1 ? 3.2 : 2.6) / sc * Math.max(1, Math.min(1.8, sc * 1.1));
      for(i = 0; i < tracciati.length; i++){
        t = tracciati[i]; if(t.modo !== m || !posizione(t, s, pb)) continue;
        ctx.moveTo(pb[0] + r, pb[1]); ctx.arc(pb[0], pb[1], r, 0, 6.2832);
      }
      ctx.fill();
    }
    ctx.restore(); ctx.globalAlpha = 1;
    if(orologio){
      var h0 = OT.inizio.split(":"), min = parseInt(h0[0], 10) * 60 + parseInt(h0[1], 10) + Math.floor(s * OT.passo_s / 60);
      var txt = ("0" + Math.floor(min / 60)).slice(-2) + ":" + ("0" + (min % 60)).slice(-2);
      if(orologio.textContent !== txt) orologio.textContent = txt;
    }
  }

  /* ---- ciclo: 30 fotogrammi al secondo al massimo; fermo se la scheda non si vede o l'eroe e' fuori schermo */
  function passoDa(ms){ return DA + (ms / 1000 % DURATA_S) / DURATA_S * (A - DA); }
  var visibile = true, t0 = null, ultimo = 0, attivo = false;
  function passo(ts){
    attivo = false;
    if(document.hidden || !visibile || ridotto) return;
    if(t0 === null) t0 = ts;
    if(ts - ultimo >= 1000 / FPS_MAX - 1){
      ultimo = ts;
      disegna(passoDa(ts - t0));
    }
    attiva();
  }
  function attiva(){ if(!attivo && !ridotto){ attivo = true; requestAnimationFrame(passo); } }
  function ricomincia(){ t0 = null; attiva(); }

  misura();
  disegna(ridotto ? (DA + A) / 2 : DA);   // con «riduci movimento»: un fotogramma fermo (le 8 circa)
  window.addEventListener("resize", function(){ misura(); disegna(ridotto ? (DA + A) / 2 : passoDa(performance.now() - (t0 || 0))); });
  document.addEventListener("visibilitychange", function(){ if(!document.hidden) ricomincia(); });
  if(window.IntersectionObserver){
    new IntersectionObserver(function(e){ visibile = e[0].isIntersecting; if(visibile) ricomincia(); }).observe(eroe);
  }
  if(!ridotto) attiva();
})();
