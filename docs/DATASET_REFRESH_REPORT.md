# Dataset Refresh Report

**Generated:** 2026-06-03  
**Scope:** Parent workspace `store_intelligence/` + existing `store-intelligence/` application  
**Status:** Discovery only — no code changes applied yet

---

## 1. Executive summary

| Finding | Impact |
|---------|--------|
| New data is organized as **two store folders** (`Store 1/`, `Store 2/`) instead of a flat `CCTV Footage/` directory with `CAM 1.mp4`…`CAM 5.mp4` | Discovery scripts and Docker volume paths are **obsolete** |
| **Store 1** maps to Brigade Bangalore POS (`ST1008`) | Existing `store_layout.json` / POS discovery align with Store 1 only |
| **Store 2** has videos + layout PNG but **no POS CSV** | Conversion metrics for Store 2 need config placeholder or synthetic POS |
| `sample_eventsbe42122.jsonl` uses a **different schema** than the repo’s internal `StoreEvent` model | Ingest will reject sample file without a normalizer |
| Committed `output.jsonl` is a **tiny demo** (69 events, 6 types) from old 5-camera assumptions | Must be regenerated from new footage |

---

## 2. Uploaded asset inventory

| Asset | Location | Role |
|-------|----------|------|
| Store 1 videos (4× MP4) | `../Store 1/` | Brigade Road footage (~10/04/2026 OSD) |
| Store 1 layout PNG | `../Store 1/Store 1 - layout.png` | Floor plan (matches Brigade xlsx) |
| Store 2 videos (4× MP4) | `../Store 2/` | Second store (~03/2026 OSD) |
| Store 2 layout PNG | `../Store 2/store 2 - layout.png` | L-shaped FOH/BOH plan, 19 wall units |
| Brigade POS (full) | `../Brigade_Bangalore_10_April_26 (1)bc6219c.csv` | **ST1008**, 101 line items, 10-Apr-2026 |
| POS sample (simplified) | `../POS - sample transactionsb1e826f.csv` | **ST1008**, subset schema |
| Layout workbook | `../Brigade Road - Store layoutc5f5d56.xlsx` | Embedded PNG in `xl/media/` (sheet cells mostly empty) |
| Sample events | `../sample_eventsbe42122.jsonl` | Reference store **ST1076** / `store_1076` — not ST1008 |
| Challenge PDF | `../Purplle Tech Challenge 2026 _ Round 2 Problem Statement480e74e.pdf` | Canonical API + event catalogue |
| Evaluation PDF | `../Assessment  Evaluation Frameworkb24a398.pdf` | Scoring weights |
| Application | `store-intelligence/` | FastAPI + pipeline + dashboard |

**Not present in upload:** `CCTV Footage/` folder, `store_layout.json` (challenge template), `assertions.py`, 5-store × 3-camera zip described in generic challenge text.

---

## 3. Store 1 — Brigade Road (primary)

### 3.1 Identity

| Field | Value | Confidence |
|-------|-------|------------|
| **Store ID** | `ST1008` | **0.99** (from Brigade POS `store_id`) |
| **Store name** | `Brigade_Bangalore` | **0.99** |
| **City** | Bangalore | **0.99** |
| **Footage date (OSD)** | 10/04/2026 ~20:09–20:11 | **0.95** (from video frames) |
| **POS date** | 10/04/2026 | **0.99** |

### 3.2 Cameras (content-based; filenames ignored for role)

| Source file | Duration | Resolution | Classified role | Confidence | Notes |
|-------------|----------|------------|-----------------|------------|-------|
| `CAM 3 - entry.mp4` | 148 s | 1920×1080 @ ~30fps | **ENTRY_CAMERA** | **0.88** | Glass door, exterior/interior asymmetry; see screenshot |
| `CAM 5 - billing.mp4` | 139 s | 1920×1080 @ ~25fps | **BILLING_CAMERA** | **0.92** | L-shaped POS, scanners — **heuristic wrongly scored as main_floor; visual override** |
| `CAM 1 - zone.mp4` | 140 s | 1920×1080 | **MAIN_FLOOR_CAMERA** | **0.85** | Brand wall + central displays |
| `CAM 2 - zone.mp4` | 126 s | 1920×1080 | **MAIN_FLOOR_CAMERA** | **0.85** | Maybelline/Lakmé aisle — billing score high but no POS in frame |

