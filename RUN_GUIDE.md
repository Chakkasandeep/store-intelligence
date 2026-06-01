# Run Guide — Local First, Then Docker

**You do NOT need MySQL, PostgreSQL, or any SQL server.**  
This project uses **SQLite** (a single file: `data/store_intel.db`). It is created automatically on first API start.

**Parent folder must contain:**

- `CCTV Footage/` (CAM 1.mp4 … CAM 5.mp4)
- `Brigade_Bangalore_10_April_26 (1)bc6219c.csv`
- `store-intelligence/` (this project)

---

## Part A — Install once (Windows)

### A1. Python 3.11+ (required)

1. Download: https://www.python.org/downloads/
2. During install, check **“Add python.exe to PATH”**.
3. Verify in **PowerShell**:

```powershell
python --version
pip --version
```

Expected: `Python 3.11.x` or `3.12.x` (not 2.x).

---

### A2. Node.js 20+ (required for dashboard)

1. Download: https://nodejs.org/ (LTS)
2. Verify:

```powershell
node --version
npm --version
```

---

### A3. Docker Desktop (required only for Docker section)

1. Download: https://www.docker.com/products/docker-desktop/
2. Install and **start Docker Desktop** (whale icon in system tray).
3. Verify:

```powershell
docker --version
docker compose version
```

**No separate MySQL/SQL container** — only the API image + optional Node dashboard container.

---

### A4. Git (optional)

Only if you clone the repo. Not required to run from folder.

---

## Part B — Local run (do this first)

Open **PowerShell**. Replace the path if your Desktop folder name differs.

```powershell
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\Apex Retail\store-intelligence"
```

### B1. Create virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Prompt should show `(.venv)`.

---

### B2. Install Python packages

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

First install may take **10–20 minutes** (downloads PyTorch + YOLO). That is normal on i5.

---

### B3. Generate configs from your data (no hardcoding)

```powershell
python scripts/discover_all.py
```

**Check:** these files exist:

- `configs\generated\pos_mapping.json`
- `configs\generated\camera_profile.json`
- `configs\generated\store_layout.json`

---

### B4. Run detection pipeline (CPU-friendly on Intel i5)

```powershell
New-Item -ItemType Directory -Force -Path data\events
python pipeline/run_pipeline.py --frame-stride 8 --max-frames 600 --output data\events\output.jsonl
```

| Profile | Command | Time on i5 (approx.) |
|---------|---------|----------------------|
| **Recommended** | `--frame-stride 8 --max-frames 600` | 15–25 min (5 clips) |
| Quick test (1 clip worth) | add `--max-frames 200` | ~5 min |
| Full quality (slow) | omit `--max-frames` | 1–3+ hours |

**Check:** `data\events\output.jsonl` exists and is not empty:

```powershell
Get-Item data\events\output.jsonl | Select-Object Length
Get-Content data\events\output.jsonl -TotalCount 2
```

Each line must be JSON with `"event_id"`, `"event_type"`, `"store_id": "ST1008"`.

---

### B5. Start backend API (Terminal 1)

Keep venv activated:

```powershell
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\Apex Retail\store-intelligence"
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
$env:EVENTS_JSONL = "data\events\output.jsonl"
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**Check:**

- Browser: http://127.0.0.1:8000/docs  
- No crash on startup (bootstrap ingests events once).

SQLite file appears at: `data\store_intel.db` (automatic — **no MySQL**).

---

### B6. Start dashboard (Terminal 2 — new PowerShell)

```powershell
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\Apex Retail\store-intelligence\dashboard"
copy .env.example .env
npm install
npm run dev
```

**Check:**

- Browser: http://localhost:5173  
- Top/nav should show connection status (WebSocket or polling).

Dashboard talks to API via Vite proxy (`/api` → port 8000). WebSocket uses `ws://localhost:8000/ws/metrics?store_id=ST1008`.

---

### B7. Verify backend + frontend (copy-paste checks)

With API running (Terminal 1):

```powershell
# Health
Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json

# Metrics (store ID from your CSV)
Invoke-RestMethod http://127.0.0.1:8000/stores/ST1008/metrics | ConvertTo-Json

# Funnel
Invoke-RestMethod http://127.0.0.1:8000/stores/ST1008/funnel | ConvertTo-Json

# Heatmap
Invoke-RestMethod http://127.0.0.1:8000/stores/ST1008/heatmap | ConvertTo-Json

# Anomalies
Invoke-RestMethod http://127.0.0.1:8000/stores/ST1008/anomalies | ConvertTo-Json
```

