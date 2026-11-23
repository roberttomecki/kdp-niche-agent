#!/usr/bin/env bash
# Codzienne sprawdzenie Twoich książek z watch.txt (+ powiadomienia Telegram) i obserwowanych nisz z nisze.txt
cd "$(dirname "$0")" && mkdir -p logs
git pull --ff-only -q >> logs/track.log 2>&1 || true
set -a; [ -f .env ] && . ./.env; set +a
./venv/bin/python kdp_agent.py track --market "${MARKETS:-us}" >> logs/track.log 2>&1
# obserwowane nisze z nisze.txt (kilkadziesiąt zapytań, raz na dobę)
[ -f nisze.txt ] && ./venv/bin/python kdp_agent.py watch-niches --market "${MARKETS:-us}" >> logs/track.log 2>&1
exit 0
