# Data Analysis — Brigade Bangalore (ST1008)

## Dataset scope

| Asset | Purpose | Confidence |
|-------|---------|------------|
| `Brigade_Bangalore_10_April_26 (1)bc6219c.csv` | POS line-level sales | 0.95 |
| `Brigade Road - Store layoutc5f5d56.xlsx` | Floor plan image (embedded PNG) | 0.88 |
| `CCTV Footage/CAM 1-5.mp4` | 5 physical angles, **1 store** | 0.99 |
| Problem statement PDF | API + event schema contract | 1.0 |
| Evaluation framework PDF | Scoring rubric | 1.0 |

**Assumption:** Official challenge ZIP describes 5 stores × 3 cameras; the provided local bundle is a **single-store subset** (Brigade / ST1008) with **5 cameras** (~2.3 min each, not 20 min). All configs derive `store_id=ST1008` from CSV.

---

## POS CSV (`Brigade_Bangalore_10_April_26 (1)bc6219c.csv`)

### Schema (39 columns)

| Column | Type | Nulls | Meaning |
|--------|------|-------|---------|
| `order_id` | int | 0 | Transaction key (24 unique orders) |
| `invoice_number` | str | 0 | Invoice id (1:1 with order) |
| `order_date` | str | 0 | `10-04-2026` (DD-MM-YYYY) |
| `order_time` | str | 0 | `12:15:05` – `21:39:55` |
| `store_id` | str | 0 | `ST1008` |
| `store_name` | str | 0 | `Brigade_Bangalore` |
| `customer_number` | int | 0 | Phone (no join to CCTV) |
| `sku` / `product_id` | str/int | 0 | Line item |
| `NMV` | float | 0 | Net merchandise value (INR) |
| `salesperson_id` / `employee_code` | int/str | 7 name gaps | Staff attribution |
| `return_id` | float | 101 | Unused (all null) |
| `coupon_code` | str | 98% null | Sparse promotions |

### Relationships

- `order_id` → many line items (1:N)
- `invoice_number` unique per order
- `salesperson_id` → staff candidates (5 employees active)

### Quality notes

- EAN floats in scientific notation — cosmetic only
- No `customer_id` — conversion by **time window + billing zone visit** (per brief)
- CCTV OSD ~**20:09–20:10** vs POS **12:15–21:39** — same calendar day, different hours (evening clip vs full-day sales)

---

## CCTV videos

| File | Resolution | FPS | Duration | Notes |
|------|------------|-----|----------|-------|
| CAM 1.mp4 | 1920×1080 | 29.97 | 140s | Main aisle / brands |
| CAM 2.mp4 | 1920×1080 | 29.97 | 126s | High edge density (billing candidate) |
| CAM 3.mp4 | 1920×1080 | 29.97 | 148s | Glass door entry |
| CAM 4.mp4 | 1920×1080 | 24.98 | 146s | Wide floor |
| CAM 5.mp4 | 1920×1080 | 24.98 | 139s | POS counter (visual validation) |

---

## Store layout XLSX

- Single sheet with embedded `image1.png` (extracted to `data/layout/image1.png`)
- No machine-readable zone polygons — zones inferred from plan labels (see `STORE_LAYOUT_ANALYSIS.md`)

---

## Generated artifacts

- `configs/generated/pos_mapping.json`
- `configs/generated/pos_transactions_derived.csv`
- `configs/generated/camera_profile.json`
- `configs/generated/store_layout.json`
- `data/discovery/video_features.json`
