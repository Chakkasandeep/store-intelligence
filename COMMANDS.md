# Commands — Store Intelligence System

This document outlines the standard commands to configure, execute, test, and run the Store Intelligence System.

## Python Environment Setup

```bash
# Create venv
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 1. Dynamic Store Discovery

Discovers POS schemas, video cameras, layouts, and generates configs under `configs/generated/{store_id}/` for all detected stores.

```bash
python scripts/discover_all.py
```

## 2. Run Computer Vision Pipeline

Processes footage with YOLOv8n + ByteTrack and emits challenge events.

```bash
# Process Store 1 (ST1008)
python pipeline/run_pipeline.py --store-id ST1008 --frame-stride 8 --max-frames 600

# Process Store 2 (ST_STORE2)
python pipeline/run_pipeline.py --store-id ST_STORE2 --frame-stride 8 --max-frames 600
```

## 3. Run FastAPI Backend

Launches the REST API server.

```bash
# Set environment path
$env:PYTHONPATH="."

# Launch API
uvicorn backend.main:app --reload --port 8000
```

## 4. Run React Dashboard

Launches the live metrics frontend.

```bash
cd dashboard
npm install
npm run dev
```

Open dashboard at: **http://localhost:5173**

## 5. Run Automated Tests

Executes the test suite verifying schemas, metrics, normalizer, and re-entry handling.

```bash
python -m pytest tests/ -v
```

## 6. Docker Compose Quickstart

Builds and runs all components in a containerized environment:

```bash
docker compose up --build
```

- API docs: **http://localhost:8000/docs**
- Health status: **http://localhost:8000/health**
- Store 1 metrics: **http://localhost:8000/stores/ST1008/metrics**
- Store 2 metrics: **http://localhost:8000/stores/ST_STORE2/metrics**
