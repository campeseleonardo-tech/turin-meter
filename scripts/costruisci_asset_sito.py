#!/usr/bin/env python3
"""
costruisci_asset_sito.py  -  immagini del sito nello stile «Torino»: assets/anteprima-it.png, -en.png e -de.png (1200x630, per l'anteprima dei link: marchio Turin Meter e tre numeri dai dati).
Le icone (logo.svg, logo-64.png, icona-32.png, icona-180.png, icona-512.png) vengono dal logo e non si rifanno qui.

Usa i numeri veri di data/schede_risultati.js e le sezioni di Torino dentro mappa_torino.html (fragilita' sociale), il font Barlow Condensed
di assets/font/ e Playwright (Chromium). Uso: python scripts/costruisci_asset_sito.py
Scrive: assets/anteprima-it.png, assets/anteprima-en.png, assets/anteprima-de.png.
"""
import glob
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
RADICE = AQUI.parent
sys.path.insert(0, str(AQUI))
from schede.pagine_sito import PAYOFF  # noqa: E402
# ruoli della palette «Torino» scura usata per le immagini del sito (valori di assets/stile.css)
PALETTE = {"torino": {"scuro": dict(bene="#32cfc2", male="#ee6a80", mid="#34507f")}}


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def a_oklab(h):
    r, g, b = (lin(x) for x in rgb(h))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def da_oklab(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    def gam(c):
        c = max(0.0, min(1.0, c))
        return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return "#" + "".join(f"{round(gam(x) * 255):02x}" for x in (r, g, bb))


def mescola(h1, h2, t):
    a, b = a_oklab(h1), a_oklab(h2)
    return da_oklab(*(x + (y - x) * t for x, y in zip(a, b)))


def scala(p):
    """5 classi dal verde acqua (bene) al corallo (male), passando dal grigio neutro: 0 = bene ... 4 = male."""
    return [p["bene"], mescola(p["bene"], p["mid"], 0.55), p["mid"], mescola(p["mid"], p["male"], 0.45), p["male"]]


def carica_dati():
    t = (RADICE / "data" / "schede_risultati.js").read_text(encoding="utf-8")
    schede = json.loads(t[t.index("["):t.rindex("]") + 1])
    scheda = next(s for s in schede if s["risultato"] == "10")
    spec = importlib.util.spec_from_file_location("g04", RADICE / "scripts" / "04_genera_mappa.py")
    g04 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g04)
    riga = next(x for x in (RADICE / "mappa_torino.html").read_text(encoding="utf-8").split("\n") if x.startswith("const DATI = "))
    D = json.loads(riga[len("const DATI = "):].rstrip(";"))
    return scheda, D["sezioni"], g04


def mappa_svg(S, g04, soglie_out):
    """Sezioni di Torino colorate per classe di fragilita' (quintili); path relativi in interi. Ritorna (svg interno, larghezza, altezza)."""
    idx = [i for i in range(S["n"]) if S["c"][i] == 1272 and S["v"][i] is not None and S["p"][i] and S["g"][i]]
    valori = sorted(S["v"][i] for i in idx)
    soglie = [valori[int(len(valori) * q)] for q in (0.2, 0.4, 0.6, 0.8)]
    soglie_out.extend(soglie)
    anelli = {}
    lat_min = lon_min = 1e9
    lat_max = lon_max = -1e9
    for i in idx:
        poligoni = []
        for r in S["g"][i].split(" "):
            n = g04.decod_int(r)
            la = lo = 0
            pts = []
            for k in range(0, len(n), 2):
                la += n[k]
                lo += n[k + 1]
                pts.append((la / 1e4, lo / 1e4))
            poligoni.append(pts)
            for la_, lo_ in pts:
                lat_min, lat_max = min(lat_min, la_), max(lat_max, la_)
                lon_min, lon_max = min(lon_min, lo_), max(lon_max, lo_)
        anelli[i] = poligoni
    k = math.cos(math.radians((lat_min + lat_max) / 2))
    larg = 900
    scala_ = larg / ((lon_max - lon_min) * k)
    alt = round((lat_max - lat_min) * scala_)
    percorsi = [[] for _ in range(5)]
    for i in idx:
        c = sum(S["v"][i] > s for s in soglie)
        d = []
        for pts in anelli[i]:
            xy = [(round((lo - lon_min) * k * scala_), round((lat_max - la) * scala_)) for la, lo in pts]
            sempl = [xy[0]]
            for p in xy[1:]:
                if p != sempl[-1]:
                    sempl.append(p)
            if len(sempl) < 3:
                continue
            d.append("M" + str(sempl[0][0]) + " " + str(sempl[0][1]) + "".join(f"l{x - px} {y - py}" for (px, py), (x, y) in zip(sempl, sempl[1:])) + "z")
        percorsi[c].append("".join(d))
    svg = "".join(f'<path class="c{c}" d="{"".join(p)}"/>' for c, p in enumerate(percorsi))
    return svg, larg, alt


