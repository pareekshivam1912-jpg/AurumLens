"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  createChart,
  ColorType,
  IChartApi,
  ISeriesApi,
  LineStyle,
  LineSeries,
  AreaSeries,
} from "lightweight-charts";
import {
  TrendingUp,
  Sliders,
  Layers,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Info,
  Maximize2,
  RefreshCw,
} from "lucide-react";

export type ChartMode = "normalized" | "raw";
export type ViewTab = "prices" | "spread" | "zscore";
export type Timeframe = "1W" | "1M" | "3M" | "6M" | "1Y" | "ALL";

interface PointData {
  time: string;
  raw_a: number;
  raw_b: number;
  norm_a: number;
  norm_b: number;
  raw_diff: number;
  norm_diff: number;
  log_spread_raw: number;
  carry_adj: number;
  log_spread_adj: number;
  roll_mean: number | null;
  roll_upper: number | null;
  roll_lower: number | null;
  roll_std: number | null;
  zscore: number | null;
  rich_leg: string | null;
  status: "ALERT" | "QUIET" | "WARMUP";
  is_alert: boolean;
}

interface PairApiResponse {
  pair_name: string;
  leg_a_symbol: string;
  leg_b_symbol: string;
  data_status: string;
  synthetic: boolean;
  summary: {
    latest_date: string | null;
    latest_zscore: number | null;
    latest_norm_diff: number | null;
    latest_log_spread_adj: number | null;
    rich_leg: string | null;
    status: string;
    has_active_alert: boolean;
  };
  points_count: number;
  points: PointData[];
}

interface InteractiveChartProps {
  initialPair?: string;
  onSelectDate?: (date: string) => void;
  className?: string;
}

