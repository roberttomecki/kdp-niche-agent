#!/usr/bin/env bash
# Bot Telegram (uruchamia go usługa systemd kdp-bot)
cd "$(dirname "$0")" && mkdir -p logs
set -a; [ -f .env ] && . ./.env; set +a
exec ./venv/bin/python kdp_agent.py bot
