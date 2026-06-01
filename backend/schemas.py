from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class EventMetadata(BaseModel):
    queue_depth: int | None = None
    sku_zone: str | None = None
    session_seq: int | None = None
    track_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class StoreEvent(BaseModel):
    event_id: str
    store_id: str
    camera_id: str
    visitor_id: str
    event_type: str
    timestamp: datetime
    zone_id: str | None = None
    dwell_ms: int = 0
    is_staff: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: EventMetadata | dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_ts(cls, v: Any) -> datetime:
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))


class IngestRequest(BaseModel):
    events: list[dict[str, Any]] = Field(max_length=500)


class IngestResponse(BaseModel):
    accepted: int
    duplicates: int
    rejected: int
    errors: list[dict[str, Any]] = Field(default_factory=list)


class MetricsResponse(BaseModel):
    store_id: str
    unique_visitors: int
    current_visitors: int
    conversion_rate: float
    avg_dwell_time_ms: float
    queue_depth: int
    abandonment_rate: float
    billing_visits: int
    zone_visits: dict[str, int]
    as_of: datetime


class FunnelStage(BaseModel):
    stage: str
    visitors: int
    drop_off_pct: float
    conversion_pct: float


class FunnelResponse(BaseModel):
    store_id: str
    stages: list[FunnelStage]
    as_of: datetime


class HeatmapZone(BaseModel):
    zone_id: str
    visit_frequency: float
    avg_dwell_ms: float


class HeatmapResponse(BaseModel):
    store_id: str
    zones: list[HeatmapZone]
    data_confidence: Literal["HIGH", "LOW"]
    as_of: datetime


class AnomalyItem(BaseModel):
    anomaly_id: str
    type: str
    severity: Literal["INFO", "WARN", "CRITICAL"]
    detected_at: datetime
    root_cause: str
    suggested_action: str


class AnomaliesResponse(BaseModel):
    store_id: str
    anomalies: list[AnomalyItem]


class HealthStoreStatus(BaseModel):
    store_id: str
    last_event_at: datetime | None
    stale: bool


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "unavailable"]
    stores: list[HealthStoreStatus]
    warnings: list[str] = Field(default_factory=list)
