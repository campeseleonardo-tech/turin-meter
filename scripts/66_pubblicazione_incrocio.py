# -*- coding: utf-8 -*-
"""
scripts/66_pubblicazione_incrocio.py - Pacchetto G (Fase 5): pubblicazione e incrocio.

Pubblica per ogni TRATTA dell'universo di Torino (e prima cintura, tabella a
parte) i numeri assoluti (con fascia 50% e 90%), relativi e graduatoria, poi
incrocia traffico x trasporto pubblico con le definizioni FISSATE nel piano:

  - "molto traffico" = nel terzo piu' alto per veic_giorno fra le tratte
    affidabili dell'universo E almeno pari al limite basso dell'intervallo
    validato; versione "per corsia" sullo stesso criterio;
  - "poco TP" = copertura_con_metro <= 50% della lunghezza; sensibilita' 30%, 70%
    e la sola copertura_300;
  - robusta = resta "molto traffico" con il traffico x0,65 e x1,35 e con le
    soglie di sensibilita';
  - divario = percentile del traffico - percentile della copertura TP.

Controllo di buon senso (NON taratura): accordo con il controllo di buon senso di sviluppo/note_tecniche/R8_traffico.md.

Output: data/processed/risultato8_traffico_tp_v2.json
        docs/rapporti/RAPPORTO_RISULTATO8_TRAFFICO_TP_V2.txt
"""

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
PROC = AQUI.parent / "data" / "processed"
OUT = PROC / "traffico_d"
RAPPORTO = AQUI.parent / "docs" / "rapporti" / "RAPPORTO_RISULTATO8_TRAFFICO_TP_V2.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

# --- conoscenza di Leo (controllo di buon senso, mai taratura) ---
LEO_STRADE = [
    ("cairoli", "A/B"), ("palestrina", "B"), ("agudio", "B-A"), ("sturzo", "B-A"),
    ("cosenza", "A"), ("san massimo", "A"), ("pollenzo", "B"), ("pasquale paoli", "B"),
    ("quarto dei mille", "C"), ("rivalta", "B"), ("fiume", "A"), ("montebello", "B-C"),
    ("bolzano", "A"), ("quintino sella", "B-A"), ("lombardia", "B"), ("racconigi", "A"),
    ("re umberto", "B-A"), ("castello", "B-A"),
]
LEO_CONFRONTI = [
    ("cosenza", "lione"), ("vittorio emanuele", "giulio cesare"),
    ("casale", "moncalieri"), ("racconigi", "re umberto"),
    ("stati uniti", "duca degli abruzzi"), ("vercelli", "bolzano"),
    ("agudio", "monte lungo"),
]
LEO_PIU_TRAFFICATE = ["francia", "regina margherita", "vittorio emanuele", "lione",
                      "vercelli", "giulio cesare", "moncalieri", "casale"]


def normalizza(nome):
    from importlib import import_module
    return import_module("24_importanza_vie").normalizza(nome)


def leo_a_b_c(giudizio):
    g = giudizio.upper()
    if g.startswith("A"):
        return "A"
    if g.startswith("C"):
        return "C"
    return "B"


