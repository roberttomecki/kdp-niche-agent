#!/usr/bin/env bash
# Codzienne sprawdzenie Twoich książek z watch.txt (+ powiadomienia Telegram)
cd "$(dirname "$0")" && mkdir -p logs
git pull --ff-only -q >> logs/track.log 2>&1 || true
set -a; [ -f .env ] && . ./.env; set +a
exec ./venv/bin/python kdp_agent.py track --market "${MARKETS:-us}" >> logs/track.log 2>&1
