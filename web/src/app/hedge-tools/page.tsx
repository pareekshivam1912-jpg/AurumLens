"use client";

import { useEffect, useState } from "react";
import { Shield, ArrowRightLeft, Calculator, AlertTriangle, CheckCircle2, RefreshCw } from "lucide-react";

interface HedgeOption {
  rank: number;
  symbol: string;
  trading_unit_g: number;
  purity: number;
  lots: number;
  effective_grams: number;
  residual_grams: number;
  total_cost_inr: number;
  cost_per_10g_inr: number;
  liquidity_tier: string;
}

const defaultHedgeOptions: HedgeOption[] = [
  { rank: 1, symbol: "GOLDM", trading_unit_g: 100, purity: 0.995, lots: 5, effective_grams: 498.0, residual_grams: -2.0, total_cost_inr: 1120.0, cost_per_10g_inr: 22.4, liquidity_tier: "HIGH" },
  { rank: 2, symbol: "GOLDTEN", trading_unit_g: 10, purity: 0.999, lots: 50, effective_grams: 500.0, residual_grams: 0.0, total_cost_inr: 1480.0, cost_per_10g_inr: 29.6, liquidity_tier: "MODERATE" },
  { rank: 3, symbol: "GOLDGUINEA", trading_unit_g: 8, purity: 0.999, lots: 62, effective_grams: 496.0, residual_grams: -4.0, total_cost_inr: 1820.0, cost_per_10g_inr: 36.4, liquidity_tier: "LOW" },
  { rank: 4, symbol: "GOLDPETAL", trading_unit_g: 1, purity: 0.999, lots: 500, effective_grams: 500.0, residual_grams: 0.0, total_cost_inr: 10400.0, cost_per_10g_inr: 208.0, liquidity_tier: "ILLIQUID" },
];

