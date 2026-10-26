# Data sources and licences

Turin Meter uses open data only (plus the check described below). The **code** is under the [MIT licence](LICENSE); **data keep the licence of their source**. Italian and German versions: [`docs/it/LICENZE_DATI.md`](docs/it/LICENZE_DATI.md), [`docs/de/DATENLIZENZEN.md`](docs/de/DATENLIZENZEN.md).

*Independent personal project: not affiliated with or endorsed by GTT, 5T, the City of Turin or any other organisation mentioned.*

| Source | What is used | Licence | What is republished | Attribution |
|---|---|---|---|---|
| GTT – timetables (GTFS) | lines, stops, timetables | CC BY (aperTO) | derived values; the GTFS in the Release | «GTT – Gruppo Torinese Trasporti, via aperTO (CC BY)» |
| GTT – real time (GTFS-RT) | GPS positions, delays | CC BY (aperTO) | summaries only (departures), never the raw history | same as above |
| 5T – traffic, parking, restricted zones | flows, speeds, free spaces | IODL 2.0 | summaries | «5T / Città di Torino, Muoversi a Torino (IODL 2.0)»; not affiliated |
| ISTAT – 2021 census, territorial bases | residents, indicators, sections | CC BY 4.0 | derived values | «Source: Istat, own elaboration» |
| City of Turin – aperTO | services, car parks, zones | CC BY 4.0 | derived values | «Città di Torino, aperTO (CC BY 4.0)» |
| OpenStreetMap | road network, services of the belt, traffic lights | ODbL 1.0 | extract in the Release (ODbL); derived results | «© OpenStreetMap contributors (ODbL)» |
| Piedmont Mobility Agency – IMQ 2022 travel survey | trips by zone and hour | no explicit licence | **aggregated values per zone only**; raw files are not republished | «Agenzia della mobilità piemontese, IMQ 2022» |
| Revenue Agency – OMI | price quotes per zone | no explicit licence | **values per zone only** | «Agenzia delle Entrate – OMI» |
| MIMIT – fuel prices observatory | two average prices | IODL 2.0 (stated on the dataset page of the ministry's open data portal) | two values | «Osservatorio prezzi carburanti (MIMIT), IODL 2.0» |
| ACI – 2026 per-km costs | two values | official act (Gazzetta Ufficiale no. 297/2025) | two values | «ACI, tables 2026» |
| GTT – fares and parking | prices | public pages | values | «GTT» |
| GTT – Sustainability Report 2025 | one figure (a delay share) | public document | only the cited figure | «GTT, Sustainability Report 2025» |
| TomTom Routing API | check of car times on 20 routes (read by a program only for this check) | commercial terms of use; **no special permission** | **nothing**: only the summary of the check (errors), no TomTom times | «check on 20 routes with TomTom» |
| Google Maps | manual check only, if used | personal use by hand | nothing | «manual check with Google Maps» |
| CARTO (light background) | map tiles | free for personal projects, with key | nothing | «© OpenStreetMap contributors, © CARTO» |
| Esri World Imagery (satellite, optional) | map tiles | ArcGIS key, free tier | nothing | «Esri, Maxar, Earthstar Geographics» |
| Barlow font | site typeface | SIL Open Font License 1.1 | the woff2 files with `assets/font/OFL.txt` | in the licence file |
| Project code | — | MIT | everything | — |

Licences were checked on the official pages; where a page states no licence the table says so and only aggregated values are shown. The fuel-price licence (IODL 2.0) is stated on the dataset page of the ministry's open data portal.
