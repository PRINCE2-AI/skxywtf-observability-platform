from __future__ import annotations

COST_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5": {"input": 0.00025, "output": 0.00125},
    "gemini-2.0-flash": {"input": 0.000075, "output": 0.0003},
    "llama3.2:8b": {"input": 0.0, "output": 0.0},
    "mistral:7b": {"input": 0.0, "output": 0.0},
}


def estimate_cost(model: str, input_tokens: int = 0, output_tokens: int = 0) -> float:
    rates = COST_PER_1K_TOKENS.get(model, {"input": 0.003, "output": 0.015})
    return round((input_tokens * rates["input"] + output_tokens * rates["output"]) / 1000, 8)
