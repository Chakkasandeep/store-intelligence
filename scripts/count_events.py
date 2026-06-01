"""Print event counts from output.jsonl — compare with manual video counts."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "data" / "events" / "output.jsonl"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not path.exists():
        print(f"Missing {path}. Run the pipeline first.")
        sys.exit(1)

    by_type: Counter[str] = Counter()
    by_camera: Counter[str] = Counter()
    visitors: set[str] = set()
    staff_events = 0
    lines = 0

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        lines += 1
        ev = json.loads(line)
        by_type[ev.get("event_type", "?")] += 1
        by_camera[ev.get("camera_id", "?")] += 1
        if ev.get("is_staff"):
            staff_events += 1
        else:
            visitors.add(ev.get("visitor_id", ""))

    print(f"File: {path}")
    print(f"Total events: {lines}")
    print(f"Unique visitors (non-staff): {len(visitors)}")
    print(f"Staff-tagged events: {staff_events}")
    print("\nBy event_type:")
    for k, v in sorted(by_type.items()):
        print(f"  {k}: {v}")
    print("\nBy camera_id:")
    for k, v in sorted(by_camera.items()):
        print(f"  {k}: {v}")
    print("\n--- Manual check ---")
    print("ENTRY count should be close to people entering on CAM 3 (entry camera).")
    print("Compare: open CAM 3.mp4 and count inbound crossings at the door.")


if __name__ == "__main__":
    main()
