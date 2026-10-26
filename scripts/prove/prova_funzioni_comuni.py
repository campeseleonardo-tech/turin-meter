#!/usr/bin/env python3
"""Prova delle funzioni che gli script 24, 25 e 29 prendevano da copie proprie e ora importano da scripts/comuni.py (giro C13, gruppo 21-29).

Le copie vecchie sono scritte qui sotto com'erano (riferimento): su migliaia di valori casuali, e sui casi limite (liste vuote, un solo valore, valori uguali),
il risultato nuovo deve essere identico al bit. Controlla anche che 24, 25 e 29 usino davvero le funzioni di comuni.py.
Uso: python scripts/prove/prova_funzioni_comuni.py        Codice di uscita 0 = tutto uguale."""
import math
import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402


def importa_da_comuni(testo, cerca):
    """True se una riga «from comuni import ...» elenca tutti i nomi di `cerca` (in qualunque ordine, con altri nomi accanto)."""
    voluti = {x.strip() for x in cerca.split("import", 1)[1].split(",")}
    for r in testo.splitlines():
        if r.startswith("from comuni import"):
            nomi = {x.split(" as ")[0].strip() for x in r.split("import", 1)[1].split("#")[0].split(",")}   # «x as y»: conta x
            if voluti <= nomi:
                return True
    return False


def haversine_vecchia(lat1, lon1, lat2, lon2):               # copia che stava negli script 24 e 25
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def percentile_rank_vecchia(valori):                          # copia che stava nello script 25
    chiavi = list(valori.keys())
    ordinati = sorted(chiavi, key=lambda k: valori[k])
    n = len(ordinati)
    if n <= 1:
        return {k: 100.0 for k in chiavi}
    rank = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and valori[ordinati[j + 1]] == valori[ordinati[i]]:
            j += 1
        for k in ordinati[i:j + 1]:
            rank[k] = (i + j) / 2
        i = j + 1
    return {k: 100.0 * rank[k] / (n - 1) for k in chiavi}


def percentile_vecchia(valori_ordinati, p):                   # copia che stava nello script 29
    n = len(valori_ordinati)
    if n == 0:
        return None
    idx = max(0, min(n - 1, round(p / 100 * (n - 1))))
    return valori_ordinati[idx]


def main():
    rnd = random.Random(2610)
    errori = []
    for _ in range(5000):
        a = (rnd.uniform(44.9, 45.3), rnd.uniform(7.4, 7.9), rnd.uniform(44.9, 45.3), rnd.uniform(7.4, 7.9))
        if comuni.haversine_m(*a) != haversine_vecchia(*a):
            errori.append(f"haversine diversa su {a}")
            break
    print("  distanze: 5000 coppie di punti uguali" if not errori else "  distanze: DIVERSE")
    n0 = len(errori)
    for n in (0, 1, 2, 5, 40, 300):
        for _ in range(40):
            v = {f"k{i}": rnd.choice([rnd.randint(0, 6), rnd.random() * 100]) for i in range(n)}   # con molti valori uguali
            if comuni.percentile_rank(v) != percentile_rank_vecchia(v):
                errori.append(f"percentile_rank diverso con n={n}")
                break
    print("  percentili per posizione: uguali (anche con valori ripetuti, 0 e 1 valori)" if len(errori) == n0 else "  percentili per posizione: DIVERSI")
    n0 = len(errori)
    for n in (0, 1, 2, 7, 100, 1001):
        for p in (0, 1, 10, 50, 90, 99, 100):
            for _ in range(20):
                v = sorted(rnd.random() * 50 - 10 for _ in range(n))
                if comuni.soglia_quantile(v, p) != percentile_vecchia(v, p):
                    errori.append(f"soglia_quantile diversa con n={n}, p={p}")
                    break
    print("  quantili (script 29): uguali" if len(errori) == n0 else "  quantili (script 29): DIVERSI")
    # gli script usano davvero comuni.py (nessuna copia rimasta)
    for nome, cerca in (("24_importanza_vie.py", "from comuni import haversine_m"), ("25_risultato6_interscambio.py", "from comuni import haversine_m, percentile_rank"),
                        ("29_risultato2_metro_notte.py", "from comuni import soglia_quantile")):
        if not (AQUI / nome).exists():      # gli script esplorativi (28-32) non sono nel repository pubblico
            continue
        testo = (AQUI / nome).read_text(encoding="utf-8")
        if not importa_da_comuni(testo, cerca):
            errori.append(f"{nome}: non importa piu' da comuni.py")
        for copia in ("def haversine_m(", "def percentile_rank(", "def percentile("):
            if copia in testo:
                errori.append(f"{nome}: ha ancora una copia ({copia})")
    print("  script 24, 25, 29: importano da comuni.py, nessuna copia rimasta" if not any("copia" in e or "importa" in e for e in errori) else "  script 24, 25, 29: PROBLEMA")
    # gruppi 33-95: distanze (37, 72, 73) e ora legale (71 non la usava piu': copia morta tolta)
    for nome, cerca in (("37_traffico_AB.py", "from comuni import haversine_m"), ("72_nodi_tp.py", "from comuni import haversine_m"), ("73_segnali_criticita.py", "from comuni import haversine_m")):
        testo = (AQUI / nome).read_text(encoding="utf-8")
        if not importa_da_comuni(testo, cerca):
            errori.append(f"{nome}: non importa piu' da comuni.py")
        if "def haversine_m(" in testo or "def hav(" in testo or "R = 6371000" in testo:
            errori.append(f"{nome}: ha ancora una copia della distanza")
    if "def ora_locale(" in (AQUI / "71_parcheggi_riempimento.py").read_text(encoding="utf-8"):
        errori.append("71: ha ancora una copia di ora_locale")
    print("  script 37, 71, 72, 73: nessuna copia rimasta" if not any("copia" in e for e in errori) else "  script 37, 71, 72, 73: PROBLEMA")
    if errori:
        print("ERRORI:\n  " + "\n  ".join(errori))
        return 1
    print("OK: tutte le funzioni sono identiche a quelle di prima")
    return 0


if __name__ == "__main__":
    sys.exit(main())
