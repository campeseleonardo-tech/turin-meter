#!/usr/bin/env python3
"""38b_codici_condivisi.py

Vedi sviluppo/note_tecniche/R8_traffico.md: i codici `lcd1` condivisi da due
sensori fisici diversi.

(i) legge il file XML grezzo del 3/10 (`data/raw/5t_flussi_20261003_224539.xml`)
    e conta le voci e i codici distinti; attesi 112 voci, 109 codici, e i tre
    codici doppi 40123, 40189, 13077 (per ognuno stampa le due voci: verso,
    offset, lat, lng, accuratezza).
(ii) nel database (sola lettura) per i tre codici stampa la riga di `sensori_5t`
    e quante righe di `flussi_5t` esistono per ogni `generato_utc` (atteso 1).
(iii) segna i tre codici con `"codice_condiviso": true` in
    `data/processed/sensori_corridoi_v2.json` (e il Passo 9 lo riporterà nei suoi
    file). 40189 resta usabile ma NON per il metodo B; 40123 e 13077 restano
    esclusi se lo erano.

NON modifica lo script 03 ne' il database. Se i numeri attesi non tornano, esce
con un errore (l'agente si ferma).
"""

import json
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
DB = RADICE / "data" / "storico_backup.sqlite"
XML = RADICE / "data" / "raw" / "5t_flussi_20261003_224539.xml"
V2 = RADICE / "data" / "processed" / "sensori_corridoi_v2.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_CODICI_CONDIVISI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

ATTESI_VOCI = 112
ATTESI_CODICI = 109
ATTESI_DOPPI = {"40123", "40189", "13077"}

RIGHE = []


def scrivi(msg=""):
    RIGHE.append(str(msg))


def main():
    if not XML.is_file():
        raise SystemExit(f"XML grezzo non trovato: {XML}")

    albero = ET.parse(XML)
    voci = []
    for el in albero.iter():
        if el.tag.endswith("FDT_data"):
            voci.append(dict(lcd1=str(el.get("lcd1")),
                             road_lcd=el.get("Road_LCD"),
                             nome=el.get("Road_name"),
                             offset=el.get("offset"),
                             direction=el.get("direction"),
                             lat=el.get("lat"), lng=el.get("lng"),
                             accuracy=el.get("accuracy")))
    per_codice = {}
    for v in voci:
        per_codice.setdefault(v["lcd1"], []).append(v)
    doppi = {k: v for k, v in per_codice.items() if len(v) > 1}

    scrivi("CODICI SENSORE CONDIVISI (Passo 8c, sola lettura)")
    scrivi("=" * 78)
    scrivi(f"file: {XML.name}")
    scrivi("")
    scrivi("(i) Controlli sul file XML grezzo")
    scrivi(f"  voci FDT_data: {len(voci)}   [atteso {ATTESI_VOCI}]")
    scrivi(f"  codici lcd1 distinti: {len(per_codice)}   [atteso {ATTESI_CODICI}]")
    scrivi(f"  codici con piu' di una voce: {len(doppi)} -> {sorted(doppi)}   "
           f"[attesi {sorted(ATTESI_DOPPI)}]")
    ok_xml = (len(voci) == ATTESI_VOCI and len(per_codice) == ATTESI_CODICI
              and set(doppi) == ATTESI_DOPPI)
    for k in sorted(doppi):
        scrivi(f"  -- {k}: {len(doppi[k])} voci")
        for v in doppi[k]:
            scrivi(f"       verso {v['direction']:8s} offset {v['offset']:>6s} "
                   f"lat {v['lat']} lng {v['lng']} accuratezza {v['accuracy']:>4s}  "
                   f"({v['nome']})")

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    con.execute("PRAGMA busy_timeout=60000")
    cur = con.cursor()
    scrivi("")
    scrivi("(ii) Cosa c'e' nel database per quegli stessi codici")
    righe_db = {}
    max_per_istante = {}
    parentesi_ok = True
    for k in sorted(ATTESI_DOPPI):
        r = cur.execute("SELECT lcd1, nome_strada, offset_m, direzione, lat, lng "
                        "FROM sensori_5t WHERE lcd1 = ?", (k,)).fetchone()
        righe_db[k] = r
        n_per_gen = cur.execute("SELECT MAX(n) FROM (SELECT COUNT(*) AS n FROM flussi_5t "
                                "WHERE lcd1 = ? GROUP BY generato_utc)", (k,)).fetchone()[0]
        tot = cur.execute("SELECT COUNT(*) FROM flussi_5t WHERE lcd1 = ?", (k,)).fetchone()[0]
        n_istanti = cur.execute("SELECT COUNT(DISTINCT generato_utc) FROM flussi_5t "
                                "WHERE lcd1 = ?", (k,)).fetchone()[0]
        max_per_istante[k] = (n_per_gen or 0, tot, n_istanti)
        if (n_per_gen or 0) != 1:
            parentesi_ok = False
        scrivi(f"  -- {k}: sensori_5t -> nome {r[1]!r} offset_m {r[2]} verso {r[3]} "
               f"lat {r[4]} lng {r[5]}")
        scrivi(f"       flussi_5t: {tot} righe su {n_istanti} istanti, "
               f"massimo righe per istante = {n_per_gen}   [atteso 1]")
    con.close()

    # (iii) marcatura nei file
    v2 = json.loads(V2.read_text(encoding="utf-8"))
    condivisi = {}
    for k in sorted(ATTESI_DOPPI):
        r = righe_db[k]
        condivisi[k] = dict(
            codice_condiviso=True,
            nome=n(r[1] if r else None),
            offset_m_db=(r[2] if r else None),
            direzione_db=(r[3] if r else None),
            lat_db=(r[4] if r else None),
            lon_db=(r[5] if r else None),
            voci_xml=[dict(direction=v["direction"], offset=v["offset"], lat=v["lat"],
                           lng=v["lng"], accuracy=v["accuracy"]) for v in doppi.get(k, [])],
            posizione_sicura=False,
            nota=("il codice e' usato da due sensori fisici: nel database la posizione "
                  "viene dall'ultimo arrivato e il flusso dal primo, quindi non e' detto "
                  "che siano lo stesso punto"))
    for k, s in v2.get("sensori", {}).items():
        if k in condivisi:
            s["codice_condiviso"] = True
            s["posizione_sicura"] = False
    v2["codici_condivisi"] = condivisi
    V2.write_text(json.dumps(v2, ensure_ascii=False, separators=(",", ":")),
                  encoding="utf-8")

    in_v2 = [k for k in sorted(ATTESI_DOPPI) if k in v2.get("sensori", {})]
    scrivi("")
    scrivi("(iii) Marcatura")
    scrivi(f"  codici marcati 'codice_condiviso: true' in {V2.name}: {sorted(ATTESI_DOPPI)}")
    scrivi(f"  di questi, presenti fra i 92 sensori usabili (Passo 8): {in_v2 or 'nessuno'}")
    scrivi(f"  40189: usabile ma NON per il metodo B (posizione non sicura) -> "
           f"{'presente' if '40189' in in_v2 else 'NON presente'}")

    testo = "\n".join(RIGHE)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.write(testo + "\n")
    RAPPORTO.write_text(testo + "\n", encoding="utf-8")
    print(f"Rapporto salvato: {RAPPORTO}")
    if not (ok_xml and parentesi_ok):
        print("CONTROLLI: NON TORNANO -> FERMARSI")
        return 1
    print("CONTROLLI: OK (112 voci, 109 codici, tre codici doppi; 1 riga per istante)")
    return 0


def n(x):
    return "" if x is None else x


if __name__ == "__main__":
    sys.exit(main())
