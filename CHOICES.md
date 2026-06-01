# CHOICES — Engineering Decisions

## 1. Detection model: YOLOv8n + ByteTrack

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| YOLOv8n | Fast on CPU, good person AP | Weaker on heavy occlusion | **Selected** |
| RT-DETR | Accuracy | Heavier | Rejected for i5 |
| MediaPipe | Very fast | Less stable tracking | Rejected |

**AI suggestion:** Use YOLOv8 medium. **Override:** `n` variant + frame stride 6–8 for ~140s clips on i5.

## 2. Event schema

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Challenge JSON schema | Grader compatibility | Verbose | **Selected** |
| Flat CSV export | Easy BI | Loses confidence | Rejected |

**AI suggestion:** Drop events &lt; 0.5 confidence. **Rejected:** Brief requires low-confidence flags, not suppression.

## 3. API storage & funnel unit

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| SQLite + session table | Zero ops, docker-friendly | Scale limits | **Selected** |
| Postgres | Scale | Extra service | Optional env `DATABASE_URL` |
| Event-only funnel | Simple | Double-count re-entry | Rejected |

**AI suggestion:** Cache `/metrics` hourly. **Rejected:** Brief asks real-time metrics for “today”.

## AI suggestions accepted

- FastAPI + Pydantic v2 validation
- Idempotent ingest via `event_id`
- Discovery scripts instead of static `store_layout.json` in repo

## AI suggestions rejected

- Hardcoded `STORE_BLR_002` from PDF sample → use CSV `ST1008`
- Pre-baked metrics JSON → all metrics computed from DB
- VLM per-frame zone labeling → cost/latency on i5
