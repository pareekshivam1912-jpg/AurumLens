"use client";

import { useState } from "react";
import {
  FlaskConical,
  ShieldAlert,
  TrendingUp,
  Clock,
  CheckCircle2,
  Check,
  XCircle,
  AlertTriangle,
} from "lucide-react";

export default function PaperTradingPage() {
  const [positionClosed, setPositionClosed] = useState(false);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-xl p-5 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-base font-bold text-ink">Paper Trading & Execution Simulator</h1>
          <p className="text-xs text-slate mt-0.5">
            Two-leg simulated order execution with adverse Corwin-Schultz slippage and itemized MCX transaction friction.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded bg-amber-50 text-amber-900 border border-amber-200 text-xs font-bold">
            Zero-Duplicate Guard: ACTIVE
          </span>
        </div>
      </div>

      {/* Safety Warning Banner */}
      <div className="bg-amber-50 border border-amber-200/90 rounded-xl p-4 flex items-center justify-between text-xs text-amber-900">
        <div className="flex items-center space-x-2.5">
          <ShieldAlert className="w-5 h-5 text-amber-700 shrink-0" />
          <span>
            <strong>SIMULATED PAPER EXECUTION — NO REAL BROKER ORDERS.</strong> Direct broker execution is strictly inhibited in MVP. All fills model adverse Bid-Ask spread impact.
          </span>
        </div>
        <span className="text-[11px] font-mono text-amber-800 shrink-0 font-medium">Gateway: 12ms simulated</span>
      </div>

      {/* 6 Performance Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Total Paper Capital</span>
          <span className="text-sm font-bold font-mono text-ink block mt-0.5">₹10,00,000</span>
          <span className="text-[10px] text-slate-light">₹8.05L free margin</span>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Realized P&L</span>
          <span className="text-sm font-bold font-mono text-emerald-600 block mt-0.5">+₹28,450</span>
          <span className="text-[10px] text-slate-light">+2.85% ROC</span>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Unrealized MTM</span>
          <span className="text-sm font-bold font-mono text-emerald-600 block mt-0.5">
            {positionClosed ? "₹0.00" : "+₹4,820"}
          </span>
          <span className="text-[10px] text-slate-light">{positionClosed ? "Closed" : "1 active pair"}</span>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Open Positions</span>
          <span className="text-sm font-bold font-mono text-ink block mt-0.5">
            {positionClosed ? "0 Open" : "1 Open"}
          </span>
          <span className="text-[10px] text-slate-light">Margin: ₹1,94,200</span>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Completed Trades</span>
          <span className="text-sm font-bold font-mono text-ink block mt-0.5">
            {positionClosed ? "9 Done" : "8 Done"}
          </span>
          <span className="text-[10px] text-slate-light">75% win rate</span>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Total Friction Paid</span>
          <span className="text-sm font-bold font-mono text-alert block mt-0.5">₹4,180</span>
          <span className="text-[10px] text-slate-light">Itemized costs</span>
        </div>
      </div>

      {/* Active Position Card */}
      {!positionClosed ? (
        <div className="bg-white rounded-xl p-5 border border-gold-border bg-gradient-to-br from-white via-white to-gold-tint/20 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <div className="flex items-center space-x-3">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                ACTIVE POSITION
              </span>
              <h2 className="text-sm font-bold text-ink">GOLDTEN — GOLDGUINEA</h2>
              <span className="text-xs font-mono text-slate">Origin: sig_20261001_01</span>
            </div>

            <button
              onClick={() => setPositionClosed(true)}
              className="px-3 py-1.5 rounded-lg bg-alert text-white hover:bg-red-700 text-xs font-semibold shadow-xs transition-colors"
            >
              Close Position (Simulated)
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            {/* Leg A */}
            <div className="p-3 bg-panel rounded-lg border border-gray-200 space-y-1">
              <div className="flex justify-between font-sans font-bold">
                <span className="text-ink">Leg A: SHORT 4 lots GOLDTEN (40g)</span>
                <span className="text-emerald-700">+₹2,800.00 MTM</span>
              </div>
              <div className="text-slate">Signal: ₹1,20,500 | Fill with slip: ₹1,20,470</div>
              <div className="text-slate">Current Mark: ₹1,20,400.00</div>
            </div>

            {/* Leg B */}
            <div className="p-3 bg-panel rounded-lg border border-gray-200 space-y-1">
              <div className="flex justify-between font-sans font-bold">
                <span className="text-ink">Leg B: LONG 5 lots GOLDGUINEA (40g)</span>
                <span className="text-emerald-700">+₹2,020.00 MTM</span>
              </div>
              <div className="text-slate">Signal: ₹96,400 | Fill with slip: ₹96,448</div>
              <div className="text-slate">Current Mark: ₹96,380.00</div>
            </div>
          </div>

          {/* Reversion Progress */}
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate font-medium">Reversion toward Rolling Mean:</span>
              <span className="font-mono font-bold text-gold">56.4% Converged (Target: 100%)</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div className="bg-gold h-full rounded-full" style={{ width: "56.4%" }} />
            </div>
            <div className="flex justify-between text-[11px] text-slate-light pt-0.5">
              <span>Days in Trade: 2 / 15 (Max holding)</span>
              <span>Tender Risk: 23 days to expiry (SAFE)</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-xs text-emerald-900 flex items-center justify-between">
          <span>
            ✓ Position closed successfully. Modeled net realized P&L <strong>+₹4,340.00</strong> credited to paper capital.
          </span>
          <button
            onClick={() => setPositionClosed(false)}
            className="text-xs font-semibold text-emerald-800 underline"
          >
            Reset
          </button>
        </div>
      )}

      {/* Closed Trades History Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden p-5 space-y-3">
        <h3 className="text-sm font-bold text-ink">Simulated Trades History (Audit Ledger)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-panel text-slate border-b border-gray-200 font-sans text-[11px] uppercase font-semibold">
              <tr>
                <th className="py-2 px-3">Trade ID</th>
                <th className="py-2 px-3">Pair</th>
                <th className="py-2 px-3">Holding</th>
                <th className="py-2 px-3">Exit Reason</th>
                <th className="py-2 px-3">Gross P&L</th>
                <th className="py-2 px-3">Friction</th>
                <th className="py-2 px-3">Net P&L</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <tr>
                <td className="py-2.5 px-3 font-bold text-ink">#SIM-2026-008</td>
                <td className="py-2.5 px-3 font-sans text-ink">GOLDTEN / GOLDM</td>
                <td className="py-2.5 px-3">3 days</td>
                <td className="py-2.5 px-3 font-sans">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    REVERSION
                  </span>
                </td>
                <td className="py-2.5 px-3 text-emerald-700">+₹14,200.00</td>
                <td className="py-2.5 px-3 text-slate">₹1,950.00</td>
                <td className="py-2.5 px-3 font-bold text-emerald-700">+₹12,250.00</td>
              </tr>

              <tr>
                <td className="py-2.5 px-3 font-bold text-ink">#SIM-2026-007</td>
                <td className="py-2.5 px-3 font-sans text-ink">GOLDM / GOLDGUINEA</td>
                <td className="py-2.5 px-3">6 days</td>
                <td className="py-2.5 px-3 font-sans">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    REVERSION
                  </span>
                </td>
                <td className="py-2.5 px-3 text-emerald-700">+₹9,800.00</td>
                <td className="py-2.5 px-3 text-slate">₹1,640.00</td>
                <td className="py-2.5 px-3 font-bold text-emerald-700">+₹8,160.00</td>
              </tr>

              <tr>
                <td className="py-2.5 px-3 font-bold text-ink">#SIM-2026-006</td>
                <td className="py-2.5 px-3 font-sans text-ink">GOLDTEN / GOLDPETAL</td>
                <td className="py-2.5 px-3">15 days</td>
                <td className="py-2.5 px-3 font-sans">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                    TIME_STOP
                  </span>
                </td>
                <td className="py-2.5 px-3 text-alert">-₹3,200.00</td>
                <td className="py-2.5 px-3 text-slate">₹1,450.00</td>
                <td className="py-2.5 px-3 font-bold text-alert">-₹4,650.00</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
