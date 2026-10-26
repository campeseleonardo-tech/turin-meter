"""Dati della home (data/home_mezzi.js): contorno di Torino, mezzi di un'ora tipica che si muovono e contatore della raccolta.

Tutto viene da file gia' prodotti: assets/torino_contorno.json (scripts/costruisci_contorno_torino.py), data/storico_riassunti/ora_tipica.json
(script 97), i meta dei giorni in data/storico_riassunti/passaggi_*.zip e le classi bus/tram/metro di data/processed/risultato4_regolarita.json.
Nessun numero e' scritto a mano."""
import json
import re
import zipfile
from datetime import date

from schede.comune import PROC, RADICE

RIASSUNTI = RADICE / "data" / "storico_riassunti"
OUT = RADICE / "data" / "home_mezzi.js"
CODICE_MODO = {"bus": 0, "tram": 1, "metro": 2}


def nome_base(linea):
    """Il feed scrive «16CDU», il GTFS «16 CD»: senza spazi e senza la U finale dei bus urbani i due nomi coincidono."""
    return re.sub(r"U$", "", linea.replace(" ", "")).upper()


def modi_per_linea():
    j = json.loads((PROC / "risultato4_regolarita.json").read_text(encoding="utf-8"))
    return {nome_base(n): m for n, m in j["modo_linea"].items()}


INIZIO_RACCOLTA = "2026-10-03"   # primo giorno della raccolta sul Raspberry Pi (mezzi GTT); la home conta i giorni da qui a oggi


def contatore():
    """Giorni con dati dei mezzi (dal primo all'ultimo) e passaggi alle fermate misurati con il GPS (uno ogni 4 byte di gps_trip.bin)."""
    giorni, passaggi = set(), 0
    for f in sorted(RIASSUNTI.glob("passaggi_*.zip")):
        with zipfile.ZipFile(f) as z:
            for n in z.namelist():
                if n.endswith("/gps_trip.bin"):
                    giorni.add(n.split("/")[0])
                    passaggi += z.getinfo(n).file_size // 4
    if not giorni:
        return None
    d = sorted(giorni)
    d0, d1 = date(int(d[0][:4]), int(d[0][4:6]), int(d[0][6:])), date(int(d[-1][:4]), int(d[-1][4:6]), int(d[-1][6:]))
    return {"giorni": (d1 - d0).days + 1, "giorni_con_dati": len(d), "passaggi": passaggi, "dal": d0.isoformat(), "al": d1.isoformat(),
            "inizio_raccolta": INIZIO_RACCOLTA}


GAP_PASSI = 12          # buchi fino a 12 passi (6 minuti) si uniscono con una linea retta
METRI_PER_PASSO = 450   # velocita' massima credibile fra due posizioni da unire (30 secondi a 54 km/h)


def distanza_m(a, b):
    """Metri fra due punti in interi da 1e-5 gradi (Torino: 1 grado di latitudine = 111 km, di longitudine = 78 km)."""
    return (((a[0] - b[0]) * 1.11) ** 2 + ((a[1] - b[1]) * 0.78) ** 2) ** 0.5


