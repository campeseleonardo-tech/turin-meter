#!/usr/bin/env python3
"""
prova_pagine.py  -  Prova automatica a runtime delle pagine (mappa, ingresso, schede).

Cosa fa
-------
  1. Avvia un piccolo server locale (python -m http.server) dalla cartella del progetto.
  2. Apre ogni pagina in un browser headless e cerca errori JavaScript (Uncaught, ReferenceError, TypeError,
     SyntaxError, Failed to execute) e richieste fallite. Pagine: ogni tema della mappa (letti dal template),
     le viste dei parcheggi, l'ingresso, le schede dei risultati.
  3. Controlla nel DOM che il pannello di errore (#jsoff) non sia visibile e che la legenda della vista mostri
     il titolo atteso.
  4. (Con Playwright e Pillow) rifà le anteprime 1200x630 dei risultati
     in assets/anteprime/rN.jpg (per le pagine r/N.html, link condivisi sui social) e le 3 immagini del README in assets/readme/.
     Fa gli screenshot di ingresso, risultati e mappa (e delle viste dei parcheggi) a 1440x900 e 390x844
     in immagini/ (cartella fuori da git).
  5. Controllo statico: cerca identificatori r6... / R6... usati nel template ma non definiti.

Browser
-------
  Su Windows usa Edge o Chrome già installati. Se non ci sono (o su Linux/Mac), usa Playwright:
  pip install playwright (il browser lo trova in PLAYWRIGHT_BROWSERS_PATH, oppure: python -m playwright install chromium).
  --playwright forza Playwright anche su Windows.

File di data/ mancanti
----------------------
  Senza la cartella data/ (per esempio nel cloud o in un clone nuovo) le pagine non trovano i loro dati: i file
  mancanti di data/ si elencano come «file assente» e NON sono errori. Gli errori veri (JavaScript, altri file
  mancanti) fanno uscire con codice 1. La lista dei file attesi e se sono in git la dà lo script 86.

Come si lancia
--------------
  python scripts/prova_pagine.py
  python scripts/prova_pagine.py --cartella CARTELLA --senza-screenshot
  Codice di uscita 0 = nessun errore; 1 = errori trovati.

Non modifica nessun dato: scrive solo gli screenshot in immagini/.
"""
import glob
import shutil
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RADICE = AQUI.parent
sys.path.insert(0, str(AQUI))
PORTA = 8799
from comuni import NOME_SITO, SITO_URL  # noqa: E402
BROWSER_WINDOWS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
TEMPLATE = RADICE / "scripts" / "mappa_template.html"
IMMAGINI = RADICE / "immagini"
PAROLE_ERRORE = ("Uncaught", "ReferenceError", "TypeError", "SyntaxError", "Failed to execute", "ERROR:CONSOLE")
TITOLI_VISTA = {
    "parcheggi": "Dove ci sono parcheggi per lasciare l'auto?",
    "mancano": "Dove servirebbe di più un parcheggio?",
}
DESKTOP, TELEFONO = (1440, 900), (390, 844)


def pagine_da_provare():
    """Le viste del Risultato 6, ogni altro tema della mappa (id letti dal template), l'ingresso e le schede."""
    temi = re.findall(r'\{id:"([a-z_0-9]+)", label:', TEMPLATE.read_text(encoding="utf-8"))
    out = [(f"mappa {v}", f"mappa_torino.html#tema=interscambio&vista={v}") for v in TITOLI_VISTA]
    out += [(f"mappa tema {t}", f"mappa_torino.html#tema={t}") for t in dict.fromkeys(temi) if t != "interscambio"]
    out.append(("ingresso", "index.html"))
    out.append(("progetto", "progetto.html"))
    out.append(("404", "404.html"))
    out += [(f"scheda R{n}", f"index.html#r{n}") for n in (4, 6, 8, 10)]
    return out


def pagine_screenshot():
    """(nome del file, pagina): ingresso, progetto, mappa e le due viste dei parcheggi."""
    return [("ingresso", "index.html"), ("progetto", "progetto.html"), ("mappa", "mappa_torino.html"),
            ("mappa_parcheggi", "mappa_torino.html#tema=interscambio&vista=parcheggi"),
            ("mappa_mancano", "mappa_torino.html#tema=interscambio&vista=mancano")]


class Silenzioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")   # il browser non deve riusare script vecchi (Edge tiene il profilo fra una prova e l'altra)
        super().end_headers()


def avvia_server(cartella):
    os.chdir(cartella)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.request_queue_size = 128   # il browser apre molte connessioni insieme: con la coda di 5 qualcuna veniva rifiutata (ERR_CONNECTION_REFUSED)
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", PORTA), Silenzioso)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.5)
    return srv


def file_di_data(url):
    """'data/...' se l'indirizzo punta dentro data/ del server locale, altrimenti None."""
    m = re.search(rf"127\.0\.0\.1:{PORTA}/(data/[^\s?#\"')]*)", url)
    return m.group(1) if m else None


# ---------------------------------------------------------------- Edge / Chrome di Windows
class BrowserWindows:
    nome = "Edge/Chrome di Windows"

    def __init__(self, percorso):
        self.percorso = percorso

    def chiudi(self):
        pass

    def esegui(self, url, extra, tag, w, h):
        """Edge/Chrome headless lanciato con PowerShell e -Wait: da Python il browser esce subito senza scrivere nulla."""
        cartella = Path(tempfile.gettempdir()) / "prova_pagine"
        cartella.mkdir(exist_ok=True)
        shutil.rmtree(cartella / ("profilo_" + tag), ignore_errors=True)   # profilo nuovo a ogni apertura: niente cache di file vecchi
        out, err = cartella / f"{tag}_out.txt", cartella / f"{tag}_err.txt"
        args = ["--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={cartella / ('profilo_' + tag)}",
                f"--window-size={w},{h}", "--enable-logging=stderr", "--v=0", "--virtual-time-budget=15000", *extra, url]
        arr = ",".join("'" + a.replace("'", "''") + "'" for a in args)
        ps = (f"$p = Start-Process -FilePath '{self.percorso}' -ArgumentList @({arr}) -Wait -PassThru "
              f"-RedirectStandardOutput '{out}' -RedirectStandardError '{err}' -WindowStyle Hidden; exit $p.ExitCode")
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], timeout=180, capture_output=True)
        except subprocess.TimeoutExpired:
            return "", "TIMEOUT"
        leggi = lambda f: f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""
        return leggi(out), leggi(err)

    def apri(self, url, tag, png=None, w=DESKTOP[0], h=DESKTOP[1]):
        """(dom, errori, file assenti)"""
        if png:
            self.esegui(url, [f"--screenshot={png}"], "shot_" + tag, w, h)
            return "", [], []
        dom, log = self.esegui(url, ["--dump-dom"], tag, w, h)
        errori, assenti = [], []
        for riga in log.splitlines():
            if not any(p in riga for p in PAROLE_ERRORE):
                continue
            if "Failed to load resource" in riga and "404" in riga and file_di_data(riga):
                assenti.append(file_di_data(riga))
            else:
                errori.append(riga.strip()[:300])
        if "TIMEOUT" in log:
            errori.append("il browser non ha risposto in tempo")
        return dom, errori, sorted(set(assenti))


