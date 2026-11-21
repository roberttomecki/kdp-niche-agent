#!/usr/bin/env bash
# Instaluje bota Telegram jako usługę (startuje sam po restarcie serwera).
# Uruchom na VPS:  sudo bash /opt/kdp-niche-agent/deploy/vps/install_bot.sh
set -e
DIR=/opt/kdp-niche-agent
chmod +x "$DIR/bot.sh"
cat > /etc/systemd/system/kdp-bot.service <<UNIT
[Unit]
Description=Agent KDP - bot Telegram
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=$DIR/bot.sh
Restart=always
RestartSec=15
StandardOutput=append:$DIR/logs/bot.log
StandardError=append:$DIR/logs/bot.log

[Install]
WantedBy=multi-user.target
UNIT
mkdir -p "$DIR/logs"
systemctl daemon-reload
systemctl enable --now kdp-bot
sleep 3
systemctl is-active kdp-bot >/dev/null && echo "Bot działa. Napisz do niego w Telegramie: /pomoc" \
  || { echo "Bot nie wystartował – ostatnie linie logu:"; tail -20 "$DIR/logs/bot.log"; }
