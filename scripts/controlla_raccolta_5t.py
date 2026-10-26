"""Controllo da eseguire SUL Pi (lo lancia AGGIORNA_RACCOLTA_LEOPI.bat via ssh):
verifica che il raccoglitore corretto salvi i 112 sensori fisici, cioe' che nell'ultimo
istante salviato ci siano 112 righe e che i tre codici condivisi ("~2") abbiano dati.
Sola lettura: non scrive niente sul Pi.

Cosa deve uscire: "sensori ultimo istante: 112" e "codici ~2 con dati: 3/3" -> giusto.
"""

import os
import sqlite3

DB = os.path.expanduser("~/GTT/data/storico.sqlite")


def main():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    ultimo = c.execute("select max(generato_utc) from flussi_5t").fetchone()[0]
    if not ultimo:
        print("NESSUN DATO in flussi_5t")
        return
    n_sensori = c.execute("select count(*) from flussi_5t where generato_utc=?",
                          (ultimo,)).fetchone()[0]
    n_pos = c.execute("select count(*) from sensori_5t").fetchone()[0]
    righe = {r[0]: (r[1], r[2]) for r in c.execute(
        "select lcd1, flusso, velocita from flussi_5t where generato_utc=?", (ultimo,))}
    print(f"ultimo istante salvato : {ultimo}")
    print(f"sensori nell'ultimo istante: {n_sensori}   (atteso 112)")
    print(f"posizioni note in sensori_5t: {n_pos}   (atteso 112)")
    trovati = 0
    for cod in ("40123~2", "40189~2", "13077~2"):
        v = righe.get(cod)
        if v is None:
            # il codice puo' non essere ancora arrivato: guardo nell'ultimo istante in cui c'e'
            r = c.execute("select generato_utc, flusso from flussi_5t where lcd1=? "
                          "order by generato_utc desc limit 1", (cod,)).fetchone()
            print(f"  {cod}: non nell'ultimo istante; ultima lettura {None if not r else r[0]} "
                  f"flusso {None if not r else r[1]}")
        else:
            trovati += 1
            print(f"  {cod}: flusso {v[0]} velocita {v[1]}  OK")
    print(f"codici ~2 con dati nell'ultimo istante: {trovati}/3")
    if n_sensori == 112 and trovati == 3:
        print("ESITO: GIUSTO (112 sensori e 3/3 codici nuovi con dati)")
    elif n_sensori == 112:
        print("ESITO: i 112 sensori ci sono; i codici nuovi stanno arrivando poco alla volta")
    else:
        print("ESITO: NON ancora 112 sensori nell'ultimo istante: il raccoglitore non e' stato "
              "aggiornato, oppure e' appena ripartito (aspetta 10 minuti e rilancia il controllo)")
    c.close()


if __name__ == "__main__":
    main()
