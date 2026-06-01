"""Discovery: extract per-clip visual features for camera role inference."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FOOTAGE = ROOT / "CCTV Footage"
OUT = Path(__file__).resolve().parents[1] / "data" / "discovery"
SHOTS = OUT / "screenshots"


def analyze_clip(mp4: Path) -> dict:
    cap = cv2.VideoCapture(str(mp4))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    meta: dict = {
        "file": mp4.name,
        "width": w,
        "height": h,
        "frame_count": n,
        "fps": fps,
        "duration_sec": n / fps if fps else 0,
        "frames": [],
    }
    SHOTS.mkdir(parents=True, exist_ok=True)
    for ratio in (0.1, 0.5, 0.9):
        fi = int(n * ratio)
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        shot = SHOTS / f"{mp4.stem.replace(' ', '_')}_f{fi}.jpg"
        cv2.imwrite(str(shot), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        meta["frames"].append(
            {
                "frame_idx": fi,
                "edge_density": float(edges.mean()),
                "brightness": {
                    "left": float(gray[:, : w // 3].mean()),
                    "center": float(gray[:, w // 3 : 2 * w // 3].mean()),
                    "right": float(gray[:, 2 * w // 3 :].mean()),
                },
                "screenshot": str(shot.relative_to(OUT.parent.parent)).replace("\\", "/"),
            }
        )
    cap.release()

    cap = cv2.VideoCapture(str(mp4))
    prev = None
    motion = {"center": 0.0, "left": 0.0, "right": 0.0}
    step = max(1, n // 40)
    count = 0
    for fi in range(0, n, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, frame = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev is not None:
            diff = cv2.absdiff(g, prev).astype(np.float32)
            motion["center"] += float(diff[:, w // 3 : 2 * w // 3].mean())
            motion["left"] += float(diff[:, : w // 3].mean())
            motion["right"] += float(diff[:, 2 * w // 3 :].mean())
            count += 1
        prev = g
    cap.release()
    if count:
        for k in motion:
            motion[k] /= count
    meta["motion"] = motion
    return meta


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = [analyze_clip(p) for p in sorted(FOOTAGE.glob("*.mp4"))]
    (OUT / "video_features.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {len(results)} clip profiles to {OUT / 'video_features.json'}")


if __name__ == "__main__":
    main()
