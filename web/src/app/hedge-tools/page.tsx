"use client";

import { useState } from "react";
import { Shield, ArrowRightLeft, Calculator, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function HedgeToolsPage() {
  const [activeTab, setActiveTab] = useState<"converter" | "cheapest" | "sizer">("cheapest");
  const [targetGrams, setTargetGrams] = useState<number>(500);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-xl p-5 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-base font-bold text-ink">Physical Gold Hedge Tools & Sizing Calculators</h1>
          <p className="text-xs text-slate mt-0.5">
            Pre-trade analytics for cross-contract parity conversion, cheapest hedge contract selection, and lot ratios.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center space-x-1 bg-panel p-1 rounded-lg border border-gray-200 text-xs font-semibold">
          <button
            onClick={() => setActiveTab("cheapest")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "cheapest" ? "bg-gold text-white shadow-xs" : "text-slate hover:text-ink"
            }`}
          >
            Cheapest-to-Hedge (FR23)
          </button>
          <button
            onClick={() => setActiveTab("converter")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "converter" ? "bg-gold text-white shadow-xs" : "text-slate hover:text-ink"
            }`}
          >
            Parity Converter (FR22)
          </button>
          <button
            onClick={() => setActiveTab("sizer")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              activeTab === "sizer" ? "bg-gold text-white shadow-xs" : "text-slate hover:text-ink"
            }`}
          >
            Lot-Ratio Sizer (FR24)
          </button>
        </div>
      </div>

      {/* Main Tab Content */}
      {activeTab === "cheapest" && (
        <div className="space-y-6">
          {/* Target Input Card */}
          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-ink">Target Fine Gold to Hedge</label>
              <div className="flex items-center space-x-2">
                <input
                  type="number"
                  value={targetGrams}
                  onChange={(e) => setTargetGrams(Number(e.target.value))}
                  className="font-mono text-lg font-bold text-ink bg-panel border border-gray-200 rounded-lg px-3 py-1.5 w-36 focus:outline-none focus:ring-1 focus:ring-gold"
                />
                <span className="text-sm font-semibold text-slate">grams (999 purity)</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {[100, 250, 500, 1000].map((preset) => (
                <button
                  key={preset}
                  onClick={() => setTargetGrams(preset)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium border transition-colors ${
                    targetGrams === preset
                      ? "bg-gold-tint border-gold text-gold font-bold"
                      : "bg-panel border-gray-200 text-slate hover:bg-gray-100"
                  }`}
                >
                  {preset}g
                </button>
              ))}
            </div>
          </div>

          {/* Ranked Output Table */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden space-y-3 p-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-ink">
                  Ranked Cross-Contract Friction Comparison for {targetGrams}g Hedge
                </h3>
                <p className="text-xs text-slate mt-0.5">
                  Ranked from lowest to highest total transaction friction (round-trip costs + adverse slippage).
                </p>
              </div>
              <span className="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold">
                Optimal: GOLDM (₹22.40 / 10g)
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-panel text-slate border-b border-gray-200 font-sans text-[11px] uppercase font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">Rank & Contract</th>
                    <th className="py-2.5 px-3">Sizing</th>
                    <th className="py-2.5 px-3">Effective Gold</th>
                    <th className="py-2.5 px-3">Residual Delta</th>
                    <th className="py-2.5 px-3">Total Cost</th>
                    <th className="py-2.5 px-3">Cost / 10g</th>
                    <th className="py-2.5 px-3">Liquidity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr className="bg-emerald-50/30">
                    <td className="py-3 px-3 font-sans font-bold text-ink">
                      🥇 Rank 1: GOLDM (100g, 995)
                    </td>
                    <td className="py-3 px-3">5 Lots</td>
                    <td className="py-3 px-3">497.5g</td>
                    <td className="py-3 px-3 text-slate">-2.5g</td>
                    <td className="py-3 px-3 font-bold text-ink">₹1,120.00</td>
                    <td className="py-3 px-3 font-bold text-emerald-700">₹22.40</td>
                    <td className="py-3 px-3 font-sans">
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                        HIGH
                      </span>
                    </td>
                  </tr>

                  <tr>
                    <td className="py-3 px-3 font-sans font-bold text-ink">
                      🥈 Rank 2: GOLDTEN (10g, 999)
                    </td>
                    <td className="py-3 px-3">50 Lots</td>
                    <td className="py-3 px-3">500.0g</td>
                    <td className="py-3 px-3 text-emerald-700 font-bold">0.0g</td>
                    <td className="py-3 px-3 text-ink">₹1,480.00</td>
                    <td className="py-3 px-3 text-ink font-semibold">₹29.60</td>
                    <td className="py-3 px-3 font-sans">
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">
                        MODERATE
                      </span>
                    </td>
                  </tr>

                  <tr>
                    <td className="py-3 px-3 font-sans font-bold text-ink">
                      🥉 Rank 3: GOLDGUINEA (8g, 999)
                    </td>
                    <td className="py-3 px-3">62 Lots</td>
                    <td className="py-3 px-3">496.0g</td>
                    <td className="py-3 px-3 text-slate">-4.0g</td>
                    <td className="py-3 px-3 text-ink">₹1,820.00</td>
                    <td className="py-3 px-3 text-ink font-semibold">₹36.40</td>
                    <td className="py-3 px-3 font-sans">
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-50 text-amber-700">
                        LOW
                      </span>
                    </td>
                  </tr>

                  <tr className="bg-red-50/40">
                    <td className="py-3 px-3 font-sans font-bold text-alert">
                      ⚠️ Rank 4: GOLDPETAL (1g, 999)
                    </td>
                    <td className="py-3 px-3 text-alert font-bold">500 Lots</td>
                    <td className="py-3 px-3">500.0g</td>
                    <td className="py-3 px-3 text-slate">0.0g</td>
                    <td className="py-3 px-3 text-alert font-bold">₹10,400.00</td>
                    <td className="py-3 px-3 text-alert font-bold">₹208.00</td>
                    <td className="py-3 px-3 font-sans">
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-100 text-alert">
                        FLAT FEE DRAG
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Micro-lot flat fee warning callout */}
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
              <div>
                <strong>Broker Ticket Dominance Note (Design §6.9):</strong> GOLDPETAL (1g) requires 500 separate lots to hedge 500g. The flat ₹20/order broker fee causes a massive <strong>+828% friction surge</strong> compared to GOLDM.
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "converter" && (
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-ink">Contract Parity Converter (FR22)</h3>
          <p className="text-xs text-slate">
            Enter a quoted price in any contract to compute exact theoretical parity prices across all MCX gold contracts.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
            <div className="p-3.5 bg-panel rounded-lg border border-gray-200 space-y-1">
              <span className="text-[11px] font-bold text-ink">GOLDM (995, 10g)</span>
              <div className="font-mono text-base font-bold text-ink">₹1,20,000.00</div>
              <span className="text-[10px] text-slate-light">Input Benchmark</span>
            </div>
            <div className="p-3.5 bg-gold-tint/40 rounded-lg border border-gold-border space-y-1">
              <span className="text-[11px] font-bold text-ink">GOLDTEN (999, 10g)</span>
              <div className="font-mono text-base font-bold text-gold">₹1,20,482.41</div>
              <span className="text-[10px] text-emerald-700">+₹482.41 purity parity</span>
            </div>
            <div className="p-3.5 bg-panel rounded-lg border border-gray-200 space-y-1">
              <span className="text-[11px] font-bold text-ink">GOLDGUINEA (999, 8g)</span>
              <div className="font-mono text-base font-bold text-ink">₹96,385.93</div>
              <span className="text-[10px] text-slate-light">8g equivalent</span>
            </div>
            <div className="p-3.5 bg-panel rounded-lg border border-gray-200 space-y-1">
              <span className="text-[11px] font-bold text-ink">GOLDPETAL (999, 1g)</span>
              <div className="font-mono text-base font-bold text-ink">₹12,048.24</div>
              <span className="text-[10px] text-slate-light">1g equivalent</span>
            </div>
          </div>
        </div>
      )}

      {activeTab === "sizer" && (
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-ink">Lot-Ratio Sizer (FR24)</h3>
          <p className="text-xs text-slate">
            Computes integer lot combinations minimizing leftover unhedged fine grams.
          </p>
          <div className="p-4 bg-panel rounded-lg border border-gray-200 space-y-2 text-xs">
            <div className="font-mono text-ink">
              GOLDTEN (10g) vs GOLDGUINEA (8g) → <strong className="text-emerald-700">Ratio 4 : 5 (40.0g vs 40.0g)</strong>
            </div>
            <div className="text-slate font-sans">
              Residual fine gold = 0.0g. Zero directional gold exposure created.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
