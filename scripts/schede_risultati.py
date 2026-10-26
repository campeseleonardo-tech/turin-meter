"""Schede dei RISULTATI (la finestra che si apre sopra index.html).

Legge i file gia' prodotti dagli script dei risultati e scrive:
  data/processed/risultato4_riepilogo_mappa.json   (Risultato 4, da 27)
  data/processed/risultato6_v2/mappa_r6.json   (Risultato 6, da 79 e 84) -> data/processed/risultato6_riepilogo_mappa.json
  data/processed/risultato8_riepilogo_mappa.json   (Risultato 8, script 56-67)
  data/processed/risultato10_riepilogo_mappa.json  (Risultato 10 = «Case, servizi e fragilita'», da case_fragilita_servizi.json dello script 95)
  data/schede_risultati.js   (tutte le schede, R2 compreso, caricate da index.html)
  data/home_mezzi.js (home) e data/progetto.js (progetto.html), scritti da schede/home.py e schede/progetto.py;
  r/1.html ... r/6.html (pagine da condividere) e gli elenchi dei risultati nel README.md, scritti da schede/pagine_r.py

Il riepilogo base del Risultato 2 lo scrive 29_risultato2_metro_notte.py: qui si legge e si arricchisce
solo nel .js (il file JSON di R2 non viene riscritto).

Formato della scheda (base, compatibile col caricamento a mano):
  {risultato, titolo, domanda, scenari:[{nome, numeri:[{label,prima,dopo,unita}], nota}], avviso}
  Un numero senza "prima/dopo" (fotografia di oggi) ha prima = null.
Campi in piu' per la finestra di dettaglio (tutti facoltativi):
  tag, stato, in_breve, numero_chiave {valore, unita, testo}, racconto, risposta [frasi],
  grafici [{tipo: "barre"|"pila"|"orario", titolo, unita, nota, voci|righe}],
  metodo [frasi], parametri [[nome, valore]], limiti [frasi], mappa {tema, nota} | null, fonti [file].
Nessun calcolo nuovo sui dati grezzi: solo numeri gia' presenti nei file prodotti dagli script
e semplici somme/conteggi su di essi.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))   # il pacchetto schede/ sta accanto a questo file
from comuni import PERIODO  # noqa: E402  (periodo fisso dei dati, per il piede delle pagine)
from schede import comune  # noqa: E402
from schede.comune import NASCOSTE, RADICE, controlla_forma, leggi  # noqa: E402
from schede.traduci import traduci_forma  # noqa: E402
from schede.home import scrivi_home  # noqa: E402
from schede.pagine_r import aggiorna_readme, scrivi_pagine_r  # noqa: E402
from schede.pagine_sito import scrivi_pagine_sito  # noqa: E402
from schede.progetto import scrivi_progetto  # noqa: E402
from schede.r10 import forma_r10, scheda_r10  # noqa: E402
from schede.r2 import arricchisci_r2  # noqa: E402
from schede.r4 import forma_r4, scheda_r4  # noqa: E402
from schede.r6 import forma_r6, scheda_r6  # noqa: E402
from schede.r8 import forma_r8, scheda_r8  # noqa: E402




FORME = {"risultato4": forma_r4, "risultato6": forma_r6, "risultato8": forma_r8, "risultato10": forma_r10}



# numerazione pubblica (L22): in pagina i risultati sono 1-6, prima quelli per decidere poi quelli ricavati dai dati; i numeri interni e i link #rN restano validi.
# Il codice delle pagine e delle prove cerca una scheda per id interno (campo «risultato»), mai per numero in pagina.
NUMERO_PUBBLICO = {"risultato4": 1, "risultato8": 2, "risultato10": 3, "risultato6": 4}
GRUPPO = {"risultato4": "vetrina", "risultato8": "vetrina", "risultato10": "vetrina", "risultato6": "approfondimento"}




def scrivi_frasi_de(frasi):
    """Elenco delle frasi delle schede ancora senza versione tedesca (restano in inglese): data/ref/frasi_de_mancanti.txt, una per riga."""
    uniche = sorted(dict.fromkeys(frasi))
    (RADICE / "data" / "ref" / "frasi_de_mancanti.txt").write_text("\n".join(uniche) + ("\n" if uniche else ""), encoding="utf-8")
    print(f"tedesco: {len(uniche)} frasi delle schede senza traduzione (restano in inglese): data/ref/frasi_de_mancanti.txt")


def main():
    schede = []
    mancanti_de = []
    for nome, fabbrica in (("risultato2", None),
                           ("risultato4", scheda_r4), ("risultato6", scheda_r6),
                           ("risultato8", scheda_r8), ("risultato10", scheda_r10)):
        if nome in NASCOSTE:
            continue
        file = f"{nome}_riepilogo_mappa.json"
        if fabbrica is None:
            s = arricchisci_r2(leggi(file))  # il JSON di R2 resta quello dello script 29
        else:
            s = fabbrica()
            s["forma"] = FORME[nome](s)
            mancanti = []
            s["forma_en"] = traduci_forma(s["forma"], "en", mancanti)   # inglese completo, dai testi di schede/testi.json
            for frase in dict.fromkeys(mancanti):
                print(f"  ATTENZIONE {nome}: frase senza traduzione in schede/testi.json: «{frase[:400]}»")
            s["forma_de"] = traduci_forma(s["forma"], "de", mancanti_de)   # tedesco: le frasi senza versione tedesca restano inglesi e si elencano (le aggiunge F4)
            s["numero_pubblico"] = NUMERO_PUBBLICO[nome]
            s["gruppo"] = GRUPPO[nome]
            s.pop("_n_su", None)
            print(f"{nome}: forma - «{s['forma']['titolo']}», numero grande {s['forma']['numero']['valore']} {s['forma']['numero']['unita']}")
            controlla_forma(nome, s["forma"])
            (comune.PROC / file).write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        s["_nome"] = file
        schede.append(s)
        print(f"{file}: {s['titolo']} - {sum(len(sc['numeri']) for sc in s['scenari'])} numeri, "
              f"{len(s.get('grafici', []))} grafici")
    scrivi_frasi_de(mancanti_de)
    comune.OUT_JS.write_text("// generato da scripts/schede_risultati.py - non modificare a mano\n"
                      "window.SCHEDE_RISULTATI = " + json.dumps(schede, ensure_ascii=False, indent=1) + ";\n"
                      # periodo fisso dei dati (comuni.PERIODO), per il piede delle pagine: dal primo all'ultimo giorno fra i tre periodi
                      "window.SCHEDE_PERIODO = " + json.dumps({"da": min(p[0] for p in PERIODO.values()), "a": max(p[1] for p in PERIODO.values())}) + ";\n",
                      encoding="utf-8")
    try:
        mostra = comune.OUT_JS.relative_to(RADICE)
    except ValueError:   # solo nelle prove, con un'altra cartella
        mostra = comune.OUT_JS
    print(f"scritto {mostra} con {len(schede)} schede")
    print(f"pagine di condivisione: {scrivi_pagine_r(schede)}")
    print(f"intestazione, barra e piede: {scrivi_pagine_sito()} pagine cambiate")
    try:
        scrivi_home()   # data/home_mezzi.js: mezzi in movimento e contatore della home
    except FileNotFoundError as e:
        print(f"AVVISO: data/home_mezzi.js non scritto, manca un file: {e.filename}")
    try:
        scrivi_progetto()   # data/progetto.js: dati di progetto.html
    except FileNotFoundError as e:
        print(f"AVVISO: data/progetto.js non scritto, manca un file: {e.filename}")
    print("README: " + ("aggiornati" if aggiorna_readme(schede) else "invariati"))   # per ultimo: «In numeri» legge data/progetto.js appena scritto




if __name__ == "__main__":
    main()
