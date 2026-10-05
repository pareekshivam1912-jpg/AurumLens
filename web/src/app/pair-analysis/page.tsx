"use client";

import { useState } from "react";
import {
  GitCompare,
  Calendar,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Play,
  SkipForward,
  Info,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

interface GateRow {
  name: string;
  passed: boolean;
  value: string;
  threshold: string;
  margin: string;
  reasonCode: string;
}

const gates: GateRow[] = [
  { name: "SPEC_OK", passed: true, value: "VERIFIED_OFFICIAL", threshold: "Official Spec", margin: "Pass", reasonCode: "—" },
  { name: "DATA_QUALITY", passed: true, value: "Both OK (0 missing ticks)", threshold: "Not SUSPECT", margin: "Pass", reasonCode: "—" },
  { name: "EXPIRY_PAIR_VALID", passed: true, value: "5 days gap", threshold: "≤ 35 days", margin: "+30 days", reasonCode: "—" },
  { name: "HISTORY_SUFFICIENT", passed: true, value: "60 sessions", threshold: "≥ 30 sessions", margin: "+30 obs", reasonCode: "—" },
  { name: "Z_SCORE_THRESHOLD", passed: false, value: "1.67", threshold: "≥ 2.00", margin: "-0.33", reasonCode: "Z_BELOW_THRESHOLD" },
  { name: "LIQUIDITY_VOLUME_A", passed: true, value: "120 lots/day", threshold: "≥ 10 lots", margin: "+110 lots", reasonCode: "—" },
  { name: "LIQUIDITY_VOLUME_B", passed: true, value: "85 lots/day", threshold: "≥ 10 lots", margin: "+75 lots", reasonCode: "—" },
  { name: "LIQUIDITY_OI_A", passed: true, value: "450 open lots", threshold: "≥ 50 lots", margin: "+400 lots", reasonCode: "—" },
  { name: "LIQUIDITY_OI_B", passed: true, value: "320 open lots", threshold: "≥ 50 lots", margin: "+270 lots", reasonCode: "—" },
  { name: "EXPIRY_SAFETY", passed: true, value: "25 days to tender", threshold: "> 5 days", margin: "+20 days", reasonCode: "—" },
  { name: "COST_HURDLE", passed: true, value: "₹480.00 gross edge", threshold: "> ₹170.00 friction", margin: "+₹310.00", reasonCode: "—" },
  { name: "DUPLICATE_CHECK", passed: true, value: "None active", threshold: "1 max open per desk", margin: "Pass", reasonCode: "—" },
];

export default function PairAnalysisPage() {
  const [selectedPair, setSelectedPair] = useState("GOLDTEN-GOLDM");
  const [replayDate, setReplayDate] = useState("2026-10-01");

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Control Strip */}
      <div className="bg-white rounded-xl p-4 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <select
            value={selectedPair}
            onChange={(e) => setSelectedPair(e.target.value)}
            className="text-sm font-bold text-ink bg-panel border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-gold"
          >
            <option value="GOLDTEN-GOLDM">GOLDTEN vs GOLDM (Gap: 5 Days)</option>
            <option value="GOLDTEN-GOLDGUINEA">GOLDTEN vs GOLDGUINEA (Gap: 0 Days)</option>
            <option value="GOLDM-GOLDGUINEA">GOLDM vs GOLDGUINEA (Gap: 5 Days)</option>
            <option value="GOLDM-GOLDPETAL">GOLDM vs GOLDPETAL (Gap: 5 Days)</option>
          </select>

          <span className="px-3 py-1 rounded-full text-xs font-bold bg-quiet-bg text-quiet border border-quiet-border">
            STATUS: QUIET
          </span>
        </div>

        {/* Replay Date Picker (Design §7 / PRD §10) */}
        <div className="flex items-center space-x-2">
          <Calendar className="w-4 h-4 text-slate" />
          <span className="text-xs text-slate font-medium">Replay Date:</span>
          <input
            type="date"
            value={replayDate}
            onChange={(e) => setReplayDate(e.target.value)}
            className="text-xs font-mono bg-panel border border-gray-200 rounded px-2 py-1 text-ink focus:outline-none"
          />
          <button className="p-1.5 text-slate hover:text-gold hover:bg-panel rounded" title="Play Replay">
            <Play className="w-3.5 h-3.5" />
          </button>
          <button className="p-1.5 text-slate hover:text-gold hover:bg-panel rounded" title="Next Session">
            <SkipForward className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Contract Specs & Normalization Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Leg A */}
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-ink">Leg A: GOLDTEN</span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              31-Oct-2026
            </span>
          </div>
          <div className="text-xs text-slate">Quote: 10g • 999 Purity</div>
          <div className="text-base font-mono font-bold text-ink">₹1,20,500.00</div>
          <div className="text-[11px] text-slate font-mono">
            Normalized: <strong className="text-ink">₹1,20,500.00</strong> / 10g (999)
          </div>
        </div>

        {/* Leg B */}
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-ink">Leg B: GOLDM</span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              05-Nov-2026
            </span>
          </div>
          <div className="text-xs text-slate">Quote: 10g • 995 Purity</div>
          <div className="text-base font-mono font-bold text-ink">₹1,20,000.00</div>
          <div className="text-[11px] text-slate font-mono">
            Normalized: <strong className="text-ink">₹1,20,482.41</strong> / 10g (999)
          </div>
          <div className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded inline-block">
            ✓ Direction test passed (995 normalizes upward)
          </div>
        </div>

        {/* Carry & Spread */}
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-ink">Carry & Spread</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-gold-tint text-gold border border-gold-border">
              CURVE (6.50% a.y.)
            </span>
          </div>
          <div className="text-xs text-slate">Expiry Gap: 5 Calendar Days</div>
          <div className="text-sm font-mono font-bold text-ink">
            Adj Log Spread: +0.000966
          </div>
          <div className="text-[11px] text-slate font-mono">
            Raw Spread: +0.000146 • 5-day Carry Adj: +0.000820
          </div>
          <div className="text-[11px] font-mono text-ink font-semibold">
            Rolling Z-Score: <span className="text-amber-600">+1.67</span> (Hurdle ≥ 2.00)
          </div>
        </div>
      </div>

      {/* 11-Gate Waterfall Table (PRD R20 / Design §6.11) */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-ink flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-gold" />
              11-Gate Risk & Liquidity Waterfall Evaluator (R20)
            </h3>
            <p className="text-xs text-slate mt-0.5">
              Every gate is evaluated on every session. Status is ALERT only if all gates pass.
            </p>
          </div>
          <span className="text-xs font-bold px-2.5 py-1 rounded bg-amber-50 text-amber-800 border border-amber-200">
            Audit: 11 / 12 Passed (Blocked by Z-Score)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-panel text-slate border-b border-gray-200 text-[11px] uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-2.5 px-4">Gate</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Measured Value</th>
                <th className="py-2.5 px-3">Threshold</th>
                <th className="py-2.5 px-3">Margin</th>
                <th className="py-2.5 px-4">Reason Code / Note</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-mono">
              {gates.map((g) => (
                <tr key={g.name} className={g.passed ? "hover:bg-panel/40" : "bg-red-50/40"}>
                  <td className="py-2.5 px-4 font-sans font-bold text-ink">{g.name}</td>
                  <td className="py-2.5 px-3">
                    {g.passed ? (
                      <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> PASS
                      </span>
                    ) : (
                      <span className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded bg-red-100 text-red-800">
                        <XCircle className="w-3 h-3 mr-1" /> FAIL
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-3 text-ink font-medium">{g.value}</td>
                  <td className="py-2.5 px-3 text-slate">{g.threshold}</td>
                  <td className={`py-2.5 px-3 font-semibold ${g.passed ? "text-emerald-700" : "text-alert"}`}>
                    {g.margin}
                  </td>
                  <td className="py-2.5 px-4 font-sans text-slate text-[11px]">{g.reasonCode}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Itemized Cost Breakdown Table (Design §6.9) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-ink">Itemized Round-Trip Friction (Design §6.9)</h3>
          <p className="text-xs text-slate">
            Mandatory quant rules: CTT sell-only, Stamp buy-only, GST only on broker/exchange/SEBI fees.
          </p>

          <div className="divide-y divide-gray-100 text-xs font-mono">
            <div className="py-1.5 flex justify-between">
              <span className="text-slate">Brokerage (min flat ₹20 or 0.03%)</span>
              <span className="font-semibold text-ink">₹40.00</span>
            </div>
            <div className="py-1.5 flex justify-between">
              <span className="text-slate">Exchange Turnover (0.0021%)</span>
              <span className="font-semibold text-ink">₹50.50</span>
            </div>
            <div className="py-1.5 flex justify-between">
              <span className="text-slate">SEBI Turnover Fee (0.0001%)</span>
              <span className="font-semibold text-ink">₹2.40</span>
            </div>
            <div className="py-1.5 flex justify-between">
              <span className="text-slate">CTT (Sell-Side Only 0.01%)</span>
              <span className="font-semibold text-ink">₹24.00</span>
            </div>
            <div className="py-1.5 flex justify-between">
              <span className="text-slate">Stamp Duty (Buy-Side Only 0.002%)</span>
              <span className="font-semibold text-ink">₹4.80</span>
            </div>
            <div className="py-1.5 flex justify-between">
              <span className="text-slate">GST (18% on Brokerage + Exchange + SEBI)</span>
              <span className="font-semibold text-ink">₹16.72</span>
            </div>
            <div className="py-2 flex justify-between text-sm font-bold border-t-2 border-gray-200">
              <span className="font-sans text-ink">Total Round-Trip Cost</span>
              <span className="text-gold font-mono">₹138.42 (₹34.61 / 10g)</span>
            </div>
          </div>
        </div>

        {/* Integer Lot Sizing (Design §6.7) */}
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-ink">Integer Lot Sizing & Fine Gold Reconciliation</h3>
          <p className="text-xs text-slate">
            Sizer searches integer lots minimizing residual fine grams.
          </p>

          <div className="bg-panel rounded-lg p-3 border border-gray-200/80 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate">Leg A (GOLDTEN 10g):</span>
              <strong className="font-mono text-ink">4 Lots (40.0g)</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate">Leg B (GOLDGUINEA 8g):</span>
              <strong className="font-mono text-ink">5 Lots (40.0g)</strong>
            </div>
            <div className="flex justify-between border-t border-gray-200 pt-2 font-semibold">
              <span className="text-ink">Residual Unhedged Fine Gold:</span>
              <span className="font-mono text-emerald-700">0.0g (Exact Zero Delta)</span>
            </div>
          </div>

          <div className="text-xs text-slate-light italic">
            * Residual fine gold is tracked continuously and attributed separately in backtest ledger.
          </div>
        </div>
      </div>
    </div>
  );
}
