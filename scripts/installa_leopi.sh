#!/usr/bin/env bash
# installa_leopi.sh — installa la raccolta GTT come servizio systemd sul Raspberry Pi.
#
# Da eseguire SUL Pi con sudo (dopo aver copiato la cartella col WinSCP):
#     sudo bash installa_leopi.sh
#
# Presupposti:
#   - /home/<utente>/GTT/scripts  contiene 03_raccolta_continua.py, 06_dati_live.py,
#     supervisore.py (copiati dal PC);
#   - /home/<utente>/GTT/data/storico.sqlite  presente (copia dal PC, se serve lo storico);
#   - python3 presente (basta la libreria standard).
#
# Il servizio systemd lancia supervisore.py, che a sua volta tiene acceso 03
# (5T + mezzi + accuratezza_5t) e ogni minuto genera i file per la mappa (06):
# stessi comportamenti del PC, senza finestre né avvio automatico di Windows.
# Su Linux la finestra settimanale "continuiamo?" diventa una riga nel journal.

set -euo pipefail

UTENTE="${SUDO_USER:-$(whoami)}"
PROGETTO="/home/${UTENTE}/GTT"
SERVIZIO="/etc/systemd/system/gtt-raccolta.service"
PYTHON="$(command -v python3)"

echo "== Ambiente =="
echo "utente: ${UTENTE}   progetto: ${PROGETTO}   python: ${PYTHON}"
"${PYTHON}" --version

# cartelle di lavoro (la base la copia Leo col WinSCP)
mkdir -p "${PROGETTO}"/data "${PROGETTO}"/logs

# fuso orario Europe/Rome (per log e aggregazioni)
if ! timedatectl show -p Timezone --value 2>/dev/null | grep -q Europe/Rome; then
    timedatectl set-timezone Europe/Rome
    echo "== Fuso impostato: Europe/Rome =="
fi

# unit systemd
cat > "${SERVIZIO}" <<EOF
[Unit]
Description=Raccolta dati GTT Torino (supervisore: 03 raccolta + 06 file mappa)
After=network-online.target
Wants=network-online.target

[Service]
User=${UTENTE}
WorkingDirectory=${PROGETTO}
Environment=PYTHONUNBUFFERED=1
ExecStart=${PYTHON} -u ${PROGETTO}/scripts/supervisore.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "== Unit scritta: ${SERVIZIO} =="
systemctl daemon-reload
systemctl enable --now gtt-raccolta.service
systemctl --no-pager --lines=20 status gtt-raccolta.service

echo
echo "Fatto. Controlli utili:"
echo "  systemctl status gtt-raccolta            # vedi attivita"
echo "  journalctl -u gtt-raccolta -f            # log in tempo reale"
echo "  ls ${PROGETTO}/logs                      # log del raccoglitore"
echo "  python3 ${PROGETTO}/scripts/06_dati_live.py  # prova manuale dei file mappa"