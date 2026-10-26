#!/usr/bin/env python3
"""
79_dati_mappa_r6.py  -  Risultato 6: il file piccolo che leggono la mappa e la scheda.

Cosa fa
-------
Prende quello che ha calcolato lo script 84 (prima: 80) e lo mette in un unico file JSON compatto, pronto
per essere disegnato sulla mappa e raccontato nella scheda. Non fa calcoli nuovi.
Correzioni del 20/10/2026 (Claude): campi nuovi dello script 84 (auto che passano, posti adatti, classi
nuove, validazione, «Pochi dati» per le aree); niente punteggi grezzi nei dati pubblici; i controlli con i
numeri di oggi sono diventati avvisi (lo script si ferma solo per errori di struttura).

Il file contiene:
  - aree (celle esagonali di circa 2 km²): centro, poligono, fermate, categoria, parcheggi pieni;
  - punti_prioritari (20): dove servirebbe di più un parcheggio, con i candidati ad ampliarsi;
  - fermate: le fermate importanti, classe (nessun parcheggio / posti insufficienti / posti sufficienti /
    poche auto da fermare);
  - parcheggi (mostrati): adatti con almeno 100 posti vicino a una fermata importante o a un nodo di trasporto
    importante, più gli interscambi ufficiali e i park & ride;
  - profili (garage 5T con dati) e profili_medi (per firma);
  - riepilogo, criteri, etichette, fonti, generato.
Le direzioni d'ingresso NON vanno in mappa: restano nel riepilogo (riferimento_direzioni) per la scheda.

Cosa legge
----------
  data/processed/risultato6_v2/porte.json   (prodotto dallo script 84)

Cosa scrive
-----------
  data/processed/risultato6_v2/mappa_r6.json

Come si lancia
--------------
  python scripts\\79_dati_mappa_r6.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
P = RADICE / "data" / "processed" / "risultato6_v2"
PORTE = P / "porte.json"
OUT = P / "mappa_r6.json"
LIMITE_BYTE = 1_500_000

ETICHETTE = {
    "aree": "celle esagonali di circa 2 km² con almeno una fermata importante; colore = quota di fermate senza posti "
            "bastanti (Critica ≥ 60%, Scarsa 30-59%, Buona < 30%); grigio = «Pochi dati» (meno di 5 fermate valutate)",
    "classe": "posti adatti entro 400 m a piedi confrontati con le auto da fermare: nessun parcheggio, posti insufficienti, "
              "posti sufficienti; «poche auto da fermare» = lì non serve un interscambio",
    "posti": "posti dichiarati dove ci sono, altrimenti stimati dalla superficie (25 m² a posto, ±30%)",
    "stato": "riempimento di giorno: pieno ≥ 85%, a metà, con posti liberi < 50%, non misurato",
    "auto_passaggio": "auto in entrata a Torino al mattino che passano sulla strada accanto",
    "riempimento": "misura 5T, media feriale 10-16",
    "profilo_feriale": "occupazione media ora per ora, giorno feriale",
    "profilo_weekend": "occupazione media ora per ora, weekend",
    "nodo_vicino": "nodo di trasporto importante entro 400 m: metro, treno, capolinea o molte corse (almeno 20 corse all'ora) oppure nessuno",
}
N_LINEE_TXT = 8          # linee utili scritte nel pannello del parcheggio
POPOLARITA = RADICE / "data" / "processed" / "popolarita_zone.json"
BUS_AUTO = RADICE / "data" / "processed" / "r6_bus_contro_auto.json"
CAMPI_FERMATA = ("id", "nome", "lat", "lon", "zona_nome", "posizione", "classe", "strada", "auto_passaggio_txt",
                 "potenziale", "posti_adatti", "mancano", "parcheggi")
CAMPI_AREA = ("id", "centro", "poligono", "n_fermate", "n_valutate", "nessun", "insufficienti", "sufficienti",
              "poche_auto", "quota_senza", "categoria", "pochi_dati", "zone_principali", "etichetta",
              "mostra_etichetta", "posti_adatti", "parcheggi_pieni", "fermate_senza")


def main():
    c = comuni.Controlli()
    c(f"esiste {PORTE.name} (lancia prima scripts\\84_risultato6_parcheggi.py)", PORTE.exists(), bloccante=True)
    d = json.loads(PORTE.read_text(encoding="utf-8"))
    c("porte.json viene dallo script 84 (ha il campo classi)", "classi" in d, bloccante=True)

    # linee utili vicine (da 87_popolarita_zone.py): solo per i parcheggi adatti; se il file manca, campi assenti
    parcheggi = d["parcheggi"]
    if POPOLARITA.exists():
        utili = {p["id"]: p for p in json.loads(POPOLARITA.read_text(encoding="utf-8"))["parcheggi_adatti"]}
        for p in parcheggi:
            u = utili.get(p.get("id"))
            if u is not None:
                p["linee_utili"] = u["linee_utili"]
                p["linee_utili_txt"] = ", ".join(u["elenco_utili"][:N_LINEE_TXT])
        c("linee utili aggiunte ai parcheggi adatti in mappa", any("linee_utili" in p for p in parcheggi),
          dettaglio=f"{sum('linee_utili' in p for p in parcheggi)} su {len(parcheggi)} parcheggi in mappa")
    else:
        c(f"esiste {POPOLARITA.name} (lancia prima scripts\\87_popolarita_zone.py): senza, niente linee utili nel pannello",
          False)

    # tempi coi mezzi e in auto verso Piazza Castello e classe (da 94_r6_bus_contro_auto.py): si aggiunge solo il campo bus_auto,
    # i punti non si tolgono dall'elenco. Se il file manca, i punti restano senza.
    if BUS_AUTO.exists():
        ba = {l["nome"]: l for l in json.loads(BUS_AUTO.read_text(encoding="utf-8"))["luoghi"]}
        for p in list(d["punti_prioritari"]) + [x for x in parcheggi if x.get("tipo") == "interscambio_ufficiale"]:
            l = ba.get(p["nome"])
            if l is not None:
                p["bus_auto"] = {k: l[k] for k in ("tp_min", "auto_favorevole_min", "auto_stima_min", "rapporto_basso", "rapporto_alto", "classe", "classe_testo")}
        c("ogni punto prioritario ha la classe bus contro auto", all("bus_auto" in p for p in d["punti_prioritari"]),
          dettaglio=f"{sum('bus_auto' in p for p in d['punti_prioritari'])} su {len(d['punti_prioritari'])}")
    else:
        c(f"esiste {BUS_AUTO.name} (lancia prima scripts\\94_r6_bus_contro_auto.py): senza, niente classe nel pannello", False)

    fermate = [{k: f.get(k) for k in CAMPI_FERMATA} for f in d["fermate"]]
    aree = [{k: a.get(k) for k in CAMPI_AREA} for a in d["aree"]]
    mappa = {
        "generato": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "fonti": ["data/processed/risultato6_v2/porte.json", "scripts/84_risultato6_parcheggi.py"],
        "etichette": ETICHETTE, "classi": d["classi"], "parametri": d["parametri"],
        "soglia_aree": d["soglia_aree"],
        "aree": aree,
        "punti_prioritari": d["punti_prioritari"],
        "fermate": fermate,
        "parcheggi": parcheggi,
        "profili": d["profili"],
        "criteri": d["criteri"],
        "riepilogo": d["riepilogo"],
        "affidabilita": d["affidabilita"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(mappa, ensure_ascii=False), encoding="utf-8")
    dim = OUT.stat().st_size
    c("mappa_r6.json sotto 1,5 MB", dim <= LIMITE_BYTE, bloccante=True, dettaglio=f"{dim} byte")
    c("ogni fermata in una sola area", sum(a["n_fermate"] for a in aree) == len(fermate), bloccante=True)
    c("niente punteggi grezzi nelle fermate", all("punteggio" not in f for f in fermate), bloccante=True)
    c("punti prioritari: da 1 a 20", 1 <= len(mappa["punti_prioritari"]) <= 20, dettaglio=f"{len(mappa['punti_prioritari'])}")
    conta = {k: sum(1 for f in fermate if f["classe"] == k) for k in d["classi"]}
    print(f"mappa_r6.json: {dim} byte ({dim/1024:.0f} KB); aree {len(aree)}, punti {len(mappa['punti_prioritari'])}, "
          f"fermate {len(fermate)} {conta}, parcheggi {len(mappa['parcheggi'])}, profili {len(mappa['profili'])}")
    print(f"Scritto: {OUT}; avvisi: {len(c.avvisi())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
