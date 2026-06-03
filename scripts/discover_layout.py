"""Build store_layout.json files with layout images and coordinate registries per store."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_BASE = Path(__file__).resolve().parents[1] / "configs" / "generated"
LAYOUT_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "layout"


def copy_layout_images() -> dict[str, str]:
    LAYOUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    mappings = {}
    
    # Store 1 layout PNG
    src1 = ROOT / "Store 1" / "Store 1 - layout.png"
    if src1.exists():
        dest1 = LAYOUT_DATA_DIR / "ST1008.png"
        shutil.copy(src1, dest1)
        mappings["ST1008"] = dest1.name
        
    # Store 2 layout PNG
    src2 = ROOT / "Store 2" / "store 2 - layout.png"
    if src2.exists():
        dest2 = LAYOUT_DATA_DIR / "ST_STORE2.png"
        shutil.copy(src2, dest2)
        mappings["ST_STORE2"] = dest2.name
        
    return mappings


def process_layout(store_id: str, store_name: str, img_name: str | None) -> dict:
    out_dir = OUT_BASE / store_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Standard retail zones per store layout
    zones = [
        {"zone_id": "ENTRY_EXIT", "label": "Main entrance threshold", "type": "traffic"},
        {"zone_id": "FOH_CENTER", "label": "Front of house / central aisle", "type": "traffic"},
        {"zone_id": "SKIN_NORTH", "label": "North wall skincare brands", "type": "product"},
        {"zone_id": "MAKEUP_SOUTH", "label": "South wall makeup brands", "type": "product"},
        {"zone_id": "FRAGRANCE_ISLAND", "label": "Fragrance & nail gondola", "type": "product"},
        {"zone_id": "MAKEUP_UNITS", "label": "Central makeup consultation units", "type": "product"},
        {"zone_id": "BILLING", "label": "Cash counter / POS", "type": "billing"},
        {"zone_id": "ACCESSORIES", "label": "Accessories wall", "type": "product"},
        {"zone_id": "PMU", "label": "PMU service nook", "type": "service"},
    ]

    # Normalized polygon coordinates stored in configuration JSON instead of code
    role_polygons = {
        "entry": [
            {"zone_id": "ENTRY_EXIT", "polygon": [[0.35, 0.35], [0.95, 0.35], [0.95, 0.95], [0.35, 0.95]]},
            {"zone_id": "FOH_CENTER", "polygon": [[0.0, 0.4], [0.5, 0.4], [0.5, 1.0], [0.0, 1.0]]}
        ],
        "billing": [
            {"zone_id": "BILLING", "polygon": [[0.0, 0.2], [0.75, 0.2], [0.75, 0.95], [0.0, 0.95]]},
            {"zone_id": "ACCESSORIES", "polygon": [[0.7, 0.0], [1.0, 0.0], [1.0, 1.0], [0.7, 1.0]]}
        ],
        "main_floor": [
            {"zone_id": "FOH_CENTER", "polygon": [[0.2, 0.3], [0.8, 0.3], [0.8, 0.95], [0.2, 0.95]]},
            {"zone_id": "SKIN_NORTH", "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 0.35], [0.0, 0.35]]},
            {"zone_id": "MAKEUP_SOUTH", "polygon": [[0.0, 0.65], [1.0, 0.65], [1.0, 1.0], [0.0, 1.0]]}
        ]
    }

    # Camera mappings based on visual audit
    if store_id == "ST1008":
        camera_zone_map = {
            "CAM_ENTRY_01": ["ENTRY_EXIT", "FOH_CENTER"],
            "CAM_BILLING_01": ["BILLING", "ACCESSORIES"],
            "CAM_FLOOR_01": ["FOH_CENTER", "SKIN_NORTH"],
            "CAM_FLOOR_02": ["FOH_CENTER", "MAKEUP_SOUTH"]
        }
    else:  # ST_STORE2
        camera_zone_map = {
            "CAM_ENTRY_01": ["ENTRY_EXIT", "FOH_CENTER"],
            "CAM_ENTRY_02": ["ENTRY_EXIT", "FOH_CENTER"],
            "CAM_BILLING_01": ["BILLING"],
            "CAM_FLOOR_01": ["FOH_CENTER", "SKIN_NORTH", "MAKEUP_SOUTH"]
        }

    layout = {
        "store_id": store_id,
        "store_name": store_name,
        "source": img_name or "layout_xlsx",
        "open_hours_local": {"open": "10:00", "close": "22:00"},
        "zones": zones,
        "role_polygons": role_polygons,
        "camera_zone_map": camera_zone_map,
        "confidence": 0.90 if img_name else 0.6,
        "assumptions": [
            "Zone polygons use normalized coordinates relative to camera role frames.",
            "PMU service nook is not active in primary tracking zone."
        ]
    }

    (out_dir / "store_layout.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")
    
    # If Store 1, write a copy to old generated path for backwards compatibility
    if store_id == "ST1008":
        (OUT_BASE / "store_layout.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")
        
    return layout


def discover() -> dict:
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    images = copy_layout_images()
    
    l1 = process_layout("ST1008", "Brigade_Bangalore", images.get("ST1008"))
    l2 = process_layout("ST_STORE2", "Store_2_Mall", images.get("ST_STORE2"))
    
    return {"ST1008": l1, "ST_STORE2": l2}


if __name__ == "__main__":
    print(json.dumps(discover(), indent=2))
