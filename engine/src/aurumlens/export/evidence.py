"""Evidence Pack Exporter (FR27).

Generates complete evidence packs in CSV and standalone HTML formats
for any pair-day signal (ALERT or QUIET).
"""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List, Optional


def export_evidence_to_csv(evidence: Dict[str, Any]) -> str:
    """Export evidence record data to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Section", "Field", "Value"])

    # Identity
    writer.writerow(["Identity", "Signal ID", evidence.get("signal_id", "")])
    writer.writerow(["Identity", "Trade Date", str(evidence.get("trade_date", ""))])
    writer.writerow(["Identity", "Pair Name", evidence.get("pair_name", "")])
    writer.writerow(["Identity", "Status", evidence.get("status", "QUIET")])
    writer.writerow(["Identity", "Expiry Gap (Days)", evidence.get("expiry_gap_days", "")])

    # Prices
    writer.writerow(["Prices", "Quoted Price A", evidence.get("quoted_price_a", "")])
    writer.writerow(["Prices", "Quoted Price B", evidence.get("quoted_price_b", "")])
    writer.writerow(["Prices", "Normalized Price A (₹/10g 999)", evidence.get("normalized_price_a", "")])
    writer.writerow(["Prices", "Normalized Price B (₹/10g 999)", evidence.get("normalized_price_b", "")])

    # Spread and Score
    writer.writerow(["Spread", "Carry Rate", evidence.get("carry_rate", "")])
    writer.writerow(["Spread", "Carry Source", evidence.get("carry_source", "")])
    writer.writerow(["Spread", "Raw Log Spread", evidence.get("log_spread_raw", "")])
    writer.writerow(["Spread", "Adj Log Spread", evidence.get("log_spread_adj", "")])
    writer.writerow(["Spread", "Rolling Z-Score", evidence.get("zscore", "")])

    # Economics
    writer.writerow(["Economics", "Expected Convergence (INR)", evidence.get("expected_convergence_inr", "")])
    writer.writerow(["Economics", "Total Friction (INR)", evidence.get("total_costs_inr", "")])
    writer.writerow(["Economics", "Slippage Estimate (INR)", evidence.get("slippage_inr", "")])
    writer.writerow(["Economics", "Net Expected Edge (INR)", evidence.get("net_expected_edge_inr", "")])

    # Sizing
    writer.writerow(["Sizing", "Lots Leg A", evidence.get("lots_a", "")])
    writer.writerow(["Sizing", "Lots Leg B", evidence.get("lots_b", "")])
    writer.writerow(["Sizing", "Residual Fine Grams", evidence.get("residual_fine_g", "")])

    # Versioning
    writer.writerow(["Audit", "Config Version", evidence.get("config_version", "")])
    writer.writerow(["Audit", "Dataset Version", evidence.get("dataset_version", "")])

    return output.getvalue()


def export_evidence_to_html(evidence: Dict[str, Any]) -> str:
    """Export evidence record data to an institutional standalone HTML report."""
    signal_id = evidence.get("signal_id", "N/A")
    pair_name = evidence.get("pair_name", "GOLDTEN_GOLDM")
    status = evidence.get("status", "QUIET")
    trade_date = str(evidence.get("trade_date", "2026-10-01"))
    status_color = "#C62828" if status == "ALERT" else "#2E7D32"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>AurumLens Evidence Pack — {signal_id}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #FDFBF7; color: #1E1E1E; padding: 40px; margin: 0; }}
    .card {{ background: white; border: 1px solid #E5E7EB; border-radius: 8px; padding: 24px; max-width: 800px; margin: 0 auto; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
    .header {{ border-bottom: 2px solid #EAD7B2; padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
    .title {{ font-size: 20px; font-weight: 700; color: #1E1E1E; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 700; color: white; background: {status_color}; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 24px; }}
    .tile {{ background: #F7F5F0; padding: 12px; border-radius: 6px; border: 1px solid #E5E7EB; }}
    .tile-label {{ font-size: 11px; color: #4B5563; text-transform: uppercase; margin-bottom: 4px; }}
    .tile-val {{ font-family: monospace; font-size: 14px; font-weight: 700; color: #1E1E1E; }}
    .footer {{ margin-top: 32px; font-size: 11px; color: #4B5563; border-top: 1px solid #E5E7EB; padding-top: 12px; text-align: center; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div>
        <div class="title">AurumLens Evidence Audit Pack</div>
        <div style="font-size: 12px; color: #4B5563; margin-top: 4px;">Signal: {signal_id} • Date: {trade_date}</div>
      </div>
      <div><span class="badge">{status}</span></div>
    </div>

    <div class="grid">
      <div class="tile">
        <div class="tile-label">Pair Mandate</div>
        <div class="tile-val">{pair_name}</div>
      </div>
      <div class="tile">
        <div class="tile-label">Divergence Z-Score</div>
        <div class="tile-val">{evidence.get('zscore', 0.0)}</div>
      </div>
      <div class="tile">
        <div class="tile-label">Expected Gross Convergence</div>
        <div class="tile-val">₹{evidence.get('expected_convergence_inr', 0.0)}</div>
      </div>
      <div class="tile">
        <div class="tile-label">Net Realizable Edge</div>
        <div class="tile-val" style="color: #2E7D32;">₹{evidence.get('net_expected_edge_inr', 0.0)}</div>
      </div>
      <div class="tile">
        <div class="tile-label">Optimal Sizing Ratio</div>
        <div class="tile-val">{evidence.get('lots_a', 0)} lots A : {evidence.get('lots_b', 0)} lots B</div>
      </div>
      <div class="tile">
        <div class="tile-label">Residual Unhedged Gold</div>
        <div class="tile-val">{evidence.get('residual_fine_g', 0.0)} g</div>
      </div>
    </div>

    <div class="footer">
      <strong>Analytics only — not investment advice.</strong> AurumLens Relative-Value Engine v2.1 (sha256: 4a9977a)
    </div>
  </div>
</body>
</html>"""
    return html
