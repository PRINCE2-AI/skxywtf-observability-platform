# SKXYWTF Observability & Evaluation Platform

## 1. Project Goal

Build a production-oriented observability platform for SKXYWTF's AI services. The platform will make LLM usage, cost, latency, quality, errors, security events, and quality regressions visible in one place.

## 2. Planned Components

## 2.1 System Flow

```text
AI Services
  |
  v
Trace SDK / Service Adapters
  |
  v
FastAPI Ingestion + Evaluation API
  |
  v
Supabase PostgreSQL
  |
  +--> Scheduler --> Evaluation Runner --> Regression Detector --> Alerts
  |
  +--> Streamlit Dashboard
```

The system will keep collection, evaluation, regression logic, API access, and presentation separate. This makes each part testable and allows the dashboard to work with either live or demo data.

### Trace Collector SDK

- Python package with `trace_llm` context manager and `TraceContext`.
- Capture service, task, model, tokens, latency, time-to-first-byte, success, errors, cost, and custom context.
- Store structured trace events in Supabase.
- Support safe operation when optional integrations are unavailable.

### Evaluation Runner

- Scheduled evaluation orchestration.
- RAGAS evaluation for retrieval-based services.
- LLM-as-judge evaluation for generated outputs.
- Evaluation adapters for advisor briefs, research, SKORE, Ollama/API comparison, FinBERT, security proxy, and AI router.
- Store evaluation results and test-case metadata.

### Regression Detector

- Create and retrieve known-good baselines.
- Compare current scores with baseline scores.
- Configurable tolerance, defaulting to 10 percent.
- Avoid invalid alerts for missing, zero, or non-numeric metrics.
- Persist alerts and send email notifications through Resend when configured.

### FastAPI Service

- Health endpoint.
- Trace ingestion/query endpoints.
- Evaluation trigger/status endpoints.
- Baseline management endpoints.
- Regression alert query and resolution endpoints.
- Configuration through environment variables.

### Streamlit Dashboard

1. AI Stack Overview
2. Trace Explorer
3. Evaluation Scores
4. Cost and Budget
5. Security Events

The dashboard will support real Supabase data when configured and useful demo data when it is not.

### Scheduler

- Daily and weekly evaluation jobs.
- Manual evaluation trigger through the API/dashboard.
- Clear logging and failure handling.

## 2.1 MVP Priority

The first usable release will focus on the smallest complete workflow:

1. Trace two representative services.
2. Store and query traces.
3. Calculate token cost and latency metrics.
4. Run one RAGAS workflow and one judge workflow.
5. Create a baseline and detect a synthetic regression.
6. Show health, cost, traces, scores, and alerts in the dashboard.

The remaining service adapters and advanced metrics will be added after this workflow is stable.

## 3. Data Model

Planned Supabase tables:

- `llm_traces`
- `eval_results`
- `eval_baselines`
- `regression_alerts`
- `llm_audit_log` integration reader

Every table will include timestamps and service identifiers where applicable. Query paths will use filters and pagination so the dashboard does not load an unbounded trace history.

## 3.1 Privacy and Security Rules

- API keys will be read only from environment variables.
- Raw prompts and outputs will be opt-in and redacted before dashboard display.
- Secrets will never be written to traces, logs, fixtures, or screenshots.
- Service-role Supabase access will remain server-side only.
- Error messages will be sanitized before external alert delivery.
- The README will document retention, redaction, and known data exposure limitations.

SQL migrations will be included so the schema can be created reproducibly.

## 4. Repository Structure

```text
observability/
  sdk/
  evaluation/
  regression/
  api/
  dashboard/
    pages/
  tests/
  migrations/
  scheduler.py
  requirements.txt
  .env.example
  Dockerfile
  README.md
```

## 5. Implementation Phases

### Phase 1: Reliable Core

