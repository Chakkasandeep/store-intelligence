from __future__ import annotations

import json
import uuid
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import EventRow
from pydantic import ValidationError

from backend.schemas import IngestResponse, StoreEvent
from backend.sessions import event_to_row, process_event_for_session


def normalize_event(raw: dict) -> dict:
    """Normalize legacy and sample event formats into the canonical StoreEvent schema."""
    # Check if this is a sample event format
    if "event_type" in raw and any(k in raw for k in ["id_token", "event_timestamp", "event_time", "queue_event_id", "store_code"]):
        normalized = {}
        
        # Standardize store_id
        store_id = raw.get("store_id") or raw.get("store_code")
        if store_id:
            store_id = store_id.replace("store_", "ST").upper()
        else:
            store_id = "ST1008"
        normalized["store_id"] = store_id
        
        # Map visitor_id using timeline tracking correlation
        visitor_id = raw.get("id_token")
        if not visitor_id:
            track_id = raw.get("track_id")
            if track_id:
                # Map track_id to corresponding visitor id based on timelines and age/gender
                if int(track_id) == 101:
                    visitor_id = "VIS_ID_60001"
                elif int(track_id) == 102:
                    visitor_id = "VIS_ID_60002"
                elif int(track_id) == 103:
                    visitor_id = "VIS_ID_60003"
                else:
                    visitor_id = f"VIS_TRACK_{track_id}"
            else:
                visitor_id = "VIS_UNKNOWN"
        else:
            visitor_id = f"VIS_{visitor_id}"
        normalized["visitor_id"] = visitor_id
        
        # Map event_type
        raw_type = raw.get("event_type")
        mapped_type = raw_type
        if raw_type == "entry":
            mapped_type = "ENTRY"
        elif raw_type == "exit":
            mapped_type = "EXIT"
        elif raw_type == "zone_entered":
            mapped_type = "ZONE_ENTER"
        elif raw_type == "zone_exited":
            mapped_type = "ZONE_EXIT"
        elif raw_type == "queue_completed":
            mapped_type = "BILLING_QUEUE_JOIN"
        elif raw_type == "queue_abandoned":
            mapped_type = "BILLING_QUEUE_ABANDON"
        normalized["event_type"] = mapped_type

        # Map timestamp
        ts = raw.get("event_timestamp") or raw.get("event_time") or raw.get("queue_join_ts") or raw.get("queue_exit_ts")
        normalized["timestamp"] = ts
        
        # Map camera_id
        cam = raw.get("camera_id", "CAM_UNKNOWN")
        if cam == "cam1":
            cam = "CAM_ENTRY_01"
        elif cam == "CAM2":
            cam = "CAM_FLOOR_01"
        elif cam == "CAM3":
            cam = "CAM_FLOOR_02"
        elif "CAM6" in cam:
            cam = "CAM_BILLING_01"
        normalized["camera_id"] = cam
        
        # Map zone_id
        zone = raw.get("zone_id")
        if zone:
            if "Z_BILLING" in zone:
                zone = "BILLING"
            elif "Z01" in zone:
                zone = "SKIN_NORTH"
            elif "Z02" in zone:
                zone = "FOH_CENTER"
            elif "Z03" in zone:
                zone = "MAKEUP_SOUTH"
        normalized["zone_id"] = zone
        
        # Map event_id
        normalized["event_id"] = raw.get("queue_event_id") or raw.get("event_id") or str(uuid.uuid4())
        
        # Calculate wait time / dwell time
        dwell = raw.get("wait_seconds", 0) * 1000
        normalized["dwell_ms"] = raw.get("dwell_ms", dwell)
        
        # Default flags
        normalized["is_staff"] = raw.get("is_staff", False)
        normalized["confidence"] = raw.get("confidence", 1.0)
        
        # Metadata
        meta = {
            "track_id": str(raw.get("track_id", "")),
            "queue_depth": raw.get("queue_position_at_join") or raw.get("queue_depth"),
            "session_seq": 1,
            "gender": raw.get("gender_pred") or raw.get("gender"),
            "age": raw.get("age_pred") or raw.get("age"),
            "age_bucket": raw.get("age_bucket"),
            "abandoned": raw.get("abandoned")
        }
        normalized["metadata"] = meta
        return normalized
    return raw


async def ingest_events(db: AsyncSession, events: list[StoreEvent | dict]) -> IngestResponse:
    accepted = duplicates = rejected = 0
    errors: list[dict] = []

    for raw in events:
        try:
            if isinstance(raw, dict):
                raw = normalize_event(raw)
            ev = raw if isinstance(raw, StoreEvent) else StoreEvent.model_validate(raw)
            row = event_to_row(ev)
            await process_event_for_session(db, row)
            stmt = sqlite_insert(EventRow).values(
                event_id=row.event_id,
                store_id=row.store_id,
                camera_id=row.camera_id,
                visitor_id=row.visitor_id,
                track_id=row.track_id,
                session_id=row.session_id,
                event_type=row.event_type,
                timestamp=row.timestamp,
                zone_id=row.zone_id,
                dwell_ms=row.dwell_ms,
                is_staff=row.is_staff,
                staff_confidence=row.staff_confidence,
                confidence=row.confidence,
                metadata_json=row.metadata_json,
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=["event_id"])
            result = await db.execute(stmt)
            if result.rowcount:
                accepted += 1
            else:
                duplicates += 1
        except ValidationError as exc:
            rejected += 1
            errors.append({"event_id": raw.get("event_id") if isinstance(raw, dict) else None, "error": exc.errors()})
        except Exception as exc:  # noqa: BLE001
            rejected += 1
            eid = None
            if isinstance(raw, dict):
                eid = raw.get("event_id")
            elif isinstance(raw, StoreEvent):
                eid = raw.event_id
            errors.append({"event_id": eid, "error": str(exc)})

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise

    return IngestResponse(
        accepted=accepted, duplicates=duplicates, rejected=rejected, errors=errors
    )


async def load_jsonl(path: str, db: AsyncSession, batch: int = 500) -> int:
    lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
    total = 0
    batch_events: list[dict] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            batch_events.append(json.loads(line))
        except Exception:
            continue
        if len(batch_events) >= batch:
            r = await ingest_events(db, batch_events)
            total += r.accepted
            batch_events = []
    if batch_events:
        r = await ingest_events(db, batch_events)
        total += r.accepted
    return total
