"use client";

import { useState } from "react";
import {
  BellRing,
  Download,
  Languages,
  CheckCircle2,
  ShieldCheck,
  FileText,
  Search,
} from "lucide-react";

export default function AlertsPage() {
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [filter, setFilter] = useState<"ALL" | "ALERT" | "QUIET">("ALL");

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-xl p-5 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-base font-bold text-ink">Alert Log & Evidence Records</h1>
          <p className="text-xs text-slate mt-0.5">
            Complete cryptographic audit trail for statistical arbitrage signals, gate results, and execution evidence.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-gray-200 text-xs font-semibold text-slate hover:text-ink hover:bg-panel transition-colors">
            <Download className="w-3.5 h-3.5" />
            <span>Export Trail (CSV)</span>
          </button>
        </div>
      </div>

      {/* Main Split View: Table on Left, Slide-over Evidence Pack on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Signals Table (7 Cols) */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden space-y-3 p-4">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center space-x-1">
              <button
                onClick={() => setFilter("ALL")}
                className={`px-2.5 py-1 rounded text-xs font-semibold ${
                  filter === "ALL" ? "bg-ink text-white" : "text-slate hover:bg-panel"
                }`}
              >
                All (14)
              </button>
              <button
                onClick={() => setFilter("ALERT")}
                className={`px-2.5 py-1 rounded text-xs font-semibold ${
                  filter === "ALERT" ? "bg-alert text-white" : "text-slate hover:bg-panel"
                }`}
              >
                Alerts (2)
              </button>
              <button
                onClick={() => setFilter("QUIET")}
                className={`px-2.5 py-1 rounded text-xs font-semibold ${
                  filter === "QUIET" ? "bg-quiet text-white" : "text-slate hover:bg-panel"
                }`}
              >
                Quiet / Near Misses (12)
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-panel text-slate border-b border-gray-200 font-sans text-[11px] uppercase font-semibold">
                <tr>
                  <th className="py-2 px-2">Signal ID</th>
                  <th className="py-2 px-2">Pair</th>
                  <th className="py-2 px-2">Status</th>
                  <th className="py-2 px-2">Z-Score</th>
                  <th className="py-2 px-2">Net Edge</th>
                  <th className="py-2 px-2">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <tr className="bg-gold-tint/30 hover:bg-gold-tint/50">
                  <td className="py-2.5 px-2 font-bold text-ink">sig_20261001_01</td>
                  <td className="py-2.5 px-2 text-ink font-sans font-medium">GOLDTEN-GOLDGUINEA</td>
                  <td className="py-2.5 px-2">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-alert-bg text-alert border border-alert-border">
                      ALERT
                    </span>
                  </td>
                  <td className="py-2.5 px-2 font-bold text-emerald-700">+2.42σ</td>
                  <td className="py-2.5 px-2 text-ink font-bold">+₹310.00</td>
                  <td className="py-2.5 px-2">
                    <span className="text-[11px] text-gold font-semibold font-sans cursor-pointer underline">
                      Inspecting ✓
                    </span>
                  </td>
                </tr>

                <tr className="hover:bg-panel/50">
                  <td className="py-2.5 px-2 text-slate">sig_20260928_02</td>
                  <td className="py-2.5 px-2 text-ink font-sans">GOLDM-GOLDTEN</td>
                  <td className="py-2.5 px-2">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-quiet-bg text-quiet border border-quiet-border">
                      QUIET
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-slate">+1.82σ</td>
                  <td className="py-2.5 px-2 text-slate">+₹190.00</td>
                  <td className="py-2.5 px-2">
                    <span className="text-[11px] text-slate-light font-sans">Inspect</span>
                  </td>
                </tr>

                <tr className="hover:bg-panel/50">
                  <td className="py-2.5 px-2 text-slate">sig_20260925_01</td>
                  <td className="py-2.5 px-2 text-ink font-sans">GOLDM-GOLDPETAL</td>
                  <td className="py-2.5 px-2">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-quiet-bg text-quiet border border-quiet-border">
                      QUIET
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-slate">+2.15σ</td>
                  <td className="py-2.5 px-2 text-slate">-₹85.00</td>
                  <td className="py-2.5 px-2">
                    <span className="text-[11px] text-slate-light font-sans">Inspect</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Slide-Over Evidence Pack (5 Cols) */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-gold-border p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-gold">
                EVIDENCE PACK (PRD §11)
              </span>
              <h2 className="text-sm font-bold text-ink">sig_20261001_01</h2>
            </div>
            {/* Language Toggle */}
            <div className="flex items-center space-x-1 bg-panel p-1 rounded-lg border border-gray-200 text-xs">
              <button
                onClick={() => setLang("en")}
                className={`px-2 py-0.5 rounded font-semibold ${
                  lang === "en" ? "bg-white text-ink shadow-xs" : "text-slate"
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLang("hi")}
                className={`px-2 py-0.5 rounded font-semibold ${
                  lang === "hi" ? "bg-white text-ink shadow-xs" : "text-slate"
                }`}
              >
                हिंदी
              </button>
            </div>
          </div>

          {/* Plain-Language Explanation Box (Passed Numeric Guard R25) */}
          <div className="bg-panel rounded-lg p-3.5 border border-gray-200 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-ink flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-gold" />
                Audited Explainer Output
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                ✓ Numeric Guard Passed
              </span>
            </div>

            {lang === "en" ? (
              <p className="text-slate leading-relaxed">
                On 01 Oct 2026, <strong>GOLDTEN</strong> (₹1,20,500) normalized is rich relative to{" "}
                <strong>GOLDGUINEA</strong> (₹96,400) by <strong>2.42 standard deviations</strong> above
                the 60-day rolling mean. All 12 risk and liquidity gates passed. Expected gross
                convergence is ₹580.00, total friction is ₹170.00, and adverse slippage is ₹50.00,
                yielding a <strong>net edge of +₹310.00</strong> (₹77.50 per 10g). Recommended sizing is{" "}
                <strong>4 lots GOLDTEN to 5 lots GOLDGUINEA</strong> with 0.0g residual unhedged gold.
              </p>
            ) : (
              <p className="text-slate leading-relaxed font-sans">
                01 अक्टूबर 2026 को, <strong>GOLDTEN</strong> (₹1,20,500) मानकीकृत भाव 60-दिवसीय रोलिंग
                औसत से <strong>2.42 मानक विचलन</strong> अधिक है (<strong>GOLDGUINEA</strong> ₹96,400 की तुलना में)।
                सभी 12 जोखिम और तरलता गेट्स पास हुए। अपेक्षित सकल अभिसरण ₹580.00 है, कुल लागत ₹170.00 और
                स्लिपेज ₹50.00 है, जिससे <strong>शुद्ध लाभ +₹310.00</strong> प्राप्त होता है। अनुशंसित
                लॉट अनुपात <strong>4 लॉट GOLDTEN और 5 लॉट GOLDGUINEA</strong> है जिसमें 0.0 ग्राम अवशिष्ट जोखिम है।
              </p>
            )}
          </div>

          {/* Sizing & Gate Checklist */}
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between py-1 border-b border-gray-100">
              <span className="text-slate">Gate Waterfall Status:</span>
              <span className="font-bold text-emerald-700">12 / 12 PASSED (100%)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-gray-100">
              <span className="text-slate">Recommended Execution:</span>
              <span className="font-mono font-semibold text-ink">Short 4 GOLDTEN : Long 5 GUINEA</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate">Residual Fine Gold:</span>
              <span className="font-mono font-bold text-emerald-600">0.0g (Perfect Parity)</span>
            </div>
          </div>

          {/* Export Actions */}
          <div className="pt-2 flex gap-2">
            <button className="flex-1 py-2 rounded-lg bg-gold text-white hover:bg-gold-hover text-xs font-semibold shadow-sm transition-colors text-center">
              Export Evidence (HTML)
            </button>
            <button className="flex-1 py-2 rounded-lg border border-gray-200 text-slate hover:text-ink text-xs font-semibold transition-colors text-center">
              Export Evidence (CSV)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
