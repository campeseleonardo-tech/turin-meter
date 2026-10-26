#!/usr/bin/env python3
"""
83_fermate_importanti.py  -  Risultato 6 (correzioni del 20/10/2026): le fermate importanti, con il
punteggio corretto. Preparato da Claude, da lanciare sul PC. Sostituisce lo scenario S2 dello script 75
(che resta solo per confronto).

Cosa cambia rispetto a S2
-------------------------
  - Segnali: a2 (importanza della strada), b2 (corse nelle ore dei pendolari), c4 (auto in entrata che
    passano accanto, script 81), e (metro o stazione entro 300 m). Tolti i doppioni a1 (= a2) e c1/c2_ztl
    (sostituiti da c4); d (calo di velocita') esce dal punteggio: c'e' solo in ~90 luoghi.
  - Pesi uguali e dichiarati (opzione --pesi).
  - Un segnale mancante NON sparisce piu' dalla media: a2 mancante = 1 (nessuna strada importante entro
    150 m), b2 mancante = 0, c4 mancante = 0.
  - Universo: luoghi della Citta' metropolitana FUORI dalla zona centrale Q001-Q009 (la stessa zona centrale
    usata per i parcheggi). I percentili e la soglia si calcolano solo su questi luoghi ("eleggibili").
  - Fermate importanti = regola fissa (Leo, 20/10): (metro, stazione o capolinea, oppure almeno N_CORSE corse/ora) e
    almeno M_AUTO auto che passano. Il punteggio serve solo per l'ordine. Con --percentuale X vale la vecchia regola
    (il X% piu' alto del punteggio), solo per confronto.
  - e resta 0 o 100 (non e' un percentile); la sensibilita' "senza e" dice quanto pesa.

Cosa legge
----------
  data/processed/risultato6_v2/luoghi.json, segnali.json, auto_passaggio.json (script 81), scenari.json (confronto)
  data/processed/imq_zone.json

Cosa scrive
-----------
  data/processed/risultato6_v2/fermate_importanti.json
  docs/rapporti/RAPPORTO_R6_FERMATE_IMPORTANTI.txt

Come si lancia
--------------
  python scripts\\83_fermate_importanti.py
  python scripts\\83_fermate_importanti.py --pesi a2=1,b2=1,c4=2,e=1 --percentuale 10
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402

RADICE = comuni.RADICE
P = RADICE / "data" / "processed" / "risultato6_v2"
LUOGHI = P / "luoghi.json"
SEGNALI = P / "segnali.json"
PASSAGGIO = P / "auto_passaggio.json"
NODI = P / "nodi.json"
SCENARI = P / "scenari.json"
ZONE = RADICE / "data" / "processed" / "imq_zone.json"
OUT = P / "fermate_importanti.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_R6_FERMATE_IMPORTANTI.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

SEGNALI_USATI = ("a2", "b2", "c4", "e")
PESI = {"a2": 1.0, "b2": 1.0, "c4": 1.0, "e": 1.0}
MANCANTE = {"a2": 1, "b2": 0.0, "c4": 0}
# Leo, 20/10: regola fissa al posto del 10% piu' alto.
# Fermata importante = (metro o stazione o capolinea, oppure almeno N_CORSE corse/ora nelle ore dei pendolari)
# e almeno M_AUTO auto in entrata che passano accanto.
N_CORSE = 10      # segnale b2 (corse all'ora, media ore 6-10 e 16-20 di un feriale)
M_AUTO = 1000     # segnale c4 (auto in entrata che passano accanto)
M_AUTO_IT = f"{M_AUTO:,}".replace(",", ".")   # per i testi all'italiana (1.000)


def punteggi(eleggibili, valori, pesi):
    """valori[segnale][id] -> punteggio per luogo (media pesata dei percentili; e cosi' com'e')."""
    perc = {}
    for s in pesi:
        if s == "e":
            perc[s] = {i: float(valori["e"][i]) for i in eleggibili}
        else:
            perc[s] = comuni.percentile_rank({i: valori[s][i] for i in eleggibili})
    tot_w = sum(pesi.values())
    return {i: sum(w * perc[s][i] for s, w in pesi.items()) / tot_w for i in eleggibili}, perc


def regola(eleggibili, valori, nodo, n_corse=N_CORSE, m_auto=M_AUTO, con_nodi=True, con_auto=True):
    """Fermate che rispettano la regola fissa (le varianti servono per la sensibilita')."""
    return {i for i in eleggibili
            if ((con_nodi and nodo[i]) or valori["b2"][i] >= n_corse) and (not con_auto or valori["c4"][i] >= m_auto)}


def scegli(pt, percentuale):
    soglia = comuni.soglia_quantile(list(pt.values()), 100.0 - percentuale)
    return soglia, {i for i, v in pt.items() if v >= soglia}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pesi", default=",".join(f"{k}={v:g}" for k, v in PESI.items()))
    ap.add_argument("--percentuale", type=float, default=None,
                    help="se data, vale la vecchia regola (il X%% piu' alto del punteggio), solo per confronto")
    args = ap.parse_args()
    pesi = {k: float(v) for k, v in (x.split("=") for x in args.pesi.split(","))}
    c = comuni.Controlli()
    t0 = time.time()

    for f in (LUOGHI, SEGNALI, PASSAGGIO, ZONE, NODI):
        c(f"esiste {f.name}", f.exists(), bloccante=True)
    c("i pesi riguardano solo a2, b2, c4, e", set(pesi) <= set(SEGNALI_USATI) and sum(pesi.values()) > 0, bloccante=True)
    luoghi = {l["id_luogo"]: l for l in json.loads(LUOGHI.read_text(encoding="utf-8"))["luoghi"]}
    seg = {s["id_luogo"]: s for s in json.loads(SEGNALI.read_text(encoding="utf-8"))["luoghi"]}
    pas = json.loads(PASSAGGIO.read_text(encoding="utf-8"))
    macro = {z["cod"]: z["macro"] for z in json.loads(ZONE.read_text(encoding="utf-8"))}
    nodi = {n["id_luogo"]: n for n in json.loads(NODI.read_text(encoding="utf-8"))["luoghi"]}

    eleggibili = [i for i, l in luoghi.items()
                  if l.get("zona_imq") and macro.get(l["zona_imq"]) in comuni.MACRO_UNIVERSO
                  and l["zona_imq"] not in comuni.ZONE_CENTRALI]
    fuori_centro = sum(1 for l in luoghi.values() if l.get("zona_imq") in comuni.ZONE_CENTRALI)
    print(f"luoghi {len(luoghi)}; eleggibili {len(eleggibili)} (in zona centrale {fuori_centro})")
    c("eleggibili > 1000", len(eleggibili) > 1000, dettaglio=f"{len(eleggibili)}")

    def val(s, i):
        v = seg.get(i, {}).get(s)
        return MANCANTE[s] if v is None else v

    valori = {
        "a2": {i: val("a2", i) for i in eleggibili},
        "b2": {i: val("b2", i) for i in eleggibili},
        "c4": {i: (pas["luoghi"].get(i) or {}).get("c4", 0) or 0 for i in eleggibili},
        "e": {i: seg.get(i, {}).get("e", 0) or 0 for i in eleggibili},
    }
    mancanti = {s: sum(1 for i in eleggibili if seg.get(i, {}).get(s) is None) for s in ("a2", "b2")}
    mancanti["c4"] = sum(1 for i in eleggibili if i not in pas["luoghi"])
    c("c4 presente per tutti gli eleggibili", mancanti["c4"] == 0, dettaglio=f"mancante in {mancanti['c4']}")

    pt, perc = punteggi(eleggibili, valori, pesi)
    nodo = {i: bool(nodi.get(i, {}).get("metro") or nodi.get(i, {}).get("ferro") or nodi.get(i, {}).get("capolinea"))
            for i in eleggibili}
    c("nodi.json copre tutti gli eleggibili", all(i in nodi for i in eleggibili),
      dettaglio=f"{sum(i not in nodi for i in eleggibili)} mancanti")
    if args.percentuale is None:
        soglia, scelti = None, regola(eleggibili, valori, nodo)
    else:
        soglia, scelti = scegli(pt, args.percentuale)
    ordine = sorted(eleggibili, key=lambda i: (-pt[i], i))   # a pari punteggio: codice del luogo (ordine fisso)
    posizione = {i: k + 1 for k, i in enumerate(ordine)}
    if args.percentuale is None:
        print(f"regola: (metro/stazione/capolinea o almeno {N_CORSE} corse/ora) e almeno {M_AUTO_IT} auto: "
              f"fermate importanti {len(scelti)}")
    else:
        print(f"soglia {soglia:.2f}: fermate importanti {len(scelti)} (vecchia regola, {args.percentuale:g}%)")
        c("le fermate importanti sono circa la percentuale scelta (+-3 punti)",
          abs(len(scelti) / len(eleggibili) * 100 - args.percentuale) <= 3,
          dettaglio=f"{len(scelti)} su {len(eleggibili)}")
    c("nessuna fermata importante in zona centrale",
      not any(luoghi[i]["zona_imq"] in comuni.ZONE_CENTRALI for i in scelti), bloccante=True)

    # alternative alla regola (per la sensibilita' nello script 84)
    alternative = {}
    for n_alt, m_alt in ((10, 500), (10, 2000), (15, 1000)):
        alternative[f"N{n_alt}_M{m_alt}"] = sorted(regola(eleggibili, valori, nodo, n_alt, m_alt))

    # sensibilita': senza la condizione sulle auto, senza i nodi; c4 col ripiego
    sens = {}
    for nome_s, sc2 in (("solo_nodi_e_corse", regola(eleggibili, valori, nodo, con_auto=False)),
                        ("senza_nodi", regola(eleggibili, valori, nodo, con_nodi=False))):
        sens[nome_s] = {"fermate": len(sc2), "entrano": len(sc2 - scelti), "escono": len(scelti - sc2)}
    zona_or = pas.get("auto_per_zona_origine", {})
    rip = {i: (zona_or.get(luoghi[i]["zona_imq"], {}).get("auto", 0) if not luoghi[i]["zona_imq"].startswith("Q") else 0)
           for i in eleggibili}
    sc3 = regola(eleggibili, {**valori, "c4": rip}, nodo)
    sens["c4_ripiego"] = {"fermate": len(sc3), "entrano": len(sc3 - scelti), "escono": len(scelti - sc3)}

    confronto = None
    if SCENARI.exists():
        s2 = {x["id_luogo"] for x in json.loads(SCENARI.read_text(encoding="utf-8"))["scenari"]["S2"]["critici"]}
        confronto = {"S2": len(s2), "nuove": len(scelti), "restano": len(s2 & scelti),
                     "entrano": len(scelti - s2), "escono": len(s2 - scelti),
                     "S2_in_zona_centrale": sum(1 for i in s2 if (luoghi.get(i) or {}).get("zona_imq") in comuni.ZONE_CENTRALI)}

    imp = []
    for i in sorted(scelti, key=lambda i: (-pt[i], i)):   # scelti e' un insieme: senza spareggio l'ordine cambiava a ogni giro
        l, s = luoghi[i], seg.get(i, {})
        imp.append({"id_luogo": i, "nome": l["nome"], "lat": l["lat"], "lon": l["lon"], "zona_imq": l["zona_imq"],
                    "punteggio": round(pt[i], 2), "posizione": posizione[i],
                    "segnali": {k: valori[k][i] for k in ("a2", "b2", "c4", "e")},
                    "percentili": {k: round(perc[k][i], 1) for k in pesi},
                    "strada": s.get("a2_strada"), "metro": bool(s.get("metro")), "ferro": bool(s.get("ferro"))})
    per_zona = Counter(x["zona_imq"] for x in imp)
    dati = {"generato": time.strftime("%d/%m/%Y %H:%M"),
            "parametri": {"segnali": list(pesi), "pesi": pesi, "mancante": MANCANTE,
                          "regola": {"n_corse": N_CORSE, "m_auto": M_AUTO} if args.percentuale is None else None,
                          "percentuale": args.percentuale, "zone_centrali": list(comuni.ZONE_CENTRALI),
                          "universo": list(comuni.MACRO_UNIVERSO), "c4_metodo": pas.get("c4_metodo"),
                          "torinesi": pas.get("torinesi")},
            "n_luoghi": len(luoghi), "n_eleggibili": len(eleggibili), "soglia": None if soglia is None else round(soglia, 2),
            "mancanti": mancanti, "importanti": imp, "alternative": alternative,
            "sensibilita": sens, "confronto_S2": confronto, "per_zona": dict(per_zona), "controlli": c.righe}
    OUT.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")

    r = ["RAPPORTO R6 - FERMATE IMPORTANTI CON IL PUNTEGGIO CORRETTO (script 83)",
         f"Generato il {dati['generato']}.",
         f"Segnali {', '.join(f'{k} (peso {v:g})' for k, v in pesi.items())}; c4 col metodo «{pas.get('c4_metodo')}»; "
         f"torinesi nella domanda: {'si' if pas.get('torinesi') else 'no'}.",
         f"Luoghi {len(luoghi)}; eleggibili (Citta' metropolitana fuori da Q001-Q009) {len(eleggibili)}.",
         (f"regola fissa: (metro, stazione o capolinea, oppure almeno {N_CORSE} corse/ora) e almeno {M_AUTO_IT} auto che passano; "
          f"fermate importanti {len(scelti)}." if args.percentuale is None else
          f"soglia del {args.percentuale:g}% piu' alto = {soglia:.2f}; fermate importanti {len(scelti)}."),
         f"Segnali mancanti fra gli eleggibili (messi al minimo): {mancanti}", "",
         "== Le 30 fermate importanti con il punteggio piu' alto ==",
         *(f"  {x['posizione']:4d}. {x['nome'][:38]:38s} {x['zona_imq']:5s} a2={x['segnali']['a2']} "
           f"b2={x['segnali']['b2']} c4={x['segnali']['c4']} e={x['segnali']['e']}" for x in imp[:30]), "",
         "== Fermate importanti per zona IMQ ==", *(f"  {z}: {n}" for z, n in per_zona.most_common()), "",
         "== Sensibilita' (quante fermate importanti entrano / escono) ==",
         *(f"  {k}: {v['fermate']} fermate; entrano {v['entrano']}, escono {v['escono']}" for k, v in sens.items()),
         *(f"  regola {k.replace('_', ', ').replace('N', 'N ').replace('M', 'M ')}: {len(v)} fermate" for k, v in alternative.items()), "",
         "== Confronto con lo scenario S2 (19/10) ==", f"  {confronto}", "",
         "== Controlli ==", *("  " + x for x in c.righe)]
    RAPPORTO.write_text("\n".join(r) + "\n", encoding="utf-8")
    print(f"Scritto: {OUT}\nScritto: {RAPPORTO}\nDurata {time.time() - t0:.0f} s; avvisi: {len(c.avvisi())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
