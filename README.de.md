# Turin Meter

**Wie sich Turin bewegt: gemessen, berechnet, analysiert.** · Ein unabhängiges Projekt von Leonardo Campese

[![Website](https://img.shields.io/badge/Website-turin--meter-0b2559)](https://campeseleonardo-tech.github.io/turin-meter/?lang=de) [![Automatische Kontrolle](https://github.com/campeseleonardo-tech/turin-meter/actions/workflows/check.yml/badge.svg)](https://github.com/campeseleonardo-tech/turin-meter/actions/workflows/check.yml) [![MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

*English: [README.md](README.md) · Italiano: [README.it.md](README.it.md)*

[![Turin Meter](assets/readme/home.jpg)](https://campeseleonardo-tech.github.io/turin-meter/?lang=de)

## Was es ist

Das Projekt erfasst jede Minute offene Daten zu Bussen, Straßenbahnen und Verkehr in Turin und verknüpft sie mit Volkszählung, Mobilitätserhebung und offenen Karten.
Vier konkrete Fragen zur Mobilität der Stadt werden beantwortet, jede mit ihrer Methode und ihren Grenzen.
Nur offene Daten; Website, Karte und Ergebnisse gibt es auf Italienisch, Englisch und Deutsch.

## Wichtigste Ergebnisse

<!-- RISULTATI-DE:INIZIO -->
1. **Etwa 1 von 15 Abfahrten hat mehr als 10 Minuten Verspätung**  
   Wie oft sind die GTT-Fahrzeuge verspätet? → **6,7%** der Abfahrten an Werktagen haben mehr als 10 Minuten Verspätung. [Öffnen](https://campeseleonardo-tech.github.io/turin-meter/index.html?lang=de#p1)
2. **Mit öffentlichen Verkehrsmitteln braucht man im Schnitt das 2,1-Fache der Zeit des Autos**  
   Wie viel länger braucht man mit Bus und Bahn als mit dem Auto? → **2,1 Mal** die Autozeit, für die Autofahrten zwischen verschiedenen Zonen. [Öffnen](https://campeseleonardo-tech.github.io/turin-meter/index.html?lang=de#p2)
3. **Etwa 1 von 10 Einwohnern Turins lebt in einer Zone mit mehr sozialen Schwierigkeiten und wenigen Einrichtungen**  
   Wer lebt dort, wo es wenige Einrichtungen und große soziale Schwierigkeiten gibt? → **79.598** Einwohner in Zonen mit mehr sozialen Schwierigkeiten und wenigen Einrichtungen: 9,5% der Einwohner der bewohnten Gebiete. [Öffnen](https://campeseleonardo-tech.github.io/turin-meter/index.html?lang=de#p3)
4. **Etwa 2 von 3 wichtigen Haltestellen haben nicht genug Stellplätze, um das Auto stehen zu lassen**  
   Finden Autofahrer von außerhalb einen Platz für ihr Auto nahe einer wichtigen Haltestelle, um mit öffentlichen Verkehrsmitteln weiterzufahren? → **179** wichtige Haltestellen von 274 haben nicht genug Stellplätze im Umkreis von 400 Metern zu Fuß. [Öffnen](https://campeseleonardo-tech.github.io/turin-meter/index.html?lang=de#p4)
<!-- RISULTATI-DE:FINE -->

Jede Karte erklärt, wie die Zahl berechnet wird und wo ihre Grenzen liegen. Die Autozeiten sind ein offenes Modell, mit einem Faktor aus dem TomTom-Vergleich korrigiert.

## Wie es funktioniert

Ein Raspberry Pi zu Hause liest jede Minute die offenen Daten von GTT und 5T aus und speichert sie in einem Archiv. Python-Skripte verknüpfen sie mit den anderen Quellen, und die Seiten werden aus den Ergebnissen gebaut.

![Turin Meter: sources, Raspberry Pi, archive, scripts, pages](docs/img/architettura.svg)

### In Zahlen

<!-- IN-NUMERI-DE:INIZIO -->
- **~1,6 Mio.** per GPS gemessene Abfahrten an Haltestellen · **112** Verkehrssensoren · **8.317** Zählsprengel · **~12** offene Datenquellen
- **3** Wochen Arbeit · **485** nachvollziehbare Versionen
<!-- IN-NUMERI-DE:FINE -->

## Meine Rolle und die Arbeit mit KI

Mit KI wurde eine Arbeit, für die man sonst ein kleines Team braucht, schnell erledigt: Prototypen in Stunden, Prüfungen an den Daten während der Arbeit. Die Fragen, die Kriterien und Schwellenwerte sowie die Kontrolle der Zahlen sind der Hauptbeitrag des Urhebers; der Rest wurde weitgehend von der KI entwickelt, mit einer automatischen Kontrolle bei jeder Lieferung. Die Geschichte steht in der [Fallstudie](https://campeseleonardo-tech.github.io/turin-meter/progetto.html?lang=de).

## Methode

Die Methodendokumente gibt es nur auf Englisch: [`docs/en/METHODS.md`](docs/en/METHODS.md). Kurz gefasst:

- **Verspätungen:** aus dem GPS der Fahrzeuge, nicht aus dem offiziellen Feed (der sie unterschätzt); eine Abfahrt ist der letzte Zeitpunkt innerhalb von 60 m der Haltestelle. Eine Messung pro Minute ergibt eine Spanne.
- **Wo Verspätungen entstehen:** Zusatzzeit zwischen zwei aufeinanderfolgenden Haltestellen, verlorene Minuten pro Werktag, nur Abschnitte mit mindestens 50 Fahrten.
- **Autozeiten:** ein offenes Modell (OpenStreetMap-Netz, Geschwindigkeiten der 5T-Sensoren und der Busse, 20 Sekunden je Ampel, 5 Minuten fürs Parken), keine kostenpflichtigen Dienste.
- **Kontrolle mit TomTom** auf 20 Strecken: Die offene Schätzung erweist sich als zu optimistisch (auf 20 von 20 Strecken schneller), daher wird sie mit einem einheitlichen Faktor korrigiert.
- **Benachteiligung:** vom Projekt aus vier Indikatoren der Volkszählung 2021 gebauter Index; kein ISTAT-Index und kein Einkommen.
- **Park-and-Ride:** einfahrende Autos aus der Erhebung IMQ 2022 über ein Verkehrsmodell, Stellplätze aus OpenStreetMap, Stadt und 5T; fehlende Plätze sind eine Größenordnung.

## Daten, Lizenzen und Hinweis

Nur offene Daten; der Code steht unter der [MIT-Lizenz](LICENSE), die Daten behalten die Lizenz ihrer Quelle: siehe [`docs/de/DATENLIZENZEN.md`](docs/de/DATENLIZENZEN.md) (maßgeblich, englisch: [`DATA_LICENSES.md`](DATA_LICENSES.md)). Wo eine Quelle keine ausdrückliche Lizenz hat, werden nur aggregierte Werte veröffentlicht. TomTom wird nur per Programm abgefragt, um die Autoschätzung auf 20 Strecken zu kontrollieren; veröffentlicht wird davon nur die Zusammenfassung der Kontrolle.

*Unabhängiges privates Projekt: nicht verbunden mit oder unterstützt von GTT, 5T, der Stadt Turin oder anderen genannten Organisationen.*

## Grenzen

- Wenige Werktage im Oktober 2026: Die Zahlen beschreiben diesen Zeitraum, kein Jahr.
- Nur städtische Linien, die das GPS gesehen hat; eine Position pro Minute, daher sind Verspätungen eine Spanne.
- Die Autozeiten stammen aus einem offenen Modell, mit TomTom auf 20 Strecken kontrolliert; sie sind nicht auf einzelnen Fahrten gemessen.
- Keine Züge, keine anderen Betreiber; der Benachteiligungsindex stammt vom Projekt, ist kein offizieller Index und kein Einkommen.
- Die Preise sind die eines Tages.

## Berechnungen nachvollziehen

```
pip install -r requirements.txt     # für die ÖV-Fahrzeiten (r5py) wird auch Java 21 oder neuer gebraucht
python scripts/scarica_dati.py      # große Daten aus der GitHub-Release (IMQ und OMI von Hand: siehe docs/en/METHODS.md)
python scripts/rifai_tutto.py       # alles in der richtigen Reihenfolge (--elenco zeigt die Phasen, --riprendi setzt fort)
python scripts/prova_pagine.py      # Prüfung der Seiten
```

## Übersicht des Repositorys

Die Skripte, nach Phasen gruppiert, sind in [`scripts/README.md`](scripts/README.md) beschrieben (englisch).

## Kontakt

Leonardo Campese · [LinkedIn](https://www.linkedin.com/in/leocampese/) · [campese.leonardo@gmail.com](mailto:campese.leonardo@gmail.com)
