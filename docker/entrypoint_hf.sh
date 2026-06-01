#!/bin/sh
set -e
cd /app

if [ -f configs/generated/camera_profile.json ] && [ -f configs/generated/pos_mapping.json ]; then
  echo "[1/3] Discovery configs present - skip"
else
  echo "[1/3] Discovery..."
  python scripts/discover_all.py || true
fi

EVENTS_FILE="/app/data/events/output.jsonl"
if [ -f "$EVENTS_FILE" ] && [ -s "$EVENTS_FILE" ]; then
  echo "[2/3] Events present ($(wc -l < "$EVENTS_FILE") lines) - skip pipeline"
else
  echo "[2/3] No events file - API will start empty (add output.jsonl for demo)"
fi

echo "[3/3] API + dashboard bootstrap..."
export EVENTS_JSONL=/app/data/events/output.jsonl
export PORT="${PORT:-7860}"
exec uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"
