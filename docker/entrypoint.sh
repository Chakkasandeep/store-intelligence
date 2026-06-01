#!/bin/sh
set -e
cd /app

if [ -f configs/generated/camera_profile.json ] && [ -f configs/generated/pos_mapping.json ]; then
  echo "[1/4] Discovery configs present - skip"
else
  echo "[1/4] Discovery..."
  python scripts/discover_all.py || true
fi

EVENTS_FILE="/app/data/events/output.jsonl"
if [ -f "$EVENTS_FILE" ] && [ -s "$EVENTS_FILE" ]; then
  echo "[2/4] Events already present - skipping pipeline"
  wc -l < "$EVENTS_FILE" || true
else
  echo "[2/4] Detection pipeline (CPU-friendly profile)..."
  python pipeline/run_pipeline.py --frame-stride 8 --max-frames 600 || echo "Pipeline warning - continuing without new events"
fi

echo "[3/4] API bootstrap..."
export EVENTS_JSONL=/app/data/events/output.jsonl
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
