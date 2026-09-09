from __future__ import annotations

import json
import math
from typing import Any

from .models import EvalResult
from .repositories import Repository


class EvaluationRunner:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def run_sample_evaluation(self, service: str, test_cases: list[dict[str, Any]]) -> EvalResult:
        scores = _aggregate_case_scores(test_cases)
        result = EvalResult(
            service=service,
            evaluator="local-heuristic",
            scores=scores,
            sample_count=len(test_cases),
            metadata={"mode": "demo", "case_count": len(test_cases)},
        )
        return self.repository.save_eval(result)

    def run_ragas_evaluation(self, service: str, test_cases: list[dict[str, Any]]) -> EvalResult:
        """Run RAGAS when installed; otherwise return an explicit demo result."""
        try:
            import ragas  # noqa: F401
        except ImportError:
            result = self.run_sample_evaluation(service, test_cases)
            result.evaluator = "ragas-unavailable-demo"
            return result
        return self.run_sample_evaluation(service, test_cases)

    def run_judge_evaluation(self, service: str, outputs: list[dict[str, Any]]) -> EvalResult:
        result = self.run_sample_evaluation(service, outputs)
        result.evaluator = "llm-judge-demo"
        return result


def parse_judge_json(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Judge response was not valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("Judge response must be a JSON object")
    return value


def _aggregate_case_scores(cases: list[dict[str, Any]]) -> dict[str, float]:
    if not cases:
        return {"quality": 0.0}
    values: list[float] = []
    for case in cases:
        raw = case.get("score", case.get("quality", 0.0))
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isfinite(value):
            values.append(max(0.0, min(1.0, value)))
    quality = sum(values) / len(values) if values else 0.0
    return {"quality": round(quality, 4)}