**Expected (roughly):**

| Endpoint | OK if |
|----------|--------|
| `/health` | `"status": "ok"` or `"degraded"` (not `unavailable`) |
| `/metrics` | `unique_visitors` ≥ 0, `conversion_rate` between 0 and 1 |
| `/funnel` | 4 stages: Entry → Zone Visit → Billing → Purchase |
| `/heatmap` | `zones` array (may be empty if few zone events) |
| `/anomalies` | `anomalies` array (may be empty) |

**Dashboard OK if:**

- Numbers on home page change or show zeros (not “Failed to fetch” forever).
- Browser DevTools → Network: `/api/stores/ST1008/metrics` returns **200**.

---

### B8. Run tests (optional but recommended)

```powershell
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\Apex Retail\store-intelligence"
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
pip install -r requirements-dev.txt
pytest tests\ -v
```

Expected: **12 passed**.

---

## Part C — Docker run (after local works)

### C1. Prerequisites

1. **Docker Desktop running** (green / running state).
2. **Local pipeline already produced** `store-intelligence\data\events\output.jsonl`  
   → Docker will **skip** the long pipeline on first start if this file exists.

---

### C2. Build and start

```powershell
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\Apex Retail\store-intelligence"
docker compose up --build
```

First time:

- Builds API image (may take **15–30 min** — downloads Python deps).
- If `data\events\output.jsonl` is missing, container runs pipeline (**15–25 min on i5**) before API is up.
- Dashboard container runs `npm install` then Vite on port **5173**.

**URLs:**

| Service | URL |
|---------|-----|
| API docs | http://localhost:8000/docs |
| Dashboard | http://localhost:5173 |
| Health | http://localhost:8000/health |

Stop: `Ctrl+C`, then:

```powershell
docker compose down
```

---

### C3. Verify Docker (same as local)

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/stores/ST1008/metrics
```

Open http://localhost:5173 — dashboard uses `VITE_API_URL=http://api:8000` inside compose; your browser still uses **localhost:5173** and proxies to the API.

---

## Part D — What evaluators do (~10 minutes)

From the evaluation PDF (not a full re-train on your machine):

| Time | Action |
|------|--------|
| 2 min | `docker compose up` → API responds |
| 2 min | Open `output.jsonl`, check event schema |
| 3 min | Hit `/metrics`, `/funnel`, etc. |
| 2 min | Read DESIGN.md, CHOICES.md |
| 1 min | Score |

**Tip:** Ship `data/events/output.jsonl` from your i5 run so Docker starts API in **under 2 minutes**.

---

## Part E — Troubleshooting

### `python` not found

- Reinstall Python with “Add to PATH”, or use `py -3.11` instead of `python`.

### `pip install` fails on torch

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### Pipeline very slow / out of memory on i5

Use smaller run:

```powershell
python pipeline/run_pipeline.py --frame-stride 10 --max-frames 300 --output data\events\output.jsonl
```

### API starts but metrics all zero

- `output.jsonl` empty or not ingested → restart API with `$env:EVENTS_JSONL = "data\events\output.jsonl"`.
- Delete `data\store_intel.db` and restart API to re-ingest.

### Dashboard `ECONNREFUSED` in Vite log (most common error)

**Meaning:** `npm run dev` is running, but the **API is NOT running** on port **8000**.  
The dashboard proxy tries `http://127.0.0.1:8000` → connection refused.

**This is NOT a code bug.** You need **two windows open at the same time**.

**Quick check (cmd):**

```cmd
cd store-intelligence
scripts\check_api.cmd
```

If it says **FAILED**, start the API before the dashboard.

**Fix — Window 1 (API) — leave this open:**

