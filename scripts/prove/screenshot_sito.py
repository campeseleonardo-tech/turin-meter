#!/usr/bin/env python3
"""Screenshot del sito (home, risultati, schede aperte, mappa) con Playwright: computer 1440x900 e telefono 390x844, chiaro e scuro,
con animazioni normali e con «riduci movimento». Controlla anche errori JavaScript, richieste esterne e scorrimento orizzontale.
Uso: python scripts/prove/screenshot_sito.py [CARTELLA_USCITA]   (default sviluppo/c5_screenshot)"""
import glob
import http.server
import os
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

RADICE = Path(__file__).resolve().parent.parent.parent
USCITA = Path(sys.argv[1]) if len(sys.argv) > 1 else RADICE / "sviluppo" / "c5_screenshot"
PORTA = 8821
PAGINE = [("home", "index.html", None),
          ("scheda1", "index.html#p1", "#finestra[open]"), ("scheda2", "index.html#p2", "#finestra[open]"),
          ("scheda3", "index.html#p3", "#finestra[open]"), ("scheda4", "index.html#p4", "#finestra[open]"), ("mappa", "mappa_torino.html#tema=vulnerabilita", None),
          ("progetto", "progetto.html", None)]


def main():
    USCITA.mkdir(parents=True, exist_ok=True)
    os.chdir(RADICE)
    socketserver.TCPServer.allow_reuse_address = True

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = socketserver.TCPServer(("127.0.0.1", PORTA), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    cand = sorted(glob.glob(os.path.join(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"), "chromium-*", "chrome-linux", "chrome")))
    problemi = []
    with sync_playwright() as p:
        try:
            br = p.chromium.launch()
        except Exception:
            br = p.chromium.launch(executable_path=cand[-1])
        for disp, (w, h) in (("computer", (1440, 900)), ("telefono", (390, 844))):
            for tema in ("chiaro", "scuro"):
                for mov in ("normale", "ridotto"):
                    if mov == "ridotto" and not (disp == "computer" and tema == "chiaro"):
                        continue          # «riduci movimento» provato solo su computer chiaro (le pagine sono le stesse)
                    ctx = br.new_context(viewport={"width": w, "height": h}, color_scheme="dark" if tema == "scuro" else "light",
                                         reduced_motion="reduce" if mov == "ridotto" else "no-preference")
                    for nome, url, attesa in PAGINE:
                        if nome == "mappa" and disp == "telefono" and tema == "scuro":
                            continue
                        if disp == "telefono" and tema == "scuro" and nome not in ("home", "scheda5"):
                            continue          # basta una prova scura su telefono (home e una scheda)
                        if mov == "ridotto" and nome not in ("home", "scheda5"):
                            continue
                        pg = ctx.new_page()
                        esterne, errori = [], []
                        pg.on("request", lambda r: esterne.append(r.url) if r.url.startswith("http") and f":{PORTA}" not in r.url and "arcgisonline" not in r.url else None)
                        pg.on("pageerror", lambda e: errori.append(str(e)[:200]))
                        pg.goto(f"http://127.0.0.1:{PORTA}/{url}", wait_until="load")
                        if attesa:
                            pg.wait_for_selector(attesa, timeout=5000)
                        pg.wait_for_timeout(2600 if nome == "mappa" else 1600)
                        larg = pg.evaluate("document.documentElement.scrollWidth")
                        if nome != "mappa" and larg > w + 1:
                            problemi.append(f"{nome} {disp} {tema}: scorrimento orizzontale {larg}>{w}")
                        if errori:
                            problemi.append(f"{nome} {disp} {tema} {mov}: errori JS {errori[:2]}")
                        if esterne:
                            problemi.append(f"{nome} {disp} {tema}: richieste esterne {esterne[:2]}")
                        nome_file = f"{nome}_{disp}_{tema}" + ("_riduci_movimento" if mov == "ridotto" else "")
                        pg.screenshot(path=str(USCITA / (nome_file + ".jpg")), type="jpeg", quality=80,
                                      full_page=nome not in ("mappa", "scheda5", "scheda2", "scheda3"))
                        pg.close()
                    ctx.close()
        # versione inglese (il browser in inglese la sceglie da solo): home, risultati e schede su computer e telefono, chiaro
        for disp, (w, h) in (("computer", (1440, 900)), ("telefono", (390, 844))):
            ctx = br.new_context(viewport={"width": w, "height": h}, locale="en-GB", color_scheme="light")
            for nome, url, attesa in PAGINE:
                if nome in ("mappa", "progetto"):
                    continue
                pg = ctx.new_page()
                errori = []
                pg.on("pageerror", lambda e: errori.append(str(e)[:200]))
                pg.goto(f"http://127.0.0.1:{PORTA}/{url}", wait_until="load")
                if attesa:
                    pg.wait_for_selector(attesa, timeout=5000)
                pg.wait_for_timeout(1600)
                if pg.evaluate("document.documentElement.lang") != "en":
                    problemi.append(f"{nome} {disp}: la pagina non e' in inglese")
                if pg.evaluate("document.documentElement.scrollWidth") > w + 1:
                    problemi.append(f"{nome} {disp} EN: scorrimento orizzontale")
                if errori:
                    problemi.append(f"{nome} {disp} EN: errori JS {errori[:2]}")
                pg.screenshot(path=str(USCITA / f"{nome}_{disp}_chiaro_EN.jpg"), type="jpeg", quality=80,
                              full_page=nome not in ("scheda5", "scheda2", "scheda3"))
                pg.close()
            ctx.close()
        br.close()
    srv.shutdown()
    for x in problemi:
        print("PROBLEMA:", x)
    print(f"{len(list(USCITA.glob('*.jpg')))} immagini in {USCITA}")
    print("OK" if not problemi else "CI SONO PROBLEMI")
    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())
