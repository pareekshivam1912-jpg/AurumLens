"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ArrowUpRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ChevronRight,
  Layers,
  Sparkles,
} from "lucide-react";

interface PairCardData {
  pair: string;
  legA: string;
  legB: string;
  zscore: number;
  status: "QUIET" | "ALERT";
  carrySource: "CURVE" | "FALLBACK";
  netEdge: number;
  hurdle: number;
  normSpread: number;
  isNearestMiss?: boolean;
}

const initialPairs: PairCardData[] = [
  {
    pair: "GOLDTEN-GOLDGUINEA",
    legA: "GOLDTEN (31-Oct)",
    legB: "GOLDGUINEA (31-Oct)",
    zscore: 1.67,
    status: "QUIET",
    carrySource: "CURVE",
    netEdge: 48.2,
    hurdle: 42.0,
    normSpread: 0.000966,
    isNearestMiss: true,
  },
  {
    pair: "GOLDM-GOLDTEN",
    legA: "GOLDM (05-Nov)",
    legB: "GOLDTEN (31-Oct)",
    zscore: 0.82,
    status: "QUIET",
    carrySource: "CURVE",
    netEdge: 18.4,
    hurdle: 38.0,
    normSpread: 0.000146,
  },
  {
    pair: "GOLDM-GOLDGUINEA",
    legA: "GOLDM (05-Nov)",
    legB: "GOLDGUINEA (31-Oct)",
    zscore: -1.14,
    status: "QUIET",
    carrySource: "FALLBACK",
    netEdge: -25.0,
    hurdle: 45.0,
    normSpread: -0.00082,
  },
  {
    pair: "GOLDM-GOLDPETAL",
    legA: "GOLDM (05-Nov)",
    legB: "GOLDPETAL (31-Oct)",
    zscore: 0.45,
    status: "QUIET",
    carrySource: "CURVE",
    netEdge: 8.5,
    hurdle: 208.0,
    normSpread: 0.00021,
  },
  {
    pair: "GOLDTEN-GOLDPETAL",
    legA: "GOLDTEN (31-Oct)",
    legB: "GOLDPETAL (31-Oct)",
    zscore: -0.91,
    status: "QUIET",
    carrySource: "FALLBACK",
    netEdge: -42.0,
    hurdle: 215.0,
    normSpread: -0.00065,
  },
  {
    pair: "GOLDGUINEA-GOLDPETAL",
    legA: "GOLDGUINEA (31-Oct)",
    legB: "GOLDPETAL (31-Oct)",
    zscore: 0.33,
    status: "QUIET",
    carrySource: "CURVE",
    netEdge: 5.1,
    hurdle: 195.0,
    normSpread: 0.00018,
  },
];

