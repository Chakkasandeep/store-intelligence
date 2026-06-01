# Submission Checklist — Evaluation Framework Alignment

Use this **before you submit**. Matches `Assessment Evaluation Framework` acceptance gate + reviewer flow.

**PostgreSQL:** NOT required. SQLite only (`data/store_intel.db`).

---

## Acceptance gate (must pass — or rejected)

| # | Requirement | How reviewer checks | Your command |
|---|-------------|---------------------|--------------|
| 1 | `docker compose up` no manual steps | Runs compose | See **Docker** below |
| 2 | `/metrics` valid JSON | Browser/curl | `curl http://localhost:8000/stores/ST1008/metrics` |
| 3 | Pipeline produces events | `output.jsonl` | `python scripts/count_events.py` |
| 4 | DESIGN.md + CHOICES.md non-trivial | Read files | `DESIGN.md`, `CHOICES.md` in repo root |
| 5 | System stable (no crash) | 2 min smoke test | `pytest tests/ -v` |

---

## Pre-submit verification (local — 15 minutes)

Run from `store-intelligence` folder.

### 1. Events + manual sanity

```cmd
venv\Scripts\activate
set PYTHONPATH=.
python scripts\count_events.py
```

Compare `ENTRY` count to **CAM 3.mp4** (entry camera) — should be roughly close.

### 2. Tests

```cmd
pytest tests\ -v
```

Expected: **12 passed**.

### 3. Start API (Window 1)

```cmd
set EVENTS_JSONL=data\events\output.jsonl
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 4. API smoke (new cmd window)

```cmd
scripts\check_api.cmd
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/stores/ST1008/metrics
curl http://127.0.0.1:8000/stores/ST1008/funnel
curl http://127.0.0.1:8000/stores/ST1008/heatmap
curl http://127.0.0.1:8000/stores/ST1008/anomalies
```

All should return **HTTP 200** and JSON (not “connection refused”).

### 5. Dashboard (Window 2)

```cmd
cd dashboard
npm run dev
```

Open http://localhost:5173 — metrics/funnel should show data (not all zeros for visitors).

**If `ECONNREFUSED` in Vite:** API Window 1 is closed — start uvicorn again.

---

## Docker submission test (what reviewers run)

**Prerequisite:** Docker Desktop running.

**Important:** Build `output.jsonl` locally first so Docker starts API in ~1–2 min (not 20+ min pipeline).

```cmd
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\Apex Retail\store-intelligence"
venv\Scripts\activate
set PYTHONPATH=.
python scripts\discover_all.py
python pipeline\run_pipeline.py --frame-stride 8 --max-frames 600 --output data\events\output.jsonl
```

Then Docker:

```cmd
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\Apex Retail\store-intelligence"

REM Ensure events exist (once) — Docker skips pipeline if file present
dir data\events\output.jsonl

cd ..
docker compose -f store-intelligence/docker-compose.yml down
docker compose -f store-intelligence/docker-compose.yml up --build
```

Or from inside `store-intelligence` (if compose file paths work on your machine):

```cmd
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\Apex Retail\store-intelligence"
docker compose down
docker compose up --build
```

**Note:** Build context is parent folder `Apex Retail/` — `.dockerignore` excludes MP4s and `venv` so build is faster.

Wait until you see API logs: `Application startup complete`.

**Verify (browser or cmd):**

| URL | Expected |
|-----|----------|
| http://localhost:8000/health | `"status":"ok"` or `"degraded"` |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/stores/ST1008/metrics | JSON, `unique_visitors` > 0 |
| http://localhost:5173 | Dashboard (bonus) |

**Stop Docker:**

```cmd
docker compose down
```

### If you see `entrypoint.sh: no such file or directory`

Windows CRLF line endings — **fixed in Dockerfile**. Rebuild API image:

```cmd
docker compose down
docker compose build --no-cache api
docker compose up
```

### If dashboard shows `ENOTFOUND api`

API container crashed first. Fix API, then dashboard will connect.

---

## Scoring map (100 marks) — your project

| Area | Marks | You have |
|------|-------|----------|
| Detection pipeline | 30 | YOLOv8n + events in `output.jsonl`, discovery configs |
| API + business logic | 35 | 6 endpoints, funnel, anomalies, POS load |
| Production | 20 | Docker, logs, pytest, README/RUN_GUIDE |
| Engineering docs | 15 | DESIGN.md, CHOICES.md |
| Dashboard bonus | +10 | React dashboard + WebSocket |

**Integrity:** Metrics computed from DB/events (not hardcoded). Document assumptions in CHOICES.md.

---

## What NOT to put in Docker / Git

### Do NOT bake into Docker image (`.dockerignore` at `Apex Retail/`)

| Exclude | Why |
|---------|-----|
| `CCTV Footage/*.mp4` | Mounted as volume; saves GB of image size |
| `venv/`, `node_modules/` | Rebuilt in container |
| `data/store_intel.db` | Created on API startup |
| `yolov8n.pt` | Re-downloaded if pipeline runs |
| Parent `*.pdf`, `*.csv`, `*.xlsx` | Not needed in API image |

### Do NOT commit to Git (`.gitignore` in `store-intelligence/`)

| Exclude | Why |
|---------|-----|
| `venv/`, `.venv/` | Local only |
| `dashboard/node_modules/` | Run `npm install` |
| `data/store_intel.db` | Regenerated |
| `yolov8n.pt` | Large; downloads automatically |

### DO commit (reviewers need these)

| Include | Why |
|---------|-----|
| All `backend/`, `pipeline/`, `tests/`, `docker/` | Source |
| `DESIGN.md`, `CHOICES.md`, `README.md` | Required |
| `configs/generated/*.json` | Data-driven config |
| `data/events/output.jsonl` | Fast `docker compose` (recommended) |
| `requirements.txt`, `docker-compose.yml` | Run |

### CCTV + POS files (parent folder)

Keep next to repo OR document in README:

- `CCTV Footage/` (5 MP4s)
- `Brigade_Bangalore_*.csv`
- Layout xlsx (optional)

**Do NOT upload CCTV to public Hugging Face** — challenge licence says no redistribution. Use **private Git** only (per problem statement).

---

## Git submit

- [ ] Private **GitHub/GitLab** repo + invite reviewer (email from challenge) — **not public Hugging Face with videos**
- [ ] Repo root = `store-intelligence/` OR monorepo with README paths to `../CCTV Footage/`
- [ ] Do **not** commit `.venv/` or `node_modules/`
- [ ] **Do** commit `data/events/output.jsonl` for fast Docker
- [ ] README points to `RUN_GUIDE.md` and `docker compose up`

---

## Known normal behaviors (not failures)

| Item | OK? |
|------|-----|
| Current visitors = 0 on dashboard | Yes (historical CCTV) |
| Conversion 0% | Yes (POS time vs clip time — document in CHOICES.md) |
| PostgreSQL | Not needed |
| STALE FEED on old builds | Fixed for historical clip dates |

---

## One-page command summary

```cmd
REM === FINAL LOCAL CHECK ===
cd store-intelligence
venv\Scripts\activate
set PYTHONPATH=.
pytest tests\ -v
python scripts\count_events.py
scripts\check_api.cmd

REM === DOCKER (SUBMISSION) ===
docker compose down
docker compose up --build

REM === AFTER VERIFY ===
docker compose down
```

You are ready to submit when: **pytest pass**, **curl metrics OK**, **docker compose up works**, **docs present**.
