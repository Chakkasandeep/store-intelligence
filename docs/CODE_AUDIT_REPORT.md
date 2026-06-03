# Code Audit Report

**Generated:** 2026-06-03  
**Repository:** `store-intelligence/`  
**Legend:** **KEEP** · **MODIFY** · **REWRITE** · **DELETE**

---

## 1. Executive summary

The backend API layer is **largely reusable** and already exposes all required endpoints. The **discovery layer and pipeline paths are obsolete** relative to the new `Store 1/` / `Store 2/` dataset layout. The **dashboard is already trimmed** to challenge pages. Primary gaps: multi-store config, billing camera mapping, `BILLING_QUEUE_ABANDON` emission, `ZONE_EXIT`, sample-event normalization, and stale generated artifacts.

---

## 2. Backend (`backend/`)

| File | Verdict | Rationale |
|------|---------|-----------|
| `main.py` | **KEEP** | All 6 required routes + WebSocket; structured logging |
| `schemas.py` | **MODIFY** | Align docs with dual schema; optional ingest adapter types |
| `ingestion.py` | **MODIFY** | Add normalizer path for legacy/sample JSONL shapes |
| `sessions.py` | **MODIFY** | Handle `REENTRY`, `ZONE_EXIT`, queue abandon session flags |
| `metrics.py` | **KEEP** | Staff exclusion, queue metrics — needs abandon events to populate |
| `funnel.py` | **KEEP** | Session-based funnel |
| `heatmap.py` | **MODIFY** | Dynamic zones per store from layout config |
| `anomalies.py` | **KEEP** | Queue spike, conversion drop logic |
| `health.py` | **MODIFY** | Multi-store `stores[]` from config registry |
| `bootstrap.py` | **MODIFY** | Multi-store bootstrap; refresh discovery on dataset change |
| `config.py` | **REWRITE** | Replace single `store_id()` with config-driven registry |
| `models.py` | **KEEP** | SQLite schema adequate |
| `db.py` | **KEEP** | |
| `analytics_window.py` | **KEEP** | |
| `feed_freshness.py` | **KEEP** | STALE_FEED support |
| `logging_setup.py` | **KEEP** | |
| `static_ui.py` | **KEEP** | Serves built dashboard |
| `__init__.py` | **KEEP** | |

### Dead / unused backend patterns

- None critical; WebSocket is used by dashboard `useLiveMetrics`

---

## 3. Pipeline (`pipeline/`)

| File | Verdict | Rationale |
|------|---------|-----------|
| `run_pipeline.py` | **MODIFY** | Missing `ZONE_EXIT`, `BILLING_QUEUE_ABANDON`; hardcoded entry line; single-store loop |
| `emit.py` | **MODIFY** | `clip_base_timestamp()` hardcoded 2026-04-10 — read from OSD or config |
| `zones.py` | **REWRITE** | ROIs must load from per-store layout JSON, not `rois_for_role()` constants |
| `config_loader.py` | **REWRITE** | `CCTV Footage/` path obsolete; need `stores/{id}/footage/` |
| `reid.py` | **KEEP** | Cross-camera dedup still valid |
| `staff.py` | **KEEP** | Heuristic staff exclusion |
| `__init__.py` | **KEEP** | |
| `run.sh` | **MODIFY** | Update paths and multi-store args |

---

## 4. Scripts (`scripts/`)

| File | Verdict | Rationale |
|------|---------|-----------|
| `discover_cameras.py` | **REWRITE** | Points to `CCTV Footage/`; wrong billing assignment; no Store 2 |
| `discover_layout.py` | **MODIFY** | Support Store 1 + Store 2 PNGs; per-store zone templates |
| `discover_pos.py` | **MODIFY** | Already flexible glob; add Store 2 POS when available |
| `discover_all.py` | **MODIFY** | Force refresh flag; don’t skip when dataset changes |
| `analyze_videos.py` | **KEEP** | Screenshot utility |
| `count_events.py` | **KEEP** | |
| `_audit_cameras_temp.py` | **DELETE** | Temporary audit script after merge into discover |
| `check_api.cmd` | **KEEP** | |
| `prepare_hf_space.ps1` | **MODIFY** | Update HF deploy assumptions |

---

## 5. Configs & data

| Path | Verdict | Rationale |
|------|---------|-----------|
| `configs/generated/camera_profile.json` | **DELETE → regenerate** | ST1008, 5-camera `CCTV Footage` paths — **wrong** |
| `configs/generated/store_layout.json` | **DELETE → regenerate** | Single-store; wrong billing cam map |
| `configs/generated/pos_mapping.json` | **MODIFY** | Refresh from Brigade CSV path |
| `configs/generated/pos_transactions_derived.csv` | **MODIFY** | Regenerate |
| `data/events/output.jsonl` | **DELETE → regenerate** | 69-event demo; missing EXIT abandon types |
| `data/discovery/video_features.json` | **DELETE → regenerate** | Old 5-cam features |
| `data/discovery/screenshots/CAM_*` | **DELETE → regenerate** | Old filenames |
| `data/store_intel.db` | **DELETE** (gitignore) | Dev artifact |
| `data/layout/image1.png` | **MODIFY** | Replace with `Store 1 - layout.png` copy |
| `yolov8n.pt` | **KEEP** | Model weights |

---

## 6. Dashboard (`dashboard/src/`)

