from __future__ import annotations

import os
from pathlib import Path

import structlog
from sqlalchemy import func, select

from backend.config import ROOT, active_stores
from backend.db import AsyncSessionLocal, init_db
from backend.ingestion import load_jsonl
from backend.metrics import load_pos_transactions, sync_pos_conversions

logger = structlog.get_logger()


async def event_count() -> int:
    from backend.models import EventRow

    async with AsyncSessionLocal() as db:
        return int((await db.execute(select(func.count()).select_from(EventRow))).scalar() or 0)


async def bootstrap_data() -> None:
    await init_db()
    
    stores = active_stores()
    logger.info("bootstrap_started", active_stores=stores)
    
    for sid in stores:
        async with AsyncSessionLocal() as db:
            logger.info("bootstrap_pos", store_id=sid)
            await load_pos_transactions(db, sid)
            
        # Determine store specific event paths
        events_path = ROOT / "data" / "events" / sid / "output.jsonl"
        if not events_path.exists() and sid == "ST1008":
            events_path = ROOT / "data" / "events" / "output.jsonl"
            
        if events_path.exists():
            logger.info("bootstrap_ingest", store_id=sid, path=str(events_path))
            async with AsyncSessionLocal() as db:
                n = await load_jsonl(str(events_path), db)
            logger.info("bootstrap_ingest_done", store_id=sid, accepted=n)
        else:
            logger.info("bootstrap_skip_events_missing", store_id=sid, path=str(events_path))
            
        async with AsyncSessionLocal() as db:
            await sync_pos_conversions(db, sid)
            
    # Optionally load sample events from root workspace parent folder for demo/testing purposes
    sample_path = ROOT.parent / "sample_eventsbe42122.jsonl"
    if not sample_path.exists():
         sample_path = ROOT / "sample_eventsbe42122.jsonl"
    if sample_path.exists():
         logger.info("bootstrap_sample_events", path=str(sample_path))
         async with AsyncSessionLocal() as db:
             n = await load_jsonl(str(sample_path), db)
         logger.info("bootstrap_sample_events_done", accepted=n)
