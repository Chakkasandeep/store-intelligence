from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "configs" / "generated"
PROJECT = ROOT.parent


def load_camera_profile(store_id: str = "ST1008") -> dict:
    path = GENERATED / store_id / "camera_profile.json"
    if not path.exists():
        path = GENERATED / "camera_profile.json"  # fallback
    return json.loads(path.read_text(encoding="utf-8"))


def load_store_layout(store_id: str = "ST1008") -> dict:
    path = GENERATED / store_id / "store_layout.json"
    if not path.exists():
        path = GENERATED / "store_layout.json"  # fallback
    return json.loads(path.read_text(encoding="utf-8"))


def footage_path(store_id: str, source_file: str) -> Path:
    profile = load_camera_profile(store_id)
    folder = profile.get("store_folder")
    if not folder:
        # Fallback heuristic based on store_id
        folder = "Store 1" if store_id == "ST1008" else "Store 2"
    return PROJECT / folder / source_file
