#!/usr/bin/env bash
# Uruchomienie z cron: ładuje .env i odpala pełny cykl
cd "$(dirname "$0")" && mkdir -p logs
# najnowsze poprawki z GitHuba przed każdym przebiegiem (tylko fast-forward, błąd nie zatrzymuje)
git pull --ff-only -q >> logs/run.log 2>&1 || true
set -a; [ -f .env ] && . ./.env; set +a
exec ./venv/bin/python kdp_agent.py run --seeds seeds.txt --market "${MARKETS:-us}" --top "${TOP:-30}" --screen "${SCREEN:-120}" --rotate "${ROTATE:-20}" --rounds "${ROUNDS:-2}" >> logs/run.log 2>&1
