from observability.cost import estimate_cost
from observability.evaluation import parse_judge_json
from observability.models import EvalResult
from observability.regression import BaselineManager
from observability.repositories import InMemoryRepository


def test_cost_estimation() -> None:
    assert estimate_cost("claude-sonnet-4-6", 1000, 500) == 0.0105


def test_trace_repository_and_regression() -> None:
    repository = InMemoryRepository()
    manager = BaselineManager(repository, tolerance=0.10)
    manager.set_baseline("advisor", {"quality": 0.90})
    alerts = manager.detect_and_store("advisor", EvalResult(service="advisor", evaluator="test", scores={"quality": 0.70}))
    assert len(alerts) == 1
    assert alerts[0].metric == "quality"


def test_zero_baseline_does_not_divide() -> None:
    repository = InMemoryRepository()
    manager = BaselineManager(repository)
    manager.set_baseline("svc", {"quality": 0.0})
    assert manager.detect_regression("svc", EvalResult(service="svc", evaluator="test", scores={"quality": 0.0})) == []


def test_invalid_judge_json_is_rejected() -> None:
    try:
        parse_judge_json("not-json")
    except ValueError as error:
        assert "valid JSON" in str(error)
    else:
        raise AssertionError("Expected invalid JSON to raise")
