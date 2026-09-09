from __future__ import annotations

import time
from contextlib import AbstractContextManager
from typing import Any

from .cost import estimate_cost
from .models import TraceContext, TraceEvent
from .repositories import Repository


class TraceHandle(AbstractContextManager["TraceHandle"]):
    def __init__(
        self,
        repository: Repository,
        service: str,
        task: str,
        model: str,
        context: TraceContext | dict[str, Any] | None = None,
    ) -> None:
        self.repository = repository
        self.service = service
        self.task = task
        self.model = model
        self.context = context.model_dump() if isinstance(context, TraceContext) else (context or {})
        self.started = time.perf_counter()
        self.first_token_at: float | None = None
        self.input_tokens: int | None = None
        self.output_tokens: int | None = None
        self.output: Any = None
        self.error: BaseException | None = None
        self.event: TraceEvent | None = None

    def mark_first_token(self) -> None:
        self.first_token_at = time.perf_counter()

    def set_output(self, output: Any, input_tokens: int | None = None, output_tokens: int | None = None) -> None:
        self.output = output
        self.input_tokens = input_tokens if input_tokens is not None else _read_tokens(output, "input_tokens")
        self.output_tokens = output_tokens if output_tokens is not None else _read_tokens(output, "output_tokens")

    def __enter__(self) -> "TraceHandle":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any) -> bool:
        self.error = exc
        elapsed_ms = int((time.perf_counter() - self.started) * 1000)
        ttfb_ms = int((self.first_token_at - self.started) * 1000) if self.first_token_at else None
        event = TraceEvent(
            service=self.service,
            task=self.task,
            model=self.model,
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            estimated_cost_usd=estimate_cost(self.model, self.input_tokens or 0, self.output_tokens or 0),
            latency_ms=elapsed_ms,
            ttfb_ms=ttfb_ms,
            success=exc is None,
            error_type=type(exc).__name__ if exc else None,
            error_message=str(exc)[:500] if exc else None,
            context=self.context,
        )
        self.event = self.repository.save_trace(event)
        return False


def trace_llm(
    repository: Repository,
    service: str,
    task: str,
    model: str,
    context: TraceContext | dict[str, Any] | None = None,
) -> TraceHandle:
    return TraceHandle(repository, service, task, model, context)


def _read_tokens(value: Any, key: str) -> int | None:
    if isinstance(value, dict):
        raw = value.get(key)
        return int(raw) if raw is not None else None
    usage = getattr(value, "usage", None)
    raw = getattr(usage, key, None) if usage else None
    return int(raw) if raw is not None else None
