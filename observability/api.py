from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .config import get_settings
from .demo import seed_demo_data
from .evaluation import EvaluationRunner
from .models import EvalResult, TraceContext, TraceEvent
from .regression import BaselineManager
from .repositories import build_repository
from .sdk import trace_llm

settings = get_settings()
repository = build_repository(settings)
if settings.demo_mode:
    seed_demo_data(repository)
runner = EvaluationRunner(repository)
baselines = BaselineManager(repository, settings.regression_tolerance)

app = FastAPI(title="SKXYWTF Observability API", version="1.0.0")


class TraceRequest(BaseModel):
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


@app.get("/api/traces")
def get_traces(service: str | None = None, limit: Annotated[int, Query(ge=1, le=1000)] = 200) -> list[dict]:
    return [trace.model_dump(mode="json") for trace in repository.list_traces(limit, service)]


@app.post("/api/traces", responses={500: {"description": "Trace was not persisted"}})
def create_trace(request: TraceRequest) -> TraceEvent:
    with trace_llm(repository, request.service, request.task, request.model, TraceContext(**request.context)) as tracer:
        tracer.set_output({"input_tokens": request.input_tokens, "output_tokens": request.output_tokens})
    if tracer.event is None:
        raise HTTPException(status_code=500, detail="Trace was not persisted")
    event = tracer.event
    event.latency_ms = request.latency_ms if request.latency_ms is not None else event.latency_ms
    event.success = request.success
    event.context = request.context
    return event


@app.get("/api/evaluations")
def get_evaluations(service: str | None = None) -> list[dict]:
    return [result.model_dump(mode="json") for result in repository.list_evals(service)]


@app.post("/api/evaluations/run")
def run_evaluation(request: EvaluationRequest) -> EvalResult:
    if request.evaluator == "ragas":
        result = runner.run_ragas_evaluation(request.service, request.cases)
    else:
        result = runner.run_sample_evaluation(request.service, request.cases)
    baseline = repository.get_baseline(request.service)
    if baseline is None:
        baselines.set_baseline(request.service, result)
    else:
        baselines.detect_and_store(request.service, result)
    return result


@app.post("/api/baselines/{service}")
def set_baseline(service: str, result: EvalResult) -> dict:
    baselines.set_baseline(service, result)
    return {"service": service, "scores": result.scores}


@app.get("/api/alerts")
def get_alerts(status: str | None = None) -> list[dict]:
    return [alert.model_dump(mode="json") for alert in repository.list_alerts(status)]
