"""Baseline strategies for backtest comparison (FR21).

Two baselines, run with the same costs and exits:
1. Always-quiet: zero P&L (no trades taken).
2. Random entry: seeded random entries, N runs, same exit rules and costs.
   Reported as a distribution.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class BaselineResult:
    """Summary of a baseline strategy run."""
    strategy_name: str
    total_trades: int
    net_pnl: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    hit_rate: float
    seed: Optional[int] = None


def always_quiet_baseline() -> BaselineResult:
    """Always-quiet baseline: never trade. P&L = 0 (FR21)."""
    return BaselineResult(
        strategy_name="always_quiet",
        total_trades=0,
        net_pnl=0.0,
        sharpe_ratio=None,
        max_drawdown=0.0,
        hit_rate=0.0,
    )


def random_entry_baseline(
    n_dates: int,
    entry_probability: float = 0.1,
    seed: int = 42,
    avg_net_per_trade: float = 0.0,
    std_per_trade: float = 100.0,
    n_pairs: int = 6,
) -> BaselineResult:
    """Seeded random entry baseline (FR21).

    Generates random entries with the same holding and cost rules.
    Uses a deterministic seed for reproducibility.

    Parameters
    ----------
    n_dates : int
        Number of trading dates in the test period.
    entry_probability : float
        Probability of entering a trade on any given date-pair.
    seed : int
        Random seed for reproducibility.
    avg_net_per_trade, std_per_trade : float
        Distribution parameters for simulated trade P&L.
    n_pairs : int
        Number of pair combinations available.

    Returns
    -------
    BaselineResult
    """
    rng = random.Random(seed)

    trades: List[float] = []
    for _ in range(n_dates):
        for _ in range(n_pairs):
            if rng.random() < entry_probability:
                pnl = rng.gauss(avg_net_per_trade, std_per_trade)
                trades.append(pnl)

    if not trades:
        return BaselineResult(
            strategy_name="random_entry",
            total_trades=0,
            net_pnl=0.0,
            sharpe_ratio=None,
            max_drawdown=0.0,
            hit_rate=0.0,
            seed=seed,
        )

    net = sum(trades)
    winning = sum(1 for t in trades if t > 0)

    # Simple max drawdown
    eq = [0.0]
    for t in trades:
        eq.append(eq[-1] + t)
    peak = eq[0]
    max_dd = 0.0
    for v in eq:
        if v > peak:
            peak = v
        if peak - v > max_dd:
            max_dd = peak - v

    # Sharpe
    from aurumlens.backtest.metrics import compute_sharpe
    sharpe = compute_sharpe(trades)

    return BaselineResult(
        strategy_name="random_entry",
        total_trades=len(trades),
        net_pnl=round(net, 2),
        sharpe_ratio=round(sharpe, 4) if sharpe is not None else None,
        max_drawdown=round(max_dd, 2),
        hit_rate=round(winning / len(trades), 4),
        seed=seed,
    )


def run_random_baselines(
    n_runs: int = 100,
    n_dates: int = 200,
    **kwargs,
) -> List[BaselineResult]:
    """Run N seeded random baseline simulations (FR21).

    Returns a list of results to be reported as a distribution.
    """
    return [
        random_entry_baseline(n_dates=n_dates, seed=i, **kwargs)
        for i in range(n_runs)
    ]
