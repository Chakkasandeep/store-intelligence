from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.anomalies import detect_anomalies
from backend.bootstrap import bootstrap_data
from backend.config import get_settings
from backend.config import store_id as default_store_id
from backend.db import get_db, init_db
from backend.funnel import compute_funnel
from backend.health import compute_health
from backend.heatmap import compute_heatmap
from backend.ingestion import ingest_events
from backend.logging_setup import configure_logging, new_trace_id
from backend.metrics import compute_metrics, sync_pos_conversions
from backend.schemas import (
    AnomaliesResponse,
    FunnelResponse,
    HealthResponse,
    HeatmapResponse,
    IngestRequest,
    IngestResponse,
    MetricsResponse,
)
from backend.static_ui import register_dashboard_ui

configure_logging(get_settings().log_level)
logger = structlog.get_logger()

_connections: set[WebSocket] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bootstrap_data()
    yield


app = FastAPI(title="Store Intelligence API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    trace_id = new_trace_id()
    structlog.contextvars.bind_contextvars(trace_id=trace_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", endpoint=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "trace_id": trace_id},
        )
    latency_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request",
        trace_id=trace_id,
        store_id=request.path_params.get("id"),
        endpoint=request.url.path,
        latency_ms=round(latency_ms, 2),
        status_code=response.status_code,
    )
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.post("/events/ingest", response_model=IngestResponse)
async def post_ingest(body: IngestRequest, db: AsyncSession = Depends(get_db)) -> IngestResponse:
    try:
        result = await ingest_events(db, body.events)
        first = body.events[0] if body.events else {}
        sid = first.get("store_id") if isinstance(first, dict) else default_store_id()
        await sync_pos_conversions(db, sid)
        await _broadcast_metrics(sid)
        return result
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"error": "database_unavailable", "message": str(exc)}) from exc


@app.get("/stores/{store_id}/metrics", response_model=MetricsResponse)
async def get_metrics(store_id: str, db: AsyncSession = Depends(get_db)) -> MetricsResponse:
    return await compute_metrics(db, store_id)


@app.get("/stores/{store_id}/funnel", response_model=FunnelResponse)
async def get_funnel(store_id: str, db: AsyncSession = Depends(get_db)) -> FunnelResponse:
    return await compute_funnel(db, store_id)


@app.get("/stores/{store_id}/heatmap", response_model=HeatmapResponse)
async def get_heatmap(store_id: str, db: AsyncSession = Depends(get_db)) -> HeatmapResponse:
    return await compute_heatmap(db, store_id)


@app.get("/stores/{store_id}/anomalies", response_model=AnomaliesResponse)
async def get_anomalies(store_id: str, db: AsyncSession = Depends(get_db)) -> AnomaliesResponse:
    return await detect_anomalies(db, store_id)


@app.get("/health", response_model=HealthResponse)
async def get_health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    return await compute_health(db)


@app.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket):
    await websocket.accept()
    _connections.add(websocket)
    sid = websocket.query_params.get("store_id") or default_store_id()
    try:
        import asyncio

        while True:
            from backend.db import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                payload = (await compute_metrics(db, sid)).model_dump(mode="json")
            await websocket.send_json(payload)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    finally:
        _connections.discard(websocket)


from backend.db import AsyncSessionLocal  # noqa: E402

register_dashboard_ui(app)


async def _broadcast_metrics(sid: str) -> None:
    import asyncio

    if not _connections:
        return
    async with AsyncSessionLocal() as db:
        payload = (await compute_metrics(db, sid)).model_dump(mode="json")
    dead = []
    for ws in _connections:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections.discard(ws)
