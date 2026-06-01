---
title: Store Intelligence — Apex Retail ST1008
emoji: 🏪
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: true
license: mit
short_description: Store Intelligence API + live dashboard (Purplle 2026)
---

# Store Intelligence — Live Demo

**End-to-end retail analytics** for **Apex Retail / Purplle Tech Challenge 2026 (Round 2)**  
Store **ST1008** (Brigade Road, Bangalore) · 5 cameras · session-based funnel · POS correlation

| Layer | Stack |
|-------|--------|
| Detection | YOLOv8n + ByteTrack + histogram Re-ID |
| Events | JSONL → idempotent FastAPI ingest |
| API | FastAPI + SQLite + structured logs |
| UI | React + Vite + Tailwind (served from same container) |

---

## Live links (this Space)

| What | URL |
|------|-----|
| **Dashboard** | [/](https://huggingface.co/spaces/SandeepChakka/store-intelligence) |
| **Swagger API** | [/docs](https://huggingface.co/spaces/SandeepChakka/store-intelligence/docs) |
| **Health** | [/health](https://huggingface.co/spaces/SandeepChakka/store-intelligence/health) |
| **Metrics** | [/stores/ST1008/metrics](https://huggingface.co/spaces/SandeepChakka/store-intelligence/stores/ST1008/metrics) |
| **Funnel** | [/stores/ST1008/funnel](https://huggingface.co/spaces/SandeepChakka/store-intelligence/stores/ST1008/funnel) |
| **Heatmap** | [/stores/ST1008/heatmap](https://huggingface.co/spaces/SandeepChakka/store-intelligence/stores/ST1008/heatmap) |
| **Anomalies** | [/stores/ST1008/anomalies](https://huggingface.co/spaces/SandeepChakka/store-intelligence/stores/ST1008/anomalies) |
| **WebSocket metrics** | `wss://…/ws/metrics?store_id=ST1008` |

Replace `…` with this Space hostname after deploy.

---

## Challenge deliverables (mapped)

Per **Problem Statement** and **Evaluation Framework**:

| Deliverable | Where |
|-------------|--------|
| Detection pipeline (structured events) | `pipeline/` + committed `data/events/output.jsonl` |
| Event ingest API | `POST /events/ingest` |
| Live metrics | `GET /stores/{id}/metrics` |
| Funnel (session-based) | `GET /stores/{id}/funnel` |
| Heatmap | `GET /stores/{id}/heatmap` |
| Anomalies | `GET /stores/{id}/anomalies` |
| Health + observability | `GET /health`, JSON logs (`trace_id`, latency) |
| Live dashboard | `/` (React, polls + WebSocket) |
| **DESIGN.md** | Architecture, event flow, DB, AI decisions |
| **CHOICES.md** | Model & API trade-offs (accepted vs rejected AI suggestions) |
| Containerized run | This Docker Space (port **7860**) |
| Tests | `tests/` (pytest) |

**Acceptance gate checklist**

- [x] Container starts without manual steps  
- [x] `/stores/ST1008/metrics` returns valid JSON  
- [x] Pipeline produced structured events (`output.jsonl`)  
- [x] DESIGN.md + CHOICES.md present  
- [x] Stable boot (pre-ingested events; no CCTV in public Space)

---

## What is *not* in this Space (by design)

| Excluded | Reason |
|----------|--------|
| Raw CCTV `.mp4` | Challenge licence — no public redistribution |
| Full `docker compose` | HF runs **one** Docker image (API + UI combined here) |
| Parent-folder POS CSV | Discovery configs committed under `configs/generated/` |

Full local run with videos: clone **private Git** repo + `docker compose up` (see submission README).

---

## Architecture (summary)

```
CCTV (local only) → discover_* → YOLOv8n + ByteTrack → output.jsonl
    → POST /events/ingest → SQLite → metrics | funnel | heatmap | anomalies
    → React dashboard + WebSocket /ws/metrics
```

**Store ID** `ST1008` is discovered from POS data — not hardcoded in pipeline logic.

**North-star metric:** offline conversion = purchasing sessions ÷ unique visitor sessions (staff excluded).

Details: see **DESIGN.md** and **CHOICES.md** in this repo.

---

## API quick test

```bash
curl -s https://SandeepChakka-store-intelligence.hf.space/health
curl -s https://SandeepChakka-store-intelligence.hf.space/stores/ST1008/metrics
```

---

## Engineering highlights (evaluators)

1. **Discovery-driven config** — `scripts/discover_*.py` → `configs/generated/*.json` (camera roles, layout, POS schema).  
2. **Session funnel** — re-entry handled via `session_id`; no naive event-only counting.  
3. **Staff heuristics** — persistence + multi-zone movement; `is_staff` on events.  
4. **POS window** — 5-minute conversion after billing-zone visit (`CHOICES.md`).  
5. **CPU profile** — YOLOv8**n**, frame stride 8, i5-friendly; optional full pipeline locally.  
6. **Idempotent ingest** — `event_id` deduplication.  
7. **Historical clips** — analytics window uses **event timestamps** (Apr 2026), not wall-clock “today”.

---

## Known demo behaviors (not bugs)

| Observation | Explanation |
|---------------|-------------|
| “Current visitors” may be 0 | Clips are historical; not live CCTV on HF |
| Conversion 0% possible | POS timestamps vs clip window alignment |
| STALE_FEED suppressed for old events | `feed_freshness.py` uses clip date range |

---

## Local reproduction (reviewers)

```bash
git clone <your-private-repo>
cd store-intelligence
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
python scripts/discover_all.py
python pipeline/run_pipeline.py --frame-stride 8 --max-frames 600
export PYTHONPATH=.
uvicorn backend.main:app --port 8000
# dashboard: cd dashboard && npm install && npm run dev
```

Or: `docker compose up --build` from repo (two services: API + Vite dev).

---

## Author

**Sandeep Chakka** — Purplle Tech Challenge 2026, Round 2  
Private Git submission + this public **API/dashboard demo** Space.
