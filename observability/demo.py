from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

from .models import EvalResult, TraceEvent
from .repositories import Repository


SERVICES = [
    "ai-router",
    "skore-pipeline",
    "advisor-brief-agent",
    "research-intelligence",
    "in-house-intelligence",
    "finbert-sentiment",
    "llm-security-proxy",
    "onboarding-hints",
]


def seed_demo_data(repository: Repository) -> None:
    if repository.list_traces(limit=1):
        return
    random.seed(42)
    now = datetime.now(timezone.utc)
    for index in range(80):
        service = SERVICES[index % len(SERVICES)]
        success = index % 13 != 0
        repository.save_trace(TraceEvent(
            service=service,
            task="demo_completion",
            model=["claude-sonnet-4-6", "gemini-2.0-flash", "llama3.2:8b"][index % 3],
            input_tokens=250 + index * 3,
            output_tokens=80 + index,
            estimated_cost_usd=round((250 + index * 3) * 0.003 / 1000, 6),
            latency_ms=180 + (index * 37) % 900,
            ttfb_ms=70 + (index * 11) % 250,
            success=success,
            error_type="ProviderTimeout" if not success else None,
            error_message="Demo provider timeout" if not success else None,
            context={"demo": True},
            created_at=now - timedelta(hours=index % 24),
        ))
        score = 0.72 + ((index % 7) / 100)
        result = EvalResult(service=service, evaluator="demo", scores={"quality": score}, sample_count=10)
        repository.save_eval(result)
        if not repository.get_baseline(service):
            repository.set_baseline(service, {"quality": 0.80})
