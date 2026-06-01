from __future__ import annotations

import os
from pathlib import Path

import structlog
from sqlalchemy import func, select

from backend.config import ROOT, store_id
from backend.db import AsyncSessionLocal, init_db
from backend.ingestion import load_jsonl
from backend.metrics import load_pos_transactions, sync_pos_conversions

logger = structlog.get_logger()

EVENTS_PATH = Path(os.getenv("EVENTS_JSONL", ROOT / "data" / "events" / "output.jsonl"))


async def event_count() -> int:
    from backend.models import EventRow

    async with AsyncSessionLocal() as db:
        return int((await db.execute(select(func.count()).select_from(EventRow))).scalar() or 0)


async def bootstrap_data() -> None:
    await init_db()
    sid = store_id()
    async with AsyncSessionLocal() as db:
        await load_pos_transactions(db, sid)
    if EVENTS_PATH.exists() and await event_count() == 0:
        logger.info("bootstrap_ingest", path=str(EVENTS_PATH))
        async with AsyncSessionLocal() as db:
            n = await load_jsonl(str(EVENTS_PATH), db)
        logger.info("bootstrap_ingest_done", accepted=n)
    else:
        logger.info("bootstrap_skip_events", exists=EVENTS_PATH.exists(), count=await event_count())
    async with AsyncSessionLocal() as db:
        await sync_pos_conversions(db, sid)
