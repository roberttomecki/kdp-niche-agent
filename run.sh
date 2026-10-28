#!/usr/bin/env bash
# Uruchomienie z cron: ładuje .env i odpala pełny cykl
cd "$(dirname "$0")"
set -a; [ -f .env ] && . ./.env; set +a
exec ./venv/bin/python kdp_agent.py run --seeds seeds.txt --market "${MARKETS:-us}" --top "${TOP:-30}" --rounds "${ROUNDS:-2}" >> logs/run.log 2>&1
