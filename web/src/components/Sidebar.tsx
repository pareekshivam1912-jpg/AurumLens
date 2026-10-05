"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  GitCompare,
  TrendingUp,
  Calendar,
  BellRing,
  Shield,
  FileCheck2,
  BookOpen,
  FlaskConical,
  Download,
  Settings,
  HelpCircle,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: any;
  badge?: string;
}

const navItems: NavItem[] = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Pair Analysis", href: "/pair-analysis", icon: GitCompare },
  { name: "Backtest", href: "/backtest", icon: TrendingUp },
  { name: "Calendar", href: "/calendar", icon: Calendar },
  { name: "Alert Log", href: "/alerts", icon: BellRing, badge: "2" },
  { name: "Hedge Tools", href: "/hedge-tools", icon: Shield },
  { name: "Data Health", href: "/data-health", icon: FileCheck2 },
  { name: "Methodology", href: "/methodology", icon: BookOpen },
  { name: "Paper Trading", href: "/paper-trading", icon: FlaskConical },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen sticky top-0 shrink-0 select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-gold flex items-center justify-center text-white font-bold text-lg shadow-sm">
            AU
          </div>
          <div>
            <div className="font-bold text-ink text-sm tracking-tight flex items-center gap-1.5">
              AurumLens
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-gold-tint text-gold font-semibold border border-gold-border">
                RV
              </span>
            </div>
            <div className="text-[11px] text-slate font-medium">MCX Gold RV Suite</div>
          </div>
        </div>
      </div>

      {/* Mandate Pod */}
      <div className="px-3 pt-3">
        <div className="bg-panel rounded-lg p-2.5 border border-gray-200/70 text-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold text-ink text-[11px]">MCX Arb-Desk 01</span>
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              ACTIVE
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate">
            <span>Latency</span>
            <span className="font-mono text-emerald-600 font-medium">3.8 ms</span>
          </div>
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                isActive
                  ? "bg-gold text-white shadow-sm font-semibold"
                  : "text-slate hover:text-ink hover:bg-panel"
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate"}`} />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span
                  className={`px-1.5 py-0.5 text-[10px] rounded-full font-bold ${
                    isActive ? "bg-white text-gold" : "bg-red-100 text-alert"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Actions */}
      <div className="p-3 border-t border-gray-100 space-y-1.5">
        <button className="w-full flex items-center justify-center space-x-1.5 py-2 px-3 rounded-lg border border-gold text-gold hover:bg-gold-tint text-xs font-semibold transition-colors">
          <Download className="w-3.5 h-3.5" />
          <span>Export Report</span>
        </button>
        <div className="flex items-center justify-between px-2 pt-1 text-[11px] text-slate">
          <Link href="/methodology" className="hover:text-ink flex items-center gap-1">
            <HelpCircle className="w-3 h-3" />
            Docs
          </Link>
          <Link href="/data-health" className="hover:text-ink flex items-center gap-1">
            <Settings className="w-3 h-3" />
            Specs
          </Link>
        </div>
      </div>
    </aside>
  );
}
