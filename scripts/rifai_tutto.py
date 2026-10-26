#!/usr/bin/env python3
"""
rifai_tutto.py - un comando per rifare tutti i calcoli, nell'ordine giusto: dati -> accessibilita' -> traffico -> risultati -> schede -> mappa -> prova.

Gli script restano quelli numerati di scripts/; i .bat sono scorciatoie per Windows. Qui l'ordine e' scritto una volta sola (ricavato dai .bat e da docs/R*.md).
Si ferma al primo errore, salva a che punto e' arrivato (logs/rifai_tutto_stato.json) e riparte da li' con --riprendi.

Prima: python scripts/scarica_dati.py (dati grandi dalla Release di GitHub). IMQ e OMI si scaricano a mano dalla fonte (sviluppo/note_tecniche/DATI.md).
Non rifa: la raccolta sul Raspberry Pi (03, 12, 06, supervisore), l'esportazione dell'IMQ (13, 14-16: dati a mano), il rapporto di sostenibilita' (30-32, chiuso),
i riassunti dello storico si rifanno solo se esiste data/storico_backup.sqlite.

Come si lancia
--------------
  python scripts/rifai_tutto.py --elenco                 mostra le fasi e i comandi, senza lanciare niente
  python scripts/rifai_tutto.py                          tutto, dall'inizio (puo' durare molte ore: l'accessibilita' e il traffico sono le fasi lunghe)
  python scripts/rifai_tutto.py --riprendi               dopo un errore: ricomincia dal primo comando non finito
  python scripts/rifai_tutto.py --solo schede,mappa      solo alcune fasi (nell'ordine canonico), per esempio dopo aver cambiato un testo
  python scripts/rifai_tutto.py --da r6                  dalla fase r6 in poi
  python scripts/rifai_tutto.py --prova-secca            controlla che ogni script esista, senza lanciarlo

Fasi: riassunti, dati, accessibilita, traffico, r1, r4, r8, r6, r10, schede, mappa, prova.
Log: logs/rifai_tutto.log (ogni comando con la sua uscita). Codice di uscita 0 = tutto fatto, 1 = fermato per un errore.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RADICE = AQUI.parent
LOGS = RADICE / "logs"
LOG = LOGS / "rifai_tutto.log"
STATO = LOGS / "rifai_tutto_stato.json"

ACC24 = ["18_accessibilita.py", "--giorno", "2026-10-12", "--ore", ",".join(str(h) for h in range(24)), "--lotto-piedi", "100", "--lotto-tp", "20",
         "--salva-tappe", "--velocita-piedi", "80", "--velocita-tp", "4.8"]

# (fase, durata indicativa, [(comando = script e argomenti, nota o None)]): l'ordine e' quello dei .bat
# Un comando con "riprova" e' ripetuto fino a 3 volte (come i .bat dell'accessibilita'); con "pulisci" cancella prima i parziali dell'accessibilita'.
FASI = [
    ("riassunti", "10-20 minuti", [(["97_riassunti_storico.py"], "solo se c'e' data/storico_backup.sqlite")]),
    ("dati", "10-30 minuti", [(["05_prepara_sezioni.py"], None), (["08_prepara_omi.py"], None), (["11_prepara_catalogo.py"], None),
                              (["17_taglia_osm.py"], "serve l'OSM grezzo di data/raw (se manca si salta: il risultato data/otp/rete/torino_cintura.osm.pbf c'e' gia'); salta_se_manca=data/raw/nord-ovest-261008.osm.pbf"), (["19_vulnerabilita.py"], None), (["20_servizi_osm.py"], None)]),
    ("accessibilita", "molte ore", [(ACC24, "riprova"), (["18_accessibilita.py", "--solo-piedi", "--cutoff-piedi", "10", "--out", "data/processed/accessibilita_piedi10.json", "--salva-tappe"], "riprova,pulisci"),
                                    (["18_accessibilita.py", "--solo-piedi", "--cutoff-piedi", "5", "--out", "data/processed/accessibilita_piedi5.json", "--salva-tappe"], "riprova,pulisci")]),
    ("traffico", "alcune ore", [(["26_velocita_5t.py"], None), (["33_flusso_sensori.py"], None), (["24_importanza_vie.py"], None), (["39_fattibilita_rete.py"], None),
                                (["40_domanda_imq.py"], None), (["41_zone_punti.py"], None), (["42_instradamento.py"], None), (["35_sensori_esclusi.py"], None),
                                (["36_abbinamento_posizione.py"], None), (["38b_codici_condivisi.py"], None), (["37_traffico_AB.py"], None), (["43_segmenti_corridoi.py"], None),
                                (["44_taratura_validazione.py"], None), (["45_prodotto_finale.py"], None), (["49_v3_punti_domanda.py"], None), (["50_v3_assegnazione.py"], None),
                                (["50b_v3_valutazione.py"], None), (["51_tp_gtfs_tratti.py"], None), (["52_tp_corridoi.py"], None), (["53_pubblicazione_traffico.py"], None),
                                (["54_incrocio_traffico_tp.py"], None), (["56_build_rete_lanes.py"], None), (["57_assi_tratte.py"], None), (["58_corsie.py"], None), (["59_ztl.py"], None),
                                (["60_tp_fermate.py"], None), (["61_tp_tratte.py"], None), (["62_v4_modello.py", "--variante", "v4", "--iter", "8", "--outdir", "v4"], "circa 1 ora"),
                                (["63_v4_valutazione.py"], None), (["65_affidabilita.py"], None), (["66_pubblicazione_incrocio.py"], None), (["67_verifiche_fase5.py"], None)]),
    ("r1", "pochi minuti", [(["21_risultato1_vuoti.py"], None), (["22_risultato1_candidati.py"], None), (["23_vulnerabilita_incrocio.py"], None), (["92_esposizione_traffico.py"], None)]),
    ("r4", "10-20 minuti", [(["27_risultato4_regolarita.py", "--sposta-secondi", "60"], "forbice della lettura al minuto (F3): giro con i passaggi spostati di 60 s"), (["27_risultato4_regolarita.py", "--sposta-secondi", "30"], None), (["27_risultato4_regolarita.py"], "giro a 0 s: scrive anche la forbice della lettura"), (["106_dove_nascono_ritardi.py"], "tratti fra fermate dove nascono i ritardi (serve la copia dello storico)"), (["70_risultato9_attesa.py"], None), (["105_correzione_tempi_mezzi.py"], "ritardo per minuto dal GPS e quota a bordo (r5py): serve prima di 93, 94 e 100"), (["104_velocita_bus.py"], "con la copia dello storico; senza, tiene il file com'e'")]),
    ("r8", "10-30 minuti", [(["107_sonde_bus.py"], "i bus come sonde del traffico: serve la copia dello storico"), (["93_tp_contro_auto.py"], "r5py: la parte lenta"), (["102_scelta_del_mezzo.py"], "legge i file IMQ dal disco"), (["99_area_tempi.py"], None)]),
    ("r6", "10 minuti", [(["25_risultato6_interscambio.py"], None), (["68_luoghi_fermate.py"], None), (["69_parcheggi_inventario.py"], None), (["71_parcheggi_riempimento.py"], None),
                         (["72_nodi_tp.py"], None), (["73_segnali_criticita.py"], None), (["81_auto_di_passaggio.py"], None), (["88_confronto_auto_sensori.py"], None),
                         (["82_parcheggi_adatti.py"], None), (["87_popolarita_zone.py"], None), (["83_fermate_importanti.py"], None), (["84_risultato6_parcheggi.py"], None),
                         (["94_r6_bus_contro_auto.py"], None), (["100_ore_del_giorno.py"], "bus contro auto a 4 ore del giorno (r5py, dopo 93 e 94)"), (["103_costo_del_viaggio.py"], "legge i prezzi di data/ref/costi.json (a mano) e i risultati di 93 e 94"), (["79_dati_mappa_r6.py"], None), (["85_verifiche_correzioni.py"], None)]),
    ("r10", "pochi minuti", [(["95_case_fragilita_servizi.py"], None)]),
    ("schede", "1 minuto", [(["schede_risultati.py"], "scrive anche data/home_mezzi.js, data/progetto.js, data/area_tempi.js e le pagine r/N.html")]),
    ("mappa", "1-2 minuti", [(["04_genera_mappa.py"], None)]),
    ("prova", "5-10 minuti", [(["86_controlla_file_pagine.py"], None), (["prova_pagine.py"], "0 errori attesi")]),
]
NOMI = [f[0] for f in FASI]


def comandi(fasi):
    """[(id, fase, argv dello script, note)] nell'ordine; l'id e' fase + comando, serve per riprendere."""
    out = []
    for nome, _durata, lista in FASI:
        if nome not in fasi:
            continue
        for argv, note in lista:
            out.append((f"{nome}: {' '.join(argv)}", nome, argv, note or ""))
    return out


