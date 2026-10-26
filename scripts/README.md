# scripts/ — map of the code

Technical file for developers (kept in English). Every file of `scripts/` appears once below, grouped by phase.
The order of the calculations is the one of `FASI` in rifai_tutto.py:

```
python scripts/rifai_tutto.py --elenco          # show the phases and commands without running anything
python scripts/rifai_tutto.py --solo schede,mappa
```

Phases: `riassunti`, `dati`, `accessibilita`, `traffico`, `r1`, `r4`, `r8`, `r6`, `r10`, `schede`, `mappa`, `prova`.
Scripts marked *exploratory* are not part of the product and are not published.

## Shared modules

| File | What it is |
|---|---|
| `comuni.py` | constants (`PERIODO`, paths) and Italian-time helpers used by many scripts |
| `config_locale.py` | reads `config_locale.json` (outside git: Raspberry Pi access, map keys) |
| `config_locale.esempio.json` | template of `config_locale.json` |
| `rete_osm.py` | drivable road graph taken from the OpenStreetMap extract |
| `riassunti_storico.py` | format and reader of the history summaries written by script 97 |
| `77_strade_comuni.py` | shared road helpers of the park-and-ride scripts |

## Collection on the Raspberry Pi

| File | What it does |
|---|---|
| `supervisore.py` | keeps the whole collection alive as a single service |
| `03_raccolta_continua.py` | every minute: vehicle positions, 5T sensors, parking occupancy |
| `12_ritardi_gtt.py` | GTT trip updates and alerts |
| `06_dati_live.py` | turns the history into small files for the map |
| `installa_leopi.sh`, `installa_ritardi.sh` | install the services on the Pi |
| `controlla_raccolta_5t.py`, `controlla_raccolta_pk.py` | checks run on the Pi |
| `controlla_leopi.py` | is the collection on the Pi working? (read-only SSH) |
| `backup_da_leopi.py` | daily consistent copy of the history from the Pi to the PC |

## Data

| File | What it does |
|---|---|
| `01_scarica_dati.py` | downloads open data into `data/raw` |
| `scarica_dati.py` | downloads the large data from the GitHub Release and checks the hashes |
| `98_prepara_release.py` | prepares the Release zips with their hashes |
| `05_prepara_sezioni.py` | 2021 census sections of Turin and surroundings |
| `08_prepara_omi.py` | real-estate (OMI) zone values |
| `11_prepara_catalogo.py` | catalogue of city services |
| `13_esporta_imq.ps1` | exports the IMQ 2022 survey tables (by hand) |
| `14_prepara_imq.py`, `15_prepara_zone_imq.py`, `16_prepara_imq_mappa.py` | IMQ 2022 trips, zones and map data |
| `17_taglia_osm.py` | cuts Turin and its belt out of the raw OSM file |
| `20_servizi_osm.py` | OSM services outside the municipality |
| `96_inventario_dati.py` | inventory of `data/`: who reads and writes each file |
| `97_riassunti_storico.py` | summaries of the collected history (read-only on the history) |
| `confronta_riassunti.py` | checks that the summaries match the real history |

## Accessibility (R5)

| File | What it does |
|---|---|
| `18_accessibilita.py` | walking and public-transport accessibility per census section (about 19 hours for the full run) |
| `19_vulnerabilita.py` | vulnerability index per census section |

## Traffic

| File | What it does |
|---|---|
| `24_importanza_vie.py` | importance score of the streets |
| `26_velocita_5t.py`, `33_flusso_sensori.py`, `35_sensori_esclusi.py`, `36_abbinamento_posizione.py`, `38b_codici_condivisi.py`, `37_traffico_AB.py` | 5T sensors: speed, flow, exclusions, matching to the road graph |
| `39_fattibilita_rete.py`, `40_domanda_imq.py`, `41_zone_punti.py`, `42_instradamento.py`, `43_segmenti_corridoi.py`, `44_taratura_validazione.py`, `45_prodotto_finale.py` | traffic model, phase 3 |
| `49_v3_punti_domanda.py`, `50_v3_assegnazione.py`, `50b_v3_valutazione.py` | model V3 |
| `51_tp_gtfs_tratti.py`, `52_tp_corridoi.py`, `53_pubblicazione_traffico.py`, `54_incrocio_traffico_tp.py` | public-transport supply and crossing with traffic |
| `56_build_rete_lanes.py`, `57_assi_tratte.py`, `58_corsie.py`, `59_ztl.py`, `60_tp_fermate.py`, `61_tp_tratte.py`, `62_v4_modello.py`, `63_v4_valutazione.py`, `65_affidabilita.py`, `66_pubblicazione_incrocio.py`, `67_verifiche_fase5.py` | model V4 (axes, lanes, ZTL, reliability, checks) |

## Delays (result 1 of the site)

