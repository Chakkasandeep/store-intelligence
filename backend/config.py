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


def load_json_config(name: str) -> dict:
    path = GENERATED / name
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run: python scripts/discover_all.py")
    return json.loads(path.read_text(encoding="utf-8"))


def store_id() -> str:
    return load_json_config("pos_mapping.json").get("store_id", "ST1008")