def scegli_fasi(args):
    if args.solo:
        scelte = [x.strip() for x in args.solo.split(",") if x.strip()]
        for s in scelte:
            if s not in NOMI:
                sys.exit(f"Fase sconosciuta: {s}. Fasi: {', '.join(NOMI)}")
        return [n for n in NOMI if n in scelte]
    if args.da:
        if args.da not in NOMI:
            sys.exit(f"Fase sconosciuta: {args.da}. Fasi: {', '.join(NOMI)}")
        return NOMI[NOMI.index(args.da):]
    return list(NOMI)


# File derivati da IMQ e OMI: fuori da git (giro L12). Se mancano, si ferma subito e dice cosa scaricare.
FONTI_IMQ = ["imq_zone.json", "imq_zone_geo.json", "imq_od.json", "imq_aggregati.json", "imq_residenti.json", "imq_mappa.json"]
FONTI_OMI = ["omi_zone.json"]
FONTI_DOMANDA = ["traffico_c/domanda_auto.json", "traffico_c/v3/domanda_v3.json"]


def controlla_fonti(fasi):
    """Ritorna un messaggio se mancano file derivati da IMQ/OMI che le fasi scelte non rifanno da sole; altrimenti None."""
    proc = RADICE / "data" / "processed"
    servono = []
    if any(f in fasi for f in ("traffico", "r6", "r8")):
        servono += [n for n in FONTI_IMQ if n != "imq_mappa.json"]      # zone, geometrie e coppie dell'IMQ (40, 41, 93, 99...)
    if "mappa" in fasi:
        servono += ["imq_mappa.json"] + FONTI_OMI                       # la mappa li ha dentro: senza, rifarla perderebbe due temi
    if "r10" in fasi and "dati" not in fasi:
        servono += FONTI_OMI                       # la fase dati li rifa dal grezzo (08), se c'e'
    if "traffico" not in fasi and any(f in fasi for f in ("r6", "r8")):
        servono += FONTI_DOMANDA                   # la fase traffico li rifa dall'IMQ (40, 49)
    servono = list(dict.fromkeys(servono))
    mancano = [n for n in servono if not (proc / n).exists()]
    if not mancano:
        return None
    return ("Mancano file derivati da IMQ 2022 / OMI, che non stanno in git (licenza non chiara):\n  " + "\n  ".join(f"data/processed/{n}" for n in mancano)
            + "\nScarica le fonti a mano (indirizzi in docs/en/METHODS.md): IMQ in data/raw/IMQ2022_opendata_web, poi python scripts/14_prepara_imq.py, "
              "15_prepara_zone_imq.py, 16_prepara_imq_mappa.py; OMI in data/raw/omi_2025_2, poi python scripts/08_prepara_omi.py "
              "(o python scripts/rifai_tutto.py --da dati). Poi rilancia questo comando.")


