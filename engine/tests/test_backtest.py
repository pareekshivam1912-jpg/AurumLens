"""Tests for walk-forward backtesting engine (Design §6.15).

Mandatory coverage from Phase.md §4:
- No-leakage tests (walk-forward isolation)
- Deterministic seeded baselines
- DSR responds to n_trials
- Trial registry logs every config
- t+1 execution and exit conditions
- P&L attribution (strategy vs residual gold)
"""

from datetime import date, timedelta
import pytest

from aurumlens.backtest.folds import Fold, TrialRegistry, build_folds
from aurumlens.backtest.executor import compute_trade_pnl, should_exit
from aurumlens.backtest.metrics import (
    compute_backtest_metrics,
    compute_deflated_sharpe,
    compute_max_drawdown,
    compute_sharpe,
)
from aurumlens.backtest.baselines import (
    always_quiet_baseline,
    random_entry_baseline,
    run_random_baselines,
)


# --- Folds ---

def _make_dates(n: int, start: date = date(2025, 1, 1)) -> list[date]:
    """Generate n weekdays starting from `start`."""
    dates = []
    d = start
    while len(dates) < n:
        if d.weekday() < 5:  # Mon-Fri
            dates.append(d)
        d += timedelta(days=1)
    return dates


def test_folds_chronological_no_overlap():
    """Walk-forward folds must be strictly chronological with no overlap."""
    dates = _make_dates(300)
    folds = build_folds(dates, train_window=120, test_window=30)

    assert len(folds) >= 2

    for i, fold in enumerate(folds):
        # Train must end before test starts
        assert fold.train_end < fold.test_start
        # No overlap between consecutive folds' test periods
        if i > 0 and not fold.is_holdout:
            assert fold.test_start >= folds[i - 1].test_start


def test_folds_train_does_not_leak_into_test():
    """Train data must never include test dates (no look-ahead)."""
    dates = _make_dates(200)
    folds = build_folds(dates, train_window=60, test_window=20)

    for fold in folds:
        # Strict: train_end < test_start
        assert fold.train_end < fold.test_start, (
            f"Train {fold.train_end} overlaps test {fold.test_start}"
        )


def test_holdout_separate():
    """Holdout fold is marked separately and uses all pre-holdout data for training."""
    dates = _make_dates(300, start=date(2025, 1, 1))
    holdout_start = date(2025, 10, 1)
    folds = build_folds(dates, train_window=60, test_window=20, holdout_start=holdout_start)

    holdout_folds = [f for f in folds if f.is_holdout]
    assert len(holdout_folds) == 1

    hf = holdout_folds[0]
    assert hf.test_start >= holdout_start
    assert hf.train_end < holdout_start


def test_insufficient_data_returns_empty():
    """With too few dates, no folds should be produced."""
    dates = _make_dates(10)
    folds = build_folds(dates, train_window=120, test_window=30)
    assert folds == []


# --- Trial Registry ---

def test_trial_registry_logs_every_config():
    """Every config tried must be logged in the trial registry."""
    registry = TrialRegistry()
    fold = Fold(0, date(2025, 1, 1), date(2025, 5, 1), date(2025, 5, 2), date(2025, 6, 1))

    r1 = registry.register(fold, "v0.4.0", {"entry_z": 2.0, "lookback": 60})
    r2 = registry.register(fold, "v0.4.0", {"entry_z": 2.5, "lookback": 60})
    r3 = registry.register(fold, "v0.4.0", {"entry_z": 2.0, "lookback": 90})

    assert registry.n_trials == 3
    assert r1.trial_id != r2.trial_id
    assert r1.trial_id != r3.trial_id


# --- Executor ---

def test_exit_reversion():
    """REVERSION exit when |z| drops below exit_z."""
    reason = should_exit(
        holding_days=3,
        current_zscore=0.3,
        days_to_expiry_a=20,
        days_to_expiry_b=25,
        exit_z=0.5,
    )
    assert reason == "REVERSION"


def test_exit_time_stop():
    """TIME_STOP exit when holding exceeds max_holding_days."""
    reason = should_exit(
        holding_days=15,
        current_zscore=1.8,
        days_to_expiry_a=20,
        days_to_expiry_b=25,
        max_holding_days=15,
    )
    assert reason == "TIME_STOP"


def test_exit_unsafe_expiry():
    """UNSAFE_EXPIRY exit when leg too close to expiry."""
    reason = should_exit(
        holding_days=3,
        current_zscore=1.8,
        days_to_expiry_a=4,  # within 5-day window
        days_to_expiry_b=25,
        unsafe_expiry_window_days=5,
    )
    assert reason == "UNSAFE_EXPIRY"