def main():
    val = json.loads((OUT / "valutazione_fase5.json").read_text(encoding="utf-8"))
    doc = json.loads((OUT / "tratte_traffico.json").read_text(encoding="utf-8"))
    finale = doc["variante_finale"]; classe = doc["classe_esito"]
    lim_inf = doc["taratura"]["intervallo_validato_measured"][0]
    reg = doc["tratte"]
    assi = {a["id"]: a for a in json.loads((OUT / "assi.json").read_text(encoding="utf-8"))["assi"]}

    torino = [o for o in reg if o["comune"] == "Torino" and o.get("punteggio", 0) >= 3
              and o["lunghezza_m"] >= 300 and o["affidabile"]
              and o["classe"] not in ("motorway", "trunk", "motorway_link", "trunk_link")
              and o["rango"] < 5 and o["veic_giorno"] > 0]
    veic = np.array([o["veic_giorno"] for o in torino])
    q33, q66 = np.percentile(veic, [33.3, 66.7])
    mediana = float(np.median(veic))
    q20, q40, q60, q80 = np.percentile(veic, [20, 40, 60, 80])
    ord_t = sorted(torino, key=lambda o: -o["veic_giorno"])
    pos = {o["id"]: i + 1 for i, o in enumerate(ord_t)}
    ord_c = sorted(torino, key=lambda o: -o["veic_per_corsia"])
    posc = {o["id"]: i + 1 for i, o in enumerate(ord_c)}
    for o in torino:
        o["indice_1_5"] = int(1 + np.searchsorted([q20, q40, q60, q80], o["veic_giorno"], "right"))
        o["rapporto_su_mediana"] = round(o["veic_giorno"] / mediana, 3) if mediana else None
        o["posizione_torino"] = pos[o["id"]]
        o["posizione_per_corsia"] = posc[o["id"]]

    # percentile di traffico e copertura
    vs = np.sort(veic)
    covs = np.sort(np.array([o["copertura_con_metro"] for o in torino]))
    for o in torino:
        o["perc_traffico"] = float(np.searchsorted(vs, o["veic_giorno"], "left") / len(vs))
        o["perc_tp"] = float(np.searchsorted(covs, o["copertura_con_metro"], "left") / len(covs))
        o["divario"] = round(o["perc_traffico"] - o["perc_tp"], 4)

    # molto traffico: terzo piu' alto E >= limite basso validato
    def molto(o, soglia= q66):
        return o["veic_giorno"] >= soglia and o["veic_giorno"] >= lim_inf

    q66c = float(np.percentile([o["veic_per_corsia"] for o in torino], 66.7))
    lim_inf_c = lim_inf / max(np.median([o["corsie_totali"] for o in torino]), 1)

    def poco_tp(o, soglia=0.5, campo="copertura_con_metro"):
        return o[campo] <= soglia

    for o in torino:
        o["molto_traffico"] = bool(molto(o))
        o["molto_traffico_per_corsia"] = bool(o["veic_per_corsia"] >= q66c and o["veic_per_corsia"] >= lim_inf_c)
        o["poco_tp"] = bool(poco_tp(o))
        o["da_guardare"] = bool(o["molto_traffico"] and o["poco_tp"])
        o["da_guardare_per_corsia"] = bool(o["molto_traffico_per_corsia"] and o["poco_tp"])
        # robustezza: resta molto traffico con -35% e +35%, e con le soglie 30/70 e copertura_300
        robusto = True
        for f in (0.65, 1.35):
            if not (o["veic_giorno"] * f >= q66 and o["veic_giorno"] * f >= lim_inf):
                robusto = False
        # sensibilita' "poco TP"
        for s in (0.3, 0.7):
            if not o["copertura_con_metro"] <= s:
                robusto = False
        if not o["copertura_300"] <= 0.5:
            robusto = False
        o["robusto"] = bool(robusto and o["da_guardare"])

    da_guardare = sorted([o for o in torino if o["da_guardare"]], key=lambda o: -o["divario"])
    robusti = [o for o in da_guardare if o["robusto"]]
    # per la risposta a Leo: top-10 tratte per "divario" (traffico alto - TP basso),
    # anche fuori dal gruppo stretto "da guardare" (che in Torino e' quasi vuoto)
    top_divario = sorted(torino, key=lambda o: -o["divario"])[:10]

    # raggruppamento in assi
    per_asse = defaultdict(list)
    for o in da_guardare:
        per_asse[o["asse"]].append(o)
    assi_guardare = []
    for aid, v in per_asse.items():
        a = assi.get(aid, {})
        v = sorted(v, key=lambda o: -o["veic_giorno"])
        assi_guardare.append({
            "id_asse": aid, "nomi": a.get("nomi", []), "nome_principale": a.get("nome_principale"),
            "comuni": a.get("comuni", []), "n_tratte": len(v),
            "veic_max": max(o["veic_giorno"] for o in v),
            "veic_max_fascia50": max(o["fascia_50"] for o in v),
            "veic_per_corsia_max": max(o["veic_per_corsia"] for o in v),
            "copertura_tp_max": max(o["copertura_con_metro"] for o in v),
            "freq_max": max(o["freq_max_300"] for o in v),
            "corsie_max": max(o["corsie_totali"] for o in v),
            "quartieri": sorted({o["quartiere"] for o in v if o["quartiere"]}),
            "robuste": sum(1 for o in v if o["robusto"]),
            "tratte": [o["id"] for o in v],
        })
    assi_guardare.sort(key=lambda a: -a["veic_max"])

    # quota di lunghezza coperta
    km_tot = sum(o["lunghezza_m"] for o in torino) / 1000
    km_cop = sum(o["lunghezza_m"] for o in torino if o["copertura_con_metro"] >= 0.5) / 1000
    km_cop300 = sum(o["lunghezza_m"] for o in torino if o["copertura_300"] >= 0.5) / 1000

    # --- controllo di buon senso: accordo con Leo ---
    def valore(chiave):
        voci = [o for o in reg if o["comune"] == "Torino" and o["veic_giorno"] > 0
                and (chiave in (o["nome"] or "").lower()
                     or any(chiave in n for n in o.get("nomi", [])))]
        if not voci:
            return None, 0
        return max(o["veic_giorno"] for o in voci), len(voci)

    def banda(chiave):
        v, n = valore(chiave)
        if v is None:
            return None
        if v >= q66:
            return "A"
        if v >= q33:
            return "B"
        return "C"

    accordo18 = []
    for chiave, giud in LEO_STRADE:
        vb = banda(chiave)
        atteso = leo_a_b_c(giud)
        accordo18.append({"strada": chiave, "leo": atteso, "nostro": vb,
                          "giusto": bool(vb == atteso)})
    n18 = sum(1 for x in accordo18 if x["giusto"])

    accordo7 = []
    for a_, b_ in LEO_CONFRONTI:
        va, _ = valore(a_); vb2, _ = valore(b_)
        # giudizio: prima > seconda (Casale â‰ˆ Moncalieri = circa uguali)
        if a_ == "casale" and b_ == "moncalieri":
            giusto = va is not None and vb2 is not None and abs(va - vb2) / max(vb2, 1) < 0.35
        else:
            giusto = va is not None and vb2 is not None and va > vb2
        accordo7.append({"confronto": f"{a_} vs {b_}", "nostro": [va, vb2], "giusto": bool(giusto)})
    n7 = sum(1 for x in accordo7 if x["giusto"])

    # correlazione di rango sulle strade note
    nomi = sorted({k for k, _ in LEO_STRADE} | {k for a_, b_ in LEO_CONFRONTI for k in (a_, b_)}
                  | set(LEO_PIU_TRAFFICATE))
    valori = []
    for k in nomi:
        v, _ = valore(k)
        valori.append((k, v if v is not None else 0.0))
    # "atteso": le piÃ¹ trafficate in alto; per le altre non c'Ã¨ un ordine -> solo
    # correlazione fra le 8 piÃ¹ trafficate e la loro posizione Ã¨ banale; si riporta
    # invece il rango medio (controllo descrittivo)
    accordo_leo = {
        "strade_18_giudizi": accordo18, "n_giuste_18": n18,
        "confronti_7": accordo7, "n_giusti_7": n7,
        "strade_trovate": sum(1 for _, v in valori if v > 0), "strade_cercate": len(valori),
        "soglie_bande": {"A_da": round(float(q66), 0), "B_da": round(float(q33), 0)},
    }

    out = {
        "stimato": True, "variante_traffico": finale, "classe_esito": classe,
        "nota": ("Numeri assoluti con fascia; relativi; graduatoria. Incrocio "
                 "traffico x TP per POSIZIONE delle fermate. Vedi i limiti in coda."),
        "taratura": doc["taratura"],
        "universo_torino": {"n_tratte": len(torino), "km": round(km_tot, 1),
                            "km_coperti_tp": round(km_cop, 1),
                            "quota_km_coperta_tp": round(km_cop / max(km_tot, 1e-9), 3),
                            "km_coperti_300": round(km_cop300, 1),
                            "quota_km_coperta_300": round(km_cop300 / max(km_tot, 1e-9), 3),
                            "mediana_veic": round(mediana, 0),
                            "soglie": {"q33": round(float(q33), 0), "q66": round(float(q66), 0)}},
        "universo_cintura": doc["universo_cintura"],
        "conteggi": {
            "molto_traffico": int(sum(o["molto_traffico"] for o in torino)),
            "poco_tp": int(sum(o["poco_tp"] for o in torino)),
            "da_guardare": len(da_guardare), "robusti": len(robusti),
            "da_guardare_per_corsia": int(sum(o["da_guardare_per_corsia"] for o in torino)),
        },
        "assi_da_guardare": assi_guardare,
        "top30": da_guardare[:30],
        "top_divario": top_divario,
        "accordo_leo": accordo_leo,
        "tratte": torino,
    }
    (PROC / "risultato8_traffico_tp_v2.json").write_text(json.dumps(out, ensure_ascii=False),
                                                         encoding="utf-8")

    righe = []
    def a_(s=""):
        righe.append(s)
    a_("RISULTATO 8 - STRADE CON MOLTO TRAFFICO E POCO TRASPORTO PUBBLICO (Fase 5)")
    a_("=" * 90)
    a_(f"variante del traffico: {finale}   classe di esito: {classe}")
    a_(f"accuratezza dichiarata: in meta' dei casi lo scarto e' entro +-"
       f"{100*doc['taratura']['fascia_50']:.0f}%; 9 volte su 10 entro +-"
       f"{100*doc['taratura']['fascia_90']:.0f}%. Fuori dall'intervallo validato la fascia x2.")
    a_(f"UNIVERSO DI TORINO: {len(torino)} tratte, {km_tot:,.1f} km "
       f"(mediana {mediana:,.0f} veic/giorno)")
    a_(f"lunghezza coperta dal TP (copertura_con_metro>=50%): {km_cop:,.1f} km "
       f"({100*km_cop/max(km_tot,1):.1f}%); con la sola copertura_300: {km_cop300:,.1f} km "
       f"({100*km_cop300/max(km_tot,1):.1f}%)")
    a_(f"soglie: molto traffico >= {q66:,.0f} veic/giorno (terzo piu' alto) e >= "
       f"{lim_inf:,.0f} (limite basso validato); poco TP = copertura_con_metro <= 50%")
    a_(f"molto traffico: {out['conteggi']['molto_traffico']}   poco TP: {out['conteggi']['poco_tp']}   "
       f"DA GUARDARE: {len(da_guardare)}   robuste: {len(robusti)}   "
       f"(per corsia: {out['conteggi']['da_guardare_per_corsia']})")
    a_("")
    a_("== I 15 ASSI 'DA GUARDARE' (tratte consecutive raggruppate) ==")
    a_(f"{'#':>3s} {'veic/g max':>11s} {'+-50%':>6s} {'/corsia':>8s} {'copTP':>6s} {'freq':>6s} "
       f"{'corsie':>6s}  nome")
    for i, a2 in enumerate(assi_guardare[:15], 1):
        a_(f"{i:3d} {a2['veic_max']:11,.0f} {100*a2['veic_max_fascia50']:5.0f}% "
           f"{a2['veic_per_corsia_max']:8,.0f} {a2['copertura_tp_max']:6.2f} {a2['freq_max']:6.1f} "
           f"{a2['corsie_max']:6.1f}  {' > '.join(a2['nomi'][:3])[:44]} "
           f"({','.join(a2['comuni'])[:18]})")
    a_("")
    a_("== Le 10 tratte/assi con il divario maggiore (traffico alto - TP basso) ==")
    a_(f"{'#':>3s} {'veic/g':>9s} {'+-50%':>6s} {'/corsia':>8s} {'copTP':>6s} {'cop300':>6s} "
       f"{'freq':>6s} {'linee':>5s}  nome (quartiere) [da guardare]")
    for i, o in enumerate(top_divario, 1):
        a_(f"{i:3d} {o['veic_giorno']:9,.0f} {100*o['fascia_50']:5.0f}% {o['veic_per_corsia']:8,.0f} "
           f"{o['copertura_con_metro']:6.2f} {o['copertura_300']:6.2f} {o['freq_max_300']:6.1f} "
           f"{o['n_linee_300']:5d}  {str(o['nome'])[:40]} ({o['quartiere']}) "
           f"{'[DA GUARDARE]' if o['da_guardare'] else ''}")
    a_("")
    a_("== La lista non deve essere dominata da raccordi/strutture/bordo ==")
    a_(f"  tratte da guardare con nome 'ponte/sottopasso/ecc': "
       f"{sum(1 for o in da_guardare if any(w in (o['nome'] or '').lower() for w in ('ponte','sottopasso','cavalcavia','viadotto')))}")
    a_(f"  tratte da guardare al bordo (porta entro 1,5 km): "
       f"{sum(1 for o in da_guardare if o.get('dist_porta_m', 1e9) <= 1500)} "
       f"(l'universo esclude gia' le tratte non affidabili, bordo compreso)")
    a_("")
    a_("== Tre esempi spiegati ==")
    if da_guardare:
        o = da_guardare[0]
        a_(f"  1) da guardare: {o['nome']} ({o['quartiere']}) - {o['veic_giorno']:,.0f} veic/giorno "
           f"+-{100*o['fascia_50']:.0f}%, {o['corsie_totali']:.0f} corsie, "
           f"{o['veic_per_corsia']:,.0f}/corsia, TP coperto {o['copertura_con_metro']:.0%} "
           f"(freq max {o['freq_max_300']:.1f}/h), linee {o['n_linee_300']}")
    buono = [o for o in torino if o["molto_traffico"] and not o["poco_tp"]]
    if buono:
        o = max(buono, key=lambda o: o["veic_giorno"])
        a_(f"  2) molto traffico ma TP buono: {o['nome']} - {o['veic_giorno']:,.0f} veic/giorno, "
           f"TP coperto {o['copertura_con_metro']:.0%}, freq max {o['freq_max_300']:.1f}/h")
    debole = [o for o in torino if not o["molto_traffico"] and o["poco_tp"]]
    if debole:
        o = max(debole, key=lambda o: o["veic_giorno"])
        a_(f"  3) poco traffico e poco TP: {o['nome']} - {o['veic_giorno']:,.0f} veic/giorno, "
           f"TP coperto {o['copertura_con_metro']:.0%}")
    a_("")
    a_("== Controllo di buon senso: accordo con la conoscenza di Leo (NON taratura) ==")
    a_(f"  strade nella fascia giusta (A/B/C): {n18} su {len(LEO_STRADE)} "
       f"(soglie bande: A >= {q66:,.0f}, B >= {q33:,.0f})")
    for x in accordo18:
        a_(f"      {x['strada']:18s} Leo {x['leo']:2s}  nostro {str(x['nostro']):2s}  "
           f"{'OK' if x['giusto'] else 'diverso'}")
    a_(f"  confronti giusti: {n7} su {len(LEO_CONFRONTI)}")
    for x in accordo7:
        a_(f"      {x['confronto']:34s} nostro {x['nostro']}  "
           f"{'OK' if x['giusto'] else 'diverso'}")
    a_("")
    a_("== LIMITI DA DICHIARARE OVUNQUE ==")
    for lim in [
        f"Le stime di traffico sono {classe} (errore mediano {100*val['errore_mediano']:.0f}%): "
        "buone per ordinare, non per contare i veicoli.",
        "I sensori 5T di Torino sono a un solo verso: la punta mattina/sera del traffico e' stimata "
        "solo per la congestione, non validata.",
        "La domanda e' l'indagine IMQ 2022: solo residenti 11-84 anni, giorno feriale medio; mancano "
        "merci, turisti, non residenti.",
        "L'offerta di trasporto pubblico e' quella programmata (GTFS): non tiene conto di ritardi, "
        "capienza, affollamento. Nessuna misura dei passeggeri.",
        "Il TP si misura per POSIZIONE delle fermate (>=4 partenze/ora entro 300 m), non dai bus "
        "sulla strada; la metropolitana/ferrovia contano entro 600 m.",
        "Centro (ZTL e aree pedonali) non stimato in modo affidabile: durante le ore ZTL il "
        "traffico di attraversamento sul centro e' escluso dal modello.",
    ]:
        a_(f"  - {lim}")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))


if __name__ == "__main__":
    main()
