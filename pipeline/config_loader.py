from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "configs" / "generated"
PROJECT = ROOT.parent


def load_camera_profile() -> dict:
    return json.loads((GENERATED / "camera_profile.json").read_text(encoding="utf-8"))


def load_store_layout() -> dict:
    return json.loads((GENERATED / "store_layout.json").read_text(encoding="utf-8"))


def footage_path(source_file: str) -> Path:
    return PROJECT / "CCTV Footage" / source_file
