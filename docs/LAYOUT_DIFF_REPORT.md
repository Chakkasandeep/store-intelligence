# Layout Diff Report

**Generated:** 2026-06-03  
**Compares:** `configs/generated/store_layout.json` (committed) vs new layout assets

---

## 1. Sources compared

| Source | Type | Store |
|--------|------|-------|
| `configs/generated/store_layout.json` | Generated JSON (9 zones) | ST1008 |
| `Store 1/Store 1 - layout.png` | New floor plan image | Store 1 |
| `Brigade Road - Store layoutc5f5d56.xlsx` | Workbook + embedded PNG | Store 1 |
| `data/layout/image1.png` | Previously extracted from xlsx | Store 1 |
| `Store 2/store 2 - layout.png` | New floor plan image | Store 2 |

---

## 2. Store 1 — zone reconciliation

### 2.1 Existing JSON zones (`store_layout.json`)

| zone_id | label | type |
|---------|-------|------|
| ENTRY_EXIT | Main entrance threshold | traffic |
| FOH_CENTER | Front of house / central aisle | traffic |
| SKIN_NORTH | North wall skincare brands | product |
| MAKEUP_SOUTH | South wall makeup brands | product |
| FRAGRANCE_ISLAND | Fragrance & nail gondola | product |
| MAKEUP_UNITS | Central makeup consultation units | product |
| BILLING | Cash counter / POS | billing |
| ACCESSORIES | Accessories wall | product |
| PMU | PMU service nook | service |

### 2.2 Layout image labels (Store 1 PNG / Brigade plan)

**North wall (green):** Salm, TFS, Minimalist, Aqualogica, Foxtale, JC  
**South wall:** Fac, Mars+Nybae, Mens, L'Oreal, Beaut  
**Center:** Fragrance / Nail gondola, Makeup units (×2)  
**East:** Cash counter, Accessories  
**West:** Entry / glass / BACKLIT

### 2.3 Diff matrix

| Status | Item | Detail |
|--------|------|--------|
| ✅ **Keep** | ENTRY_EXIT | Matches left entrance on plan |
| ✅ **Keep** | FOH_CENTER | Labeled “F.O.H” on plan |
| ✅ **Keep** | BILLING | “CASH COUNTER” east side |
| ✅ **Keep** | FRAGRANCE_ISLAND | “Fragrance / NAIL GONDOLA” |
| ✅ **Keep** | MAKEUP_UNITS | Two consultation stations |
| ✅ **Keep** | ACCESSORIES | “Acces” wall |
| ⚠️ **Modify** | SKIN_NORTH | Plan has **6+ named brand bays** — current zone is one aggregated polygon |
| ⚠️ **Modify** | MAKEUP_SOUTH | Plan splits Fac / Mars / Mens / L'Oreal / Beaut |
| ➕ **New (optional)** | BRAND_* micro-zones | For heatmap fidelity (e.g. `BRAND_MAYBELLINE` from CAM 2 FOV) |
| ➖ **Removed** | — | No zones in JSON absent from plan |
| 🔄 **Renamed** | PMU | Not clearly labeled on Store 1 PNG — may be **service nook** or B.O.H; **low confidence** |
| 📍 **Billing location** | East wall counter | Confirmed — align `CAM_BILLING_01` to **CAM 5** feed |
| 📍 **Entry location** | West glass doors | Confirmed — CAM 3 |
| 📍 **Queue location** | Floor between makeup units and counter | Covered by BILLING ROI extension in pipeline |

### 2.4 Coordinate system gap

| Current implementation | Layout asset |
|------------------------|--------------|
| Normalized ROIs per **camera role** in `pipeline/zones.py` | Millimeter CAD dimensions on PNG |
| No polygon export from xlsx | Sheet1 empty — only embedded image |

**Required change:** Load zone polygons from per-store layout config (or generated from layout image via CV), not hardcoded `rois_for_role()`.

---

## 3. Store 2 — new layout (no existing JSON)

### 3.1 Plan elements

| Element | Plan label | Proposed zone_id |
|---------|------------|------------------|
| Entrance | Bottom center doors (1917mm) | `ENTRY_EXIT` |
| Cash counter | Rear-center FOH | `BILLING` |
| Queue | In front of counter | `BILLING_QUEUE` (metadata) |
| Gondolas | MK-GONDOLA-1, MK-GONDOLA-2 | `GONDOLA_01`, `GONDOLA_02` |
| Makeup | 4× MAKEUP UNIT | `MAKEUP_UNITS` |
| Wall retail | Units 1–19 | `WALL_01`…`WALL_19` or grouped `WALL_NORTH` / `WALL_EAST` |
| B.O.H | Top narrow rectangle | `BOH` (staff-only — exclude from customer metrics) |
| Glazing | EXISTING GLAZING flanks | Not a dwell zone |

### 3.2 Diff vs Store 1 JSON

| Store 1 zone | Store 2 equivalent |
|--------------|-------------------|
| SKIN_NORTH | Wall units 1–6 (left) |
| MAKEUP_SOUTH | Wall units 15–19 (right) |
| FRAGRANCE_ISLAND | Gondolas (different position: center-left angled) |
| PMU | B.O.H service area |
| ACCESSORIES | Not explicit — may be wall units |

**Conclusion:** Store 2 needs a **separate** `store_layout.json` — do not reuse Store 1 zone IDs for analytics.

---

## 4. `camera_zone_map` diff

### Current (committed)

```json
"CAM_ENTRY_01": ["ENTRY_EXIT", "FOH_CENTER"],
"CAM_BILLING_01": ["BILLING", "ACCESSORIES"],
"CAM_QUEUE_01": ["BILLING"]
```

### Issues

| Issue | Fix |
|-------|-----|
| `CAM_QUEUE_01` has no matching video in new dataset | Remove or map to billing camera queue ROI |
| IDs reference old discovery names | Regenerate from Store 1/2 camera profiles |
| No Store 2 entries | Add `ST2_CAM_*` maps |

### Proposed Store 1 map

| camera_id | zones |
|-----------|-------|
| ST1008_CAM_ENTRY_01 | ENTRY_EXIT, FOH_CENTER |
| ST1008_CAM_BILLING_01 | BILLING, BILLING_QUEUE |
| ST1008_CAM_FLOOR_01 | FOH_CENTER, SKIN_NORTH, FRAGRANCE_ISLAND |
| ST1008_CAM_FLOOR_02 | FOH_CENTER, MAKEUP_SOUTH, MAKEUP_UNITS |

---

## 5. open_hours_local

Committed: `10:00`–`22:00` (assumed).  
POS on 10-Apr-2026 spans **12:15–20:25** — consistent. No change required unless layout specifies otherwise.

---

## 6. Priority layout tasks (post-approval)

1. Extract / copy layout PNGs into `data/layout/ST1008.png`, `data/layout/ST_STORE2.png`
2. Regenerate `store_layout.json` per store from discovery + plan labels
3. Move ROIs from `zones.py` into layout JSON (`zones[].polygon_norm`)
4. Update heatmap grid component to read dynamic zone list
5. Document PMU / BOH staff-exclusion zones

---

## 7. Confidence

| Item | Confidence |
|------|------------|
| Billing + entry positions (Store 1) | 0.92 |
| Store 1 macro-zones map to plan | 0.88 |
| Store 2 requires new zone catalogue | 0.90 |
| CAD-accurate polygons without manual digitization | 0.45 |