# ---------------------------------------------------------------- Playwright
class BrowserPlaywright:
    nome = "Playwright (Chromium)"

    def __init__(self):
        from playwright.sync_api import sync_playwright   # pip install playwright
        self.pw = sync_playwright().start()
        try:
            self.br = self.pw.chromium.launch()
        except Exception:
            # il browser puo' stare in una cartella che Playwright non indovina (es. /opt/pw-browsers)
            base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
            cand = sorted(glob.glob(os.path.join(base, "chromium-*", "chrome-linux", "chrome")) + glob.glob(os.path.join(base, "chromium-*", "chrome-linux64", "chrome")))
            if not cand:
                self.pw.stop()
                raise
            self.br = self.pw.chromium.launch(executable_path=cand[-1])

    def chiudi(self):
        self.br.close()
        self.pw.stop()

    def apri(self, url, tag, png=None, w=DESKTOP[0], h=DESKTOP[1]):
        """(dom, errori, file assenti)"""
        ctx = self.br.new_context(viewport={"width": w, "height": h})
        page = ctx.new_page()
        errori, assenti = [], []

        def console(msg):
            if msg.type == "error" and "Failed to load resource" not in msg.text:
                errori.append(f"console: {msg.text[:300]}")

        def risposta(r):
            if r.status >= 400:
                d = file_di_data(r.url)
                (assenti.append(d) if d else errori.append(f"HTTP {r.status}: {r.url}"))

        page.on("console", console)
        page.on("pageerror", lambda e: errori.append(f"Uncaught {str(e)[:300]}"))
        page.on("response", risposta)
        page.on("requestfailed", lambda r: errori.append(f"richiesta fallita: {r.url[-90:]} ({r.failure})"))
        try:
            page.goto(url, wait_until="load", timeout=60000)
            page.wait_for_timeout(2500)   # i dati si caricano con script aggiunti dopo
            if png:
                page.screenshot(path=str(png))
            dom = page.content()
        except Exception as e:
            dom = ""
            errori.append(f"il browser non ha caricato la pagina: {str(e)[:200]}")
        ctx.close()
        return dom, errori, sorted(set(assenti))


def prova_cambio_indirizzo(br, cartella):
    """index.html: se cambia #p3 / #r6 senza ricaricare la pagina, la scheda giusta si apre; il clic su un riquadro apre la scheda e il tasto indietro la chiude.
    Solo con Playwright
    e con data/schede_risultati.js presente. Ritorna un elenco di errori."""
    if not isinstance(br, BrowserPlaywright) or not (cartella / "data" / "schede_risultati.js").exists():
        print("  cambio di indirizzo (#p3, #r6): non provato (serve Playwright e data/schede_risultati.js)")
        return []
    page = br.br.new_page()
    errori = []
    try:
        page.goto(f"http://127.0.0.1:{PORTA}/index.html", wait_until="load", timeout=60000)
        page.wait_for_timeout(500)
        for h in ("#p3", "#r6", "#p1"):
            page.evaluate(f"location.hash = '{h}'")
            page.wait_for_timeout(300)
            aperta = page.evaluate("document.getElementById('finestra').open")
            if not aperta:
                errori.append(f"index.html: cambiando l'indirizzo in {h} la scheda non si apre")
        page.evaluate("location.hash = ''")
        page.wait_for_timeout(300)
        if page.evaluate("document.getElementById('finestra').open"):
            errori.append("index.html: senza #p la scheda resta aperta")
        page.click('a.riquadro[href="#p2"]')
        page.wait_for_timeout(500)
        if not page.evaluate("document.getElementById('finestra').open") or page.evaluate("location.hash") != "#p2":
            errori.append("index.html: il clic sul riquadro 2 non apre la scheda 2")
        page.go_back()
        page.wait_for_timeout(500)
        if page.evaluate("document.getElementById('finestra').open"):
            errori.append("index.html: il tasto indietro non chiude la scheda")
        page.click('a.riquadro[href="#p1"]')
        page.wait_for_timeout(400)
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)
        if page.evaluate("document.getElementById('finestra').open") or page.evaluate("location.hash") != "":
            errori.append("index.html: Esc non chiude la scheda e toglie il #p")
    finally:
        page.close()
    print(f"  cambio di indirizzo (#p3, #r6, #p1): {'OK' if not errori else 'ERRORE'}")
    return errori


def prova_link_mappa(br, cartella):
    """Giro L11: ogni «Vedi sulla mappa» delle schede (data/schede_risultati.js) e i temi consigliati della mappa aprono il tema e la vista scelti.
    Si apre l'indirizzo e si legge nel DOM: menu dei temi, vista scelta, ora. Solo con Playwright. Ritorna un elenco di errori."""
    js = cartella / "data" / "schede_risultati.js"
    if not isinstance(br, BrowserPlaywright) or not js.exists():
        print("  link «Vedi sulla mappa»: non provati (serve Playwright e data/schede_risultati.js)")
        return []
    testo = js.read_text(encoding="utf-8")
    schede = json.loads(testo[testo.index("["):].split(chr(10) + "window.SCHEDE_PERIODO")[0].rstrip().rstrip(";"))
    link = []
    for s in schede:
        m = (s.get("forma") or {}).get("mappa")
        if m:
            h = f"tema={m['id']}" + (f"&vista={m['vista']}" if m.get("vista") else "")
            link.append((f"scheda {s.get('numero_pubblico', s['risultato'])}", h))
    modello = (cartella / "mappa_torino.html").read_text(encoding="utf-8")
    cons = re.findall(r'\["(tema=[^"]+)","[^"]+"\]', modello[modello.index("const CONSIGLIATI="):][:600])[:4]
    link += [("vista consigliata", h.replace("&amp;", "&")) for h in cons if "tema=tratti" not in h or '"ritardi_tratti":' in modello]
    errori = []
    for nome, h in link:
        tema = re.search(r"tema=(\w+)", h).group(1)
        vista = re.search(r"vista=(\w+)", h)
        ora = re.search(r"ora=(\d+)", h)
        page = br.br.new_page(viewport={"width": DESKTOP[0], "height": DESKTOP[1]})
        try:
            page.goto(f"http://127.0.0.1:{PORTA}/mappa_torino.html#{h}", wait_until="load", timeout=60000)
            page.wait_for_timeout(2500)
            letto = page.evaluate("""() => ({tema: document.getElementById('temi').value,
                subVuln: (document.getElementById('subVuln') || {}).value, r6: (document.getElementById('r6Vista') || {}).value,
                ora: (document.getElementById('oraTxt') || {}).textContent})""")
            if letto["tema"] != tema:
                errori.append(f"{nome} (#{h}): il menu dei temi mostra «{letto['tema']}», atteso «{tema}»")
            if vista and tema == "vulnerabilita" and letto["subVuln"] != "vuln_doppio":
                errori.append(f"{nome} (#{h}): la vista del tema Fragilità è «{letto['subVuln']}», attesa «vuln_doppio»")
            if vista and tema == "interscambio" and letto["r6"] != vista.group(1):
                errori.append(f"{nome} (#{h}): la vista dei parcheggi è «{letto['r6']}», attesa «{vista.group(1)}»")
            if ora and not (letto["ora"] or "").startswith(f"{int(ora.group(1)):02d}:"):
                errori.append(f"{nome} (#{h}): l'ora mostrata è «{letto['ora']}», attesa le {int(ora.group(1)):02d}")
        finally:
            page.close()
    # le viste consigliate si possono cliccare anche quando l'indirizzo e' gia' quello (hash uguale): si riapplicano
    page = br.br.new_page(viewport={"width": DESKTOP[0], "height": DESKTOP[1]})
    try:
        page.goto(f"http://127.0.0.1:{PORTA}/mappa_torino.html", wait_until="load", timeout=60000)
        page.wait_for_timeout(2000)
        voci = page.evaluate("[...document.querySelectorAll('#temi option[data-h]')].map(o => [o.value, /tema=([a-z_]+)/.exec(o.dataset.h)[1]])")
        for i, (valore, atteso) in enumerate(voci + [voci[0]]):   # l'ordine dipende dai dati (i «tratti» ci sono solo con i dati)
            page.select_option("#temi", valore)
            page.wait_for_timeout(1200)
            if i == len(voci):   # di nuovo la prima voce dopo aver cambiato tema col menu: l'indirizzo non cambia, il tema deve tornare
                page.select_option("#temi", "omi")
                page.wait_for_timeout(500)
                page.select_option("#temi", valore)
                page.wait_for_timeout(1200)
            tema = page.evaluate("document.getElementById('temi').value")
            if tema != atteso:
                errori.append(f"tema consigliato {i + 1}: il tema è «{tema}», atteso «{atteso}»")
    finally:
        page.close()
    print(f"  link «Vedi sulla mappa» e temi consigliati ({len(link)} indirizzi): {'OK' if not errori else 'ERRORE'}")
    return errori


ANTEPRIME = RADICE / "assets" / "anteprime"
IMMAGINI_README = RADICE / "assets" / "readme"