def test_no_exit_when_all_ok():
    """No exit when all conditions are fine."""
    reason = should_exit(
        holding_days=3,
        current_zscore=1.8,
        days_to_expiry_a=20,
        days_to_expiry_b=25,
    )
    assert reason is None


def test_trade_pnl_attribution():
    """P&L attribution separates strategy from residual gold exposure."""
    result = compute_trade_pnl(
        entry_norm_a=120500.0,
        entry_norm_b=120400.0,
        exit_norm_a=120300.0,   # A fell 200
        exit_norm_b=120350.0,   # B fell 50
        lots_a=4,
        lots_b=5,
        fine_grams_a=10.0,
        fine_grams_b=8.0,
        residual_fine_g=0.0,  # 4*10 - 5*8 = 0
        total_costs=50.0,
        total_slippage=20.0,
        rich_leg="A",
    )

    assert "gross_pnl" in result
    assert "residual_gold_pnl" in result
    assert "strategy_pnl" in result
    assert "net_pnl" in result
    # Net = gross - costs - slippage
    assert abs(result["net_pnl"] - (result["gross_pnl"] - 50.0 - 20.0)) < 0.01


# --- Metrics ---

def test_sharpe_ratio():
    """Sharpe ratio computation with known values."""
    # All positive returns -> positive Sharpe
    returns = [100, 50, 75, 120, 80]
    sharpe = compute_sharpe(returns)
    assert sharpe is not None
    assert sharpe > 0

    # All equal -> None (zero std)
    sharpe_flat = compute_sharpe([100, 100, 100])
    assert sharpe_flat is None


def test_max_drawdown():
    """Max drawdown from equity curve."""
    equity = [0, 100, 200, 150, 100, 250, 200]
    dd = compute_max_drawdown(equity)
    assert dd == 100  # Peak 200, trough 100


def test_dsr_responds_to_n_trials():
    """DSR must decrease as n_trials increases (more multiple-testing penalty)."""
    sr = 1.5
    n_ret = 100

    dsr_1 = compute_deflated_sharpe(sr, n_ret, n_trials=1)
    dsr_10 = compute_deflated_sharpe(sr, n_ret, n_trials=10)
    dsr_100 = compute_deflated_sharpe(sr, n_ret, n_trials=100)

    assert dsr_1 is not None
    assert dsr_10 is not None
    assert dsr_100 is not None

    # More trials -> lower DSR (stricter threshold)
    assert dsr_1 > dsr_10 > dsr_100, (
        f"DSR must decrease with more trials: {dsr_1} > {dsr_10} > {dsr_100}"
    )


def test_backtest_metrics_with_trades():
    """BacktestMetrics aggregation from trade data."""
    pnls = [100, -50, 75, -30, 200]
    costs = [10, 10, 10, 10, 10]
    slips = [5, 5, 5, 5, 5]
    days = [5, 3, 7, 2, 10]

    metrics = compute_backtest_metrics(pnls, costs, slips, days, n_trials=5)

    assert metrics.total_trades == 5
    assert metrics.winning_trades == 3
    assert metrics.hit_rate == 0.6
    assert metrics.net_pnl == sum(pnls)
    assert metrics.avg_holding_days == 5.4


def test_backtest_metrics_empty():
    """Empty trade list returns zero metrics."""
    metrics = compute_backtest_metrics([], [], [], [])
    assert metrics.total_trades == 0
    assert metrics.net_pnl == 0.0


# --- Baselines ---

def test_always_quiet_zero_pnl():
    """Always-quiet baseline has zero P&L and zero trades."""
    result = always_quiet_baseline()
    assert result.net_pnl == 0.0
    assert result.total_trades == 0
    assert result.strategy_name == "always_quiet"


def test_random_baseline_deterministic():
    """Same seed produces identical results (deterministic, R15)."""
    r1 = random_entry_baseline(n_dates=100, seed=42)
    r2 = random_entry_baseline(n_dates=100, seed=42)

    assert r1.net_pnl == r2.net_pnl
    assert r1.total_trades == r2.total_trades
    assert r1.hit_rate == r2.hit_rate


def test_random_baselines_distribution():
    """Running N baselines produces N different results (distribution)."""
    results = run_random_baselines(n_runs=10, n_dates=50)
    assert len(results) == 10
    # Different seeds should give different P&Ls
    pnls = {r.net_pnl for r in results}
    assert len(pnls) > 1  # Not all identical
