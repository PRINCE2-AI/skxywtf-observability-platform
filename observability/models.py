from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class TraceContext(BaseModel):
    model_config = ConfigDict(extra="allow")


class TraceEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    trace_id: UUID = Field(default_factory=uuid4)
    service: str
    task: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float = 0.0
    latency_ms: int | None = None
    ttfb_ms: int | None = None
    success: bool = True
    error_type: str | None = None
    error_message: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    input_preview: str | None = None
    output_preview: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvalResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    service: str
    evaluator: str
    scores: dict[str, float]
    sample_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
    run_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RegressionAlert(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    service: str
    metric: str
    baseline: float
    current: float
    drop_pct: float
    status: str = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceSummary(BaseModel):
    service: str
    calls: int
    errors: int
    error_rate: float
    spend_usd: float
    avg_latency_ms: float
    health: str
