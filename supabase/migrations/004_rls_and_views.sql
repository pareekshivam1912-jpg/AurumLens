-- 004_rls_and_views.sql
-- Enable RLS on all 14 tables, SELECT-only policies, view, and Realtime

-- Enable RLS on every table
do $$
declare t text;
begin
  foreach t in array array['contract_spec','source_file','contract','daily_price','pair_daily','gate_result',
                           'signal','cost_line','market_event','backtest_run','trial','trade','paper_position','audit_log']
  loop
    execute format('alter table public.%I enable row level security', t);
  end loop;

  -- Public read (anon + authenticated) for analytics tables
  foreach t in array array['contract_spec','contract','daily_price','pair_daily','gate_result',
                           'signal','cost_line','market_event','backtest_run','trial','trade']
  loop
    execute format('create policy "public read" on public.%I for select to anon, authenticated using (true)', t);
  end loop;
end $$;

-- Admin-only read for sensitive tables (authenticated only, no anon)
create policy "admin read" on public.source_file    for select to authenticated using (true);
create policy "admin read" on public.paper_position for select to authenticated using (true);
create policy "admin read" on public.audit_log      for select to authenticated using (true);

-- No INSERT / UPDATE / DELETE policies for anon or authenticated.
-- Only the service role (Python engine) can write.

-- Latest status view (no formulas, only select and join)
create view public.v_latest_status with (security_invoker = true) as
select distinct on (pair_id) pair_id, trade_date, status, reason_codes, near_miss_score, config_version
from public.signal order by pair_id, trade_date desc, created_at desc;

-- Enable Realtime on signal table for live ALERT feed
alter publication supabase_realtime add table public.signal;