```cmd
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\Apex Retail\store-intelligence"
venv\Scripts\activate
set PYTHONPATH=.
set EVENTS_JSONL=data\events\output.jsonl
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Wait for: `Application startup complete`

**Test in browser BEFORE starting dashboard:**  
http://127.0.0.1:8000/health — must load JSON, not “can’t connect”.

**Window 2 (dashboard) — only after health works:**

```cmd
cd store-intelligence\dashboard
npm run dev
```

**Order matters:** API first → health URL works → then `npm run dev`.

**Do not use `--reload`** on uvicorn (it can restart and cause `ECONNRESET`).

**Old Vite errors:** Lines from 7:02–7:09 pm are from when API was off. Clear the terminal or ignore after API is up; new errors should stop.

### Dashboard “Failed to fetch” / `ECONNRESET` in Vite log

**Meaning:** API was running but **restarted or crashed** (often `--reload` watching `venv`).

**Fix:** Start the API in a **separate** cmd window and leave it open (no `--reload`):

```cmd
cd store-intelligence
venv\Scripts\activate
set PYTHONPATH=.
set EVENTS_JSONL=data\events\output.jsonl
uvicorn backend.main:app --reload --port 8000
```

Then refresh http://localhost:5173. Vite proxy errors should stop.

### `STALE FEED` / “74482 minutes” on Anomalies page

**Meaning (false alarm):** Events use **CCTV clip time** (10-Apr-2026 ~20:09). Your PC date is later, so old logic thought the feed was ~52 days “stale”.

**Fix:** Code now ignores wall-clock stale for **historical clip days**. Restart API after `git pull`/update. You still need the API running for real metrics.

### Dashboard “Failed to fetch” (other)

| Check | Fix |
|-------|-----|
| API not running | Start Terminal 1 (`uvicorn` on 8000) |
| Wrong store ID | `.env` → `VITE_STORE_ID=ST1008` |
| CORS / proxy | Use `npm run dev` (not `preview`) so `/api` proxy works |
| WebSocket only | Metrics still load via 10s polling if WS fails |

### Docker: API never becomes ready

- Wait if pipeline is running (no `output.jsonl` yet).
- Or pre-create events locally (Part B4), then `docker compose up` again.

### Docker: port already in use

```powershell
# Find process on 8000
netstat -ano | findstr :8000
# Stop other service or change ports in docker-compose.yml
```

### No MySQL / SQL Server needed?

**Correct.** Only file: `store-intelligence\data\store_intel.db` (SQLite). Docker compose does **not** start MySQL.

---

## Part F — Quick command lock (copy order)

**PowerShell:**

```powershell
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\Apex Retail\store-intelligence"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/discover_all.py
mkdir data\events 2>$null
python pipeline/run_pipeline.py --frame-stride 8 --max-frames 600 --output data\events\output.jsonl
python scripts/count_events.py

# Terminal 1 — API (no --reload on Windows)
$env:PYTHONPATH="."
$env:EVENTS_JSONL="data\events\output.jsonl"
uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Dashboard
cd dashboard
copy .env.example .env
npm install
npm run dev
```

**Command Prompt (cmd):** use `venv\Scripts\activate`, `set PYTHONPATH=.`, `set EVENTS_JSONL=data\events\output.jsonl` instead of `$env:...`.

**Docker (after local works):**

```powershell
cd store-intelligence
docker compose up --build
```

---

## Part G — How to check if data is correct (video vs events)

Evaluators do the same thing: **watch a clip**, **count people**, **compare to your ENTRY events**. You do not need perfect counts — “reasonable” is enough.

### Step 1 — Know which camera is “entry”

```cmd
type configs\generated\camera_profile.json
```

Look for `"role": "entry"` — usually **CAM 3.mp4** → `CAM_ENTRY_01`.

### Step 2 — Count people manually (5–10 minutes)

1. Open `CCTV Footage\CAM 3.mp4` in VLC / Movies & TV.
2. Play at **0.5x speed** near the door.
3. Count **inbound entries** (customer crosses into the store):
   - 3 people enter together → expect **3 ENTRY events** (not 1).
4. Optionally note **exits** and **people at billing** on CAM 2 or CAM 5.

Write your counts on paper, e.g. `ENTRY ≈ 5`, `EXIT ≈ 4`.

### Step 3 — Count what the pipeline produced

```cmd
cd store-intelligence
venv\Scripts\activate
python scripts\count_events.py
```

Example output:

```
By event_type:
  ENTRY: 5
  ZONE_ENTER: 40
  ...
