"""Chronological fold builder and trial registry for walk-forward backtesting.

Implements Design §6.15:
- Chronological folds (train_window, test_window). Parameters chosen on train only.
- Trial registry: every config tried is logged with a unique trial_id.
- Holdout: the final period runs once, after methodology is frozen.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Sequence


@dataclass(frozen=True)
class Fold:
    """A single chronological train/test fold."""
    fold_index: int
    train_start: date
    train_end: date
    test_start: date
    test_end: date
    is_holdout: bool = False

    @property
    def train_days(self) -> int:
        return (self.train_end - self.train_start).days + 1

    @property
    def test_days(self) -> int:
        return (self.test_end - self.test_start).days + 1


@dataclass
class TrialRecord:
    """Trial registry entry — every config tried is logged (R14)."""
    trial_id: str
    fold_index: int
    config_version: str
    parameters: Dict[str, Any]
    train_start: date
    train_end: date
    test_start: date
    test_end: date
    is_holdout: bool = False
    metrics: Dict[str, float] = field(default_factory=dict)


def build_folds(
    all_dates: Sequence[date],
    train_window: int = 120,
    test_window: int = 30,
    holdout_start: Optional[date] = None,
) -> List[Fold]:
    """Build chronological walk-forward folds from sorted trade dates.

    Parameters
    ----------
    all_dates : Sequence[date]
        Sorted list of available trade dates.
    train_window : int
        Number of trade dates in each training window.
    test_window : int
        Number of trade dates in each test window.
    holdout_start : Optional[date]
        If set, dates on or after this date form the holdout fold.
        The holdout is labeled separately and runs once.

    Returns
    -------
    list[Fold]
        Chronological folds. The last fold may be marked is_holdout=True.
    """
    sorted_dates = sorted(set(all_dates))
    n = len(sorted_dates)

    if n < train_window + 1:
        return []

    # Separate holdout if configured
    holdout_dates: List[date] = []
    working_dates = sorted_dates

    if holdout_start is not None:
        working_dates = [d for d in sorted_dates if d < holdout_start]
        holdout_dates = [d for d in sorted_dates if d >= holdout_start]

    folds: List[Fold] = []
    fold_idx = 0
    start = 0

    while start + train_window < len(working_dates):
        train_end_idx = start + train_window - 1
        test_start_idx = train_end_idx + 1
        test_end_idx = min(test_start_idx + test_window - 1, len(working_dates) - 1)

        if test_start_idx >= len(working_dates):
            break

        folds.append(Fold(
            fold_index=fold_idx,
            train_start=working_dates[start],
            train_end=working_dates[train_end_idx],
            test_start=working_dates[test_start_idx],
            test_end=working_dates[test_end_idx],
            is_holdout=False,
        ))

        fold_idx += 1
        start = test_start_idx  # rolling forward

    # Add holdout fold if available
    if holdout_dates and working_dates:
        # Train on all pre-holdout data
        folds.append(Fold(
            fold_index=fold_idx,
            train_start=working_dates[0],
            train_end=working_dates[-1],
            test_start=holdout_dates[0],
            test_end=holdout_dates[-1],
            is_holdout=True,
        ))

    return folds


class TrialRegistry:
    """Registry for all configs tried during backtesting.

    Every config tried is logged (R14). The count feeds into the
    Deflated Sharpe Ratio calculation.
    """

    def __init__(self) -> None:
        self._trials: List[TrialRecord] = []

    def register(
        self,
        fold: Fold,
        config_version: str,
        parameters: Dict[str, Any],
    ) -> TrialRecord:
        """Register a new trial and return its record."""
        param_hash = hashlib.sha256(
            json.dumps(parameters, sort_keys=True, default=str).encode()
        ).hexdigest()[:12]

        trial_id = f"trial_{fold.fold_index}_{param_hash}"

        record = TrialRecord(
            trial_id=trial_id,
            fold_index=fold.fold_index,
            config_version=config_version,
            parameters=parameters,
            train_start=fold.train_start,
            train_end=fold.train_end,
            test_start=fold.test_start,
            test_end=fold.test_end,
            is_holdout=fold.is_holdout,
        )
        self._trials.append(record)
        return record

    @property
    def n_trials(self) -> int:
        """Total number of trials — feeds into DSR."""
        return len(self._trials)

    @property
    def trials(self) -> List[TrialRecord]:
        return list(self._trials)
