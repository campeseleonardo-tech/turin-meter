#!/usr/bin/env python3
"""
05_prepara_sezioni.py - prepara le sezioni di censimento 2021 di Torino e cintura.

Legge  GTT/R01_21.zip  (confini ISTAT del Piemonte, UTM32N) oppure GTT/data/raw/istat/basi_territoriali_2021/R01_21.zip
e scrive  GTT/data/processed/sezioni_torino.json  (poligoni semplificati, famiglie/abitazioni e indicatori ISTAT di occupazione ed eta').
Solo libreria standard di Python. Non scarica niente.
Uso:  python 05_prepara_sezioni.py            (cintura = default, vedi RAGGIO_KM)
"""
import json, math, struct, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
def trova_radice():
    for c in [AQUI, *AQUI.parents]:
        if c.name.lower() == "gtt":
            return c
    d = Path.home() / "Desktop" / "GTT"
    return d if d.is_dir() else AQUI.parent
RADICE = trova_radice()
CAND = [RADICE / "data/raw/istat/basi_territoriali_2021/R01_21.zip", RADICE / "R01_21.zip"]
ZIP = next((c for c in CAND if c.is_file()), None)
if ZIP is None:
    sys.exit("R01_21.zip non trovato in GTT (ne' in data/raw/istat/basi_territoriali_2021)")
OUT = RADICE / "data" / "processed" / "sezioni_torino.json"
INDICATORI = RADICE / "data" / "raw" / "istat" / "altro" / "Dati_regionali_2021" / "R01_indicatori_2021_sezioni.xlsx"

CENTRO = (45.0703, 7.6869)   # Torino, piazza Castello
RAGGIO_KM = 18.0             # cintura: sezioni entro questa distanza dal centro
TOL_M = 4.0                  # semplificazione bordi (metri)
PRO_COM_TORINO = 1272

# --- UTM32N (WGS84) -> lat/lon
A, F = 6378137.0, 1 / 298.257223563
E2 = F * (2 - F); EP2 = E2 / (1 - E2); K0 = 0.9996
def utm_inv(x, y):
    x -= 500000.0
    m = y / K0
    mu = m / (A * (1 - E2/4 - 3*E2**2/64 - 5*E2**3/256))
    e1 = (1 - math.sqrt(1-E2)) / (1 + math.sqrt(1-E2))
    p = (mu + (3*e1/2 - 27*e1**3/32)*math.sin(2*mu) + (21*e1**2/16 - 55*e1**4/32)*math.sin(4*mu)
         + (151*e1**3/96)*math.sin(6*mu) + (1097*e1**4/512)*math.sin(8*mu))
    c1 = EP2*math.cos(p)**2; t1 = math.tan(p)**2
    n1 = A/math.sqrt(1-E2*math.sin(p)**2); r1 = A*(1-E2)/(1-E2*math.sin(p)**2)**1.5
    d = x/(n1*K0)
    lat = p - (n1*math.tan(p)/r1)*(d*d/2 - (5+3*t1+10*c1-4*c1*c1-9*EP2)*d**4/24
          + (61+90*t1+298*c1+45*t1*t1-252*EP2-3*c1*c1)*d**6/720)
    lon = (d - (1+2*t1+c1)*d**3/6 + (5-2*c1+28*t1-3*c1*c1+8*EP2+24*t1*t1)*d**5/120)/math.cos(p)
    return math.degrees(lat), 9.0 + math.degrees(lon)

def km(lat, lon):
    return math.hypot((lat-CENTRO[0])*111.2, (lon-CENTRO[1])*111.2*math.cos(math.radians(CENTRO[0])))

def dp(pts, tol):
    if len(pts) < 4: return pts
    keep = [False]*len(pts); keep[0] = keep[-1] = True
    st = [(0, len(pts)-1)]
    while st:
        a, b = st.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2-x1, y2-y1; L = math.hypot(dx, dy) or 1e-9
        md, mi = 0, None
        for i in range(a+1, b):
            d = abs(dy*(pts[i][0]-x1) - dx*(pts[i][1]-y1))/L
            if d > md: md, mi = d, i
        if mi is not None and md > tol:
            keep[mi] = True; st += [(a, mi), (mi, b)]
    return [p for p, k in zip(pts, keep) if k]

def dp_anello(ring, tol):
    """Semplifica un anello chiuso: lo spezzo nel punto piu' lontano dall'inizio, cosi' la formula funziona."""
    if len(ring) < 6: return ring
    x0, y0 = ring[0]
    m = max(range(1, len(ring)-1), key=lambda i: (ring[i][0]-x0)**2 + (ring[i][1]-y0)**2)
    return dp(ring[:m+1], tol)[:-1] + dp(ring[m:], tol)

def leggi_dbf(b):
    n, hl, rl = struct.unpack("<IHH", b[4:12])
    campi, i = [], 32
    while b[i] != 0x0D:
        campi.append((b[i:i+11].split(b"\0")[0].decode(), b[i+16])); i += 32
    righe = []
    for r in range(n):
        rec = b[hl + r*rl: hl + (r+1)*rl]; o = 1; d = {}
        for nome, ln in campi:
            d[nome] = rec[o:o+ln].decode("latin-1").strip(); o += ln
        righe.append(d)
    return righe