| File | Verdict | Rationale |
|------|---------|-----------|
| `App.tsx` | **KEEP** | Only Dashboard, Heatmap, Funnel, Anomalies, Health |
| `pages/*.tsx` | **KEEP** | Challenge-aligned |
| `config.ts` | **MODIFY** | Multi-store selector from env or API |
| `api/client.ts`, `normalize.ts` | **KEEP** | |
| `hooks/useLiveMetrics.ts` | **KEEP** | Live metrics bonus |
| `components/*` | **KEEP** | No vanity pages detected |
| `dashboard/dist/` | **DELETE** from VCS | Build artifact (optional) |
| `dashboard/node_modules/` | **DELETE** from VCS | Already gitignored |

**Unused UI pages:** None — prior cleanup already done.

---

## 7. Docker & deploy

| File | Verdict | Rationale |
|------|---------|-----------|
| `docker-compose.yml` | **MODIFY** | Mount `../Store 1`, `../Store 2` or unified `data/stores/` |
| `docker/Dockerfile` | **MODIFY** | Discovery on startup optional |
| `docker/entrypoint.sh` | **MODIFY** | Run discovery if configs stale |
| `deploy/hf/*` | **MODIFY** | ST1008-only docs |
| `.dockerignore` (parent) | **MODIFY** | Exclude large MP4 from image; mount volumes |

---

## 8. Documentation

| File | Verdict | Rationale |
|------|---------|-----------|
| `README.md` | **REWRITE** | New dataset layout, 2 stores, discovery commands |
| `DESIGN.md` | **REWRITE** | Architecture for multi-store config |
| `CHOICES.md` | **REWRITE** | Camera billing correction, schema adapter |
| `COMMANDS.md` | **REWRITE** | |
| `RUN_GUIDE.md` | **MODIFY** | Very long — trim outdated CCTV Footage sections |
| `EVALUATION_ALIGNMENT.md` | **MODIFY** | Update pass/fail after refresh |
| `SUBMISSION_CHECKLIST.md` | **MODIFY** | |
| `IMPLEMENTATION_PLAN.md` | **DELETE** or archive | Superseded by this audit |
| `docs/CAMERA_ANALYSIS.md` | **MODIFY** | Merge into CAMERA_REFRESH_REPORT |
| `docs/STORE_LAYOUT_ANALYSIS.md` | **MODIFY** | Merge into LAYOUT_DIFF |
| `docs/DATA_ANALYSIS.md` | **MODIFY** | Superseded by DATASET_REFRESH |
| `docs/DESIGN.md`, `docs/CHOICES.md` | **DELETE** | Duplicates root — consolidate |
| `docs/_extracted/*.txt` | **KEEP** | PDF extracts for reference |
| New audit reports | **KEEP** | This audit set |

---

## 9. Tests (`tests/`)

| File | Verdict | Rationale |
|------|---------|-----------|
| `test_api.py` | **MODIFY** | Store 1 ST1008 + Store 2 fixtures |
| `test_metrics.py` | **MODIFY** | Abandon events, empty store |
| `test_anomalies.py` | **KEEP** | |
| `test_pipeline.py` | **REWRITE** | New camera roles, ZONE_EXIT, abandon |
| `conftest.py` | **MODIFY** | Multi-store test DB |

---

## 10. Duplicate / obsolete logic

| Pattern | Location | Issue |
|---------|----------|-------|
| Single `ST1008` default | `config.py`, `dashboard/config.ts`, docker env | Blocks Store 2 |
| `footage_path()` | `config_loader.py` | Hardcoded `CCTV Footage` |
| `discover_all` skip-if-exists | `discover_all.py` | Prevents dataset refresh |
| Billing on CAM 2 | `camera_profile.json` | Contradicts new footage |
| Two DESIGN/CHOICES | root + `docs/` | Doc drift |

---

## 11. Hardcoded assumptions (must remove)

1. `FOOTAGE = ROOT / "CCTV Footage"`
2. `clip_base_timestamp` → `2026-04-10 20:09 UTC`
3. `rois_for_role()` zone polygons
4. `discover_all` early return if configs exist
5. `VITE_STORE_ID=ST1008` as only store
6. Committed `output.jsonl` as production data

---

## 12. Reuse scorecard

| Component | Reuse % | Notes |
|-----------|---------|-------|
| FastAPI + analytics | **85%** | Core business logic solid |
| YOLO + ByteTrack pipeline | **70%** | Event emission gaps |
| Discovery scripts | **40%** | Path + role logic outdated |
| Dashboard | **90%** | Already minimal |
| Docker shell | **60%** | Volume paths |
| Tests | **50%** | Need new fixtures |

---

## 13. Proposed deletions (post-approval)

```
configs/generated/camera_profile.json    # regenerate
configs/generated/store_layout.json      # regenerate
data/events/output.jsonl                 # regenerate
data/discovery/video_features.json       # regenerate
data/discovery/screenshots/CAM_*.jpg     # old set
scripts/_audit_cameras_temp.py           # temp
IMPLEMENTATION_PLAN.md                   # optional archive
docs/DESIGN.md, docs/CHOICES.md          # duplicate
```

**Do not delete:** `backend/*`, `pipeline/reid.py`, `pipeline/staff.py`, dashboard pages.

---

## 14. Approval gate

No refactor code changes until stakeholder approves this audit and the companion compliance report.
