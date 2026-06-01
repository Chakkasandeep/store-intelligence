# DESIGN — Store Intelligence System

## Architecture

```
CCTV Footage (5× MP4)
    → discover_cameras.py → camera_profile.json
    → run_pipeline.py (YOLOv8n + ByteTrack + ReID)
    → output.jsonl
    → POST /events/ingest
    → SQLite (sessions, events, transactions)
    → metrics / funnel / heatmap / anomalies
    → WebSocket + React dashboard
```

## Event flow

1. **Detection:** Ultralytics YOLOv8n `person` class, `track()` with ByteTrack.
2. **Tracking:** Per-clip `track_id` → global `visitor_id` via HSV histogram Re-ID bank.
3. **Semantics:** Role-based rules (entry line, zone polygons, billing queue counter).
4. **Staff:** Persistence + movement + multi-zone heuristics → `is_staff`, `staff_confidence`.
5. **Ingestion:** Idempotent insert on `event_id`; session_id attached on ENTRY/EXIT lifecycle.
6. **POS:** Orders loaded from derived CSV; conversion within 5-minute window after billing visit.

## Database (SQLite default)

| Table | Role |
|-------|------|
| events | Raw ingested stream |
| sessions | Visitor visit unit for funnel |
| transactions | POS orders |
| anomalies | Last detected operational issues |

ER (logical):

```
stores (implicit ST1008) 1—* sessions 1—* events
sessions *—* transactions (time-window conversion)
stores 1—* anomalies
```

## API layer

- FastAPI + async SQLAlchemy
- Structured JSON logs: `trace_id`, `store_id`, `endpoint`, `latency_ms`, `status_code`
- Partial ingest success (per-event validation)
- `/health` STALE_FEED if last event > 10 minutes

## AI-assisted decisions

1. **Camera roles:** AI suggested scoring motion/brightness; human validation noted CAM 5 billing vs auto CAM 2 — documented in `CAMERA_ANALYSIS.md`, no hardcoded overrides in code.
2. **Zone polygons:** AI proposed normalized ROIs per role; rejected pixel-perfect CAD mapping due to raster-only layout.
3. **Staff detection:** AI proposed uniform color classifier; chose trajectory persistence + multi-zone rules for CPU budget on i5.

## Deployment

`docker compose up` builds API image, mounts CCTV + data volumes, runs discovery + pipeline + uvicorn; dashboard via Node service.