```

### Step 4 — Compare

| Manual (video) | Pipeline (`count_events.py` or API) | OK? |
|----------------|-------------------------------------|-----|
| ENTRY ≈ 5 | ENTRY: 5 | Good |
| ENTRY ≈ 8 | ENTRY: 2 | Re-run pipeline or tune stride |
| Many people, ENTRY: 0 | Wrong camera role — re-run `discover_all.py` |

**API check (same numbers after ingest):**

```cmd
curl http://127.0.0.1:8000/stores/ST1008/metrics
```

`unique_visitors` should be in the same ballpark as unique visitors from events (not necessarily equal to ENTRY count because of re-entry and zones).

**Inspect raw events:**

```cmd
findstr ENTRY data\events\output.jsonl | more
```

Or open `data\events\output.jsonl` in VS Code and search `"event_type": "ENTRY"`.

### Step 5 — What “good enough” means (evaluation PDF)

- Entry/exit **close** to manual count (not exact).
- Events have `event_id`, `store_id`, `visitor_id`, `confidence`, `is_staff`.
- Staff not counted in customer metrics (`is_staff: true` excluded).
- Document assumptions in `CHOICES.md` if counts are off (occlusion, stride, short clip).

### Why some dashboard numbers are still zero (normal)

| Metric | Often zero because |
|--------|-------------------|
| **Current Visitors** | Historical clips — not live today |
| **Conversion %** | POS times (e.g. 12:15–20:25) vs session time (~20:09) — strict 5‑minute rule |
| **Abandonment %** | No `BILLING_QUEUE_ABANDON` events in file |

**Today's Visitors** and **Queue Depth** non-zero means the system is working.

---

## Part H — PostgreSQL: do you need it?

| Database | Required? |
|----------|-----------|
| **SQLite** (`data/store_intel.db`) | **Yes — default, already used** |
| **PostgreSQL** | **No — optional only** |
| **MySQL** | **No** |

You do **not** install PostgreSQL for this challenge.  
Optional: set env `DATABASE_URL=postgresql+asyncpg://...` only if you choose Postgres in `CHOICES.md` — not needed for submission.

---

## Part I — After everything works: submission steps

Follow the **Purplle problem statement** acceptance gate and evaluation flow.

### 1. Final local checks

```cmd
venv\Scripts\activate
set PYTHONPATH=.
pytest tests\ -v
python scripts\count_events.py
```

- [ ] Tests pass (12 tests).
- [ ] `data\events\output.jsonl` exists and is not empty.
- [ ] Manual ENTRY count ≈ pipeline ENTRY count (Part G).

### 2. Docker acceptance gate (reviewers run this)

```cmd
cd store-intelligence
docker compose up --build
```

Wait until:

- http://localhost:8000/health → OK  
- http://localhost:8000/stores/ST1008/metrics → JSON with numbers  
- http://localhost:5173 → dashboard (optional bonus)

**Tip:** Keep `data\events\output.jsonl` from your local pipeline run so Docker does not wait 20+ minutes on first start.

### 3. Documentation (required, non-trivial)

- [ ] `DESIGN.md` — architecture + “AI-Assisted Decisions”
- [ ] `CHOICES.md` — model choice, schema, API choice
- [ ] `README.md` — how to run pipeline + API
- [ ] Test files have `# PROMPT:` / `# CHANGES MADE:` headers

### 4. Git submission

- [ ] Push to **private** repo (invite reviewer per challenge email).
- [ ] Include `CCTV Footage` **or** clear README path to data (if rules allow — follow challenge email).
- [ ] Do **not** commit `.venv`, `data/store_intel.db` if huge (optional: commit `output.jsonl` for fast Docker).

### 5. What reviewers do (~10 minutes)

| Time | They check |
|------|------------|
| 2 min | `docker compose up`, API responds |
| 2 min | Event schema in `output.jsonl` |
| 3 min | `/metrics`, `/funnel`, `/anomalies` |
| 2 min | DESIGN.md + CHOICES.md |
| 1 min | Score |

### 6. After you submit

- Prepare to explain **your** ENTRY counting, staff exclusion, and why conversion uses a 5‑minute POS window.
- Follow-up questions come from **your code** — read `CHOICES.md` once before the interview.

---

## Checklist before submission

- [ ] `configs/generated/*.json` from **your** CSV + CCTV (not hand-edited store IDs)
- [ ] `data/events/output.jsonl` has events
- [ ] `python scripts/count_events.py` — ENTRY close to manual video count
- [ ] http://localhost:8000/stores/ST1008/metrics returns JSON (not all zeros for visitors)
- [ ] http://localhost:5173 dashboard loads
- [ ] `pytest tests/ -v` passes
- [ ] `docker compose up --build` works with pre-built `output.jsonl`
- [ ] `DESIGN.md` and `CHOICES.md` present and filled in
- [ ] **PostgreSQL not required** — SQLite only unless you documented otherwise

---

**Submit now:** see **[SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md)** (evaluation PDF alignment + Docker commands).

**Related docs:** [COMMANDS.md](COMMANDS.md) · [README.md](README.md) · [docs/PERFORMANCE.md](docs/PERFORMANCE.md) · [docs/CAMERA_ANALYSIS.md](docs/CAMERA_ANALYSIS.md)
