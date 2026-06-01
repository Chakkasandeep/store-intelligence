# PROMPT: Unit-test pipeline config loading, zone mapping, and event schema emission without full YOLO run.
# CHANGES MADE: Tests discovery JSON presence and emit.make_event schema keys.

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "configs" / "generated"


def test_discovery_configs_exist():
    assert (GENERATED / "camera_profile.json").exists()
    assert (GENERATED / "store_layout.json").exists()
    assert (GENERATED / "pos_mapping.json").exists()


def test_camera_profile_has_five_clips():
    profile = json.loads((GENERATED / "camera_profile.json").read_text(encoding="utf-8"))
    assert len(profile["cameras"]) == 5
    roles = {c["role"] for c in profile["cameras"]}
    assert "entry" in roles


def test_emit_schema():
    from pipeline.emit import make_event

    ev = make_event(
        store_id="ST1008",
        camera_id="CAM_ENTRY_01",
        visitor_id="VIS_x",
        event_type="ENTRY",
        timestamp=datetime.now(timezone.utc),
        confidence=0.42,
    )
    assert ev["event_id"]
    assert ev["confidence"] == 0.42
    assert ev["timestamp"].endswith("Z")


def test_zone_point_mapping():
    from pipeline.zones import zone_for_point

    z = zone_for_point(0.5, 0.7, "entry")
    assert z in {"ENTRY_EXIT", "FOH_CENTER", None}
