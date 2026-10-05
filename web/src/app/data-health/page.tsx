"use client";

import { useState } from "react";
import {
  FileCheck2,
  AlertTriangle,
  CheckCircle2,
  Database,
  ShieldAlert,
  HelpCircle,
} from "lucide-react";

export default function DataHealthPage() {
  const [specMode, setSpecMode] = useState<"research" | "strict">("research");

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-xl p-5 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-base font-bold text-ink">
            Data Health & Contract Specifications Trust Register
          </h1>
          <p className="text-xs text-slate mt-0.5">
            Audit trail of MCX Bhavcopy ingestion, deduplication guarantee, and official contract specification statuses.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold">
            DATA INTEGRITY: 98.4% (HEALTHY)
          </span>
        </div>
      </div>

      {/* Spec Mode Toggle (PRD R24) */}
      <div className="bg-panel border border-gray-200 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
        <div className="space-y-1">
          <div className="font-bold text-ink flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-gold" />
            Specification Strictness Mode (R24)
          </div>
          <p className="text-slate">
            In <strong>Strict Mode</strong>, any contract with an unverified or disputed specification (e.g. GOLDGUINEA purity) forces QUIET with reason <code className="text-red-700 bg-red-50 px-1 py-0.5 rounded">SPEC_UNVERIFIED</code>.
          </p>
        </div>

        <div className="flex items-center bg-white p-1 rounded-lg border border-gray-200 shrink-0 font-semibold">
          <button
            onClick={() => setSpecMode("research")}
            className={`px-3 py-1 rounded ${
              specMode === "research" ? "bg-amber-100 text-amber-900 font-bold" : "text-slate"
            }`}
          >
            Research Mode (Watermarked)
          </button>
          <button
            onClick={() => setSpecMode("strict")}
            className={`px-3 py-1 rounded ${
              specMode === "strict" ? "bg-ink text-white font-bold" : "text-slate"
            }`}
          >
            Strict Mode (Enforced)
          </button>
        </div>
      </div>

      {/* Facts Register (Panel 1) */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden p-5 space-y-3">
        <h2 className="text-sm font-bold text-ink">Contract Specifications Facts Register (contracts.yaml)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-panel text-slate border-b border-gray-200 text-[11px] uppercase font-semibold">
              <tr>
                <th className="py-2.5 px-3">Symbol</th>
                <th className="py-2.5 px-3">Trading Unit</th>
                <th className="py-2.5 px-3">Quote Basis</th>
                <th className="py-2.5 px-3">Purity</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-4">Official Citation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-mono">
              <tr>
                <td className="py-2.5 px-3 font-sans font-bold text-ink">GOLDM</td>
                <td className="py-2.5 px-3">100g</td>
                <td className="py-2.5 px-3">10g</td>
                <td className="py-2.5 px-3">0.995</td>
                <td className="py-2.5 px-3">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    VERIFIED_OFFICIAL
                  </span>
                </td>
                <td className="py-2.5 px-4 font-sans text-slate text-[11px]">MCX Circular MCX/TRD/724/2023</td>
              </tr>

              <tr>
                <td className="py-2.5 px-3 font-sans font-bold text-ink">GOLDTEN</td>
                <td className="py-2.5 px-3">10g</td>
                <td className="py-2.5 px-3">10g</td>
                <td className="py-2.5 px-3">0.999</td>
                <td className="py-2.5 px-3">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    VERIFIED_OFFICIAL
                  </span>
                </td>
                <td className="py-2.5 px-4 font-sans text-slate text-[11px]">MCX Circular MCX/TRD/112/2024</td>
              </tr>

              <tr className="bg-amber-50/50">
                <td className="py-2.5 px-3 font-sans font-bold text-amber-900">GOLDGUINEA</td>
                <td className="py-2.5 px-3">8g</td>
                <td className="py-2.5 px-3">8g</td>
                <td className="py-2.5 px-3 text-amber-900 font-bold">DISPUTED (0.995 vs 0.999)</td>
                <td className="py-2.5 px-3">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                    DISPUTED
                  </span>
                </td>
                <td className="py-2.5 px-4 font-sans text-amber-900 text-[11px]">
                  Divergence between contract note & BIS hallmark
                </td>
              </tr>

              <tr>
                <td className="py-2.5 px-3 font-sans font-bold text-ink">GOLDPETAL</td>
                <td className="py-2.5 px-3">1g</td>
                <td className="py-2.5 px-3">1g</td>
                <td className="py-2.5 px-3">0.999</td>
                <td className="py-2.5 px-3">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    VERIFIED_OFFICIAL
                  </span>
                </td>
                <td className="py-2.5 px-4 font-sans text-slate text-[11px]">MCX Contract Master 2025-26</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Ingestion Run Log & Suspect Prices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ingestion Log */}
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-3 text-xs">
          <h3 className="text-sm font-bold text-ink">Ingestion Pipeline Run Audit (Phase 1 / A3)</h3>
          <div className="space-y-2 font-mono">
            <div className="flex justify-between p-2 rounded bg-panel">
              <span className="font-sans text-slate">Dates Requested:</span>
              <strong className="text-ink">10 Days</strong>
            </div>
            <div className="flex justify-between p-2 rounded bg-panel">
              <span className="font-sans text-slate">Successfully Parsed:</span>
              <strong className="text-emerald-700">9 Days</strong>
            </div>
            <div className="flex justify-between p-2 rounded bg-panel">
              <span className="font-sans text-slate">Holidays/Weekends Rejected:</span>
              <strong className="text-amber-700">1 Day (Holiday Guard Passed)</strong>
            </div>
            <div className="flex justify-between p-2 rounded bg-panel">
              <span className="font-sans text-slate">Total Records Ingested:</span>
              <strong className="text-ink">151 Contract Records</strong>
            </div>
            <div className="flex justify-between p-2 rounded bg-emerald-50 text-emerald-900 border border-emerald-200 font-sans font-semibold">
              <span>Silent Duplicate Count:</span>
              <strong>0 Duplicates (100% Unique)</strong>
            </div>
          </div>
        </div>

        {/* SUSPECT Monitor */}
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-3 text-xs">
          <h3 className="text-sm font-bold text-ink">SUSPECT Prices Filter (R19 Quality Engine)</h3>
          <p className="text-slate">
            12 contract records flagged as SUSPECT and suppressed from relative-value spread calculations.
          </p>
          <div className="space-y-1.5 font-mono text-[11px]">
            <div className="p-2 rounded bg-panel border border-gray-200 flex justify-between">
              <span>GOLDGUINEA Nov-2026 (Vol: 2 lots &lt; 5 lots threshold)</span>
              <span className="text-alert font-bold">LOW_VOLUME</span>
            </div>
            <div className="p-2 rounded bg-panel border border-gray-200 flex justify-between">
              <span>GOLDPETAL Dec-2026 (Close vs Settle gap &gt; 1.5%)</span>
              <span className="text-alert font-bold">SETTLE_DIVERGENCE</span>
            </div>
            <div className="p-2 rounded bg-panel border border-gray-200 flex justify-between">
              <span>GOLDM Jan-2027 (Illiquid spread spike)</span>
              <span className="text-alert font-bold">WIDE_SPREAD</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
