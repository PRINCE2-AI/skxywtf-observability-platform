# SKXYWTF Observability Platform

A demo-ready AI observability and evaluation platform built around a Python tracing SDK, FastAPI, Supabase, evaluation workflows, regression detection, and Streamlit.

## What this demonstrates

- Structured LLM traces with token, cost, latency, and error metadata
- Evaluation results with baseline comparison and regression alerts
- FastAPI endpoints for traces, evaluations, baselines, and alerts
- Streamlit views for service health, traces, quality, cost, and security events
- Demo mode that works without external credentials

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m pytest
python -m uvicorn observability.api:app --reload --port 8095
```

Open `http://localhost:8095/docs` for the API. Start the dashboard in another terminal:

```powershell
streamlit run dashboard/app.py
```

For a local demo, set `DEMO_MODE=true`; this seeds representative data and allows protected API routes without an API key. The safe application default is `DEMO_MODE=false`.

For production, set `DEMO_MODE=false` and configure `OBSERVABILITY_API_KEY`. All non-health API routes require this value in the `X-API-Key` header. The dashboard receives only the API URL and API key; it never receives the Supabase service-role key.

## Repository layout

```text
observability/       Core models, SDK, repositories, evaluation, regression, and API
dashboard/           Streamlit dashboard
migrations/          Supabase SQL schema
tests/               Automated tests
scheduler.py         Scheduled evaluation entry point
Dockerfile           API container
docker-compose.yml   API and dashboard containers
```

## SDK usage

```python
from observability.repositories import InMemoryRepository
from observability.sdk import trace_llm

repository = InMemoryRepository()
with trace_llm(repository, "skore-pipeline", "dimension_fundamentals", "claude-sonnet-4-6") as tracer:
    response = {"input_tokens": 1200, "output_tokens": 350}
    tracer.set_output(response)
```

In a service, replace `InMemoryRepository` with the configured repository or an ingestion client. The context manager records successful and failed calls on exit.

## Supabase setup

1. Create a Supabase project.
2. Run `migrations/001_initial_schema.sql` in the SQL editor.
3. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env`.
4. Set `DEMO_MODE=false` after confirming the schema and access policy.

The service-role key must remain server-side and must never be exposed in Streamlit client code.

## Evaluation and alerts

`POST /api/evaluations/run` accepts a service and cases such as:

```json
{"service":"advisor-brief-agent","cases":[{"score":0.9},{"score":0.8}]}
```

The first run establishes a baseline. Later runs compare scores using `REGRESSION_TOLERANCE`. Alerts are persisted and can be queried through `GET /api/alerts`.

## Scheduler

Run a local scheduled evaluation pass with:

```powershell
python scheduler.py
```

For production, invoke it from cron, GitHub Actions, or a managed scheduler rather than keeping a process alive inside the API container.

## Configuration

See `.env.example`. Anthropic, Resend, and Supabase integrations are optional until real credentials are provided. Demo mode intentionally uses local in-memory data so the complete workflow can be reviewed safely.

## Current integration boundary

The workspace does not contain the eight observed AI services yet. Their adapters and shared-table integration are represented by the SDK contract, fixtures, and `llm_audit_log` schema. Real service-specific instrumentation can be added when those repositories and API credentials are available.

## Submission status

This repository is ready for review in demo mode. Production integration requires access to the target services, Supabase project, and optional Anthropic/Resend credentials. Secrets are intentionally excluded from Git and must be supplied through environment variables.
