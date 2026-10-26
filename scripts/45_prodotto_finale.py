# -*- coding: utf-8 -*-
"""
scripts/45_prodotto_finale.py - Pacchetto G del piano Fase 3.

Costruisce il prodotto finale per corridoio:
 - valore MISURATO dove c'e' un sensore (stimato=false, fonte=sensore);
 - valore del modello tarato altrove (stimato=true, fonte=modello C) con la
   classe di esito del pacchetto F;
 - livello di fiducia: alta = sensore sullo stesso corridoio entro 300 m;
   media = modello tarato e classe C-ASSOLUTO o C-INDICE e il corridoio non e'
   sotto il 5% del massimo (il modello e' sensibile); bassa = altro;
 - campo da pubblicare secondo la classe di esito (qui C-DEBOLE -> classe3).

Output:
  data/processed/traffico_stimato_finale.json
  docs/rapporti/RAPPORTO_TRAFFICO_C.txt
"""

import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))


def trova_radice():
    for cartella in [AQUI, *AQUI.parents]:
        if cartella.name.lower() == "gtt":
            return cartella
    return AQUI.parent


RADICE = trova_radice()
OUT_DIR = RADICE / "data" / "processed" / "traffico_c"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_TRAFFICO_C.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)


def main():
    cm = json.loads((OUT_DIR / "corridoi_modello.json").read_text(encoding="utf-8"))
    corridoi = cm["corridoi"]
    sensori_corr = cm["sensori"]
    val = json.loads((OUT_DIR / "taratura_validazione.json").read_text(encoding="utf-8"))
    classe = val["classe_esito"]
    finale = val["variante_finale"]
    a_tot = val["varianti"][finale].get("a_totale")
    b_tot = val["varianti"][finale].get("b_totale")
    k_tot = val["varianti"][finale].get("k_totale")

    # sensori per corridoio (misurato + distanza)
    per_corridoio_sensore = {}
    for s in sensori_corr:
        per_corridoio_sensore.setdefault(s["corridoio"], []).append(s)

    # modello tarato per corridoio
    def tara(x):
        if x is None:
            return None
        if a_tot is not None and b_tot is not None:
            return float(a_tot) * float(x) ** float(b_tot)
        return float(x) * float(k_tot)

    # soglie di classe3 sui corridoi con flusso > 0 e almeno 3 tratti (strade vere,
    # non spezzoni): i tercili su tutti i corridoi sarebbero inutilmente bassi
    positivi = [c["flusso_diurno_medio"] for c in corridoi
                if c.get("n_tratti", 0) >= 3 and c.get("flusso_diurno_medio", 0) > 0]
    q33, q67 = (float(np.percentile(positivi, 33.3)), float(np.percentile(positivi, 66.7))) \
        if positivi else (0.0, 0.0)

    # soglia "modello sensibile": 5% del massimo
    fmax = max(positivi) if positivi else 1.0
    soglia_sensibile = 0.05 * fmax

    def classe3(x):
        if x is None or x <= 0:
            return "basso"
        if x >= q67:
            return "alto"
        if x >= q33:
            return "medio"
        return "basso"

    fiducia_conta = {"alta": 0, "media": 0, "bassa": 0}
    out = []
    for c in corridoi:
        n = c.get("n_tratti", 0)
        base = {
            "nome": c["nome"], "chiave": c.get("chiave"),
            "comune": c.get("comune"), "punteggio": c["punteggio"],
            "lunghezza_km": c["lunghezza_km"], "n_tratti": n,
            "km_coperti_dal_modello": c.get("km_tratti_modello"),
        }
        if not n:
            base.update({"fonte": None, "stimato": True, "senza_stima": True,
                         "motivo": c.get("motivo"), "fiducia": "bassa"})
            out.append(base)
            fiducia_conta["bassa"] += 1
            continue
        modello = c["flusso_diurno_medio"]
        tarato = tara(modello)
        base["modello_C_diurno_2versi"] = round(tarato, 1)
        base["modello_C_grezzo"] = round(modello, 1)
        base["modello_stimato"] = True
        base["stimato"] = True
        base["fonte"] = "modello C"
        base["classe_esito"] = classe
        base["classe3"] = classe3(tarato)
        s = per_corridoio_sensore.get(c["nome"])
        if s:
            m = float(s[0]["misurato_diurno_2versi"])
            base["misurato_diurno_2versi"] = round(m, 1)
            base["misurato"] = True
            base["fonte"] = "sensore"
            base["stimato"] = False
            base["fiducia"] = "alta" if float(s[0]["dist_sensore_tratto_m"] or 999) <= 300 else "bassa"
        else:
            if classe in ("C-ASSOLUTO", "C-INDICE") and tarato is not None and tarato >= soglia_sensibile:
                base["fiducia"] = "media"
            else:
                base["fiducia"] = "bassa"
        # campi per la pubblicazione secondo la classe
        if classe == "C-ASSOLUTO":
            base["veic_diurno_2versi"] = round(tarato, 1)
        elif classe == "C-INDICE":
            base["indice"] = 1 + min(4, int(4 * (tarato / fmax)) if fmax else 0)
        elif classe == "C-DEBOLE":
            base["classe3"] = base["classe3"]
        fiducia_conta[base["fiducia"]] += 1
        out.append(base)

    # corridoi di Torino ordinati per traffico stimato
    torino = [c for c in out if c.get("comune") == "Torino" and c.get("n_tratti")]
    torino.sort(key=lambda c: -(c.get("modello_C_diurno_2versi") or 0))

    # --- sorprese ---
    sorprese = []
    for c in out:
        if not c.get("n_tratti") or c.get("misurato"):
            continue
        p = c["punteggio"]
        f = c.get("modello_C_diurno_2versi") or 0
        if p <= 2 and f >= 0.25 * fmax:
            sorprese.append((f, c["nome"], p, "molto piu' traffico del previsto per la classe di strada"))
    sorprese.sort(key=lambda t: -t[0])

    doc = {
        "stimato": True,
        "classe_esito": classe,
        "variante_finale": finale,
        "taratura": {"a": a_tot, "b": b_tot, "k": k_tot},
        "soglie_classe3": {"q33": round(q33, 1), "q67": round(q67, 1)},
        "conteggi_fiducia": fiducia_conta,
        "nota": ("Ogni valore e' tranne quelli marcati misurato=true (sensore 5T). "
                 "Grandezza: veicoli/giorno 6-21 a due versi."),
        "corridoi": out,
    }
    (OUT_DIR / "traffico_stimato_finale.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    # il piano chiede il file anche in data/processed/traffico_stimato_finale.json
    (RADICE / "data" / "processed" / "traffico_stimato_finale.json").write_text(
        json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    # --- rapporto ---
    righe = []
    def a(s=""):
        righe.append(s)
    a("RAPPORTO FINALE - TRAFFICO VEICOLARE STIMATO (metodo C, Risultato 8)")
    a("=" * 74)
    a(f"Classe di esito (pacchetto F): {classe}   variante finale: {finale}")
    a("Taratura: " + (f"misurato = {a_tot:.2f} x modello^{b_tot:.3f}" if a_tot else f"k = {k_tot:.3f}"))
    a(f"Corridoi totali: {len(out):,}  con stima: {sum(1 for c in out if c.get('n_tratti')):,}  "
      f"senza stima: {sum(1 for c in out if not c.get('n_tratti')):,}")
    a(f"Fiducia: alta {fiducia_conta['alta']} (sensore sul corridoio), "
      f"media {fiducia_conta['media']}, bassa {fiducia_conta['bassa']}")
    a("")
    a("ATTENZIONE - cosa si puo' pubblicare:")
    if classe == "C-DEBole" or classe == "C-DEBOLE":
        a("  essendo la classe C-DEBOLE, il valore pubblicabile e' solo la CLASSE a 3 livelli")
        a("  (alto/medio/basso, campo classe3), marcata come DEBOLE. I numeri di veicoli/giorno")
        a("  ci sono nel file ma vanno usati con cautela: la correlazione di rango e' 0,58.")
    a("")
    a(f"Soglie classe3: medio da {q33:,.0f}, alto da {q67:,.0f} veicoli/giorno (dopo taratura).")
    a("")
    a("== 30 corridoi di Torino con piu' traffico stimato ==")
    for c in torino[:30]:
        mis = f"  (sensore: {c['misurato_diurno_2versi']:,.0f})" if c.get("misurato") else ""
        a(f"  {c['modello_C_diurno_2versi']:9,.0f} veic/g  {c['classe3']:5s} fiducia {c['fiducia']:5s} "
          f"{c['nome'][:42]:42s} p{c['punteggio']}{mis}")
    a("")
    a("== 10 sorprese rispetto al senso comune ==")
    for f, nome, p, sp in sorprese[:10]:
        a(f"  {f:9,.0f} veic/g [STIMATO]  {nome[:45]:45s} punteggio {p} - {sp}")
    if len(sorprese) < 10:
        a(f"  (trovate {len(sorprese)} strade di basso rango con traffico alto; le altre "
          f"sorprese possibili sono le arterie con traffico basso, da leggere nella tabella completa)")
    a("")
    a("== Limiti (da dichiarare sempre) ==")
    for lim in [
        "IMQ 2022: solo residenti 11-84 anni, giorno feriale medio, campione telefonico. "
        "Mancano merci, turisti, non residenti: il modello sottostima in media (k = 1,7).",
        "Zone grandi (23 quartieri + 189 comuni): il traffico e' distribuito per punti, "
        "non per singolo indirizzo.",
        "Assegnazione tutto-o-niente senza congestione ne' capacita': il traffico si concentra "
        "sui percorsi piu' veloci; i valori sui singoli tratti sono indicativi.",
        "Peso che non produce flusso: ~46% dei viaggi (vedi riepilogo del pacchetto D), "
        "quasi tutto viaggi con entrambi gli estremi fuori dal taglio OSM (praticamente "
        "non attraversano l'area studiata); dentro Torino l'area persa e' ~2% dei viaggi.",
        "Traffico esterno concentrato su poche porte: i valori sui tratti di bordo non sono attendibili.",
        "17 sensori esclusi (morti/bloccati) non usati per tarare; 3 codici lcd1 condivisi da 2 sensori.",
    ]:
        a(f"  - {lim}")
    RAPPORTO.write_text("\n".join(righe) + "\n", encoding="utf-8")
    print("\n".join(righe))
    print("\nTop 5 corridoi di Torino per traffico stimato:")
    for c in torino[:5]:
        print(f"  {c['modello_C_diurno_2versi']:,.0f}  {c['nome']}")


if __name__ == "__main__":
    main()
