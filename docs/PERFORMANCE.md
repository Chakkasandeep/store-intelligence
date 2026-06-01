# Performance — Intel i5 Profile

## Targets

- Pipeline: process 5× ~140s clips in &lt; 30 min (interactive) with stride 8 + max 600 frames
- API: &lt; 100 ms for `/metrics` on 10k events (SQLite)
- Dashboard: 5 s WebSocket push / 10 s poll fallback

## Optimizations

| Layer | Technique |
|-------|-----------|
| CV | YOLOv8n, frame stride, optional max_frames |
| Tracking | Built-in ByteTrack (no separate GPU ReID model) |
| Re-ID | 16×16 HSV histogram (CPU) |
| API | Indexed columns: store_id, timestamp, visitor_id |
| Docker | Limited frames in entrypoint for acceptance |

## Measurements (expected)

| Step | Approx. time (i5-8GB) |
|------|------------------------|
| Discovery | 30–60 s |
| Pipeline (600 f × 5 cams) | 15–25 min |
| Ingest 5k events | &lt; 2 s |
| pytest | &lt; 1 s |

Run `python pipeline/run_pipeline.py --frame-stride 8 --max-frames 300` for demos.
