"""Backtest metrics: Sharpe, max drawdown, hit rate, and Deflated Sharpe Ratio.

The Deflated Sharpe Ratio (DSR) adjusts the observed Sharpe for the number
of trials (n_trials from the trial registry), plus the skewness and kurtosis
of returns. It is reported, never optimized (R15).

DSR formula (Harvey & Liu 2015, Bailey & López de Prado 2014):
    SR* = √(V_SR) × ((1 - γ)Φ⁻¹(1 - 1/N) + γΦ⁻¹(1 - 1/N × e^(-1)))
    DSR = Φ((SR_obs - SR*) / √(V_SR))
    
    V_SR = (1 - skew×SR + (kurt-1)/4 × SR²) / T
    
Where N = n_trials, T = number of observations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class BacktestMetrics:
    """Summary metrics for a backtest run or fold."""
    total_trades: int
    winning_trades: int
    hit_rate: float
    gross_pnl: float
    net_pnl: float
    total_costs: float
    total_slippage: float
    sharpe_ratio: Optional[float]
    max_drawdown: float
    max_drawdown_pct: Optional[float]
    deflated_sharpe: Optional[float]
    avg_holding_days: float
    avg_net_per_trade: float


def compute_sharpe(returns: Sequence[float], annualization: float = 252.0) -> Optional[float]:
    """Compute annualized Sharpe ratio from a sequence of periodic returns.

    Parameters
    ----------
    returns : Sequence[float]
        Period returns (e.g., per-trade net P&L).
    annualization : float
        Annualization factor (252 for daily).

    Returns
    -------
    Optional[float]
        Sharpe ratio, or None if std is zero or insufficient data.
    """
    if len(returns) < 2:
        return None

    mean_r = sum(returns) / len(returns)
    var_r = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std_r = math.sqrt(var_r) if var_r > 0 else 0.0

    if std_r < 1e-12:
        return None

    return (mean_r / std_r) * math.sqrt(annualization)


def compute_max_drawdown(equity_curve: Sequence[float]) -> float:
    """Compute maximum drawdown from an equity curve.

    Parameters
    ----------
    equity_curve : Sequence[float]
        Cumulative P&L or equity values.

    Returns
    -------
    float
        Maximum drawdown (as a positive number in the same units).
    """
    if not equity_curve:
        return 0.0

    peak = equity_curve[0]
    max_dd = 0.0

    for val in equity_curve:
        if val > peak:
            peak = val
        dd = peak - val
        if dd > max_dd:
            max_dd = dd

    return max_dd


def _skewness(values: Sequence[float]) -> float:
    """Sample skewness."""
    n = len(values)
    if n < 3:
        return 0.0
    mean = sum(values) / n
    m2 = sum((x - mean) ** 2 for x in values) / n
    m3 = sum((x - mean) ** 3 for x in values) / n
    if m2 < 1e-15:
        return 0.0
    return m3 / (m2 ** 1.5)


def _kurtosis(values: Sequence[float]) -> float:
    """Sample excess kurtosis."""
    n = len(values)
    if n < 4:
        return 0.0
    mean = sum(values) / n
    m2 = sum((x - mean) ** 2 for x in values) / n
    m4 = sum((x - mean) ** 4 for x in values) / n
    if m2 < 1e-15:
        return 0.0
    return (m4 / (m2 ** 2)) - 3.0


def _norm_cdf(x: float) -> float:
    """Standard normal CDF approximation (Abramowitz & Stegun)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Inverse standard normal CDF (rational approximation)."""
    if p <= 0:
        return -10.0
    if p >= 1:
        return 10.0
    # Beasley-Springer-Moro algorithm
    a = [0, -3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [0, -5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [0, -7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [0, 7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00]

    p_low = 0.02425
    p_high = 1.0 - p_low

    if p < p_low:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[1]*q+c[2])*q+c[3])*q+c[4])*q+c[5])*q+c[6]) / \
               ((((d[1]*q+d[2])*q+d[3])*q+d[4])*q+1.0)
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[1]*r+a[2])*r+a[3])*r+a[4])*r+a[5])*r+a[6])*q / \
               (((((b[1]*r+b[2])*r+b[3])*r+b[4])*r+b[5])*r+1.0)
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c[1]*q+c[2])*q+c[3])*q+c[4])*q+c[5])*q+c[6]) / \
                ((((d[1]*q+d[2])*q+d[3])*q+d[4])*q+1.0)


def compute_deflated_sharpe(
    observed_sharpe: float,
    n_returns: int,
    n_trials: int,
    skew: float = 0.0,
    kurt_excess: float = 0.0,
) -> Optional[float]:
    """Compute the Deflated Sharpe Ratio (Bailey & López de Prado 2014).

    DSR adjusts the observed Sharpe for multiple testing (n_trials).
    It is REPORTED, never optimized (R15).

    Parameters
    ----------
    observed_sharpe : float
        Observed Sharpe ratio.
    n_returns : int
        Number of return observations.
    n_trials : int
        Total number of configurations tried (from trial registry).
    skew : float
        Skewness of returns.
    kurt_excess : float
        Excess kurtosis of returns.

    Returns
    -------
    Optional[float]
        DSR (probability that the true Sharpe > 0), or None if insufficient data.
    """
    if n_returns < 2 or n_trials < 1:
        return None

    T = float(n_returns)
    SR = observed_sharpe

    # Variance of Sharpe ratio estimator
    v_sr = (1.0 - skew * SR + ((kurt_excess + 2.0) / 4.0) * SR ** 2) / T
    if v_sr <= 0:
        return None

    # Expected maximum Sharpe under the null (N independent trials)
    # SR* ≈ √(2 ln(N)) - (ln(π) + ln(ln(N))) / (2√(2 ln(N)))
    # Simplified: use Euler-Mascheroni approximation
    if n_trials <= 1:
        sr_star = 0.0
    else:
        ln_n = math.log(n_trials)
        sr_star = math.sqrt(2.0 * ln_n) - (math.log(math.pi) + math.log(ln_n)) / (2.0 * math.sqrt(2.0 * ln_n))

    # DSR = Φ((SR_obs - SR*) / √V_SR)
    dsr = _norm_cdf((SR - sr_star) / math.sqrt(v_sr))

    return round(dsr, 6)


def compute_backtest_metrics(
    trade_pnls: Sequence[float],
    trade_costs: Sequence[float],
    trade_slippages: Sequence[float],
    trade_holding_days: Sequence[int],
    n_trials: int = 1,
    initial_equity: float = 0.0,
) -> BacktestMetrics:
    """Compute summary metrics from a backtest trade ledger.

    Parameters
    ----------
    trade_pnls : Sequence[float]
        Net P&L for each trade.
    trade_costs, trade_slippages : Sequence[float]
        Costs and slippage per trade.
    trade_holding_days : Sequence[int]
        Holding period for each trade.
    n_trials : int
        Number of configs tried (for DSR).
    initial_equity : float
        Starting equity for drawdown calculation.
    """
    n = len(trade_pnls)
    if n == 0:
        return BacktestMetrics(
            total_trades=0, winning_trades=0, hit_rate=0.0,
            gross_pnl=0.0, net_pnl=0.0, total_costs=0.0, total_slippage=0.0,
            sharpe_ratio=None, max_drawdown=0.0, max_drawdown_pct=None,
            deflated_sharpe=None, avg_holding_days=0.0, avg_net_per_trade=0.0,
        )

    net_pnls = list(trade_pnls)
    gross_pnls = [p + c + s for p, c, s in zip(trade_pnls, trade_costs, trade_slippages)]

    winning = sum(1 for p in net_pnls if p > 0)
    total_gross = sum(gross_pnls)
    total_net = sum(net_pnls)
    total_cost = sum(trade_costs)
    total_slip = sum(trade_slippages)

    # Equity curve
    equity = [initial_equity]
    for p in net_pnls:
        equity.append(equity[-1] + p)

    max_dd = compute_max_drawdown(equity)
    peak_equity = max(equity) if equity else 0.0
    max_dd_pct = (max_dd / peak_equity * 100) if peak_equity > 0 else None

    # Sharpe
    sharpe = compute_sharpe(net_pnls)

    # DSR
    dsr = None
    if sharpe is not None:
        skew = _skewness(net_pnls)
        kurt = _kurtosis(net_pnls)
        dsr = compute_deflated_sharpe(sharpe, n, n_trials, skew, kurt)

    avg_hold = sum(trade_holding_days) / n if n > 0 else 0.0
    avg_net = total_net / n if n > 0 else 0.0

    return BacktestMetrics(
        total_trades=n,
        winning_trades=winning,
        hit_rate=round(winning / n, 4) if n > 0 else 0.0,
        gross_pnl=round(total_gross, 2),
        net_pnl=round(total_net, 2),
        total_costs=round(total_cost, 2),
        total_slippage=round(total_slip, 2),
        sharpe_ratio=round(sharpe, 4) if sharpe is not None else None,
        max_drawdown=round(max_dd, 2),
        max_drawdown_pct=round(max_dd_pct, 2) if max_dd_pct is not None else None,
        deflated_sharpe=dsr,
        avg_holding_days=round(avg_hold, 1),
        avg_net_per_trade=round(avg_net, 2),
    )