def colonna_excel(rif):
    n = 0
    for c in rif:
        if c.isalpha(): n = n * 26 + ord(c.upper()) - ord("A") + 1
        else: break
    return n

def leggi_indicatori(sezioni):
    """Unisce i tre indicatori di mobilita' potenziale ISTAT per codice sezione."""
    if not INDICATORI.is_file():
        sys.exit(f"File ISTAT non trovato: {INDICATORI}")
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    richiesti = {"SEZ21_ID", "P101", "P15", "P16", *[f"P{i}" for i in range(17, 27)],
                 "P14", "P27", "P28", "P29",
                 # famiglie per numero di componenti (PF1 totale, PF3 = una sola persona)
                 "PF1", "PF3",
                 # titoli di studio (pop 9+): tracciato R01 2021
                 "P83", "P86", "P87", "P88", "P89", "P90"}
    target = {str(s["id"]): s for s in sezioni if s["p"] > 0}
    agganciati = {}
    with zipfile.ZipFile(INDICATORI) as z:
        nomi = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in nomi:
            radice = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.findall(".//m:t", ns))
                      for si in radice.findall("m:si", ns)]

        def valore(c):
            v = c.find("m:v", ns)
            if c.attrib.get("t") == "inlineStr":
                return "".join(t.text or "" for t in c.findall(".//m:t", ns))
            if v is None: return None
            return shared[int(v.text)] if c.attrib.get("t") == "s" else v.text

        intestazioni = None
        indici = {}
        percorso = "xl/worksheets/sheet1.xml"
        with z.open(percorso) as f:
            for _, riga in ET.iterparse(f, events=("end",)):
                if not riga.tag.endswith("}row"):
                    continue
                celle = riga.findall("m:c", ns)
                if intestazioni is None:
                    intestazioni = {str(valore(c)).strip(): colonna_excel(c.attrib["r"])
                                    for c in celle if valore(c) is not None}
                    mancanti = richiesti - set(intestazioni)
                    if mancanti:
                        raise ValueError(f"Colonne ISTAT mancanti: {sorted(mancanti)}")
                    indici = {intestazioni[k]: k for k in richiesti}
                else:
                    dati = {}
                    for c in celle:
                        idx = colonna_excel(c.attrib["r"])
                        nome = indici.get(idx)
                        if nome is not None:
                            dati[nome] = valore(c)
                    raw_id = dati.get("SEZ21_ID")
                    if raw_id:
                        sid = str(int(float(raw_id)))
                        if sid in target:
                            if sid in agganciati:
                                raise ValueError(f"Codice sezione duplicato nel file ISTAT: {sid}")
                            agganciati[sid] = dati
                riga.clear()

    assenti = set(target) - set(agganciati)
    quota = len(assenti) / max(len(target), 1)
    print(f"  Indicatori R01: {len(agganciati)}/{len(target)} sezioni abitate agganciate; "
          f"mancanti {len(assenti)} ({quota:.2%})")
    if quota > 0.02:
        raise ValueError(f"Merge indicatori R01 oltre tolleranza 2%: {len(assenti)} sezioni mancanti")

    def numero(dati, nome, sid):
        raw = dati.get(nome)
        if raw is None or str(raw).strip() == "":
            raise ValueError(f"Valore {nome} mancante per la sezione {sid}")
        n = int(float(raw))
        if n < 0:
            raise ValueError(f"Valore {nome} negativo per la sezione {sid}: {n}")
        return n

    for sid, dati in agganciati.items():
        popolazione_lavorativa = sum(numero(dati, f"P{i}", sid) for i in range(17, 27))
        occupati = numero(dati, "P101", sid)
        if occupati > popolazione_lavorativa:
            raise ValueError(f"Occupati superiori ai residenti 15-64 anni nella sezione {sid}")
        ist9 = numero(dati, "P83", sid)
        pezzi_ist = [numero(dati, f"P{i}", sid) for i in (86, 87, 88, 89, 90)]
        if ist9 > 0 and sum(pezzi_ist) != ist9:
            print(f"  [NOTA] sezione {sid}: titoli di studio {sum(pezzi_ist)} != pop 9+ {ist9}")
        classi = [numero(dati, f"P{i}", sid) for i in range(14, 30)]   # P14 <5 anni ... P29 oltre 74 anni
        centri = [2.5, 7.5, 12.5, 17.5, 22.5, 27.5, 32.5, 37.5, 42.5, 47.5, 52.5, 57.5, 62.5, 67.5, 72.5, 80.0]   # centro di ogni classe; 80 per «oltre 74» (stima)
        tot_cl = sum(classi)
        target[sid].update({
            # bambini e ragazzi 0-14 (P14-P16) e eta' media stimata dai centri delle classi (mai la nazionalita')
            "p014": sum(classi[:3]),
            "em": round(sum(c * n for c, n in zip(centri, classi)) / tot_cl, 1) if tot_cl else None,
            # famiglie: totale e con un solo componente
            "pf1": numero(dati, "PF1", sid), "pf3": numero(dati, "PF3", sid),
            "occ": occupati,
            "p1564": popolazione_lavorativa,
            "sc": numero(dati, "P15", sid) + numero(dati, "P16", sid),
            "sen": sum(numero(dati, f"P{i}", sid) for i in (27, 28, 29)),
            # istruzione (pop 9+): senza titolo, elementare, media, superiore, terziaria
            "ist9": ist9, "i0": pezzi_ist[0], "iel": pezzi_ist[1],
            "im": pezzi_ist[2], "isu": pezzi_ist[3], "it": pezzi_ist[4],
        })

    for nome, pred in (("Torino", lambda s: s["c"] == PRO_COM_TORINO), ("area", lambda s: True)):
        gruppo = [s for s in target.values() if pred(s)]
        occ = sum(s["occ"] for s in gruppo)
        p1564 = sum(s["p1564"] for s in gruppo)
        print(f"  {nome}: occupati 15-64 {occ}, residenti 15-64 {p1564}, "
              f"quota occupati {100*occ/p1564:.1f}% se il denominatore e' positivo; "
              f"residenti 5-14 {sum(s['sc'] for s in gruppo)}, residenti 65+ {sum(s['sen'] for s in gruppo)}")
        print(f"         0-14 anni {sum(s['p014'] for s in gruppo)}, famiglie {sum(s['pf1'] for s in gruppo)} di cui di una persona {sum(s['pf3'] for s in gruppo)}, "
              f"eta' media stimata (pesata) {sum(s['em']*s['p'] for s in gruppo if s['em'] is not None)/max(1,sum(s['p'] for s in gruppo if s['em'] is not None)):.1f}")
        ist9 = sum(s["ist9"] for s in gruppo)
        bassa = sum(s["i0"] + s["iel"] for s in gruppo)
        if ist9:
            print(f"         pop 9+ {ist9}, senza titolo o solo elementare {bassa} ({100*bassa/ist9:.1f}%)")
        else:
            print("         pop 9+ 0")

