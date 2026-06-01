from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.analytics_window import get_analytics_window
from backend.config import get_settings
from backend.feed_freshness import is_stale_feed, stale_feed_message
from backend.models import AnomalyRow, EventRow, SessionRow
from backend.schemas import AnomaliesResponse, AnomalyItem


async def detect_anomalies(db: AsyncSession, store_id: str) -> AnomaliesResponse:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    hour_ago = now - timedelta(hours=1)
    items: list[AnomalyItem] = []

    queue_q = await db.execute(
        select(EventRow.metadata_json)
        .where(
            EventRow.store_id == store_id,
            EventRow.event_type == "BILLING_QUEUE_JOIN",
            EventRow.timestamp >= hour_ago,
        )
        .order_by(EventRow.timestamp.desc())
        .limit(20)
    )
    import json

    depths = []
    for (meta_str,) in queue_q.all():
        if meta_str:
            qd = json.loads(meta_str).get("queue_depth")
            if isinstance(qd, int):
                depths.append(qd)
    if depths and max(depths) >= 3:
        items.append(
            AnomalyItem(
                anomaly_id=f"ANM_{uuid.uuid4().hex[:10]}",
                type="QUEUE_SPIKE",
                severity="WARN" if max(depths) < 5 else "CRITICAL",
                detected_at=now,
                root_cause=f"Billing queue depth peaked at {max(depths)} in the last hour.",
                suggested_action="Open another billing lane or deploy floor staff to queue bust.",
            )
        )

    window_start, window_end, _ = await get_analytics_window(db, store_id)
    sessions_today = (
        await db.execute(
            select(SessionRow).where(
                SessionRow.store_id == store_id,
                SessionRow.is_staff.is_(False),
                SessionRow.started_at >= window_start,
                SessionRow.started_at < window_end,
            )
        )
    ).scalars().all()
    entry_count = len(sessions_today)
    converted = sum(1 for s in sessions_today if s.converted)
    rate = (converted / entry_count) if entry_count else 0.0
    baseline = 0.35
    if entry_count >= 5 and rate < baseline * 0.6:
        items.append(
            AnomalyItem(
                anomaly_id=f"ANM_{uuid.uuid4().hex[:10]}",
                type="CONVERSION_DROP",
                severity="WARN",
                detected_at=now,
                root_cause=f"Conversion rate {rate:.1%} below expected ~{baseline:.0%}.",
                suggested_action="Review staffing at billing and promotional signage on high-dwell zones.",
            )
        )

    layout_zones = []
    try:
        from backend.config import load_json_config

        layout_zones = [
            z["zone_id"]
            for z in load_json_config("store_layout.json").get("zones", [])
            if z.get("type") == "product"
        ]
    except FileNotFoundError:
        pass

    for zone_id in layout_zones[:5]:
        recent = await db.execute(
            select(func.count())
            .select_from(EventRow)
            .where(
                EventRow.store_id == store_id,
                EventRow.zone_id == zone_id,
                EventRow.timestamp >= now - timedelta(minutes=30),
            )
        )
        if int(recent.scalar() or 0) == 0 and entry_count > 3:
            items.append(
                AnomalyItem(
                    anomaly_id=f"ANM_{uuid.uuid4().hex[:10]}",
                    type="DEAD_ZONE",
                    severity="INFO",
                    detected_at=now,
                    root_cause=f"No visits detected in zone {zone_id} for 30+ minutes.",
                    suggested_action="Check camera ROI calibration or refresh merchandising in this zone.",
                )
            )
            break

    last_event = (
        await db.execute(
            select(func.max(EventRow.timestamp)).where(EventRow.store_id == store_id)
        )
    ).scalar()
    if is_stale_feed(last_event, now=now, threshold_minutes=settings.stale_feed_minutes):
        items.append(
            AnomalyItem(
                anomaly_id=f"ANM_{uuid.uuid4().hex[:10]}",
                type="STALE_FEED",
                severity="CRITICAL",
                detected_at=now,
                root_cause=stale_feed_message(last_event, now=now),
                suggested_action="Restart pipeline worker and verify camera RTSP/clip ingestion.",
            )
        )

    for item in items:
        await db.merge(
            AnomalyRow(
                anomaly_id=item.anomaly_id,
                store_id=store_id,
                anomaly_type=item.type,
                severity=item.severity,
                detected_at=item.detected_at,
                root_cause=item.root_cause,
                suggested_action=item.suggested_action,
                active=True,
            )
        )
    await db.commit()
    return AnomaliesResponse(store_id=store_id, anomalies=items)
