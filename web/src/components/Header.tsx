"use client";

import { RefreshCw, Radio, ShieldAlert } from "lucide-react";
import { useState } from "react";

export default function Header() {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 600);
  };

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
      {/* Research Mode Top Banner (PRD R24 Watermark) */}
      <div className="bg-amber-50 border-b border-amber-200/80 px-4 py-1 text-xs text-amber-900 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-700" />
          <span className="font-medium">
            <strong className="font-semibold">Research Mode:</strong> Unverified specs permitted with watermark (GOLDGUINEA purity disputed 0.995 vs 0.999).
          </span>
        </div>
        <span className="text-[11px] text-amber-700 font-mono">SEBI Sandbox Rule 4.2</span>
      </div>

      {/* Main Header Bar */}
      <div className="px-6 py-2.5 flex items-center justify-between">
        {/* Left Ticker */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-ink text-sm">MCX: GOLD (ACTIVE)</span>
            <span className="font-mono text-ink font-semibold text-sm">₹1,20,482.41</span>
            <span className="text-[11px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
              +0.34%
            </span>
          </div>
          <div className="h-4 w-px bg-gray-200" />
          <div className="flex items-center space-x-1.5 text-xs text-slate">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-medium">Live Feed (0.4s)</span>
          </div>
        </div>

        {/* Right Controls */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleRefresh}
            className="p-1.5 text-slate hover:text-ink hover:bg-panel rounded-md transition-colors"
            title="Refresh Quotes"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-gold" : ""}`} />
          </button>

          <span className="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-gold-tint text-gold border border-gold-border">
            Paper Engine: Active
          </span>

          <span className="inline-flex items-center px-2.5 py-1 rounded text-xs font-bold bg-ink text-white">
            <Radio className="w-3 h-3 text-emerald-400 mr-1.5" />
            Terminal Live
          </span>

          <div className="w-7 h-7 rounded-full bg-slate text-white text-xs font-semibold flex items-center justify-center cursor-pointer">
            RO
          </div>
        </div>
      </div>
    </header>
  );
}
