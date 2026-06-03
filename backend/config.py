from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]  # store-intelligence/
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # Apex Retail/
GENERATED = ROOT / "configs" / "generated"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = f"sqlite+aiosqlite:///{(ROOT / 'data' / 'store_intel.db').as_posix()}"
    log_level: str = "INFO"
    conversion_window_minutes: int = 5
    stale_feed_minutes: int = 10
    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def load_json_config(name: str, store_id: str = "ST1008") -> dict:
    path = GENERATED / store_id / name
    if not path.exists():
        path = GENERATED / name  # fallback
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run: python scripts/discover_all.py")
    return json.loads(path.read_text(encoding="utf-8"))


def store_id() -> str:
    # Deprecated single store getter - falls back to first discovered store
    stores = active_stores()
    return stores[0] if stores else "ST1008"


def active_stores() -> list[str]:
    """Dynamically scan generated config registry for active store IDs."""
    if not GENERATED.exists():
        return ["ST1008"]
    stores = []
    for p in GENERATED.iterdir():
        if p.is_dir() and (p / "pos_mapping.json").exists():
            stores.append(p.name)
    return sorted(stores) if stores else ["ST1008"]
