"""Stale-feed logic that respects historical CCTV clip timestamps (e.g. Apr 2026 footage)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_stale_feed(
    last_event_at: datetime | None,
    *,
    now: datetime | None = None,
    threshold_minutes: int = 10,
) -> bool:
    """
    Return True only when the latest event is from *today* (UTC) but older than threshold.

    Historical challenge clips use past timestamps (e.g. 2026-04-10). Comparing those to
    wall-clock 'now' would always look ~50 days stale — that is a false positive.
    """
    if last_event_at is None:
        return True

    now = _utc(now or datetime.now(timezone.utc))
    last = _utc(last_event_at)

    if last.date() < now.date():
        return False

    return (now - last) > timedelta(minutes=threshold_minutes)


def stale_feed_message(last_event_at: datetime | None, now: datetime | None = None) -> str:
    now = _utc(now or datetime.now(timezone.utc))
    if last_event_at is None:
        return "No events have been ingested yet."
    last = _utc(last_event_at)
    if last.date() < now.date():
        return (
            f"Historical dataset: latest event at {last.isoformat()} "
            f"(clip/POS day). Wall-clock stale check suppressed."
        )
    lag_min = int((now - last).total_seconds() // 60)
    return f"No new events for {lag_min} minutes (within today's window)."