# immagine di anteprima 1200x630 di un risultato (per r/N.html, r/en/N.html, r/de/N.html: i link condivisi sui social). L24 (G11): a sinistra numero grande con il suo testo breve e il titolo
# (niente doppioni), a destra il disegno finale e fermo dell'animazione della scheda (come con «riduci movimento»), su un riquadro chiaro
JS_ANTEPRIMA = """(a) => {
  const n = a.n, s = window.SCHEDE_RISULTATI.find(x => x.numero_pubblico === n), f = Sito.forma(s), g = f.numero;
  const val = typeof g.valore === "number" ? Sito.formattaNumero(g.valore) : g.valore;
  const unita = g.unita === "%" ? "%" : (g.unita || "");
  const breve = g.breve || g.testo;
  const st = document.createElement("style");
  st.textContent = "html,body{margin:0;padding:0;background:var(--barra)}.og{width:1200px;height:630px;box-sizing:border-box;background:var(--barra);color:var(--su-barra);"
    + "border-bottom:14px solid var(--oro);padding:48px 56px 40px 68px;display:flex;gap:40px;overflow:hidden}"
    + ".og .sx{flex:1 1 0;min-width:0;display:flex;flex-direction:column;justify-content:space-between}"
    + ".og .k{font:700 28px/1 var(--font-titoli);letter-spacing:.08em;text-transform:uppercase;color:var(--oro-su-barra)}"
    + ".og .n{font:700 132px/1 var(--font-titoli)}.og .n small{font-size:46px;margin-left:12px;font-weight:600;opacity:.9}"
    + ".og .b{font:600 29px/1.2 var(--font-testi);margin-top:10px;max-width:560px}"
    + ".og .t{font:600 33px/1.2 var(--font-testi);max-width:580px;opacity:.95}.og .f{font:400 21px/1 var(--font-testi);opacity:.75}"
    + ".og .dx{flex:0 0 470px;align-self:center;box-sizing:border-box;max-height:490px;overflow:hidden;background:var(--card,#fff);color:var(--ink,#1b2433);border-radius:14px;padding:18px;border:1px solid var(--line,#d5dbe8)}"
    + ".og .dx .anima .didascalia{display:none}.og .dx .anima{margin:0}";
  document.head.appendChild(st);
  document.body.className = "";
  document.body.innerHTML = '<div class="og"><div class="sx"><div class="k">' + Sito.esc(a.marchio) + ' · ' + Sito.esc(Sito.etichetta(n)) + '</div>'
    + '<div><div class="n">' + val + (unita === "%" ? "%" : "<small>" + Sito.esc(unita) + "</small>") + '</div><div class="b">' + Sito.esc(breve) + '</div></div>'
    + '<div class="t">' + Sito.esc(f.titolo) + '</div><div class="f">' + Sito.esc(a.indirizzo) + '</div></div>'
    + '<div class="dx">' + (f.anima && window.Anima ? Anima.html(f.anima, {compatto: false}) : "") + '</div></div>';
  if(window.Sito && Sito.osserva) Sito.osserva(document.querySelector(".og .dx"));
}"""


def _jpg(png_bytes, percorso, larghezza=None, qualita=82, ritaglia_alt=None):
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    if ritaglia_alt:
        img = img.crop((0, 0, img.width, min(img.height, ritaglia_alt)))
    if larghezza and img.width > larghezza:
        img = img.resize((larghezza, round(img.height * larghezza / img.width)), Image.LANCZOS)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    img.save(percorso, "JPEG", quality=qualita, optimize=True)
    return percorso.stat().st_size


def fai_immagini_condivisione(br, cartella):
    """Anteprime 1200x630 dei risultati in tre lingue (assets/anteprime/{it,en,de}/rN.jpg, per le pagine di condivisione) e le 3 immagini del README (assets/readme/: home, un risultato, mappa).
    Serve Playwright, Pillow e i dati delle schede; altrimenti salta senza errore. Ritorna un elenco di errori."""
    if not isinstance(br, BrowserPlaywright) or not (cartella / "data" / "schede_risultati.js").exists():
        print("  immagini di anteprima e README: non fatte (serve Playwright e data/schede_risultati.js)")
        return []
    try:
        __import__("PIL")  # solo per sapere se Pillow c'è
    except ImportError:
        print("  immagini di anteprima e README: non fatte (manca Pillow: pip install pillow)")
        return []
    errori = []
    base = f"http://127.0.0.1:{PORTA}/"
    for lingua in LINGUE:
        ctx = br.br.new_context(viewport={"width": 1200, "height": 630}, reduced_motion="reduce", color_scheme="light", locale=f"{lingua}-{lingua.upper()}")
        page = ctx.new_page()
        try:
            page.goto(f"{base}index.html?lang={lingua}", wait_until="load", timeout=60000)
            numeri = page.evaluate("(window.SCHEDE_RISULTATI || []).filter(s => s.forma && s.numero_pubblico != null).map(s => s.numero_pubblico)")
            for n in sorted(numeri):
                page.goto(f"{base}index.html?lang={lingua}", wait_until="load", timeout=60000)
                page.evaluate(JS_ANTEPRIMA, {"n": n, "marchio": NOME_SITO, "indirizzo": SITO_URL.split("://", 1)[1].rstrip("/")})
                page.wait_for_timeout(1500)
                if page.evaluate("(() => { const d = document.querySelector('.og .dx'); return !!d && (d.querySelectorAll('svg, canvas').length > 0 || d.innerText.trim().length > 20); })()") is False:
                    errori.append(f"anteprima {lingua}/r{n}: il disegno dell'animazione e' vuoto")
                dim = _jpg(page.screenshot(clip={"x": 0, "y": 0, "width": 1200, "height": 630}), ANTEPRIME / lingua / f"r{n}.jpg", qualita=85)
                print(f"  anteprima {lingua}/r{n}.jpg: 1200x630, {dim // 1024} KB")
                if dim > 300_000:
                    errori.append(f"anteprima {lingua}/r{n}.jpg pesa {dim} byte (limite 300000)")
        except Exception as e:
            errori.append(f"anteprime {lingua}: {str(e)[:200]}")
        finally:
            ctx.close()
    ctx = br.br.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce", color_scheme="light", locale="en-GB")   # immagini del README in inglese
    page = ctx.new_page()
    try:
        for nome, indirizzo, attesa in (("home", "index.html?lang=en", 1500), ("mappa", "mappa_torino.html?lang=en#tema=vulnerabilita&vista=doppio", 4000)):
            page.goto(base + indirizzo, wait_until="load", timeout=60000)
            page.wait_for_timeout(attesa)
            dim = _jpg(page.screenshot(), IMMAGINI_README / f"{nome}.jpg", larghezza=900, qualita=80)
            print(f"  README {nome}.jpg: {dim // 1024} KB")
            if dim > 250_000:
                errori.append(f"assets/readme/{nome}.jpg pesa {dim} byte (limite 250000)")
        page.goto(base + "index.html?lang=en#p4", wait_until="load", timeout=60000)
        page.wait_for_timeout(1200)
        dim = _jpg(page.locator("#finestra").screenshot(), IMMAGINI_README / "scheda.jpg", larghezza=900, qualita=80, ritaglia_alt=1000)
        print(f"  README scheda.jpg: {dim // 1024} KB")
    except Exception as e:
        errori.append(f"immagini README: {str(e)[:200]}")
    finally:
        ctx.close()
    return errori


PAGINE_SITO = ("index.html", "progetto.html", "404.html")
LINGUE = ("it", "en", "de")
ETICHETTA_MAPPA = {"it": "Mappa", "en": "Map", "de": "Karte"}      # il secondo link della barra, per lingua
# parole italiane comuni che non devono comparire nel testo visibile in inglese e in tedesco (nomi propri di vie e zone non ne contengono)
PAROLE_ITALIANE = re.compile(r"\b(sono|ogni|più|anche|quanto|mezzi|dati|risultati|risultato|fermate|ritardo|ritardi|torinesi|persone|giorni|settimane|dalla|alla|tutti|tutte|perché|nella|delle|degli)\b")


