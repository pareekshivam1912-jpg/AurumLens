"use client";

import {
  Calendar as CalendarIcon,
  ShieldAlert,
  Flame,
  AlertTriangle,
  Info,
  Clock,
  Pin,
} from "lucide-react";

interface EventPin {
  date: string;
  title: string;
  category: string;
  impact: "HIGH" | "MEDIUM";
  note: string;
}

const events: EventPin[] = [
  {
    date: "08 Oct 2026",
    title: "RBI Monetary Policy Committee Rate Decision",
    category: "Macro / Rates",
    impact: "HIGH",
    note: "Domestic sovereign repo rate trajectory affects INR gold carry cost basis.",
  },
  {
    date: "14 Oct 2026",
    title: "US CPI Inflation Release",
    category: "Macro / FX",
    impact: "HIGH",
    note: "Dollar index and real yield volatility impact international gold price velocity.",
  },
  {
    date: "29 Oct 2026",
    title: "Dhanteras / Diwali Festive Sourcing Peak",
    category: "Physical Basis",
    impact: "HIGH",
    note: "Extreme physical bullion delivery demand may trigger localized spot-to-futures basis blowouts.",
  },
  {
    date: "04 Nov 2026",
    title: "US Federal Reserve FOMC Rate Decision",
    category: "Macro / Fed",
    impact: "HIGH",
    note: "Benchmark global carry cost repricing across bullion curve.",
  },
];

export default function CalendarPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="bg-white rounded-xl p-5 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-base font-bold text-ink">Contract Lifecycle & Market Event Calendar</h1>
          <p className="text-xs text-slate mt-0.5">
            Expiry horizons, SEBI physical tender unsafe windows, and macro bullion event pins.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded bg-panel border border-gray-200 font-mono text-xs text-ink font-semibold">
            Q4 2026 Horizon
          </span>
        </div>
      </div>

      {/* Expiry Risk Gate Banner (R11) */}
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start space-x-3 text-xs">
        <ShieldAlert className="w-5 h-5 text-alert shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-alert">
            SEBI Compulsory Tender Risk Window — Gate R11 Active Enforcement
          </div>
          <p className="text-red-900 leading-relaxed">
            All relative-value arbitrage alerts are strictly suppressed when either contract leg enters its <strong>5-calendar-day pre-expiry window</strong> (3-day physical delivery tender period + 2-day buffer). This protects capital from compulsory physical delivery obligations on MCX.
          </p>
        </div>
      </div>

      {/* Contract Lifecycle Horizons Gantt */}
      <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-4">
        <h2 className="text-sm font-bold text-ink">Q4 2026 MCX Contract Tenors & Tender Windows</h2>

        <div className="space-y-3">
          {/* GOLDM */}
          <div className="bg-panel rounded-lg p-3 border border-gray-200 space-y-1.5">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-ink">GOLDM (100g • Expiry: 5th of Month)</span>
              <span className="font-mono text-slate">Next: 05-Nov-2026</span>
            </div>
            <div className="h-6 w-full bg-emerald-100 rounded flex overflow-hidden text-[10px] font-mono text-center leading-6">
              <div className="w-[12%] bg-red-300 text-red-900 font-bold" title="Oct 01 - Oct 05 Tender Window">
                Tender Risk (Oct 01-05)
              </div>
              <div className="w-[76%] text-emerald-800 font-semibold">
                Liquid Trading Horizon (Safe Zone)
              </div>
              <div className="w-[12%] bg-red-300 text-red-900 font-bold" title="Nov 01 - Nov 05 Tender Window">
                Tender Risk (Nov 01-05)
              </div>
            </div>
          </div>

          {/* GOLDTEN */}
          <div className="bg-panel rounded-lg p-3 border border-gray-200 space-y-1.5">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-ink">GOLDTEN (10g • Expiry: Month-End)</span>
              <span className="font-mono text-slate">Next: 31-Oct-2026</span>
            </div>
            <div className="h-6 w-full bg-emerald-100 rounded flex overflow-hidden text-[10px] font-mono text-center leading-6">
              <div className="w-[85%] text-emerald-800 font-semibold">
                Liquid Trading Horizon (Safe Zone)
              </div>
              <div className="w-[15%] bg-red-300 text-red-900 font-bold" title="Oct 26 - Oct 31 Tender Window">
                Tender Risk (Oct 26-31)
              </div>
            </div>
          </div>

          {/* GOLDGUINEA */}
          <div className="bg-panel rounded-lg p-3 border border-gray-200 space-y-1.5">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-ink">GOLDGUINEA (8g • Expiry: Month-End)</span>
              <span className="font-mono text-slate">Next: 31-Oct-2026</span>
            </div>
            <div className="h-6 w-full bg-emerald-100 rounded flex overflow-hidden text-[10px] font-mono text-center leading-6">
              <div className="w-[85%] text-emerald-800 font-semibold">
                Liquid Trading Horizon (Safe Zone)
              </div>
              <div className="w-[15%] bg-red-300 text-red-900 font-bold" title="Oct 26 - Oct 31 Tender Window">
                Tender Risk (Oct 26-31)
              </div>
            </div>
          </div>

          {/* GOLDPETAL */}
          <div className="bg-panel rounded-lg p-3 border border-gray-200 space-y-1.5">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-ink">GOLDPETAL (1g • Expiry: Month-End)</span>
              <span className="font-mono text-slate">Next: 31-Oct-2026</span>
            </div>
            <div className="h-6 w-full bg-emerald-100 rounded flex overflow-hidden text-[10px] font-mono text-center leading-6">
              <div className="w-[85%] text-emerald-800 font-semibold">
                Liquid Trading Horizon (Safe Zone)
              </div>
              <div className="w-[15%] bg-red-300 text-red-900 font-bold" title="Oct 26 - Oct 31 Tender Window">
                Tender Risk (Oct 26-31)
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Macro Events & Cross-Contract Alignment Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Macro Events */}
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-ink flex items-center gap-1.5">
            <Pin className="w-4 h-4 text-gold" />
            Macro Market Event Pins (from events.yaml)
          </h3>
          <div className="space-y-2.5">
            {events.map((e) => (
              <div key={e.title} className="p-3 rounded-lg border border-gray-200 bg-panel text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-ink">{e.date}</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900">
                    {e.category}
                  </span>
                </div>
                <div className="font-semibold text-ink">{e.title}</div>
                <p className="text-[11px] text-slate">{e.note}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Minimal Expiry Gap Rule (R17) */}
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-ink">Smallest-Gap Expiry Matching (R17)</h3>
          <p className="text-xs text-slate">
            Pairs contracts by smallest absolute expiry gap (within 35 days) to minimize calendar carry distortion.
          </p>

          <div className="bg-gold-tint/40 p-4 rounded-lg border border-gold-border text-xs space-y-2">
            <div className="font-bold text-ink">Hand Fixture Verification (Design §6.4):</div>
            <div className="font-mono text-[11px] text-slate space-y-1">
              <div>• GOLDTEN Oct-31 pairs with <strong>GOLDM Nov-05 (gap: 5 days)</strong></div>
              <div>• Rejects GOLDM Oct-05 (gap: 26 days) due to larger calendar divergence</div>
              <div>• Carry rate is implied from curve; fallback rate: 6.50%</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
