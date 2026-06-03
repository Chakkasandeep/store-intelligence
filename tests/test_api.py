# PROMPT: Generate FastAPI integration tests for multi-store metrics, health, event ingestion, legacy schema normalizer, and re-entry visitor handling.
# CHANGES MADE: Added tests for sample/legacy event normalizer, re-entry session persistence, and ST1008 vs ST_STORE2 metrics separation.

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
    body = r.json()
    assert body["status"] in {"ok", "degraded", "unavailable"}
    assert len(body["stores"]) >= 2
    store_ids = {s["store_id"] for s in body["stores"]}
    assert "ST1008" in store_ids
    assert "ST_STORE2" in store_ids


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
            camera_id="CAM_FLOOR_01",
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
    
    # Store 1 metrics
    m = await client.get(f"/stores/{STORE}/metrics")
    assert m.status_code == 200
    assert m.json()["unique_visitors"] >= 1
    
    # Store 1 funnel
    f = await client.get(f"/stores/{STORE}/funnel")
    assert f.status_code == 200
    assert len(f.json()["stages"]) == 4


@pytest.mark.asyncio
async def test_legacy_event_normalization(client):
    # Try ingesting a legacy sample shape (e.g. from sample_eventsbe42122.jsonl)
    legacy_payload = {
        "events": [
            {
                "event_type": "entry",
                "id_token": "ID_TEST_99",
                "store_code": "store_1076",
                "camera_id": "cam1",
                "event_timestamp": "2026-03-08T18:10:05.120000",
                "is_staff": False
            }
        ]
    }
    r = await client.post("/events/ingest", json=legacy_payload)
    assert r.status_code == 200
    body = r.json()
    assert body["accepted"] == 1
    assert body["rejected"] == 0
    
    # Verify the normalized store_id and visitor_id exist in the DB
    m = await client.get("/stores/ST1076/metrics")
    assert m.status_code == 200
    assert m.json()["unique_visitors"] == 1


@pytest.mark.asyncio
async def test_reentry_session_reopen(client):
    vid = "VIS_reentry_" + uuid.uuid4().hex[:6]
    
    # 1. Enter
    e1 = _event(event_id=str(uuid.uuid4()), visitor_id=vid, event_type="ENTRY")
    await client.post("/events/ingest", json={"events": [e1]})
    
    # 2. Exit
    e2 = _event(event_id=str(uuid.uuid4()), visitor_id=vid, event_type="EXIT")
    await client.post("/events/ingest", json={"events": [e2]})
    
    # 3. Re-entry
    e3 = _event(event_id=str(uuid.uuid4()), visitor_id=vid, event_type="REENTRY")
    await client.post("/events/ingest", json={"events": [e3]})
    
    # Verify we don't have multiple active sessions causing double counting
    m = await client.get(f"/stores/{STORE}/metrics")
    assert m.status_code == 200
    assert m.json()["unique_visitors"] == 1


@pytest.mark.asyncio
async def test_websocket_isolation(db_engine):
    from fastapi.testclient import TestClient
    from backend.main import app, _connections
    
    client = TestClient(app)
    assert len(_connections) == 0
    
    with client.websocket_connect("/ws/metrics?store_id=ST1008") as ws1:
        with client.websocket_connect("/ws/metrics?store_id=ST_STORE2") as ws2:
            assert len(_connections) == 2
            stores = list(_connections.values())
            assert "ST1008" in stores
            assert "ST_STORE2" in stores
            
            # Read first frames
            d1 = ws1.receive_json()
            d2 = ws2.receive_json()
            assert d1["store_id"] == "ST1008"
            assert d2["store_id"] == "ST_STORE2"
    
    assert len(_connections) == 0

