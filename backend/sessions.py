from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import EventRow, SessionRow
from backend.schemas import StoreEvent


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def event_to_row(ev: StoreEvent) -> EventRow:
    meta = ev.metadata if isinstance(ev.metadata, dict) else ev.metadata.model_dump()
    track_id = meta.get("track_id")
    return EventRow(
        event_id=ev.event_id,
        store_id=ev.store_id,
        camera_id=ev.camera_id,
        visitor_id=ev.visitor_id,
        track_id=track_id,
        session_id=None,
        event_type=ev.event_type,
        timestamp=_utc(ev.timestamp),
        zone_id=ev.zone_id,
        dwell_ms=ev.dwell_ms,
        is_staff=ev.is_staff,
        staff_confidence=float(meta.get("staff_confidence", 0.0)),
        confidence=ev.confidence,
        metadata_json=json.dumps(meta),
    )


async def process_event_for_session(db: AsyncSession, row: EventRow) -> str:
    """Attach session_id based on visitor entry/exit lifecycle."""
    now = row.timestamp
    if row.event_type == "ENTRY":
        session_id = f"SES_{uuid.uuid4().hex[:12]}"
        db.add(
            SessionRow(
                session_id=session_id,
                store_id=row.store_id,
                visitor_id=row.visitor_id,
                started_at=now,
                is_staff=row.is_staff,
            )
        )
        row.session_id = session_id
        return session_id

    result = await db.execute(
        select(SessionRow)
        .where(
            SessionRow.store_id == row.store_id,
            SessionRow.visitor_id == row.visitor_id,
            SessionRow.ended_at.is_(None),
        )
        .order_by(SessionRow.started_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if session is None:
        session_id = f"SES_{uuid.uuid4().hex[:12]}"
        db.add(
            SessionRow(
                session_id=session_id,
                store_id=row.store_id,
                visitor_id=row.visitor_id,
                started_at=now,
                is_staff=row.is_staff,
            )
        )
        row.session_id = session_id
        return session_id

    row.session_id = session.session_id
    if row.event_type in {"ZONE_ENTER", "ZONE_DWELL"} and row.zone_id:
        session.zone_visited = True
    if row.event_type == "BILLING_QUEUE_JOIN" or row.zone_id == "BILLING":
        session.billing_visited = True
    if row.event_type == "EXIT":
        session.ended_at = now
    if row.is_staff:
        session.is_staff = True
    return session.session_id
