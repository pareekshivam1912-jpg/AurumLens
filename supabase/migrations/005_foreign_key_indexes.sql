-- 005_foreign_key_indexes.sql
-- Indexes for unindexed foreign keys (Supabase performance advisor fix)

CREATE INDEX idx_cost_line_signal_id ON public.cost_line (signal_id);
CREATE INDEX idx_daily_price_file_id ON public.daily_price (file_id);
CREATE INDEX idx_pair_daily_leg_a ON public.pair_daily (leg_a_contract_id);
CREATE INDEX idx_pair_daily_leg_b ON public.pair_daily (leg_b_contract_id);
CREATE INDEX idx_trade_run_id ON public.trade (run_id);
CREATE INDEX idx_trial_run_id ON public.trial (run_id);
