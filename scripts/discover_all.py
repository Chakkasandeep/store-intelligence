"""Run full discovery pipeline (POS, cameras, layout) for both stores."""
from __future__ import annotations

import json
from pathlib import Path

from discover_cameras import discover as discover_cameras
from discover_layout import discover as discover_layout
from discover_pos import main as discover_pos

GENERATED = Path(__file__).resolve().parents[1] / "configs" / "generated"


def main() -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    print("Running multi-store discovery pipeline...")
    
    try:
        pos_res = discover_pos()
        print(f"POS Discovery complete. Found stores: {list(pos_res.keys())}")
    except Exception as exc:
        print(f"discover_pos failed: {exc}")
        
    try:
        cam_res = discover_cameras()
        print(f"Camera Discovery complete. Profiled stores: {list(cam_res.keys())}")
    except Exception as exc:
        print(f"discover_cameras failed: {exc}")
        
    try:
        lay_res = discover_layout()
        print(f"Layout Discovery complete. Mapped stores: {list(lay_res.keys())}")
    except Exception as exc:
        print(f"discover_layout failed: {exc}")
        
    print("All Discovery complete -> configs/generated/")


if __name__ == "__main__":
    main()