def decodifica(p):
    pts, lat, lon = [(p[0], p[1])], p[0], p[1]
    for i in range(1, len(p) // 2):
        lat += p[2 * i]
        lon += p[2 * i + 1]
        pts.append((lat, lon))
    return pts


def codifica(pts):
    p = [pts[0][0], pts[0][1]]
    for (a, b), (c, d) in zip(pts, pts[1:]):
        p += [c - a, d - b]
    return p


def unisci_buchi(voci):
    """Le posizioni del GPS arrivano a ondate (il feed a volte non si aggiorna per qualche minuto: tutti i mezzi spariscono insieme).
    Un tratto che finisce e un altro della STESSA linea che comincia entro 6 minuti, abbastanza vicino da essere lo stesso mezzo
    (sceglie il piu' vicino, ogni tratto una volta sola), si uniscono con una linea retta. Ritorna (voci, unioni fatte)."""
    per_linea = {}
    for v in voci:
        per_linea.setdefault(v["linea"], []).append(v)
    fatte = 0
    for lista in per_linea.values():
        usati = set()
        cambiato = True
        while cambiato:
            cambiato = False
            lista.sort(key=lambda v: v["t"] + len(v["pts"]) - 1)
            for a in lista:
                if id(a) in usati or a.get("morto"):
                    continue
                fine = a["t"] + len(a["pts"]) - 1
                migliore, dmin = None, None
                for b in lista:
                    if b is a or b.get("morto") or not (fine < b["t"] <= fine + GAP_PASSI):
                        continue
                    d = distanza_m(a["pts"][-1], b["pts"][0])
                    if d <= METRI_PER_PASSO * (b["t"] - fine) and (dmin is None or d < dmin):
                        migliore, dmin = b, d
                if migliore is None:
                    continue
                b, n = migliore, migliore["t"] - fine - 1
                (la, oa), (lb, ob) = a["pts"][-1], b["pts"][0]
                a["pts"] += [(round(la + (lb - la) * (k + 1) / (n + 1)), round(oa + (ob - oa) * (k + 1) / (n + 1))) for k in range(n)] + b["pts"]
                b["morto"] = True
                fatte += 1
                cambiato = True
    return [v for lista in per_linea.values() for v in lista if not v.get("morto")], fatte


def passi_utili(voci, passi):
    """Primo e ultimo passo con almeno il 25% dei mezzi che si vedono al massimo: fuori da li' il GPS non ha dati e l'animazione resterebbe vuota."""
    att = [0] * passi
    for v in voci:
        for i in range(len(v["pts"])):
            if 0 <= v["t"] + i < passi:
                att[v["t"] + i] += 1
    soglia = 0.25 * max(att)
    buoni = [i for i, x in enumerate(att) if x >= soglia]
    return (buoni[0], buoni[-1]), att


def scrivi_home():
    cont = json.loads((RADICE / "assets" / "torino_contorno.json").read_text(encoding="utf-8"))
    ot = json.loads((RIASSUNTI / "ora_tipica.json").read_text(encoding="utf-8"))
    modi = modi_per_linea()
    voci, senza_modo = [], 0
    for m in ot["mezzi"]:
        modo = modi.get(nome_base(m["l"]))
        if modo is None:
            senza_modo += 1
            modo = "bus"
        voci.append({"linea": nome_base(m["l"]), "modo": modo, "t": m["t"], "pts": decodifica(m["p"])})
    voci, unioni = unisci_buchi(voci)
    (da, a), att = passi_utili(voci, ot["passi"])
    mezzi = [[CODICE_MODO[v["modo"]], v["t"], codifica(v["pts"])] for v in sorted(voci, key=lambda v: (v["t"], v["linea"]))]
    quanti = {k: sum(1 for x in mezzi if x[0] == c) for k, c in CODICE_MODO.items()}
    dati = {"contorno": cont,
            "ora_tipica": {"giorno": ot["giorno"], "inizio": ot["inizio"], "passo_s": ot["passo_s"], "passi": ot["passi"], "da": da, "a": a, "mezzi": mezzi, "quanti": quanti},
            "contatore": contatore()}
    OUT.write_text("window.HOME_MEZZI = " + json.dumps(dati, separators=(",", ":")) + ";\n", encoding="utf-8")
    kb = OUT.stat().st_size // 1024
    print(f"home_mezzi.js: {len(mezzi)} mezzi ({quanti['bus']} bus, {quanti['tram']} tram, {quanti['metro']} metro; {senza_modo} linee senza classe contate come bus), "
          f"{unioni} buchi uniti; animazione dal passo {da} al {a} su {ot['passi']} (attivi: min {min(att[da:a + 1])}, max {max(att)}); contatore {dati['contatore']}, {kb} KB")
    if a - da < 0.5 * (ot["passi"] - 1):
        print(f"AVVISO: il GPS copre solo {(a - da) * ot['passo_s'] // 60} minuti dell'ora tipica ({ot['giorno']}): rifai l'ora tipica con lo script 97 (sceglie il giorno con piu' copertura)")
    if kb > 300:
        print(f"AVVISO: data/home_mezzi.js pesa {kb} KB (limite scelto: 300 KB)")
