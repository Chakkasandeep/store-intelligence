# PROMPT: Test anomaly detection for queue spike, conversion drop, stale feed.
# CHANGES MADE: Synthetic queue_depth metadata triggers QUEUE_SPIKE; stale uses old timestamp event.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

STORE = "ST1008"


@pytest.mark.asyncio
async def test_queue_spike_anomaly(client):
    events = []
    for i in range(5):
        events.append(
            {
                "event_id": str(uuid.uuid4()),
                "store_id": STORE,
                "camera_id": "CAM_BILLING_01",
                "visitor_id": f"VIS_q_{i}",
                "event_type": "BILLING_QUEUE_JOIN",
                "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "zone_id": "BILLING",
                "dwell_ms": 0,
                "is_staff": False,
                "confidence": 0.85,
                "metadata": {"queue_depth": 4, "session_seq": 1},
            }
        )
    await client.post("/events/ingest", json={"events": events})
    r = await client.get(f"/stores/{STORE}/anomalies")
    assert r.status_code == 200
    types = {a["type"] for a in r.json()["anomalies"]}
    assert "QUEUE_SPIKE" in types


@pytest.mark.asyncio
async def test_stale_feed_anomaly(client):
    old = datetime.now(timezone.utc) - timedelta(minutes=30)
    await client.post(
        "/events/ingest",
        json={
            "events": [
                {
                    "event_id": str(uuid.uuid4()),
                    "store_id": STORE,
                    "camera_id": "CAM_ENTRY_01",
                    "visitor_id": "VIS_stale",
                    "event_type": "ENTRY",
                    "timestamp": old.isoformat().replace("+00:00", "Z"),
                    "dwell_ms": 0,
                    "is_staff": False,
                    "confidence": 0.5,
                    "metadata": {},
                }
            ]
        },
    )
    r = await client.get(f"/stores/{STORE}/anomalies")
    types = {a["type"] for a in r.json()["anomalies"]}
    assert "STALE_FEED" in types
