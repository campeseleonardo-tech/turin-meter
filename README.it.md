# Turin Meter

**Come si muove Torino: misurato, calcolato, analizzato.** · Un progetto indipendente di Leonardo Campese

[![Sito](https://img.shields.io/badge/Sito-turin--meter-0b2559)](https://campeseleonardo-tech.github.io/turin-meter/) [![Controllo automatico](https://github.com/campeseleonardo-tech/turin-meter/actions/workflows/check.yml/badge.svg)](https://github.com/campeseleonardo-tech/turin-meter/actions/workflows/check.yml) [![MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

*English: [README.md](README.md) · Deutsch: [README.de.md](README.de.md)*

[![Turin Meter](assets/readme/home.jpg)](https://campeseleonardo-tech.github.io/turin-meter/)

## Cos'è

Il progetto raccoglie ogni minuto i dati aperti di bus, tram e traffico di Torino e li unisce a censimento, indagine sugli spostamenti e mappe aperte.
Quattro domande concrete sulla mobilità della città hanno una risposta, ognuna col suo metodo e i suoi limiti.
Solo dati aperti; sito, mappa e risultati sono in italiano, inglese e tedesco.

## Risultati principali

<!-- RISULTATI-IT:INIZIO -->
1. **Circa 1 passaggio su 15 arriva con più di 10 minuti di ritardo**  
   Quanto spesso i mezzi GTT arrivano in ritardo? → **6,7%** dei passaggi feriali arriva con oltre 10 minuti di ritardo. [Apri](https://campeseleonardo-tech.github.io/turin-meter/index.html#p1)
2. **Al mattino, coi mezzi pubblici si impiega da 1,9 a 2,4 volte il tempo dell'auto**  
   Al mattino, quanto ci si mette in più coi mezzi pubblici che in auto? → **1,9–2,4 volte** il tempo dell'auto, per i viaggi in auto del mattino fra zone diverse. [Apri](https://campeseleonardo-tech.github.io/turin-meter/index.html#p2)
3. **Circa 1 torinese su 10 vive in una zona con più difficoltà sociali e pochi servizi**  
   Chi vive dove i servizi sono pochi e le difficoltà sociali sono alte? → **79.598** residenti in zone con più difficoltà sociali e servizi bassi: il 9,5% dei residenti delle zone abitate. È 1,7 volte quanto ci si aspetterebbe per caso. [Apri](https://campeseleonardo-tech.github.io/turin-meter/index.html#p3)
4. **Circa 2 fermate importanti su 3 non hanno abbastanza posti per lasciare l'auto**  
   Chi arriva in auto da fuori trova dove lasciarla vicino a una fermata importante, per proseguire coi mezzi? → **179** fermate importanti su 274 non hanno posti bastanti a 400 metri a piedi. [Apri](https://campeseleonardo-tech.github.io/turin-meter/index.html#p4)
<!-- RISULTATI-IT:FINE -->

Ogni scheda spiega come è calcolato il numero e quali sono i limiti. I tempi in auto si danno come forbice.

## Come funziona

Un Raspberry Pi a casa legge ogni minuto i dati aperti di GTT e 5T e li salva in un archivio. Script Python li uniscono alle altre fonti, e le pagine si costruiscono dai risultati.

![Turin Meter: sources, Raspberry Pi, archive, scripts, pages](docs/img/architettura.svg)

### In numeri

<!-- IN-NUMERI-IT:INIZIO -->
- **~1,6 milioni** di passaggi alle fermate misurati col GPS · **112** sensori del traffico · **8.317** sezioni di censimento · **~12** fonti di dati aperti
- **3** settimane di lavoro · **485** versioni tracciate
<!-- IN-NUMERI-IT:FINE -->

## Il mio ruolo e il lavoro con l'AI

Ho scelto le domande, le fonti, le regole e le soglie, e deciso cosa pubblicare. La raccolta dei dati e parte delle analisi in Python le ho scritte io; per il resto l'AI ha fatto da acceleratore, con più modelli e un controllo automatico a ogni consegna. La storia è nella [pagina del progetto](https://campeseleonardo-tech.github.io/turin-meter/progetto.html).

## Il metodo

I documenti di metodo sono solo in inglese: [`docs/en/METHODS.md`](docs/en/METHODS.md). I punti principali:

- **Ritardi:** dal GPS dei mezzi, non dal feed ufficiale (che li sottostima); un passaggio è l'ultimo istante a meno di 60 m dalla fermata. Una lettura al minuto dà una forbice.
- **Dove nascono i ritardi:** tempo in più fra due fermate consecutive, minuti persi per giorno feriale, solo tratti con almeno 50 corse.
- **Tempi in auto:** una stima aperta (rete OpenStreetMap, velocità dei sensori 5T e dei bus, 20 secondi per semaforo, 5 minuti per parcheggiare), non servizi a pagamento.
- **Controllo con TomTom** su 20 percorsi: la stima aperta risulta troppo ottimista, quindi i numeri sono una forbice (stima aperta – stima corretta col fattore del controllo) e le classi si danno solo se uguali ai due estremi.
- **Fragilità:** indice costruito dal progetto con quattro indicatori del censimento 2021; non è un indice ISTAT né il reddito.
- **Parcheggi di scambio:** auto in entrata dall'indagine IMQ 2022 su un modello del traffico, posti da OpenStreetMap, Comune e 5T; i posti mancanti sono un ordine di grandezza.

## Dati, licenze e avvertenza

Solo dati aperti; il codice ha licenza [MIT](LICENSE), i dati mantengono la licenza della loro fonte: vedi [`docs/it/LICENZE_DATI.md`](docs/it/LICENZE_DATI.md) (riferimento in inglese: [`DATA_LICENSES.md`](DATA_LICENSES.md)). Dove una fonte non ha una licenza esplicita si pubblicano solo valori aggregati. TomTom si legge da programma solo per controllare la stima dell'auto su 20 percorsi, e di lì non si pubblica niente oltre al riepilogo del controllo.

*Progetto personale e indipendente: non è affiliato né approvato da GTT, 5T, Città di Torino o dagli altri enti citati.*

## Limiti

- Pochi giorni feriali di ottobre 2026: i numeri descrivono quel periodo, non un anno.
- Solo linee urbane viste dal GPS; una posizione al minuto, quindi i ritardi sono una forbice.
- I tempi in auto vengono da un modello aperto, controllato con TomTom su 20 percorsi; non sono misurati sui singoli viaggi.
- Niente treni né altre aziende; l'indice di fragilità è costruito dal progetto, non è un indice ufficiale e non è il reddito.
- I prezzi sono quelli di un giorno.

## Come rifare i calcoli

```
pip install -r requirements.txt     # per i tempi coi mezzi pubblici (r5py) serve anche Java 21 o più
python scripts/scarica_dati.py      # dati grandi dalla Release di GitHub (IMQ e OMI a mano: vedi docs/en/METHODS.md)
python scripts/rifai_tutto.py       # tutto, nell'ordine giusto (--elenco mostra le fasi, --riprendi riparte)
python scripts/prova_pagine.py      # controllo delle pagine
```

## Mappa del repository

Gli script, raggruppati per fase, sono descritti in [`scripts/README.md`](scripts/README.md) (in inglese).

## Contatti

Leonardo Campese · [LinkedIn](https://www.linkedin.com/in/leocampese/) · [campese.leonardo@gmail.com](mailto:campese.leonardo@gmail.com)
