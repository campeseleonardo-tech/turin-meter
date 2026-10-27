"""Funzioni e costanti comuni delle schede dei risultati (percorsi, lettura dei JSON, formati dei numeri, forma base delle schede)."""
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
import json
import re



RADICE = Path(__file__).resolve().parent.parent.parent


PROC = RADICE / "data" / "processed"


DOCS = RADICE / "docs"


OUT_JS = RADICE / "data" / "schede_risultati.js"




def leggi(nome):
    return json.loads((PROC / nome).read_text(encoding="utf-8"))


def ore_del_giorno():
    """I risultati dello script 100 (bus contro auto a 4 ore del giorno), oppure None se mancano o sono di prova/campione:
    le schede 3 e 4 restano allora solo alle 8."""
    f = PROC / "ore_del_giorno.json"
    if not f.is_file():
        return None
    d = json.loads(f.read_text(encoding="utf-8"))
    return None if (d.get("prova") or d.get("campione")) else d




def num(label, dopo, unita, prima=None):
    return {"label": label, "prima": prima, "dopo": dopo, "unita": unita}




def voce(label, valore, prima=None, tono=None, link=None):
    v = {"label": label, "valore": valore}
    if link is not None:   # la barra e' un link (es. alla linea nella mappa)
        v["link"] = link
    if prima is not None:
        v["prima"] = prima
    if tono is not None:   # "verde"/"rosso" = bene/male; senza tono = blu neutro (quantità)
        v["tono"] = tono
    return v




def migliaia(n):
    return f"{n:,}".replace(",", ".")




def virgola(x):
    testo = f"{x:.1f}".replace(".", ",")
    return testo[:-2] if testo.endswith(",0") else testo




def circa(x, unita=""):
    """Numero secondario con il segno «~» davanti, arrotondato all'intero: circa(68.3, "%") -> «~68%», circa(2.4, " volte") -> «~2 volte».
    Un testo gia' scritto prende solo il «~». Il numero grande, i conteggi piccoli e il testo del calcolo restano precisi (niente circa)."""
    if isinstance(x, str):
        return "~" + x
    return "~" + migliaia(round(x)) + unita




def circa_mila(n):
    """Conteggio grande arrotondato: 222179 -> «~222 mila»; sotto i 10.000 resta intero con il «~» (circa(n))."""
    return f"~{migliaia(round(n / 1000))} mila" if n >= 10000 else circa(n)




def minuti_a_parole(x):
    """Minuti arrotondati al mezzo minuto e scritti a parole: 1.6 -> «~1 minuto e mezzo», 0.5 -> «~mezzo minuto», 3 -> «~3 minuti»."""
    m = round(x * 2) / 2
    intero_, mezzo = int(m), (m % 1) > 0
    if intero_ == 0:
        return "~mezzo minuto" if mezzo else "~0 minuti"
    return f"~{intero_} {'minuto' if intero_ == 1 else 'minuti'}" + (" e mezzo" if mezzo else "")




def intero(x):
    """Valore di una barra: intero senza «~» (sotto 1 resta com'e', per non far sparire i valori piccoli)."""
    return round(x) if abs(x) >= 1 else x




TIPO_DATO = {   # una riga nella parte chiusa «Come e' stato calcolato, e limiti»: il tipo di dato, a parole
    "STIMATO": "Tipo di dato: calcolato da dati veri, non misurato direttamente.",
    "MISURATO": "Tipo di dato: misurato, con la posizione GPS dei mezzi.",
    "STIMATO / CENSIMENTO": "Tipo di dato: calcolato da dati veri, con gli abitanti del censimento 2021.",
    "STIMATO / PREZZI": "Tipo di dato: calcolato con prezzi pubblici di ottobre 2026 e con i tempi in auto col traffico tipico.",
    "STIMATO / MISURATO (dati scarsi)": "Tipo di dato: calcolato da dati veri e in parte misurato, su pochi giorni di dati.",
    "STIMATO / MISURATO / PROGRAMMATO": "Tipo di dato: calcolato da dati veri, con tempi in auto col traffico tipico, misure dei sensori e orari ufficiali dei mezzi.",
}




def periodo_it(da, a):
    """«dal 10/10/2026 al 23/10/2026» da due date AAAA-MM-GG (le date dei dati usati, scritte nei JSON)."""
    it = lambda t: f"{t[8:10]}/{t[5:7]}/{t[:4]}"
    return f"dal {it(str(da))} al {it(str(a))}"




def pct2(x):
    """percentuale con due decimali e virgola (per valori piccoli, es. 'oltre 10 minuti')."""
    return f"{x:.2f}".replace(".", ",")