def prova_lingue(br, cartella):
    """Ogni pagina del sito in ogni lingua: 0 errori JavaScript, lingua giusta, avvertenza e autore (nel piede) presenti, nessuna parola italiana comune in EN e DE;
    poi i bottoni IT EN DE cambiano lingua senza ricaricare la pagina. Solo con Playwright. Ritorna un elenco di errori."""
    if not isinstance(br, BrowserPlaywright):
        print("  lingue delle pagine: non provate (serve Playwright)")
        return []
    from schede.pagine_sito import AVVERTENZA, PAYOFF
    errori = []
    base = f"http://127.0.0.1:{PORTA}/"
    for file in PAGINE_SITO:
        for lingua in LINGUE:
            ctx = br.br.new_context(viewport={"width": DESKTOP[0], "height": DESKTOP[1]})
            page = ctx.new_page()
            js = []
            page.on("pageerror", lambda e: js.append(str(e)[:200]))
            page.on("console", lambda m: js.append(m.text[:200]) if m.type == "error" and "Failed to load resource" not in m.text else None)
            try:
                page.goto(f"{base}{file}?lang={lingua}", wait_until="load", timeout=60000)
                page.wait_for_timeout(1500)
                dove = f"{file} [{lingua}]"
                errori += [f"{dove}: errore JavaScript: {e}" for e in js]
                if page.evaluate("document.documentElement.lang") != lingua:
                    errori.append(f"{dove}: l'attributo lang non e' «{lingua}»")
                testo = page.evaluate("document.body.innerText")
                if lingua != "it":
                    trovate = sorted(set(PAROLE_ITALIANE.findall(testo.replace("Castello di Mirafiori", ""))))   # nome proprio di una fermata
                    if trovate:
                        errori.append(f"{dove}: parole italiane nel testo visibile: {trovate}")
                if page.evaluate("(document.querySelector('.piede .avvertenza') || {}).textContent") != AVVERTENZA[lingua]:
                    errori.append(f"{dove}: avvertenza assente o nella lingua sbagliata")
                if "Leonardo Campese" not in page.evaluate("(document.querySelector('.piede') || {}).textContent || ''"):
                    errori.append(f"{dove}: nel piede manca l'autore")
                if file == "index.html" and page.evaluate("(document.querySelector('.eroe .sotto') || {}).textContent") != PAYOFF[lingua]:
                    errori.append(f"{dove}: sotto il titolo manca il payoff nella lingua giusta")
                if "Turin Meter" not in page.title():
                    errori.append(f"{dove}: il titolo della scheda del browser non contiene «Turin Meter»: «{page.title()}»")
                for vecchio in VECCHI_NOMI:
                    if vecchio.lower() in testo.lower() or vecchio.lower() in page.content().lower():
                        errori.append(f"{dove}: compare «{vecchio}»")
            except Exception as e:
                errori.append(f"{file} [{lingua}]: {str(e)[:200]}")
            finally:
                ctx.close()
    for file in PAGINE_SITO:
        ctx = br.br.new_context(viewport={"width": DESKTOP[0], "height": DESKTOP[1]}, locale="it-IT")
        page = ctx.new_page()
        try:
            page.goto(base + file, wait_until="load", timeout=60000)
            page.wait_for_timeout(800)
            page.evaluate("window.__stessaPagina = 1")
            for l in ("en", "de", "it"):
                page.click(f".lingua button[data-l='{l}']")
                page.wait_for_timeout(300)
                letto = page.evaluate("""() => ({lang: document.documentElement.lang, premuto: (document.querySelector('.lingua button[aria-pressed=true]') || {dataset: {}}).dataset.l,
                    nav: document.querySelector('nav a[href=\"mappa_torino.html\"]').textContent, stessa: window.__stessaPagina === 1})""")
                if letto["lang"] != l or letto["premuto"] != l or letto["nav"] != ETICHETTA_MAPPA[l]:
                    errori.append(f"{file}: il bottone {l.upper()} non cambia lingua ({letto})")
                if not letto["stessa"]:
                    errori.append(f"{file}: il bottone {l.upper()} ha ricaricato la pagina")
        except Exception as e:
            errori.append(f"{file}: bottoni della lingua: {str(e)[:200]}")
        finally:
            ctx.close()
    print(f"  pagine del sito in tre lingue ({len(PAGINE_SITO) * len(LINGUE)} aperture) e bottoni IT EN DE: {'OK' if not errori else 'ERRORE'}")
    return errori


JS_CARATTERI = """() => { const out = [];
  document.querySelectorAll('svg text, svg tspan').forEach(t => { if(!t.getClientRects().length) return; const m = t.getScreenCTM(), fs = parseFloat(getComputedStyle(t).fontSize), e = fs * (m ? Math.hypot(m.a, m.b) : 1);
    if(e < 10.9) out.push('svg ' + e.toFixed(1) + 'px «' + (t.textContent || '').trim().slice(0, 30) + '»'); });
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
  while(n = w.nextNode()){ const el = n.parentElement; if(!n.textContent.trim() || el.closest('svg,script,style,title,noscript') || !el.getClientRects().length) continue;
    const fs = parseFloat(getComputedStyle(el).fontSize); if(fs < 10.9) out.push('testo ' + fs + 'px «' + n.textContent.trim().slice(0, 30) + '»'); }
  return out; }"""


def prova_telefono(br, cartella):
    """A 390x844 ogni testo dei grafici e delle pagine misura almeno 11 px veri (tenendo conto della scala del disegno), in ogni scheda e lingua. Solo con Playwright."""
    js = cartella / "data" / "schede_risultati.js"
    if not isinstance(br, BrowserPlaywright) or not js.exists():
        print("  caratteri sul telefono: non provati (serve Playwright e data/schede_risultati.js)")
        return []
    testo = js.read_text(encoding="utf-8")
    schede = json.loads(testo[testo.index("["):testo.index("window.SCHEDE_PERIODO")].rstrip().rstrip(";"))
    numeri = sorted(s["numero_pubblico"] for s in schede if s.get("forma") and s.get("numero_pubblico") is not None)
    errori = []
    for lingua in LINGUE:
        for pagina in [f"index.html?lang={lingua}"] + [f"index.html?lang={lingua}#p{n}" for n in numeri]:
            ctx = br.br.new_context(viewport={"width": TELEFONO[0], "height": TELEFONO[1]})
            page = ctx.new_page()
            try:
                page.goto(f"http://127.0.0.1:{PORTA}/{pagina}", wait_until="load", timeout=60000)
                page.wait_for_timeout(3500)
                for x in page.evaluate(JS_CARATTERI)[:5]:
                    errori.append(f"{pagina} (telefono): carattere troppo piccolo: {x}")
            finally:
                ctx.close()
    print(f"  caratteri di almeno 11 px sul telefono ({len(LINGUE) * (len(numeri) + 1)} pagine): {'OK' if not errori else 'ERRORE'}")
    return errori


PAROLE_ITALIANE = re.compile(r"\b(tutte|due|di|della|dei|degli|che|con|nel|nella|nei|più|dove|quanti|quanto|sono|anche|ogni|questo|questa|fuori|nessun|nessuna|chi|cosa|dati|dato|mezzi|linee|abitanti|fermata|fermate|passaggi|servizi|ritardo|giorno|giorni|feriale|manca|mancano|posti|parcheggio|parcheggi|oltre|sotto|poco|poca|molto|molta)\b", re.I)
# etichette del tipo di dato (§5.0 del piano): mai da sole, mai fra parentesi quadre
ETICHETTA_TIPO = re.compile(r"\[[A-ZÄÖÜ][A-ZÄÖÜ ]{3,}[^\]]*\]|\b(MISURATO|STIMATO|CALCOLATO|DATI SCARSI|MEASURED|ESTIMATED|CALCULATED|GEMESSEN|GESCHÄTZT|BERECHNET)\b")
JS_TESTO_MAPPA = "() => [...document.querySelectorAll('#pannello,#legenda')].map(e => e.innerText).join('\\n')"
JS_CARATTERI_PANNELLO = """() => { const out = [];
  document.querySelectorAll('#pannello *').forEach(el => { if(!el.getClientRects().length) return;
    const dir = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if(!dir) return;
    const fs = parseFloat(getComputedStyle(el).fontSize); if(fs < 10.9) out.push(fs + 'px «' + el.textContent.trim().slice(0, 30) + '»'); });
  return out; }"""


