# POS Mapping — Inferred from Brigade CSV

**Source file:** `Brigade_Bangalore_10_April_26 (1)bc6219c.csv`  
**Generated:** `configs/generated/pos_mapping.json`, `pos_transactions_derived.csv`

## Schema mapping

| Challenge `pos_transactions.csv` | Brigade CSV field | Notes |
|----------------------------------|-------------------|-------|
| `store_id` | `store_id` | `ST1008` |
| `transaction_id` | `order_id` | 24 orders |
| `timestamp` | `order_date` + `order_time` | Parsed day-first |
| `basket_value_inr` | sum(`NMV`) per order | Line items aggregated |

## Staff (for exclusion cross-check)

| salesperson_id | employee_code | Lines |
|----------------|---------------|-------|
| 971 | CL2727 | 42 |
| 1178 | CL2063 | 19 |
| 1190 | CL2680 | 13 |
| 523 | CL1997 | 12 |
| 737 | CL2541 | 8 |

CV staff flag (`is_staff`) is independent; POS staff used for validation only.

## Conversion logic

1. Session must have `billing_visited=true` (from `BILLING_QUEUE_JOIN` or `ZONE_ENTER` in BILLING).
2. POS order timestamp within **5 minutes** after session start (`conversion_window_minutes` in mapping JSON).
3. No `customer_id` — session-level correlation only (per brief).

## Double-counting guards

- Funnel uses **sessions**, not raw events.
- `REENTRY` does not create a new funnel entry visitor.
- Re-ingest is idempotent on `event_id`.

## Stats (10-Apr-2026)

- 101 line items, 24 orders, ₹34,831.74 NMV
- Time span 12:15–21:39 (POS) vs ~20:09 (CCTV)
