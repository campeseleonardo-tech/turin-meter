# -*- coding: utf-8 -*-
"""
scripts/58_corsie.py - Pacchetto B (Fase 5), parte 2: corsie e capacita'.

Legge la rete con i tag lanes (script 56) e produce, per ogni TRATTA (script 57)
e per ogni tratto, corsie e capacita'. Con la copertura dei tag e il confronto a
mano su 10 strade note.

Tabella dichiarata capacita' per corsia (veicoli/ora): vedi CAPACITA_CORSIA in
rete_osm.py (valori standard HCM/pratica urbana). Valori standard di corsie per
verso quando il tag manca: CORSIE_DEFAULT_VERSO.

Output: data/processed/traffico_d/corsie.csv
        data/processed/traffico_d/tratte_corsie.json
        docs/rapporti/RAPPORTO_CORSIE.txt
"""

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import rete_osm  # noqa: E402


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
PROC = RADICE / "data" / "processed"
OUT = PROC / "traffico_d"
RETE_DIR = OUT / "rete"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_CORSIE.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)


def main():
    rete = rete_osm.carica(RETE_DIR)
    meta = rete["meta"]
    n_edge = len(rete["edge_a"])
    hw = meta["highway"]
    corsie_av = np.array(meta["corsie_avanti"]) if "corsie_avanti" in meta else np.ones(n_edge, int)
    corsie_in = np.array(meta["corsie_indietro"]) if "corsie_indietro" in meta else np.ones(n_edge, int)
    stimate = np.array(meta["corsie_stimate"]) if "corsie_stimate" in meta else np.ones(n_edge, bool)
    edge_len = rete["edge_len"]

    # copertura per classe
    per_classe = defaultdict(lambda: [0, 0, 0.0, 0.0])  # n, n_tag, km, km_tag
    for e in range(n_edge):
        c = hw[e]
        per_classe[c][0] += 1
        per_classe[c][2] += float(edge_len[e])
        if not bool(stimate[e]):
            per_classe[c][1] += 1
            per_classe[c][3] += float(edge_len[e])

    # tratte
    tratte = json.loads((OUT / "tratte.json").read_text(encoding="utf-8"))["tratte"]
    out = []
    for t in tratte:
        cls = t["classe"]
        cap = rete_osm.CAPACITA_CORSIA.get(cls, 500)
        cav = t["corsie_avanti"]
        cin = t["corsie_indietro"]
        out.append({
            "id": t["id"], "asse": t["asse"], "nome": t["nome_principale"],
            "classe": cls, "corsie_avanti": cav, "corsie_indietro": cin,
            "corsie_totali": round(cav + cin, 2),
            "corsie_stimate": bool(t.get("corsie_stimate", True)),
            "capacita_corsia": cap,
            "capacita_oraria": round((cav + cin) * cap, 0),
            "capacita_verso_max": round(max(cav, cin) * cap, 0),
        })
    (OUT / "tratte_corsie.json").write_text(json.dumps({
        "stimato": False,
        "nota": ("Corsie per tratta dal tag OSM lanes (valori standard dichiarati dove manca) "
                 "e capacita' per corsia dalla tabella CAPACITA_CORSIA (rete_osm.py)."),
        "capacita_corsia": rete_osm.CAPACITA_CORSIA,
        "corsie_default_verso": rete_osm.CORSIE_DEFAULT_VERSO,
        "tratte": out,
    }, ensure_ascii=False), encoding="utf-8")

    with (OUT / "corsie.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["id_tratta", "id_asse", "nome", "classe", "corsie_avanti", "corsie_indietro",
                    "corsie_totali", "corsie_stimate", "capacita_corsia", "capacita_oraria"])
        for o in out:
            w.writerow([o["id"], o["asse"], o["nome"] or "", o["classe"], o["corsie_avanti"],
                        o["corsie_indietro"], o["corsie_totali"], int(o["corsie_stimate"]),
                        o["capacita_corsia"], o["capacita_oraria"]])

    # --- 10 strade note ---
    from importlib import import_module
    norm = import_module("24_importanza_vie").normalizza
    note = ["Corso Racconigi", "Corso Re Umberto", "Corso Francia", "Via Nizza",
            "Corso Vittorio Emanuele II", "Lungo Po Armando Diaz", "Corso Unita' d'Italia",
            "Corso Giulio Cesare", "Via Agudio", "Corso Cosenza"]
    per_nome = defaultdict(list)
    for e in range(n_edge):
        if meta["nomi"][e]:
            per_nome[norm(meta["nomi"][e])].append(e)

    righe = []
    def a_(s=""):
        righe.append(s)
    a_("CORSIE E CAPACITA' (pacchetto B, Fase 5)")
    a_("=" * 74)
    a_("Tabella capacita' per corsia (veic/ora) usata:")
    for k, v in rete_osm.CAPACITA_CORSIA.items():
        a_(f"    {k:14s} {v}")
    a_("Corsie per verso quando manca il tag 'lanes' (valori standard DICHIARATI):")
    a_("    " + ", ".join(f"{k}={v}" for k, v in rete_osm.CORSIE_DEFAULT_VERSO.items()))
    a_("")
    a_("== Copertura del tag 'lanes' per classe ==")
    a_(f"{'classe':14s} {'tratti':>8s} {'con tag':>8s} {'%':>6s} {'km':>9s} {'km con tag':>11s} {'%':>6s}")
    for c, (n, nt, km, kmt) in sorted(per_classe.items(), key=lambda kv: -kv[1][2]):
        a_(f"{c:14s} {n:8d} {nt:8d} {100*nt/max(n,1):5.1f}% {km/1000:9.1f} {kmt/1000:11.1f} "
           f"{100*kmt/max(km,1):5.1f}%")
    tot_n = sum(v[0] for v in per_classe.values())
    tot_nt = sum(v[1] for v in per_classe.values())
    tot_km = sum(v[2] for v in per_classe.values())
    tot_kmt = sum(v[3] for v in per_classe.values())
    a_(f"{'TOTALE':14s} {tot_n:8d} {tot_nt:8d} {100*tot_nt/max(tot_n,1):5.1f}% "
       f"{tot_km/1000:9.1f} {tot_kmt/1000:11.1f} {100*tot_kmt/max(tot_km,1):5.1f}%")
    a_("")
    a_("== Controllo a mano su 10 strade note (tag OSM trovati) ==")
    for nome in note:
        chiave = norm(nome)
        idx = per_nome.get(chiave, [])
        if not idx:
            a_(f"  {nome:32s}: nessun tratto con questo nome")
            continue
        av = int(np.median([corsie_av[e] for e in idx]))
        ind = int(np.median([corsie_in[e] for e in idx]))
        ntag = sum(1 for e in idx if not bool(stimate[e]))
        klass = Counter(hw[e] for e in idx).most_common(1)[0][0]
        a_(f"  {nome:32s}: {len(idx):4d} tratti  corsie av/ind (mediana) {av}/{ind}  "
           f"classe {klass:10s}  con tag lanes {ntag}")
    a_("")
    a_("Nota: dove le corsie sembrano sbagliate si veda il tag grezzo in "
       "rete_auto_metadati.json (campi maxspeed_raw/width_raw). I sensori 5T misurano "
       "un flusso per corsia teorico; le corsie 'stimate' sono dichiarate.")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))
    print(f"\nScritti {OUT/'corsie.csv'} e {OUT/'tratte_corsie.json'}")


if __name__ == "__main__":
    main()
