#!/usr/bin/env python3
"""
controlla_leopi.py  -  la raccolta sul Raspberry Pi (leopi) sta funzionando? (Claude, 20/10/2026)

Cosa fa
-------
Si collega a leopi con SSH (chiave indicata in config_locale.json) SOLO PER LEGGERE: apre il database
storico.sqlite del Pi in sola lettura e guarda l'ultima riga scritta in ogni tabella raccolta.
  OK       = ogni tabella ha una lettura recente (vedi LIMITI_MINUTI);
  ALLARME  = almeno una tabella e' ferma (scrive quale e da quando).
Di notte (00-06 ora italiana) il feed dei ritardi GTT e' spento: per quella tabella non c'e' allarme.
La ZTL NON da' allarme: il raccoglitore la controlla una volta al giorno e la salva solo se cambia (il dato e'
fermo dal 2024), quindi per settimane non compare nessuna riga nuova. Si stampa solo la data dell'ultima versione.
Si stampano anche gli errori scritti dal raccoglitore nelle ultime 24 ore (tabella errori), solo come informazione.
(20/10, sera: tolto il falso allarme sulla ZTL trovato nel primo giro.)
Dal 23/10 (L4) anche: spazio libero sul Pi, /tmp (dove si fa lo snapshot della copia), peso e crescita dello storico,
archivio del GTFS con i giorni alla scadenza, feed degli avvisi GTT. Le soglie sono costanti qui sotto (fissate prima di
vedere i numeri): ALLARME cambia il codice di uscita e fa uscire la finestra di Windows; AVVISO sta solo nel testo e nel registro.
Scrive anche una riga in logs\\controlla_leopi.log. Non modifica niente sul Pi.

Come si lancia
--------------
  doppio clic su scripts\\CONTROLLA_LEOPI.bat     (oppure: python scripts\\controlla_leopi.py)
  Codice di uscita: 0 = OK (anche con AVVISI), 1 = ALLARME, 2 = Pi non raggiungibile.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comuni  # noqa: E402
import config_locale  # noqa: E402

CFG = config_locale.carica()  # config_locale.json nella radice (non in git)
PI = CFG["pi"]
CHIAVE = Path(CFG["chiave"])
DB_PI = CFG["dir_remota"] + "/data/storico.sqlite"
# tabella -> (colonna del tempo, minuti oltre i quali e' ferma)
LIMITI_MINUTI = {
    "mezzi_gtt": ("letto_utc", 30),
    "trip_update_gtt": ("letto_utc", 30),
    "flussi_5t": ("generato_utc", 30),
    "occupazione_pk": ("generato_utc", 30),
}
LOG = comuni.RADICE / "logs" / "controlla_leopi.log"
STATO = comuni.RADICE / "logs" / "controlla_leopi_stato.json"  # peso dello storico al lancio precedente

# Soglie (L4, 23/10/2026): non cambiarle dopo aver visto i numeri.
GB = 1024 ** 3
SPAZIO_ALLARME_GB = 5     # spazio libero sul Pi sotto questo: ALLARME
SPAZIO_AVVISO_GB = 10     # sotto questo: AVVISO
STORICO_AVVISO_GB = 8     # storico piu' grande di questo: AVVISO
TMP_VOLTE_STORICO = 1.5   # cartella data/tmp_copia (lo snapshot sta li', L4b) con meno di 1,5 volte lo storico: ALLARME
GTFS_ALLARME_GIORNI = 14  # GTFS a 14 giorni o meno dalla scadenza: ALLARME
GTFS_AVVISO_GIORNI = 45   # a 45 giorni o meno: AVVISO
GTFS_TENTATIVI_FALLITI_GIORNI = 3  # un errore GTFS in ognuno degli ultimi 3 giorni: AVVISO
ORE_AVVISI_IN_ERRORE = 24  # errore in ognuna delle ultime 24 ore e nessuna riga nuova: AVVISO
CRESCITA_MIN_ORE = 6       # la crescita si calcola solo se il lancio precedente e' piu' vecchio di cosi'
FONTE_AVVISI = "alerts"    # nome usato da scripts/12_ritardi_gtt.py nella tabella errori

CODICE_PI = (
    "import sqlite3,json;"
    f"c=sqlite3.connect('file:{DB_PI}?mode=ro',uri=True);r={{}}\n"
    f"for t,col in {json.dumps({k: v[0] for k, v in LIMITI_MINUTI.items()})}.items():\n"
    "  try:\n"
    "    x=c.execute(f'SELECT {col} FROM {t} ORDER BY rowid DESC LIMIT 1').fetchone();r[t]=x[0] if x else None\n"
    "  except Exception as e:\n"
    "    r[t]='errore: '+str(e)\n"
    "x=c.execute('SELECT max(scaricato_utc) FROM ztl_5t').fetchone();r['_ztl']=x[0] if x else None\n"
    "import datetime as D,os\n"
    "n=D.datetime.now(D.timezone.utc)\n"
    "da=(n-D.timedelta(hours=24)).isoformat(timespec='seconds')\n"
    "try:\n"
    "  r['_errori']=[list(y) for y in c.execute('SELECT fonte,count(*),max(quando_utc) FROM errori WHERE quando_utc>=? GROUP BY fonte',(da,))]\n"
    "except Exception as e:\n"
    "  r['_errori']='errore: '+str(e)\n"
    # L4: spazio, /tmp, peso, GTFS, errori per fonte
    f"d=os.path.dirname('{DB_PI}')\n"
    "v=os.statvfs(d);r['_libero']=v.f_bavail*v.f_frsize\n"
    "v=os.statvfs('/tmp');r['_tmp_libero']=v.f_bavail*v.f_frsize\n"
    "k=d+'/tmp_copia'\n"
    "v=os.statvfs(k if os.path.isdir(k) else d);r['_copia_libero']=v.f_bavail*v.f_frsize\n"
    "r['_tmp_tipo']=''\n"
    "for l in open('/proc/mounts'):\n"
    "  q=l.split()\n"
    "  if len(q)>2 and q[1]=='/tmp': r['_tmp_tipo']=q[2]\n"
    f"r['_peso']=os.path.getsize('{DB_PI}')\n"
    "try:\n"
    "  x=c.execute('SELECT scaricato_utc,file,valido_da,valido_a FROM gtfs_versioni ORDER BY scaricato_utc DESC, rowid DESC LIMIT 1').fetchone()\n"
    "  r['_gtfs']=list(x) if x else None\n"
    "except Exception as e:\n"
    "  r['_gtfs']='tabella assente' if 'no such table' in str(e) else 'errore: '+str(e)\n"
    "def giorni(fonte,passo,quanti):\n"
    "  t=[y[0] for y in c.execute('SELECT quando_utc FROM errori WHERE fonte=? AND quando_utc>=?',(fonte,(n-D.timedelta(seconds=passo*quanti)).isoformat(timespec='seconds')))]\n"
    "  b=set()\n"
    "  for u in t:\n"
    "    d=D.datetime.fromisoformat(u.replace('Z','+00:00'))\n"
    "    if d.tzinfo is None: d=d.replace(tzinfo=D.timezone.utc)\n"
    "    b.add(int((n-d).total_seconds()//passo))\n"
    "  return len(b)\n"
    "def ultimo(fonte):\n"
    "  x=c.execute('SELECT quando_utc,messaggio FROM errori WHERE fonte=? ORDER BY rowid DESC LIMIT 1',(fonte,)).fetchone()\n"
    "  return list(x) if x else None\n"
    "try:\n"
    f"  r['_gtfs_err_giorni']=giorni('GTFS',86400,{GTFS_TENTATIVI_FALLITI_GIORNI});r['_gtfs_err']=ultimo('GTFS')\n"
    f"  r['_avvisi_err_ore']=giorni('{FONTE_AVVISI}',3600,{ORE_AVVISI_IN_ERRORE});r['_avvisi_err']=ultimo('{FONTE_AVVISI}')\n"
    "  x=c.execute('SELECT max(last_seen_utc) FROM avvisi_gtt').fetchone();r['_avvisi_ultimo']=x[0] if x else None\n"
    "except Exception as e:\n"
    "  r['_errori_fonti']='errore: '+str(e)\n"
    "print(json.dumps(r))"
)


def leggi_dal_pi():
    cmd = ["ssh", "-i", str(CHIAVE), "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", PI, "python3", "-"]
    p = subprocess.run(cmd, input=CODICE_PI, capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or f"ssh codice {p.returncode}")
    return json.loads(p.stdout.strip().splitlines()[-1])


def parsa(ts):
    """Tempo del database (UTC, con o senza 'Z') -> datetime UTC."""
    d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)


def gb(byte):
    return f"{byte / GB:,.1f} GB"


def controlli_risorse(u, ora, ora_it, righe, avvisi):
    """Spazio, /tmp, peso, GTFS, avvisi GTT. Aggiunge righe e AVVISI; ritorna la lista degli ALLARMI."""
    allarmi = []
    libero, peso = u.get("_libero"), u.get("_peso")
    if libero is None or peso is None:
        righe.append("  spazio e peso: non letti dal Pi")
        return allarmi
    righe.append(f"  spazio libero sul Pi: {gb(libero)}")
    if libero < SPAZIO_ALLARME_GB * GB:
        allarmi.append(f"spazio libero sul Pi {gb(libero)} (meno di {SPAZIO_ALLARME_GB} GB)")
    elif libero < SPAZIO_AVVISO_GB * GB:
        avvisi.append(f"spazio libero sul Pi {gb(libero)} (meno di {SPAZIO_AVVISO_GB} GB)")
    tipo = u.get("_tmp_tipo") or "disco (non e' un punto di mount a parte)"
    righe.append(f"  /tmp del Pi (solo informativo, dal 23/10 lo snapshot non sta piu' li'): {gb(u['_tmp_libero'])} liberi, tipo {tipo}")
    copia = u.get("_copia_libero")
    if copia is not None:
        righe.append(f"  spazio per lo snapshot (data/tmp_copia): {gb(copia)} liberi, ne servono {gb(TMP_VOLTE_STORICO * peso)}")
        if copia < TMP_VOLTE_STORICO * peso:
            allarmi.append(f"spazio per lo snapshot {gb(copia)}, meno di {TMP_VOLTE_STORICO} volte lo storico ({gb(peso)}): la copia fallira'")
    crescita = ""
    try:
        prima = json.loads(STATO.read_text(encoding="utf-8"))
        ore = (ora - parsa(prima["quando_utc"])).total_seconds() / 3600
        if ore >= CRESCITA_MIN_ORE:
            crescita = f", cresciuto di {(peso - prima['peso']) / 1e6 / (ore / 24):,.0f} MB al giorno dal lancio del {comuni.ora_locale(parsa(prima['quando_utc'])):%d/%m %H:%M}"
        base = prima if ore < CRESCITA_MIN_ORE else None
    except (OSError, ValueError, KeyError):
        base = None
    if base is None:
        STATO.parent.mkdir(exist_ok=True)
        STATO.write_text(json.dumps({"quando_utc": ora.isoformat(timespec="seconds"), "peso": peso}), encoding="utf-8")
    righe.append(f"  storico sul Pi: {gb(peso)}{crescita or ' (crescita: serve un lancio di almeno ' + str(CRESCITA_MIN_ORE) + ' ore fa)'}")
    if peso > STORICO_AVVISO_GB * GB:
        avvisi.append(f"storico oltre {STORICO_AVVISO_GB} GB ({gb(peso)}): vedi PIANO_RACCOLTA, passo 5")
    g = u.get("_gtfs")
    if isinstance(g, list):
        fine = datetime.strptime(g[3], "%Y-%m-%d").date()
        giorni = (fine - ora_it.date()).days
        righe.append(f"  GTFS: versione del {comuni.ora_locale(parsa(g[0])):%d/%m/%Y}, valido fino al {fine:%d/%m/%Y}, mancano {giorni} giorni")
        if giorni <= GTFS_ALLARME_GIORNI:
            allarmi.append(f"GTFS scade fra {giorni} giorni")
        elif giorni <= GTFS_AVVISO_GIORNI:
            avvisi.append(f"GTFS scade fra {giorni} giorni")
    else:
        righe.append(f"  GTFS: archivio senza versioni ({g or 'nessuna riga'})")
        avvisi.append("archivio GTFS non attivo o vuoto: il raccoglitore del Pi non l'ha ancora scaricato")
    if u.get("_gtfs_err_giorni", 0) >= GTFS_TENTATIVI_FALLITI_GIORNI:
        avvisi.append(f"GTFS: errore in ognuno degli ultimi {GTFS_TENTATIVI_FALLITI_GIORNI} giorni (ultimo: {u.get('_gtfs_err')})")
    ultimo_avviso = u.get("_avvisi_ultimo")
    nuovo_24h = bool(ultimo_avviso) and (ora - parsa(ultimo_avviso)).total_seconds() < 86400
    righe.append("  feed avvisi GTT: ultima riga vista " + (f"{comuni.ora_locale(parsa(ultimo_avviso)):%d/%m %H:%M}" if ultimo_avviso else "mai")
                 + f"; ore con errore nelle ultime 24: {u.get('_avvisi_err_ore', '?')}")
    if u.get("_avvisi_err_ore", 0) >= ORE_AVVISI_IN_ERRORE and not nuovo_24h:
        avvisi.append(f"feed avvisi GTT in errore per tutte le ultime 24 ore (ultimo: {u.get('_avvisi_err')})")
    return allarmi


def main():
    ora = datetime.now(timezone.utc)
    ora_it = comuni.ora_locale(ora)
    try:
        ultimi = leggi_dal_pi()
    except Exception as e:  # noqa: BLE001
        riga = f"{ora_it:%d/%m %H:%M} Pi non raggiungibile: {e}"
        print(riga)
        LOG.parent.mkdir(exist_ok=True)
        LOG.open("a", encoding="utf-8").write(riga + "\n")
        return 2
    allarmi, righe = [], []
    for t, (_, limite) in LIMITI_MINUTI.items():
        v = ultimi.get(t)
        if v is None or str(v).startswith("errore"):
            righe.append(f"  {t:16s} nessun dato ({v})")
            allarmi.append(t)
            continue
        minuti = (ora - parsa(v)).total_seconds() / 60
        notte = t == "trip_update_gtt" and 0 <= ora_it.hour < 6
        ferma = minuti > limite and not notte
        righe.append(f"  {t:16s} ultima lettura {comuni.ora_locale(parsa(v)):%d/%m %H:%M} (da {minuti:,.0f} min)"
                     + ("  <-- FERMA" if ferma else ""))
        if ferma:
            allarmi.append(t)
    ztl = ultimi.get("_ztl")
    righe.append(f"  {'ztl_5t':16s} ultima versione salvata {comuni.ora_locale(parsa(ztl)):%d/%m/%Y} (si salva solo se cambia: nessun allarme)"
                 if ztl else f"  {'ztl_5t':16s} nessuna versione salvata (nessun allarme)")
    err = ultimi.get("_errori")
    if isinstance(err, list):
        righe.append("  errori del raccoglitore nelle ultime 24 ore: " + (
            ", ".join(f"{f} {n} (ultimo {comuni.ora_locale(parsa(u)):%d/%m %H:%M})" for f, n, u in err) if err else "nessuno"))
    elif err:
        righe.append(f"  errori del raccoglitore: non letti ({err})")
    avvisi = []
    allarmi += controlli_risorse(ultimi, ora, ora_it, righe, avvisi)
    ferme = [a for a in allarmi if a in LIMITI_MINUTI]
    altri = [a for a in allarmi if a not in LIMITI_MINUTI]
    esito = "OK" if not allarmi else "ALLARME: " + "; ".join(([f"ferme {', '.join(ferme)}"] if ferme else []) + altri)
    if avvisi:
        esito += f" ({len(avvisi)} avvisi)"
    righe += [f"  AVVISO: {a}" for a in avvisi]
    print(f"Raccolta su leopi, {ora_it:%d/%m/%Y %H:%M}: {esito}")
    print("\n".join(righe))
    LOG.parent.mkdir(exist_ok=True)
    LOG.open("a", encoding="utf-8").write(f"{ora_it:%d/%m %H:%M} {esito}\n")
    return 0 if not allarmi else 1


if __name__ == "__main__":
    sys.exit(main())