export default function HedgeToolsPage() {
  const [activeTab, setActiveTab] = useState<"converter" | "cheapest" | "sizer">("cheapest");
  const [targetGrams, setTargetGrams] = useState<number>(500);
  const [hedgeOptions, setHedgeOptions] = useState<HedgeOption[]>(defaultHedgeOptions);
  const [loadingHedge, setLoadingHedge] = useState<boolean>(false);

  // Converter state
  const [convertSource, setConvertSource] = useState<string>("GOLDM");
  const [convertPrice, setConvertPrice] = useState<number>(120000);
  const [convertResults, setConvertResults] = useState<{ [symbol: string]: number }>({
    GOLDM: 120000.0,
    GOLDTEN: 120482.41,
    GOLDGUINEA: 96385.93,
    GOLDPETAL: 12048.24,
  });
  const [normPrice, setNormPrice] = useState<number>(120482.41);

  // Sizer state
  const [sizerLegA, setSizerLegA] = useState<string>("GOLDTEN");
  const [sizerLegB, setSizerLegB] = useState<string>("GOLDGUINEA");
  const [sizerMaxLots, setSizerMaxLots] = useState<number>(20);
  const [sizerResult, setSizerResult] = useState<{
    lotsA: number;
    lotsB: number;
    gramsA: number;
    gramsB: number;
    residual: number;
  }>({
    lotsA: 4,
    lotsB: 5,
    gramsA: 40.0,
    gramsB: 40.0,
    residual: 0.0,
  });

  // Fetch Cheapest-to-Hedge from FastAPI
  useEffect(() => {
    let ignore = false;
    const fetchHedge = async () => {
      setLoadingHedge(true);
      try {
        const res = await fetch(`http://localhost:8000/v1/tools/hedge-cost?target_grams=${targetGrams}`);
        if (res.ok) {
          const data: HedgeOption[] = await res.json();
          if (!ignore) setHedgeOptions(data);
        }
      } catch (err) {
        // Local fallback when FastAPI is offline
      } finally {
        if (!ignore) setLoadingHedge(false);
      }
    };
    fetchHedge();
    return () => { ignore = true; };
  }, [targetGrams]);

  // Fetch Price Conversion from FastAPI
  useEffect(() => {
    let ignore = false;
    const symbols = ["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"];
    const fetchConversions = async () => {
      try {
        const newResults: { [symbol: string]: number } = {};
        for (const target of symbols) {
          const res = await fetch(
            `http://localhost:8000/v1/tools/convert?source_symbol=${convertSource}&price=${convertPrice}&target_symbol=${target}`
          );
          if (res.ok) {
            const data = await res.json();
            newResults[target] = data.target_price;
            if (data.normalized_price_per_10g_999) {
              setNormPrice(data.normalized_price_per_10g_999);
            }
          }
        }
        if (!ignore && Object.keys(newResults).length > 0) {
          setConvertResults(newResults);
        }
      } catch (e) {
        // Offline fallback
      }
    };
    fetchConversions();
    return () => { ignore = true; };
  }, [convertSource, convertPrice]);

  // Fetch Lot Sizer from FastAPI
  useEffect(() => {
    let ignore = false;
    const fetchSizer = async () => {
      try {
        const res = await fetch(
          `http://localhost:8000/v1/tools/lot-ratio?symbol_a=${sizerLegA}&symbol_b=${sizerLegB}&max_lots=${sizerMaxLots}`
        );
        if (res.ok) {
          const data = await res.json();
          if (!ignore) {
            setSizerResult({
              lotsA: data.lots_a,
              lotsB: data.lots_b,
              gramsA: data.grams_a,
              gramsB: data.grams_b,
              residual: data.residual_fine_g,
            });
          }
        }
      } catch (e) {
        // Offline fallback
      }
    };
    fetchSizer();
    return () => { ignore = true; };
  }, [sizerLegA, sizerLegB, sizerMaxLots]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-xl p-5 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-base font-bold text-ink">Physical Gold Hedge Tools & Sizing Calculators</h1>
          <p className="text-xs text-slate mt-0.5">
            Pre-trade analytics for cross-contract parity conversion, cheapest hedge contract selection, and lot ratios. Powered by FastAPI engine.
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
                  min={1}
                  max={50000}
                  value={targetGrams}
                  onChange={(e) => setTargetGrams(Math.max(1, Number(e.target.value)))}
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
              {hedgeOptions[0] && (
                <span className="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold">
                  Optimal: {hedgeOptions[0].symbol} (₹{hedgeOptions[0].cost_per_10g_inr.toFixed(2)} / 10g)
                </span>
              )}
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
                  {hedgeOptions.map((opt) => (
                    <tr
                      key={opt.symbol}
                      className={
                        opt.rank === 1
                          ? "bg-emerald-50/30"
                          : opt.symbol === "GOLDPETAL"
                          ? "bg-red-50/30"
                          : ""
                      }
                    >
                      <td className="py-3 px-3 font-sans font-bold text-ink">
                        {opt.rank === 1
                          ? "🥇 Rank 1: "
                          : opt.rank === 2
                          ? "🥈 Rank 2: "
                          : opt.rank === 3
                          ? "🥉 Rank 3: "
                          : "⚠️ Rank 4: "}
                        {opt.symbol} ({opt.trading_unit_g}g, {opt.purity})
                      </td>
                      <td className="py-3 px-3">{opt.lots} Lots</td>
                      <td className="py-3 px-3">{opt.effective_grams.toFixed(1)}g</td>
                      <td className={`py-3 px-3 ${opt.residual_grams === 0 ? "text-emerald-700 font-bold" : "text-slate"}`}>
                        {opt.residual_grams > 0 ? `+${opt.residual_grams.toFixed(1)}g` : `${opt.residual_grams.toFixed(1)}g`}
                      </td>
                      <td className={`py-3 px-3 font-bold ${opt.symbol === "GOLDPETAL" ? "text-alert" : "text-ink"}`}>
                        ₹{opt.total_cost_inr.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>
                      <td className={`py-3 px-3 font-bold ${opt.rank === 1 ? "text-emerald-700" : opt.symbol === "GOLDPETAL" ? "text-alert" : "text-ink"}`}>
                        ₹{opt.cost_per_10g_inr.toFixed(2)}
                      </td>
                      <td className="py-3 px-3 font-sans">
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            opt.liquidity_tier === "HIGH"
                              ? "bg-emerald-100 text-emerald-800"
                              : opt.liquidity_tier === "MODERATE"
                              ? "bg-blue-50 text-blue-700"
                              : opt.liquidity_tier === "LOW"
                              ? "bg-amber-50 text-amber-700"
                              : "bg-red-100 text-alert"
                          }`}
                        >
                          {opt.liquidity_tier}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Micro-lot flat fee warning callout */}
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
              <div>
                <strong>Broker Ticket Dominance Note (Design §6.9):</strong> GOLDPETAL (1g) requires micro-orders. The flat ₹20/order broker fee causes a massive friction surge compared to GOLDM or GOLDTEN.
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "converter" && (
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-ink">Contract Parity Converter (FR22)</h3>
              <p className="text-xs text-slate">
                Enter a quoted price in any contract to compute exact theoretical parity prices across all MCX gold contracts.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={convertSource}
                onChange={(e) => setConvertSource(e.target.value)}
                className="text-xs font-bold text-ink bg-panel border border-gray-200 rounded-lg px-2.5 py-1.5"
              >
                <option value="GOLDM">Source: GOLDM (10g, 995)</option>
                <option value="GOLDTEN">Source: GOLDTEN (10g, 999)</option>
                <option value="GOLDGUINEA">Source: GOLDGUINEA (8g, 999)</option>
                <option value="GOLDPETAL">Source: GOLDPETAL (1g, 999)</option>
              </select>
              <input
                type="number"
                value={convertPrice}
                onChange={(e) => setConvertPrice(Number(e.target.value))}
                className="font-mono text-xs font-bold text-ink bg-panel border border-gray-200 rounded-lg px-3 py-1.5 w-32"
              />
            </div>
          </div>

          <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs flex justify-between items-center">
            <span className="text-slate">Standard Normalized Price:</span>
            <span className="font-mono font-bold text-ink text-sm">
              ₹{normPrice.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / 10g (999 pure)
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
            {["GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"].map((sym) => {
              const priceVal = convertResults[sym] ?? 0;
              const isSource = sym === convertSource;
              return (
                <div
                  key={sym}
                  className={`p-3.5 rounded-lg border space-y-1 ${
                    isSource ? "bg-gold-tint/40 border-gold-border" : "bg-panel border-gray-200"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-ink">{sym}</span>
                    {isSource && (
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-gold text-white">INPUT</span>
                    )}
                  </div>
                  <div className="font-mono text-base font-bold text-ink">
                    ₹{priceVal.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <span className="text-[10px] text-slate-light">
                    {sym === "GOLDM" ? "10g (995)" : sym === "GOLDTEN" ? "10g (999)" : sym === "GOLDGUINEA" ? "8g (999)" : "1g (999)"}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {activeTab === "sizer" && (
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-ink">Lot-Ratio Sizer (FR24)</h3>
              <p className="text-xs text-slate">
                Computes integer lot combinations minimizing leftover unhedged fine grams.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={sizerLegA}
                onChange={(e) => setSizerLegA(e.target.value)}
                className="text-xs font-bold text-ink bg-panel border border-gray-200 rounded-lg px-2.5 py-1.5"
              >
                <option value="GOLDTEN">Leg A: GOLDTEN</option>
                <option value="GOLDM">Leg A: GOLDM</option>
                <option value="GOLDGUINEA">Leg A: GOLDGUINEA</option>
                <option value="GOLDPETAL">Leg A: GOLDPETAL</option>
              </select>
              <span className="text-xs text-slate font-bold">vs</span>
              <select
                value={sizerLegB}
                onChange={(e) => setSizerLegB(e.target.value)}
                className="text-xs font-bold text-ink bg-panel border border-gray-200 rounded-lg px-2.5 py-1.5"
              >
                <option value="GOLDGUINEA">Leg B: GOLDGUINEA</option>
                <option value="GOLDTEN">Leg B: GOLDTEN</option>
                <option value="GOLDM">Leg B: GOLDM</option>
                <option value="GOLDPETAL">Leg B: GOLDPETAL</option>
              </select>
            </div>
          </div>

          <div className="p-4 bg-panel rounded-lg border border-gray-200 space-y-3 text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-200 pb-2">
              <span className="font-sans text-ink font-semibold">Computed Optimal Lot Ratio:</span>
              <strong className="font-mono text-emerald-700 text-sm">
                {sizerLegA} ({sizerResult.lotsA} lots) : {sizerLegB} ({sizerResult.lotsB} lots)
              </strong>
            </div>
            <div className="grid grid-cols-2 gap-4 text-xs font-mono">
              <div>
                <span className="text-slate">Fine Gold Leg A:</span>
                <div className="font-bold text-ink text-sm">{sizerResult.gramsA.toFixed(1)}g</div>
              </div>
              <div>
                <span className="text-slate">Fine Gold Leg B:</span>
                <div className="font-bold text-ink text-sm">{sizerResult.gramsB.toFixed(1)}g</div>
              </div>
            </div>
            <div className="flex justify-between border-t border-gray-200 pt-2 font-semibold">
              <span className="text-ink">Residual Unhedged Fine Gold:</span>
              <span className="font-mono text-emerald-700">
                {sizerResult.residual.toFixed(2)}g {sizerResult.residual === 0 ? "(Exact Zero Delta)" : ""}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
