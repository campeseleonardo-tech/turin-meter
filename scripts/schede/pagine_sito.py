"""Parti comuni delle pagine del sito: intestazione (meta e social), barra in alto e piede.

Le pagine index.html, progetto.html e 404.html hanno, fra segnaposto, tre blocchi che scrive questo modulo, cosi' sono uguali
in tutte le pagine e nelle tre lingue (IT, EN, DE):
  <!--SITO:TESTA-->  ...  <!--/SITO:TESTA-->    titolo, descrizione, icone, canonical, Open Graph e Twitter
  <!--SITO:BARRA-->  ...  <!--/SITO:BARRA-->    barra in alto: marchio, pagine, bottoni della lingua
  <!--SITO:PIEDE-->  ...  <!--/SITO:PIEDE-->    piede: autore, contatti, avvertenza, periodo dei dati, fonti e licenze, licenza, GitHub
Il testo fisso ha l'italiano dentro l'elemento e le altre lingue in data-en e data-de (li legge assets/sito.js).
Lo richiama schede_risultati.main(); il testo di ogni blocco sta solo qui."""
import html

from comuni import NOME_SITO, REPO_URL, SITO_URL
from schede.comune import RADICE

LINKEDIN = "https://www.linkedin.com/in/leocampese/"
EMAIL = "campese.leonardo@gmail.com"
FONTI_LICENZE = REPO_URL + "/blob/main/DATA_LICENSES.md"

PAYOFF = {"it": "Come si muove Torino: misurato, calcolato, analizzato.", "en": "How Turin moves: measured, calculated, analysed.",
          "de": "Wie sich Turin bewegt: gemessen, berechnet, analysiert."}
AVVERTENZA = {
    "it": "Progetto personale e indipendente: non è affiliato né approvato da GTT, 5T, Città di Torino o dagli altri enti citati.",
    "en": "Independent personal project: not affiliated with or endorsed by GTT, 5T, the City of Turin or any other organisation mentioned.",
    "de": "Unabhängiges privates Projekt: nicht verbunden mit oder unterstützt von GTT, 5T, der Stadt Turin oder anderen genannten Organisationen.",
}

# pagina -> (file, titolo, descrizione); titolo e descrizione in (it, en, de)
PAGINE = {
    "index": ("index.html",
              (NOME_SITO + " — " + PAYOFF["it"], NOME_SITO + " — " + PAYOFF["en"], NOME_SITO + " — " + PAYOFF["de"]),
              ("Ritardi di bus e tram, auto contro mezzi pubblici, fragilità e servizi, parcheggi di scambio: dati aperti di Torino, raccolti ogni minuto.",
               "Bus and tram delays, car versus public transport, social vulnerability and services, park-and-ride: open data from Turin, collected every minute.",
               "Verspätungen von Bus und Tram, Auto gegen öffentlichen Verkehr, soziale Benachteiligung und Einrichtungen, Park-and-Ride: offene Daten aus Turin, jede Minute erfasst.")),
    "progetto": ("progetto.html",
                 ("Il progetto — " + NOME_SITO, "Case study — " + NOME_SITO, "Fallstudie — " + NOME_SITO),
                 ("Perché questo progetto, come funziona e quanto ci si può fidare dei dati: la tesi del 2020 era la promessa, questo progetto è la verifica sui dati veri di Torino.",
                  "Why this project, how it works and how far the data can be trusted: the 2020 thesis was the promise, this project is the check on real data from Turin.",
                  "Warum dieses Projekt, wie es funktioniert und wie weit man den Daten trauen kann: die Abschlussarbeit von 2020 war das Versprechen, dieses Projekt ist die Überprüfung an echten Daten aus Turin.")),
    "404": ("404.html",
            ("Pagina non trovata — " + NOME_SITO, "Page not found — " + NOME_SITO, "Seite nicht gefunden — " + NOME_SITO),
            ("", "", "")),
}
NAV = [  # (pagina, file, it, en, de)
    ("index", "index.html", "Home", "Home", "Start"),
    ("mappa", "mappa_torino.html", "Mappa", "Map", "Karte"),
    ("progetto", "progetto.html", "Il progetto", "Case study", "Fallstudie"),
]
LINGUE = (("it", "IT", "Italiano"), ("en", "EN", "English"), ("de", "DE", "Deutsch"))
# GitHub Pages serve la 404 a qualsiasi indirizzo sbagliato, anche in sottocartelle: i percorsi si calcolano dalla cartella del sito (su github.io: il nome del repository)
BASE_404 = """<script>
(function(){
  var b = "/";
  if(/\\.github\\.io$/.test(location.hostname)){ var p = location.pathname.split("/")[1]; if(p) b = "/" + p + "/"; }
  document.write('<base href="' + b + '">');
})();
</script>"""
LOCALE = {"it": "it_IT", "en": "en_GB", "de": "de_DE"}


def a(testo):
    return html.escape(testo, quote=True)


def tri(testi, tag=""):
    """Attributi di un elemento di testo fisso: l'italiano va dentro l'elemento, data-en e data-de qui."""
    return f' data-en="{a(testi[1])}" data-de="{a(testi[2])}"'


def etichetta(testi):
    return f'aria-label="{a(testi[0])}" data-en-label="{a(testi[1])}" data-de-label="{a(testi[2])}"'


