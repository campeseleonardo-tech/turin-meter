# Datenquellen und Lizenzen

Turin Meter verwendet nur offene Daten (plus die unten beschriebene Kontrolle). Der **Code** steht unter der [MIT-Lizenz](../../LICENSE); die **Daten behalten die Lizenz ihrer Quelle**. Englische Fassung (maßgeblich): [`DATA_LICENSES.md`](../../DATA_LICENSES.md).

*Unabhängiges privates Projekt: nicht verbunden mit oder unterstützt von GTT, 5T, der Stadt Turin oder anderen genannten Organisationen.*

| Quelle | Was verwendet wird | Lizenz | Was erneut veröffentlicht wird | Quellenangabe |
|---|---|---|---|---|
| GTT – Fahrpläne (GTFS) | Linien, Haltestellen, Fahrpläne | CC BY (aperTO) | abgeleitete Werte; das GTFS in der Release | «GTT – Gruppo Torinese Trasporti, via aperTO (CC BY)» |
| GTT – Echtzeit (GTFS-RT) | GPS-Positionen, Verspätungen | CC BY (aperTO) | nur Zusammenfassungen (Abfahrten), nie das rohe Archiv | wie oben |
| 5T – Verkehr, Parkplätze, ZTL | Verkehrsflüsse, Geschwindigkeiten, freie Plätze | IODL 2.0 | Zusammenfassungen | «5T / Città di Torino, Muoversi a Torino (IODL 2.0)»; nicht verbunden |
| ISTAT – Volkszählung 2021, Gebietsgrundlagen | Einwohner, Indikatoren, Zählsprengel | CC BY 4.0 | abgeleitete Werte | «Quelle: Istat, eigene Auswertung» |
| Stadt Turin – aperTO | Einrichtungen, Parkplätze, Zonen | CC BY 4.0 | abgeleitete Werte | «Città di Torino, aperTO (CC BY 4.0)» |
| OpenStreetMap | Straßennetz, Einrichtungen im Umland, Ampeln | ODbL 1.0 | Auszug in der Release (ODbL); abgeleitete Ergebnisse | «© OpenStreetMap-Mitwirkende (ODbL)» |
| Agenzia della mobilità piemontese – Mobilitätserhebung IMQ 2022 | Fahrten nach Zone und Stunde | keine ausdrückliche Lizenz | **nur aggregierte Werte je Zone**; Rohdateien werden nicht erneut veröffentlicht | «Agenzia della mobilità piemontese, IMQ 2022» |
| Agenzia delle Entrate – OMI | Preisangaben je Zone | keine ausdrückliche Lizenz | **nur Werte je Zone** | «Agenzia delle Entrate – OMI» |
| MIMIT – Preisbeobachtungsstelle Kraftstoffe | zwei Durchschnittspreise | IODL 2.0 (auf der Datensatzseite des Open-Data-Portals des Ministeriums angegeben) | zwei Werte | «Osservatorio prezzi carburanti (MIMIT), IODL 2.0» |
| ACI – Kilometerkosten 2026 | zwei Werte | amtlicher Akt (Gazzetta Ufficiale Nr. 297/2025) | zwei Werte | «ACI, Tabellen 2026» |
| GTT – Tarife und Parken | Preise | öffentliche Seiten | Werte | «GTT» |
| GTT – Nachhaltigkeitsbericht 2025 | eine Zahl (Verspätungsanteil) | öffentliches Dokument | nur die zitierte Zahl | «GTT, Nachhaltigkeitsbericht 2025» |
| TomTom Routing API | Kontrolle der Autozeiten auf 20 Strecken (nur für diese Kontrolle per Programm abgefragt) | kommerzielle Nutzungsbedingungen; **keine Sondererlaubnis** | **nichts**: nur die Zusammenfassung der Kontrolle (Abweichungen), keine TomTom-Zeiten | «Kontrolle auf 20 Strecken mit TomTom» |
| Google Maps | nur manuelle Kontrolle, falls genutzt | persönliche Nutzung von Hand | nichts | «manuelle Kontrolle mit Google Maps» |
| CARTO (heller Hintergrund) | Kartenkacheln | kostenlos für private Projekte, mit Schlüssel | nichts | «© OpenStreetMap contributors, © CARTO» |
| Esri World Imagery (Satellit, optional) | Kacheln | ArcGIS-Schlüssel, kostenlose Stufe | nichts | «Esri, Maxar, Earthstar Geographics» |
| Schrift Barlow | Schrift der Website | SIL Open Font License 1.1 | die woff2-Dateien mit `assets/font/OFL.txt` | in der Lizenzdatei |
| Code des Projekts | — | MIT | alles | — |

Die Lizenzen wurden auf den offiziellen Seiten geprüft; wo eine Seite nichts angibt, steht das in der Tabelle, und es werden nur aggregierte Werte gezeigt. Die Lizenz der Kraftstoffpreise (IODL 2.0) ist auf der Datensatzseite des Open-Data-Portals des Ministeriums angegeben.
