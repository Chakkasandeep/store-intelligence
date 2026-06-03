"""
Process CCTV clips with YOLOv8n + ByteTrack and emit challenge schema events.
Supports config-driven layouts, multiple stores, and exits.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.config_loader import footage_path, load_camera_profile, load_store_layout
from pipeline.emit import EventWriter, clip_base_timestamp, make_event, ts_for_frame
from pipeline.reid import ReIDBank
from pipeline.staff import TrackStats, classify_staff
from pipeline.zones import zone_for_point

PERSON_CLASS = 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--store-id", default="ST1008")
    p.add_argument("--output", default="")
    p.add_argument("--frame-stride", type=int, default=6)
    p.add_argument("--max-frames", type=int, default=0, help="0 = all frames")
    p.add_argument("--conf", type=float, default=0.25)
    return p.parse_args()


def process_clip(
    model,
    cam: dict,
    store_id: str,
    layout: dict,
    writer: EventWriter,
    global_reid: ReIDBank,
    frame_stride: int,
    max_frames: int,
    conf: float,
) -> None:
    path = footage_path(store_id, cam["source_file"])
    if not path.exists():
        print(f"Video file not found: {path} - skipping this camera")
        return
        
    role = cam["role"]
    camera_id = cam["camera_id"]
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    base = clip_base_timestamp(cam["source_file"], store_id)

    track_stats: dict[int, TrackStats] = defaultdict(TrackStats)
    visitor_map: dict[int, str] = {}
    session_state: dict[str, dict] = {}
    
    # Active zones and queue tracking
    active_zones: dict[str, str | None] = defaultdict(lambda: None)
    in_queue: dict[str, bool] = defaultdict(bool)
    
    queue_depth = 0
    queued_visitors: set[str] = set()
    prev_centroids: dict[int, tuple[float, float]] = {}
    entered: set[str] = set()
    exited: set[str] = set()
    zone_entered: dict[tuple[str, str], bool] = {}
    dwell_accum: dict[tuple[str, str], int] = defaultdict(int)
    seq: dict[str, int] = defaultdict(int)

    processed = 0
    frame_idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % frame_stride != 0:
            frame_idx += 1
            continue
        if max_frames and processed >= max_frames:
            break
        processed += 1
        h, w = frame.shape[:2]
        ts = ts_for_frame(base, frame_idx, fps)
        results = model.track(
            frame,
            persist=True,
            classes=[PERSON_CLASS],
            conf=conf,
            verbose=False,
            tracker="bytetrack.yaml",
        )
        boxes = results[0].boxes
        if boxes is None:
            frame_idx += 1
            continue
        ids = boxes.id
        if ids is None:
            frame_idx += 1
            continue
            
        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        
        present_visitors = set()
        
        for i, tid in enumerate(ids.int().tolist()):
            x1, y1, x2, y2 = xyxy[i]
            cx, cy = (x1 + x2) / 2 / w, (y1 + y2) / 2 / h
            crop = frame[max(0, int(y1)) : min(h, int(y2)), max(0, int(x1)) : min(w, int(x2))]
            
            if tid not in visitor_map:
                if crop.size > 0:
                    vid, reid_conf = global_reid.match_or_create(crop, frame_idx / fps)
                else:
                    vid, reid_conf = f"VIS_{tid}", 0.7
                visitor_map[tid] = vid
            else:
                reid_conf = 0.85
                if crop.size > 0:
                    global_reid.match_or_create(crop, frame_idx / fps)

            vid = visitor_map[tid]
            present_visitors.add(vid)
            
            st = track_stats[tid]
            st.frames += 1
            st.camera_roles.add(role)
            
            z = zone_for_point(cx, cy, role, layout)
            if z:
                st.zones.add(z)
            if tid in prev_centroids:
                px, py = prev_centroids[tid]
                st.total_movement += abs(cx - px) + abs(cy - py)
            prev_centroids[tid] = (cx, cy)

            is_staff, staff_conf = classify_staff(st, n)
            det_conf = float(confs[i])
            meta_base = {
                "track_id": str(tid),
                "staff_confidence": staff_conf,
                "session_seq": 0,
            }

            # 1. Entry / Exit Crossing Logic
            if role == "entry":
                line_y = 0.55
                if vid not in entered and cy > line_y and cy < 0.92:
                    entered.add(vid)
                    seq[vid] += 1
                    meta = {**meta_base, "session_seq": seq[vid]}
                    writer.write(
                        make_event(
                            store_id=store_id,
                            camera_id=camera_id,
                            visitor_id=vid,
                            event_type="ENTRY",
                            timestamp=ts,
                            zone_id="ENTRY_EXIT",
                            is_staff=is_staff,
                            confidence=min(det_conf, reid_conf),
                            metadata=meta,
                        )
                    )
                    session_state[vid] = {"active": True, "exited": False}
                elif vid in session_state and session_state[vid].get("active") and cy < line_y - 0.05:
                    if vid not in exited:
                        exited.add(vid)
                        
                        # Emit active zone exit first if present
                        if active_zones[vid]:
                            seq[vid] += 1
                            writer.write(
                                make_event(
                                    store_id=store_id,
                                    camera_id=camera_id,
                                    visitor_id=vid,
                                    event_type="ZONE_EXIT",
                                    timestamp=ts,
                                    zone_id=active_zones[vid],
                                    is_staff=is_staff,
                                    confidence=det_conf,
                                    metadata={**meta_base, "session_seq": seq[vid], "sku_zone": active_zones[vid]},
                                )
                            )
                            active_zones[vid] = None
                            
                        # Emit queue abandon if exited store while in queue
                        if in_queue[vid]:
                            in_queue[vid] = False
                            seq[vid] += 1
                            writer.write(
                                make_event(
                                    store_id=store_id,
                                    camera_id=camera_id,
                                    visitor_id=vid,
                                    event_type="BILLING_QUEUE_ABANDON",
                                    timestamp=ts,
                                    zone_id="BILLING",
                                    is_staff=is_staff,
                                    confidence=det_conf,
                                    metadata={**meta_base, "session_seq": seq[vid]},
                                )
                            )
                            
                        seq[vid] += 1
                        writer.write(
                            make_event(
                                store_id=store_id,
                                camera_id=camera_id,
                                visitor_id=vid,
                                event_type="EXIT",
                                timestamp=ts,
                                zone_id="ENTRY_EXIT",
                                is_staff=is_staff,
                                confidence=det_conf,
                                metadata={**meta_base, "session_seq": seq[vid]},
                            )
                        )
                        session_state[vid]["active"] = False
                        session_state[vid]["exited"] = True
                        
                if vid in session_state and session_state[vid].get("exited") and cy > line_y:
                    seq[vid] += 1
                    writer.write(
                        make_event(
                            store_id=store_id,
                            camera_id=camera_id,
                            visitor_id=vid,
                            event_type="REENTRY",
                            timestamp=ts,
                            zone_id="ENTRY_EXIT",
                            is_staff=is_staff,
                            confidence=det_conf,
                            metadata={**meta_base, "session_seq": seq[vid]},
                        )
                    )
                    session_state[vid]["exited"] = False
                    session_state[vid]["active"] = True

            # 2. Zone Transitions (ZONE_ENTER, ZONE_EXIT, ZONE_DWELL)
            prev_z = active_zones[vid]
            if z != prev_z:
                # If they were in a zone, emit ZONE_EXIT
                if prev_z is not None:
                    seq[vid] += 1
                    writer.write(
                        make_event(
                            store_id=store_id,
                            camera_id=camera_id,
                            visitor_id=vid,
                            event_type="ZONE_EXIT",
                            timestamp=ts,
                            zone_id=prev_z,
                            is_staff=is_staff,
                            confidence=det_conf,
                            metadata={**meta_base, "session_seq": seq[vid], "sku_zone": prev_z},
                        )
                    )
                    
                    # If they exit the billing zone, emit queue abandon candidate
                    if prev_z == "BILLING" and in_queue[vid]:
                        in_queue[vid] = False
                        seq[vid] += 1
                        writer.write(
                            make_event(
                                store_id=store_id,
                                camera_id=camera_id,
                                visitor_id=vid,
                                event_type="BILLING_QUEUE_ABANDON",
                                timestamp=ts,
                                zone_id="BILLING",
                                is_staff=is_staff,
                                confidence=det_conf,
                                metadata={**meta_base, "session_seq": seq[vid]},
                            )
                        )
                        
                active_zones[vid] = z
                
                # Emit ZONE_ENTER for new zone
                if z is not None:
                    key = (vid, z)
                    zone_entered[key] = True
                    seq[vid] += 1
                    writer.write(
                        make_event(
                            store_id=store_id,
                            camera_id=camera_id,
                            visitor_id=vid,
                            event_type="ZONE_ENTER",
                            timestamp=ts,
                            zone_id=z,
                            is_staff=is_staff,
                            confidence=det_conf,
                            metadata={**meta_base, "session_seq": seq[vid], "sku_zone": z},
                        )
                    )
            
            # 3. Zone Dwell Tracking
            if z:
                key = (vid, z)
                dwell_accum[key] += int(1000 * frame_stride / fps)
                if dwell_accum[key] >= 30000:
                    seq[vid] += 1
                    writer.write(
                        make_event(
                            store_id=store_id,
                            camera_id=camera_id,
                            visitor_id=vid,
                            event_type="ZONE_DWELL",
                            timestamp=ts,
                            zone_id=z,
                            dwell_ms=dwell_accum[key],
                            is_staff=is_staff,
                            confidence=det_conf,
                            metadata={**meta_base, "session_seq": seq[vid], "sku_zone": z},
                        )
                    )
                    dwell_accum[key] = 0

            # 4. Queue Ingress / Egress Logic
            if role == "billing" and z == "BILLING":
                if queue_depth > 0 and not in_queue[vid] and vid not in queued_visitors:
                    queued_visitors.add(vid)
                    in_queue[vid] = True
                    seq[vid] += 1
                    writer.write(
                        make_event(
                            store_id=store_id,
                            camera_id=camera_id,
                            visitor_id=vid,
                            event_type="BILLING_QUEUE_JOIN",
                            timestamp=ts,
                            zone_id="BILLING",
                            is_staff=is_staff,
                            confidence=det_conf,
                            metadata={
                                **meta_base,
                                "session_seq": seq[vid],
                                "queue_depth": queue_depth,
                            },
                        )
                    )
                if cy > 0.5:
                    queue_depth = min(8, queue_depth + 1)
                else:
                    queue_depth = max(0, queue_depth - 1)

        frame_idx += 1
        
    # Flush remaining active zones at the end of the clip
    for vid, az in list(active_zones.items()):
        if az is not None:
            ts_end = ts_for_frame(base, frame_idx - 1, fps)
            seq[vid] += 1
            writer.write(
                make_event(
                    store_id=store_id,
                    camera_id=camera_id,
                    visitor_id=vid,
                    event_type="ZONE_EXIT",
                    timestamp=ts_end,
                    zone_id=az,
                    is_staff=False,
                    confidence=0.8,
                    metadata={"session_seq": seq[vid], "sku_zone": az},
                )
            )
            if az == "BILLING" and in_queue[vid]:
                in_queue[vid] = False
                seq[vid] += 1
                writer.write(
                    make_event(
                        store_id=store_id,
                        camera_id=camera_id,
                        visitor_id=vid,
                        event_type="BILLING_QUEUE_ABANDON",
                        timestamp=ts_end,
                        zone_id="BILLING",
                        is_staff=False,
                        confidence=0.8,
                        metadata={"session_seq": seq[vid]},
                    )
                )
            active_zones[vid] = None
            
    cap.release()


def main() -> None:
    args = parse_args()
    store_id = args.store_id
    profile = load_camera_profile(store_id)
    layout = load_store_layout(store_id)
    
    from ultralytics import YOLO

    model = YOLO("yolov8n.pt")
    
    out_file = args.output
    if not out_file:
        out_dir = ROOT / "data" / "events" / store_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = str(out_dir / "output.jsonl")
        
    writer = EventWriter(Path(out_file))
    reid = ReIDBank()
    for cam in profile["cameras"]:
        print(f"Processing {cam['source_file']} as {cam['camera_id']} ({cam['role']})")
        process_clip(
            model,
            cam,
            store_id,
            layout,
            writer,
            reid,
            args.frame_stride,
            args.max_frames,
            args.conf,
        )
    writer.close()
    print(f"Events written to {out_file}")
    
    # Write a copy to global events/output.jsonl if it is ST1008 for backwards compatibility
    if store_id == "ST1008":
        global_out = ROOT / "data" / "events" / "output.jsonl"
        global_out.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy(out_file, global_out)
        except Exception:
            # Fallback if shutil is not imported
            import shutil
            shutil.copy(out_file, global_out)


if __name__ == "__main__":
    main()