def link_linea(nome):
    """Link dalla scheda alla mappa con quella linea selezionata (tema «Puntualita' delle linee»)."""
    return "mappa_torino.html#tema=puntualita&linea=" + quote(str(nome), safe="") + "&ora=8"   # si apre alle 8 di un feriale




def il(x):
    """articolo davanti a una percentuale: 'il 4,2%', ma 'l'8,3%' e 'l'11%'."""
    testo = virgola(x)
    return ("l'" if testo[0] == "8" or testo.split(",")[0] in ("11", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89") else "il ") + testo




def ora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")




def minuti(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)




def nome_pulito(n):
    """'RIVALTA DI TORINO' -> 'Rivalta di Torino', 'PORTA SUSA FS' -> 'Porta Susa FS'; gli altri nomi restano uguali."""
    if not n.isupper():
        return n
    return n.title().replace(" Di ", " di ").replace(" Fs", " FS")




def date_it(iso_list):
    """['2026-10-15', '2026-10-16'] -> '15/10 e 16/10'"""
    giorni = [d[8:10] + "/" + d[5:7] for d in iso_list]
    if not giorni:
        return "—"
    return giorni[0] if len(giorni) == 1 else ", ".join(giorni[:-1]) + " e " + giorni[-1]




NASCOSTE = {"risultato2"}   # non in pagina: risultato2 in pausa (sviluppo/note_tecniche/R2_metro_notte.md)




# ---------------------------------------------------------------- Forma nuova delle schede
# Ogni scheda ha un campo "forma" con tutto quello che la pagina mostra: tipo di dato (nella parte chiusa), titolo-risposta, domanda in una riga,
# numero grande, grafico principale, 3 punti chiave, e le parti chiuse (altri grafici, calcolo, limiti, inglese).
# I campi vecchi restano nel JSON ma la pagina non li usa. I numeri vengono sempre dai file dei risultati.

PAROLE_VIETATE = re.compile(r"\bLeo\b|\bgiro\b|\bfase\b|\bversione\b|\.py\b|\.json\b|\.md\b|\bIMQ\b|\bQ00\d|\b5T\b|\bGTFS\b", re.I)




def controlla_forma(nome, f):
    """Avvisi sui testi della forma: frasi di oltre 20 parole e parole che non vanno nelle pagine."""
    testi = [f["titolo"], f["domanda"], f["numero"]["testo"], *f["punti"], *f["calcolo"], *f.get("confronto", []),
             *f["limiti"], *(a for a in [f.get("extra", {}).get("punto")] if a)]
    for p in f["punti"]:
        if len(p.split()) > 25:
            print(f"  ATTENZIONE {nome}: punto chiave di {len(p.split())} parole (massimo 25): «{p[:60]}…»")
    for t in testi:
        if PAROLE_VIETATE.search(t):
            print(f"  ATTENZIONE {nome}: parola da togliere in «{t[:60]}»")
        for frase in re.split(r"(?<=[a-zA-ZàèéìòùÀ%)\]»])[.;:] +(?=[A-ZÈÀ])", t):
            if len(frase.split()) > 20:
                print(f"  ATTENZIONE {nome}: frase di {len(frase.split())} parole: «{frase[:70]}…»")
    if not 2 <= len(f["punti"]) <= 3 or len(f["limiti"]) > 5 or len(f["altri"]) > 4 or len(f["calcolo"]) > 8:
        print(f"  ATTENZIONE {nome}: numero di righe fuori misura")




# Fonti di ogni scheda (L21): e' l'unico punto del sito dove compaiono i nomi dei fornitori dei dati; ultima riga della parte chiusa.
FONTI_NOMI = {
    "gtt_orari": "GTT (orari ufficiali)",
    "gtt_gps": "GTT (posizioni GPS dei mezzi, dato in tempo reale e orari ufficiali)",
    "gtt_orari_gps": "GTT (orari ufficiali e posizioni dei mezzi)",
    "comune_servizi": "Comune di Torino (servizi)",
    "comune_parcheggi": "Comune di Torino (parcheggi)",
    "osm": "OpenStreetMap",
    "istat": "ISTAT (censimento 2021)",
    "5t": "5T (sensori del traffico)",
    "imq": "Agenzia della mobilità piemontese (indagine sugli spostamenti 2022)",
    "omi": "Agenzia delle Entrate (quotazioni OMI)",
    "tomtom": "TomTom (controllo dei tempi in auto su 20 percorsi)",
    "carburanti": "Osservatorio prezzi carburanti (Ministero delle imprese e del made in Italy)",
    "aci": "ACI (tabelle dei costi chilometrici 2026)",
    "gtt_tariffe": "GTT (tariffe e sosta)",
}
FONTI_SCHEDA = {   # per numero interno del risultato
    "1": ["comune_servizi", "osm", "istat", "gtt_orari", "5t", "imq"],
    "4": ["gtt_gps"],
    "6": ["gtt_orari_gps", "comune_parcheggi", "5t", "imq", "osm", "tomtom"],
    "8": ["gtt_orari", "5t", "imq", "osm", "carburanti", "aci", "gtt_tariffe", "tomtom"],
    "10": ["omi", "istat", "comune_servizi", "osm", "gtt_orari"],
}


# nome breve del risultato (al massimo 4 parole) per i riquadri della home; l'inglese sta in testi.json
TITOLI_BREVI = {"8": "Bus contro auto", "6": "Dove lasciare l'auto",
                "10": "Fragilità e servizi", "4": "Ritardi dei mezzi", "1": "Servizi a piedi"}


def forma_base(s, titolo, domanda, numero, principale, punti, altri, calcolo, criteri, limiti, english=None, mappa=True, **extra):
    """La forma di una scheda. «english» non si usa più (l'inglese viene da traduci.py): resta come argomento per non cambiare le chiamate."""
    f = {"tipo_dato": TIPO_DATO[s["tag"]], "titolo": titolo, "domanda": domanda, "numero": numero, "principale": principale,
         "punti": punti, "altri": altri, "calcolo": calcolo, "criteri": criteri, "limiti": limiti}
    if mappa and s.get("mappa"):
        f["mappa"] = {"id": s["mappa"]["id"], "nota": s["mappa"]["nota"]}
        if s["mappa"].get("vista"):   # es. #tema=vulnerabilita&vista=doppio
            f["mappa"]["vista"] = s["mappa"]["vista"]
    f["fonti"] = [FONTI_NOMI[k] for k in FONTI_SCHEDA[str(s["risultato"])]]
    f["titolo_breve"] = TITOLI_BREVI[str(s["risultato"])]
    f.update(extra)
    return f




def grafico_per_titolo(s, inizio):
    return next(g for g in s["grafici"] if g["titolo"].startswith(inizio))




def numero_di(s, label_inizio, scenario=0):
    return next(n for n in s["scenari"][scenario]["numeri"] if n["label"].startswith(label_inizio))["dopo"]




# ---------------------------------------------------------------- Tempi in auto corretti col controllo con TomTom (§6.2 del piano, decisione 16 di §2)
# La stima aperta dell'auto e' piu' veloce di TomTom in tutti i 20 percorsi controllati: in pagina si usa solo la stima aperta corretta col fattore unico
# del controllo (estremo B). Il fattore si legge da controllo_navigatori_riepilogo.json, mai scritto a mano.

MINUTI_PARCHEGGIO = 5.0   # gli stessi di scripts/93_tp_contro_auto.py (MIN_PARCHEGGIO): il fattore corregge solo il tempo di guida


def fattore_controllo():
    """f = 1 / (1 + mediana dell'errore con segno): oggi circa 1,31 (la stima aperta e' -23,5% rispetto a TomTom)."""
    r = leggi("controllo_navigatori_riepilogo.json")
    return 1.0 / (1.0 + r["mediana_errore_con_segno_pct"] / 100.0)


def auto_corretta(auto_min, f=None):
    """Tempo in auto B: la guida (senza i 5 minuti di parcheggio) per f, piu' i 5 minuti."""
    f = fattore_controllo() if f is None else f
    return (auto_min - MINUTI_PARCHEGGIO) * f + MINUTI_PARCHEGGIO


def mediana_pesata(valori_pesi):
    vp = sorted(valori_pesi)
    tot = sum(w for _, w in vp)
    acc = 0.0
    for v, w in vp:
        acc += w
        if acc >= tot / 2:
            return v
    return vp[-1][0]


def classe_rapporto(r, soglia=1.5):
    return "conviene" if r <= soglia else "non_conviene"


def rapporto_medio_giorno():
    """Numero grande della scheda 2 (decisione 16 di §2): media semplice, sulle 4 ore del giorno, del rapporto mediano coi mezzi pubblici / auto
    (tempo in auto corretto col controllo), con un decimale. None se ore_del_giorno.json manca o e' una prova: allora vale il valore delle 8."""
    od = ore_del_giorno()
    if not od:
        return None
    v = [o["ab"]["limite_corretto"]["mediano"] for o in od["ore"]]
    return round(sum(v) / len(v), 1)