def numeri(lingua):
    """I numeri grandi delle schede in pagina, nella lingua: [(numero con unita', frase breve)]. Inglese 1,234.5; italiano e tedesco 1.234,5."""
    t = (RADICE / "data" / "schede_risultati.js").read_text(encoding="utf-8")
    schede = json.loads(t[t.index("["):t.index("window.SCHEDE_PERIODO")].rstrip().rstrip(";"))
    out = []
    for s in sorted(schede, key=lambda x: x.get("numero_pubblico") or 99):
        f = s["forma"] if lingua == "it" else (s.get("forma_" + lingua) or s.get("forma_en") or s["forma"])
        n = f["numero"]
        v = n["valore"]
        if isinstance(v, int):
            txt = f"{v:,}".replace(",", "," if lingua == "en" else ".")
        else:
            txt = str(round(v, 1) if isinstance(v, float) and n["unita"] == "%" else v).replace(".", "." if lingua == "en" else ",")   # misurati: un decimale
        out.append((txt + ("%" if n["unita"] == "%" else (" " + n["unita"] if n["unita"] else "")), n.get("breve") or n["testo"]))
    return out


def pagina(lingua):
    scheda, S, g04 = carica_dati()
    soglie = []
    svg, W, H = mappa_svg(S, g04, soglie)
    p = PALETTE["torino"]["scuro"]
    sc = scala(p)
    css_sc = "".join(f".c{i}{{fill:{c}}}" for i, c in enumerate(sc))
    righe = "".join(f'<div class="n"><b>{v}</b><span>{d}</span></div>' for v, d in numeri(lingua)[:3])      # le tre schede della vetrina
    logo = (RADICE / "assets" / "logo.svg").as_uri()
    font = (RADICE / "assets" / "font").as_uri()
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:BC;font-weight:700;src:url({font}/BarlowCondensed-700.woff2)}}
@font-face{{font-family:BC;font-weight:600;src:url({font}/BarlowCondensed-600.woff2)}}
@font-face{{font-family:B;font-weight:400;src:url({font}/Barlow-400.woff2)}}
@font-face{{font-family:B;font-weight:600;src:url({font}/Barlow-600.woff2)}}
*{{box-sizing:border-box;margin:0}}
body{{width:1200px;height:630px;background:linear-gradient(135deg,#08142e 0%,#0b2559 100%);color:#f1f4fb;font:400 26px/1.3 B;position:relative;overflow:hidden}}
.oro{{position:absolute;left:0;right:0;top:0;height:10px;background:#e3bf55}}
.testo{{position:absolute;left:64px;top:122px;width:640px}}
h1{{font:700 118px/0.92 BC;text-transform:uppercase;letter-spacing:.01em}}
h1 em{{font-style:normal;color:#e3bf55}}
.sotto{{margin-top:22px;font-size:28px;line-height:1.25;color:#c8d2ea;max-width:600px}}
.nums{{position:absolute;left:64px;bottom:44px;display:flex;gap:40px}}
.n b{{display:block;font:700 54px/1 BC;color:#e3bf55}}
.n span{{display:block;font-size:18px;color:#a8b5d1;max-width:300px;line-height:1.25;margin-top:4px}}
.logo{{position:absolute;left:64px;top:26px;width:auto;height:78px}}
.mappa{{position:absolute;right:40px;top:50px;width:470px;height:{round(470 * H / W)}px}}
{css_sc}
</style></head><body><div class="oro"></div>
<img class="logo" src="{logo}" alt=""><div class="testo"><h1>Turin<br><em>Meter</em></h1><div class="sotto">{PAYOFF[lingua]}</div></div>
<svg class="mappa" viewBox="0 0 {W} {H}"><g>{svg}</g></svg>
<div class="nums">{righe}</div></body></html>"""


def main():
    cand = sorted(glob.glob(os.path.join(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"), "chromium-*", "chrome-linux*", "chrome")))
    html = RADICE / "assets" / "_anteprima_tmp.html"
    try:
        with sync_playwright() as pw:
            try:
                br = pw.chromium.launch()
            except Exception:
                br = pw.chromium.launch(executable_path=cand[-1])
            pg = br.new_page(viewport={"width": 1200, "height": 630})
            for lingua in ("it", "en", "de"):
                html.write_text(pagina(lingua), encoding="utf-8")
                pg.goto(html.as_uri())
                pg.evaluate("document.fonts.ready")
                pg.wait_for_timeout(500)
                pg.screenshot(path=str(RADICE / "assets" / f"anteprima-{lingua}.png"))
            br.close()
    finally:
        html.unlink(missing_ok=True)
    for lingua in ("it", "en", "de"):
        n = f"anteprima-{lingua}.png"
        print(n, (RADICE / "assets" / n).stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
