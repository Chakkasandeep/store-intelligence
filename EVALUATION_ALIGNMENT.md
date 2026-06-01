# Evaluation Framework Alignment (Purplle 2026 Round 2)

This document maps **every acceptance gate and scoring criterion** to concrete artifacts in this repository. Reviewers can use it during the structured ~10-minute evaluation window.

**Live demo (optional):** [Hugging Face Space](https://huggingface.co/spaces/SandeepChakka/store-intelligence)  
**Graded submission:** Private **Git** repo + `docker compose up` (see [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md))

---

## 3. Acceptance Gate (mandatory — fail any = reject)

| Check | Required | Status | Evidence |
|-------|----------|--------|----------|
| System execution | `docker compose up` without manual steps | **PASS** | [docker-compose.yml](docker-compose.yml), [docker/entrypoint.sh](docker/entrypoint.sh) — discovery skip if configs exist; pipeline skip if `data/events/output.jsonl` present; auto bootstrap ingest |
| API availability | `/metrics` valid JSON | **PASS** | `GET /stores/ST1008/metrics` — [backend/metrics.py](backend/metrics.py) |
| Event generation | Pipeline produces structured events | **PASS** | [pipeline/run_pipeline.py](pipeline/run_pipeline.py) → [data/events/output.jsonl](data/events/output.jsonl) (69 events, schema in [pipeline/emit.py](pipeline/emit.py)) |
| Documentation | DESIGN.md + CHOICES.md non-trivial | **PASS** | [DESIGN.md](DESIGN.md), [CHOICES.md](CHOICES.md) |
| Stability | No crash during basic run | **PASS** | Healthcheck in compose; pytest suite |

**Reviewer commands (2 min):**

```bash
cd store-intelligence
docker compose up --build
curl -s http://localhost:8000/stores/ST1008/metrics
curl -s http://localhost:8000/health
```

**Dataset layout (parent folder):** Place `CCTV Footage/` and Brigade POS CSV next to `store-intelligence/` as documented in [RUN_GUIDE.md](RUN_GUIDE.md). Committed `output.jsonl` allows fast start without re-running YOLO on review hardware.

---

## 5.1 Detection Pipeline (30 marks)

| Criterion | Implementation | Where to verify |
|-----------|----------------|-----------------|
| Entry/exit counts | Entry camera role on CAM 3; line-crossing in pipeline | `python scripts/count_events.py` — compare ENTRY count to CAM 3 clip |
| Re-entry | Session lifecycle on ENTRY/EXIT; Re-ID bank | [pipeline/reid.py](pipeline/reid.py), [backend/sessions.py](backend/sessions.py) |
| Staff | Trajectory + multi-zone heuristics | [pipeline/staff.py](pipeline/staff.py), `is_staff` on events |
| Group entry | Multiple track_ids; shared session rules | [pipeline/run_pipeline.py](pipeline/run_pipeline.py) |
| Structured events | Full schema with `event_id`, `confidence`, `metadata` | [tests/test_pipeline.py](tests/test_pipeline.py) `test_emit_schema` |

**Validation:** Inspect `data/events/output.jsonl` — types include `ENTRY`, `EXIT`, `ZONE_ENTER`, `ZONE_DWELL`, `QUEUE`, `BILLING`, etc.

---

## 5.2 API and Business Logic (35 marks)

| Criterion | Implementation | Endpoint |
|-----------|----------------|----------|
| Endpoint correctness | Pydantic models + SQL aggregation | `/stores/{id}/metrics`, `/funnel`, `/heatmap`, `/anomalies` |
| Session funnel (no double count) | Funnel uses `sessions` table, not raw event count | [backend/funnel.py](backend/funnel.py) |
| POS conversion | 5-minute window after billing visit | [backend/metrics.py](backend/metrics.py), [CHOICES.md](CHOICES.md) |
| Anomaly detection | Queue depth, stale feed, conversion drop | [backend/anomalies.py](backend/anomalies.py) |
| Ingest | Idempotent `event_id` | `POST /events/ingest` — [tests/test_api.py](tests/test_api.py) |

**Validation:** `/funnel` shows Entry → Zone → Billing → Purchase drop-off; `/metrics` uses event date window ([backend/analytics_window.py](backend/analytics_window.py)).

---

## 5.3 Production Readiness (20 marks)

| Criterion | Implementation |
|-----------|----------------|
| Deployment | Docker + compose; HF Docker Space for demo |
| Observability | structlog JSON: `trace_id`, `latency_ms`, `store_id` — [backend/main.py](backend/main.py) |
| Testing | 12 pytest tests — [tests/](tests/) |
| Health | `/health` with component status — [backend/health.py](backend/health.py) |
| Live dashboard | React + WebSocket `/ws/metrics` — [dashboard/](dashboard/) |

---

## 5.4 Engineering Thinking (15 marks)

| Criterion | Document |
|-----------|----------|
| Architecture | [DESIGN.md](DESIGN.md) |
| Trade-offs (AI accepted/rejected) | [CHOICES.md](CHOICES.md) |
| Discovery (no hardcoded store/camera IDs) | [scripts/discover_*.py](scripts/), [configs/generated/](configs/generated/) |
| Analysis depth | [docs/CAMERA_ANALYSIS.md](docs/CAMERA_ANALYSIS.md), [docs/POS_MAPPING.md](docs/POS_MAPPING.md) |

---

## 6. Integrity Check (score cap at 50 if violated)

| Check | Status | Notes |
|-------|--------|-------|
| Hardcoded metric outputs | **PASS** | Metrics computed from SQLite after ingest |
| Outputs vary with input | **PASS** | Re-run pipeline or ingest → DB changes |
| Real computation | **PASS** | YOLOv8n + ByteTrack in [pipeline/run_pipeline.py](pipeline/run_pipeline.py); API aggregates from DB |

Committed `output.jsonl` is a **reviewer convenience** (same as shipping pre-built artifacts); pipeline source reproduces events from CCTV when clips are mounted.

---

## 7. Score targets

| Range | Interpretation |
|-------|----------------|
| 85+ | Strong — working system + clear docs + tests |
| 70–85 | Interview suitable |
| 60–70 | Above average |

**Known limitations (documented, not hidden):** Historical clip dates; conversion % may be 0 if POS timestamps misalign with clip window — see [CHOICES.md](CHOICES.md).

---

## Submission channels

| Channel | Role |
|---------|------|
| **Private GitHub/GitLab** | **Primary** — full `docker compose`, CCTV instructions, all source |
| **Hugging Face Space** | **Secondary** — always-on API + dashboard demo (no MP4) |

Do **not** use public HF as the only submission if the brief asks for a Git repo link.