**Missing vs old repo:** `CAM 4` clip removed (old profile had 5 cameras).  
**Overlap:** Entry (CAM 3) FOV overlaps FOH seen on CAM 1 — expect **OVERLAP_CAMERA** dedup via Re-ID.

### 3.3 Layout assets

| Asset | Zones identifiable | Confidence |
|-------|-------------------|------------|
| `Store 1 - layout.png` | ENTRY (left), FOH, north skincare wall, south makeup wall, fragrance gondola, makeup units, **BILLING** (right), accessories | **0.90** |
| `Brigade Road - Store layoutc5f5d56.xlsx` | Same plan via embedded image | **0.85** |

### 3.4 Functional areas

| Area | Layout evidence | Camera coverage |
|------|-----------------|-----------------|
| **Entry** | Left glass door | CAM 3 |
| **Billing** | Cash counter east wall | CAM 5 (primary); not CAM 2 |
| **Queue** | Floor space in front of counter | CAM 5 |
| **Main floor / zones** | FOH + brand walls + gondola | CAM 1, CAM 2 |

### 3.5 Missing information

- CAD-scale polygon coordinates (layout is image-only; xlsx sheet has no zone table)
- Ground-truth entry/exit counts for accuracy scoring
- Explicit `store_layout.json` from challenge pack
- Camera 4 overlap clip (if evaluators expect 5 feeds)

---

## 4. Store 2 — second location

### 4.1 Identity

| Field | Value | Confidence |
|-------|-------|------------|
| **Store ID** | **UNKNOWN** (no POS file) | — |
| **Proposed ID** | `ST_STORE2` or discover from future POS | **0.40** |
| **Footage date (OSD)** | 08/03/2026 and 29/03/2026 (mixed) | **0.90** |
| **Layout** | Distinct L-shaped store, 19 wall units, 2 gondolas, 4 makeup stations | **0.88** |

### 4.2 Cameras (content-based + visual validation)

| Source file | Duration | Resolution | Classified role | Confidence | Notes |
|-------------|----------|------------|-----------------|------------|-------|
| `entry 1.mp4` | 105 s | 960×? @ 25fps | **ENTRY_CAMERA** | **0.90** | Glass doors, mall threshold (OSD CAM1) |
| `entry 2.mp4` | 85 s | 960×? | **ENTRY_CAMERA** (overlap) | **0.78** | Second entry angle — dual-entry dedup required |
| `billing_area.mp4` | 125 s | 960×? | **BILLING_CAMERA** | **0.93** | Counter + queue — **heuristic misclassified as main_floor** |
| `zone.mp4` | 116 s | 960×? | **MAIN_FLOOR_CAMERA** | **0.91** | Central aisle / Pilgrim skincare (OSD CAM2) |

### 4.3 Layout assets

| Asset | Zones | Confidence |
|-------|-------|------------|
| `store 2 - layout.png` | FOH entrance (bottom), cash counter (rear-center), MK gondolas 1–2, makeup units, wall units 1–19, B.O.H | **0.88** |

### 4.4 Functional areas

| Area | Location on plan | Camera |
|------|------------------|--------|
| **Entry** | Bottom center doors | entry 1, entry 2 |
| **Billing** | Rear-center cash counter | billing_area |
| **Queue** | In front of counter | billing_area |
| **Zones** | Gondolas + wall units + makeup grid | zone |

### 4.5 Missing information

- **POS transactions** (blocks conversion rate for Store 2)
- Store ID and display name
- Whether Store 2 is scored or only Store 1 (evaluation PDF mentions one store in acceptance gate)
- Zone polygon definitions per wall unit (19 units vs 9 zones in Store 1 config)