export default function OverviewPage() {
  const [pairs, setPairs] = useState<PairCardData[]>(initialPairs);
  const [liveAlertToast, setLiveAlertToast] = useState<string | null>(null);

  // Subscribe to live alerts from Supabase Realtime
  useEffect(() => {
    try {
      const channel = supabase
        .channel("signal-feed")
        .on(
          "postgres_changes",
          { event: "INSERT", schema: "public", table: "signal" },
          (payload: any) => {
            if (payload.new && payload.new.status === "ALERT") {
              setLiveAlertToast(`🚨 New Arbitrage Alert Triggered on ${payload.new.pair_id}!`);
              setTimeout(() => setLiveAlertToast(null), 8000);
            }
          }
        )
        .subscribe();

      return () => {
        supabase.removeChannel(channel);
      };
    } catch (e) {
      console.warn("Realtime subscription fallback (offline mode):", e);
    }
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Live Alert Toast */}
      {liveAlertToast && (
        <div className="p-3.5 bg-alert-bg border border-alert-border text-alert rounded-lg flex items-center justify-between shadow-md animate-bounce">
          <div className="flex items-center space-x-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-alert animate-ping" />
            <span className="font-bold text-sm">{liveAlertToast}</span>
          </div>
          <Link
            href="/alerts"
            className="text-xs underline font-semibold text-alert hover:opacity-80"
          >
            Inspect Evidence →
          </Link>
        </div>
      )}

      {/* Top Status Strip */}
      <div className="bg-white rounded-xl p-5 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          {/* Main Status Pill */}
          <div className="inline-flex items-center px-4 py-2 rounded-xl bg-quiet-bg text-quiet border border-quiet-border font-bold text-lg tracking-wide shadow-sm">
            <span className="w-2.5 h-2.5 rounded-full bg-quiet mr-2" />
            QUIET
          </div>
          <div>
            <div className="text-xs text-slate font-medium flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-light" />
              <span>Last evaluated: 01 Oct 2026, 15:45 IST</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            </div>
            <div className="text-xs font-semibold text-ink mt-0.5">
              Market state normal • No persistent divergence exceeds risk hurdles
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="px-2.5 py-1 rounded-md bg-panel border border-gray-200 text-xs font-mono font-medium text-slate">
            config: <strong className="text-ink">v0.4.0</strong> (sha256: 4a9977a)
          </span>
          <span className="px-2.5 py-1 rounded-md bg-panel border border-gray-200 text-xs font-mono font-medium text-slate">
            dataset: <strong className="text-ink">ds_20261001_v1</strong>
          </span>
        </div>
      </div>

      {/* Nearest Miss Spotlight Card (FR17) */}
      <div className="bg-gradient-to-r from-gold-tint via-[#FAF0D7] to-gold-tint rounded-xl p-5 border border-gold-border shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-gold text-white">
              Nearest Miss
            </span>
            <span className="font-bold text-ink text-base">GOLDTEN — GOLDGUINEA</span>
            <span className="text-xs text-slate font-medium">(Expiry Gap: 0 Days)</span>
          </div>
          <p className="text-xs text-slate font-medium">
            Closest pair to triggering an arbitrage alert. <strong>11 of 12 gates passed</strong>. Blocked strictly by anomaly threshold.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-5 shrink-0">
          <div className="text-right">
            <div className="text-xs text-slate font-medium">Current Divergence</div>
            <div className="font-mono text-base font-bold text-ink">
              z = +1.67 <span className="text-xs font-normal text-slate">(target ≥ 2.00)</span>
            </div>
          </div>

          <div className="w-28 bg-white/80 rounded-full h-2.5 border border-gold-border/80 overflow-hidden">
            <div className="bg-gold h-full rounded-full" style={{ width: "83.5%" }} />
          </div>

          <Link
            href="/pair-analysis"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-gold text-white hover:bg-gold-hover text-xs font-semibold shadow-sm transition-colors"
          >
            <span>Inspect Waterfall</span>
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* 2x3 Pair Cards Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-ink text-sm flex items-center gap-2">
            <Layers className="w-4 h-4 text-gold" />
            Active MCX Cross-Contract Pairs (6 Combinations)
          </h2>
          <span className="text-xs text-slate">Normalized to ₹ per 10g of 999 fine gold</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {pairs.map((p) => {
            const isNear = p.isNearestMiss;
            return (
              <div
                key={p.pair}
                className={`bg-white rounded-xl p-4 border transition-all hover:shadow-md ${
                  isNear ? "border-gold shadow-sm ring-1 ring-gold/20" : "border-gray-200"
                }`}
              >
                <div className="flex items-start justify-between mb-2.5">
                  <div>
                    <div className="font-bold text-ink text-sm flex items-center gap-1.5">
                      {p.pair}
                      {isNear && (
                        <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-gold-tint text-gold border border-gold-border">
                          TOP NEAR MISS
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-light font-mono">
                      {p.legA} • {p.legB}
                    </div>
                  </div>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-quiet-bg text-quiet border border-quiet-border">
                    {p.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 my-3 py-2 border-y border-gray-100">
                  <div>
                    <span className="text-[10px] text-slate-light block">Z-Score Divergence</span>
                    <span className="font-mono text-sm font-bold text-ink">
                      {p.zscore > 0 ? `+${p.zscore.toFixed(2)}` : p.zscore.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-light block">Carry Source</span>
                    <span
                      className={`inline-block text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                        p.carrySource === "CURVE"
                          ? "bg-blue-50 text-blue-700 border border-blue-200"
                          : "bg-amber-50 text-amber-700 border border-amber-200"
                      }`}
                    >
                      {p.carrySource}
                    </span>
                  </div>
                </div>

                {/* Net Edge vs Hurdle Bar */}
                <div className="space-y-1 mb-3">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate">Net Edge vs Hurdle</span>
                    <span
                      className={`font-mono font-semibold ${
                        p.netEdge > 0 ? "text-emerald-600" : "text-slate"
                      }`}
                    >
                      {p.netEdge > 0 ? `+₹${p.netEdge.toFixed(1)}` : `₹${p.netEdge.toFixed(1)}`} / ₹{p.hurdle.toFixed(0)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        p.netEdge > 0 ? "bg-emerald-500" : "bg-gray-300"
                      }`}
                      style={{
                        width: `${Math.min(100, Math.max(5, (p.netEdge / p.hurdle) * 100))}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="pt-1 flex items-center justify-between">
                  <span className="text-[11px] font-mono text-slate">
                    Spread: {(p.normSpread * 100).toFixed(4)}%
                  </span>
                  <Link
                    href={`/pair-analysis?pair=${encodeURIComponent(p.pair)}`}
                    className="text-xs font-semibold text-gold hover:text-gold-hover flex items-center gap-0.5"
                  >
                    Analysis <ArrowUpRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
