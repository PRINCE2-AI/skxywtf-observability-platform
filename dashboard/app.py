from __future__ import annotations

import os

import pandas as pd
import streamlit as st
import httpx

SERVICES = [
    "ai-router", "skore-pipeline", "advisor-brief-agent", "research-intelligence",
    "in-house-intelligence", "finbert-sentiment", "llm-security-proxy", "onboarding-hints",
]
API_URL = os.getenv("OBSERVABILITY_API_URL", "http://127.0.0.1:8095").rstrip("/")
API_KEY = os.getenv("OBSERVABILITY_API_KEY", "")

st.set_page_config(page_title="SKXYWTF Observability", page_icon="O", layout="wide")

OVERVIEW = "Overview"
TRACE_EXPLORER = "Trace Explorer"
EVALUATION_SCORES = "Evaluation Scores"
COST_BUDGET = "Cost & Budget"
SECURITY_EVENTS = "Security Events"

st.title("SKXYWTF Observability")
st.caption("AI reliability, evaluation, cost, and security control center")

def api_get(path: str, params: dict | None = None) -> list[dict]:
    response = httpx.get(f"{API_URL}{path}", params=params, headers={"X-API-Key": API_KEY}, timeout=10)
    response.raise_for_status()
    return response.json()


try:
    traces = api_get("/api/traces", {"limit": 1000})
    evals = api_get("/api/evaluations")
    alerts = api_get("/api/alerts")
except httpx.HTTPError as exc:
    st.error(f"Observability API unavailable: {exc}")
    st.stop()
page = st.sidebar.radio("View", [OVERVIEW, TRACE_EXPLORER, EVALUATION_SCORES, COST_BUDGET, SECURITY_EVENTS])


def trace_frame() -> pd.DataFrame:
    rows = traces
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["service", "model", "estimated_cost_usd", "latency_ms", "success"])


def _service_status(rate: float) -> str:
    if rate > 0.10:
        return "RED"
    if rate > 0.03:
        return "AMBER"
    return "GREEN"


def _health_summary(frame: pd.DataFrame) -> list[dict[str, object]]:
    summary = []
    observed = set(frame["service"].dropna().tolist()) if not frame.empty else set()
    for service in sorted(set(SERVICES) | observed):
        subset = frame[frame["service"] == service] if not frame.empty else frame
        calls = len(subset)
        service_errors = int((~subset["success"]).sum()) if calls else 0
        rate = service_errors / calls if calls else 0.0
        summary.append({"Service": service, "Calls": calls, "Error rate": f"{rate:.1%}", "Status": _service_status(rate)})
    return summary


def render_overview() -> None:
    frame = trace_frame()
    total_spend = float(frame["estimated_cost_usd"].sum()) if not frame.empty else 0.0
    errors = int((~frame["success"]).sum()) if not frame.empty else 0
    error_rate = errors / len(frame) if len(frame) else 0.0
    first, second, third, fourth = st.columns(4)
    first.metric("LLM spend", f"${total_spend:.4f}")
    second.metric("Traces", len(frame))
    third.metric("Error rate", f"{error_rate:.1%}")
    fourth.metric("Open alerts", len([a for a in alerts if a.get("status") == "open"]))
    st.subheader("Service health")
    st.dataframe(pd.DataFrame(_health_summary(frame)), use_container_width=True, hide_index=True)
    st.subheader("Spend by service")
    if not frame.empty:
        st.bar_chart(frame.groupby("service")["estimated_cost_usd"].sum())


def render_traces() -> None:
    frame = trace_frame()
    st.subheader("Trace Explorer")
    if frame.empty:
        st.info("No traces available.")
        return
    services = ["All"] + sorted(frame["service"].dropna().unique().tolist())
    selected = st.selectbox("Service", services)
    if selected != "All":
        frame = frame[frame["service"] == selected]
    columns = ["created_at", "service", "task", "model", "latency_ms", "input_tokens", "output_tokens", "estimated_cost_usd", "success"]
    st.dataframe(frame[columns], use_container_width=True, hide_index=True)
    st.write("Latency percentiles")
    st.json({"p50_ms": float(frame["latency_ms"].quantile(.50)), "p95_ms": float(frame["latency_ms"].quantile(.95)), "p99_ms": float(frame["latency_ms"].quantile(.99))})


def render_evaluations() -> None:
    st.subheader("Evaluation Scores")
    rows = []
    for result in evals:
        for metric, current in result["scores"].items():
            rows.append({"Service": result["service"], "Metric": metric, "Current": current, "Evaluator": result["evaluator"], "Samples": result["sample_count"]})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if alerts:
        st.subheader("Regression alerts")
        st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)


def render_cost() -> None:
    st.subheader("Cost & Budget")
    frame = trace_frame()
    if frame.empty:
        st.info("No cost data available.")
        return
    by_model = frame.groupby("model")["estimated_cost_usd"].sum().sort_values(ascending=False)
    by_service = frame.groupby("service")["estimated_cost_usd"].sum().sort_values(ascending=False)
    left, right = st.columns(2)
    frame["created_at"] = pd.to_datetime(frame["created_at"], utc=True, errors="coerce")
    days = max((frame["created_at"].max() - frame["created_at"].min()).total_seconds() / 86400, 1)
    daily_spend = float(frame["estimated_cost_usd"].sum()) / days
    left.metric("Projected monthly spend", f"${daily_spend * 30:.2f}")
    right.metric("Open-weight savings estimate", f"${float(frame[frame['model'].str.contains('llama|mistral', regex=True)]['estimated_cost_usd'].sum()):.4f}")
    st.bar_chart(by_model)
    st.dataframe(by_service.rename("Spend USD").to_frame(), use_container_width=True)


def render_security() -> None:
    st.subheader("Security Events")
    st.info("Security proxy audit events will appear here when the shared llm_audit_log table is connected.")
    st.metric("Observed security traces", len([t for t in traces if t.get("service") == "llm-security-proxy"]))
    st.dataframe(pd.DataFrame([{"Event": "Demo audit feed", "Status": "Waiting for proxy integration", "Action": "Configure shared Supabase table"}]), use_container_width=True, hide_index=True)


{OVERVIEW: render_overview, TRACE_EXPLORER: render_traces, EVALUATION_SCORES: render_evaluations, COST_BUDGET: render_cost, SECURITY_EVENTS: render_security}[page]()
