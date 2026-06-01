"""Analytics time window — uses dataset event range, not wall-clock 'today'."""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import load_json_config
from backend.models import EventRow


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _window_from_pos_date() -> tuple[datetime, datetime] | None:
    try:
        pos = load_json_config("pos_mapping.json")
        raw = pos.get("date")
        if not raw:
            return None
        day = datetime.strptime(str(raw), "%d-%m-%Y").date()
        start = datetime.combine(day, time.min, tzinfo=timezone.utc)
        end = datetime.combine(day, time.max, tzinfo=timezone.utc)
        return start, end
    except (FileNotFoundError, ValueError, OSError):
        return None


async def get_analytics_window(
    db: AsyncSession, store_id: str
) -> tuple[datetime, datetime, bool]:
    """
    Returns (window_start, window_end, is_historical).

    Prefer min/max timestamps from ingested events so CCTV clip day (e.g. Apr 10)
    matches metrics when the server runs on a later calendar day (e.g. Jun 1).
    """
    row = await db.execute(
        select(
            func.min(EventRow.timestamp),
            func.max(EventRow.timestamp),
        ).where(EventRow.store_id == store_id)
    )
    min_ts, max_ts = row.one()
    now = datetime.now(timezone.utc)

    if min_ts is not None and max_ts is not None:
        start = _utc(min_ts).replace(hour=0, minute=0, second=0, microsecond=0)
        end = _utc(max_ts) + timedelta(seconds=1)
        historical = _utc(max_ts).date() < now.date()
        return start, end, historical

    fallback = _window_from_pos_date()
    if fallback:
        start, end = fallback
        historical = end.date() < now.date()
        return start, end, historical

    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now, False
