#!/usr/bin/env python3
"""
prova_riassunti.py  -  prova che i riassunti dello storico (script 97) danno gli STESSI numeri dello storico, per gli script 27, 70, 26 e 71.

Crea uno storico finto (scripts/prove/storico_finto.py) in una cartella temporanea, lo riassume con lo script 97, poi lancia ogni script due volte:
  A) leggendo lo storico SQLite;  B) con lo storico NASCOSTO, quindi dai riassunti.
Confronta i JSON (senza i campi «generato») e i rapporti (senza le righe che nominano la sorgente). Tolleranza sui numeri: 0,011
(i riassunti salvano gli istanti GPS al millisecondo: l'ultima cifra arrotondata puo' cambiare in casi limite).

Uso: python scripts/prove/prova_riassunti.py        Codice di uscita 0 = tutto uguale.
"""
import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SCRIPTS = AQUI.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(AQUI))
import comuni  # noqa: E402
import riassunti_storico as rs  # noqa: E402
import storico_finto  # noqa: E402

TOLLERANZA = 0.011


class Testo(io.StringIO):
    def reconfigure(self, **kw):      # gli script chiamano sys.stdout.reconfigure(...)
        pass


def lancia(modulo, argv):
    vecchio = sys.argv
    sys.argv = [modulo.__name__] + argv
    try:
        with contextlib.redirect_stdout(Testo()) as out, contextlib.redirect_stderr(Testo()) as err:
            r = modulo.main()
    finally:
        sys.argv = vecchio
    return r, out.getvalue(), err.getvalue()


def esito(c, nome, rc, file, testo):
    ok = rc in (None, 0) and file.exists()
    c(nome, ok, bloccante=True, dettaglio="" if ok else testo[-400:])


def senza_generato(o):
    if isinstance(o, dict):
        return {k: senza_generato(v) for k, v in o.items() if k not in ("generato", "periodo_generato")}
    if isinstance(o, list):
        return [senza_generato(x) for x in o]
    return o


def confronta(a, b, percorso, diff, massimo):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                diff.append(f"{percorso}/{k}: presente solo da una parte")
            else:
                confronta(a[k], b[k], f"{percorso}/{k}", diff, massimo)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diff.append(f"{percorso}: lunghezza {len(a)} contro {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            confronta(x, y, f"{percorso}[{i}]", diff, massimo)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        d = abs(a - b)
        if d > massimo[0]:
            massimo[0] = d
        if d > TOLLERANZA:
            diff.append(f"{percorso}: {a} contro {b}")
    elif a != b:
        diff.append(f"{percorso}: {a!r} contro {b!r}")


def righe_rapporto(testo):
    return [r for r in testo.splitlines() if not re.search(r"sorgente|Sorgente|DB \(sola lettura\)", r)]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    c = comuni.Controlli()
    tmp = Path(tempfile.mkdtemp(prefix="prova_riassunti_"))
    finto = storico_finto.crea(tmp)
    cart = tmp / "storico_riassunti"
    print(f"cartella di prova: {tmp}")
    r = subprocess.run([sys.executable, str(SCRIPTS / "97_riassunti_storico.py"), "--db", str(finto["db"]), "--gtfs", str(finto["gtfs"]),
                        "--riassunti-in", str(cart)], capture_output=True, text=True, encoding="utf-8")
    c("script 97 su storico finto: nessun errore", r.returncode == 0, bloccante=True, dettaglio=r.stderr[-300:])
    rs.CARTELLA = cart
    nascosto = tmp / "data" / "NON_C_E.sqlite"

    # ---- script 27 e 70 (il 70 legge il JSON del 27: ognuno col suo)
    esiti = {}
    for nome, dove in (("A", finto["db"]), ("B", nascosto)):
        out = tmp / f"out_{nome}"
        out.mkdir()
        m27 = comuni.carica_script("27_risultato4_regolarita.py")
        m27.DB, m27.GTFS = dove, finto["gtfs"]
        m27.OUT_JSON, m27.OUT_RAPPORTO, m27.POPOLARITA = out / "r4.json", out / "r4.txt", out / "nessuna.json"
        rc, o, e = lancia(m27, [])
        esito(c, f"27 [{nome}] gira", rc, m27.OUT_JSON, o + e)
        c(f"27 [{nome}] sorgente: " + ("storico" if nome == "A" else "riassunti"), ("storico SQLite" if nome == "A" else "riassunti") in e)
        m70 = comuni.carica_script("70_risultato9_attesa.py")
        m70.r4.DB, m70.r4.GTFS = dove, finto["gtfs"]
        m70.OUT_JSON, m70.OUT_RAPPORTO, m70.IN_R4 = out / "r9.json", out / "r9.txt", out / "r4.json"
        rc, o, e = lancia(m70, [])
        esito(c, f"70 [{nome}] gira", rc, m70.OUT_JSON, o + e)
        # ---- 26 e 71
        m26 = comuni.carica_script("26_velocita_5t.py")
        m26.DB, m26.OUT, m26.RAPPORTO = dove, out / "v5t.json", out / "v5t.txt"
        rc, o, e = lancia(m26, [])
        esito(c, f"26 [{nome}] gira", rc, m26.OUT, o + e)
        m71 = comuni.carica_script("71_parcheggi_riempimento.py")
        m71.DB, m71.OUT, m71.RAPPORTO = dove, out / "riemp.json", out / "riemp.txt"
        rc, o, e = lancia(m71, [])
        esito(c, f"71 [{nome}] gira", rc, m71.OUT, o + e)
        esiti[nome] = out

    for nome_f, tipo in (("r4.json", "json"), ("r9.json", "json"), ("v5t.json", "json"), ("riemp.json", "json"),
                         ("r4.txt", "txt"), ("r9.txt", "txt"), ("v5t.txt", "txt"), ("riemp.txt", "txt")):
        a, b = esiti["A"] / nome_f, esiti["B"] / nome_f
        if tipo == "json":
            ja, jb = senza_generato(json.loads(a.read_text(encoding="utf-8"))), senza_generato(json.loads(b.read_text(encoding="utf-8")))
            diff, massimo = [], [0.0]
            confronta(ja, jb, "", diff, massimo)
            c(f"{nome_f}: storico = riassunti (differenza massima {massimo[0]:.6f})", not diff, dettaglio="; ".join(diff[:3]))
        else:
            la, lb = righe_rapporto(a.read_text(encoding="utf-8")), righe_rapporto(b.read_text(encoding="utf-8"))
            diffs = [(x, y) for x, y in zip(la, lb) if x != y]
            c(f"{nome_f}: stesse righe ({len(la)} contro {len(lb)})", len(la) == len(lb) and not diffs,
              dettaglio=" | ".join(f"«{x[:50]}» ≠ «{y[:50]}»" for x, y in diffs[:2]))
    print(f"\navvisi: {len(c.avvisi())}")
    return 0 if not c.avvisi() else 1


if __name__ == "__main__":
    sys.exit(main())
