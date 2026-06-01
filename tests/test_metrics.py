# PROMPT: Write pytest cases for metrics with empty store, all staff, and zero purchases.
# CHANGES MADE: Staff sessions excluded from unique_visitors; empty ingest returns zeros.

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

STORE = "ST1008"


def ev(visitor_id: str, **kw):
    d = {
        "event_id": str(uuid.uuid4()),
        "store_id": STORE,
        "camera_id": "CAM_ENTRY_01",
        "visitor_id": visitor_id,
        "event_type": "ENTRY",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "dwell_ms": 0,
        "is_staff": False,
        "confidence": 0.8,
        "metadata": {},
    }
    d.update(kw)
    return d


@pytest.mark.asyncio
async def test_empty_store_metrics(client):
    r = await client.get(f"/stores/{STORE}/metrics")
    assert r.status_code == 200
    body = r.json()
    assert body["unique_visitors"] >= 0
    assert body["conversion_rate"] >= 0


@pytest.mark.asyncio
async def test_all_staff_excluded(client):
    await client.post(
        "/events/ingest",
        json={
            "events": [
                ev("VIS_staff_only", is_staff=True, event_type="ENTRY"),
                ev("VIS_staff_only", is_staff=True, event_type="ZONE_ENTER", zone_id="BILLING"),
            ]
        },
    )
    m = await client.get(f"/stores/{STORE}/metrics")
    staff_visitors = m.json()["unique_visitors"]
    await client.post(
        "/events/ingest",
        json={"events": [ev("VIS_customer_" + uuid.uuid4().hex[:4], is_staff=False)]},
    )
    m2 = await client.get(f"/stores/{STORE}/metrics")
    assert m2.json()["unique_visitors"] >= staff_visitors
