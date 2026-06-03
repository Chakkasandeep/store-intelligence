# DESIGN — Store Intelligence System

This document describes the architectural specifications, event semantics, and design choices of the Store Intelligence System.

## Architecture Overview

The system is designed to process multiple retail stores dynamically. No store IDs, camera mappings, or layout coordinate polygons are hardcoded in the codebase. All details are discovered and loaded from store-specific configuration files.

```
CCTV Footage (Store 1, Store 2 sibling folders)
    → discover_all.py → configs/generated/{store_id}/camera_profile.json
                        configs/generated/{store_id}/store_layout.json
    → run_pipeline.py --store-id {store_id} (YOLOv8n + ByteTrack + Re-ID)
    → data/events/{store_id}/output.jsonl
    → uvicorn bootstrap → Ingest output.jsonl + POS transactions
    → GET API & WebSocket endpoints (metrics, funnel, heatmap, anomalies)
    → React dashboard (with multi-store dropdown selector)
```

## Data-Driven Configuration Model

All settings and configurations are grouped by store ID inside `configs/generated/{store_id}/`:
- **`camera_profile.json`**: Lists available camera feeds, roles (`entry`, `billing`, `main_floor`), resolution, fps, and reasoning.
- **`store_layout.json`**: Outlines store metadata, open hours, active zones, camera-to-zone mappings, and normalized coordinate ROIs (`role_polygons`) per camera role.
- **`pos_transactions_derived.csv`**: Contains aggregated sales transactions used to calculate conversion rates.

## Structured Event Stream

The pipeline processes each camera feed and produces an event stream matching the canonical schema.

### Event Catalogue

1. **`ENTRY`**: Emitted when a visitor crosses the entrance threshold in the inbound direction. Starts a session.
2. **`EXIT`**: Emitted when a visitor crosses the entrance threshold in the outbound direction. Closes the active session.
3. **`ZONE_ENTER`**: Emitted when a visitor enters a zone polygon.
4. **`ZONE_EXIT`**: Emitted when a visitor leaves a zone polygon (either by entering another zone, moving to an unmonitored space, or exiting the store).
5. **`ZONE_DWELL`**: Emitted periodically every 30 seconds of continuous dwell time in a zone.
6. **`BILLING_QUEUE_JOIN`**: Emitted when a visitor enters the cash counter queue (while queue depth > 0).
7. **`BILLING_QUEUE_ABANDON`**: Emitted when a visitor exits the cash counter queue area without checking out. If they subsequently complete a purchase, this abandonment is pruned by the backend during POS correlation.
8. **`REENTRY`**: Emitted when a previously seen visitor returns to the store after a prior exit.

## Session Lifecycle and Re-Entry Handling

Visitor session boundaries are managed statefully in the database:
- **Session Reopening**: If a visitor leaves and re-enters, the pipeline emits a `REENTRY` event. The ingestion layer intercepts this event and re-opens their most recent session (by clearing `ended_at`) instead of spawning a new session. This prevents inflating unique visitor counts and ensures the funnel accurately reports conversion.
- **Staff Exclusion**: Staff tracks are identified via high persistence across multiple clips and high speed movement. They are flagged as `is_staff=True` and filtered out of all customer metrics.

## Database Schema (SQLite)

- **`events`**: Ingested raw event stream (deduplicated by `event_id` using `ON CONFLICT DO NOTHING`).
- **`sessions`**: visitor sessions containing start/end timestamps, zone visit flags, and conversion status.
- **`transactions`**: POS sales invoices correlated by time-window + store ID.
- **`anomalies`**: Operational anomalies (e.g. `BILLING_QUEUE_SPIKE`, `CONVERSION_DROP`, `DEAD_ZONE`, `STALE_FEED`).

## AI-Assisted Design Decisions

1. **Camera Billing Heuristic Override**: Heuristics based on edge density misclassified Store 1's `CAM 5` as main_floor. An explicit visual override map was introduced to correctly classify `CAM 5` as `BILLING_CAMERA` and `CAM 2` as `MAIN_FLOOR_CAMERA`.
2. **Schema Adapter/Normalizer**: The ingestion layer includes a dynamic adaptor that parses legacy schemas (such as `sample_eventsbe42122.jsonl` with `id_token` and `event_timestamp`) on the fly, transforming them into `StoreEvent` records during ingestion.
3. **Queue Abandonment Deletion**: Since the pipeline cannot inspect POS records offline, it emits a `BILLING_QUEUE_ABANDON` candidate when a track exits the checkout queue. The backend deletes this event if POS correlation matches a transaction within the conversion window.
