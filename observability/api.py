from __future__ import annotations

from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import get_settings
from .cost import estimate_cost
from .alerts import send_regression_alerts
from .demo import seed_demo_data
from .evaluation import EvaluationRunner
from .models import EvalResult, TraceContext, TraceEvent
from .regression import BaselineManager
from .repositories import RepositoryError, build_repository
from .sdk import trace_llm

settings = get_settings()
repository = build_repository(settings)
if settings.demo_mode:
    seed_demo_data(repository)
runner = EvaluationRunner(repository)
baselines = BaselineManager(repository, settings.regression_tolerance)

app = FastAPI(title="SKXYWTF Observability API", version="1.0.0")


@app.exception_handler(RepositoryError)
def repository_error_handler(request: object, exc: RepositoryError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if settings.demo_mode and not settings.api_key:
        return
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Valid X-API-Key header required")


class TraceRequest(BaseModel):
    trace_id: str | None = None
    service: str
    task: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    success: bool = True
    context: dict = Field(default_factory=dict)


class EvaluationRequest(BaseModel):
    service: str
    cases: list[dict] = Field(default_factory=list)
    evaluator: str = "sample"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "demo_mode": settings.demo_mode, "supabase_enabled": settings.supabase_enabled}


@app.get("/api/traces", dependencies=[Depends(require_api_key)])
def get_traces(
    service: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[dict]:
    return [trace.model_dump(mode="json") for trace in repository.list_traces(limit, offset, service)]


@app.post("/api/traces", dependencies=[Depends(require_api_key)], responses={500: {"description": "Trace was not persisted"}})
def create_trace(request: TraceRequest) -> TraceEvent:
    event = TraceEvent(
        trace_id=request.trace_id or TraceEvent.model_fields["trace_id"].default_factory(),
        service=request.service,
        task=request.task,
        model=request.model,
        input_tokens=request.input_tokens,
        output_tokens=request.output_tokens,
        estimated_cost_usd=estimate_cost(request.model, request.input_tokens or 0, request.output_tokens or 0),
        latency_ms=request.latency_ms,
        success=request.success,
        context=request.context,
    )
    return repository.save_trace(event)


@app.get("/api/evaluations", dependencies=[Depends(require_api_key)])
def get_evaluations(service: str | None = None) -> list[dict]:
    return [result.model_dump(mode="json") for result in repository.list_evals(service)]


@app.post("/api/evaluations/run", dependencies=[Depends(require_api_key)])
def run_evaluation(request: EvaluationRequest) -> EvalResult:
    if request.evaluator == "ragas":
        result = runner.run_ragas_evaluation(request.service, request.cases)
    else:
        result = runner.run_sample_evaluation(request.service, request.cases)
    baseline = repository.get_baseline(request.service)
    if baseline is None:
        baselines.set_baseline(request.service, result)
    else:
        alerts = baselines.detect_and_store(request.service, result)
        send_regression_alerts(alerts, settings.resend_api_key, settings.founder_email)
    return result


@app.post("/api/baselines/{service}", dependencies=[Depends(require_api_key)])
def set_baseline(service: str, result: EvalResult) -> dict:
    baselines.set_baseline(service, result)
    return {"service": service, "scores": result.scores}


@app.get("/api/alerts", dependencies=[Depends(require_api_key)])
def get_alerts(status: str | None = None) -> list[dict]:
    return [alert.model_dump(mode="json") for alert in repository.list_alerts(status)]


@app.post("/api/alerts/{alert_id}/resolve", dependencies=[Depends(require_api_key)])
def resolve_alert(alert_id: str, status: Literal["resolved", "open"] = "resolved") -> dict:
    alert = repository.update_alert_status(alert_id, status)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert.model_dump(mode="json")
