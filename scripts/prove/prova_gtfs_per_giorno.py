#!/usr/bin/env python3
"""Prova senza dati veri del GTFS per giorno (PIANO_RACCOLTA passo 2b, L7): in una cartella temporanea due versioni finte del GTFS
con date diverse; ogni giorno deve usare quella valida allora, e prima del primo archivio il GTFS di data/raw."""
import importlib.util
import sys
import tempfile
import zipfile
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI.parent))
spec = importlib.util.spec_from_file_location("r4", QUI.parent / "27_risultato4_regolarita.py")
r4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r4)

ERRORI = 0


def esito(nome, ok):
    global ERRORI
    print(("OK     " if ok else "ERRORE ") + nome)
    ERRORI += 0 if ok else 1


def zip_finto(percorso, corse):
    with zipfile.ZipFile(percorso, "w") as z:
        z.writestr("routes.txt", "route_id,route_short_name,route_type\nR1,1,3\nR2,M,1\n")
        z.writestr("stops.txt", "stop_id,stop_name,stop_lat,stop_lon\nS1,Uno,45.0,7.6\nS2,Due,45.01,7.61\n")
        z.writestr("trips.txt", "route_id,trip_id,direction_id\n" + "".join(f"R1,{t},0\n" for t in corse))
        z.writestr("stop_times.txt", "trip_id,arrival_time,stop_sequence,stop_id\n"
                   + "".join(f"{t},08:00:00,1,S1\n{t},08:10:00,2,S2\n" for t in corse))


with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    raw, arch = t / "gtfs_raw.zip", t / "gtfs_archivio"
    arch.mkdir()
    zip_finto(raw, ["VECCHIA"])
    zip_finto(arch / "gtt_gtfs_20261020.zip", ["PRIMA"])
    zip_finto(arch / "gtt_gtfs_20261025.zip", ["SECONDA"])
    zip_finto(arch / "gtt_gtfs_20261025_2.zip", ["TERZA"])        # stesso giorno, secondo scaricamento: vale quest'ultimo
    (arch / "altro.zip").write_bytes(b"x")                         # nome estraneo: ignorato
    r4.GTFS, r4.GTFS_ARCHIVIO = raw, arch
    esito("versioni trovate: 3, in ordine, nome estraneo ignorato", [d for d, _ in r4.versioni_gtfs()] == ["20261020", "20261025", "20261025"])
    esito("prima del primo archivio: il GTFS di data/raw", r4.gtfs_del_giorno("20261019") == raw)
    esito("dal giorno del primo archivio: quello", r4.gtfs_del_giorno("20261020").name == "gtt_gtfs_20261020.zip"
          and r4.gtfs_del_giorno("20261024").name == "gtt_gtfs_20261020.zip")
    esito("dal giorno del secondo: il secondo scaricamento di quel giorno", r4.gtfs_del_giorno("20261025").name == "gtt_gtfs_20261025_2.zip"
          and r4.gtfs_del_giorno("20261130").name == "gtt_gtfs_20261025_2.zip")
    g = r4.GtfsPerGiorno(True)
    corse = {d: sorted(g.stato(d).trip_info) for d in ("20261019", "20261022", "20261026")}
    esito("ogni giorno vede le corse della sua versione", corse == {"20261019": ["VECCHIA"], "20261022": ["PRIMA"], "20261026": ["TERZA"]})
    esito("prima_seq e fermate caricate", g.stato("20261026").prima_seq == {"TERZA": 1} and len(g.stato("20261026").fermate) == 2)
    esito("modi_linea: 1 bus, M metro", r4.modi_linea(raw) == {"1": "bus", "M": "metro"})
    r4.GTFS_ARCHIVIO = None
    esito("senza archivio: sempre data/raw (nessun cambio con un solo GTFS)", r4.gtfs_del_giorno("20261130") == raw)
sys.exit(1 if ERRORI else 0)
