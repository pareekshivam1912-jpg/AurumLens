"""Tests for evidence pack export in CSV and HTML (FR27)."""

from aurumlens.export.evidence import export_evidence_to_csv, export_evidence_to_html


def test_evidence_export_to_csv():
    data = {
        "signal_id": "sig_20261001_01",
        "trade_date": "2026-10-01",
        "pair_name": "GOLDTEN_GOLDGUINEA",
        "status": "ALERT",
        "zscore": 2.42,
        "expected_convergence_inr": 580.0,
        "net_expected_edge_inr": 310.0,
        "lots_a": 4,
        "lots_b": 5,
        "residual_fine_g": 0.0,
        "config_version": "v0.4.0",
        "dataset_version": "ds_20261001_v1",
    }
    csv_str = export_evidence_to_csv(data)
    assert "sig_20261001_01" in csv_str
    assert "GOLDTEN_GOLDGUINEA" in csv_str
    assert "ALERT" in csv_str
    assert "310.0" in csv_str
    assert "Section,Field,Value" in csv_str


def test_evidence_export_to_html():
    data = {
        "signal_id": "sig_20261001_01",
        "trade_date": "2026-10-01",
        "pair_name": "GOLDTEN_GOLDGUINEA",
        "status": "ALERT",
        "zscore": 2.42,
        "expected_convergence_inr": 580.0,
        "net_expected_edge_inr": 310.0,
        "lots_a": 4,
        "lots_b": 5,
        "residual_fine_g": 0.0,
    }
    html_str = export_evidence_to_html(data)
    assert "<!DOCTYPE html>" in html_str
    assert "sig_20261001_01" in html_str
    assert "ALERT" in html_str
    assert "Analytics only — not investment advice" in html_str
