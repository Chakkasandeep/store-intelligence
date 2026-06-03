# PROMPT: Unit-test multi-store pipeline config loading, dynamic zone mapping, and event schema emission for the new 4-camera dataset.
# CHANGES MADE: Updated tests to check both ST1008 and ST_STORE2 config directories, dynamic zones with loaded layouts, and 4-camera clips.

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "configs" / "generated"


def test_discovery_configs_exist():
    # Verify root copy fallback exists
    assert (GENERATED / "camera_profile.json").exists()
    assert (GENERATED / "store_layout.json").exists()
    assert (GENERATED / "pos_mapping.json").exists()
    
    # Verify store-specific folders exist
    assert (GENERATED / "ST1008" / "camera_profile.json").exists()
    assert (GENERATED / "ST1008" / "store_layout.json").exists()
    assert (GENERATED / "ST_STORE2" / "camera_profile.json").exists()
    assert (GENERATED / "ST_STORE2" / "store_layout.json").exists()


def test_camera_profiles_have_four_clips():
    # Store 1 ST1008
    profile1 = json.loads((GENERATED / "ST1008" / "camera_profile.json").read_text(encoding="utf-8"))
    assert len(profile1["cameras"]) == 4
    roles1 = {c["role"] for c in profile1["cameras"]}
    assert "entry" in roles1
    assert "billing" in roles1

    # Store 2 ST_STORE2
    profile2 = json.loads((GENERATED / "ST_STORE2" / "camera_profile.json").read_text(encoding="utf-8"))
    assert len(profile2["cameras"]) == 4
    roles2 = {c["role"] for c in profile2["cameras"]}
    assert "entry" in roles2
    assert "billing" in roles2


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


def test_zone_point_mapping_dynamic():
    from pipeline.config_loader import load_store_layout
    from pipeline.zones import zone_for_point

    layout1 = load_store_layout("ST1008")
    z1 = zone_for_point(0.5, 0.7, "entry", layout1)
    assert z1 in {"ENTRY_EXIT", "FOH_CENTER", None}

    layout2 = load_store_layout("ST_STORE2")
    z2 = zone_for_point(0.1, 0.3, "billing", layout2)
    assert z2 in {"BILLING", "ACCESSORIES", None}
