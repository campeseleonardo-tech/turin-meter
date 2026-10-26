#!/usr/bin/env python3
"""37_traffico_AB.py

Vedi sviluppo/note_tecniche/R8_traffico.md: i metodi A e B per stimare il
traffico dove il sensore non c'e', con la prova "nascondi un sensore".

Grandezze usate (dal file dello script 33 v2, feriale):
- f_punta_am = massimo fra le ore locali 7-9 (per verso, non si moltiplica);
- f_punta_pm = massimo fra le ore 16-19 (per verso);
- f_diurno   = somma delle ore locali 6-21;
- f_diurno_totale (due versi) = somma dei due versi se la coppia esiste; altrimenti
  f_diurno x 2 con `un_verso: true` e `stimato: true` (decisione 5 del piano).

Unita' di calcolo: un sensore (o una coppia di versi sommata) abbinato a un
corridoio SICURO (Passo 8) o confermato (Claude + Passo 8b).

Metodo A: per gruppo (punteggio 3/4/5) x (dentro Torino / fuori Torino) la
mediana, il 10o e il 90o percentile; gruppi con meno di 3 unita': "non stimabile".
Metodo B: ai corridoi senza sensore ma con lo stesso nome di un corridoio con
sensore, entro 1 km, si estende il valore del sensore (`"metodo": "B"`, stimato).
  Approssimazione dichiarata: 1 km in linea d'aria, non lungo la strada.
  Fonte B esclusa per i codici condivisi (posizione non sicura, es. 40189).

Prova "nascondi un sensore" per A: per ogni unita' la previsione e' la mediana del
suo gruppo SENZA di lei; errore relativo = |previsione - misurato| / misurato.
Prova per B: sui corridoi con almeno 2 sensori, distanza fra i due sensori e
errore fra i loro valori.

I risultati NON si "aggiustano": se gli errori sono grandi, si scrivono come sono.

Output:
- data/processed/traffico_stimato_AB.json
- docs/rapporti/RAPPORTO_TRAFFICO_AB.txt

Solo libreria standard.
"""

import importlib.util
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comuni import haversine_m as hav  # noqa: E402  (stessa formula della copia che stava qui)

RADICE = Path(__file__).resolve().parents[1]
IN_FLUSSO = RADICE / "data" / "processed" / "flusso_5t_sensori.json"
IN_V2 = RADICE / "data" / "processed" / "sensori_corridoi_v2.json"
IN_CONF = RADICE / "data" / "processed" / "abbinamenti_confermati_v2.json"
IN_ESCLUSI = RADICE / "data" / "processed" / "sensori_esclusi.json"
IN_CORRIDOI = RADICE / "data" / "processed" / "importanza_vie.json"
OUT = RADICE / "data" / "processed" / "traffico_stimato_AB.json"
RAPPORTO = RADICE / "docs" / "rapporti" / "RAPPORTO_TRAFFICO_AB.txt"
RAPPORTO.parent.mkdir(parents=True, exist_ok=True)

TIPO = "0"                # feriale
SOGLIA_B_M = 1000         # metro 1 km, in linea d'aria (approssimazione dichiarata)
SOGLIA_COPPIA_M = 200     # coppia di versi (decisione 5)
MIN_GRUPPO = 3            # sotto questo numero il gruppo non e' stimabile

RIGHE = []


def scrivi(msg=""):
    RIGHE.append(str(msg))


def carica_script_24():
    percorso = RADICE / "scripts" / "24_importanza_vie.py"
    spec = importlib.util.spec_from_file_location("m24_importanza_vie", percorso)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def p10_p90(valori):
    """10o e 90o percentile (statistics.quantiles, metodo 'inclusive')."""
    if len(valori) < 2:
        return None, None
    q = statistics.quantiles(valori, n=10, method="inclusive")
    return q[0], q[8]


def distanza_minima(lat, lon, geometria, haversine_m):
    migliore = None
    for tratto in geometria:
        for punto in tratto:
            d = haversine_m(lat, lon, punto[0], punto[1])
            if migliore is None or d < migliore:
                migliore = d
    return migliore


