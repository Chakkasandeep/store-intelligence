from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import EventRow
from pydantic import ValidationError

from backend.schemas import IngestResponse, StoreEvent
from backend.sessions import event_to_row, process_event_for_session


async def ingest_events(db: AsyncSession, events: list[StoreEvent | dict]) -> IngestResponse:
    accepted = duplicates = rejected = 0
    errors: list[dict] = []

    for raw in events:
        try:
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
        except Exception as exc:  # noqa: BLE001 — partial success contract
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
    from pathlib import Path

    from pydantic import ValidationError

    lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
    total = 0
    batch_events: list[StoreEvent] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            batch_events.append(StoreEvent.model_validate(json.loads(line)))
        except ValidationError:
            continue
        if len(batch_events) >= batch:
            r = await ingest_events(db, batch_events)
            total += r.accepted
            batch_events = []
    if batch_events:
        r = await ingest_events(db, batch_events)
        total += r.accepted
    return total
