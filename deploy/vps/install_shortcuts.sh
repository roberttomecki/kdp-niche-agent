#!/usr/bin/env bash
# Instaluje polecenie 'kdp' i podpowiedź wyświetlaną po zalogowaniu.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Uruchom jako root."; exit 1; }
HERE=$(cd "$(dirname "$0")" && pwd)
ln -sf "$HERE/kdp" /usr/local/bin/kdp
chmod +x "$HERE/kdp"
cat > /etc/update-motd.d/99-kdp <<'EOF'
#!/bin/sh
echo ""
echo "  Agent KDP:  kdp status | kdp raport | kdp history \"fraza\" | kdp run   (kdp = pomoc)"
echo "  Luckfox:    kdp luckfox   (logowanie przez tunel, hasło użytkownika pico; powrót: exit)"
echo ""
EOF
chmod +x /etc/update-motd.d/99-kdp
echo "Gotowe. Wpisz:  kdp"
