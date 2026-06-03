"""Infer camera roles for Store 1 and Store 2 dynamically with visual audit overrides."""
from __future__ import annotations

import json
from pathlib import Path
import cv2

ROOT = Path(__file__).resolve().parents[2]
FEATURES_JSON = Path(__file__).resolve().parents[1] / "data" / "discovery" / "new_dataset_camera_audit.json"
OUT_BASE = Path(__file__).resolve().parents[1] / "configs" / "generated"

# Explicit overrides matching the visual audit findings
VISUAL_OVERRIDES = {
    "CAM 5 - billing.mp4": "billing",
    "CAM 2 - zone.mp4": "main_floor",
    "CAM 1 - zone.mp4": "main_floor",
    "CAM 3 - entry.mp4": "entry",
    "billing_area.mp4": "billing",
    "entry 1.mp4": "entry",
    "entry 2.mp4": "entry",
    "zone.mp4": "main_floor"
}


def _clip_features(path: Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.release()
    return {
        "file": path.name,
        "width": w,
        "frame_count": n,
        "fps": round(fps, 2),
        "duration_sec": round(n / fps, 1),
    }


def discover_store(store_folder_name: str, store_id: str) -> dict:
    store_dir = ROOT / store_folder_name
    if not store_dir.exists():
        store_dir = Path(__file__).resolve().parents[1] / store_folder_name

    clips = sorted(store_dir.glob("*.mp4"))
    if not clips:
        store_dir = Path(__file__).resolve().parents[1] / "data" / store_folder_name
        clips = sorted(store_dir.glob("*.mp4"))

    audit_features = {}
    if FEATURES_JSON.exists():
        try:
            audit_features = json.loads(FEATURES_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass

    store_audit = audit_features.get(store_folder_name, [])
    audit_map = {item["file"]: item for item in store_audit}

    cameras = []
    for c in clips:
        # Determine role from override, else audit file, else fallback
        if c.name in VISUAL_OVERRIDES:
            assigned_role = VISUAL_OVERRIDES[c.name]
            confidence = 0.95
            reason = "Visual audit override matching physical counter/signage"
        elif c.name in audit_map:
            feat = audit_map[c.name]
            role = feat["classified_role"].lower()
            if "entry" in role:
                assigned_role = "entry"
            elif "billing" in role:
                assigned_role = "billing"
            else:
                assigned_role = "main_floor"
            confidence = feat.get("confidence", 0.8)
            reason = feat.get("reasoning", "")
        else:
            name_lower = c.name.lower()
            if "entry" in name_lower:
                assigned_role = "entry"
            elif "billing" in name_lower or "cash" in name_lower:
                assigned_role = "billing"
            else:
                assigned_role = "main_floor"
            confidence = 0.8
            reason = "Filename pattern match fallback"

        # Load video shape features
        if c.name in audit_map:
            feat = audit_map[c.name]
        else:
            feat = _clip_features(c)

        # Assign systematic camera IDs based on count
        if assigned_role == "entry":
            entry_cams = [cam for cam in cameras if cam["role"] == "entry"]
            camera_id = f"CAM_ENTRY_{len(entry_cams) + 1:02d}"
        elif assigned_role == "billing":
            billing_cams = [cam for cam in cameras if cam["role"] == "billing"]
            camera_id = f"CAM_BILLING_{len(billing_cams) + 1:02d}"
        else:
            floor_cams = [cam for cam in cameras if cam["role"] == "main_floor"]
            camera_id = f"CAM_FLOOR_{len(floor_cams) + 1:02d}"

        cameras.append({
            "source_file": c.name,
            "camera_id": camera_id,
            "role": assigned_role,
            "confidence": round(confidence, 3),
            "width": feat.get("width", 1920),
            "frame_count": feat.get("frame_count", 3000),
            "fps": feat.get("fps", 25.0),
            "reasoning": reason,
        })

    profile = {
        "discovery_method": "features_json_and_fallbacks",
        "store_id": store_id,
        "store_folder": store_folder_name,
        "footage_dir": str(store_dir.relative_to(ROOT) if store_dir.is_relative_to(ROOT) else store_dir).replace("\\", "/"),
        "cameras": cameras,
        "overlap_notes": [
            "Entry camera views overlap with front of house traffic.",
            "Billing queue areas partially captured by floor cameras."
        ],
    }

    out_dir = OUT_BASE / store_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "camera_profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")

    # Backwards compatibility root copy
    if store_id == "ST1008":
        (OUT_BASE / "camera_profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")

    return profile


def discover() -> dict:
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    p1 = discover_store("Store 1", "ST1008")
    p2 = discover_store("Store 2", "ST_STORE2")
    return {"ST1008": p1, "ST_STORE2": p2}


if __name__ == "__main__":
    print(json.dumps(discover(), indent=2))