def mostra(p):
    try:
        return p.relative_to(RADICE)
    except ValueError:
        return p


def carica_stato():
    try:
        return json.loads(STATO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"fatti": []}


def salva_stato(stato):
    LOGS.mkdir(exist_ok=True)
    STATO.write_text(json.dumps(stato, ensure_ascii=False, indent=1), encoding="utf-8")


def pulisci_parziali():
    import shutil
    p = RADICE / "data" / "processed" / "accessibilita_parziale"
    if p.exists():
        shutil.rmtree(p)


def lancia(cid, argv, note, log):
    """Lancia un comando; ritorna il codice di uscita. L'uscita va nel log e a schermo (ultime righe)."""
    script = AQUI / argv[0]
    if "salta_se_manca=" in note:
        richiesto = RADICE / note.split("salta_se_manca=")[1].split(",")[0].split()[0]
        if not richiesto.exists():
            log.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')}  {cid}: saltato, manca {mostra(richiesto)} ===\n")
            print(f"    saltato: manca {mostra(richiesto)}", flush=True)
            return 0
    tentativi = 3 if "riprova" in note else 1
    if "pulisci" in note:
        pulisci_parziali()
    for t in range(1, tentativi + 1):
        log.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')}  {cid}" + (f"  (tentativo {t})" if tentativi > 1 else "") + " ===\n")
        log.flush()
        r = subprocess.run([sys.executable, "-u", str(script), *argv[1:]], cwd=str(RADICE), stdout=log, stderr=subprocess.STDOUT)
        if r.returncode == 0:
            return 0
        if t < tentativi:
            print(f"    interrotto con codice {r.returncode}, riparto fra 60 secondi (tentativo {t + 1} di {tentativi})", flush=True)
            time.sleep(60)
    return r.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solo", help="fasi da fare, separate da virgola (es. schede,mappa)")
    ap.add_argument("--da", help="fase da cui partire (dopo la quale si fa tutto)")
    ap.add_argument("--riprendi", action="store_true", help="salta i comandi gia' finiti nel giro precedente")
    ap.add_argument("--elenco", action="store_true", help="mostra le fasi e i comandi senza lanciare niente")
    ap.add_argument("--prova-secca", action="store_true", help="controlla che ogni script esista, senza lanciarlo")
    args = ap.parse_args()
    fasi = scegli_fasi(args)
    elenco = comandi(fasi)
    if args.elenco:
        for nome, durata, lista in FASI:
            if nome in fasi:
                print(f"\n[{nome}]  ({durata})")
                for argv, note in lista:
                    print(f"  python scripts/{' '.join(argv)}" + (f"    # {note}" if note else ""))
        return 0
    mancano = [argv[0] for _id, _f, argv, _n in elenco if not (AQUI / argv[0]).is_file()]
    if mancano:
        print("Script che non esistono: " + ", ".join(sorted(set(mancano))))
        return 1
    if args.prova_secca:
        print(f"OK: {len(elenco)} comandi in {len(fasi)} fasi, tutti gli script esistono.")
        return 0

    messaggio = controlla_fonti(fasi)
    if messaggio:
        print(messaggio)
        return 1
    LOGS.mkdir(exist_ok=True)
    stato = carica_stato() if args.riprendi else {"fatti": []}
    fatti = set(stato["fatti"])
    da_fare = [c for c in elenco if c[0] not in fatti]
    print(f"{len(elenco)} comandi in {len(fasi)} fasi ({', '.join(fasi)}); da fare {len(da_fare)}" + (f", gia' fatti {len(elenco) - len(da_fare)}" if args.riprendi else ""), flush=True)
    t0 = time.time()
    with open(LOG, "a" if args.riprendi else "w", encoding="utf-8", errors="replace") as log:
        for k, (cid, fase, argv, note) in enumerate(da_fare, 1):
            print(f"[{time.strftime('%H:%M:%S')}] ({k}/{len(da_fare)}) {cid}" + (f"   [{note}]" if note and note not in ("riprova", "pulisci", "riprova,pulisci") else ""), flush=True)
            codice = lancia(cid, argv, note, log)
            if codice != 0:
                salva_stato(stato)
                print(f"\nERRORE in «{cid}» (codice {codice}). Guarda la fine di {mostra(LOG)}.\n"
                      f"Dopo aver sistemato: python scripts/rifai_tutto.py --riprendi" + (f" --solo {args.solo}" if args.solo else f" --da {args.da}" if args.da else ""))
                return 1
            stato["fatti"].append(cid)
            salva_stato(stato)
    minuti = (time.time() - t0) / 60
    print(f"\nFATTO in {minuti:.0f} minuti. Gli AVVISI sono nel log: cerca la parola AVVISO in {mostra(LOG)}")
    if STATO.exists() and len(fasi) == len(NOMI):
        STATO.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
