/* Le quattro schede dei risultati: la finestra che si apre sopra la home (index.html#p1 … #p4) con numero, grafici, calcolo e limiti.
   I dati stanno in data/schede_risultati.js (scritto da scripts/schede_risultati.py); i grafici si disegnano qui. Schede.monta(lista) la attiva. */
(function(){
"use strict";
const $ = id => document.getElementById(id);
let schede = [];

const esc = Sito.esc, formattaNumero = Sito.formattaNumero, T = Sito.T;
const forma = Sito.forma;   // la forma nella lingua scelta
function conUnita(n, unita){ return formattaNumero(n) + (unita ? (unita === "%" ? "%" : " " + esc(unita)) : ""); }
function valoreGrande(n){ return formattaNumero(n.valore) + (n.unita === "%" ? "%" : ""); }
/* attributi per i numeri che salgono (assets/sito.js): un numero, oppure una forbice «21–28» */
function attrConta(n){
  if(typeof n.valore === "number") return ` data-valore="${n.valore}"`;
  const m = /^(\d+)\s*[–-]\s*(\d+)$/.exec(String(n.valore));
  return m ? ` data-forbice="${m[1]},${m[2]}"` : "";
}
function dopoGrande(n){ return n.unita && n.unita !== "%" ? esc(n.unita) + " " : ""; }

/* una scheda valida ha la «forma» (scripts/schede_risultati.py) */
function schedaValida(r){
  const f = r && r.forma;
  return !!(f && typeof f.titolo === "string" && f.numero && Array.isArray(f.punti));
}

/* numero mostrato in pagina (1-6); il numero interno (s.risultato) resta valido per i link #rN */
function numeroDi(s){ return s.numero_pubblico != null ? s.numero_pubblico : s.risultato; }

/* ---------------- grafici ---------------- */
// «verde»/«rosso» = bene/male; «giallo», «blu», «arancio» = categorie; senza tono = blu neutro
const TONO_COL = {verde:"var(--vr-verde)", rosso:"var(--vr-rosso)", giallo:"var(--vr-giallo)", blu:"var(--neu-blu)", arancio:"var(--neu-arancio)"};
const TONO_TESTO = {verde:"var(--su-verde)", rosso:"var(--su-rosso)", giallo:"var(--su-giallo)", blu:"var(--su-giallo)", arancio:"var(--su-giallo)"};
const PALETTE_PILA = ["var(--neu-blu)", "var(--neu-arancio)", "var(--pila-3)", "var(--pila-4)", "var(--pila-5)"];

/* testo del numero di una barra, e larghezza (in caratteri) della colonna dei numeri: la stessa in tutte le righe del grafico */
function testoValore(g, v){
  const sep = g.forbice ? " – " : " → ";
  return v.testo ? esc(v.testo)
    : (typeof v.prima === "number" ? conUnita(v.prima, g.unita === "%" ? "%" : "") + sep : "") + conUnita(v.valore, g.unita === "%" ? "%" : "");
}
function larghezzaValori(g, voci){
  return Math.max(3, ...voci.map(v => testoValore(g, v).replace(/&[a-z#0-9]+;/g, "x").length));
}
function graficoBarre(g){
  const voci = g.voci || [];
  const max = g.max || Math.max(1, ...voci.flatMap(v => [Math.abs(v.valore||0), Math.abs(v.prima||0)]));
  const larghezza = g.larghezza || larghezzaValori(g, voci);
  const righe = voci.map(v => {
    const pct = x => Math.max(1.5, Math.abs(x) / max * 100);
    const haPrima = typeof v.prima === "number";
    const val = testoValore(g, v);
    return `<div class="barra-riga" style="--cv:${Math.ceil(larghezza * 1.12)}ch">
      <span class="barra-etichetta" title="${esc(v.label)}">${v.link ? `<a href="${esc(v.link)}" class="barra-link">${esc(v.label)}</a>` : esc(v.label)}</span>
      <span class="barra-traccia">
        ${haPrima ? `<span style="width:${pct(v.prima)}%;background:var(--neu-blu-chiaro)"></span>` : ""}
        <span style="width:${pct(v.valore)}%;background:${TONO_COL[v.tono] || "var(--neu-blu)"}"></span>
        ${typeof g.soglia === "number" ? `<span class="soglia" style="left:${g.soglia / max * 100}%" title="${esc(g.soglia_label || "soglia")}"></span>` : ""}
      </span>
      <span class="barra-valore">${val}</span>
    </div>`;
  }).join("");
  const haTesto = voci.some(v => v.testo);
  const unita = g.unita && g.unita !== "%" && !haTesto ? `<div class="nota">${T("Valori in", "Values in", "Werte in")} ${esc(g.unita)}.</div>` : "";
  const legenda = Array.isArray(g.legenda) && g.legenda.length ? `<div class="legenda">${g.legenda.map(l => `<span><i style="background:${TONO_COL[l.tono] || "var(--neu-blu)"}"></i>${esc(l.label)}</span>`).join("")}</div>` : "";
  return righe + unita + legenda;
}

/* barre delle differenze: una riga per fascia, la barra va a destra (positiva) o a sinistra (negativa) dello zero;
   sotto la barra il valore e, scritto, il numero di zone che stanno dietro la differenza */
function graficoBarreDiff(g){
  const voci = g.voci || [];
  const max = g.max || Math.max(1, ...voci.map(v => Math.abs(v.valore || 0)));
  return voci.map(v => {
    const ok = typeof v.valore === "number";
    const w = ok ? Math.max(1.5, Math.abs(v.valore) / max * 50) : 0;
    const barra = ok ? `<span class="${v.valore >= 0 ? "pos" : "neg"}" style="width:${w}%"></span>` : "";
    const segno = ok && v.valore > 0 ? "+" : "";
    return `<div class="diff-riga"><span class="barra-etichetta">${esc(v.label)}</span><span class="diff-traccia" role="img" aria-label="${esc(v.label)}">${barra}</span>
      <span class="diff-testo">${ok ? segno + formattaNumero(v.valore) + (g.unita ? " " + esc(g.unita) : "") : T("non confrontabile", "not comparable", "nicht vergleichbar")} <small>${esc(v.testo || "")}</small></span></div>`;
  }).join("");
}

/* il numero grande disegnato: omini, quadratini o pallini (dalla scheda: f.unita) */
const OMINO = '<svg viewBox="0 0 24 48" class="omino{c}" aria-hidden="true"><circle cx="12" cy="7" r="6"/><path d="M5 17h14a3 3 0 0 1 3 3v14h-4v14h-5V34h-2v14H6V34H2V20a3 3 0 0 1 3-3z"/></svg>';
function unitaHtml(u){
  if(!u) return "";
  const n = Math.max(0, Math.round(u.colorati || 0)), tot = Math.max(1, u.totale || 10);
  let corpo = "";
  if(u.tipo === "omini") corpo = `<div class="riga-figure" role="img" aria-label="${esc(u.didascalia || "")}">${Array.from({length: tot}, (_, i) => OMINO.replace("{c}", i < n ? " acceso" : "")).join("")}</div>`;
  else if(u.tipo === "quadratini") corpo = `<div class="quadri" role="img" aria-label="${esc(u.didascalia || "")}">${Array.from({length: tot}, (_, i) => `<i class="${i < n ? "acceso" : ""}"></i>`).join("")}</div>`;
  else if(u.tipo === "pallini") corpo = `<div class="pallini" role="img" aria-label="${esc(u.didascalia || "")}">${(u.pallini || []).map(p => `<span><i class="tono-${esc(p.tono || "grigio")}"></i>${esc(p.label)}</span>`).join("")}</div>`;
  return `<div class="unita">${corpo}${u.didascalia ? `<p class="didascalia">${esc(u.didascalia)}</p>` : ""}</div>`;
}

/* barre a gruppi: un titolo per gruppo (es. fascia) e sotto le sue barre (es. le due stime), tutte sulla stessa scala */
function graficoBarreGruppi(g){
  const tutte = (g.gruppi || []).flatMap(gr => gr.voci || []);
  const tuttiValori = larghezzaValori(g, tutte);
  // L24 (G1): senza g.max la scala e' una sola per tutti i gruppi (il massimo di tutte le barre), cosi' lo stesso valore ha la stessa lunghezza ovunque
  const max = g.max || Math.max(1, ...tutte.flatMap(v => [Math.abs(v.valore || 0), Math.abs(v.prima || 0)]));
  return (g.gruppi || []).map(gr => `<div class="etichetta-gruppo">${esc(gr.label)}</div>` + graficoBarre({voci: gr.voci, unita: g.unita, max: max, larghezza: tuttiValori})).join("");
}

function graficoPila(g){
  const voci = g.voci || [];
  const tot = voci.reduce((a, v) => a + Math.max(0, v.valore || 0), 0) || 1;
  const col = (v, j) => TONO_COL[v.tono] || PALETTE_PILA[j % PALETTE_PILA.length];
  const pezzi = voci.map((v, j) => `<span style="width:${Math.max(0, v.valore) / tot * 100}%;background:${col(v, j)}" title="${esc(v.label)}"></span>`).join("");
  const leg = voci.map((v, j) => `<span><i style="background:${col(v, j)}"></i>${esc(v.label)}: <b>${conUnita(v.valore, g.unita === "%" ? "%" : g.unita)}</b></span>`).join("");
  return `<div class="pila" role="img" aria-label="${esc(g.titolo)}">${pezzi}</div><div class="legenda">${leg}</div>`;
}

/* barre a 100% impilate, una per riga (es. feriale, sabato, domenica); legenda dalla prima riga */
function graficoPila100(g){
  const righe = g.righe || [];
  const corpo = righe.map(r => {
    const tot = r.voci.reduce((a, v) => a + Math.max(0, v.valore || 0), 0) || 1;
    const pezzi = r.voci.map(v => {
      const w = Math.max(0, v.valore) / tot * 100;
      return `<span style="width:${w}%;background:${TONO_COL[v.tono] || "var(--neu-blu)"};color:${TONO_TESTO[v.tono] || "var(--ink)"}" title="${esc(v.label)}: ${conUnita(Math.round(v.valore), "%")}">${w >= 9 ? formattaNumero(Math.round(w)) + "%" : ""}</span>`;
    }).join("");
    // L24 (G5): i pezzi troppo piccoli per il numero scritto dentro lo hanno scritto accanto, con il nome
    const piccoli = r.voci.filter(v => Math.max(0, v.valore) / tot * 100 < 9 && v.valore > 0).map(v => `${esc(v.label)} ${conUnita(Math.round(v.valore), "%")}`);
    return `<div class="pila100-riga"><span class="barra-etichetta">${esc(r.label)}</span><div class="pila" role="img" aria-label="${esc(r.label)}">${pezzi}</div></div>`
      + (piccoli.length ? `<div class="pila-piccoli">${piccoli.join(" · ")}</div>` : "");
  }).join("");
  const leg = (righe[0] ? righe[0].voci : []).map(v => `<span><i style="background:${TONO_COL[v.tono] || "var(--neu-blu)"}"></i>${esc(v.label)}</span>`).join("");
  return corpo + `<div class="legenda">${leg}</div>`;
}

/* Telefono (sotto 560 px): il disegno prende la larghezza vera della colonna, cosi' i caratteri restano di 12 px e non si rimpiccioliscono col viewBox.
   Le etichette lunghe vanno su piu' righe (al massimo 3) o, se sono tante, si saltano. */
const stretto = () => window.innerWidth < 560;
const largDisegno = () => stretto() ? Math.max(280, Math.min(480, window.innerWidth - 104)) : 480;
function spezza(t, max){
  const r = [""];
  String(t).split(/\s+/).forEach(w => { const u = r[r.length - 1]; if(u && (u + " " + w).length > max && r.length < 3) r.push(w); else r[r.length - 1] = u ? u + " " + w : w; });
  return r;
}
function righeSvg(x, righe, fs){ return righe.map((r, k) => `<tspan x="${x}" dy="${k ? (fs * 1.15).toFixed(1) : 0}">${esc(r)}</tspan>`).join(""); }

/* linea su poche categorie (es. fasce orarie); asse da zero, valore scritto su ogni punto */
function graficoLinea(g){
  const st = stretto(), fs = st ? 12 : 10, fv = st ? 12.5 : 11, LW = largDisegno(), LH = st ? 230 : 190, PL = st ? 40 : 56, PR = st ? 22 : 56, PT = 24, PB = st ? 54 : 34, AW = LW - PL - PR, AH = LH - PT - PB;
  const cat = g.categorie || [], serie = g.serie || [];
  const max = Math.max(1, ...serie.flatMap(s => s.valori.filter(v => typeof v === "number")));
  // L24 (G7): asse da 0 al primo valore tondo sopra il massimo (passo 0,5; 1; 2; 5; 10; 20; 50), con 3-6 righe; il primo punto non tocca l'asse dei numeri
  const passoAsse = [0.5, 1, 2, 5, 10, 20, 50, 100].find(p => Math.ceil(max / p) <= 5) || 100;
  const tetto = Math.max(passoAsse, Math.ceil(max / passoAsse) * passoAsse);
  const X = i => PL + 14 + (cat.length > 1 ? i / (cat.length - 1) : .5) * (AW - 28), Y = v => PT + (1 - v / tetto) * AH;
  const valoriAsse = []; for(let v = 0; v <= tetto + 1e-9; v += passoAsse) valoriAsse.push(v);
  const guide = valoriAsse.map(v => `<line x1="${PL}" x2="${LW - PR}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" style="stroke:var(--line)"/>`
    + `<text x="${PL - 6}" y="${(Y(v) + 4).toFixed(1)}" text-anchor="end" font-size="${fs}" style="fill:var(--muted)">${formattaNumero(v)}${g.unita === "%" ? "%" : ""}</text>`).join("");
  // le etichette non escono dal disegno (centro a mezza larghezza stimata dal bordo); su telefono vanno su due o tre righe e, se sono tante, se ne salta qualcuna
  const larghCar = fs * 0.56, righeCat = cat.map(c => spezza(c, st ? 11 : 99)), maxCar = Math.max(1, ...righeCat.map(r => Math.max(...r.map(x => x.length))));
  const salto = Math.max(1, Math.ceil(maxCar * larghCar * 1.15 / (cat.length > 1 ? (AW - 28) / (cat.length - 1) : AW)));
  const nomi = cat.map((c, i) => {
    if(i % salto) return "";
    const rr = righeCat[i], mezza = Math.max(...rr.map(x => x.length)) * larghCar / 2, x = Math.min(LW - 3 - mezza, Math.max(3 + mezza, X(i))).toFixed(1);
    return `<text x="${x}" y="${PT + AH + 8 + fs}" text-anchor="middle" font-size="${fs}" style="fill:var(--muted)">${righeSvg(x, rr, fs)}</text>`;
  }).join("");
  const linee = serie.map(s => {
    const pts = s.valori.map((v, i) => `${X(i).toFixed(1)},${Y(v).toFixed(1)}`);
    const punti = s.valori.map((v, i) => `<circle cx="${X(i).toFixed(1)}" cy="${Y(v).toFixed(1)}" r="3.5" style="fill:var(--accent)"/>`
      + `<text x="${X(i).toFixed(1)}" y="${(Y(v) - 8).toFixed(1)}" text-anchor="middle" font-size="${fv}" font-weight="700" style="fill:var(--ink)">${formattaNumero(v)}${g.unita === "%" ? "%" : ""}</text>`).join("");
    return `<polyline points="${pts.join(" ")}" fill="none" style="stroke:var(--accent)" stroke-width="2.2" stroke-linejoin="round"/>${punti}`;
  }).join("");
  return `<svg viewBox="0 0 ${LW} ${LH}" role="img" aria-label="${esc(g.titolo)}">${guide}${nomi}${linee}</svg>`;
}

/* dispersione: un punto per coppia (x, y, grandezza); linea di riferimento y = linea * x (es. «il doppio») */
function graficoDispersione(g){
  const st = stretto(), fs = st ? 12 : 10, fv = st ? 12 : 11, LW = largDisegno(), LH = st ? 310 : 250, PL = st ? 70 : 44, PR = 14, PT = 12, PB = st ? 76 : 44, AW = LW - PL - PR, AH = LH - PT - PB;
  const pts = g.punti || [];
  const passo = v => v <= 60 ? 10 : v <= 150 ? 20 : 30;
  const pX = g.passo_x || passo(60), pY = g.passo_y || passo(ymaxGrezzo(pts));   // passi degli assi: di solito automatici, a mano se servono
  const xmax = Math.ceil(Math.max(10, ...pts.map(p => p[0])) / pX) * pX;
  const ymax = Math.ceil(Math.max(10, ...pts.map(p => p[1])) / pY) * pY;
  const X = v => PL + v / xmax * AW, Y = v => PT + (1 - v / ymax) * AH;
  const maxAuto = Math.max(1, ...pts.map(p => p[2]));
  const tx = [], ty = [];
  for(let v = 0; v <= xmax; v += pX) tx.push(v);
  for(let v = 0; v <= ymax; v += pY) ty.push(v);
  const griglia = tx.map(v => `<line x1="${X(v).toFixed(1)}" x2="${X(v).toFixed(1)}" y1="${PT}" y2="${PT + AH}" style="stroke:var(--line)"/><text x="${X(v).toFixed(1)}" y="${PT + AH + 14}" text-anchor="middle" font-size="${fs}" style="fill:var(--muted)">${formattaNumero(v)}</text>`).join("")
    + ty.map(v => `<line x1="${PL}" x2="${PL + AW}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" style="stroke:var(--line)"/><text x="${PL - 6}" y="${(Y(v) + 3.5).toFixed(1)}" text-anchor="end" font-size="${fs}" style="fill:var(--muted)">${formattaNumero(v)}</text>`).join("");
  const linee = g.linee || (g.retta ? [] : [{k: g.linea || 2, label: g.linea_label || ""}]);
  // retta di tendenza y = a + b*x (es. prezzo contro servizi), tagliata dentro il grafico
  const retta = (() => {
    const r = g.retta; if(!r) return "";
    let x0 = 0, x1 = xmax;
    if(r.b !== 0){   // L24 (G6): la parte della retta con y fra 0 e ymax e x fra 0 e xmax, per pendenza positiva o negativa
      const xa = (0 - r.a) / r.b, xb = (ymax - r.a) / r.b;
      x0 = Math.max(0, Math.min(xa, xb)); x1 = Math.min(xmax, Math.max(xa, xb));
    }
    const y0 = r.a + r.b * x0, y1 = r.a + r.b * x1;
    return `<line x1="${X(x0).toFixed(1)}" y1="${Y(y0).toFixed(1)}" x2="${X(x1).toFixed(1)}" y2="${Y(y1).toFixed(1)}" style="stroke:var(--accent)" stroke-width="2.2"/>`
      + `<text x="${(X(x1) - 6).toFixed(1)}" y="${(Y(y1) + 14).toFixed(1)}" text-anchor="end" font-size="${fv}" font-weight="700" style="fill:var(--accent)">${esc(r.label || "")}</text>`;
  })();
  const linea = linee.map(l => {
    const xf = Math.min(xmax, ymax / l.k);
    return `<line x1="${X(0)}" y1="${Y(0)}" x2="${X(xf).toFixed(1)}" y2="${Y(l.k * xf).toFixed(1)}" style="stroke:var(--vr-rosso)" stroke-width="2" stroke-dasharray="6 4"/>`
      + `<text x="${(X(xf) - 6).toFixed(1)}" y="${(Y(l.k * xf) + 14).toFixed(1)}" text-anchor="end" font-size="${fv}" font-weight="700" style="fill:var(--vr-rosso)">${esc(l.label)}</text>`;
  }).join("");
  const punti = pts.map(p => `<circle cx="${X(p[0]).toFixed(1)}" cy="${Y(p[1]).toFixed(1)}" r="${(2 + 6 * Math.sqrt(p[2] / maxAuto)).toFixed(1)}" style="fill:var(--neu-blu);fill-opacity:.45;stroke:var(--neu-blu)" stroke-width=".6"><title>${p.length > 3 ? esc(p[3]) + ": " + formattaNumero(Math.round(p[2])) + " " + esc(g.dnome || "abitanti") + ", " + esc(g.xnome || "x") + " " + formattaNumero(Math.round(p[0])) + ", " + esc(g.ynome || "y") + " " + formattaNumero(Math.round(p[1])) : formattaNumero(Math.round(p[2])) + T(" auto: ", " cars: ", " Autos: ") + formattaNumero(Math.round(p[0])) + T(" min in auto, ", " min by car, ", " Min. mit dem Auto, ") + formattaNumero(Math.round(p[1])) + T(" min coi mezzi", " min by public transport", " Min. mit öffentlichen Verkehrsmitteln")}</title></circle>`).join("");
  const maxX = st ? Math.floor(AW / (fs * 0.56)) : 999, maxY = st ? Math.floor(AH / (fs * 0.56)) : 999;
  const rx = spezza(g.xlabel || "", maxX), ry = spezza(g.ylabel || "", maxY).slice(0, st ? 2 : 3);
  const assi = `<text x="${PL + AW / 2}" y="${PT + AH + 14 + fs + 10}" text-anchor="middle" font-size="${fv}" style="fill:var(--muted)">${righeSvg(PL + AW / 2, rx, fv)}</text>`
    + `<text transform="translate(${fv} ${PT + AH / 2}) rotate(-90)" text-anchor="middle" font-size="${fv}" style="fill:var(--muted)">${righeSvg(0, ry, fv)}</text>`;
  return `<svg viewBox="0 0 ${LW} ${LH}" role="img" aria-label="${esc(g.titolo)}">${griglia}${linea}${retta}${punti}${assi}</svg>`;
}
function ymaxGrezzo(pts){ return Math.max(10, ...pts.map(p => p[1])); }

function grafico(g){
  const corpo = g.tipo === "gara" ? (window.Gara ? Gara.html({luoghi: g.luoghi, scelto: g.scelto, giro: true}) : "") : g.tipo === "area" ? (window.Area ? Area.html() : "") : g.tipo === "pila100" ? graficoPila100(g) : g.tipo === "linea" ? graficoLinea(g) : g.tipo === "dispersione" ? graficoDispersione(g) : g.tipo === "barre_diff" ? graficoBarreDiff(g) : g.tipo === "barre_gruppi" ? graficoBarreGruppi(g) : g.tipo === "pila" ? graficoPila(g) : graficoBarre(g);
  return `<div class="grafico"><h5>${esc(g.titolo)}</h5>${corpo}${g.nota ? `<div class="nota">${esc(g.nota)}</div>` : ""}</div>`;
}

/* ---------------- scheda ---------------- */
function elenco(arr, tag){ return Array.isArray(arr) && arr.length ? `<${tag}>${arr.map(x => `<li>${esc(x)}</li>`).join("")}</${tag}>` : ""; }
function parte(titolo, html){ return html ? `<details class="parte"><summary>${titolo}</summary>${html}</details>` : ""; }

let corrente = -1;
function apri(i){
  corrente = i;
  const s = schede[i], f = forma(s);
  $("finMeta").textContent = `${Sito.etichetta(numeroDi(s))}`;
  $("finTitolo").textContent = f.titolo;
  const mappa = `<div class="azioni">${f.mappa
    ? `<a class="btn primario" href="mappa_torino.html#tema=${encodeURIComponent(f.mappa.id)}${f.mappa.vista ? "&vista=" + encodeURIComponent(f.mappa.vista) : ""}">${T("Vedi sulla mappa", "See on the map", "Auf der Karte ansehen")}</a>` : ""}</div>`;
  const criteri = Array.isArray(f.criteri) && f.criteri.length
    ? `<div class="sottotitolo">${T("I criteri", "The criteria", "Die Kriterien")}</div><table class="param">${f.criteri.map(c => `<tr><td>${esc(c[0])}</td><td>${esc(c[1])}</td></tr>`).join("")}</table>` : "";
  const confronto = Array.isArray(f.confronto) && f.confronto.length
    ? `<div class="sottotitolo">${T("Confronto con GTT", "Comparison with GTT", "Vergleich mit GTT")}</div>${elenco(f.confronto, "ul")}` : "";
  // tutti gli altri grafici sono aperti (Leo, 23/10); resta chiusa solo la parte «come è stato calcolato, e limiti»
  const extra = f.extra
    ? `<div class="sottotitolo">${esc(f.extra.titolo)}</div><p>${esc(f.extra.punto)}</p>${grafico(f.extra.grafico)}` : "";
  const altri = (f.altri || []).length || f.area ? `<div class="sottotitolo">${T("Altri grafici", "More charts", "Weitere Grafiken")}</div>${(f.area ? [f.area] : []).concat(f.altri || []).map(grafico).join("")}` : "";
  const figura = f.anima && window.Anima ? Anima.html(f.anima) : unitaHtml(f.unita);
  $("finCorpo").innerHTML =
    `<p class="domanda">${esc(f.domanda)}</p>` +
    `<div class="grande"><span class="val"${attrConta(f.numero)}>${valoreGrande(f.numero)}</span><span class="txt">${dopoGrande(f.numero)}${esc(f.numero.testo)}</span></div>` +
    figura +
    elenco(f.punti, "ul").replace("<ul>", '<ul class="punti">') +
    grafico(f.principale) + mappa +
    altri + extra +
    parte(T("Come è stato calcolato, e limiti", "How it was calculated, and limits", "Wie es berechnet wurde, und Grenzen"),
          (f.tipo_dato ? `<p>${esc(f.tipo_dato)}</p>` : "") + elenco(f.calcolo, "ol") + confronto + criteri + `<div class="sottotitolo">${T("Limiti", "Limits", "Grenzen")}</div>` + elenco(f.limiti, "ul") + (f.fonti && f.fonti.length ? `<p class="fonti"><b>${T("Fonti", "Sources", "Quellen")}:</b> ${f.fonti.map(esc).join("; ")}.</p>` : ""));
  const d = $("finestra");
  if(!d.open) d.showModal();
  d.scrollTop = 0;
  Sito.osserva($("finCorpo"));
}

/* ---------------- apertura e chiusura ---------------- */
/* L'indirizzo è index.html#p1 … #p4 (anche con ?lang=; #r4 = numero interno, vale ancora). Aprire una scheda dal clic aggiunge una voce alla cronologia:
   il tasto indietro la chiude. Se la pagina si apre già con #pN, chiudere toglie solo il #pN. */
let aggiunta = false;
function indice(){
  const m = /^#([rp])(\d+)$/.exec(location.hash);
  return m ? schede.findIndex(s => m[1] === "r" ? s.risultato === m[2] : String(numeroDi(s)) === m[2]) : -1;
}
function dall_indirizzo(){
  const k = indice();
  if(k >= 0) apri(k);
  else if($("finestra").open) $("finestra").close();
}
function chiudi(){
  $("finestra").close();   // l'evento «close» sistema l'indirizzo
}
function dopoChiusura(){
  if(!/^#[rp]\d+$/.test(location.hash)) return;
  if(aggiunta){ aggiunta = false; history.back(); }
  else { try { history.replaceState(null, "", location.pathname + location.search); } catch(e){} }
}
/* link «#pN» nella pagina: apre la scheda e aggiunge la voce alla cronologia */
function apriLink(e){
  const a = e.target.closest && e.target.closest('a[href^="#p"], a[href^="#r"]');
  if(!a) return;
  e.preventDefault();
  if(a.getAttribute("href") !== location.hash){ aggiunta = true; location.hash = a.getAttribute("href"); }
}
function monta(lista){
  schede = lista.filter(schedaValida).sort((a, b) => (parseFloat(numeroDi(a)) || 99) - (parseFloat(numeroDi(b)) || 99));
  $("finChiudi").addEventListener("click", chiudi);
  $("finestra").addEventListener("click", e => { if(e.target === e.currentTarget) chiudi(); });
  $("finestra").addEventListener("close", dopoChiusura);
  document.addEventListener("click", apriLink);
  window.addEventListener("hashchange", dall_indirizzo);
  // cambio di lingua: se la scheda è aperta, si ridisegna
  window.addEventListener("lingua", () => { if($("finestra").open && corrente >= 0) apri(corrente); });
  dall_indirizzo();
}
window.Schede = {monta: monta, elenco: () => schede, numeroDi: numeroDi};
})();
