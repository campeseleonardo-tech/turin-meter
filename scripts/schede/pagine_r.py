"""Pagine di condivisione e elenchi dei risultati nei README.

Pagine minime (titolo, descrizione e immagine di anteprima Open Graph, per i post su LinkedIn e simili) che rimandano subito al sito:
  r/N.html, r/en/N.html, r/de/N.html    un risultato, nella lingua della cartella: rimando a index.html#pN (con ?lang= per EN e DE)
  en/index.html, de/index.html          la home in inglese e in tedesco: rimando a index.html?lang=...
Le immagini 1200x630 (assets/anteprime/{it,en,de}/rN.jpg, assets/anteprima-{it,en,de}.png) le fanno scripts/prova_pagine.py e
scripts/costruisci_asset_sito.py dai dati della scheda. I file di una scheda che non c'e' piu' (o nascosta) si cancellano.
I README hanno un elenco dei risultati fra i segnaposto <!-- RISULTATI-IT:INIZIO --> ... <!-- RISULTATI-IT:FINE --> (e lo stesso con EN e DE):
li riscrive questo modulo, cosi' i numeri non invecchiano. Nessun numero e' scritto a mano."""
import html
import json
import re

from comuni import NOME_SITO, SITO_URL
from schede.comune import RADICE
from schede.pagine_sito import LOCALE, PAGINE, PAYOFF

SITO = SITO_URL
LINGUE = ("it", "en", "de")
CARTELLA = RADICE / "r"
README = [RADICE / "README.md", RADICE / "README.it.md", RADICE / "README.de.md"]
INDICE = {"it": 0, "en": 1, "de": 2}

PAGINA = """<!doctype html>
<html lang="{lingua}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titolo} — {sito}</title>
<meta name="description" content="{descrizione}">
<meta name="theme-color" content="#0b2559">
<link rel="icon" href="{su}assets/icona-32.png" sizes="32x32" type="image/png">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{tipo}">
<meta property="og:site_name" content="{sito}">
<meta property="og:locale" content="{locale}">
<meta property="og:title" content="{titolo}">
<meta property="og:description" content="{descrizione}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{immagine}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{titolo}">
<meta name="twitter:description" content="{descrizione}">
<meta name="twitter:image" content="{immagine}">
<meta http-equiv="refresh" content="0; url={dest}">
<link rel="stylesheet" href="{su}assets/stile.css">
</head>
<body>
<main>
<p class="sub">{sito} · {etichetta}</p>
<h1>{titolo}</h1>
<p class="sub">{descrizione}</p>
<p><a class="btn primario" href="{dest}">{bottone}</a></p>
</main>
<script>location.replace("{dest}");</script>
</body>
</html>
"""
ETICHETTA = {"it": "Risultato {n}", "en": "Finding {n}", "de": "Ergebnis {n}"}
BOTTONE = {"it": "Apri il risultato", "en": "Open the finding", "de": "Ergebnis öffnen"}
BOTTONE_HOME = {"it": "Apri il sito", "en": "Open the site", "de": "Website öffnen"}
APRI = {"it": "Apri", "en": "Open", "de": "Öffnen"}


def forma_in(s, lingua):
    """La forma della scheda nella lingua, con ripiego sull'inglese e poi sull'italiano."""
    if lingua == "it":
        return s["forma"]
    return s.get("forma_" + lingua) or s.get("forma_en") or s["forma"]


def _grande(f, lingua):
    """Numero grande della scheda come testo: «99,2%», «2–3 volte», «79.598»."""
    n = f["numero"]
    v = n["valore"]
    if isinstance(v, int):
        v = f"{v:,}".replace(",", "," if lingua == "en" else ".")
    elif isinstance(v, float):
        if n["unita"] == "%":
            v = round(v, 1)      # misurati: un decimale (§5.9 del piano)
        v = f"{v:g}" if lingua == "en" else f"{v:g}".replace(".", ",")
    return f"{v}%" if n["unita"] == "%" else f"{v} {n['unita']}".strip()


def _pagina(lingua, titolo, descrizione, url, immagine, dest, etichetta, bottone, tipo, profondita):
    """Il testo di una pagina di condivisione; profondita = quante cartelle sopra la radice del sito."""
    return PAGINA.format(lingua=lingua, titolo=html.escape(titolo, quote=True), descrizione=html.escape(descrizione, quote=True), sito=NOME_SITO,
                         su="../" * profondita, url=url, immagine=immagine, dest=dest, etichetta=etichetta, bottone=bottone, tipo=tipo,
                         locale=LOCALE[lingua])


def _scrivi(percorso, testo, scritti):
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(testo, encoding="utf-8")
    scritti.add(percorso)


