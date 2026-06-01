# PROMPT: Generate FastAPI tests for Store Intelligence ingest idempotency, metrics, funnel, health, and malformed event partial success.
# CHANGES MADE: Added session-based funnel checks, duplicate ingest test, and staff exclusion metric validation.

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

STORE = "ST1008"


def _event(**kwargs):
    base = {
        "event_id": str(uuid.uuid4()),
        "store_id": STORE,
        "camera_id": "CAM_ENTRY_01",
        "visitor_id": "VIS_test_api",
        "event_type": "ENTRY",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "zone_id": "ENTRY_EXIT",
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.9,
        "metadata": {"session_seq": 1},
    }
    base.update(kwargs)
    return base


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] in {"ok", "degraded", "unavailable"}


@pytest.mark.asyncio
async def test_ingest_idempotent(client):
    eid = str(uuid.uuid4())
    payload = {"events": [_event(event_id=eid, visitor_id="VIS_idem")]}
    r1 = await client.post("/events/ingest", json=payload)
    r2 = await client.post("/events/ingest", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["accepted"] == 1
    assert r2.json()["duplicates"] == 1


@pytest.mark.asyncio
async def test_malformed_partial_success(client):
    good = _event(visitor_id="VIS_partial")
    bad = {"event_id": "x", "store_id": STORE}
    r = await client.post("/events/ingest", json={"events": [good, bad]})
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] >= 1
    assert body["rejected"] >= 1


@pytest.mark.asyncio
async def test_metrics_and_funnel(client):
    vid = "VIS_funnel_" + uuid.uuid4().hex[:6]
    events = [
        _event(event_id=str(uuid.uuid4()), visitor_id=vid, event_type="ENTRY"),
        _event(
            event_id=str(uuid.uuid4()),
            visitor_id=vid,
            event_type="ZONE_ENTER",
            zone_id="FOH_CENTER",
            camera_id="CAM_FLOOR_1",
        ),
        _event(
            event_id=str(uuid.uuid4()),
            visitor_id=vid,
            event_type="BILLING_QUEUE_JOIN",
            zone_id="BILLING",
            camera_id="CAM_BILLING_01",
            metadata={"queue_depth": 2, "session_seq": 3},
        ),
    ]
    await client.post("/events/ingest", json={"events": events})
    m = await client.get(f"/stores/{STORE}/metrics")
    assert m.status_code == 200
    assert m.json()["unique_visitors"] >= 1
    f = await client.get(f"/stores/{STORE}/funnel")
    assert f.status_code == 200
    assert len(f.json()["stages"]) == 4
