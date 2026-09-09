from __future__ import annotations

import math

from .models import EvalResult, RegressionAlert
from .repositories import Repository


class BaselineManager:
    def __init__(self, repository: Repository, tolerance: float = 0.10) -> None:
        self.repository = repository
        self.tolerance = max(0.0, min(1.0, tolerance))

    def set_baseline(self, service: str, result: EvalResult | dict[str, float]) -> None:
        scores = result.scores if isinstance(result, EvalResult) else result
        self.repository.set_baseline(service, scores)

    def detect_regression(self, service: str, current: EvalResult) -> list[RegressionAlert]:
        baseline = self.repository.get_baseline(service)
        if not baseline:
            return []
        alerts: list[RegressionAlert] = []
        for metric, current_score in current.scores.items():
            baseline_score = baseline.get(metric)
            if baseline_score is None or not _finite(current_score) or not _finite(baseline_score):
                continue
            if baseline_score <= 0:
                continue
            threshold = baseline_score * (1 - self.tolerance)
            if current_score < threshold:
                drop_pct = (baseline_score - current_score) / baseline_score
                alerts.append(RegressionAlert(
                    service=service,
                    metric=metric,
                    baseline=baseline_score,
                    current=current_score,
                    drop_pct=round(drop_pct, 4),
                ))
        return alerts

    def detect_and_store(self, service: str, current: EvalResult) -> list[RegressionAlert]:
        alerts = self.detect_regression(service, current)
        return [self.repository.save_alert(alert) for alert in alerts]


def _finite(value: float) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)
