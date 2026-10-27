"""Risultato 10 (pubblico 5): case, servizi e fragilita'."""
import re
from schede.comune import circa, circa_mila, forma_base, leggi, migliaia, num, ora, pct2, virgola, voce




# ---------------------------------------------------------------- Risultato 10 (pubblico: 5) «Case, servizi e fragilita'»
# Tutti i numeri vengono da data/processed/case_fragilita_servizi.json (script 95); qui niente e' scritto a mano.

def nome_zona(n):
    """«D6 MIRAFIORI SUD» -> «Mirafiori Sud»: via il codice OMI davanti, maiuscole normali."""
    parole = n.split(" ", 1)
    resto = parole[1] if len(parole) == 2 and re.fullmatch(r"[A-Z]\d+", parole[0]) else n
    return " ".join(w.capitalize() for w in resto.split())




def scheda_r10():
    j = leggi("case_fragilita_servizi.json")
    e1, e2 = j["e1_si_paga_per_i_servizi"], j["e2_doppio_svantaggio"]
    se = e2["sezioni"]
    quota = se["quota_residenti_di_riferimento"]
    # stessa approssimazione degli omini (decimi): 9,5% -> «circa 1 su 10», cosi' titolo e testo coincidono
    decimi = round(10 * quota)
    n_su = round(10 / decimi) if decimi else 0
    return {
        "risultato": "10",
        "titolo": "Case, servizi e fragilità",
        "tag": "STIMATO / CENSIMENTO",
        "stato": "Fatto",
        "in_breve": "Le case costano di più dove ci sono più servizi? E dove la fragilità sociale è alta e i servizi sono pochi?",
        "domanda": "Chi vive dove i servizi sono pochi e le difficoltà sociali sono alte?",
        "numero_chiave": {"valore": se["residenti_doppio_svantaggio"], "unita": "",
                          "testo": f"residenti in sezioni con fragilità alta e pochi servizi ({virgola(100 * quota)}% dei residenti)"},
        "racconto": "", "risposta": [], "grafici": [], "metodo": [], "limiti": [], "parametri": [],
        "mappa": {"id": "vulnerabilita", "vista": "doppio", "nota": "Vista «Doppio svantaggio» nel tema Fragilità sociale."},
        "fonti": ["docs/en/METHODS.md", "data/processed/case_fragilita_servizi.json"],
        "generato": ora(),
        "avviso": ["Differenza fra zone, non effetto causale."],
        "in_english": [],
        "scenari": [{
            "nome": "Oggi",
            "numeri": [
                num("Residenti in sezioni con fragilità alta e pochi servizi", se["residenti_doppio_svantaggio"], "residenti"),
                num("Quota dei residenti di Torino", round(100 * quota, 1), "%"),
                num("Zone in doppio svantaggio", len(e2["zone"]), "zone"),
                num("Correlazione prezzo-servizi (Spearman)", e1["spearman"], ""),
            ],
            "nota": "Zone OMI di Torino; le sezioni si sommano nella zona, pesate per abitanti.",
        }],
        "_n_su": n_su,
    }




def servizi_a_piedi():
    """Dal vecchio risultato 1 (script 21, v3): residenti per numero di servizi di base raggiunti a piedi in 5, 10 e 15 minuti. Ritorna (grafico, % con tutti e 5 a 5 minuti, % a 15)."""
    v = leggi("risultato1_vuoti.json")
    v3, v2 = v["v3"], v["v2"]
    sol = v3["soglie"]

    def quota(m, k):   # % dei residenti delle zone abitate con k servizi presenti a m minuti
        return 100.0 * sol[str(m)]["per_n_servizi"][str(k)] / sol[str(m)]["residenti"]
    righe = []
    for m in (5, 10, 15):
        cinque, quattro = round(quota(m, 5), 1), round(quota(m, 4), 1)
        righe.append({"label": f"{m} minuti", "voci": [voce("tutti e 5 i servizi", cinque, tono="verde"), voce("4 servizi", quattro, tono="giallo"),
                                                         voce("3 o meno", round(100 - cinque - quattro, 1), tono="rosso")]})
    soglia = migliaia(v2["soglia_poco_abitata_ab_km2"])
    grafico = {"tipo": "pila100", "titolo": "Servizi a 5, 10 e 15 minuti a piedi", "unita": "%",
               "nota": f"Ogni barra è un tempo a piedi: 100% dei residenti delle zone abitate (almeno {soglia} abitanti per km²).", "righe": righe}
    return grafico, quota(5, 5), quota(15, 5)


