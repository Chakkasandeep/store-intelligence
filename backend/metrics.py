from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.analytics_window import get_analytics_window
from backend.config import get_settings
from backend.models import EventRow, SessionRow, TransactionRow
from backend.schemas import MetricsResponse


async def compute_metrics(db: AsyncSession, store_id: str) -> MetricsResponse:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    window_start, window_end, is_historical = await get_analytics_window(db, store_id)

    sessions_q = select(SessionRow).where(
        SessionRow.store_id == store_id,
        SessionRow.is_staff.is_(False),
        SessionRow.started_at >= window_start,
        SessionRow.started_at < window_end,
    )
    sessions = (await db.execute(sessions_q)).scalars().all()
    unique_visitors = len({s.visitor_id for s in sessions})

    if is_historical:
        current_visitors = 0
    else:
        open_sessions = [s for s in sessions if s.ended_at is None]
        current_visitors = len(open_sessions)

    converted = sum(1 for s in sessions if s.converted)
    conversion_rate = (converted / unique_visitors) if unique_visitors else 0.0

    dwell_q = await db.execute(
        select(func.avg(EventRow.dwell_ms)).where(
            EventRow.store_id == store_id,
            EventRow.event_type == "ZONE_DWELL",
            EventRow.is_staff.is_(False),
            EventRow.timestamp >= window_start,
            EventRow.timestamp < window_end,
        )
    )
    avg_dwell = float(dwell_q.scalar() or 0.0)

    queue_q = await db.execute(
        select(EventRow.metadata_json)
        .where(
            EventRow.store_id == store_id,
            EventRow.event_type.in_(["BILLING_QUEUE_JOIN", "BILLING_QUEUE_ABANDON"]),
            EventRow.timestamp >= window_start,
            EventRow.timestamp < window_end,
        )
        .order_by(EventRow.timestamp.desc())
        .limit(50)
    )
    queue_depth = 0
    for (meta_str,) in queue_q.all():
        if not meta_str:
            continue
        import json

        meta = json.loads(meta_str)
        qd = meta.get("queue_depth")
        if isinstance(qd, int):
            queue_depth = max(queue_depth, qd)

    joins = await db.execute(
        select(func.count())
        .select_from(EventRow)
        .where(
            EventRow.store_id == store_id,
            EventRow.event_type == "BILLING_QUEUE_JOIN",
            EventRow.timestamp >= window_start,
            EventRow.timestamp < window_end,
        )
    )
    abandons = await db.execute(
        select(func.count())
        .select_from(EventRow)
        .where(
            EventRow.store_id == store_id,
            EventRow.event_type == "BILLING_QUEUE_ABANDON",
            EventRow.timestamp >= window_start,
            EventRow.timestamp < window_end,
        )
    )
    j, a = int(joins.scalar() or 0), int(abandons.scalar() or 0)
    abandonment_rate = (a / j) if j else 0.0

    billing_visits = sum(1 for s in sessions if s.billing_visited)

    zone_q = await db.execute(
        select(EventRow.zone_id, func.count())
        .where(
            EventRow.store_id == store_id,
            EventRow.event_type.in_(["ZONE_ENTER", "ZONE_DWELL"]),
            EventRow.zone_id.is_not(None),
            EventRow.is_staff.is_(False),
            EventRow.timestamp >= window_start,
            EventRow.timestamp < window_end,
        )
        .group_by(EventRow.zone_id)
    )
    zone_visits = {z: int(c) for z, c in zone_q.all() if z}

    return MetricsResponse(
        store_id=store_id,
        unique_visitors=unique_visitors,
        current_visitors=current_visitors,
        conversion_rate=round(conversion_rate, 4),
        avg_dwell_time_ms=avg_dwell,
        queue_depth=queue_depth,
        abandonment_rate=round(abandonment_rate, 4),
        billing_visits=billing_visits,
        zone_visits=zone_visits,
        as_of=now,
    )


async def sync_pos_conversions(db: AsyncSession, store_id: str) -> None:
    """Mark sessions converted when billing visit precedes POS txn within window."""
    settings = get_settings()
    window = timedelta(minutes=settings.conversion_window_minutes)
    txns = (
        await db.execute(
            select(TransactionRow).where(TransactionRow.store_id == store_id)
        )
    ).scalars().all()
    if not txns:
        return
    sessions = (
        await db.execute(select(SessionRow).where(SessionRow.store_id == store_id))
    ).scalars().all()
    for txn in txns:
        for ses in sessions:
            if ses.is_staff or ses.converted or not ses.billing_visited:
                continue
            if ses.started_at <= txn.timestamp <= ses.started_at + window:
                ses.converted = True
    await db.commit()


async def load_pos_transactions(db: AsyncSession, store_id: str) -> int:
    import pandas as pd
    from pathlib import Path

    from backend.config import ROOT as SI_ROOT

    path = SI_ROOT / "configs" / "generated" / "pos_transactions_derived.csv"
    if not path.exists():
        return 0
    df = pd.read_csv(path)
    count = 0
    for _, row in df.iterrows():
        tid = str(row["order_id"])
        ts = pd.to_datetime(row["timestamp"], utc=True)
        existing = await db.get(TransactionRow, tid)
        if existing:
            continue
        db.add(
            TransactionRow(
                transaction_id=tid,
                store_id=store_id,
                timestamp=ts.to_pydatetime(),
                amount_inr=float(row.get("nmv", 0)),
            )
        )
        count += 1
    await db.commit()
    await sync_pos_conversions(db, store_id)
    return count
