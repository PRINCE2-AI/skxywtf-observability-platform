from __future__ import annotations

from collections import defaultdict
from typing import Any, Protocol

from .models import EvalResult, RegressionAlert, TraceEvent


class Repository(Protocol):
    def save_trace(self, trace: TraceEvent) -> TraceEvent: ...
    def list_traces(self, limit: int = 200, service: str | None = None) -> list[TraceEvent]: ...
    def save_eval(self, result: EvalResult) -> EvalResult: ...
    def list_evals(self, service: str | None = None) -> list[EvalResult]: ...
    def set_baseline(self, service: str, scores: dict[str, float]) -> None: ...
    def get_baseline(self, service: str) -> dict[str, float] | None: ...
    def save_alert(self, alert: RegressionAlert) -> RegressionAlert: ...
    def list_alerts(self, status: str | None = None) -> list[RegressionAlert]: ...


class InMemoryRepository:
    def __init__(self) -> None:
        self.traces: list[TraceEvent] = []
        self.evals: list[EvalResult] = []
        self.baselines: dict[str, dict[str, float]] = {}
        self.alerts: list[RegressionAlert] = []

    def save_trace(self, trace: TraceEvent) -> TraceEvent:
        self.traces.append(trace)
        return trace

    def list_traces(self, limit: int = 200, service: str | None = None) -> list[TraceEvent]:
        values = [t for t in self.traces if not service or t.service == service]
        return list(reversed(values[-limit:]))

    def save_eval(self, result: EvalResult) -> EvalResult:
        self.evals.append(result)
        return result

    def list_evals(self, service: str | None = None) -> list[EvalResult]:
        return [e for e in self.evals if not service or e.service == service]

    def set_baseline(self, service: str, scores: dict[str, float]) -> None:
        self.baselines[service] = dict(scores)

    def get_baseline(self, service: str) -> dict[str, float] | None:
        return self.baselines.get(service)

    def save_alert(self, alert: RegressionAlert) -> RegressionAlert:
        self.alerts.append(alert)
        return alert

    def list_alerts(self, status: str | None = None) -> list[RegressionAlert]:
        return [a for a in self.alerts if not status or a.status == status]


class SupabaseRepository(InMemoryRepository):
    """Supabase-backed repository with an in-memory fallback for local/demo mode."""

    def __init__(self, url: str, service_role_key: str) -> None:
        super().__init__()
        from supabase import create_client
        self.client = create_client(url, service_role_key)

    def save_trace(self, trace: TraceEvent) -> TraceEvent:
        payload = trace.model_dump(mode="json")
        self.client.table("llm_traces").insert(payload).execute()
        return trace

    def list_traces(self, limit: int = 200, service: str | None = None) -> list[TraceEvent]:
        query = self.client.table("llm_traces").select("*").order("created_at", desc=True).limit(limit)
        if service:
            query = query.eq("service", service)
        data = query.execute().data or []
        return [TraceEvent.model_validate(item) for item in data]

    def save_eval(self, result: EvalResult) -> EvalResult:
        self.client.table("eval_results").insert(result.model_dump(mode="json")).execute()
        return result

    def list_evals(self, service: str | None = None) -> list[EvalResult]:
        query = self.client.table("eval_results").select("*").order("run_at", desc=True)
        if service:
            query = query.eq("service", service)
        data = query.execute().data or []
        return [EvalResult.model_validate(item) for item in data]

    def set_baseline(self, service: str, scores: dict[str, float]) -> None:
        self.client.table("eval_baselines").upsert({"service": service, "scores": scores}).execute()

    def get_baseline(self, service: str) -> dict[str, float] | None:
        data = self.client.table("eval_baselines").select("scores").eq("service", service).limit(1).execute().data or []
        return data[0]["scores"] if data else None

    def save_alert(self, alert: RegressionAlert) -> RegressionAlert:
        self.client.table("regression_alerts").insert(alert.model_dump(mode="json")).execute()
        return alert

    def list_alerts(self, status: str | None = None) -> list[RegressionAlert]:
        query = self.client.table("regression_alerts").select("*").order("created_at", desc=True)
        if status:
            query = query.eq("status", status)
        data = query.execute().data or []
        return [RegressionAlert.model_validate(item) for item in data]


def build_repository(settings: Any) -> Repository:
    if settings.supabase_enabled:
        try:
            return SupabaseRepository(settings.supabase_url, settings.supabase_service_role_key)
        except ImportError:
            pass
    return InMemoryRepository()