def forma_r10(s):
    j = leggi("case_fragilita_servizi.json")
    e2 = j["e2_doppio_svantaggio"]
    cn, se = j["conteggi"], e2["sezioni"]
    # L9: legami a parita' di distanza dal centro (correlazione parziale sui ranghi, intervallo al 95%) e confronto col caso
    leg = {g["legame"]: g for g in j["e4_a_parita_di_distanza"]["legami"]}
    gf = leg["fragilita-servizi"]
    meno = lambda x: pct2(x).replace("-", "−")
    caso = se["confronto_col_caso"]
    volte_caso = virgola(round(caso["volte_il_caso"], 1))
    soglie = e2["soglie_fissate"]
    n_su = s["_n_su"]
    # grafico principale (L9b): una zona = un punto (fragilita', servizi, abitanti, nome) e la retta di tendenza: e' il legame che regge a parita' di distanza
    zone = j["zone"]
    rfs = j["e4_a_parita_di_distanza"]["retta_fragilita_servizi"]
    ic_f = f"da {meno(gf['parziale_ic95'][0])} a {meno(gf['parziale_ic95'][1])}"
    doppio = {z["zona"] for z in e2["zone"]}      # le zone in doppio svantaggio (script 95): bolle rosse nel grafico, stesse sigle di `zone`
    principale = {"tipo": "dispersione", "titolo": f"Fragilità sociale e servizi a piedi, una zona OMI per punto ({len(zone)} zone)",
                  "xlabel": "indice di fragilità sociale, 0-100", "ylabel": "punteggio «Tutti i servizi» a piedi, 0-100",
                  "passo_x": 10, "passo_y": 20, "xnome": "fragilità", "ynome": "servizi",
                  "punti": [[z["fragilita"], z["servizi"], z["abitanti"], nome_zona(z["zona"]), "rosso" if z["zona"] in doppio else None] for z in zone],
                  "legenda": [{"tono": "rosso", "label": "zone in doppio svantaggio"}, {"label": "altre zone"}],
                  "retta": {"a": rfs["intercetta_servizi"], "b": rfs["pendenza_servizi_per_punto_fragilita"], "label": "tendenza"},
                  "nota": ("Ogni punto è una zona, grande quanto i suoi abitanti. La linea è la tendenza: più la fragilità è alta, meno servizi. "
                           + (f"Il legame regge anche a parità di distanza dal centro: correlazione {meno(gf['parziale'])} ({ic_f})." if gf["regge"]
                              else f"A parità di distanza dal centro il legame non regge: correlazione {meno(gf['parziale'])} ({ic_f})."))}
    graf_servizi, c5, c15 = servizi_a_piedi()   # il grafico prezzo contro servizi si toglie: il legame non regge a parita' di distanza dal centro
    zd = e2["zone"]
    nomi_zd = ", ".join(nome_zona(z["zona"]) for z in zd[:5]) + (" e altre" if len(zd) > 5 else "")
    classi = se["classi"]
    nomi_classi = [("tutte_e_due", "fragilità alta e servizi bassi", "rosso"), ("solo_fragilita", "solo fragilità alta", "arancio"),
                   ("solo_servizi", "solo servizi bassi", "blu"), ("nessuna", "nessuna delle due", "verde")]
    graf_classi = {"tipo": "barre", "titolo": "Residenti delle sezioni di Torino per condizione", "unita": "residenti",
                   "nota": f"Sezioni abitate di Torino, senza le zone quasi disabitate. Fragilità alta = indice sopra {virgola(se['soglia_fragilita_sopra'])} su 100 (il 20% più alto); "
                           f"servizi bassi = punteggio fino a {virgola(se['soglia_servizi_fino_a'])} su 100 (il 20% più basso).",
                   "voci": [{"label": n, "valore": classi[k]["residenti"], "tono": tn, "testo": f"{migliaia(classi[k]['residenti'])} ({migliaia(classi[k]['sezioni'])} sezioni)"}
                            for k, n, tn in nomi_classi]}
    nz_usate = cn["zone_usate"]
    return forma_base(
        s,
        f"Circa 1 torinese su {n_su} vive in una zona con più difficoltà sociali e pochi servizi",
        "Chi vive dove i servizi sono pochi e le difficoltà sociali sono alte?",
        {"valore": se["residenti_doppio_svantaggio"], "unita": "",
         "testo": f"residenti in zone con più difficoltà sociali e servizi bassi: il {virgola(100 * se['quota_residenti_di_riferimento'])}% dei residenti delle zone abitate.",
         "breve": "residenti con pochi servizi e più difficoltà"},
        principale,
        [f"Fragilità alta e pochi servizi capitano insieme {volte_caso} volte più spesso che se fossero distribuiti a caso in città.",
         f"A 15 minuti a piedi quasi tutti hanno i 5 servizi di base ({circa(c15, '%')}); a 5 minuti solo {circa(c5, '%')}.",
         f"Le zone più colpite: {nomi_zd}. Ci abitano {circa_mila(e2['residenti_zone_doppio_svantaggio'])} persone."],
        [graf_classi, graf_servizi],
        [f"Unità: le {nz_usate} zone OMI di Torino con almeno 500 abitanti. Le sezioni si sommano nella zona, pesate per abitanti.",
         "Servizi: punteggio «Tutti i servizi» a piedi in 15 minuti. Fragilità: indice del censimento 2021 (lavoro, istruzione, case, anziani).",
         "Tendenza: retta dei minimi quadrati. Il legame fra fragilità e servizi si controlla a parità di distanza dal centro.",
         f"Doppio svantaggio = fragilità nel 20% più alto e servizi nel 20% più basso. Soglie fissate prima dei numeri, per sezioni: {virgola(se['soglia_fragilita_sopra'])} e {virgola(se['soglia_servizi_fino_a'])}; per zone: {virgola(soglie['fragilita_sopra'])} e {virgola(soglie['servizi_fino_a'])}.",
         "Legami a parità di distanza dal centro: correlazione parziale sui ranghi, con intervallo al 95% per ricampionamento. Regge solo se l'intervallo non contiene lo zero."],
        [["Zone", f"{nz_usate} zone OMI di Torino, almeno 500 abitanti"],
         ["Fragilità alta", f"indice sopra {virgola(se['soglia_fragilita_sopra'])} su 100"],
         ["Servizi bassi", f"punteggio fino a {virgola(se['soglia_servizi_fino_a'])} su 100"],
         ["Legami a parità di distanza", "correlazione parziale sui ranghi, intervallo al 95%; distanza dal centro della zona a Piazza Castello"]],
        ["L'indice di fragilità non è il reddito e non è un indice ufficiale ISTAT: misura lavoro, istruzione, affollamento e anziani.",
         "Si conta se un servizio c'è, non quanto è grande.",
         "Le zone OMI sono grandi: dentro una zona i servizi e la fragilità cambiano molto."],
        None,
        anima={"tipo": "omini", "totale": 10, "colorati": round(10 * se["quota_residenti_di_riferimento"]),
               "didascalia": f"Circa {round(10 * se['quota_residenti_di_riferimento'])} torinese su 10 vive dove l'indice di fragilità sociale è alto e i servizi sono pochi "
                             f"({virgola(100 * se['quota_residenti_di_riferimento'])}% dei residenti delle zone abitate)."},
        )
