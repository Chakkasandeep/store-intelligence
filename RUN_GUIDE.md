# Run Guide — Local First, Then Docker (Multi-Store Upgrade)

This guide provides instructions for setting up, running, testing, and containerizing the Store Intelligence System supporting both Store 1 (`ST1008`) and Store 2 (`ST_STORE2`).

The system uses **SQLite** (a single file at `data/store_intel.db`), which is automatically created and bootstrapped on first start. No external SQL server is required.

### Directory Structure Requirements

Ensure your workspace directory layout matches this structure:
```
store_intelligence/ (Parent Workspace)
├── Store 1/
│   ├── CAM 1 - zone.mp4
│   ├── CAM 2 - zone.mp4
│   ├── CAM 3 - entry.mp4
│   ├── CAM 5 - billing.mp4
│   └── Store 1 - layout.png
├── Store 2/
│   ├── billing_area.mp4
│   ├── entry 1.mp4
│   ├── entry 2.mp4
│   ├── zone.mp4
│   └── store 2 - layout.png
├── Brigade_Bangalore_10_April_26 (1)bc6219c.csv
├── POS - sample transactionsb1e826f.csv
├── sample_eventsbe42122.jsonl
└── store-intelligence/  (This codebase repository)
```

---

## Part A — Local Run Setup (Do This First)

Open **PowerShell** or Command Prompt and navigate to the project directory:

```powershell
cd "C:\Users\chakk_jvzpsux\OneDrive\Desktop\store_intelligence\store-intelligence"
```

### A1. Create Python Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*Note: If script execution is blocked on Windows, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` and activate again.*

### A2. Install Python Dependencies
```powershell
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
*Note: The first install downloads PyTorch + YOLOv8 weights and may take 5–10 minutes.*

### A3. Run Store Discovery
Analyze video features, copy layout maps, and parse POS transaction CSVs to generate config JSON files:
```powershell
python scripts/discover_all.py
```
This command generates the store-specific config subdirectories under `configs/generated/ST1008/` and `configs/generated/ST_STORE2/`.

### A4. Run Video Tracking Pipeline (CPU-Friendly Profile)
Process clips using the YOLOv8 tracker to generate behavior events:
```powershell
# Run tracking for Store 1 (ST1008)
python pipeline/run_pipeline.py --store-id ST1008 --frame-stride 8 --max-frames 600

# Run tracking for Store 2 (ST_STORE2)
python pipeline/run_pipeline.py --store-id ST_STORE2 --frame-stride 8 --max-frames 600
```
*This outputs `output.jsonl` event streams in `data/events/ST1008/` and `data/events/ST_STORE2/`.*

### A5. Run Automated Tests
Execute the pytest suite to verify metrics calculations, re-entry session logic, health staleness, and the legacy schema normalizer:
```powershell
python -m pytest tests/ -v
```
All tests should pass successfully.

### A6. Start backend API (Terminal 1)
```powershell
$env:PYTHONPATH="."
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Verify the API Swagger documentation is running by navigating to **http://127.0.0.1:8000/docs** in your browser.

### A7. Start Dashboard (Terminal 2 — New PowerShell)
```powershell
cd dashboard
npm install
npm run dev
```
Open **http://localhost:5173** to view the live dashboard. Select different stores (`ST1008` vs `ST_STORE2`) from the dropdown in the sidebar to toggle metrics and heatmaps immediately.

---

## Part B — Docker Containerization (Reviewer Gate)

Reviewers run the application inside Docker containers. Follow these steps to verify it runs seamlessly.

### B1. Build and Start Services
Make sure Docker Desktop is active, then run:
```powershell
docker compose up --build
```
This builds the API image, starts the Node.js dashboard container, and initializes the environment. 

*Note: Since pre-built event output files already exist locally in `data/events/`, Docker Compose will skip running the slow object detection pipeline, launching the entire system in under 2 minutes.*

### B2. API Endpoint Verification
With Docker Compose active, test these endpoints directly in your browser or terminal:

```powershell
# Service health status
Invoke-RestMethod http://localhost:8000/health

# Store 1 metrics
Invoke-RestMethod http://localhost:8000/stores/ST1008/metrics

# Store 2 metrics
Invoke-RestMethod http://localhost:8000/stores/ST_STORE2/metrics

# Session funnel
Invoke-RestMethod http://localhost:8000/stores/ST1008/funnel

# Heatmap zones
Invoke-RestMethod http://localhost:8000/stores/ST1008/heatmap
```

---

## Part C — Camera Role Deduction Verification

The role classification of cameras is determined by visual inspection and hardcoded as overrides in discovery to resolve heuristic errors. 

| Store | Video File | Audited Role | Bounding Box/Centroid Logic |
|-------|------------|--------------|-----------------------------|
| **Store 1** | `CAM 3 - entry.mp4` | `ENTRY_CAMERA` | Tracks crossings of inbound line `y ≈ 0.55`. |
| **Store 1** | `CAM 5 - billing.mp4` | `BILLING_CAMERA` | Tracks billing queues and counter presence. |
| **Store 1** | `CAM 1 - zone.mp4` | `MAIN_FLOOR_CAMERA` | Tracks skincare brand wall dwells. |
| **Store 1** | `CAM 2 - zone.mp4` | `MAIN_FLOOR_CAMERA` | Tracks makeup display aisles. |
| **Store 2** | `entry 1.mp4` | `ENTRY_CAMERA` | Tracks primary mall doorway entries/exits. |
| **Store 2** | `entry 2.mp4` | `ENTRY_CAMERA` (Overlap) | Secondary entry; merged by Re-ID to avoid duplicate sessions. |
| **Store 2** | `billing_area.mp4` | `BILLING_CAMERA` | Tracks queue abandonment and cash desk dwells. |
| **Store 2** | `zone.mp4` | `MAIN_FLOOR_CAMERA` | Tracks Pilgrim skincare center aisle dwells. |

### Verification check:
1. Inspect `configs/generated/{store_id}/camera_profile.json`.
2. Confirm `"role": "billing"` is assigned to `CAM 5 - billing.mp4` (Store 1) and `billing_area.mp4` (Store 2).
3. Confirm `"role": "entry"` is assigned to `CAM 3 - entry.mp4` (Store 1) and `entry 1.mp4` / `entry 2.mp4` (Store 2).
4. Run `python scripts/count_events.py` to check that the pipeline event counts match video observations within a reasonable error margin.
