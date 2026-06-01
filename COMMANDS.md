# Commands — Store Intelligence

## Python virtual environment

```bash
python -m venv .venv
```

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Discovery (run before pipeline/API)

```bash
cd store-intelligence
python scripts/discover_all.py
python scripts/analyze_videos.py
```

## Run detection pipeline

Full clips (slow on i5):

```bash
python pipeline/run_pipeline.py --output data/events/output.jsonl
```

CPU-friendly profile:

```bash
python pipeline/run_pipeline.py --frame-stride 8 --max-frames 600 --output data/events/output.jsonl
```

## Run API

```bash
set PYTHONPATH=.
uvicorn backend.main:app --reload --port 8000
```

## Run dashboard

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:5173

## Run tests

```bash
pytest tests/ -v --cov=backend --cov=pipeline --cov-report=term-missing
```

## Generate events (discovery + pipeline)

```bash
python scripts/discover_all.py && python pipeline/run_pipeline.py --frame-stride 8 --max-frames 600
```

## Replay events into API

```bash
curl -X POST http://localhost:8000/events/ingest -H "Content-Type: application/json" --data-binary "@data/events/output.jsonl"
```

Or rely on API bootstrap (`EVENTS_JSONL` env) on startup.

## Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/stores/ST1008/metrics
curl http://localhost:8000/stores/ST1008/funnel
curl http://localhost:8000/stores/ST1008/heatmap
curl http://localhost:8000/stores/ST1008/anomalies
```

## Docker

From `store-intelligence/`:

```bash
docker compose up --build
```

- API: http://localhost:8000  
- Dashboard: http://localhost:5173  
- Docs: http://localhost:8000/docs  

## WebSocket

```
ws://localhost:8000/ws/metrics?store_id=ST1008
```
