#!/usr/bin/env bash
# Po stronie VPS: konto 'kdptunnel', które może TYLKO wystawić port 127.0.0.1:8888.
# Uruchom jako root:  sudo bash setup_vps_tunnel.sh 'ssh-ed25519 AAAA... kdp-tunnel@luckfox'
set -euo pipefail

PUBKEY="${1:?Podaj klucz publiczny wypisany przez setup_luckfox.sh (w apostrofach)}"
PROXY_PORT=8888
U=kdptunnel

[ "$(id -u)" -eq 0 ] || { echo "Uruchom jako root (sudo)."; exit 1; }
case "$PUBKEY" in ssh-ed25519\ *|ssh-rsa\ *) ;; *) echo "To nie wygląda na klucz SSH."; exit 1;; esac

id "$U" >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin "$U"
H=$(getent passwd "$U" | cut -d: -f6)
install -d -m 700 -o "$U" -g "$U" "$H/.ssh"
# restrict = zero uprawnień; potem tylko jedno przekierowanie zdalne na localhost:8888
echo "restrict,port-forwarding,permitlisten=\"127.0.0.1:${PROXY_PORT}\",command=\"/bin/false\" ${PUBKEY}" > "$H/.ssh/authorized_keys"
chown "$U:$U" "$H/.ssh/authorized_keys"
chmod 600 "$H/.ssh/authorized_keys"

# Sprawdź ustawienia sshd, które mogłyby zablokować tunel
EFF=$(sshd -T 2>/dev/null || true)
echo "$EFF" | grep -qi '^allowtcpforwarding \(no\|local\)' && \
  echo "UWAGA: sshd ma AllowTcpForwarding no/local – zmień na 'yes' lub 'remote' w /etc/ssh/sshd_config"
echo "$EFF" | grep -qi '^allowusers ' && ! echo "$EFF" | grep -i '^allowusers ' | grep -qw "$U" && \
  echo "UWAGA: sshd ma AllowUsers bez '$U' – dopisz go w /etc/ssh/sshd_config i zrestartuj ssh"

echo "OK: konto '$U' gotowe. Na Luckfoxie: systemctl restart kdp-tunnel"
echo "Test tutaj (po ~30 s):  curl -s -x http://127.0.0.1:${PROXY_PORT} https://api.ipify.org ; echo"
echo "Powinien pokazać Twój domowy adres IP, a nie adres VPS."
