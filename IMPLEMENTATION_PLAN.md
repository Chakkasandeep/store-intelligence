# Implementation Plan

## Scoring map

| Challenge area | Points | Module |
|----------------|--------|--------|
| Detection pipeline | 30 | `pipeline/run_pipeline.py`, `reid.py`, `staff.py` |
| API & business logic | 35 | `backend/*` |
| Production readiness | 20 | `docker/`, `tests/`, logging |
| Engineering thinking | 15 | `DESIGN.md`, `CHOICES.md`, test PROMPT blocks |
| Dashboard bonus | +10 | `dashboard/` |

## Phases completed

| Phase | Deliverable |
|-------|-------------|
| 0 | Repo scaffold, requirements, COMMANDS.md |
| 1 | DATA_ANALYSIS, CAMERA_ANALYSIS, STORE_LAYOUT, POS_MAPPING |
| 2 | Architecture (this plan + DESIGN.md) |
| 3 | YOLOv8n pipeline, all event types, Re-ID, staff |
| 4 | FastAPI endpoints + OpenAPI |
| 5 | Metrics, funnel, heatmap |
| 6 | Anomalies (QUEUE_SPIKE, CONVERSION_DROP, DEAD_ZONE, STALE_FEED) |
| 7 | React dashboard + WebSocket |
| 8 | SQLite schema |
| 9 | structlog JSON request logs |
| 10 | pytest suite (12 tests) |
| 11 | Documentation set |
| 12 | docker compose |

## System flow (detailed)

1. `discover_all.py` → POS + cameras + layout JSON  
2. `run_pipeline.py` → `data/events/output.jsonl`  
3. `uvicorn` bootstrap → ingest JSONL + POS transactions  
4. Dashboard polls/WebSocket metrics  

## i5 execution profile

- `--frame-stride 8`  
- `--max-frames 600` per clip (~20s wall-clock per camera with YOLOv8n)  
- Full run optional overnight  

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| CAM 2 vs CAM 5 billing | Documented; role-driven ROIs; re-run discovery |
| POS/CCTV time mismatch | Session conversion window; OSD-aligned clip base time |
| Slow docker first boot | `max-frames` in entrypoint |
