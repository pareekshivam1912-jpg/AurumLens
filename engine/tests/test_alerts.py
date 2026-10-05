"""Tests for Telegram alert adapter and deduplication."""

from aurumlens.alerts.telegram import TelegramAlertAdapter, TelegramConfig


def test_telegram_format_message():
    adapter = TelegramAlertAdapter()
    evidence = {
        "signal_id": "sig_20261001_01",
        "pair_name": "GOLDTEN_GOLDGUINEA",
        "zscore": 2.42,
        "net_expected_edge_inr": 310.0,
        "lots_a": 4,
        "lots_b": 5,
        "residual_fine_g": 0.0,
        "leg_a_symbol": "GOLDTEN",
        "leg_b_symbol": "GOLDGUINEA",
    }
    msg = adapter.format_alert_message(evidence)
    assert "sig_20261001_01" in msg
    assert "+2.42" in msg
    assert "+₹310.00" in msg
    assert "4 lots GOLDTEN : 5 lots GOLDGUINEA" in msg
    assert "Analytics only — not investment advice" in msg


def test_telegram_deduplication():
    # Adapter in mock mode
    adapter = TelegramAlertAdapter(TelegramConfig(enabled=False))
    evidence = {
        "signal_id": "sig_20261001_01",
        "pair_name": "GOLDTEN_GOLDGUINEA",
    }

    # First send succeeds
    assert adapter.send_alert(evidence) is True

    # Immediate second send on same signal_id is suppressed
    assert adapter.send_alert(evidence) is False
