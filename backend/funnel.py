from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.analytics_window import get_analytics_window
from backend.models import SessionRow
from backend.schemas import FunnelResponse, FunnelStage


async def compute_funnel(db: AsyncSession, store_id: str) -> FunnelResponse:
    now = datetime.now(timezone.utc)
    window_start, window_end, _ = await get_analytics_window(db, store_id)
    sessions = (
        await db.execute(
            select(SessionRow).where(
                SessionRow.store_id == store_id,
                SessionRow.is_staff.is_(False),
                SessionRow.started_at >= window_start,
                SessionRow.started_at < window_end,
            )
        )
    ).scalars().all()

    entry = len(sessions)
    zone = sum(1 for s in sessions if s.zone_visited)
    billing = sum(1 for s in sessions if s.billing_visited)
    purchase = sum(1 for s in sessions if s.converted)

    def stage(name: str, count: int, prev: int) -> FunnelStage:
        drop = ((prev - count) / prev * 100) if prev else 0.0
        conv = (count / entry * 100) if entry else 0.0
        return FunnelStage(
            stage=name,
            visitors=count,
            drop_off_pct=round(max(0.0, drop), 2),
            conversion_pct=round(conv, 2),
        )

    stages = [
        stage("Entry", entry, entry),
        stage("Zone Visit", zone, entry),
        stage("Billing", billing, zone or entry),
        stage("Purchase", purchase, billing or zone or entry),
    ]
    return FunnelResponse(store_id=store_id, stages=stages, as_of=now)
