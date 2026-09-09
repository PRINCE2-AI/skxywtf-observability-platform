create extension if not exists pgcrypto;

create table if not exists llm_traces (
  id uuid primary key default gen_random_uuid(),
  trace_id uuid not null,
  service text not null,
  task text not null,
  model text not null,
  input_tokens integer,
  output_tokens integer,
  estimated_cost_usd double precision not null default 0,
  latency_ms integer,
  ttfb_ms integer,
  success boolean not null default true,
  error_type text,
  error_message text,
  context jsonb not null default '{}'::jsonb,
  input_preview text,
  output_preview text,
  created_at timestamptz not null default now()
);

create index if not exists idx_llm_traces_service_created on llm_traces(service, created_at desc);

create table if not exists eval_results (
  id uuid primary key default gen_random_uuid(),
  service text not null,
  evaluator text not null,
  scores jsonb not null default '{}'::jsonb,
  sample_count integer not null default 0,
  metadata jsonb not null default '{}'::jsonb,
  run_at timestamptz not null default now()
);

create table if not exists eval_baselines (
  service text primary key,
  scores jsonb not null,
  set_at timestamptz not null default now()
);

create table if not exists regression_alerts (
  id uuid primary key default gen_random_uuid(),
  service text not null,
  metric text not null,
  baseline double precision not null,
  current double precision not null,
  drop_pct double precision not null,
  status text not null default 'open',
  created_at timestamptz not null default now()
);

create index if not exists idx_regression_alerts_status on regression_alerts(status, created_at desc);

create table if not exists llm_audit_log (
  id uuid primary key default gen_random_uuid(),
  event_type text,
  service text,
  blocked boolean,
  latency_ms integer,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