| File | What it does |
|---|---|
| `27_risultato4_regolarita.py` | late and irregular buses, measured |
| `70_risultato9_attesa.py` | promised waiting time against the real one |
| `104_velocita_bus.py` | commercial speed of buses and trams from GPS, hour by hour |
| `105_correzione_tempi_mezzi.py` | corrects public-transport times with the measured delay and waiting |
| `106_dove_nascono_ritardi.py` | the stop-to-stop segments where delays arise (minutes lost per weekday) |

## Car or public transport (result 2)

| File | What it does |
|---|---|
| `93_tp_contro_auto.py` | where public transport does not pay off against the car (r5py) |
| `107_sonde_bus.py` | buses as traffic probes: how much slower than free flow, by zone and hour |
| `108_controllo_navigatori.py` | check of the open car estimate on 20 routes against TomTom (`--tomtom`, read by a program only for this check; saves only the summary) |
| `99_area_tempi.py` | the expanding area from Piazza Castello, by public transport and by car |
| `100_ore_del_giorno.py` | the same comparison at four hours of the day |
| `102_scelta_del_mezzo.py` | who can choose, by zone |
| `103_costo_del_viaggio.py` | cost of the trip by car and by public transport |

## Park and ride (result 4)

| File | What it does |
|---|---|
| `25_risultato6_interscambio.py` | coverage of the park-and-ride lots |
| `68_luoghi_fermate.py`, `69_parcheggi_inventario.py`, `71_parcheggi_riempimento.py`, `72_nodi_tp.py`, `73_segnali_criticita.py` | stops as places, parking inventory, filling, transport nodes, signals |
| `79_dati_mappa_r6.py` | small file read by the map and the card |
| `80_porte_interscambio.py` | superseded by script 84, kept for reference |
| `81_auto_di_passaggio.py`, `82_parcheggi_adatti.py`, `83_fermate_importanti.py`, `84_risultato6_parcheggi.py`, `85_verifiche_correzioni.py` | corrected result: cars entering, suitable lots, major stops, missing spaces, independent checks |
| `87_popolarita_zone.py`, `88_confronto_auto_sensori.py` | zone popularity, model against sensors |
| `94_r6_bus_contro_auto.py` | from the lot to the centre: bus against car |

## Vulnerability and services (result 3)

| File | What it does |
|---|---|
| `21_risultato1_vuoti.py`, `22_risultato1_candidati.py` | where essential services are missing, where to add one |
| `23_vulnerabilita_incrocio.py` | vulnerability against service gaps |
| `92_esposizione_traffico.py` | residents' exposure to traffic (read-only) |
| `95_case_fragilita_servizi.py` | house prices against vulnerability and services |

## Cards and site

| File | What it does |
|---|---|
| `schede_risultati.py` | writes `data/schede_risultati.js`, the home and project data, and the share pages `r/N.html` |
| `schede/` | one module per card: `r4.py`, `r8.py`, `r10.py`, `r6.py` (findings 1–4; `r2.py` is kept but hidden); `home.py`, `progetto.py`, `raccomandazioni.py` (the numbers of «Three decisions for Turin»), `pagine_r.py`, `pagine_sito.py`, `comune.py`, `traduci.py`, `__init__.py`; the texts of the other languages are in `testi.json` |
| `04_genera_mappa.py` | builds `mappa_torino.html` from the map template (writes the background-map keys from `config_locale.json` into the page) |
| `rifai_mappa_da_html.py` | rebuilds `mappa_torino.html` with the current template, reusing the data already inside the current map (no raw data needed; for tests and the cloud) |
| `mappa_template.html` | template of the map; the placeholder `"__DATI__"` is filled by script 04 |
| `costruisci_asset_sito.py` | social preview image of the site |
| `costruisci_contorno_torino.py` | outline of Turin for the animations |

## Checks

| File | What it does |
|---|---|
| `controllo_completo.py` | the same steps as the GitHub check, in the same order |
| `prova_pagine.py` | runtime test of every page and map theme |
| `86_controlla_file_pagine.py` | every file loaded by the pages exists and is in git |
| `controlla_pesi_git.py` | files in git are small enough |
| `controlla_rami.py` | local and remote branches agree |
| `rifai_tutto.py` | the one command that redoes every calculation in order |
| `prove/` | tests and tools: `prova_capolinea.py`, `prova_funzioni_comuni.py`, `prova_gtfs_archivio.py`, `prova_gtfs_per_giorno.py`, `prova_riassunti.py`, `prova_scheda_case.py`, `prova_traduzione.py`, `prova_contenuto.py` (card contents, tone phrases in `frasi_vietate.py`), `storico_finto.py` (fake history), `estrai_dati_mappa.py` (data out of the current map), `screenshot_sito.py` |

## Exploratory, not published

| File | What it does |
|---|---|
| `28_scenario_metro_notte.py`, `29_risultato2_metro_notte.py` | night-metro scenario |
| `30_rapporto_estrai.py`, `31_rapporto_fatti.py`, `32_rapporto_riassunto.py` | reading of the GTT sustainability report |