---

## 5. POS CSV analysis

### Brigade (`Brigade_Bangalore_10_April_26 (1)bc6219c.csv`)

- **Columns:** 40+ retail fields (`order_id`, `NMV`, `salesperson_*`, `sku`, …)
- **Store:** `ST1008` / `Brigade_Bangalore` / Bangalore
- **Orders:** ~30+ unique `order_id` on 10-Apr-2026 (12:15–20:25)
- **Reuse:** `discover_pos.py` already targets this schema ✅

### Sample POS (`POS - sample transactionsb1e826f.csv`)

- Simplified: `order_id`, `order_date`, `order_time`, `store_id`, `product_id`, `brand_name`, `total_amount`
- Same **ST1008** — useful for unit tests, not a second store

---

## 6. Sample events (`sample_eventsbe42122.jsonl`)

- **13 lines** (not 200 as in generic challenge description)
- **Three incompatible shapes:**
  1. `entry`/`exit` — `store_code`, `id_token`, `event_timestamp`, demographics
  2. `zone_entered`/`zone_exited` — `track_id`, `ST1076`, Purplle zone IDs
  3. `queue_completed`/`queue_abandoned` — queue timestamps, `abandoned` flag
- **Does not match** internal ingest schema (`event_id`, `visitor_id`, `timestamp`, …)
- **Store ID mismatch:** ST1076 vs ST1008 in new POS

---

## 7. Invalid assumptions in current repo

| Assumption | Reality |
|----------|---------|
| Footage lives in `CCTV Footage/*.mp4` | Now `Store 1/`, `Store 2/` |
| 5 cameras per store | Store 1 has **4**; Store 2 has **4** (2 entry) |
| `CAM 2` = billing (auto-discovery) | Store 1 billing is **CAM 5** visually |
| Single store deployment | Two stores uploaded; API is single-store-centric |
| `discover_all` skips if configs exist | Stale `configs/generated/*` won't refresh |
| `clip_base_timestamp` hardcoded 2026-04-10 20:09 | Store 2 OSD differs |
| Sample events ingestible as-is | Requires normalizer adapter |

---

## 8. Recommended config model (post-approval)

```
configs/
  stores/
    ST1008/
      store_layout.json
      camera_profile.json
      pos.csv (symlink or copy)
    ST_STORE2/
      store_layout.json
      camera_profile.json
data/
  stores/
    ST1008/raw/*.mp4
    ST_STORE2/raw/*.mp4
```

Discovery should scan `../Store */` and emit per-store manifests.

---

## 9. Screenshots (audit run)

| Store | File | Path |
|-------|------|------|
| Store 1 | CAM 3 entry | `docs/audit_screenshots/CAM_3_entry_mid.jpg` |
| Store 1 | CAM 5 billing | `docs/audit_screenshots/CAM_5_billing_mid.jpg` |
| Store 1 | CAM 1 zone | `docs/audit_screenshots/CAM_1_zone_mid.jpg` |
| Store 1 | CAM 2 zone | `docs/audit_screenshots/CAM_2_zone_mid.jpg` |
| Store 2 | entry 1 | `docs/audit_screenshots/entry_1_mid.jpg` |
| Store 2 | entry 2 | `docs/audit_screenshots/entry_2_mid.jpg` |
| Store 2 | billing | `docs/audit_screenshots/billing_area_mid.jpg` |
| Store 2 | zone | `docs/audit_screenshots/zone_mid.jpg` |

Machine-readable features: `data/discovery/new_dataset_camera_audit.json`

---

## 10. Confidence summary

| Store | Overall mapping readiness | Blocker |
|-------|---------------------------|---------|
| Store 1 (ST1008) | **High (0.85)** | Regenerate events; fix billing cam mapping |
| Store 2 | **Medium (0.55)** | Store ID + POS + zone schema |

**Awaiting approval** before refactor implementation.
