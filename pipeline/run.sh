#!/bin/sh
cd "$(dirname "$0")/.."
python scripts/discover_all.py
python pipeline/run_pipeline.py --frame-stride 8 --max-frames 600 --output data/events/output.jsonl