export default function InteractiveChart({
  initialPair = "GOLDTEN_GOLDGUINEA",
  onSelectDate,
  className = "",
}: InteractiveChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<IChartApi | null>(null);

  // Controls state
  const [selectedPair, setSelectedPair] = useState<string>(initialPair);
  const [chartMode, setChartMode] = useState<ChartMode>("normalized");
  const [viewTab, setViewTab] = useState<ViewTab>("prices");
  const [timeframe, setTimeframe] = useState<Timeframe>("ALL");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [dataPayload, setDataPayload] = useState<PairApiResponse | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<PointData | null>(null);

  // Fetch chart data from API with fallback
  useEffect(() => {
    let isCancelled = false;
    setIsLoading(true);

    async function loadData() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(
          `${apiUrl}/v1/chart/pair/${selectedPair}?range=${timeframe}&lookback=60&min_history=30`
        );
        if (!res.ok) throw new Error("API returned status " + res.status);
        const json: PairApiResponse = await res.json();
        if (!isCancelled) {
          setDataPayload(json);
          setIsLoading(false);
        }
      } catch (err) {
        // Deterministic fallback dataset matching Design §6.3 fixtures
        if (!isCancelled) {
          const fallbackData = generateFallbackSeries(selectedPair, timeframe);
          setDataPayload(fallbackData);
          setIsLoading(false);
        }
      }
    }

    loadData();
    return () => {
      isCancelled = true;
    };
  }, [selectedPair, timeframe]);

  // Build and update Lightweight Chart
  useEffect(() => {
    if (!chartContainerRef.current || !dataPayload || dataPayload.points.length === 0) {
      return;
    }

    // Clean up previous instance
    if (chartInstanceRef.current) {
      chartInstanceRef.current.remove();
      chartInstanceRef.current = null;
    }

    const container = chartContainerRef.current;
    const width = container.clientWidth || 800;
    const height = 380;

    const chart = createChart(container, {
      width,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "#0B0E14" },
        textColor: "#94A3B8",
        fontSize: 12,
        fontFamily: "Inter, -apple-system, sans-serif",
      },
      grid: {
        vertLines: { color: "#1E293B", style: LineStyle.Dotted },
        horzLines: { color: "#1E293B", style: LineStyle.Dotted },
      },
      crosshair: {
        vertLine: { color: "#64748B", width: 1, style: LineStyle.Dashed },
        horzLine: { color: "#64748B", width: 1, style: LineStyle.Dashed },
      },
      rightPriceScale: {
        borderColor: "#1E293B",
        autoScale: true,
      },
      timeScale: {
        borderColor: "#1E293B",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartInstanceRef.current = chart;

    const points = dataPayload.points;

    // View: Dual Prices Overlay
    if (viewTab === "prices") {
      const legASeries = chart.addSeries(LineSeries, {
        color: "#F59E0B", // Amber Gold
        lineWidth: 2,
        title: `${dataPayload.leg_a_symbol} (${chartMode === "normalized" ? "₹/10g 999" : "Quoted"})`,
      });

      const legBSeries = chart.addSeries(LineSeries, {
        color: "#06B6D4", // Cyan
        lineWidth: 2,
        title: `${dataPayload.leg_b_symbol} (${chartMode === "normalized" ? "₹/10g 999" : "Quoted"})`,
      });

      const dataA = points.map((p) => ({
        time: p.time,
        value: chartMode === "normalized" ? p.norm_a : p.raw_a,
      }));

      const dataB = points.map((p) => ({
        time: p.time,
        value: chartMode === "normalized" ? p.norm_b : p.raw_b,
      }));

      legASeries.setData(dataA);
      legBSeries.setData(dataB);
    }
    // View: Cross-Contract Log Spread & Rolling Bollinger Bands
    else if (viewTab === "spread") {
      const spreadSeries = chart.addSeries(LineSeries, {
        color: "#38BDF8", // Sky blue
        lineWidth: 2,
        title: "Adjusted Spread s_t",
      });

      const meanSeries = chart.addSeries(LineSeries, {
        color: "#94A3B8", // Neutral slate
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        title: "Rolling Mean μ_{t-1}",
      });

      const upperBand = chart.addSeries(LineSeries, {
        color: "#F43F5E", // Rose red
        lineWidth: 1,
        lineStyle: LineStyle.Dotted,
        title: "+2σ Band",
      });

      const lowerBand = chart.addSeries(LineSeries, {
        color: "#10B981", // Emerald green
        lineWidth: 1,
        lineStyle: LineStyle.Dotted,
        title: "-2σ Band",
      });

      spreadSeries.setData(
        points.map((p) => ({ time: p.time, value: p.log_spread_adj }))
      );

      const meanData = points
        .filter((p) => p.roll_mean !== null)
        .map((p) => ({ time: p.time, value: p.roll_mean! }));
      meanSeries.setData(meanData);

      const upperData = points
        .filter((p) => p.roll_upper !== null)
        .map((p) => ({ time: p.time, value: p.roll_upper! }));
      upperBand.setData(upperData);

      const lowerData = points
        .filter((p) => p.roll_lower !== null)
        .map((p) => ({ time: p.time, value: p.roll_lower! }));
      lowerBand.setData(lowerData);
    }
    // View: Z-Score Oscillator with Entry Hurdles
    else if (viewTab === "zscore") {
      const zSeries = chart.addSeries(LineSeries, {
        color: "#A855F7", // Purple
        lineWidth: 2,
        title: "Z-Score (t-1)",
      });

      const upperHurdle = chart.addSeries(LineSeries, {
        color: "#E11D48",
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        title: "+2.0 Entry Hurdle",
      });

      const lowerHurdle = chart.addSeries(LineSeries, {
        color: "#059669",
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        title: "-2.0 Entry Hurdle",
      });

      const zeroLine = chart.addSeries(LineSeries, {
        color: "#64748B",
        lineWidth: 1,
        lineStyle: LineStyle.Solid,
        title: "Equilibrium (0.0)",
      });

      const zData = points
        .filter((p) => p.zscore !== null)
        .map((p) => ({ time: p.time, value: p.zscore! }));
      zSeries.setData(zData);

      upperHurdle.setData(points.map((p) => ({ time: p.time, value: 2.0 })));
      lowerHurdle.setData(points.map((p) => ({ time: p.time, value: -2.0 })));
      zeroLine.setData(points.map((p) => ({ time: p.time, value: 0.0 })));
    }

    chart.timeScale().fitContent();

    // Subscribe to crosshair move
    chart.subscribeCrosshairMove((param) => {
      if (!param || !param.time) {
        setHoveredPoint(null);
        return;
      }
      const timeStr = param.time.toString();
      const pt = points.find((p) => p.time === timeStr);
      if (pt) {
        setHoveredPoint(pt);
        if (onSelectDate) onSelectDate(pt.time);
      }
    });

    // Handle container resize
    const handleResize = () => {
      if (chartContainerRef.current && chartInstanceRef.current) {
        chartInstanceRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (chartInstanceRef.current) {
        chartInstanceRef.current.remove();
        chartInstanceRef.current = null;
      }
    };
  }, [dataPayload, chartMode, viewTab, onSelectDate]);

  const activePoint = hoveredPoint || (dataPayload && dataPayload.points.length > 0 ? dataPayload.points[dataPayload.points.length - 1] : null);

  return (
    <div className={`bg-[#0F141C] border border-slate-800 rounded-xl overflow-hidden shadow-2xl ${className}`}>
      {/* Top Controls Header */}
      <div className="px-5 py-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4 bg-slate-900/60">
        <div className="flex flex-wrap items-center gap-3">
          {/* Pair Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Pair:</span>
            <select
              value={selectedPair}
              onChange={(e) => setSelectedPair(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-amber-400 font-mono text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-amber-500"
            >
              <option value="GOLDTEN_GOLDGUINEA">GOLDTEN — GOLDGUINEA</option>
              <option value="GOLDM_GOLDTEN">GOLDM — GOLDTEN</option>
              <option value="GOLDM_GOLDGUINEA">GOLDM — GOLDGUINEA</option>
              <option value="GOLDM_GOLDPETAL">GOLDM — GOLDPETAL</option>
              <option value="GOLDTEN_GOLDPETAL">GOLDTEN — GOLDPETAL</option>
            </select>
          </div>

          {/* View Tab Selector */}
          <div className="inline-flex rounded-lg bg-slate-800/80 p-0.5 border border-slate-700/80">
            <button
              onClick={() => setViewTab("prices")}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                viewTab === "prices"
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Dual Prices
            </button>
            <button
              onClick={() => setViewTab("spread")}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                viewTab === "spread"
                  ? "bg-sky-500/20 text-sky-300 border border-sky-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Spread & Bands
            </button>
            <button
              onClick={() => setViewTab("zscore")}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                viewTab === "zscore"
                  ? "bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Z-Score Oscillator
            </button>
          </div>

          {/* Dual-Mode Parity Toggle (only shown on Prices view) */}
          {viewTab === "prices" && (
            <div className="inline-flex rounded-lg bg-slate-800/80 p-0.5 border border-slate-700/80">
              <button
                onClick={() => setChartMode("normalized")}
                title="Normalize to standard Rs per 10g of 999 fine gold (Rule R16)"
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                  chartMode === "normalized"
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                ₹/10g 999 Parity
              </button>
              <button
                onClick={() => setChartMode("raw")}
                title="Quoted MCX contract prices"
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                  chartMode === "raw"
                    ? "bg-blue-500/20 text-blue-400 border border-blue-500/40"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Raw MCX Quoted
              </button>
            </div>
          )}
        </div>

        {/* Timeframe Selector & Audit Status */}
        <div className="flex items-center gap-3">
          <div className="inline-flex rounded-lg bg-slate-800/80 p-0.5 border border-slate-700/80 text-xs">
            {(["1W", "1M", "3M", "6M", "1Y", "ALL"] as Timeframe[]).map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2.5 py-1 font-mono rounded-md transition-all ${
                  timeframe === tf
                    ? "bg-slate-700 text-white font-semibold"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* Data Quality Badge */}
          {dataPayload && (
            <div
              className={`px-2.5 py-1 rounded-full text-[11px] font-mono flex items-center gap-1.5 border ${
                dataPayload.data_status === "VERIFIED_REAL"
                  ? "bg-emerald-950/60 text-emerald-400 border-emerald-800/80"
                  : "bg-amber-950/60 text-amber-400 border-amber-800/80"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  dataPayload.data_status === "VERIFIED_REAL"
                    ? "bg-emerald-400 animate-pulse"
                    : "bg-amber-400"
                }`}
              />
              {dataPayload.data_status === "VERIFIED_REAL"
                ? "REAL BHAVCOPY"
                : "CALIBRATED FIXTURE"}
            </div>
          )}
        </div>
      </div>

      {/* Synchronized Inspection Strip (HUD) */}
      {activePoint && (
        <div className="px-5 py-2.5 bg-slate-900/40 border-b border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3 text-xs font-mono">
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Trade Date</span>
            <span className="text-slate-200 font-semibold">{activePoint.time}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">
              {dataPayload?.leg_a_symbol || "Leg A"} ({chartMode === "normalized" ? "Norm" : "Raw"})
            </span>
            <span className="text-amber-400 font-semibold">
              ₹{chartMode === "normalized" ? activePoint.norm_a.toLocaleString("en-IN") : activePoint.raw_a.toLocaleString("en-IN")}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">
              {dataPayload?.leg_b_symbol || "Leg B"} ({chartMode === "normalized" ? "Norm" : "Raw"})
            </span>
            <span className="text-cyan-400 font-semibold">
              ₹{chartMode === "normalized" ? activePoint.norm_b.toLocaleString("en-IN") : activePoint.raw_b.toLocaleString("en-IN")}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Norm Gap (₹/10g)</span>
            <span className={activePoint.norm_diff >= 0 ? "text-emerald-400" : "text-rose-400"}>
              {activePoint.norm_diff >= 0 ? "+" : ""}
              ₹{activePoint.norm_diff.toFixed(2)}
            </span>
          </div>
          <div>
            <span className="text-slate-500 block text-[10px] uppercase">Spread s_t (bps)</span>
            <span className="text-sky-300">
              {(activePoint.log_spread_adj * 10000).toFixed(1)} bp
            </span>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <span className="text-slate-500 block text-[10px] uppercase">Z-Score (t-1)</span>
              <span
                className={`font-bold ${
                  activePoint.zscore !== null && Math.abs(activePoint.zscore) >= 2.0
                    ? "text-rose-400 animate-pulse"
                    : "text-purple-300"
                }`}
              >
                {activePoint.zscore !== null ? (activePoint.zscore >= 0 ? `+${activePoint.zscore.toFixed(2)}` : activePoint.zscore.toFixed(2)) : "WARMUP"}
              </span>
            </div>
            {activePoint.status === "ALERT" ? (
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 font-sans text-[10px] font-bold">
                ALERT
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-sans text-[10px]">
                QUIET
              </span>
            )}
          </div>
        </div>
      )}

      {/* Chart Canvas Container */}
      <div className="relative p-2 min-h-[380px] bg-[#0B0E14]">
        {isLoading && (
          <div className="absolute inset-0 bg-[#0B0E14]/80 backdrop-blur-sm flex flex-col items-center justify-center z-10">
            <RefreshCw className="w-6 h-6 text-amber-500 animate-spin mb-2" />
            <span className="text-xs text-slate-400 font-mono">Loading relative-value series...</span>
          </div>
        )}
        <div ref={chartContainerRef} className="w-full h-[380px]" />
      </div>

      {/* Bottom Quantitative Legend & Footnote */}
      <div className="px-5 py-3 border-t border-slate-800/80 bg-slate-900/40 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
            Leg A: <strong className="text-slate-300">{dataPayload?.leg_a_symbol || "Leg A"}</strong>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 inline-block" />
            Leg B: <strong className="text-slate-300">{dataPayload?.leg_b_symbol || "Leg B"}</strong>
          </span>
          {viewTab === "spread" && (
            <span className="flex items-center gap-1.5 text-purple-400">
              <span className="w-3 h-0.5 bg-purple-400 inline-block" />
              Rolling ±2σ Bollinger Bounds (t-1)
            </span>
          )}
          {viewTab === "zscore" && (
            <span className="flex items-center gap-1.5 text-rose-400">
              <span className="w-3 h-0.5 bg-rose-500 inline-block" />
              ±2.0 Entry Hurdle
            </span>
          )}
        </div>
        <div className="text-[11px] text-slate-500">
          Analytics only — not investment advice. Pure quant functions calculate all series strictly through t-1.
        </div>
      </div>
    </div>
  );
}

// Deterministic fallback generator for offline scenarios and client preview
function generateFallbackSeries(pair: string, timeframe: string): PairApiResponse {
  const parts = pair.split("_");
  const symA = parts[0] || "GOLDTEN";
  const symB = parts[1] || "GOLDGUINEA";

  const points: PointData[] = [];
  const baseSpot = 120500.0;
  const factorA = symA === "GOLDGUINEA" ? 0.8 : symA === "GOLDPETAL" ? 0.1 : 1.0;
  const factorB = symB === "GOLDGUINEA" ? 0.8 : symB === "GOLDPETAL" ? 0.1 : 1.0;

  const count = timeframe === "1W" ? 7 : timeframe === "1M" ? 22 : timeframe === "3M" ? 65 : 80;
  const startDate = new Date(2026, 6, 1);

  for (let i = 0; i < count; i++) {
    const cur = new Date(startDate);
    cur.setDate(startDate.getDate() + i);
    if (cur.getDay() === 0 || cur.getDay() === 6) continue;

    const timeStr = cur.toISOString().split("T")[0];
    const cycle = Math.sin(i * 0.12) * 0.0006;
    const spike = i >= count - 10 && i <= count - 6 ? 0.0014 : 0.0;
    const logSpreadAdj = 0.0002 + cycle + spike;

    const normA = baseSpot * (1.0 + logSpreadAdj / 2.0);
    const normB = baseSpot * (1.0 - logSpreadAdj / 2.0);

    const rawA = normA * factorA;
    const rawB = normB * factorB;

    const zscore = i < 30 ? null : (logSpreadAdj - 0.0002) / 0.00045;
    const isAlert = zscore !== null && Math.abs(zscore) >= 2.0;

    points.push({
      time: timeStr,
      raw_a: Math.round(rawA * 100) / 100,
      raw_b: Math.round(rawB * 100) / 100,
      norm_a: Math.round(normA * 100) / 100,
      norm_b: Math.round(normB * 100) / 100,
      raw_diff: Math.round((rawA - rawB) * 100) / 100,
      norm_diff: Math.round((normA - normB) * 100) / 100,
      log_spread_raw: Math.round((logSpreadAdj - 0.00082) * 1000000) / 1000000,
      carry_adj: 0.00082,
      log_spread_adj: Math.round(logSpreadAdj * 1000000) / 1000000,
      roll_mean: i < 30 ? null : 0.0002,
      roll_upper: i < 30 ? null : 0.0002 + 2 * 0.00045,
      roll_lower: i < 30 ? null : 0.0002 - 2 * 0.00045,
      roll_std: i < 30 ? null : 0.00045,
      zscore: zscore !== null ? Math.round(zscore * 100) / 100 : null,
      rich_leg: logSpreadAdj > 0.0002 ? "A" : "B",
      status: isAlert ? "ALERT" : i < 30 ? "WARMUP" : "QUIET",
      is_alert: isAlert,
    });
  }

  const latest = points[points.length - 1];

  return {
    pair_name: `${symA}_${symB}`,
    leg_a_symbol: symA,
    leg_b_symbol: symB,
    data_status: "CALIBRATED_FIXTURE",
    synthetic: true,
    summary: {
      latest_date: latest.time,
      latest_zscore: latest.zscore,
      latest_norm_diff: latest.norm_diff,
      latest_log_spread_adj: latest.log_spread_adj,
      rich_leg: latest.rich_leg,
      status: latest.status,
      has_active_alert: points.some((p) => p.is_alert),
    },
    points_count: points.length,
    points,
  };
}
