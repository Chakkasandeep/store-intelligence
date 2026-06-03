from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def make_event(
    *,
    store_id: str,
    camera_id: str,
    visitor_id: str,
    event_type: str,
    timestamp: datetime,
    zone_id: str | None = None,
    dwell_ms: int = 0,
    is_staff: bool = False,
    confidence: float = 0.8,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "store_id": store_id,
        "camera_id": camera_id,
        "visitor_id": visitor_id,
        "event_type": event_type,
        "timestamp": timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "zone_id": zone_id,
        "dwell_ms": dwell_ms,
        "is_staff": is_staff,
        "confidence": round(confidence, 3),
        "metadata": metadata or {},
    }


class EventWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = path.open("w", encoding="utf-8")

    def write(self, event: dict[str, Any]) -> None:
        self._fh.write(json.dumps(event) + "\n")

    def close(self) -> None:
        self._fh.close()


def clip_base_timestamp(filename: str, store_id: str = "ST1008") -> datetime:
    """Align pipeline clock to footage OSD dates per store."""
    if store_id == "ST_STORE2" or any(k in filename.lower() for k in ["entry 1", "entry 2", "billing_area", "zone.mp4"]):
        return datetime(2026, 3, 8, 18, 10, 0, tzinfo=timezone.utc)
    return datetime(2026, 4, 10, 20, 9, 0, tzinfo=timezone.utc)


def ts_for_frame(base: datetime, frame_idx: int, fps: float) -> datetime:
    return base + timedelta(seconds=frame_idx / max(fps, 1.0))
