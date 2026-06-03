# CHOICES — Engineering Decisions and Trade-offs

This document details the critical design options, trade-offs, and LLM-assisted decisions implemented in the Store Intelligence System.

## 1. Multi-Store Config-Driven Design vs. Hardcoded ROIs

- **Option A (Hardcoded Constants)**: Define camera names, layouts, and ROI polygons as Python variables. Easy to implement initially, but fails when new datasets (like Store 2) are introduced.
- **Option B (JSON Config Registry)**: Move all store configurations (polygons, cameras, OSD dates, names) into JSON files under `configs/generated/{store_id}/`.
- **Decision**: **Selected Option B**. All coordinate containment checks are completely decoupled from Python source and loaded from JSON. This ensures the system remains extensible.

## 2. Dynamic Event Schema Normalizer vs. Strict Schema Rejection

- **Option A (Strict Ingestion)**: Reject any payload that does not conform 100% to the internal Pydantic `StoreEvent` model. Causes failures on legacy datasets (like `sample_eventsbe42122.jsonl` using `id_token` and `event_timestamp`).
- **Option B (Ingestion Adapter)**: Add a normalizer in `backend/ingestion.py` that intercepts legacy keys, maps track/token IDs to visitor IDs, and reformats them.
- **Decision**: **Selected Option B**. This allows seamless ingestion of third-party mock sets and legacy streams while maintaining Pydantic validation on the database schema.

## 3. Visitor Re-entry Handling: Session Reopening vs. Multiple Sessions

- **Option A (Independent Sessions)**: Spawn a new session for every `ENTRY` / `REENTRY` event. Simple to program, but double-counts visitors returning from a brief exit and deflates conversion rates.
- **Option B (Session Reopening)**: Track visitor re-entries using Re-ID tracking. When a `REENTRY` event is processed, the backend retrieves their previous session and clears `ended_at` to resume it.
- **Decision**: **Selected Option B**. This satisfies the requirement that re-entries must not double-count a visitor in unique metrics or conversion funnels.

## 4. Queue Abandonment Tracking: In-Pipeline Detection vs. Backend Correlation

- **Option A (Backend-only Inference)**: Rely entirely on timestamps to guess if a visitor abandoned a queue. Inaccurate due to time synchronization drift.
- **Option B (Pipeline Candidate + Backend Prune)**: The CV pipeline emits a `BILLING_QUEUE_ABANDON` event when a customer leaves the checkout queue. If the backend matches a subsequent POS purchase for that visitor, it deletes the abandonment event.
- **Decision**: **Selected Option B**. Combining spatial queue exiting (pipeline) with transaction validation (backend) yields a highly accurate abandonment metric.

## AI Suggestions and Overrides

- **AI Suggestion**: Cache heatmaps and metrics hourly to reduce SQL load.
  - **Override**: Rejected because retail dashboards require live, real-time analytics. Optimized database queries using indexes instead.
- **AI Suggestion**: Use segmenting/VLM networks for zone labeling.
  - **Override**: Rejected due to high latency on standard Intel i5 processors. Selected normalized polygon coordinates with fast `cv2` containment checks.