def poligoni(b, k):
    """k-esimo record .shp -> lista di anelli [(x,y)]. Usa l'indice .shx fornito esternamente."""
    pass

def main():
    z = zipfile.ZipFile(ZIP)
    shp = z.read("SHP/R01_21_WGS84.shp"); shx = z.read("SHP/R01_21_WGS84.shx"); dbf = z.read("SHP/R01_21_WGS84.dbf")
    righe = leggi_dbf(dbf)
    n = (len(shx) - 100)//8
    assert n == len(righe), (n, len(righe))
    out, saltate = [], 0
    for k in range(n):
        off = struct.unpack(">i", shx[100+8*k:104+8*k])[0]*2
        tipo = struct.unpack("<i", shp[off+8:off+12])[0]
        if tipo == 0: continue
        xmin, ymin, xmax, ymax = struct.unpack("<4d", shp[off+12:off+44])
        la, lo = utm_inv((xmin+xmax)/2, (ymin+ymax)/2)
        r = righe[k]
        if km(la, lo) > RAGGIO_KM and int(r["PRO_COM"] or 0) != PRO_COM_TORINO:
            saltate += 1; continue
        npart, npt = struct.unpack("<2i", shp[off+44:off+52])
        parti = list(struct.unpack(f"<{npart}i", shp[off+52:off+52+4*npart])) + [npt]
        p0 = off+52+4*npart
        pts = struct.unpack(f"<{2*npt}d", shp[p0:p0+16*npt])
        anelli = []
        for a, b in zip(parti, parti[1:]):
            ring = [(pts[2*i], pts[2*i+1]) for i in range(a, b)]
            ring = dp_anello(ring, TOL_M)
            if len(ring) < 4: continue
            anelli.append([[round(c, 5) for c in utm_inv(x, y)] for x, y in ring])
        if not anelli: continue
        # area in km2 (formula dei lacci sull'anello esterno, UTM) 
        ex = [(pts[2*i], pts[2*i+1]) for i in range(parti[0], parti[1])]
        ar = abs(sum(ex[i][0]*ex[i+1][1]-ex[i+1][0]*ex[i][1] for i in range(len(ex)-1)))/2/1e6
        out.append({"id": r["SEZ21_ID"], "c": int(r["PRO_COM"]), "p": int(r["POP21"] or 0), "a": round(ar, 5),
                    "t": int(r["COD_TIPO_S"] or 0), "f": int(r["FAM21"] or 0), "ab": int(r["ABI21"] or 0), "g": anelli})
    leggi_indicatori(out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    tor = [s for s in out if s["c"] == PRO_COM_TORINO]
    print(f"Sezioni salvate: {len(out)} (Torino {len(tor)}, abitanti Torino {sum(s['p'] for s in tor)}); fuori area: {saltate}")
    print(f"Abitanti totali nell'area: {sum(s['p'] for s in out)}; file {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")
main()
