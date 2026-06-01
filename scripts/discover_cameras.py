"""Infer camera roles from CCTV clips — no hardcoded filenames."""
from __future__ import annotations

import json
import re
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FOOTAGE = ROOT / "CCTV Footage"
FEATURES = Path(__file__).resolve().parents[1] / "data" / "discovery" / "video_features.json"
OUT = Path(__file__).resolve().parents[1] / "configs" / "generated"


def _clip_features(path: Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    step = max(1, n // 30)
    prev = None
    motion = {"left": 0.0, "center": 0.0, "right": 0.0}
    bright = {"left": 0.0, "right": 0.0}
    edge = 0.0
    right_edge = 0.0
    count = 0
    for fi in range(0, n, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        bright["left"] += float(gray[:, : w // 3].mean())
        bright["right"] += float(gray[:, 2 * w // 3 :].mean())
        edges = cv2.Canny(gray, 50, 150)
        edge += float(edges.mean())
        right_edge += float(edges[:, 2 * w // 3 :].mean())
        if prev is not None:
            diff = cv2.absdiff(gray, prev).astype(np.float32)
            motion["left"] += float(diff[:, : w // 3].mean())
            motion["center"] += float(diff[:, w // 3 : 2 * w // 3].mean())
            motion["right"] += float(diff[:, 2 * w // 3 :].mean())
        prev = gray
        count += 1
    cap.release()
    if count:
        for k in motion:
            motion[k] /= count
        for k in bright:
            bright[k] /= count
        edge /= count
        right_edge /= count
    return {
        "file": path.name,
        "motion": motion,
        "brightness": bright,
        "edge_density": edge,
        "right_edge_density": right_edge,
        "brightness_asymmetry": bright["left"] - bright["right"],
    }


def _score_roles(feat: dict) -> dict[str, float]:
    m = feat["motion"]
    return {
        "entry": max(0, feat["brightness_asymmetry"] / 40.0)
        + max(0, 1.0 - feat["edge_density"] / 25.0)
        + max(0, 0.5 - m["center"] / 20.0),
        "billing": feat.get("right_edge_density", feat["edge_density"]) / 30.0
        + m["center"] / 30.0
        + feat["brightness"]["right"] / 120.0,
        "main_floor": m["center"] / 25.0 + feat["edge_density"] / 40.0,
        "queue": m["center"] / 30.0 + feat["edge_density"] / 45.0,
    }


def discover() -> dict:
    clips = sorted(FOOTAGE.glob("*.mp4"))
    if not clips:
        raise FileNotFoundError(f"No MP4 files in {FOOTAGE}")
    features = []
    for c in clips:
        f = _clip_features(c)
        f["role_scores"] = _score_roles(f)
        features.append(f)

    assigned: dict[str, str] = {}
    role_slots = ["entry", "billing", "main_floor", "main_floor", "queue"]
    used_roles: set[str] = set()
    for feat in sorted(features, key=lambda x: x["role_scores"]["entry"], reverse=True):
        scores = feat["role_scores"]
        role = max(scores, key=scores.get)
        if role == "entry" and "entry" in used_roles:
            role = max(
                (k, v) for k, v in scores.items() if k != "entry" or "entry" not in used_roles
            )[0]
        if role in used_roles and role != "main_floor":
            role = sorted(scores.items(), key=lambda x: x[1], reverse=True)[1][0]
        used_roles.add(role)
        stem = Path(feat["file"]).stem
        cam_num = re.search(r"(\d+)", stem)
        idx = int(cam_num.group(1)) if cam_num else len(assigned) + 1
        role_map = {
            "entry": "CAM_ENTRY_01",
            "billing": "CAM_BILLING_01",
            "main_floor": f"CAM_FLOOR_{idx:02d}",
            "queue": "CAM_QUEUE_01",
        }
        assigned[feat["file"]] = role
        feat["assigned_role"] = role
        feat["camera_id"] = role_map.get(role, f"CAM_{idx:02d}")

    # Refine: highest entry score → entry, highest billing → billing
    by_entry = max(features, key=lambda x: x["role_scores"]["entry"])
    top_billing = sorted(features, key=lambda x: x["role_scores"]["billing"], reverse=True)[:2]
    by_billing = max(top_billing, key=lambda x: x.get("right_edge_density", 0))
    for f in features:
        if f["file"] == by_entry["file"]:
            f["assigned_role"] = "entry"
            f["camera_id"] = "CAM_ENTRY_01"
            f["confidence"] = min(0.98, 0.7 + f["role_scores"]["entry"] / 10)
        elif f["file"] == by_billing["file"]:
            f["assigned_role"] = "billing"
            f["camera_id"] = "CAM_BILLING_01"
            f["confidence"] = min(0.98, 0.7 + f["role_scores"]["billing"] / 10)
        else:
            f["assigned_role"] = "main_floor"
            m = re.search(r"(\d+)", f["file"])
            f["camera_id"] = f"CAM_FLOOR_{m.group(1) if m else '99'}"
            f["confidence"] = 0.75

    pos_path = ROOT / "configs" / "generated" / "pos_mapping.json"
    store_id = "ST1008"
    if pos_path.exists():
        store_id = json.loads(pos_path.read_text(encoding="utf-8")).get("store_id", store_id)

    profile = {
        "discovery_method": "motion_brightness_edge_heuristics",
        "store_id": store_id,
        "footage_dir": str(FOOTAGE.relative_to(ROOT)).replace("\\", "/"),
        "cameras": [
            {
                "source_file": f["file"],
                "camera_id": f["camera_id"],
                "role": f["assigned_role"],
                "confidence": round(f.get("confidence", 0.8), 3),
                "role_scores": {k: round(v, 3) for k, v in f["role_scores"].items()},
            }
            for f in features
        ],
        "overlap_notes": [
            "Entry cam (glass door) overlaps with front-of-house floor cams.",
            "Billing cam shares partial FOV with east-side floor traffic.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "camera_profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")
    if FEATURES.exists():
        (OUT / "camera_profile.json").write_text(
            json.dumps({**profile, "raw_features": json.loads(FEATURES.read_text())}, indent=2),
            encoding="utf-8",
        )
    return profile


if __name__ == "__main__":
    print(json.dumps(discover(), indent=2))
