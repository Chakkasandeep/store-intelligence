"""Run full discovery pipeline (POS, cameras, layout)."""
from __future__ import annotations

import json
from pathlib import Path

from discover_cameras import discover as discover_cameras
from discover_layout import discover as discover_layout
from discover_pos import main as discover_pos

GENERATED = Path(__file__).resolve().parents[1] / "configs" / "generated"


def main() -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    if (GENERATED / "pos_mapping.json").exists() and (GENERATED / "camera_profile.json").exists():
        print("Discovery configs already present - skipping")
        return
    try:
        discover_pos()
    except Exception as exc:
        print(f"discover_pos skipped: {exc}")
    try:
        discover_cameras()
    except Exception as exc:
        print(f"discover_cameras skipped: {exc}")
    try:
        discover_layout()
    except Exception as exc:
        print(f"discover_layout skipped: {exc}")
    print("Discovery complete -> configs/generated/")


if __name__ == "__main__":
    main()
