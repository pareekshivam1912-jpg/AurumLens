-- 003_backtest_paper.sql
-- Backtest and paper trading tables

create table public.backtest_run (
  run_id uuid primary key default gen_random_uuid(),
  dataset_version text not null, config_version text not null,
  folds jsonb not null, is_holdout boolean not null default false,
  summary jsonb, created_at timestamptz not null default now()
);

create table public.trial (
  trial_id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.backtest_run(run_id),
  params jsonb not null, train_metric numeric
);

create table public.trade (
  trade_id uuid primary key default gen_random_uuid(),
  run_id uuid references public.backtest_run(run_id),
  pair_id text not null, entry_date date not null, exit_date date,
  legs jsonb not null,                           -- actual contracts, lots, entry/exit prices
  gross_pnl numeric, costs numeric, slippage numeric, net_pnl numeric,
  strategy_pnl numeric, residual_gold_pnl numeric, exit_reason text
);

create table public.paper_position (
  position_id uuid primary key default gen_random_uuid(),
  signal_id uuid not null unique references public.signal(signal_id),  -- duplicate-execution guard
  state text not null check (state in ('OPEN','CLOSED','FAILED','PARTIAL')),
  legs jsonb not null, pnl jsonb, opened_at timestamptz default now(), closed_at timestamptz
);

create table public.audit_log (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(), actor text not null, action text not null, detail jsonb
);
