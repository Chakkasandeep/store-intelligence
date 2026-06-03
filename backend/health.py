from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings, active_stores
from backend.db import engine
from backend.feed_freshness import is_stale_feed
from backend.models import EventRow
from backend.schemas import HealthResponse, HealthStoreStatus


async def compute_health(db: AsyncSession) -> HealthResponse:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    warnings: list[str] = []
    stores: list[HealthStoreStatus] = []

    try:
        async with engine.connect() as conn:
            await conn.execute(select(1))
        status = "ok"
    except Exception:
        return HealthResponse(status="unavailable", stores=[], warnings=["database_unavailable"])

    for sid in active_stores():
        last = (
            await db.execute(select(func.max(EventRow.timestamp)).where(EventRow.store_id == sid))
        ).scalar()
        stale = is_stale_feed(last, now=now, threshold_minutes=settings.stale_feed_minutes)
        if stale:
            warnings.append(f"STALE_FEED:{sid}")
        stores.append(HealthStoreStatus(store_id=sid, last_event_at=last, stale=stale))
        if stale and status == "ok":
            status = "degraded"
            
    return HealthResponse(status=status, stores=stores, warnings=warnings)
