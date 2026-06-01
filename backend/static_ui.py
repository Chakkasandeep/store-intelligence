"""Serve built React dashboard from dashboard/dist when present (Docker / HF Space)."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

DIST_DIR = Path(__file__).resolve().parents[1] / "dashboard" / "dist"
_API_PREFIXES = ("stores", "events", "health", "ws", "docs", "openapi.json", "redoc")


def register_dashboard_ui(app: FastAPI) -> None:
    if not (DIST_DIR / "index.html").is_file():
        return

    assets_dir = DIST_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="dashboard-assets")

    @app.get("/", include_in_schema=False)
    async def dashboard_root() -> FileResponse:
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/{page_path:path}", include_in_schema=False)
    async def dashboard_spa(page_path: str) -> FileResponse:
        first = page_path.split("/", 1)[0]
        if first in _API_PREFIXES:
            raise HTTPException(status_code=404, detail="Not found")
        candidate = DIST_DIR / page_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")
