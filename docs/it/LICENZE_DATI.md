# Fonti dei dati e licenze

Turin Meter usa solo dati aperti (più il controllo descritto sotto). Il **codice** ha licenza [MIT](../../LICENSE); i **dati mantengono la licenza della loro fonte**. Versione inglese (di riferimento): [`DATA_LICENSES.md`](../../DATA_LICENSES.md).

*Progetto personale e indipendente: non è affiliato né approvato da GTT, 5T, Città di Torino o dagli altri enti citati.*

| Fonte | Cosa si usa | Licenza | Cosa si ripubblica | Attribuzione |
|---|---|---|---|---|
| GTT – orari (GTFS) | linee, fermate, orari | CC BY (aperTO) | valori derivati; il GTFS nella Release | «GTT – Gruppo Torinese Trasporti, via aperTO (CC BY)» |
| GTT – tempo reale (GTFS-RT) | posizioni GPS, ritardi | CC BY (aperTO) | solo riassunti (passaggi), mai lo storico grezzo | come sopra |
| 5T – traffico, parcheggi, ZTL | flussi, velocità, posti liberi | IODL 2.0 | riassunti | «5T / Città di Torino, Muoversi a Torino (IODL 2.0)»; non affiliato |
| ISTAT – censimento 2021, basi territoriali | residenti, indicatori, sezioni | CC BY 4.0 | valori derivati | «Fonte: Istat, elaborazione propria» |
| Comune di Torino – aperTO | servizi, parcheggi, zone | CC BY 4.0 | valori derivati | «Città di Torino, aperTO (CC BY 4.0)» |
| OpenStreetMap | rete stradale, servizi della cintura, semafori | ODbL 1.0 | estratto nella Release (ODbL); risultati derivati | «© contributori di OpenStreetMap (ODbL)» |
| Agenzia della mobilità piemontese – indagine IMQ 2022 | spostamenti per zona e ora | nessuna licenza esplicita | **solo valori aggregati per zona**; i file grezzi non si ripubblicano | «Agenzia della mobilità piemontese, IMQ 2022» |
| Agenzia delle Entrate – OMI | quotazioni per zona | nessuna licenza esplicita | **solo valori per zona** | «Agenzia delle Entrate – OMI» |
| MIMIT – Osservatorio prezzi carburanti | due prezzi medi | IODL 2.0 (dichiarata nella pagina del dataset del portale open data del ministero) | due valori | «Osservatorio prezzi carburanti (MIMIT), IODL 2.0» |
| ACI – costi chilometrici 2026 | due valori | atto ufficiale (Gazzetta Ufficiale n. 297/2025) | due valori | «ACI, tabelle 2026» |
| GTT – tariffe e sosta | prezzi | pagine pubbliche | valori | «GTT» |
| GTT – Rapporto di sostenibilità 2025 | un numero (quota di ritardi) | documento pubblico | solo la cifra citata | «GTT, Rapporto di sostenibilità 2025» |
| TomTom Routing API | controllo dei tempi in auto su 20 percorsi (letto da programma solo per questo controllo) | condizioni d'uso commerciali; **nessun permesso speciale** | **nulla**: solo il riepilogo del controllo (errori), nessun tempo TomTom | «controllo su 20 percorsi con TomTom» |
| Google Maps | solo controllo a mano, se usato | uso personale a mano | nulla | «controllo a mano con Google Maps» |
| CARTO (sfondo chiaro) | mattonelle della mappa | gratuito per progetti personali, con chiave | nulla | «© OpenStreetMap contributors, © CARTO» |
| Esri World Imagery (satellite, facoltativo) | mattonelle | chiave ArcGIS, livello gratuito | nulla | «Esri, Maxar, Earthstar Geographics» |
| Font Barlow | caratteri del sito | SIL Open Font License 1.1 | i file woff2 con `assets/font/OFL.txt` | nel file di licenza |
| Codice del progetto | — | MIT | tutto | — |

Le licenze sono state controllate sulle pagine ufficiali; dove una pagina non dice nulla, la tabella lo scrive e si mostrano solo valori aggregati. La licenza dei prezzi dei carburanti (IODL 2.0) è dichiarata nella pagina del dataset del portale open data del ministero.
