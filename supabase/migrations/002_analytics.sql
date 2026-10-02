-- 002_analytics.sql
-- Analytics tables: pair_daily, gate_result, signal, cost_line, market_event

create table public.pair_daily (
  pair_id text not null, trade_date date not null, config_version text not null,
  leg_a_contract_id text not null references public.contract(contract_id),
  leg_b_contract_id text not null references public.contract(contract_id),
  expiry_gap_days int, norm_a numeric, norm_b numeric,
  log_spread_raw numeric, carry_rate numeric,
  carry_source text check (carry_source in ('CURVE','FALLBACK')),
  carry_adj numeric, log_spread_adj numeric, roll_mean numeric, roll_std numeric, zscore numeric,
  rich_leg text, lots_a int, lots_b int, residual_fine_g numeric,
  expected_convergence_inr numeric, cost_total_inr numeric, slippage_inr numeric, buffer_inr numeric,
  net_edge_inr numeric, dataset_version text not null,
  primary key (pair_id, trade_date, config_version)
);

create table public.gate_result (
  pair_id text not null, trade_date date not null, config_version text not null,
  gate_no smallint not null check (gate_no between 1 and 11),
  gate text not null, passed boolean not null,
  value numeric, threshold numeric, margin numeric, reason_code text,
  primary key (pair_id, trade_date, config_version, gate_no)
);

create table public.signal (
  signal_id uuid primary key default gen_random_uuid(),
  pair_id text not null, trade_date date not null, config_version text not null,
  status text not null check (status in ('QUIET','ALERT')),
  direction text, reason_codes text[] not null default '{}',
  near_miss_score numeric,
  evidence jsonb not null,                       -- the full evidence record (PRD §11)
  dataset_version text not null,
  created_at timestamptz not null default now(),
  unique (pair_id, trade_date, config_version)
);

create table public.cost_line (
  id bigint generated always as identity primary key,
  signal_id uuid references public.signal(signal_id),
  trade_id uuid,
  leg text, side text check (side in ('BUY','SELL')),
  component text not null, amount_inr numeric not null
);

create table public.market_event (
  id bigint generated always as identity primary key,
  event_date date not null, label text not null, category text,
  source text, verified boolean not null default false
);
