# Turin Meter — methods

This is the only methods document of the project and it is in English. Italian and German readers find a short summary in
[`README.it.md`](../../README.it.md) and [`README.de.md`](../../README.de.md). The sources and their licences are in
[`DATA_LICENSES.md`](../../DATA_LICENSES.md).

**Numbers are not written here.** Every figure shown on the site is written by a script from the data files and can be read on the
[site](https://campeseleonardo-tech.github.io/turin-meter/) or in `data/schede_risultati.js`. This document only states the rules.

The kind of data (read from sensors or vehicle GPS, calculated from a model, combined from census data) is stated in words in the part of each card that explains how the number is calculated, together with the limits. A card ends with its sources.

## Common parts

### Collection
A Raspberry Pi reads, about once a minute, the GTT real-time feeds (vehicle positions, trip updates) and the 5T traffic sensors and car-park counters.
Everything goes into a SQLite archive. The scripts read the archive read-only; the raw archive is not published, only summaries.
Period used for the first release: whole days only, never the day of the copy (`comuni.PERIODO`). All time conversions go through `scripts/comuni.py` (Italian local time).

### Area and units
Turin and its surrounding belt (the metropolitan city), with 2021 census sections as the smallest unit. Stops and roads are matched **by coordinates, never by name**.
A street that changes name along the route is one axis.

### Accessibility engine
Walking times and public transport times use the R5 routing engine (`r5py`, Java 21 or later) on the OpenStreetMap network and the GTFS timetable valid on each day.
Walking speed 4.8 km/h. Timetable-based times are optimistic by construction; the scripts add the **measured waiting time and the measured delay on board**.

### Open estimate of car times
Used by findings 2 and 4.
- **Network:** the OpenStreetMap drivable graph; the fastest route in time.
- **Speed of a segment by hour:** (a) where the segment is matched to a reliable 5T sensor, the median measured speed at that hour; (b) elsewhere, the free-flow speed
  (OSM limit, else the road-class value, at most 50 km/h inside built-up areas) times **k(zone, hour)**.
- **k(zone, hour):** from bus probes (script 107): the median speed of buses **in motion** at that hour divided by the speed at 5–6 a.m., in the travel-survey zone.
  Positions within 60 m of a stop of the line are excluded; buses only. A cell needs at least 300 pairs of consecutive positions (30–120 s apart), otherwise the city-wide value is used. k is clamped to 0.3–1.
- **Traffic lights:** OSM `traffic_signals` nodes on the route; nodes within 50 m count as one junction; 20 seconds average delay each, at every hour. Sensitivity: 10 and 30 seconds.
- **Parking and walking:** +5 minutes.
- **Most car-friendly estimate:** 5T sensor speeds with a single factor, no traffic lights; used only as an extreme in sensitivity checks.
- **Sanity checks** (a failed check is a warning, reviewed before publishing): night times stay within ±25% of free flow plus traffic lights; Piazza Castello → Collegno at 8 a.m. is between 20 and 35 minutes;
  rush-hour k is below night k; at least 70% of route length has a sensor or a zone k. Report: `RAPPORTO_STIMA_AUTO.txt` (private working report).

### Manual check of car times with TomTom
- **Routes:** 20, fixed in advance: the 12 entry points of finding 4 → Piazza Castello, plus the 8 most frequent morning car trips (travel-survey zone pairs).
- **Reading:** `scripts/108_controllo_navigatori.py --tomtom` asks the TomTom Routing API for the predicted travel time with traffic for the following Tuesday at 7:45, 8:00 and 8:15 (minimum and maximum kept).
  This is the **only** place where a proprietary service is read by a program, and only to check the estimate; no TomTom value enters an estimate.
  The script saves only the summary (`data/processed/controllo_navigatori_riepilogo.json`): median signed and absolute error, routes inside the TomTom range.
- **Result handling:** the check found the open estimate systematically faster than TomTom (on 20 routes out of 20). Rather than hide this, car times in findings 2 and 4 are the open estimate **corrected with a single factor**:
  time = (open estimate − 5 min) × f + 5 min, with f = 1 / (1 + median signed error), read from the summary file, never typed by hand.
  Only this corrected time is shown; classes (public transport worth it or not) are decided on it alone.
- **Terms of use:** the project has no special permission from TomTom. The TomTom terms of use limit storing results and building databases from them (clauses on saving results and derived databases),
  which is why results are not saved, only the summary, and why TomTom is named only as the source of the check. This remains a risk to be weighed again before wider use.
  Google Maps is never read by a program; it can be used by hand only.

## Finding 1 — Delays of buses and trams (measured)
- **Question:** how often are GTT buses and trams late, and where do they lose time?
- **Data:** GTFS timetable and the vehicle positions collected every minute; urban lines seen by GPS.
- **Method:** a *departure* is the last GPS instant within 60 m of the stop (segments between two positions at most 180 s long, stops searched in `stop_sequence` order). Delay = that instant minus the timetable time
  (GTFS arrival equals departure for GTT). Classes: early below −1 minute, late above 5 and above 10 minutes. A day counts only if the GPS saw at least half the median number of trips of days of the same type.
- **Reading step:** one position per minute means the true departure can be up to a minute *earlier* than measured. The script is re-run with 0, 30 and 60 seconds of shift; the big number is the 0-second (most prudent) value,
  the range is in the calculation. The point on early departures is shown only if the share stays above 15% even at +60 s.
- **Where delays arise (script 106):** for each pair of consecutive stops of a trip, extra time = (time at stop k+1 − time at stop k) − (scheduled difference). Minutes lost per weekday = sum of positive extra times / number of weekdays; a segment counts with at least 50 observed trips in the band.
  Check: on complete trips the sum of extra times equals final minus initial delay (difference under 1%).
- **Comparison with GTT:** GTT declares a 2025 yearly figure (all lines, method not published); here the GPS measures October weekdays on urban lines. The two are not the same quantity.
- **Limits:** a handful of October weekdays; urban lines seen by GPS only; one position per minute; it counts how often there is delay, not how many people wait.
- **Redo:** `python scripts/rifai_tutto.py --solo r4`.

## Finding 2 — Car or public transport: time and money (estimated)
- **Question:** how much longer does public transport take than the car, and what does the car cost?
- **Data:** travel-survey zones with calculation points (up to 5 per zone); R5 routing; open car estimate; measured waiting and delay; prices.
- **Method:** public transport time = R5 median over departures 7:45–8:15 with measured extra waiting and delay on board. Car = open estimate plus 5 minutes, corrected with the single factor (see above).
  The ratio is public transport time / car time over the car trips of the survey between different zones (weighted by the cars of each pair); the headline number is the simple mean of the median ratio at 4 times of the day (8:00, 13:00, 17:30, 21:00), computed in one function, `rapporto_medio_giorno`, and read from the data files.
- **Costs:** prices of one day (fuel self-service within 5 km of Piazza Castello, ACI 2026 running costs for a reference compact car, GTT fares, on-street parking at the ordinary rate for 8 hours × 20 days).
  *Out-of-pocket cost* = fuel + parking; *full cost* = ACI per-km cost + parking.
- **Value of time:** v = (extra monthly cost with paid parking) / (extra minutes per trip × 2 trips × 20 days / 60), rounded to 5 €; also computed with the full cost.
- **Limits:** no trains and no other operators; scheduled timetable corrected with measurements; one reference car; restricted-traffic zones and parking permits left out; prices of one day.
- **Redo:** `python scripts/rifai_tutto.py --solo r8`.

## Finding 3 — Vulnerability and services (calculated)
- **Question:** who lives where social difficulties are high and services are few?
- **Index:** **built by this project**, from four 2021 census indicators: not employed (15–64), low education, crowding, share of over-65s. **It is not an official ISTAT index** and not income. A circularity check confirms that no service or green-space component is inside it.
- **Services:** the «all services» score within 15 minutes on foot on the OpenStreetMap network; also 5 and 10 minutes.
- **Thresholds:** the highest 20% for vulnerability and the lowest 20% for services. «By chance» means «if the two were independent».
- **Links at equal distance from the centre:** partial rank correlation controlling for the distance of the zone from Piazza Castello, with a 95% interval by resampling zones (2,000 draws, fixed seed); a link «holds» only if the interval excludes 0.
  The price–services link does not hold and is therefore not shown.
- **Limits:** the index is not income; a service is counted if it exists, not by size; OMI prices are quotes, not sales; OMI zones are large.
- **Redo:** `python scripts/rifai_tutto.py --solo r10`.

## Finding 4 — Park-and-ride (estimated, deep dive)
- **Question:** can people driving in from outside leave the car near an important stop and continue by public transport?
- **Important stops:** outside the centre, with a metro, train station or terminus, or at least a fixed number of departures per hour in commuting hours, and at least a fixed number of cars passing (parameters in the finding card).
- **Cars:** inbound car trips from the 2022 travel survey assigned to the fastest route; the share that already leaves the car is applied. **Spaces:** suitable car parks within 400 m on foot (City, 5T, OpenStreetMap).
- **Priority points:** stops without enough spaces grouped within 1 km, one per entry axis. **Missing spaces** are an order of magnitude, with a sensitivity for half and double the people leaving the car.
- **Bus against car:** public transport minutes to Piazza Castello at 8 a.m. against the car (corrected as above) plus parking; the bus is «worth it» if it takes at most 1.5 times the car.
- **Limits:** car flows come from a simple traffic model; occupancy is measured on few days and only where 5T reports it; trains are not included.
- **Redo:** `python scripts/rifai_tutto.py --solo r6`.

## Checks and reproducibility
`python scripts/controllo_completo.py` compiles the scripts, runs pyflakes, tests on synthetic data, checks that the cards in git are those produced by the data, file weights, links, and a browser test.
`python scripts/rifai_tutto.py --elenco` lists the phases; large data come from the GitHub Release (`scripts/scarica_dati.py`, hashes checked).

## Data to download by hand
The large data come from the GitHub Release (`python scripts/scarica_dati.py`). Two sources are **not** republished because their licence is unclear (see `DATA_LICENSES.md`) and are downloaded from the source:
- IMQ 2022 travel survey, open data page of the Piedmont Mobility Agency: <https://mtm.torino.it/it/dati-statistiche/indagini-old/indagine-imq-2021/open-data-imq-2022/> → `data/raw/IMQ2022_opendata_web/`, then `python scripts/14_prepara_imq.py`.
- OMI price quotes and zone perimeters, Revenue Agency: <https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/banche-dati/quotazioni-immobiliari> → `data/raw/omi_2025_2/`, then `python scripts/08_prepara_omi.py`.
- Road network: OpenStreetMap extract from Geofabrik (<https://download.geofabrik.de/europe/italy/nord-ovest.html>), cut by `scripts/17_taglia_osm.py`.

Then `python scripts/rifai_tutto.py --da dati`. The pages work without them; the calculations that need them stop with a message saying what to download.
