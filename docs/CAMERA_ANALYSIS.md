# Camera Analysis — Automated + Visual Validation

## Method

1. **Automated:** `scripts/discover_cameras.py` scores each MP4 using motion (left/center/right), brightness asymmetry, global and right-third edge density.
2. **Screenshots:** `scripts/analyze_videos.py` → `data/discovery/screenshots/`
3. **Human validation:** Frame review (OSD 10/04/2026 ~20:09 IST)

No filenames or store IDs are hardcoded in application code; roles are written to `configs/generated/camera_profile.json` at discovery time.

---

## Role assignments

| File | Auto role | `camera_id` | Confidence | Visual validation |
|------|-----------|-------------|------------|-------------------|
| CAM 3.mp4 | **entry** | `CAM_ENTRY_01` | **0.98** | Glass door, threshold — **agree** |
| CAM 2.mp4 | **billing** (auto) | `CAM_BILLING_01` | 0.98 | Counter visible; **CAM 5 also shows POS** |
| CAM 5.mp4 | main_floor (auto) | `CAM_FLOOR_5` | 0.75 | **Billing counter + queue** — visual override candidate |
| CAM 1.mp4 | main_floor | `CAM_FLOOR_1` | 0.75 | Brand wall + island — **agree** |
| CAM 4.mp4 | main_floor | `CAM_FLOOR_4` | 0.75 | Wide aisle — **agree** |

### Reasoning — Entry (CAM 3)

- Highest `brightness_asymmetry` (bright store interior vs dark exterior right)
- Lowest edge density (~13 vs ~35 on floor cams)
- Low center motion — fixed door view

Screenshot: `data/discovery/screenshots/CAM_3_f2218.jpg`

### Reasoning — Billing ambiguity (CAM 2 vs CAM 5)

Both clips score high on `billing` heuristics. Auto-discovery picks **CAM 2** (slightly higher composite billing score). Visual review of **CAM 5** shows L-shaped POS, scanners, and queue area — recommended for production billing analytics.

**Mitigation in pipeline:** Any camera with `role=billing` receives billing zone ROIs; re-run discovery after adding bottom-right edge features or auditor file `configs/generated/camera_visual_audit.json` (optional).

### Overlap / blind spots

- Entry (CAM 3) overlaps FOH seen on CAM 1 — **cross-camera Re-ID** in `pipeline/reid.py` reduces double entry counts.
- CAM 4 back aisle partially occluded by fixtures — lower confidence detections retained (not dropped).

---

## Duplicate views

CAM 1 and CAM 2 share partial FOV of east floor; not full duplicates.

---

## Screenshots index

| Camera | Sample |
|--------|--------|
| CAM 1 | `data/discovery/screenshots/CAM_1_f2096.jpg` |
| CAM 2 | `data/discovery/screenshots/CAM_2_f1887.jpg` |
| CAM 3 | `data/discovery/screenshots/CAM_3_f2218.jpg` |
| CAM 4 | `data/discovery/screenshots/CAM_4_f1823.jpg` |
| CAM 5 | `data/discovery/screenshots/CAM_5_f1732.jpg` |