def scrivi_pagine_r(schede):
    """Una pagina per ogni scheda con numero pubblico e forma, in ogni lingua, e le due home en/ e de/. Ritorna quante pagine ha scritto."""
    scritti = set()
    for s in schede:
        n = s.get("numero_pubblico")
        if n is None or not s.get("forma"):
            continue
        for lingua in LINGUE:
            f = forma_in(s, lingua)
            cartella = CARTELLA if lingua == "it" else CARTELLA / lingua
            profondita = 1 if lingua == "it" else 2
            q = "" if lingua == "it" else f"?lang={lingua}"
            testo = _pagina(lingua, f["titolo"], f["domanda"], url=f"{SITO}r/{n}.html" if lingua == "it" else f"{SITO}r/{lingua}/{n}.html",
                            immagine=f"{SITO}assets/anteprime/{lingua}/r{n}.jpg", dest=f"{'../' * profondita}index.html{q}#p{n}",
                            etichetta=ETICHETTA[lingua].format(n=n), bottone=BOTTONE[lingua], tipo="article", profondita=profondita)
            _scrivi(cartella / f"{n}.html", testo, scritti)
    for lingua in ("en", "de"):
        i = INDICE[lingua]
        _file, titolo, desc = PAGINE["index"]
        testo = _pagina(lingua, titolo[i], desc[i], url=f"{SITO}{lingua}/", immagine=f"{SITO}assets/anteprima-{lingua}.png", dest=f"../index.html?lang={lingua}",
                        etichetta=PAYOFF[lingua], bottone=BOTTONE_HOME[lingua], tipo="website", profondita=1)
        _scrivi(RADICE / lingua / "index.html", testo, scritti)
    for p in list(CARTELLA.glob("*.html")) + list(CARTELLA.glob("*/*.html")):      # pagine di schede che non ci sono piu'
        if p not in scritti:
            p.unlink()
    return len(scritti)


def _elenco(schede, lingua):
    righe = []
    for s in sorted((x for x in schede if x.get("numero_pubblico") is not None and x.get("forma")), key=lambda x: x["numero_pubblico"]):
        f = forma_in(s, lingua)
        n = s["numero_pubblico"]
        url = f"{SITO}index.html{'' if lingua == 'it' else '?lang=' + lingua}#p{n}"   # la scheda si apre sopra la home (le pagine r/… servono alle anteprime sui social)
        righe.append(f"{n}. **{f['titolo']}**  \n   {f['domanda']} → **{_grande(f, lingua)}** {f['numero']['testo'].rstrip('.')}. [{APRI[lingua]}]({url})")
    return "\n".join(righe)


IN_NUMERI = {
    "it": "- **~{passaggi} milioni** di passaggi alle fermate misurati col GPS · **{sensori}** sensori del traffico · **{sezioni}** sezioni di censimento · **~{fonti}** fonti di dati aperti\n"
          "- **{settimane}** settimane di lavoro · **{commit}** versioni tracciate",
    "en": "- **~{passaggi} million** stop departures measured by GPS · **{sensori}** traffic sensors · **{sezioni}** census sections · **~{fonti}** open data sources\n"
          "- **{settimane}** weeks of work · **{commit}** tracked versions",
    "de": "- **~{passaggi} Mio.** per GPS gemessene Abfahrten an Haltestellen · **{sensori}** Verkehrssensoren · **{sezioni}** Zählsprengel · **~{fonti}** offene Datenquellen\n"
          "- **{settimane}** Wochen Arbeit · **{commit}** nachvollziehbare Versionen",
}


def _in_numeri(lingua):
    """Il blocco «In numeri» dei README, dai dati di data/progetto.js (campo in_numeri); None se il file non c'e'."""
    f = RADICE / "data" / "progetto.js"
    if not f.is_file():
        return None
    n = json.loads(f.read_text(encoding="utf-8").split("window.PROGETTO = ", 1)[1].rstrip().rstrip(";"))["in_numeri"]
    def fmt(x):
        return f"{x:,}".replace(",", "," if lingua == "en" else ".")
    def dec(x):
        return f"{x:g}" if lingua == "en" else f"{x:g}".replace(".", ",")
    return IN_NUMERI[lingua].format(passaggi=dec(round(n["passaggi"] / 1e5) / 10), sensori=fmt(n["sensori"]), sezioni=fmt(n["sezioni"]),
                                    fonti=fmt(n["fonti"]), settimane=fmt(n["settimane"]), commit=fmt(n["commit"]))


def aggiorna_readme(schede):
    """Riscrive gli elenchi dei risultati dei README fra i segnaposto (README.md, README.it.md, README.de.md, quelli che ci sono).
    Ritorna True se almeno un README e' cambiato."""
    cambiato = False
    for file in README:
        if not file.is_file():
            continue
        testo = vecchio = file.read_text(encoding="utf-8")
        trovati = 0
        for lingua in LINGUE:
            sigla = lingua.upper()
            for blocco, contenuto in (("RISULTATI", _elenco(schede, lingua)), ("IN-NUMERI", _in_numeri(lingua))):
                rx = re.compile(rf"(<!-- {blocco}-{sigla}:INIZIO -->)\n.*?(<!-- {blocco}-{sigla}:FINE -->)", re.S)
                if rx.search(testo) and contenuto is not None:
                    trovati += 1
                    testo = rx.sub(lambda m: m.group(1) + "\n" + contenuto + "\n" + m.group(2), testo)
        if not trovati:
            print(f"AVVISO: {file.name} senza i segnaposto RISULTATI-IT / -EN / -DE")
        if testo != vecchio:
            file.write_text(testo, encoding="utf-8", newline="\n")
            cambiato = True
    return cambiato
