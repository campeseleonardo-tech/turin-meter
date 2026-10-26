#!/usr/bin/env bash
# Installa la raccolta continua GTFS-RT trip_update/alerts come servizio systemd.
# Da eseguire sul Pi dopo aver copiato 12_ritardi_gtt.py:
#     sudo bash installa_ritardi.sh

set -euo pipefail

UTENTE="${SUDO_USER:-$(whoami)}"
PROGETTO="/home/${UTENTE}/GTT"
PYTHON="$(command -v python3)"
SERVIZIO="/etc/systemd/system/gtt-ritardi.service"

if [[ ! -f "${PROGETTO}/scripts/12_ritardi_gtt.py" ]]; then
    echo "Script non trovato: ${PROGETTO}/scripts/12_ritardi_gtt.py" >&2
    exit 1
fi

cat > "${SERVIZIO}" <<EOF
[Unit]
Description=Raccolta continua GTT trip_update e avvisi
After=network-online.target gtt-raccolta.service
Wants=network-online.target

[Service]
User=${UTENTE}
WorkingDirectory=${PROGETTO}
Environment=PYTHONUNBUFFERED=1
ExecStart=${PYTHON} -u ${PROGETTO}/scripts/12_ritardi_gtt.py raccogli-db --db ${PROGETTO}/data/storico.sqlite --ogni-secondi 60
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now gtt-ritardi.service
systemctl --no-pager --lines=20 status gtt-ritardi.service

echo
echo "Verifiche utili:"
echo "  systemctl status gtt-ritardi"
echo "  journalctl -u gtt-ritardi -f"
echo "  systemctl restart gtt-ritardi"
