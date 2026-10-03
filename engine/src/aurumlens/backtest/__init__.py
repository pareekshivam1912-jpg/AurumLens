"""AurumLens Walk-Forward Backtest Engine."""

from aurumlens.backtest.folds import (
    Fold,
    TrialRecord,
    TrialRegistry,
    build_folds,
)
from aurumlens.backtest.executor import (
    TradeEntry,
    compute_trade_pnl,
    should_exit,
)
from aurumlens.backtest.metrics import (
    BacktestMetrics,
    compute_backtest_metrics,
    compute_deflated_sharpe,
    compute_max_drawdown,
    compute_sharpe,
)
from aurumlens.backtest.baselines import (
    BaselineResult,
    always_quiet_baseline,
    random_entry_baseline,
    run_random_baselines,
)

__all__ = [
    # Folds
    "Fold", "TrialRecord", "TrialRegistry", "build_folds",
    # Executor
    "TradeEntry", "compute_trade_pnl", "should_exit",
    # Metrics
    "BacktestMetrics", "compute_backtest_metrics",
    "compute_deflated_sharpe", "compute_max_drawdown", "compute_sharpe",
    # Baselines
    "BaselineResult", "always_quiet_baseline",
    "random_entry_baseline", "run_random_baselines",
]