- Create the Python project structure.
- Implement typed trace models and cost estimation.
- Implement the tracer SDK and local/in-memory test storage.
- Add Supabase repository integration.
- Add database migration and environment configuration.
- Write unit tests for tracing, errors, latency, and cost calculation.

### Phase 2: Evaluation and Regression

- Implement evaluation result models and persistence.
- Add RAGAS adapter with a mock/fallback mode for local development.
- Add LLM-as-judge adapter with structured JSON validation.
- Implement baseline management and regression detection.
- Add alert persistence and optional Resend notifications.
- Test missing baselines, NaN values, zero baselines, and noisy metrics.

### Phase 3: API and Dashboard

- Implement FastAPI routes and health checks.
- Build overview, traces, evaluations, cost, and security pages.
- Add filters, charts, status indicators, alert views, and manual evaluation controls.
- Add demo data mode so the dashboard can be reviewed without secrets.

### Phase 4: Scheduling and Delivery

- Add daily/weekly scheduler configuration.
- Add Docker support.
- Add integration tests and API tests.
- Complete README with setup, SDK integration, Supabase setup, dashboard usage, and limitations.
- Validate the complete local workflow.

## 5.1 Validation Strategy

- Unit tests: cost calculation, trace lifecycle, token extraction, baseline comparison, and metric edge cases.
- API tests: health, trace ingestion, evaluation triggers, baseline operations, and alert queries.
- Integration tests: Supabase repository behavior using a test or local database substitute.
- Dashboard smoke test: demo mode loads all pages and renders empty, normal, and alert states.
- Failure tests: provider error, Supabase outage, invalid judge JSON, timeout, NaN score, and missing baseline.

## 5.2 Delivery Checkpoints

- Checkpoint A: SDK creates a valid trace for success and failure paths.
- Checkpoint B: Evaluation result is persisted and visible through the API.
- Checkpoint C: A controlled score drop creates exactly one alert and does not alert when within tolerance.
- Checkpoint D: Dashboard answers spend, health, regression, and security questions using demo data.
- Checkpoint E: Docker startup and README setup instructions work on a clean environment.

## 6. Important Assumptions

- The current workspace contains the specification but not the eight existing AI services.
- Real service integration will initially be represented by adapters, sample payloads, and test fixtures.
- Supabase, Anthropic, and Resend credentials will be supplied later through environment variables, never committed to the repository.
- Demo mode will be available so the application can run without external credentials.
- The first implementation will prioritize a reliable working system over pretending that every external service is already connected.

## 6.1 Explicit Non-Goals for the First Release

- Rewriting or owning the internal logic of the eight observed services.
- Building a full authentication and multi-tenant access-control product.
- Guaranteeing that an LLM judge is perfectly objective.
- Replacing the security proxy; this platform only reads its audit events.
- Claiming production accuracy before real labelled datasets and service traffic are available.

## 6.2 Main Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Real services are unavailable | Use adapters, fixtures, and demo mode first. |
| LLM judge returns malformed output | Enforce structured parsing, retries, and failed-run status. |
| RAGAS is expensive or slow | Keep test sets small, schedule them, and support mocked local runs. |
| False regression alerts | Use configurable tolerance, minimum sample sizes, and explicit metric types. |
| Sensitive prompt data leaks | Redact by default and keep raw payload storage disabled unless configured. |
| Dashboard becomes slow | Add date filters, pagination, aggregation queries, and cached summaries. |

## 7. Current Status

The demo-ready implementation is complete and validated locally. Production integration is pending access to the target AI services, Supabase project, and optional provider credentials.

The repository can be reviewed and shared now in demo mode.

## 8. Definition of Done

- The application starts locally with documented commands.
- Trace events can be created, stored, queried, and tested.
- Evaluation results and baselines can be stored and compared.
- Regression alerts work with configurable thresholds.
- Dashboard pages show demo data and support configured Supabase data.
- API, SDK, regression, and core dashboard behavior have focused tests.
- Docker and environment setup are documented.
- Limitations and external integration requirements are clearly documented.