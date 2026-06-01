# Store Layout Analysis — Brigade Road

**Source:** `Brigade Road - Store layoutc5f5d56.xlsx` → embedded `data/layout/image1.png`  
**Store:** ST1008 / Brigade_Bangalore (from POS CSV)

## Identified areas

| Zone ID | Label | Type | Confidence |
|---------|-------|------|------------|
| ENTRY_EXIT | Main entrance (glass door, west) | traffic | 0.92 |
| FOH_CENTER | Central aisle / islands | traffic | 0.85 |
| SKIN_NORTH | North wall (Face Shop, Good Vibes, DermDoc, Minimalist, Aqualogica, Lakme Skin) | product | 0.80 |
| MAKEUP_SOUTH | South wall (Maybelline, Faces, Lakme, Colorbar, Swiss Beauty, etc.) | product | 0.80 |
| FRAGRANCE_ISLAND | Left-center gondola | product | 0.75 |
| MAKEUP_UNITS | Central consultation tables | product | 0.78 |
| BILLING | Cash counter + LED panel (east) | billing | 0.90 |
| ACCESSORIES | East wall accessories bay | product | 0.82 |
| PMU | Permanent makeup nook (SE) | service | 0.70 |

## Traffic flow (inferred)

Entry (west) → FOH loop around islands → optional north/south browsing → billing (east) → exit west.

## Camera ↔ zone mapping

Derived in `configs/generated/store_layout.json`:

- `CAM_ENTRY_01` → ENTRY_EXIT, FOH_CENTER
- `CAM_BILLING_01` → BILLING, ACCESSORIES
- Floor cameras → FOH_CENTER, SKIN_NORTH, MAKEUP_SOUTH

## Assumptions

- CAD dimensions on plan (mm) are **not** used for pixel polygons; pipeline uses **normalized ROIs per camera role** (`pipeline/zones.py`).
- Brand-level zones are grouped for dwell heatmaps; sub-brand segmentation would need shelf-level calibration.

## Quality issues

- XLSX has no vector zone data — only raster image (confidence 0.88 for zone labels, 0.60 for exact polygons).