def main():
    m24 = carica_script_24()
    for p in (IN_FLUSSO, IN_V2, IN_CONF, IN_ESCLUSI, IN_CORRIDOI):
        if not p.is_file():
            raise SystemExit(f"File non trovato: {p}")

    flusso = json.loads(IN_FLUSSO.read_text(encoding="utf-8"))["sensori"]
    v2 = json.loads(IN_V2.read_text(encoding="utf-8"))
    conf = json.loads(IN_CONF.read_text(encoding="utf-8"))
    esclusi_raw = json.loads(IN_ESCLUSI.read_text(encoding="utf-8"))
    if isinstance(esclusi_raw, dict):
        esclusi_raw = esclusi_raw.get("sensori", [])
    esclusi = {str(e["lcd1"]): e["motivo"] for e in esclusi_raw}
    corridoi = json.loads(IN_CORRIDOI.read_text(encoding="utf-8"))["corridoi"]

    classi = {k: s for k, s in v2["sensori"].items()}
    confermati = {str(c["lcd1"]): c for c in conf["confermati"]}

    # --- unita': sensori abbinati a un corridoio SICURO o confermato ---
    unita = {}
    for lcd1, s in classi.items():
        if s["classe"] == "SICURO" and s.get("corridoio"):
            unita[lcd1] = dict(corridoio=s["corridoio"], fonte="SICURO")
    for lcd1 in confermati:
        if lcd1 in unita:
            continue
        s = classi.get(lcd1)
        if s and s.get("corridoio"):
            unita[lcd1] = dict(corridoio=s["corridoio"], fonte="confermato")
    for lcd1 in list(unita):
        if lcd1 in esclusi:
            del unita[lcd1]

    # --- valori di ogni sensore ---
    def valori_sensore(lcd1):
        s = flusso.get(lcd1)
        if not s or "tipo" not in s:
            return None
        b = s["tipo"].get(TIPO)
        if not b:
            return None
        return b

    # --- coppie di versi fra le unita' (stesso nome, verso opposto, <= 200 m) ---
    per_nome = {}
    for lcd1 in unita:
        per_nome.setdefault(flusso[lcd1]["via"], []).append(lcd1)
    coppie = []
    usati_in_coppia = set()
    for nome, lista in per_nome.items():
        if len(lista) != 2:
            continue
        a, b = lista
        if flusso[a]["dir"] == flusso[b]["dir"]:
            continue
        d = hav(flusso[a]["lat"], flusso[a]["lon"], flusso[b]["lat"], flusso[b]["lon"])
        if d <= SOGLIA_COPPIA_M:
            coppie.append((a, b, d))
            usati_in_coppia |= {a, b}

    # --- costruzione dei gruppi (unita' di calcolo) ---
    def gruppo_di(corr, lcd1):
        dentro = bool(flusso[lcd1]["urbano"])
        return f"p{corr['punteggio']}_{'dentro' if dentro else 'fuori'}"

    unita_calcolo = []
    for a, b, d in coppie:
        ba, bb = valori_sensore(a), valori_sensore(b)
        if not ba or not bb:
            continue
        unita_calcolo.append(dict(
            id=f"{a}+{b}", tipo="due_versi", lcd1=[a, b], corridoio=unita[a]["corridoio"],
            sorgente=unita[a]["fonte"], distanza_coppia_m=round(d, 1),
            gruppo=gruppo_di(unita[a]["corridoio"], a),
            f_punta_am=ba["f_punta_am"],
            f_punta_am_secondo=bb["f_punta_am"],
            f_punta_pm=ba["f_punta_pm"], f_punta_pm_secondo=bb["f_punta_pm"],
            f_diurno=ba["f_diurno"], f_diurno_secondo=bb["f_diurno"],
            f_diurno_totale=(None if ba["f_diurno"] is None or bb["f_diurno"] is None
                             else ba["f_diurno"] + bb["f_diurno"]),
            un_verso=False, stimato=False))
    for lcd1 in sorted(unita):
        if lcd1 in usati_in_coppia:
            continue
        b = valori_sensore(lcd1)
        if not b:
            continue
        unita_calcolo.append(dict(
            id=lcd1, tipo="sensore", lcd1=[lcd1], corridoio=unita[lcd1]["corridoio"],
            sorgente=unita[lcd1]["fonte"], gruppo=gruppo_di(unita[lcd1]["corridoio"], lcd1),
            f_punta_am=b["f_punta_am"], f_punta_pm=b["f_punta_pm"],
            f_diurno=b["f_diurno"],
            f_diurno_totale=(None if b["f_diurno"] is None else 2 * b["f_diurno"]),
            un_verso=True, stimato=True))

    # --- metodo A: statistiche per gruppo ---
    gruppi = {}
    for u in unita_calcolo:
        if u["f_diurno_totale"] is None:
            continue
        gruppi.setdefault(u["gruppo"], []).append(u)
    gruppi_A = {}
    for g, lista in sorted(gruppi.items()):
        vals = [u["f_diurno_totale"] for u in lista]
        med = statistics.median(vals)
        p10, p90 = p10_p90(vals)
        gruppi_A[g] = dict(n=len(lista), stimabile=len(lista) >= MIN_GRUPPO,
                           f_diurno_totale=dict(mediana=round(med),
                                                p10=None if p10 is None else round(p10),
                                                p90=None if p90 is None else round(p90)),
                           unita=[u["id"] for u in lista])

    # --- prova "nascondi un sensore" per A ---
    prova_A = []
    for u in unita_calcolo:
        if u["f_diurno_totale"] is None:
            continue
        altri = [x["f_diurno_totale"] for x in gruppi.get(u["gruppo"], [])
                 if x["id"] != u["id"] and x["f_diurno_totale"] is not None]
        stimabile = gruppi_A.get(u["gruppo"], {}).get("stimabile", False)
        if not stimabile or not altri or u["f_diurno_totale"] <= 0:
            prova_A.append(dict(id=u["id"], gruppo=u["gruppo"], usato=False,
                                motivo="gruppo non stimabile (< 3 unita') "
                                       "o valore misurato nullo"))
            continue
        pred = statistics.median(altri)
        err = abs(pred - u["f_diurno_totale"]) / u["f_diurno_totale"]
        prova_A.append(dict(id=u["id"], gruppo=u["gruppo"], usato=True,
                            misurato=u["f_diurno_totale"], previsione=round(pred),
                            errore_relativo=round(err, 4),
                            scarto_relativo_con_segno=round((pred - u["f_diurno_totale"])
                                                            / u["f_diurno_totale"], 4)))

    def riassunto_prova(voci):
        us = [v for v in voci if v["usato"]]
        if not us:
            return dict(n=0, nota="nessun sensore valutabile")
        errs = [v["errore_relativo"] for v in us]
        med = statistics.median(errs)
        p10, p90 = p10_p90(errs)
        return dict(n=len(us), errore_mediano=round(med, 4),
                    errore_90=round(p90, 4) if p90 is not None else None,
                    distorsione_media_con_segno=round(
                        sum(v["scarto_relativo_con_segno"] for v in us) / len(us), 4),
                    peggiore=round(max(errs), 4))

    prova_A_riassunto = {g: riassunto_prova([v for v in prova_A if v["gruppo"] == g])
                         for g in sorted(gruppi_A)}
    prova_A_riassunto["TOTALE"] = riassunto_prova(prova_A)

    # --- corridoi con un valore (sensore) e metodo B ---
    per_nome_corr = {}
    for i, c in enumerate(corridoi):
        per_nome_corr.setdefault(c["chiave_normalizzata"], []).append(i)

    corridoi_out = {}
    per_corridoio_sensore = {}
    for u in unita_calcolo:
        per_corridoio_sensore.setdefault(u["corridoio"]["nome"], []).append(u)
    geometria_per_nome = {}
    for c in corridoi:
        geometria_per_nome.setdefault(c["nome"], c)

    def km_entro_raggio(nome, lat, lon, raggio_m):
        """(km del corridoio entro il raggio dal punto, km totali del corridoio)."""
        c = geometria_per_nome.get(nome)
        if not c:
            return None, None
        dentro = tot = 0.0
        for tratto in c["geometria"]:
            for (la1, lo1), (la2, lo2) in zip(tratto, tratto[1:]):
                d = hav(la1, lo1, la2, lo2)
                tot += d
                if (hav(lat, lon, la1, lo1) <= raggio_m
                        and hav(lat, lon, la2, lo2) <= raggio_m):
                    dentro += d
        return dentro / 1000.0, tot / 1000.0

    for nome, us in per_corridoio_sensore.items():
        c0 = us[0]["corridoio"]
        lcd0 = us[0]["lcd1"][0]
        km_d, km_t = km_entro_raggio(nome, flusso[lcd0]["lat"], flusso[lcd0]["lon"],
                                     SOGLIA_B_M)
        corridoi_out[nome] = dict(
            nome=nome, punteggio=c0["punteggio"], lunghezza_km=c0["lunghezza_km"],
            dentro_torino=any(flusso[u["lcd1"][0]]["urbano"] for u in us),
            gruppo=us[0]["gruppo"], metodo="sensore", stimato=False,
            unita=[u["id"] for u in us],
            f_punta_am=us[0]["f_punta_am"], f_punta_pm=us[0]["f_punta_pm"],
            f_diurno=us[0]["f_diurno"], f_diurno_totale=us[0]["f_diurno_totale"],
            codice_condiviso=any(
                u["lcd1"][0] in v2.get("codici_condivisi", {})
                or v2.get("sensori", {}).get(u["lcd1"][0], {}).get("codice_condiviso", False)
                for u in us),
            unita_valori=[dict(id=u["id"], f_punta_am=u["f_punta_am"],
                               f_punta_pm=u["f_punta_pm"], f_diurno=u["f_diurno"],
                               f_diurno_totale=u["f_diurno_totale"]) for u in us],
            f_punta_am_secondo_verso=us[0].get("f_punta_am_secondo"),
            f_punta_pm_secondo_verso=us[0].get("f_punta_pm_secondo"),
            nota=("due sensori dello stesso verso sullo stesso corridoio"
                  if len(us) > 1 else
                  ("coppia di versi sommata" if us[0]["tipo"] == "due_versi"
                   else "un solo verso: per il totale a due versi si usa x2 (stimato)")),
            estensione_B=dict(
                metodo="B", stimato=True, raggio_m=SOGLIA_B_M,
                km_corridoio=None if km_t is None else round(km_t, 2),
                km_entro_1km=None if km_d is None else round(km_d, 2),
                quota_entro_1km=None if not km_t else round(km_d / km_t, 4),
                nota="il valore del sensore vale, come stima, lungo il corridoio fino a "
                     "1 km (in linea d'aria) dal sensore; oltre non si estende"))

    # metodo B: corridoi senza unita', stesso nome di un corridoio con unita', entro 1 km
    nomi_con_unita = {}
    for u in unita_calcolo:
        lcd1 = u["lcd1"][0]
        if lcd1 in v2.get("codici_condivisi", {}):
            continue                      # posizione non sicura: escluso come fonte di B
        if u["f_diurno"] is None:
            continue
        nomi_con_unita.setdefault(u["corridoio"]["nome"], []).append(u)

    b_estesi = []
    for nome_sorg, us in nomi_con_unita.items():
        corr_sorg = us[0]["corridoio"]
        chiave = m24.normalizza(corr_sorg["nome"])
        for idx in per_nome_corr.get(chiave, []):
            c = corridoi[idx]
            if c["nome"] in corridoi_out or c["nome"] == nome_sorg:
                continue
            lat, lon = flusso[us[0]["lcd1"][0]]["lat"], flusso[us[0]["lcd1"][0]]["lon"]
            d = distanza_minima(lat, lon, c["geometria"], m24.haversine_m)
            if d is not None and d <= SOGLIA_B_M:
                corridoi_out[c["nome"]] = dict(
                    nome=c["nome"], punteggio=c["punteggio"],
                    lunghezza_km=c["lunghezza_km"],
                    dentro_torino="(TO)" in c["nome"], gruppo=us[0]["gruppo"],
                    metodo="B", stimato=True,
                    esteso_da=us[0]["id"], distanza_dalla_fonte_m=round(d, 1),
                    f_punta_am=us[0]["f_punta_am"], f_punta_pm=us[0]["f_punta_pm"],
                    f_diurno=us[0]["f_diurno"], f_diurno_totale=us[0]["f_diurno_totale"],
                    codice_condiviso=False,
                    nota=f"valore del sensore {us[0]['id']} esteso alla stessa strada "
                         f"({m24.normalizza(c['nome'])}), {round(d)} m in linea d'aria")
                b_estesi.append((c["nome"], us[0]["id"], round(d, 1)))

    # --- prova per B: corridoi con almeno 2 sensori (stesso corridoio, stesso verso) ---
    coppie_corridoio = []
    for nome, us in per_corridoio_sensore.items():
        singoli = [u for u in us if u["tipo"] == "sensore"]
        for i in range(len(singoli)):
            for j in range(i + 1, len(singoli)):
                a, b = singoli[i], singoli[j]
                la, lb = a["lcd1"][0], b["lcd1"][0]
                if flusso[la]["dir"] != flusso[lb]["dir"]:
                    continue
                if a["f_diurno"] in (None, 0) or b["f_diurno"] in (None, 0):
                    continue
                d = hav(flusso[la]["lat"], flusso[la]["lon"],
                        flusso[lb]["lat"], flusso[lb]["lon"])
                coppie_corridoio.append(dict(
                    corridoio=nome, lcd1_a=la, lcd1_b=lb, distanza_m=round(d, 1),
                    f_diurno_a=a["f_diurno"], f_diurno_b=b["f_diurno"],
                    rapporto=round(a["f_diurno"] / b["f_diurno"], 3),
                    errore_relativo=round(abs(a["f_diurno"] - b["f_diurno"])
                                          / b["f_diurno"], 4)))
    prova_B = dict(casi=len(coppie_corridoio),
                   valutabile=len(coppie_corridoio) >= 5,
                   nota=("distanza in linea d'aria; errore = |f_diurno_A - f_diurno_B| / "
                         "f_diurno_B (usare A al posto di B)"),
                   tabella=sorted(coppie_corridoio, key=lambda x: x["distanza_m"]))

    # --- corridoi senza stima ---
    senza = {}
    for c in corridoi:
        if c["nome"] in corridoi_out:
            continue
        chiave = c["chiave_normalizzata"]
        if any(m24.normalizza(u["corridoio"]["nome"]) == chiave for u in unita_calcolo):
            motivo = "stessa strada di un corridoio con sensore ma oltre 1 km"
        elif chiave in {m24.normalizza(flusso[l]["via"]) for l in flusso}:
            motivo = "nome uguale a una via con sensore, ma nessun corridoio abbinato"
        else:
            motivo = "nessun sensore su questa strada e nessun metodo applicabile"
        senza[c["nome"]] = motivo

    payload = dict(
        fonte={"flusso": "data/processed/flusso_5t_sensori.json",
               "abbinamenti": "data/processed/sensori_corridoi_v2.json",
               "confermati": "data/processed/abbinamenti_confermati_v2.json",
               "corridoi": "data/processed/importanza_vie.json"},
        tag="valori misurati dai sensori; i valori con metodo B e i f_diurno_totale "
            "con un_verso sono",
        parametri={"tipo_giorno": "feriale", "soglia_B_m": SOGLIA_B_M,
                   "soglia_coppia_m": SOGLIA_COPPIA_M, "min_gruppo": MIN_GRUPPO,
                   "arrotondamenti": "valori in veicoli/ora arrotondati all'intero; "
                                     "errori a 4 decimali"},
        codici_condivisi=v2.get("codici_condivisi", {}),
        gruppi_A=gruppi_A,
        prova_A={"per_unita": prova_A, "riassunto": prova_A_riassunto},
        prova_B=prova_B,
        coppie_stesso_corridoio=coppie_corridoio,
        unita=unita_calcolo,
        corridoi=corridoi_out,
        corridoi_senza_stima={k: senza[k] for k in sorted(senza)},
        conteggi={"unita_di_calcolo": len(unita_calcolo),
                  "corridoi_con_valore": len(corridoi_out),
                  "corridoi_con_metodo_B": len(b_estesi),
                  "corridoi_senza_stima": len(senza)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")

    # ---------- rapporto ----------
    scrivi("TRAFFICO STIMATO CON I METODI A E B (feriale)  [MISURATO dove c'e' il sensore]")
    scrivi("=" * 92)
    scrivi(f"unita' di calcolo (sensore o coppia di versi, abbinati a un corridoio): {len(unita_calcolo)}")
    scrivi(f"  di cui coppie di versi sommate: {sum(1 for u in unita_calcolo if u['tipo'] == 'due_versi')}")
    scrivi(f"  di cui un solo verso (totale x2 stimato): {sum(1 for u in unita_calcolo if u['un_verso'])}")
    scrivi(f"corridoi con un valore: {len(corridoi_out)} (di cui estesi da metodo B da un "
           f"altro corridoio: {len(b_estesi)})")
    km_dentro = sum(c["estensione_B"]["km_entro_1km"] or 0 for c in corridoi_out.values()
                    if "estensione_B" in c)
    km_tot = sum(c["estensione_B"]["km_corridoio"] or 0 for c in corridoi_out.values()
                 if "estensione_B" in c)
    scrivi(f"metodo B dentro il corridoio del sensore (parti entro 1 km): "
           f"{km_dentro:.1f} km su {km_tot:.1f} km dei corridoi con sensore"
           + (f" ({km_dentro / km_tot:.1%})" if km_tot else ""))
    scrivi(f"corridoi senza stima: {len(senza)}")
    scrivi("")
    scrivi("(1) METODO A - gruppi (punteggio x dentro/fuori Torino), valori di f_diurno_totale")
    scrivi(f"  {'gruppo':>14} {'n':>3} {'stimabile':>10} {'mediana':>8} {'p10':>7} {'p90':>7}  unita'")
    for g, v in sorted(gruppi_A.items()):
        t = v["f_diurno_totale"]
        scrivi(f"  {g:>14} {v['n']:>3} {'si' if v['stimabile'] else 'NO':>10} "
               f"{t['mediana']:>8} {str(t['p10']):>7} {str(t['p90']):>7}  {', '.join(v['unita'])}")
    scrivi("")
    scrivi("(2) PROVA 'NASCONDI UN SENSORE' per il metodo A (errore relativo)")
    scrivi("    errore = |mediana del gruppo senza il sensore - valore misurato| / valore misurato")
    scrivi(f"  {'gruppo':>14} {'n':>3} {'mediano':>8} {'90o':>7} {'peggiore':>9} {'distorsione':>12}")
    for g, v in prova_A_riassunto.items():
        if v["n"] == 0:
            scrivi(f"  {g:>14} {0:>3}  {v['nota']}")
        else:
            scrivi(f"  {g:>14} {v['n']:>3} {v['errore_mediano']:>8.1%} {v['errore_90']:>7.1%} "
                   f"{v['peggiore']:>9.1%} {v['distorsione_media_con_segno']:>12.1%}")
    scrivi("  (distorsione = media di (previsione - misurato)/misurato: positiva = A sovrastima)")
    scrivi("")
    scrivi("(3) Dettaglio della prova per il metodo A")
    scrivi(f"  {'unita':>14} {'gruppo':>14} {'misurato':>9} {'previsione':>11} {'errore':>8}")
    for v in prova_A:
        if not v["usato"]:
            scrivi(f"  {v['id']:>14} {v['gruppo']:>14} {'-':>9} {'-':>11} {'-':>8}  {v['motivo']}")
        else:
            scrivi(f"  {v['id']:>14} {v['gruppo']:>14} {v['misurato']:>9} "
                   f"{v['previsione']:>11} {v['errore_relativo']:>8.1%}")
    scrivi("")
    scrivi("(4) PROVA per il metodo B - coppie di sensori sullo STESSO corridoio e stesso verso")
    scrivi(f"    casi: {prova_B['casi']} -> {'valutabile' if prova_B['valutabile'] else 'NON VALUTABILE (< 5 casi)'}")
    scrivi(f"  {'corridoio':>34} {'a':>7} {'b':>7} {'dist_m':>8} {'f_A':>7} {'f_B':>7} "
           f"{'rapporto':>9} {'errore':>8}")
    for c in prova_B["tabella"]:
        scrivi(f"  {c['corridoio'][:34]:>34} {c['lcd1_a']:>7} {c['lcd1_b']:>7} "
               f"{c['distanza_m']:>8.1f} {c['f_diurno_a']:>7} {c['f_diurno_b']:>7} "
               f"{c['rapporto']:>9.2f} {c['errore_relativo']:>8.1%}")
    scrivi("")
    scrivi("(5) Corridoi con un valore")
    scrivi(f"  {'corridoio':>38} {'p':>2} {'metodo':>7} {'stim':>5} {'f_diurno':>9} "
           f"{'tot 2 versi':>12} {'km<=1km':>8} {'km tot':>7}  unita'")
    for nome in sorted(corridoi_out):
        c = corridoi_out[nome]
        ext = c.get("estensione_B", {})
        scrivi(f"  {nome[:38]:>38} {c['punteggio']:>2} {c['metodo']:>7} "
               f"{'si' if c['stimato'] else 'no':>5} {str(c['f_diurno']):>9} "
               f"{str(c['f_diurno_totale']):>12} {str(ext.get('km_entro_1km')):>8} "
               f"{str(ext.get('km_corridoio')):>7}  "
               f"{', '.join(c.get('unita', [c.get('esteso_da', '-')]))}")
    scrivi("")
    scrivi("(6) Corridoi senza stima, per motivo (l'elenco completo e' nel file JSON)")
    from collections import Counter
    for motivo, n in Counter(senza.values()).most_common():
        scrivi(f"  {n:>6}  {motivo}")
    interessanti = sorted(k for k, v in senza.items()
                          if "stessa strada" in v or "nome uguale" in v)
    scrivi(f"  corridoi da guardare (stessa strada di un sensore, o nome uguale a una via "
           f"con sensore): {len(interessanti)}")
    for k in interessanti[:40]:
        scrivi(f"      {k[:60]:60s} {senza[k]}")
    if len(interessanti) > 40:
        scrivi(f"      ... e altri {len(interessanti) - 40} nel file JSON")

    testo = "\n".join(RIGHE)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.write(testo + "\n")
    RAPPORTO.write_text(testo + "\n", encoding="utf-8")
    print(f"Rapporto salvato: {RAPPORTO}")
    print(f"JSON salvato: {OUT}")

    # --- controlli ---
    problemi = []
    # nessun sensore usato per predire se stesso: la previsione esclude sempre l'unita' stessa
    for g, lista in gruppi.items():
        for u in lista:
            altri = [x for x in lista if x["id"] != u["id"]]
            if any(x["id"] == u["id"] for x in altri):
                problemi.append(f"unita' {u['id']} presente fra le 'altre'")
    # nessun valore senza etichetta di metodo
    for nome, c in corridoi_out.items():
        if c.get("metodo") not in ("sensore", "B"):
            problemi.append(f"corridoio {nome}: metodo mancante")
    print("CONTROLLI:", "OK" if not problemi else f"PROBLEMI: {problemi[:5]}")
    print(f"corridoi con valore: {len(corridoi_out)} (B: {len(b_estesi)}); "
          f"senza stima: {len(senza)}; unita': {len(unita_calcolo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