def mappa_con_tratti(cartella):
    """Copia provvisoria della mappa con tratti finti (da fermate vere) per provare il tema «Dove i bus perdono tempo»; ritorna il nome del file o None."""
    import rifai_mappa_da_html as rifai
    import config_locale
    mappa = cartella / "mappa_torino.html"
    if not mappa.exists():
        return None
    dati = rifai.leggi_dati(mappa)
    st = [f for f in dati.get("fermate", []) if 45.04 < f["la"] < 45.10 and 7.62 < f["lo"] < 7.72]
    tratti = []
    for i in range(0, min(len(st) - 1, 300), 2):
        a, b = st[i], st[i + 1]
        if abs(a["la"] - b["la"]) + abs(a["lo"] - b["lo"]) < 0.012:
            tratti.append({"a": a["n"], "b": b["n"], "l": (a["r"] or "").split(", ")[:2], "g": [[a["la"], a["lo"]], [b["la"], b["lo"]]],
                           "m": round(0.5 + (i % 25), 1), "n": 60 + i})
    dati["ritardi_tratti"] = {"meta": {"periodo": {"da": "2026-10-09", "a": "2026-10-22"}, "min_corse": 50}, "tratti": tratti}
    testo = json.dumps(dati, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    html = (AQUI / "mappa_template.html").read_text(encoding="utf-8").replace('"__DATI__"', testo)
    nome = "mappa_prova_tratti.tmp.html"
    (cartella / nome).write_text(config_locale.metti_chiavi_mappa(html), encoding="utf-8")
    return nome


def prova_mappa(br, cartella):
    """La mappa: apre senza tema («Scegli un tema»), senza caricamento che resta; sfondo iniziale giusto con e senza chiavi; temi consigliati con la stellina (3 o 4) che applicano
    tema, giorno e ora; guida di al massimo 150 parole; nessuna etichetta del tipo di dato; in IT, EN, DE; cambio lingua senza ricaricare;
    ogni tema senza errori; in EN e DE niente parole italiane nel pannello e nella legenda di ogni tema; sul telefono caratteri del pannello da 11 px; tema nuovo dei tratti."""
    if not isinstance(br, BrowserPlaywright) or not (cartella / "mappa_torino.html").exists():
        print("  mappa in tre lingue: non provata (serve Playwright e mappa_torino.html)")
        return []
    errori = []
    base = f"http://127.0.0.1:{PORTA}/"
    temi = re.findall(r'\{id:"([a-z_0-9]+)", label:', TEMPLATE.read_text(encoding="utf-8"))
    for lingua in LINGUE:
        ctx = br.br.new_context(viewport={"width": DESKTOP[0], "height": 800}, locale=lingua)
        page = ctx.new_page()
        js_err = []
        page.on("pageerror", lambda e: js_err.append(str(e)))
        try:
            page.goto(f"{base}mappa_torino.html?lang={lingua}", wait_until="load", timeout=90000)
            page.wait_for_timeout(1500)
            st = page.evaluate("""() => ({tema: document.getElementById('temi').value, ora: document.getElementById('oraTxt').textContent,
                feriale: document.querySelector('#giorno button[data-k="0"]').getAttribute('aria-pressed'), lang: document.documentElement.lang,
                caricamento: !!document.getElementById('caricamento'), jsoff: getComputedStyle(document.getElementById('jsoff')).display,
                chiara: !!document.querySelector('#basemap option[value="chiara"]'), sat: !!document.querySelector('#basemap option[value="sat"]'), base: document.getElementById('basemap').value,
                lingue: [...document.querySelectorAll('.lingua button')].map(b => b.dataset.l + ':' + b.getAttribute('aria-pressed')).join()})""")
            if st["tema"] != "":
                errori.append(f"mappa ({lingua}): all'apertura il tema è «{st['tema']}», atteso nessuno")
            primo = page.evaluate("document.querySelector('#temi option').textContent")
            if primo != {"it": "Scegli un tema", "en": "Choose a theme", "de": "Thema wählen"}[lingua]:
                errori.append(f"mappa ({lingua}): il menu dei temi dice «{primo}» all'apertura")
            cons = page.evaluate("() => [...document.querySelectorAll('#temi option[data-h]')].map(o => o.textContent.trim())")
            gruppi = page.evaluate("() => [...document.querySelectorAll('#temi optgroup')].map(g => g.label)")
            if any(g in ("Consigliati", "Recommended", "Empfohlen") for g in gruppi):
                errori.append(f"mappa ({lingua}): il menu ha ancora un gruppo a sé per i temi consigliati: {gruppi}")
            if len(cons) not in (3, 4) or not all(c.endswith("★") for c in cons):
                errori.append(f"mappa ({lingua}): i temi consigliati dovrebbero essere 3 o 4, con la stellina a destra: {cons}")
            guida = page.evaluate("() => { const d = document.getElementById('infoDati'); d.open = true; const c = d.cloneNode(true); c.querySelector('#stato').previousElementSibling.remove(); c.querySelector('#stato').remove(); return c.innerText; }")   # la guida senza l'elenco «Fonti e date» (date dei dati)
            if len(guida.split()) > 150:
                errori.append(f"mappa ({lingua}): la guida ha {len(guida.split())} parole (massimo 150)")
            if lingua != "it" and PAROLE_ITALIANE.search(guida.replace("Agenzia della Mobilità Piemontese", "")):
                errori.append(f"mappa ({lingua}): la guida ha parole italiane: «{PAROLE_ITALIANE.search(guida).group(0)}»")
            if st["lang"] != lingua or f"{lingua}:true" not in st["lingue"]:
                errori.append(f"mappa ({lingua}): lingua della pagina «{st['lang']}», pulsanti {st['lingue']}")
            if st["caricamento"]:
                errori.append(f"mappa ({lingua}): la schermata di caricamento è ancora lì dopo 1,5 secondi")
            if st["jsoff"] != "none":
                errori.append(f"mappa ({lingua}): il pannello di errore è visibile")
            atteso = "sat" if st["sat"] else "chiara" if st["chiara"] else None   # con la chiave Esri si apre sul satellite, con la sola chiave CARTO sulla mappa chiara
            if atteso and st["base"] != atteso:
                errori.append(f"mappa ({lingua}): lo sfondo all'apertura è «{st['base']}», atteso «{atteso}»")
            if lingua == "it":
                # un tema consigliato applica tema, giorno e ora
                page.select_option("#temi", "puntualita")
                page.wait_for_timeout(500)
                c = page.evaluate("() => ({tema: document.getElementById('temi').value, ora: document.getElementById('oraTxt').textContent})")
                if c["tema"] != "puntualita" or c["ora"] != "08:00":
                    errori.append(f"mappa: il tema consigliato «Ritardi delle linee» non applica tema e ora ({c})")
            for t in page.evaluate("() => [...document.querySelectorAll('#temi option')].map(o => o.value).filter(v => v && !v.startsWith('cons:'))"):
                page.select_option("#temi", t)
                page.wait_for_timeout(250)
                sels = page.evaluate("() => [...document.querySelectorAll('#boxOpzioni select')].map(s => s.id)")
                testi = [page.evaluate(JS_TESTO_MAPPA)]
                if page.evaluate("document.querySelectorAll('.tag, .tipo-dato').length"):
                    errori.append(f"mappa ({lingua}), tema {t}: ci sono etichette del tipo di dato (.tag)")
                for sid in sels:
                    for o in page.evaluate("(id) => [...document.querySelectorAll('#' + id + ' option')].map(o => o.value)", sid):
                        page.select_option("#" + sid, o)
                        page.wait_for_timeout(120)
                        testi.append(page.evaluate(JS_TESTO_MAPPA))
                for r in dict.fromkeys(riga.strip() for tx in testi for riga in tx.split("\n")):
                    if ETICHETTA_TIPO.search(r):
                        errori.append(f"mappa ({lingua}), tema {t}: etichetta del tipo di dato: {r[:90]}")
                if lingua != "it":
                    for r in dict.fromkeys(riga.strip() for tx in testi for riga in tx.split("\n")):
                        m = PAROLE_ITALIANE.search(r.replace("Agenzia della Mobilità Piemontese", ""))   # nome proprio
                        if m:
                            errori.append(f"mappa ({lingua}), tema {t}: testo non tradotto («{m.group(0)}»): {r[:90]}")
            if lingua == "it":
                # cambio lingua senza ricaricare: EN, DE, di nuovo IT con lo stesso testo di prima
                page.select_option("#temi", "puntualita")
                page.wait_for_timeout(300)
                it1 = page.evaluate(JS_TESTO_MAPPA)
                attesi = {"en": "Line delays", "de": "Verspätungen der Linien"}
                for l2 in ("en", "de"):
                    page.click(f'.lingua button[data-l="{l2}"]')
                    page.wait_for_timeout(300)
                    t2 = page.evaluate(JS_TESTO_MAPPA)
                    if attesi[l2] not in t2:
                        errori.append(f"mappa: dopo il clic su {l2.upper()} manca «{attesi[l2]}» nel pannello")
                    salvata = page.evaluate("localStorage.getItem('tm_lingua')")
                    if salvata != l2 or page.evaluate("document.documentElement.lang") != l2:
                        errori.append(f"mappa: dopo il clic su {l2.upper()} la lingua salvata è «{salvata}»")
                page.click('.lingua button[data-l="it"]')
                page.wait_for_timeout(300)
                if page.evaluate(JS_TESTO_MAPPA) != it1:
                    errori.append("mappa: tornando all'italiano il testo del pannello non è uguale a prima")
        finally:
            ctx.close()
        for e in js_err[:3]:
            errori.append(f"mappa ({lingua}): errore JavaScript: {e[:120]}")
    # sfondo iniziale con e senza chiavi (nel cloud la chiave Esri non c'è: copie provvisorie della pagina con una chiave finta, nessun riquadro scaricato)
    html = (cartella / "mappa_torino.html").read_text(encoding="utf-8")
    m = re.search(r'const CHIAVI=\{carto:"([^"]*)", arcgis:"([^"]*)"\};', html)
    if not m:
        errori.append("mappa: non trovo la riga delle chiavi degli sfondi")
    else:
        casi = {"con_arcgis": ('carto:"chiave-finta-c", arcgis:"chiave-finta-a"', "sat", ["sat", "chiara", "nessuno"], "Esri, Maxar, Earthstar Geographics"),
                "solo_carto": ('carto:"chiave-finta-c", arcgis:""', "chiara", ["chiara", "nessuno"], "CARTO"),
                "senza_chiavi": ('carto:"", arcgis:""', "nessuno", ["nessuno"], "")}
        for nome, (riga, atteso, opzioni, credito) in casi.items():
            copia = cartella / f"mappa_prova_{nome}.html"
            copia.write_text(html.replace(m.group(0), "const CHIAVI={" + riga + "};"), encoding="utf-8")
            page = br.br.new_page(viewport={"width": DESKTOP[0], "height": 800})
            try:
                page.route("**/*cartocdn.com/**", lambda route: route.abort())
                page.route("**/*arcgis.com/**", lambda route: route.abort())
                page.goto(f"{base}{copia.name}?lang=en", wait_until="load", timeout=90000)
                page.wait_for_timeout(1000)
                st = page.evaluate("() => ({base: document.getElementById('basemap').value, opz: [...document.querySelectorAll('#basemap option')].map(o => o.value), cred: document.getElementById('attrib').textContent, tema: document.getElementById('temi').value})")
                if st["base"] != atteso or st["opz"] != opzioni:
                    errori.append(f"mappa ({nome}): sfondo «{st['base']}» con voci {st['opz']}, attesi «{atteso}» e {opzioni}")
                if credito and credito not in st["cred"]:
                    errori.append(f"mappa ({nome}): l'attribuzione «{credito}» non è visibile: «{st['cred']}»")
                if st["tema"] != "":
                    errori.append(f"mappa ({nome}): c'è un tema all'avvio ({st['tema']})")
            finally:
                page.close()
                try:
                    copia.unlink()
                except OSError:
                    pass
    # telefono: i testi del pannello (aperto) misurano almeno 11 px
    ctx = br.br.new_context(viewport={"width": TELEFONO[0], "height": TELEFONO[1]})
    page = ctx.new_page()
    try:
        page.goto(f"{base}mappa_torino.html?lang=it", wait_until="load", timeout=90000)
        page.wait_for_timeout(1500)
        page.click("#maniglia")
        page.wait_for_timeout(400)
        page.evaluate("() => { document.getElementById('boxAltre').open = true; document.getElementById('infoDati').open = true; }")
        for x in page.evaluate(JS_CARATTERI_PANNELLO)[:5]:
            errori.append(f"mappa (telefono): carattere del pannello troppo piccolo: {x}")
    finally:
        ctx.close()
    # tema dei tratti: con dati compare e funziona, senza dati non compare
    senza = br.br.new_page(viewport={"width": DESKTOP[0], "height": 800})
    try:
        senza.goto(f"{base}mappa_torino.html", wait_until="load", timeout=90000)
        senza.wait_for_timeout(1000)
        ha_dati = '"ritardi_tratti":' in (cartella / "mappa_torino.html").read_text(encoding="utf-8")
        if not ha_dati and senza.evaluate("!!document.querySelector('#temi option[value=tratti]')"):
            errori.append("mappa: senza dati il tema «Dove i bus perdono tempo» compare nel menu")
        if senza.evaluate("!!document.querySelector('#temi option[data-h=\"tema=tratti\"]')") and senza.evaluate("!document.querySelector('#temi option[value=tratti]')"):
            errori.append("mappa: senza dati la vista consigliata dei tratti resta")
    finally:
        senza.close()
    nome = mappa_con_tratti(cartella)
    if nome:
        page = br.br.new_page(viewport={"width": DESKTOP[0], "height": 800})
        js_err = []
        page.on("pageerror", lambda e: js_err.append(str(e)))
        try:
            page.goto(f"{base}{nome}?lang=en#tema=tratti", wait_until="load", timeout=90000)
            page.wait_for_timeout(1500)
            st = page.evaluate("() => ({tema: document.getElementById('temi').value, leg: document.getElementById('legenda').innerText})")
            if st["tema"] != "tratti" or "Minutes lost on a weekday" not in st["leg"]:
                errori.append(f"mappa (tratti): tema «{st['tema']}», legenda «{st['leg'][:60]}»")
            trovato = ""
            for x in range(380, 780, 14):
                for y in range(260, 620, 14):
                    page.mouse.move(x, y)
                    tip = page.evaluate("() => { const t = document.getElementById('tip'); return t.style.display !== 'none' ? t.innerText : ''; }")
                    if tip:
                        trovato = tip
                        break
                if trovato:
                    break
            if not re.search(r"Between .+ and .+, lines .+, \+[\d.,]+ minutes per day", trovato):
                errori.append(f"mappa (tratti): la finestrella non dice «tra A e B, linee …, +N minuti al giorno»: «{trovato[:100]}»")
            for e in js_err[:3]:
                errori.append(f"mappa (tratti): errore JavaScript: {e[:120]}")
        finally:
            page.close()
            try:
                (cartella / nome).unlink()
            except OSError:
                pass
    print(f"  mappa in tre lingue, tema iniziale, {len(temi)} temi, telefono, tratti: {'OK' if not errori else 'ERRORE'}")
    return errori


def prova_testi(br, cartella):
    """Testi e pagina del progetto (§5.0 del piano), in tre lingue, con Playwright:
      - home, schede aperte, mappa e progetto: nessun elemento .tipo-dato / .tag, nessuna etichetta del tipo di dato, nessuna formula vietata (prove/frasi_vietate.py);
      - «Raspberry» solo nella parte «Come funziona» del progetto (e nel suo disegno); mai in home, schede e mappa;
      - progetto: al massimo 750 parole in italiano, inglese e tedesco non oltre il 30% in più; 10 parti;
      - scorrendo in avanti e all'indietro il disegno visibile è quello della parte letta; accanto a «Chi sono» nessun disegno."""
    if not isinstance(br, BrowserPlaywright):
        print("  testi e pagina del progetto: non provati (serve Playwright)")
        return []
    sys.path.insert(0, str(RADICE / "scripts" / "prove"))
    import frasi_vietate
    errori = []
    base = f"http://127.0.0.1:{PORTA}/"
    parole = {}
    for lingua in LINGUE:
        ctx = br.br.new_context(viewport={"width": DESKTOP[0], "height": 900})
        page = ctx.new_page()
        js = []
        page.on("pageerror", lambda e: js.append(str(e)[:150]))
        try:
            def controlla(dove, testo, raspberry_ok=False):
                for t in frasi_vietate.trova(testo, lingua):
                    errori.append(f"{dove} [{lingua}]: formula vietata o etichetta del tipo di dato: «{t}»")
                if not raspberry_ok and "raspberry" in testo.lower():
                    errori.append(f"{dove} [{lingua}]: compare «Raspberry»")
            # home
            page.goto(f"{base}index.html?lang={lingua}", wait_until="load", timeout=60000)
            page.wait_for_timeout(1500)
            controlla("home", page.evaluate("document.body.innerText"))
            if page.evaluate("document.querySelectorAll('.tipo-dato, .tag').length"):
                errori.append(f"home [{lingua}]: ci sono elementi .tipo-dato o .tag")
            for n in (1, 2, 3, 4):
                page.goto(f"{base}index.html?lang={lingua}#p{n}", wait_until="load", timeout=60000)
                page.wait_for_timeout(900)
                if not page.evaluate("document.getElementById('finestra').open"):
                    errori.append(f"index.html#p{n} [{lingua}]: la scheda non si apre")
                    continue
                controlla(f"scheda {n}", page.evaluate("document.getElementById('finestra').innerText"))
                if page.evaluate("document.querySelectorAll('#finestra .tipo-dato').length"):
                    errori.append(f"scheda {n} [{lingua}]: c'è un .tipo-dato")
            # mappa: pannello, guida e legenda del tema iniziale
            page.goto(f"{base}mappa_torino.html?lang={lingua}", wait_until="load", timeout=90000)
            page.wait_for_timeout(1500)
            controlla("mappa", page.evaluate("document.getElementById('pannello').innerText + ' ' + document.getElementById('legenda').innerText"))
            # progetto
            page.goto(f"{base}progetto.html?lang={lingua}", wait_until="load", timeout=60000)
            page.wait_for_timeout(1500)
            testo = page.evaluate("document.querySelector('main').innerText")
            parole[lingua] = page.evaluate("[document.querySelector('.intro-pag'), document.querySelector('.testi')].map(e => e.innerText).join(' ').split(/\\s+/).filter(Boolean).length")
            sezioni = page.evaluate("[...document.querySelectorAll('.testi section')].length")
            if sezioni != 9 + 1 - 0 and sezioni != 10:
                errori.append(f"progetto [{lingua}]: {sezioni} parti, non 10")
            fuori = page.evaluate("""() => { const c = document.querySelector('main').cloneNode(true);
                c.querySelectorAll('#sistema, #fS').forEach(e => e.remove()); return c.innerText; }""")
            controlla("progetto", fuori)
            if "raspberry" not in testo.lower():
                errori.append(f"progetto [{lingua}]: «Raspberry» manca nella parte «Come funziona»")
            controlla("progetto (testo intero)", testo, raspberry_ok=True)
            # scorrimento: ogni parte, in avanti e all'indietro, mostra il suo disegno
            ordine = page.evaluate("[...document.querySelectorAll('.testi [data-fig]')].map((e, i) => i)")
            for passata in (ordine, list(reversed(ordine))):
                for i in passata:
                    page.evaluate(f"document.querySelectorAll('.testi [data-fig]')[{i}].scrollIntoView({{block: 'center'}})")
                    page.wait_for_timeout(120)
                    letto = page.evaluate(f"""() => {{ const e = document.querySelectorAll('.testi [data-fig]')[{i}];
                        const att = [...document.querySelectorAll('.fig.attiva')].map(f => f.id); return [e.getAttribute('data-fig'), att.join()]; }}""")
                    if letto[0] != letto[1]:
                        errori.append(f"progetto [{lingua}]: alla parte {i} il disegno visibile è «{letto[1]}», atteso «{letto[0]}»")
            # scorrimento veloce all'indietro: dalla fine al principio in un colpo solo
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(150)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(300)
            att = page.evaluate("[...document.querySelectorAll('.fig.attiva')].map(f => f.id).join()")
            if att != "fN":
                errori.append(f"progetto [{lingua}]: tornando in cima il disegno è «{att}», atteso «fN»")
            for e in js[:3]:
                errori.append(f"[{lingua}]: errore JavaScript: {e}")
        finally:
            ctx.close()
    if parole.get("it", 0) > 750:
        errori.append(f"progetto: {parole['it']} parole in italiano (massimo 750)")
    for lingua in ("en", "de"):
        if parole.get(lingua, 0) > parole.get("it", 0) * 1.3:
            errori.append(f"progetto: {parole[lingua]} parole in {lingua}, troppe rispetto all'italiano ({parole['it']})")
    print(f"  testi, tono, disegni e pagina del progetto ({parole}): {'OK' if not errori else 'ERRORE'}")
    return errori



def prova_condivisione(cartella):
    """Pagine di condivisione (r/N.html, r/en/N.html, r/de/N.html, en/index.html, de/index.html): titolo, og:locale, og:image nella lingua giusta,
    immagine presente e leggera, rimando con ?lang=; niente pagine di schede che non ci sono piu'. Ritorna un elenco di errori."""
    from schede.pagine_sito import LOCALE
    js = cartella / "data" / "schede_risultati.js"
    if not js.exists():
        print("  pagine di condivisione: non provate (manca data/schede_risultati.js)")
        return []
    testo = js.read_text(encoding="utf-8")
    schede = json.loads(testo[testo.index("["):testo.index("window.SCHEDE_PERIODO")].rstrip().rstrip(";"))
    numeri = sorted(s["numero_pubblico"] for s in schede if s.get("forma") and s.get("numero_pubblico") is not None)
    attese = {}
    for lingua in LINGUE:
        for n in numeri:
            attese[f"r/{n}.html" if lingua == "it" else f"r/{lingua}/{n}.html"] = (lingua, f"assets/anteprime/{lingua}/r{n}.jpg", n)
    attese["en/index.html"] = ("en", "assets/anteprima-en.png", None)
    attese["de/index.html"] = ("de", "assets/anteprima-de.png", None)
    errori = []
    for rel, (lingua, immagine, n) in attese.items():
        p = cartella / rel
        if not p.exists():
            errori.append(f"{rel}: pagina di condivisione mancante")
            continue
        t = p.read_text(encoding="utf-8")
        og = lambda k: (re.search(rf'<meta property="og:{k}" content="([^"]*)"', t) or [None, ""])[1]
        if f'<html lang="{lingua}">' not in t:
            errori.append(f"{rel}: lang non e' «{lingua}»")
        if og("locale") != LOCALE[lingua]:
            errori.append(f"{rel}: og:locale e' «{og('locale')}», atteso «{LOCALE[lingua]}»")
        if not og("title").strip() or not og("description").strip():
            errori.append(f"{rel}: og:title o og:description vuoti")
        if not og("image").endswith("/" + immagine):
            errori.append(f"{rel}: og:image e' «{og('image')}», atteso un indirizzo che finisce con {immagine}")
        if lingua == "en" and PAROLE_ITALIANE.search(og("title") + " " + og("description")):
            errori.append(f"{rel}: parole italiane in og:title o og:description")
        if f"lang={lingua}" not in t and lingua != "it":
            errori.append(f"{rel}: il rimando non porta ?lang={lingua}")
        img = cartella / immagine
        if not img.exists():
            errori.append(f"{rel}: manca l'immagine {immagine}")
        elif immagine.endswith(".jpg") and img.stat().st_size > 300_000:
            errori.append(f"{immagine} pesa {img.stat().st_size} byte (limite 300000)")
    for vecchia in list((cartella / "r").glob("*.html")) + list((cartella / "r").glob("*/*.html")):
        if vecchia.relative_to(cartella).as_posix() not in attese:
            errori.append(f"{vecchia.relative_to(cartella).as_posix()}: pagina di una scheda che non c'e' piu'")
    print(f"  pagine di condivisione ({len(attese)}): {'OK' if not errori else 'ERRORE'}")
    return errori


VECCHI_NOMI = ("Turin" + "-mobility", "Torino" + " Mobilità")
CARTELLE_SALTATE = {".git", "sviluppo", "data", "immagini", "node_modules", "__pycache__", "_prova_pubblico"}


def prova_nomi_vecchi(cartella):
    """Nessun file di testo del progetto (fuori da sviluppo/ e data/) nomina il vecchio indirizzo o il vecchio nome. Ritorna un elenco di errori."""
    errori = []
    for p in sorted(cartella.rglob("*")):
        rel = p.relative_to(cartella)
        if not p.is_file() or CARTELLE_SALTATE & set(rel.parts) or p.suffix.lower() not in (".html", ".js", ".md", ".py", ".json", ".css", ".txt", ".yml", ".svg") or p.name == "prova_pagine.py":
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for v in VECCHI_NOMI:
            if v.lower() in t:
                errori.append(f"{rel.as_posix()}: compare «{v}»")
    print(f"  vecchio indirizzo e vecchio nome: {'nessuno' if not errori else errori[:3]}")
    return errori



def sceglie_browser(forza_playwright):
    if not forza_playwright and os.name == "nt":
        for p in BROWSER_WINDOWS:
            if os.path.exists(p):
                return BrowserWindows(p)
        print("non trovo Edge né Chrome: provo con Playwright")
    try:
        return BrowserPlaywright()
    except ImportError:
        print("manca Playwright: pip install playwright (poi, se serve, python -m playwright install chromium)")
    except Exception as e:
        print(f"Playwright non riesce ad aprire il browser: {str(e)[:200]}")
    return None


def controllo_statico():
    """Identificatori r6.../R6... usati come variabili e non definiti.
    Esclusi: chiavi di oggetto («nome:»), proprietà («.nome»), testi tra virgolette («"nome"»)."""
    testo = TEMPLATE.read_text(encoding="utf-8")
    # via il testo tra virgolette (stringhe e id) prima di cercare gli usi
    senza_stringhe = re.sub(r'"[^"\n]*"|\'[^\'\n]*\'|`[^`]*`', '""', testo)
    usati = set()
    for m in re.finditer(r"(?<![\w.])([rR]6[A-Za-z_]\w*)\b", senza_stringhe):
        dopo = senza_stringhe[m.end():m.end() + 3].lstrip(" ")
        if dopo.startswith(":") and not dopo.startswith("::"):
            continue   # chiave di oggetto
        usati.add(m.group(1))
    definiti = set(re.findall(r"\b(?:const|let|var|function)\s+([rR]6\w*)", testo))
    return sorted(usati - definiti)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cartella", default=None, help="cartella da servire (default: radice del progetto)")
    ap.add_argument("--senza-screenshot", action="store_true")
    ap.add_argument("--playwright", action="store_true", help="usa Playwright anche su Windows")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    cartella = (RADICE / args.cartella) if args.cartella else RADICE
    br = sceglie_browser(args.playwright)
    if not br:
        print("prova automatica non possibile: nessun browser utilizzabile")
        return 1
    print(f"browser: {br.nome}")
    errori, assenti_tot = [], {}
    srv = avvia_server(cartella)
    pagine = pagine_da_provare()
    try:
        for nome, pagina in pagine:
            dom, err, assenti = br.apri(f"http://127.0.0.1:{PORTA}/{pagina}", nome.replace(" ", "_"))
            errori += [f"{nome}: {e}" for e in err]
            for a in assenti:
                assenti_tot.setdefault(a, []).append(nome)
            m = re.search(r'<div[^>]*id="jsoff"[^>]*>', dom)
            if m and re.search(r"display:\s*block", m.group(0)):
                errori.append(f"{nome}: il pannello #jsoff è visibile (display: block)")
            if pagina.startswith("mappa"):
                vista = re.search(r"vista=(\w+)", pagina)
                if vista and vista.group(1) in TITOLI_VISTA:
                    atteso = TITOLI_VISTA[vista.group(1)]
                    if atteso not in dom:
                        errori.append(f"{nome}: nella pagina manca il titolo della legenda «{atteso}»")
            print(f"  {nome}: {len(err)} errori, {len(assenti)} file assenti, DOM {len(dom)} caratteri")
        errori += prova_cambio_indirizzo(br, cartella)
        errori += prova_link_mappa(br, cartella)
        errori += prova_testi(br, cartella)
        errori += prova_lingue(br, cartella)
        errori += prova_telefono(br, cartella)
        errori += prova_mappa(br, cartella)
        if not args.senza_screenshot:
            IMMAGINI.mkdir(exist_ok=True)
            for nome, pagina in pagine_screenshot():
                for sigla, (w, h) in (("desktop", DESKTOP), ("telefono", TELEFONO)):
                    png = IMMAGINI / f"{nome}_{sigla}.png"
                    if png.exists():
                        png.unlink()
                    br.apri(f"http://127.0.0.1:{PORTA}/{pagina}", f"{nome}_{sigla}", png=png, w=w, h=h)
                    dim = png.stat().st_size if png.exists() else 0
                    print(f"  screenshot {png.name} ({w}x{h}): {dim} byte" + ("  (meno di 5 KB: probabile pagina vuota)" if dim < 5000 else ""))
                    if dim < 5000:
                        errori.append(f"screenshot {png.name}: file piccolo ({dim} byte): probabile pagina vuota")
            errori += fai_immagini_condivisione(br, cartella)
    finally:
        srv.shutdown()
        srv.server_close()
        br.chiudi()
    errori += prova_condivisione(cartella)
    errori += prova_nomi_vecchi(cartella)
    mancanti = controllo_statico()
    print(f"  identificatori r6/R6 non definiti: {mancanti if mancanti else 'nessuno'}")
    for m_ in mancanti:
        errori.append(f"identificatore non definito: {m_}")
    # etichette della vista aree: una sola per nome di zona
    dati = cartella / "data" / "processed" / "risultato6_v2" / "mappa_r6.json"
    if dati.exists():
        aree = json.loads(dati.read_text(encoding="utf-8"))["aree"]
        nomi = [a["etichetta"] for a in aree if a.get("mostra_etichetta")]
        ripetuti = sorted({n for n in nomi if nomi.count(n) > 1})
        print(f"  etichette della vista aree: {len(nomi)} (con nome ripetuto: {ripetuti or 'nessuno'})")
        if ripetuti:
            errori.append(f"etichette ripetute nella vista aree: {ripetuti}")
    # pesi dei file in git (piano 2, passo 5): nessun file sopra 50 MB, totale sotto 300 MB
    try:
        import controlla_pesi_git
        err_pesi, avv_pesi, tot_pesi, n_pesi = controlla_pesi_git.controlla(RADICE)
        print(f"  pesi in git: {n_pesi} file, {tot_pesi / 1e6:.1f} MB, {len(avv_pesi)} avvisi, {len(err_pesi)} errori")
        errori += [f"pesi in git: {e}" for e in err_pesi]
    except Exception as e:     # git assente o cartella senza git: non e' un errore delle pagine
        print(f"  pesi in git: non controllati ({str(e)[:80]})")
    if assenti_tot:
        print("\nfile assente (non è un errore del codice; senza data/ è normale):")
        for f, dove in sorted(assenti_tot.items()):
            print(f"  - {f}  (cercato da: {', '.join(dict.fromkeys(dove))})")
    if errori:
        print("\nERRORI:")
        for e in errori:
            print("  - " + e)
        return 1
    print(f"\nOK: nessun errore a runtime sulle {len(pagine)} pagine")
    return 0


if __name__ == "__main__":
    sys.exit(main())
