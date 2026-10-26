"""Controllo da eseguire SUL Pi (lo lancia AGGIORNA_RACCOLTA_LEOPI.bat via ssh):
stampa quante letture parcheggi/ZTL ci sono nello storico. Sola lettura."""
import os
import sqlite3

c = sqlite3.connect("file:" + os.path.expanduser("~/GTT/data/storico.sqlite") + "?mode=ro", uri=True)
n_pk = c.execute("select count(*) from parcheggi_5t").fetchone()[0]
n_let, ultima = c.execute("select count(*), max(generato_utc) from occupazione_pk").fetchone()
n_ztl = c.execute("select count(*) from ztl_5t").fetchone()[0]
print(f"parcheggi: {n_pk}  letture: {n_let}  ultima: {ultima}  ztl: {n_ztl}")
