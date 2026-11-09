#!/usr/bin/env bash
# Bramka domowa na Luckfox Pico Ultra (Ubuntu): tinyproxy + odwrotny tunel SSH do VPS.
# Uruchom jako root na Luckfoxie:  sudo bash setup_luckfox.sh IP_LUB_HOST_VPS [PORT_SSH]
set -euo pipefail

VPS_HOST="${1:?Podaj adres VPS, np.: sudo bash setup_luckfox.sh 123.45.67.89}"
VPS_PORT="${2:-22}"
PROXY_PORT=8888
KEY=/root/.ssh/kdp_tunnel

[ "$(id -u)" -eq 0 ] || { echo "Uruchom jako root (sudo)."; exit 1; }
command -v systemctl >/dev/null || { echo "Brak systemd – potrzebny obraz Ubuntu, nie Buildroot."; exit 1; }

echo "== Instaluję tinyproxy i autossh"
apt-get update -q
DEBIAN_FRONTEND=noninteractive apt-get install -y -q tinyproxy autossh openssh-client

echo "== Konfiguruję tinyproxy (tylko localhost, tylko HTTPS)"
[ -f /etc/tinyproxy/tinyproxy.conf.orig ] || cp /etc/tinyproxy/tinyproxy.conf /etc/tinyproxy/tinyproxy.conf.orig
cat > /etc/tinyproxy/tinyproxy.conf <<EOF
User tinyproxy
Group tinyproxy
Port ${PROXY_PORT}
Listen 127.0.0.1
Timeout 60
MaxClients 10
LogLevel Warning
Syslog On
Allow 127.0.0.1
# Tylko tunele HTTPS (CONNECT na 443) – nic innego nie przejdzie
ConnectPort 443
# Nie zdradzaj, że to proxy
DisableViaHeader Yes
XTinyproxy No
EOF
systemctl enable tinyproxy >/dev/null
systemctl restart tinyproxy

echo "== Klucz SSH dla tunelu"
mkdir -p /root/.ssh && chmod 700 /root/.ssh
[ -f "$KEY" ] || ssh-keygen -q -t ed25519 -N "" -C "kdp-tunnel@$(hostname)" -f "$KEY"

echo "== Usługa kdp-tunnel (autossh)"
cat > /etc/systemd/system/kdp-tunnel.service <<EOF
[Unit]
Description=KDP: odwrotny tunel SSH do VPS (proxy 127.0.0.1:${PROXY_PORT})
After=network-online.target tinyproxy.service
Wants=network-online.target

[Service]
Environment=AUTOSSH_GATETIME=0
ExecStart=/usr/bin/autossh -M 0 -N -T \\
  -i ${KEY} -p ${VPS_PORT} \\
  -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \\
  -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=accept-new \\
  -o BatchMode=yes \\
  -R 127.0.0.1:${PROXY_PORT}:127.0.0.1:${PROXY_PORT} \\
  kdptunnel@${VPS_HOST}
Restart=always
RestartSec=20

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable kdp-tunnel >/dev/null

echo
echo "================================================================"
echo "Gotowe po stronie Luckfoxa. Teraz na VPS (jako root) uruchom:"
echo
echo "  sudo bash deploy/vps/setup_vps_tunnel.sh '$(cat ${KEY}.pub)'"
echo
echo "Potem wróć tutaj i wpisz:  systemctl restart kdp-tunnel"
echo "Status:                    systemctl status kdp-tunnel --no-pager"
echo "================================================================"
