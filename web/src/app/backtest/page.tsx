"use client";

import {
  TrendingUp,
  ShieldAlert,
  Lock,
  BarChart3,
  Layers,
  ArrowDownRight,
  ArrowUpRight,
} from "lucide-react";

export default function BacktestPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="bg-white rounded-xl p-5 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-base font-bold text-ink">
            Walk-Forward Backtesting & Performance Attribution
          </h1>
          <p className="text-xs text-slate mt-0.5">
            Chronological folds with t+1 execution, adverse Corwin-Schultz slippage, and Deflated Sharpe Ratio.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-panel border border-gray-200 font-mono text-xs text-slate">
            Dataset: <strong className="text-ink">ds_20261001_v1</strong>
          </span>
          <span className="px-2.5 py-1 rounded bg-panel border border-gray-200 font-mono text-xs text-slate">
            Config: <strong className="text-ink">v0.4.0 (sha256: 4a9977a)</strong>
          </span>
        </div>
      </div>

      {/* KPI Ribbon (5 Tiles) */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <span className="text-[11px] text-slate font-medium block">Net Strategy P&L</span>
          <span className="text-lg font-bold font-mono text-emerald-600 block mt-1">+₹48,250.00</span>
          <span className="text-[10px] text-slate-light">After all costs & slippage</span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <span className="text-[11px] text-slate font-medium block">Sharpe Ratio</span>
          <span className="text-lg font-bold font-mono text-ink block mt-1">1.48</span>
          <span className="text-[10px] text-slate-light">Annualized (252 days)</span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-gold-border bg-gold-tint/40 shadow-sm">
          <span className="text-[11px] text-gold font-bold block">Deflated Sharpe (DSR)</span>
          <span className="text-lg font-bold font-mono text-ink block mt-1">0.8842</span>
          <span className="text-[10px] text-slate-light">N_trials = 12 evaluated</span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <span className="text-[11px] text-slate font-medium block">Hit Rate</span>
          <span className="text-lg font-bold font-mono text-ink block mt-1">68.2%</span>
          <span className="text-[10px] text-slate-light">15 of 22 winning trades</span>
        </div>

        <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm">
          <span className="text-[11px] text-slate font-medium block">Max Drawdown</span>
          <span className="text-lg font-bold font-mono text-alert block mt-1">₹8,400.00</span>
          <span className="text-[10px] text-slate-light">3.2% peak-to-trough</span>
        </div>
      </div>

      {/* Equity Curve & Baselines Visual */}
      <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-ink">Cumulative Equity Curve vs Two Baselines (FR21)</h2>
          <div className="flex items-center space-x-4 text-xs">
            <span className="flex items-center gap-1.5 font-medium">
              <span className="w-3 h-0.5 bg-gold" /> AurumLens Strategy (+₹48.2k)
            </span>
            <span className="flex items-center gap-1.5 text-slate">
              <span className="w-3 h-0.5 bg-gray-400 border-dashed" /> Always-Quiet (₹0)
            </span>
            <span className="flex items-center gap-1.5 text-slate">
              <span className="w-3 h-0.5 bg-red-400" /> Random Entry (-₹4.2k)
            </span>
          </div>
        </div>

        {/* SVG Equity Chart */}
        <div className="h-56 bg-panel/50 rounded-lg border border-gray-200 p-3 relative flex items-end">
          <svg className="w-full h-full" viewBox="0 0 800 200" preserveAspectRatio="none">
            {/* Zero Baseline */}
            <line x1="0" y1="140" x2="800" y2="140" stroke="#9CA3AF" strokeDasharray="4" strokeWidth="1" />
            {/* Random Baseline Envelope */}
            <path
              d="M0,140 Q200,145 400,155 T800,165 L800,175 Q600,165 400,160 T0,140 Z"
              fill="#FEE2E2"
              opacity="0.6"
            />
            {/* AurumLens Equity Curve */}
            <path
              d="M0,140 Q150,120 300,95 T600,60 T800,40"
              fill="none"
              stroke="#B7862C"
              strokeWidth="2.5"
            />
          </svg>
        </div>
      </div>

      {/* P&L Attribution & Folds */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Waterfall Breakdown */}
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-ink">P&L Attribution Waterfall (Design §6.15)</h3>
          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between items-center p-2 rounded bg-emerald-50 text-emerald-900 border border-emerald-200">
              <span className="font-sans font-medium">Gross Trading P&L</span>
              <strong className="text-emerald-700">+₹64,200.00</strong>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-gray-50 text-slate">
              <span className="font-sans">Itemized Exchange & Regulatory Costs</span>
              <strong className="text-alert">-₹11,150.00</strong>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-gray-50 text-slate">
              <span className="font-sans">Adverse Corwin-Schultz Slippage</span>
              <strong className="text-alert">-₹4,800.00</strong>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-gold-tint border border-gold-border font-bold">
              <span className="font-sans text-ink">Net Strategy Realized P&L</span>
              <strong className="text-gold">+₹48,250.00</strong>
            </div>
          </div>

          <div className="pt-2 border-t border-gray-100 flex justify-between text-xs text-slate">
            <span>Strategy Alpha: <strong className="text-ink">₹46,900.00</strong></span>
            <span>Residual Gold P&L: <strong className="text-ink">₹1,350.00</strong></span>
          </div>
        </div>

        {/* Untouched Holdout Card */}
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-ink flex items-center gap-1.5">
              <Lock className="w-4 h-4 text-gold" />
              Untouched Out-of-Sample Holdout
            </h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
              FROZEN: 2026-06-01
            </span>
          </div>

          <p className="text-xs text-slate">
            The final holdout period runs exactly once after methodology freeze, reported separately to prevent backtest overfitting.
          </p>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono bg-panel p-3 rounded-lg border border-gray-200">
            <div>
              <span className="text-[10px] text-slate block font-sans">Holdout Net P&L</span>
              <span className="font-bold text-emerald-600 text-sm">+₹8,820.00</span>
            </div>
            <div>
              <span className="text-[10px] text-slate block font-sans">Holdout Sharpe</span>
              <span className="font-bold text-ink text-sm">1.58</span>
            </div>
            <div>
              <span className="text-[10px] text-slate block font-sans">Trades Executed</span>
              <span className="font-bold text-ink text-sm">4 Trades (75% Win)</span>
            </div>
            <div>
              <span className="text-[10px] text-slate block font-sans">DSR Significance</span>
              <span className="font-bold text-emerald-700 text-sm">p = 0.012 (Pass)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