def testa(chiave):
    """Intestazione: ritorna il testo fra <head> e il foglio di stile."""
    file, titolo, desc = PAGINE[chiave]
    righe = [f'<title{tri(titolo)}>{html.escape(titolo[0])}</title>']
    if chiave == "404":
        righe.append('<meta name="robots" content="noindex">')
        righe.append('<meta name="theme-color" content="#0b2559">')
        righe.append(BASE_404)
        righe.append('<link rel="icon" href="assets/icona-32.png" sizes="32x32" type="image/png">')
        return "\n".join(righe)
    url = SITO_URL + ("" if chiave == "index" else file)
    img = SITO_URL + "assets/anteprima-en.png"   # anteprima social in inglese (decisione di Leo, 26/10/2026): LinkedIn la mostra a tutti
    righe += [
        f'<meta name="description" content="{a(desc[0])}">',
        '<meta name="theme-color" content="#0b2559">',
        '<link rel="icon" href="assets/icona-32.png" sizes="32x32" type="image/png">',
        '<link rel="apple-touch-icon" href="assets/icona-180.png">',
        f'<link rel="canonical" href="{url}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{a(NOME_SITO)}">',
        f'<meta property="og:locale" content="{LOCALE["en"]}">',
        f'<meta property="og:locale:alternate" content="{LOCALE["it"]}">',
        f'<meta property="og:locale:alternate" content="{LOCALE["de"]}">',
        f'<meta property="og:title" content="{a(titolo[1])}">',
        f'<meta property="og:description" content="{a(desc[1])}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{img}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{a(titolo[1])}">',
        f'<meta name="twitter:description" content="{a(desc[1])}">',
        f'<meta name="twitter:image" content="{img}">',
    ]
    return "\n".join(righe)


def barra(chiave):
    voci = "".join(
        f'<a href="{f}"' + (' aria-current="page"' if p == chiave else "") + f'{tri((it, en, de))}>{it}</a>'
        for p, f, it, en, de in NAV)
    bottoni = "".join(
        f'<button type="button" data-l="{l}" aria-pressed="{"true" if l == "it" else "false"}" title="{t}">{s}</button>' for l, s, t in LINGUE)
    return (f'<header class="barra-alta"><div class="dentro">\n'
            f'  <a class="marchio" href="index.html"><img src="assets/logo.svg" alt="" width="34" height="34">{a(NOME_SITO)}</a>\n'
            f'  <nav {etichetta(("Pagine del sito", "Site pages", "Seiten der Website"))}>{voci}</nav>\n'
            f'  <div class="lingua" role="group" {etichetta(("Lingua", "Language", "Sprache"))}>{bottoni}</div>\n'
            f'</div></header>')


def piede():
    chi = ("Chi sono", "About me", "Über mich")
    lic = ("Codice con licenza MIT; i dati hanno la licenza della loro fonte.",
           "Code under the MIT licence; data keep the licence of their source.",
           "Code unter MIT-Lizenz; die Daten behalten die Lizenz ihrer Quelle.")
    fonti = ("Fonti e licenze", "Sources and licences", "Quellen und Lizenzen")
    return (f'<footer class="piede"><div class="dentro">\n'
            f'  <div>\n'
            f'    <h2{tri(chi)}>{chi[0]}</h2>\n'
            f'    <p>Leonardo Campese</p>\n'
            f'    <p><a href="{LINKEDIN}">LinkedIn</a> · <a href="mailto:{EMAIL}">{EMAIL}</a> · <a href="{REPO_URL}">GitHub</a></p>\n'
            f'    <p class="piccolo"><a href="{FONTI_LICENZE}"{tri(fonti)}>{fonti[0]}</a></p>\n'
            f'  </div>\n'
            f'  <div>\n'
            f'    <p class="piccolo avvertenza"{tri((AVVERTENZA["it"], AVVERTENZA["en"], AVVERTENZA["de"]))}>{html.escape(AVVERTENZA["it"])}</p>\n'
            f'    <p class="piccolo" id="datiAggiornati">Dati dal … al …</p>\n'
            f'    <p class="piccolo"{tri(lic)}>{lic[0]}</p>\n'
            f'  </div>\n'
            f'</div></footer>')


def sostituisci(testo, nome, blocco):
    """Riscrive il testo fra <!--SITO:nome--> e <!--/SITO:nome-->. Ritorna il testo nuovo (uguale se il segnaposto manca)."""
    ini, fin = f"<!--SITO:{nome}-->", f"<!--/SITO:{nome}-->"
    i, f = testo.find(ini), testo.find(fin)
    if i < 0 or f < i:
        raise ValueError(f"segnaposto {ini} mancante")
    return testo[:i + len(ini)] + "\n" + blocco + "\n" + testo[f:]


def scrivi_pagine_sito():
    """Aggiorna i tre blocchi in ogni pagina. Ritorna quante pagine sono cambiate."""
    cambiate = 0
    for chiave, (file, _t, _d) in PAGINE.items():
        p = RADICE / file
        grezzo = p.read_bytes().decode("utf-8")
        crlf = "\r\n" in grezzo
        testo = grezzo.replace("\r\n", "\n")
        nuovo = sostituisci(testo, "TESTA", testa(chiave))
        nuovo = sostituisci(nuovo, "BARRA", barra(chiave))
        nuovo = sostituisci(nuovo, "PIEDE", piede())
        if nuovo != testo:
            p.write_bytes((nuovo.replace("\n", "\r\n") if crlf else nuovo).encode("utf-8"))
            cambiate += 1
    return cambiate
