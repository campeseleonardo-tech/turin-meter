#!/usr/bin/env python3
"""88 - Confronto fra le auto in entrata del mattino stimate dal modello (script 81) e i sensori 5T.

SOLO LETTURA: non modifica nessun risultato. Scrive solo docs/rapporti/RAPPORTO_R6_CONFRONTO_SENSORI.txt.

Misurato: data/processed/velocita_5t.json, feriale ("0"), somma di f (veicoli/ora) delle ore 6-9, solo
celle con ok vero. Un sensore conta un verso solo.
Modello: flusso_archi di risultato6_v2/auto_passaggio.npz, letto con c4_per_punti dello script 81
(il tratto piu' trafficato entro 50 m dal sensore, due versi).
Si confronta l'ORDINE (Spearman), non il valore: il modello conta solo le auto in entrata del mattino,
il sensore tutte le auto.
  (a) sensore per sensore; (b) per luogo: sensori a meno di 30 m fra loro sommati (i due versi).
"Torino e cintura" = sensori entro 25 km dal centro di Torino (scelta dichiarata: il file ha anche
sensori di tutto il Piemonte, che non c'entrano con le auto che entrano a Torino).
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import rankdata, spearmanr

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
SENSORI = RADICE / "data" / "processed" / "velocita_5t.json"
P = RADICE / "data" / "processed" / "risultato6_v2"
NPZ = P / "auto_passaggio.npz"
RETE_DIR = RADICE / "data" / "processed" / "traffico_c" / "rete"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6_CONFRONTO_SENSORI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON = P / "confronto_sensori.json"

ORE = (6, 7, 8, 9)
RAGGIO_M = 50
DIST_LUOGO_M = 30.0
RAGGIO_CINTURA_KM = 25.0
CENTRO = (45.0703, 7.6869)      # Torino, piazza Castello


def flusso_misurato(celle):
    f = celle.get("0", {})
    return float(sum(f[str(h)]["f"] for h in ORE if str(h) in f and f[str(h)].get("ok")))


def strada(via):
    return via.replace("(TO)", "").strip()


def raggruppa(lista, soglia):
    """Gruppi di sensori collegati da distanze < soglia (union-find)."""
    padre = list(range(len(lista)))

    def trova(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i
    for i in range(len(lista)):
        for j in range(i + 1, len(lista)):
            if comuni.haversine_m(lista[i]["lat"], lista[i]["lon"], lista[j]["lat"], lista[j]["lon"]) < soglia:
                padre[trova(i)] = trova(j)
    gruppi = {}
    for i in range(len(lista)):
        gruppi.setdefault(trova(i), []).append(lista[i])
    return list(gruppi.values())


def classifiche(righe):
    """righe con 'mis' e 'mod': aggiunge rango (1 = piu' trafficato; pari merito = media)."""
    r_mis = rankdata([-r["mis"] for r in righe])
    r_mod = rankdata([-r["mod"] for r in righe])
    for r, a, b in zip(righe, r_mis, r_mod):
        r["r_mis"], r["r_mod"], r["diff"] = float(a), float(b), abs(float(a) - float(b))
    rho, p = spearmanr([r["mis"] for r in righe], [r["mod"] for r in righe])
    return float(rho), float(p)


def tabella(righe, etichetta):
    out = [f"{'N':>3} {etichetta:<44s} {'misurato':>9s} {'modello':>9s} {'pos.mis':>8s} {'pos.mod':>8s} {'diff':>6s}"]
    for i, r in enumerate(sorted(righe, key=lambda r: r["r_mis"]), 1):
        out.append(f"{i:>3} {r['nome'][:44]:<44s} {r['mis']:9.0f} {r['mod']:9.0f} {r['r_mis']:8.1f} {r['r_mod']:8.1f} {r['diff']:6.1f}")
    return out


def posizione(righe, testo):
    return [r for r in righe if testo in r["nome"].lower()]


def lettura(rho):
    if rho >= 0.6:
        return "buono: il modello mette le strade d'ingresso in un ordine simile ai sensori"
    if rho >= 0.4:
        return "debole: il modello segue solo in parte l'ordine delle strade d'ingresso"
    return "il modello NON segue le strade d'ingresso: l'ordine e' troppo diverso da quello dei sensori"


def main():
    c = comuni.Controlli()
    for f in (SENSORI, NPZ):
        c(f"esiste {f.name}", f.exists(), bloccante=True)
    dati = json.loads(SENSORI.read_text(encoding="utf-8"))
    flusso_archi = np.load(NPZ)["flusso_archi"]
    print(f"sensori 5T: {len(dati['sensori'])}, periodo {dati['periodo']['da']} - {dati['periodo']['a']}")
    comuni.controlla_periodo(dati.get("periodo"), "sensori")      # periodo fisso (L9)

    m81 = comuni.carica_script("81_auto_di_passaggio.py")
    import rete_osm
    rete = rete_osm.carica(RETE_DIR)
    c("flusso_archi ha la lunghezza degli archi della rete", len(flusso_archi) == len(rete["archi"]),
      bloccante=True, dettaglio=f"{len(flusso_archi)} vs {len(rete['archi'])}")
    c("flusso del modello senza valori negativi", float(flusso_archi.min()) >= 0, bloccante=True)

    sens = []
    for ident, s in dati["sensori"].items():
        mis = flusso_misurato(s["celle"])
        if mis <= 0:
            continue
        km = comuni.haversine_m(CENTRO[0], CENTRO[1], s["lat"], s["lon"]) / 1000
        if km > RAGGIO_CINTURA_KM:
            continue
        sens.append({"id": ident, "via": strada(s["via"]), "dir": s["dir"], "lat": s["lat"], "lon": s["lon"],
                     "mis": mis, "km": km})
    n_tot = len(dati["sensori"])
    print(f"sensori tenuti: {len(sens)} su {n_tot} (flusso misurato > 0 ore 6-9, entro {RAGGIO_CINTURA_KM:.0f} km da Torino)")
    c("almeno 20 sensori nel confronto", len(sens) >= 20, bloccante=True, dettaglio=f"{len(sens)}")

    mod, _ = m81.c4_per_punti(rete, flusso_archi, [(s["id"], s["lat"], s["lon"]) for s in sens], RAGGIO_M)
    for s in sens:
        s["mod"] = float(mod[s["id"]]["c4"])
        s["tratto"] = mod[s["id"]]["tratto"]
    fuori = [s for s in sens if s["tratto"] is None]
    zero = [s for s in sens if s["tratto"] is not None and s["mod"] == 0]
    c("sensori senza strada della rete entro 50 m", not fuori,
      dettaglio=f"{len(fuori)}: " + ", ".join(f"{s['id']} {s['via']}" for s in fuori))
    c("sensori su strada della rete ma modello = 0", not zero,
      dettaglio=f"{len(zero)}: " + ", ".join(f"{s['id']} {s['via']}" for s in zero))

    # (a) sensore per sensore
    righe_a = [{"nome": f"{s['via']} ({s['dir'][:3]}) [{s['id']}]", "mis": s["mis"], "mod": s["mod"]} for s in sens]
    rho_a, p_a = classifiche(righe_a)

    # (b) per luogo
    righe_b = []
    for g in raggruppa(sens, DIST_LUOGO_M):
        vie = Counter(s["via"] for s in g)
        nome = (vie.most_common(1)[0][0] + (f" ({len(g)} sensori)" if len(g) > 1 else "")
                + f" @{g[0]['lat']:.3f},{g[0]['lon']:.3f}")
        righe_b.append({"nome": nome, "mis": sum(s["mis"] for s in g), "mod": max(s["mod"] for s in g)})
    rho_b, p_b = classifiche(righe_b)

    # variante (b) senza i sensori fuori rete o a zero
    esclusi = {s["id"] for s in fuori + zero}
    rho_b2 = None
    if esclusi:
        tenuti = [s for s in sens if s["id"] not in esclusi]
        if len(tenuti) >= 10:
            rb = []
            for g in raggruppa(tenuti, DIST_LUOGO_M):
                rb.append({"nome": g[0]["via"], "mis": sum(s["mis"] for s in g), "mod": max(s["mod"] for s in g)})
            rho_b2, _ = classifiche(rb)
            n_b2 = len(rb)

    c("correlazione (b) calcolabile", not np.isnan(rho_b), bloccante=True)

    righe_txt = []
    righe_txt.append(f"(a) sensore per sensore: rho = {rho_a:.3f} (p = {p_a:.3f}), {len(righe_a)} sensori")
    righe_txt.append(f"(b) per luogo (sensori a meno di {DIST_LUOGO_M:.0f} m sommati): rho = {rho_b:.3f} (p = {p_b:.3f}), {len(righe_b)} luoghi")
    if rho_b2 is not None:
        righe_txt.append(f"    variante (b) senza i {len(esclusi)} sensori fuori rete o con modello 0: rho = {rho_b2:.3f}, {n_b2} luoghi")
    print()
    print("\n".join(righe_txt))
    print("\n--- (a) sensore per sensore ---")
    print("\n".join(tabella(righe_a, "sensore / strada")))
    print("\n--- (b) per luogo ---")
    print("\n".join(tabella(righe_b, "luogo / strada")))

    # rapporto
    top = sorted(righe_b, key=lambda r: -r["diff"])[:10]
    rap = ["RAPPORTO R6 - CONFRONTO AUTO IN ENTRATA (MODELLO) E SENSORI 5T",
           f"Sensori: velocita_5t.json, feriale, ore {ORE[0]}-{ORE[-1]}, veicoli/ora, periodo "
           f"{dati['periodo']['da']} - {dati['periodo']['a']}.",
           f"Modello: auto_passaggio.npz (script 81), tratto piu' trafficato entro {RAGGIO_M} m, due versi.",
           f"Tenuti {len(sens)} sensori su {n_tot} (flusso > 0, entro {RAGGIO_CINTURA_KM:.0f} km da Torino).",
           "Si confronta l'ordine, non il valore (il modello conta le auto in entrata del mattino, il sensore tutte).",
           ""] + righe_txt + [""]
    rap.append("Le 10 strade dove le due classifiche sono piu' diverse (confronto b, posizione 1 = piu' trafficata):")
    for r in top:
        rap.append(f"  {r['nome']:<44s} misurato {r['mis']:6.0f} (pos. {r['r_mis']:.1f})   modello {r['mod']:7.0f} (pos. {r['r_mod']:.1f})   diff {r['diff']:.1f}")
    rap.append("")
    for chiave, nome in (("francia", "Corso Francia"), ("trieste", "Strada/Corso Trieste")):
        for sede, righe in (("(a)", righe_a), ("(b)", righe_b)):
            for r in posizione(righe, chiave):
                rap.append(f"{nome} {sede}: {r['nome']} - misurato pos. {r['r_mis']:.1f}/{len(righe)}, "
                           f"modello pos. {r['r_mod']:.1f}/{len(righe)} (misurato {r['mis']:.0f}, modello {r['mod']:.0f})")
    rap.append("")
    rap.append(f"Lettura (b): rho = {rho_b:.3f}: {lettura(rho_b)}.")
    if fuori or zero:
        rap.append("Attenzione: sensori senza strada della rete o con modello 0: "
                   + ", ".join(f"{s['via']} [{s['id']}]" for s in fuori + zero))
    rap += ["", "--- (a) sensore per sensore ---"] + tabella(righe_a, "sensore / strada")
    rap += ["", "--- (b) per luogo ---"] + tabella(righe_b, "luogo / strada")
    RAPPORTO.write_text("\n".join(rap) + "\n", encoding="utf-8")
    # piccolo file per la scheda del Risultato 6 (lo legge schede_risultati.py)
    ok_b2 = rho_b2 is not None
    OUT_JSON.write_text(json.dumps({
        "rho_a": round(rho_a, 3), "rho_b": round(rho_b, 3),
        "rho_b_senza_fuori_rete": round(rho_b2 if ok_b2 else rho_b, 3),
        "n_a": len(righe_a), "n_b": len(righe_b),
        "n_b_senza_fuori_rete": n_b2 if ok_b2 else len(righe_b),
        "generato": time.strftime("%d/%m/%Y %H:%M")}, ensure_ascii=False), encoding="utf-8")
    print(f"\nScritti {RAPPORTO.relative_to(RADICE)} e {OUT_JSON.relative_to(RADICE)}")
    print(f"Lettura (b): {lettura(rho_b)}")
    av = c.avvisi()
    print(f"{len(av)} AVVISI" if av else "nessun avviso")


if __name__ == "__main__":
    main()
