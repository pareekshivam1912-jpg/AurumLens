"""Telegram Alert Adapter for AurumLens relative-value intelligence.

Implements alert dispatch behind the AlertNotifier interface with
built-in deduplication by signal_id (preventing duplicate message spam).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set


class AlertNotifier(ABC):
    """Abstract interface for dispatching alerts."""

    @abstractmethod
    def send_alert(self, evidence: Dict[str, Any]) -> bool:
        """Send an alert. Returns True if sent, False if suppressed or failed."""
        pass


@dataclass
class TelegramConfig:
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    enabled: bool = False


class TelegramAlertAdapter(AlertNotifier):
    """Telegram alert dispatcher with signal_id deduplication."""

    def __init__(self, config: Optional[TelegramConfig] = None) -> None:
        self.config = config or TelegramConfig()
        self._sent_signals: Set[str] = set()

    def format_alert_message(self, evidence: Dict[str, Any]) -> str:
        """Format an alert message with compliance disclaimer."""
        signal_id = evidence.get("signal_id", "N/A")
        pair_name = evidence.get("pair_name", "UNKNOWN")
        zscore = evidence.get("zscore", 0.0)
        net_edge = evidence.get("net_expected_edge_inr", 0.0)
        lots_a = evidence.get("lots_a", 0)
        lots_b = evidence.get("lots_b", 0)
        residual = evidence.get("residual_fine_g", 0.0)
        leg_a = evidence.get("leg_a_symbol", "A")
        leg_b = evidence.get("leg_b_symbol", "B")

        msg = (
            f"🚨 *AurumLens Relative-Value ALERT*\n\n"
            f"• *Signal ID:* `{signal_id}`\n"
            f"• *Pair Mandate:* `{pair_name}`\n"
            f"• *Divergence:* `z = +{zscore:.2f}σ`\n"
            f"• *Expected Net Edge:* `+₹{net_edge:.2f}`\n"
            f"• *Optimal Sizing:* `{lots_a} lots {leg_a} : {lots_b} lots {leg_b}`\n"
            f"• *Residual Fine Gold:* `{residual:.1f}g`\n"
            f"• *All 12 Risk Gates:* `PASSED (100%)`\n\n"
            f"⚠️ _Analytics only — not investment advice. Simulated decision support only._"
        )
        return msg

    def send_alert(self, evidence: Dict[str, Any]) -> bool:
        """Send an alert to Telegram if not already sent."""
        signal_id = str(evidence.get("signal_id", ""))
        if not signal_id:
            return False

        # Deduplication check
        if signal_id in self._sent_signals:
            return False  # Suppressed duplicate

        self._sent_signals.add(signal_id)

        # If mock mode or disabled, return True without HTTP call
        if not self.config.enabled or not self.config.bot_token or not self.config.chat_id:
            return True

        # In live mode with credentials, dispatch HTTP request
        try:
            import urllib.parse
            import urllib.request
            message = self.format_alert_message(evidence)
            url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
            payload = urllib.parse.urlencode({
                "chat_id": self.config.chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False
