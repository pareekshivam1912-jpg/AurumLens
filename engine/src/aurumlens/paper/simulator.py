"""Paper Execution Simulator Adapter for AurumLens.

Implements two-leg simulated order execution, adverse slippage fills,
position state tracking, exit triggers, and zero-duplicate guard.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class PositionStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    FAILED = "FAILED"


@dataclass
class PaperLeg:
    symbol: str
    side: str  # 'BUY' or 'SELL'
    lots: int
    fine_grams_per_lot: float
    signal_price: float
    fill_price: float
    slippage_bps: float


@dataclass
class PaperPosition:
    position_id: str
    signal_id: str
    pair_name: str
    created_at: datetime
    status: PositionStatus
    leg_a: PaperLeg
    leg_b: PaperLeg
    residual_fine_g: float
    entry_spread: float
    current_spread: Optional[float] = None
    exit_date: Optional[date] = None
    exit_reason: Optional[str] = None
    gross_pnl: float = 0.0
    total_costs: float = 0.0
    net_pnl: float = 0.0
    audit_trail: List[str] = field(default_factory=list)


class DuplicateExecutionError(Exception):
    """Raised when an execution is attempted on an already staged signal."""
    pass


class PaperExecutionAdapter:
    """Simulated execution engine with duplicate-execution guard and P&L attribution."""

    def __init__(self, initial_capital: float = 1_000_000.0) -> None:
        self.initial_capital = initial_capital
        self.available_capital = initial_capital
        self._executed_signals: Set[str] = set()
        self.positions: Dict[str, PaperPosition] = {}
        self.audit_log: List[Dict[str, Any]] = []

    def _log_audit(self, action: str, signal_id: str, detail: str) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "signal_id": signal_id,
            "detail": detail,
        }
        self.audit_log.append(entry)

    def stage_order(self, evidence: Dict[str, Any]) -> PaperPosition:
        """Stage and simulate fill for a two-leg arbitrage signal.

        Enforces zero-duplicate execution at the signal_id level.
        """
        signal_id = str(evidence.get("signal_id", ""))
        if not signal_id:
            raise ValueError("Evidence must contain a valid signal_id")

        if signal_id in self._executed_signals:
            self._log_audit("DUPLICATE_BLOCKED", signal_id, "Execution blocked by zero-duplicate guard.")
            raise DuplicateExecutionError(f"Signal {signal_id} has already been executed in paper portfolio.")

        self._executed_signals.add(signal_id)

        position_id = f"pos_{signal_id}"
        pair_name = evidence.get("pair_name", "UNKNOWN")
        rich_leg = evidence.get("rich_leg", "A")

        # Leg specs
        price_a = float(evidence.get("quoted_price_a", 120500.0))
        price_b = float(evidence.get("quoted_price_b", 96400.0))
        lots_a = int(evidence.get("lots_a", 4))
        lots_b = int(evidence.get("lots_b", 5))
        slip_a = float(evidence.get("slippage_bps_a", 5.0))
        slip_b = float(evidence.get("slippage_bps_b", 5.0))

        # Adverse fill simulation: buying pays +slip/2, selling receives -slip/2
        side_a = "SELL" if rich_leg == "A" else "BUY"
        side_b = "BUY" if rich_leg == "A" else "SELL"

        fill_a = price_a * (1.0 - (slip_a / 20000.0)) if side_a == "SELL" else price_a * (1.0 + (slip_a / 20000.0))
        fill_b = price_b * (1.0 + (slip_b / 20000.0)) if side_b == "BUY" else price_b * (1.0 - (slip_b / 20000.0))

        leg_a = PaperLeg(
            symbol=evidence.get("leg_a_symbol", "GOLDTEN"),
            side=side_a,
            lots=lots_a,
            fine_grams_per_lot=10.0,
            signal_price=price_a,
            fill_price=round(fill_a, 2),
            slippage_bps=slip_a,
        )

        leg_b = PaperLeg(
            symbol=evidence.get("leg_b_symbol", "GOLDGUINEA"),
            side=side_b,
            lots=lots_b,
            fine_grams_per_lot=8.0,
            signal_price=price_b,
            fill_price=round(fill_b, 2),
            slippage_bps=slip_b,
        )

        pos = PaperPosition(
            position_id=position_id,
            signal_id=signal_id,
            pair_name=pair_name,
            created_at=datetime.now(timezone.utc),
            status=PositionStatus.OPEN,
            leg_a=leg_a,
            leg_b=leg_b,
            residual_fine_g=float(evidence.get("residual_fine_g", 0.0)),
            entry_spread=float(evidence.get("log_spread_adj", 0.00165)),
            audit_trail=[f"Filled t+1: Leg A @ {fill_a:.2f}, Leg B @ {fill_b:.2f}"],
        )

        self.positions[position_id] = pos
        self._log_audit("ORDER_FILLED", signal_id, f"Position {position_id} opened for {pair_name}")

        return pos

    def close_position(
        self,
        position_id: str,
        current_price_a: float,
        current_price_b: float,
        exit_reason: str = "REVERSION",
        costs_inr: float = 170.0,
    ) -> PaperPosition:
        """Simulate closing an open position and compute final P&L."""
        if position_id not in self.positions:
            raise KeyError(f"Position {position_id} not found.")

        pos = self.positions[position_id]
        if pos.status != PositionStatus.OPEN:
            return pos

        # Calculate P&L for leg A and leg B
        delta_a = current_price_a - pos.leg_a.fill_price
        pnl_a = -delta_a * pos.leg_a.lots if pos.leg_a.side == "SELL" else delta_a * pos.leg_a.lots

        delta_b = current_price_b - pos.leg_b.fill_price
        pnl_b = delta_b * pos.leg_b.lots if pos.leg_b.side == "BUY" else -delta_b * pos.leg_b.lots

        gross_pnl = pnl_a + pnl_b
        net_pnl = gross_pnl - costs_inr

        pos.status = PositionStatus.CLOSED
        pos.exit_date = date.today()
        pos.exit_reason = exit_reason
        pos.gross_pnl = round(gross_pnl, 2)
        pos.total_costs = round(costs_inr, 2)
        pos.net_pnl = round(net_pnl, 2)
        pos.audit_trail.append(f"Closed on {exit_reason} with Net P&L: ₹{net_pnl:.2f}")

        self.available_capital += net_pnl
        self._log_audit("POSITION_CLOSED", pos.signal_id, f"Net P&L: ₹{net_pnl:.2f}, Reason: {exit_reason}")

        return pos
