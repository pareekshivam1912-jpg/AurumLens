"use client";

import { BookOpen, ShieldCheck, ArrowRight, AlertTriangle, CheckCircle2, Lock } from "lucide-react";

export default function MethodologyPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-xl p-5 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-base font-bold text-ink">
            Methodology, Mathematical Architecture & Regulatory Bounds
          </h1>
          <p className="text-xs text-slate mt-0.5">
            Complete mathematical specification of quantitative models, risk gates, and regulatory boundaries governing AurumLens.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-panel border border-gray-200 font-mono text-xs text-slate">
            Version: <strong className="text-ink">v2.1</strong> (sha256: 4a9977a)
          </span>
        </div>
      </div>

      {/* 9-Stage Analytics DAG Pipeline */}
      <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-3">
        <h2 className="text-sm font-bold text-ink flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-gold" />
          End-to-End Deterministic Analytics Pipeline (DAG)
        </h2>
        <p className="text-xs text-slate">
          Every derived calculation is traceable back to an immutable raw Bhavcopy file hash.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs space-y-1">
            <span className="font-mono text-[10px] font-bold text-gold">STAGE 01</span>
            <div className="font-bold text-ink">Raw Ingestion</div>
            <p className="text-[11px] text-slate">Immutable Bhavcopy + SHA-256 seal.</p>
          </div>

          <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs space-y-1">
            <span className="font-mono text-[10px] font-bold text-gold">STAGE 02</span>
            <div className="font-bold text-ink">Price Quality (R19)</div>
            <p className="text-[11px] text-slate">Close/settle filter, discard SUSPECT data.</p>
          </div>

          <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs space-y-1">
            <span className="font-mono text-[10px] font-bold text-gold">STAGE 03</span>
            <div className="font-bold text-ink">Purity Normalization (R16)</div>
            <p className="text-[11px] text-slate">Standardize to ₹/10g of 999 fine gold.</p>
          </div>

          <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs space-y-1">
            <span className="font-mono text-[10px] font-bold text-gold">STAGE 04</span>
            <div className="font-bold text-ink">Smallest-Gap Matching (R17)</div>
            <p className="text-[11px] text-slate">Minimize absolute calendar expiry gap.</p>
          </div>

          <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs space-y-1">
            <span className="font-mono text-[10px] font-bold text-gold">STAGE 05</span>
            <div className="font-bold text-ink">Implied Carry (R18)</div>
            <p className="text-[11px] text-slate">Curve carry first; fallback rate second.</p>
          </div>

          <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs space-y-1">
            <span className="font-mono text-[10px] font-bold text-gold">STAGE 06</span>
            <div className="font-bold text-ink">Spread & Z-Score (R21)</div>
            <p className="text-[11px] text-slate">Rolling mean through t-1 (no look-ahead).</p>
          </div>

          <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs space-y-1">
            <span className="font-mono text-[10px] font-bold text-gold">STAGE 07</span>
            <div className="font-bold text-ink">11-Gate Evaluator (R20)</div>
            <p className="text-[11px] text-slate">All gates evaluated, margins stored.</p>
          </div>

          <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs space-y-1">
            <span className="font-mono text-[10px] font-bold text-gold">STAGE 08</span>
            <div className="font-bold text-ink">Decision & Nearest Miss (FR17)</div>
            <p className="text-[11px] text-slate">Default QUIET, rank closest pair.</p>
          </div>

          <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs space-y-1">
            <span className="font-mono text-[10px] font-bold text-gold">STAGE 09</span>
            <div className="font-bold text-ink">Evidence Pack & Paper Execution</div>
            <p className="text-[11px] text-slate">Simulated t+1 fill with slippage.</p>
          </div>
        </div>
      </div>

      {/* Core Mathematical Formulations */}
      <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-ink">Key Mathematical Formulations (Design §6)</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-panel rounded-lg border border-gray-200 space-y-1.5 text-xs">
            <div className="font-bold text-ink">1. Purity Normalization (R16)</div>
            <div className="font-mono bg-white p-2 rounded border border-gray-200 text-slate">
              P_norm = P_used × (10 / quote_basis_g) × (0.999 / purity)
            </div>
            <p className="text-[11px] text-slate">
              Lower purity normalizes <strong>upward</strong>. (e.g. 995 GOLDM normalizes by ×1.00402).
            </p>
          </div>

          <div className="p-4 bg-panel rounded-lg border border-gray-200 space-y-1.5 text-xs">
            <div className="font-bold text-ink">2. Adjusted Log Spread & Z-Score (R21)</div>
            <div className="font-mono bg-white p-2 rounded border border-gray-200 text-slate">
              s_t = ln(P_norm_A) - ln(P_norm_B) + carry_adj
              <br />
              z_t = (s_t - μ_(t-1)) / σ_(t-1)
            </div>
            <p className="text-[11px] text-slate">
              Convergence is measured to the <strong>rolling mean</strong>, not zero. Structural premiums do not trigger false alerts.
            </p>
          </div>

          <div className="p-4 bg-panel rounded-lg border border-gray-200 space-y-1.5 text-xs">
            <div className="font-bold text-ink">3. Corwin-Schultz (2012) Spread Estimator</div>
            <div className="font-mono bg-white p-2 rounded border border-gray-200 text-slate">
              S = 2(e^α - 1) / (1 + e^α)
            </div>
            <p className="text-[11px] text-slate">
              Derived from consecutive daily high-low ranges. Hand fixture S ≈ 0.000424 verified.
            </p>
          </div>

          <div className="p-4 bg-panel rounded-lg border border-gray-200 space-y-1.5 text-xs">
            <div className="font-bold text-ink">4. Deflated Sharpe Ratio (DSR)</div>
            <div className="font-mono bg-white p-2 rounded border border-gray-200 text-slate">
              DSR = Φ( (SR - SR*) / √V_SR )
            </div>
            <p className="text-[11px] text-slate">
              Penalizes selection bias across all backtested configs. Reported, never optimized (R15).
            </p>
          </div>
        </div>
      </div>

      {/* Product Boundaries (PRD §4 / AGENTS.md) */}
      <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-3 text-xs">
        <h2 className="text-sm font-bold text-ink flex items-center gap-1.5">
          <Lock className="w-4 h-4 text-gold" />
          Product Boundaries & Invariants
        </h2>
        <ul className="space-y-1.5 text-slate list-disc list-inside">
          <li><strong>No Directional Forecasting:</strong> AurumLens does NOT predict gold price direction (pure relative-value arbitrage).</li>
          <li><strong>Zero Real-Money Execution:</strong> Direct broker execution is strictly inhibited in MVP. Paper execution only.</li>
          <li><strong>Pure Presentation Layer:</strong> Zero mathematical formulas in client JavaScript or SQL views. All analytics in Python pure functions.</li>
          <li><strong>Quiet by Default:</strong> If any single gate fails or data is missing, output is strictly QUIET.</li>
        </ul>
      </div>
    </div>
  );
}
