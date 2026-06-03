# Compliance Gap Report

**Generated:** 2026-06-03  
**References:**
- Purplle Tech Challenge 2026 Round 2 Problem Statement
- Assessment Evaluation Framework (April 2026)
- `sample_eventsbe42122.jsonl`
- Committed `data/events/output.jsonl`

---

## 1. API endpoints

| Endpoint | Status | Evidence | Gap |
|----------|--------|----------|-----|
| `POST /events/ingest` | ✅ **Implemented** | `backend/main.py`, `ingestion.py` | Does not accept sample JSONL schema without transform |
| `GET /stores/{id}/metrics` | ✅ **Implemented** | `metrics.py` | Single-store tested; Store 2 N/A without POS |
| `GET /stores/{id}/funnel` | ✅ **Implemented** | `funnel.py` | REENTRY dedup partial |
| `GET /stores/{id}/heatmap` | ✅ **Implemented** | `heatmap.py` | `data_confidence` present |
| `GET /stores/{id}/anomalies` | ✅ **Implemented** | `anomalies.py` | |
| `GET /health` | ✅ **Implemented** | `health.py`, `feed_freshness.py` | Multi-store list needs config drive |

**API score:** **5/6 fully wired** — ingest adapter for external schema is the main gap.

---

## 2. Event type catalogue (challenge Part A)

| Event type | Status | Pipeline | In `output.jsonl` |
|------------|--------|----------|-------------------|
| `ENTRY` | ✅ Implemented | `run_pipeline.py` (entry role) | ✅ 5 |
| `EXIT` | ✅ Implemented | entry role | ✅ 3 |
| `ZONE_ENTER` | ✅ Implemented | all roles | ✅ 22 |
| `ZONE_EXIT` | ⚠️ **Partial** | **Not emitted** in pipeline | ❌ 0 |
| `ZONE_DWELL` | ✅ Implemented | 30s accum | ✅ 30 |
| `BILLING_QUEUE_JOIN` | ✅ Implemented | billing role | ✅ 6 |
| `BILLING_QUEUE_ABANDON` | ❌ **Missing** | Not in `run_pipeline.py` | ❌ 0 |
| `REENTRY` | ✅ Implemented | after EXIT | ✅ 3 |

**Event score:** **6/8** complete in code; **7/8** in committed output file.

---

## 3. Event schema compliance

### 3.1 Challenge canonical schema (`StoreEvent`)

| Field | Required | Ingest support |
|-------|----------|----------------|
| `event_id` | UUID | ✅ |
| `store_id` | string | ✅ |
| `camera_id` | string | ✅ |
| `visitor_id` | string | ✅ |
| `event_type` | enum | ✅ |
| `timestamp` | ISO-8601 | ✅ |
| `zone_id` | nullable | ✅ |
| `dwell_ms` | int | ✅ |
| `is_staff` | bool | ✅ |
| `confidence` | 0–1 | ✅ |
| `metadata` | object | ✅ |

**Internal schema:** ✅ Aligned with challenge PDF.

### 3.2 Sample file schema (`sample_eventsbe42122.jsonl`)

| Check | Result |
|-------|--------|
| Validates as `StoreEvent` | ❌ **0/13 lines** without adapter |
| `event_id` present | ❌ Uses `id_token` / `queue_event_id` / `track_id` |
| `visitor_id` | ❌ Uses `id_token` or `track_id` |
| `timestamp` | ❌ Uses `event_timestamp` / `event_time` |
| Event names | ❌ `entry`, `zone_entered`, `queue_completed` vs `ENTRY`, `ZONE_ENTER` |
| Store IDs | ❌ `store_1076`, `ST1076` vs `ST1008` |

**Sample schema compliance:** ❌ **0%** direct ingest — need **`ingest/normalize_sample.py`** adapter (MODIFY `ingestion.py`).

### 3.3 Committed pipeline output validation

```
Event counts: ZONE_ENTER:22, ZONE_DWELL:30, BILLING_QUEUE_JOIN:6,
              ENTRY:5, EXIT:3, REENTRY:3
Total lines: 69
```

| Check | Result |
|-------|--------|
| Unique `event_id` | ✅ |
| ISO timestamps | ✅ |
| Staff flag present | ✅ |
| `BILLING_QUEUE_ABANDON` | ❌ |
| `ZONE_EXIT` | ❌ |
| Volume vs 20-min×4 cameras | ❌ **Demo subset** (bootstrap only) |

---

## 4. Edge cases (challenge §3.3)

| Edge case | Status | Notes |
|-----------|--------|-------|
| Group entry | ⚠️ Partial | Multiple ENTRY per frame possible; no explicit `group_id` in internal schema |
| Staff exclusion | ✅ | `staff.py` + `is_staff` filtered in metrics |
| Re-entry | ✅ | `REENTRY` events in output |
| Partial occlusion | ⚠️ Partial | Low conf kept — good |
| Billing queue / abandon | ⚠️ Partial | JOIN yes; **ABANDON not emitted** |
| Empty store periods | ⚠️ Partial | API handles zero; not proven on empty clip |
| Camera overlap dedup | ⚠️ Partial | `reid.py` exists; dual entry on Store 2 untested |

