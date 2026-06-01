"""Build store_layout.json from floor-plan image + POS store metadata."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "configs" / "generated"


def _extract_layout_image() -> Path | None:
    for xlsx in ROOT.glob("*layout*.xlsx"):
        with zipfile.ZipFile(xlsx) as z:
            for name in z.namelist():
                if name.startswith("xl/media/") and name.endswith(".png"):
                    dest = Path(__file__).resolve().parents[1] / "data" / "layout" / Path(name).name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(z.read(name))
                    return dest
    return None


def discover() -> dict:
    pos_path = OUT / "pos_mapping.json"
    store_id, store_name = "ST1008", "Brigade_Bangalore"
    if pos_path.exists():
        pos = json.loads(pos_path.read_text(encoding="utf-8"))
        store_id = pos.get("store_id", store_id)
        store_name = pos.get("store_name", store_name)

    img = _extract_layout_image()
    # Zones inferred from floor plan labels (see STORE_LAYOUT_ANALYSIS.md)
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
    layout = {
        "store_id": store_id,
        "store_name": store_name,
        "source": str(img.name) if img else "layout_xlsx",
        "open_hours_local": {"open": "10:00", "close": "22:00"},
        "zones": zones,
        "camera_zone_map": {
            "CAM_ENTRY_01": ["ENTRY_EXIT", "FOH_CENTER"],
            "CAM_BILLING_01": ["BILLING", "ACCESSORIES"],
            "CAM_QUEUE_01": ["BILLING"],
        },
        "confidence": 0.88 if img else 0.6,
        "assumptions": [
            "Zone polygons in pipeline use normalized ROIs per camera role, not CAD coordinates.",
            "Brand-level zones on north/south walls are grouped for dwell analytics.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "store_layout.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")
    return layout


if __name__ == "__main__":
    print(json.dumps(discover(), indent=2))
