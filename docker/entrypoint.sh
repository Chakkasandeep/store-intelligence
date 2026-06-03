#!/bin/sh
set -e
cd /app

if [ -d configs/generated/ST1008 ] && [ -d configs/generated/ST_STORE2 ]; then
  echo "[1/4] Discovery configs present for both stores - skip"
else
  echo "[1/4] Discovery..."
  python scripts/discover_all.py || true
fi

ST1_EVENTS="/app/data/events/ST1008/output.jsonl"
ST2_EVENTS="/app/data/events/ST_STORE2/output.jsonl"

if [ -f "$ST1_EVENTS" ] && [ -f "$ST2_EVENTS" ]; then
  echo "[2/4] Store events already present - skipping pipeline"
else
  echo "[2/4] Detection pipeline (CPU-friendly profile)..."
  if [ ! -f "$ST1_EVENTS" ]; then
    echo "Running pipeline for ST1008..."
    python pipeline/run_pipeline.py --store-id ST1008 --frame-stride 8 --max-frames 600 || echo "Pipeline warning ST1008 - continuing"
  fi
  if [ ! -f "$ST2_EVENTS" ]; then
    echo "Running pipeline for ST_STORE2..."
    python pipeline/run_pipeline.py --store-id ST_STORE2 --frame-stride 8 --max-frames 600 || echo "Pipeline warning ST_STORE2 - continuing"
  fi
fi

echo "[3/4] API bootstrap..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