---

## 5. POS correlation

| Requirement | Status |
|-------------|--------|
| POS CSV ingested | ✅ Brigade → `discover_pos.py` |
| Conversion window | ✅ `metrics.sync_pos_conversions` |
| No customer_id | ✅ Time-window correlation |
| Store 2 POS | ❌ Missing file |

---

## 6. Production readiness (Part C)

| Requirement | Status |
|-------------|--------|
| `docker compose up` | ✅ Present |
| Structured logging | ✅ trace_id, latency |
| Ingest idempotency | ✅ `on_conflict_do_nothing` + tests |
| 503 on DB failure | ✅ |
| Tests >70% coverage | ⚠️ Not measured in audit — tests exist |
| README 5-command setup | ⚠️ Needs update for new paths |
| DESIGN.md + CHOICES.md | ⚠️ Outdated vs new dataset |

---

## 7. Dashboard (Part E bonus)

| Requirement | Status |
|-------------|--------|
| Live metric updates | ✅ WebSocket `/ws/metrics` |
| Challenge pages only | ✅ 5 routes in `App.tsx` |
| Vanity features removed | ✅ |

---

## 8. Acceptance gate (evaluation framework)

| Check | Status | Blocker |
|-------|--------|---------|
| `docker compose up` | ✅ Likely pass | Volume path if footage missing |
| `/metrics` valid JSON | ✅ With bootstrap JSONL | Stale data |
| Pipeline produces events | ⚠️ | Must point to `Store 1/` |
| DESIGN + CHOICES | ⚠️ | Need rewrite |
| Stability | ✅ | |

---

## 9. Validation reports summary

### 9.1 Event validation report

| Source | Lines | Valid internal schema | Action |
|--------|-------|----------------------|--------|
| `sample_eventsbe42122.jsonl` | 13 | 0 | Build normalizer + mapping table ST1076→ST1008 for demo only |
| `data/events/output.jsonl` | 69 | 69 | Regenerate from full pipeline run |
| Live pipeline (target) | TBD | — | Full clip processing |

### 9.2 Schema compliance report

| Schema | Compliance |
|--------|------------|
| Challenge PDF `StoreEvent` | **Ingest: 100%** for canonical events |
| Sample JSONL | **0%** without adapter |
| Queue events in sample | Separate aggregate schema — map to `BILLING_QUEUE_JOIN` / `BILLING_QUEUE_ABANDON` |

**Recommended adapter mappings:**

| Sample `event_type` | Internal `event_type` |
|---------------------|----------------------|
| `entry` | `ENTRY` |
| `exit` | `EXIT` |
| `zone_entered` | `ZONE_ENTER` |
| `zone_exited` | `ZONE_EXIT` |
| `queue_completed` (abandoned=false) | `BILLING_QUEUE_JOIN` + metadata |
| `queue_abandoned` (abandoned=true) | `BILLING_QUEUE_ABANDON` |

---

## 10. Priority fix list (implementation phase)

| P0 | Item |
|----|------|
| 1 | Multi-store discovery from `Store 1/`, `Store 2/` |
| 2 | Fix Store 1 billing camera → CAM 5 |
| 3 | Emit `BILLING_QUEUE_ABANDON` + `ZONE_EXIT` |
| 4 | Regenerate `output.jsonl` from new footage |
| 5 | Sample event normalizer (optional test fixture) |

| P1 | Item |
|----|------|
| 6 | Per-store `store_layout.json` + ROI from config |
| 7 | OSD-based timestamps per store |
| 8 | Store selector in dashboard |
| 9 | Rewrite README / DESIGN / CHOICES / COMMANDS |

| P2 | Item |
|----|------|
| 10 | Store 2 POS placeholder + conversion |
| 11 | Micro-brand zones from layout |
| 12 | Coverage gate in CI |

---

## 11. Overall compliance score (estimate)

| Area | Score |
|------|-------|
| API endpoints | **95%** |
| Event types | **75%** |
| Schema (canonical) | **100%** |
| Schema (sample file) | **0%** without adapter |
| New dataset readiness | **40%** |
| Production docs | **50%** |

**Verdict:** Repository is a **strong foundation** but **not yet aligned** with the newly uploaded two-store dataset. Refactor scope is **targeted**, not greenfield.

---

## 12. Approval

Proceed to implementation phase only after review of:
- `DATASET_REFRESH_REPORT.md`
- `CAMERA_REFRESH_REPORT.md`
- `LAYOUT_DIFF_REPORT.md`
- `CODE_AUDIT_REPORT.md`
- This document
