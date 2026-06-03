#!/bin/sh
cd "$(dirname "$0")/.."
python scripts/discover_all.py
python pipeline/run_pipeline.py --store-id ST1008 --frame-stride 8 --max-frames 600
python pipeline/run_pipeline.py --store-id ST_STORE2 --frame-stride 8 --max-frames 600
