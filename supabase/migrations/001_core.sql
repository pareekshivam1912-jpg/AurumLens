-- 001_core.sql
-- Core tables: contract_spec, source_file, contract, daily_price

create table public.contract_spec (
  symbol text primary key check (symbol in ('GOLDM','GOLDTEN','GOLDGUINEA','GOLDPETAL')),
  trading_unit_g numeric, quote_basis_g numeric, purity numeric,
  expiry_rule text, tender_days int, tick_size numeric,
  field_status jsonb not null default '{}'::jsonb,   -- {"purity":"DISPUTED", ...}
  source_reference text, verified_at timestamptz
);

create table public.source_file (
  file_id bigint generated always as identity primary key,
  requested_date date not null,
  returned_date date,
  adapter text not null check (adapter in ('legacy','cdp')),
  sha256 text not null unique,
  storage_path text not null,
  status text not null check (status in ('OK','REJECTED')),
  reject_reason text,
  fetched_at timestamptz not null default now()
);

create table public.contract (
  contract_id text primary key,                       -- e.g. GOLDM_20261105
  symbol text not null references public.contract_spec(symbol),
  expiry_date date not null,
  first_seen date, last_seen date,
  unique (symbol, expiry_date)
);

create table public.daily_price (
  contract_id text not null references public.contract(contract_id),
  trade_date date not null,
  open numeric, high numeric, low numeric, close numeric, settlement numeric,
  volume bigint, open_interest bigint,
  price_used numeric,
  price_source text check (price_source in ('settlement','close')),
  price_quality text not null check (price_quality in ('OK','SUSPECT')),
  quality_reason text,
  normalized_price numeric,
  file_id bigint not null references public.source_file(file_id),
  dataset_version text not null,
  primary key (contract_id, trade_date)
);
