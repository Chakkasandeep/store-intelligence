from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.analytics_window import get_analytics_window
from backend.models import EventRow, SessionRow
from backend.schemas import HeatmapResponse, HeatmapZone


async def compute_heatmap(db: AsyncSession, store_id: str) -> HeatmapResponse:
    now = datetime.now(timezone.utc)
    window_start, window_end, _ = await get_analytics_window(db, store_id)

    session_count = (
        await db.execute(
            select(func.count())
            .select_from(SessionRow)
            .where(
                SessionRow.store_id == store_id,
                SessionRow.is_staff.is_(False),
                SessionRow.started_at >= window_start,
                SessionRow.started_at < window_end,
            )
        )
    ).scalar() or 0

    stats = await db.execute(
        select(
            EventRow.zone_id,
            func.count(EventRow.event_id),
            func.avg(EventRow.dwell_ms),
        )
        .where(
            EventRow.store_id == store_id,
            EventRow.zone_id.is_not(None),
            EventRow.is_staff.is_(False),
            EventRow.timestamp >= window_start,
            EventRow.timestamp < window_end,
        )
        .group_by(EventRow.zone_id)
    )
    rows = stats.all()
    if not rows:
        return HeatmapResponse(
            store_id=store_id, zones=[], data_confidence="LOW", as_of=now
        )

    max_visits = max(r[1] for r in rows) or 1
    max_dwell = max(float(r[2] or 0) for r in rows) or 1.0
    zones: list[HeatmapZone] = []
    for zone_id, visits, dwell in rows:
        freq = (visits / max_visits) * 100.0
        dwell_norm = (float(dwell or 0) / max_dwell) * 100.0
        intensity = (freq * 0.6 + dwell_norm * 0.4)
        zones.append(
            HeatmapZone(
                zone_id=zone_id,
                visit_frequency=round(intensity, 2),
                avg_dwell_ms=float(dwell or 0),
            )
        )
    confidence = "HIGH" if session_count >= 20 else "LOW"
    return HeatmapResponse(
        store_id=store_id, zones=zones, data_confidence=confidence, as_of=now
    )
