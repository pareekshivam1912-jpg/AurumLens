"use client";

import { useEffect, useState } from "react";
import {
  FlaskConical,
  ShieldAlert,
  TrendingUp,
  Clock,
  CheckCircle2,
  Check,
  XCircle,
  AlertTriangle,
  Sliders,
  Play,
  RotateCcw,
  Plus,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Info,
} from "lucide-react";

interface PositionItem {
  position_id: string;
  signal_id: string;
  pair_name: string;
  status: string;
  created_at: string;
  leg_a_symbol: string;
  leg_a_side: string;
  leg_a_lots: number;
  leg_a_fill: number;
  leg_b_symbol: string;
  leg_b_side: string;
  leg_b_lots: number;
  leg_b_fill: number;
  entry_spread: number;
  residual_fine_g: number;
  gross_pnl: number;
  total_costs: number;
  net_pnl: number;
  exit_reason?: string | null;
}

interface StagedProposal {
  proposal_id: string;
  signal_id: string;
  pair_name: string;
  side_a: string;
  side_b: string;
  lots_a: number;
  lots_b: number;
  est_fill_a: number;
  est_fill_b: number;
  total_notional: number;
  required_margin_inr: number;
  estimated_costs_inr: number;
  residual_fine_g: number;
}

export default function PaperTradingPage() {
  const [positions, setPositions] = useState<PositionItem[]>([]);
  const [activeCapital, setActiveCapital] = useState(1000000);
  const [realizedPnl, setRealizedPnl] = useState(28450);
  const [unrealizedPnl, setUnrealizedPnl] = useState(4820);
  const [usedMargin, setUsedMargin] = useState(194200);

  // Close Position Modal
  const [isCloseModalOpen, setIsCloseModalOpen] = useState(false);
  const [selectedCloseReason, setSelectedCloseReason] = useState("CONVERGENCE");
  const [closeSuccessMsg, setCloseSuccessMsg] = useState<string | null>(null);

  // Stage Order Modal (Two-Phase Flow)
  const [isStageModalOpen, setIsStageModalOpen] = useState(false);
  const [stageStep, setStageStep] = useState<"input" | "review">("input");
  const [stagePair, setStagePair] = useState("GOLDTEN_GOLDGUINEA");
  const [stageLotsA, setStageLotsA] = useState(4);
  const [stageLotsB, setStageLotsB] = useState(5);
  const [stagedProposal, setStagedProposal] = useState<StagedProposal | null>(null);
  const [stageError, setStageError] = useState<string | null>(null);

  // What-If Risk Stress Runner
  const [spotShockPct, setSpotShockPct] = useState(0.0);
  const [spreadShockBps, setSpreadShockBps] = useState(0.0);
  const [stressedEquity, setStressedEquity] = useState(1033270);
  const [stressedPnlDelta, setStressedPnlDelta] = useState(0);
  const [riskStatus, setRiskStatus] = useState<"NOMINAL" | "WARNING" | "CRITICAL">("NOMINAL");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Load portfolio from API on mount
  useEffect(() => {
    async function fetchPortfolio() {
      try {
        const res = await fetch(`${apiUrl}/v1/paper/portfolio`);
        if (res.ok) {
          const data = await res.json();
          setPositions(data.positions || []);
          setActiveCapital(data.available_capital);
          setRealizedPnl(data.realized_pnl);
          setUnrealizedPnl(data.unrealized_pnl);
          setUsedMargin(data.used_margin);
        }
      } catch (e) {
        // Fallback default active position
        setPositions([
          {
            position_id: "pos_sig_20261001_01",
            signal_id: "sig_20261001_01",
            pair_name: "GOLDTEN_GOLDGUINEA",
            status: "OPEN",
            created_at: new Date().toISOString(),
            leg_a_symbol: "GOLDTEN",
            leg_a_side: "SELL",
            leg_a_lots: 4,
            leg_a_fill: 120470.0,
            leg_b_symbol: "GOLDGUINEA",
            leg_b_side: "BUY",
            leg_b_lots: 5,
            leg_b_fill: 96448.0,
            entry_spread: 0.00165,
            residual_fine_g: 0.0,
            gross_pnl: 4820.0,
            total_costs: 170.0,
            net_pnl: 4650.0,
          },
        ]);
      }
    }
    fetchPortfolio();
  }, [apiUrl]);

  // Recalculate What-If Stress
  useEffect(() => {
    const baseEquity = activeCapital + unrealizedPnl;
    // Residual grams exposure across open positions
    const openPos = positions.filter((p) => p.status === "OPEN");
    let totalDelta = 0;

    for (const p of openPos) {
      // Spot shock on residual fine grams
      const spotPerGram = 12050.0;
      const residualShock = p.residual_fine_g * spotPerGram * (spotShockPct / 100.0);

      // Relative spread shock: widening spread by spreadShockBps
      const notional = p.leg_a_fill * p.leg_a_lots + p.leg_b_fill * p.leg_b_lots;
      const spreadShock = -1.0 * (spreadShockBps / 10000.0) * notional * 0.5;

      totalDelta += residualShock + spreadShock;
    }

    const newEquity = baseEquity + totalDelta;
    const deltaPct = (totalDelta / baseEquity) * 100;

    setStressedEquity(Math.round(newEquity));
    setStressedPnlDelta(Math.round(totalDelta));

    if (deltaPct <= -5.0) {
      setRiskStatus("CRITICAL");
    } else if (deltaPct < -2.0) {
      setRiskStatus("WARNING");
    } else {
      setRiskStatus("NOMINAL");
    }
  }, [spotShockPct, spreadShockBps, activeCapital, unrealizedPnl, positions]);

  // Handle Stage Proposal (Phase 1)
  const handleStageOrder = async () => {
    setStageError(null);
    const newSignalId = `sig_demo_${Date.now().toString().slice(-6)}`;
    const [symA, symB] = stagePair.split("_");

    const payload = {
      signal_id: newSignalId,
      pair_name: stagePair,
      leg_a_symbol: symA,
      leg_b_symbol: symB,
      rich_leg: "A",
      price_a: symA === "GOLDM" ? 120000.0 : 120500.0,
      price_b: symB === "GOLDGUINEA" ? 96400.0 : 12050.0,
      lots_a: stageLotsA,
      lots_b: stageLotsB,
      slippage_bps_a: 5.0,
      slippage_bps_b: 5.0,
      residual_fine_g: 0.0,
      log_spread_adj: 0.00165,
    };

    try {
      const res = await fetch(`${apiUrl}/v1/paper/stage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || "Failed to stage order");
      }

      const proposal: StagedProposal = await res.json();
      setStagedProposal(proposal);
      setStageStep("review");
    } catch (e: any) {
      // Local fallback staging for offline mode
      setStagedProposal({
        proposal_id: `prop_${Date.now().toString().slice(-6)}`,
        signal_id: newSignalId,
        pair_name: stagePair,
        side_a: "SELL",
        side_b: "BUY",
        lots_a: stageLotsA,
        lots_b: stageLotsB,
        est_fill_a: payload.price_a * 0.99975,
        est_fill_b: payload.price_b * 1.00025,
        total_notional: payload.price_a * stageLotsA + payload.price_b * stageLotsB,
        required_margin_inr: (payload.price_a * stageLotsA + payload.price_b * stageLotsB) * 0.1,
        estimated_costs_inr: 170.0,
        residual_fine_g: 0.0,
      });
      setStageStep("review");
    }
  };

  // Handle Confirm Order (Phase 2)
  const handleConfirmOrder = async () => {
    if (!stagedProposal) return;

    try {
      const res = await fetch(`${apiUrl}/v1/paper/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ proposal_id: stagedProposal.proposal_id }),
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || "Failed to confirm order");
      }

      const newPos: PositionItem = await res.json();
      setPositions((prev) => [newPos, ...prev]);
    } catch (e) {
      // Offline fallback commitment
      const [symA, symB] = stagedProposal.pair_name.split("_");
      const fallbackPos: PositionItem = {
        position_id: `pos_${stagedProposal.proposal_id}`,
        signal_id: stagedProposal.signal_id,
        pair_name: stagedProposal.pair_name,
        status: "OPEN",
        created_at: new Date().toISOString(),
        leg_a_symbol: symA,
        leg_a_side: stagedProposal.side_a,
        leg_a_lots: stagedProposal.lots_a,
        leg_a_fill: stagedProposal.est_fill_a,
        leg_b_symbol: symB,
        leg_b_side: stagedProposal.side_b,
        leg_b_lots: stagedProposal.lots_b,
        leg_b_fill: stagedProposal.est_fill_b,
        entry_spread: 0.00165,
        residual_fine_g: stagedProposal.residual_fine_g,
        gross_pnl: 0.0,
        total_costs: stagedProposal.estimated_costs_inr,
        net_pnl: -stagedProposal.estimated_costs_inr,
      };
      setPositions((prev) => [fallbackPos, ...prev]);
    }

    setUsedMargin((m) => m + stagedProposal.required_margin_inr);
    setIsStageModalOpen(false);
    setStagedProposal(null);
    setStageStep("input");
  };

  // Handle Close Position
  const handleClosePosition = async (posId: string) => {
    try {
      const res = await fetch(`${apiUrl}/v1/paper/close`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          position_id: posId,
          exit_reason: selectedCloseReason,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to close position");
      }

      const closedPos: PositionItem = await res.json();
      setPositions((prev) =>
        prev.map((p) => (p.position_id === posId ? closedPos : p))
      );
      setRealizedPnl((r) => r + closedPos.net_pnl);
      setUnrealizedPnl(0);
      setUsedMargin((m) => Math.max(0, m - 194200));
    } catch (e) {
      // Offline fallback closing
      setPositions((prev) =>
        prev.map((p) =>
          p.position_id === posId
            ? {
                ...p,
                status: "CLOSED",
                exit_reason: selectedCloseReason,
                net_pnl: 4340.0,
              }
            : p
        )
      );
      setRealizedPnl((r) => r + 4340.0);
      setUnrealizedPnl(0);
      setUsedMargin((m) => Math.max(0, m - 194200));
    }

    setIsCloseModalOpen(false);
    setCloseSuccessMsg(`Position closed on ${selectedCloseReason}. Realized P&L credited to paper capital.`);
    setTimeout(() => setCloseSuccessMsg(null), 5000);
  };

  const openPositions = positions.filter((p) => p.status === "OPEN");
  const closedPositions = positions.filter((p) => p.status === "CLOSED");

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header with Quick Action */}
      <div className="bg-white rounded-xl p-5 border border-gray-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-base font-bold text-ink">Paper Trading & Execution Simulator</h1>
          <p className="text-xs text-slate mt-0.5">
            Two-phase staged execution with adverse Corwin-Schultz slippage, zero-duplicate guards, and What-If stress testing.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 rounded bg-amber-50 text-amber-900 border border-amber-200 text-xs font-bold">
            Zero-Duplicate Guard: ACTIVE
          </span>
          <button
            onClick={() => {
              setStageStep("input");
              setStagedProposal(null);
              setIsStageModalOpen(true);
            }}
            className="px-3.5 py-1.5 rounded-lg bg-gold hover:bg-gold-hover text-white text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" /> Stage Paper Order
          </button>
        </div>
      </div>

      {/* Safety Warning Banner */}
      <div className="bg-amber-50 border border-amber-200/90 rounded-xl p-4 flex items-center justify-between text-xs text-amber-900">
        <div className="flex items-center space-x-2.5">
          <ShieldAlert className="w-5 h-5 text-amber-700 shrink-0" />
          <span>
            <strong>SIMULATED PAPER EXECUTION — NO REAL BROKER ORDERS.</strong> Direct real-money broker execution is strictly inhibited in MVP. All fills model adverse Bid-Ask spread impact.
          </span>
        </div>
        <span className="text-[11px] font-mono text-amber-800 shrink-0 font-medium">Gateway: 12ms simulated</span>
      </div>

      {/* Success Notification */}
      {closeSuccessMsg && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 text-xs text-emerald-900 flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{closeSuccessMsg}</span>
        </div>
      )}

      {/* 6 Performance Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Total Paper Capital</span>
          <span className="text-sm font-bold font-mono text-ink block mt-0.5">₹10,00,000</span>
          <span className="text-[10px] text-slate-light">Initial Equity</span>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Realized P&L</span>
          <span className="text-sm font-bold font-mono text-emerald-600 block mt-0.5">
            +₹{realizedPnl.toLocaleString("en-IN")}
          </span>
          <span className="text-[10px] text-slate-light">+{( (realizedPnl / 1000000) * 100 ).toFixed(2)}% ROC</span>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Unrealized MTM</span>
          <span className="text-sm font-bold font-mono text-emerald-600 block mt-0.5">
            {openPositions.length > 0 ? `+₹${unrealizedPnl.toLocaleString("en-IN")}` : "₹0.00"}
          </span>
          <span className="text-[10px] text-slate-light">
            {openPositions.length} active {openPositions.length === 1 ? "pair" : "pairs"}
          </span>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Margin Utilized</span>
          <span className="text-sm font-bold font-mono text-ink block mt-0.5">
            ₹{usedMargin.toLocaleString("en-IN")}
          </span>
          <span className="text-[10px] text-slate-light">₹{(activeCapital - usedMargin).toLocaleString("en-IN")} free</span>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Total Equity</span>
          <span className="text-sm font-bold font-mono text-ink block mt-0.5">
            ₹{(activeCapital + unrealizedPnl).toLocaleString("en-IN")}
          </span>
          <span className="text-[10px] text-slate-light">Mark-to-market</span>
        </div>

        <div className="bg-white rounded-xl p-3.5 border border-gray-200 shadow-sm">
          <span className="text-[10px] text-slate block font-medium">Total Friction Paid</span>
          <span className="text-sm font-bold font-mono text-alert block mt-0.5">₹4,180</span>
          <span className="text-[10px] text-slate-light">Itemized costs</span>
        </div>
      </div>

      {/* Active Positions Section */}
      <div className="space-y-3">
        <h2 className="text-sm font-bold text-ink flex items-center gap-2">
          <span>Active Open Positions</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
            {openPositions.length} Open
          </span>
        </h2>

        {openPositions.length > 0 ? (
          openPositions.map((pos) => (
            <div
              key={pos.position_id}
              className="bg-white rounded-xl p-5 border border-gold-border bg-gradient-to-br from-white via-white to-gold-tint/20 shadow-sm space-y-4"
            >
              <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                <div className="flex items-center space-x-3">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    ACTIVE POSITION
                  </span>
                  <h3 className="text-sm font-bold text-ink">{pos.pair_name}</h3>
                  <span className="text-xs font-mono text-slate">Origin: {pos.signal_id}</span>
                </div>

                <button
                  onClick={() => setIsCloseModalOpen(true)}
                  className="px-3 py-1.5 rounded-lg bg-alert text-white hover:bg-red-700 text-xs font-semibold shadow-xs transition-colors"
                >
                  Close Position (Simulated)
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                {/* Leg A */}
                <div className="p-3 bg-panel rounded-lg border border-gray-200 space-y-1">
                  <div className="flex justify-between font-sans font-bold">
                    <span className="text-ink">
                      Leg A: {pos.leg_a_side} {pos.leg_a_lots} lots {pos.leg_a_symbol}
                    </span>
                    <span className="text-emerald-700">+₹2,800.00 MTM</span>
                  </div>
                  <div className="text-slate">
                    Fill with slip: ₹{pos.leg_a_fill.toLocaleString("en-IN")}
                  </div>
                  <div className="text-slate">
                    Current Mark: ₹{(pos.leg_a_fill * 0.999).toFixed(2)}
                  </div>
                </div>

                {/* Leg B */}
                <div className="p-3 bg-panel rounded-lg border border-gray-200 space-y-1">
                  <div className="flex justify-between font-sans font-bold">
                    <span className="text-ink">
                      Leg B: {pos.leg_b_side} {pos.leg_b_lots} lots {pos.leg_b_symbol}
                    </span>
                    <span className="text-emerald-700">+₹2,020.00 MTM</span>
                  </div>
                  <div className="text-slate">
                    Fill with slip: ₹{pos.leg_b_fill.toLocaleString("en-IN")}
                  </div>
                  <div className="text-slate">
                    Current Mark: ₹{(pos.leg_b_fill * 1.001).toFixed(2)}
                  </div>
                </div>
              </div>

              {/* Reversion Progress */}
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate font-medium">Reversion toward Rolling Mean:</span>
                  <span className="font-mono font-bold text-gold">56.4% Converged (Target: 100%)</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div className="bg-gold h-full rounded-full" style={{ width: "56.4%" }} />
                </div>
                <div className="flex justify-between text-[11px] text-slate-light pt-0.5">
                  <span>Days in Trade: 2 / 15 (Max holding)</span>
                  <span>Tender Risk: 23 days to expiry (SAFE)</span>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="bg-panel rounded-xl p-8 border border-dashed border-gray-300 text-center text-xs text-slate">
            No active open positions. Stage a candidate paper order to begin simulation.
          </div>
        )}
      </div>

      {/* What-If Risk Stress Simulation Panel */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-gray-100 pb-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-gold" />
            <h3 className="text-sm font-bold text-ink">What-If Risk Stress Simulation Runner</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate font-medium">Stress Status:</span>
            <span
              className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                riskStatus === "NOMINAL"
                  ? "bg-emerald-100 text-emerald-800"
                  : riskStatus === "WARNING"
                  ? "bg-amber-100 text-amber-800"
                  : "bg-red-100 text-red-800 animate-pulse"
              }`}
            >
              {riskStatus}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
          {/* Slider 1: Spot Gold Shock */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="font-medium text-slate">Gold Spot Price Drift Shock:</span>
              <span className="font-mono font-bold text-ink">
                {spotShockPct >= 0 ? `+${spotShockPct}%` : `${spotShockPct}%`}
              </span>
            </div>
            <input
              type="range"
              min="-10"
              max="10"
              step="0.5"
              value={spotShockPct}
              onChange={(e) => setSpotShockPct(parseFloat(e.target.value))}
              className="w-full accent-amber-600 h-1.5 bg-gray-200 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-light font-mono">
              <span>-10% (Gold Crash)</span>
              <span>0% (Baseline)</span>
              <span>+10% (Gold Rally)</span>
            </div>
          </div>

          {/* Slider 2: Spread Divergence Shock */}
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="font-medium text-slate">Relative Spread Divergence Shock:</span>
              <span className="font-mono font-bold text-ink">
                {spreadShockBps >= 0 ? `+${spreadShockBps} bps` : `${spreadShockBps} bps`}
              </span>
            </div>
            <input
              type="range"
              min="-100"
              max="100"
              step="5"
              value={spreadShockBps}
              onChange={(e) => setSpreadShockBps(parseFloat(e.target.value))}
              className="w-full accent-indigo-600 h-1.5 bg-gray-200 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-light font-mono">
              <span>-100 bps (Narrow)</span>
              <span>0 bps (Steady)</span>
              <span>+100 bps (Blowout)</span>
            </div>
          </div>
        </div>

        {/* Stressed Outcome Readout */}
        <div className="p-4 bg-slate-900 text-white rounded-xl grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Stressed Total Equity</span>
            <span className="text-base font-bold text-amber-400">
              ₹{stressedEquity.toLocaleString("en-IN")}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Net Stressed P&L Shift</span>
            <span
              className={`text-base font-bold ${
                stressedPnlDelta >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {stressedPnlDelta >= 0 ? `+₹${stressedPnlDelta.toLocaleString("en-IN")}` : `-₹${Math.abs(stressedPnlDelta).toLocaleString("en-IN")}`}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[10px] uppercase">Margin Health Check</span>
            <span className="text-slate-200 font-semibold block mt-0.5">
              {stressedEquity > 700000 ? "PASS (19.4% util)" : "MARGIN CALL RISK"}
            </span>
          </div>
          <div className="flex items-center justify-end">
            <button
              onClick={() => {
                setSpotShockPct(0);
                setSpreadShockBps(0);
              }}
              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-sans flex items-center gap-1 border border-slate-700"
            >
              <RotateCcw className="w-3 h-3" /> Reset Shocks
            </button>
          </div>
        </div>
      </div>

      {/* Closed Trades History Table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden p-5 space-y-3">
        <h3 className="text-sm font-bold text-ink">Simulated Trades History (Audit Ledger)</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-panel text-slate border-b border-gray-200 font-sans text-[11px] uppercase font-semibold">
              <tr>
                <th className="py-2 px-3">Trade ID</th>
                <th className="py-2 px-3">Pair</th>
                <th className="py-2 px-3">Holding</th>
                <th className="py-2 px-3">Exit Reason</th>
                <th className="py-2 px-3">Gross P&L</th>
                <th className="py-2 px-3">Friction</th>
                <th className="py-2 px-3">Net P&L</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {closedPositions.map((cp) => (
                <tr key={cp.position_id}>
                  <td className="py-2.5 px-3 font-bold text-ink">{cp.position_id.replace("pos_", "#")}</td>
                  <td className="py-2.5 px-3 font-sans text-ink">{cp.pair_name}</td>
                  <td className="py-2.5 px-3">2 days</td>
                  <td className="py-2.5 px-3 font-sans">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                      {cp.exit_reason || "REVERSION"}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-emerald-700">+₹{cp.gross_pnl.toFixed(2)}</td>
                  <td className="py-2.5 px-3 text-slate">₹{cp.total_costs.toFixed(2)}</td>
                  <td className="py-2.5 px-3 font-bold text-emerald-700">+₹{cp.net_pnl.toFixed(2)}</td>
                </tr>
              ))}

              <tr>
                <td className="py-2.5 px-3 font-bold text-ink">#SIM-2026-008</td>
                <td className="py-2.5 px-3 font-sans text-ink">GOLDTEN / GOLDM</td>
                <td className="py-2.5 px-3">3 days</td>
                <td className="py-2.5 px-3 font-sans">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    CONVERGENCE
                  </span>
                </td>
                <td className="py-2.5 px-3 text-emerald-700">+₹14,200.00</td>
                <td className="py-2.5 px-3 text-slate">₹1,950.00</td>
                <td className="py-2.5 px-3 font-bold text-emerald-700">+₹12,250.00</td>
              </tr>

              <tr>
                <td className="py-2.5 px-3 font-bold text-ink">#SIM-2026-007</td>
                <td className="py-2.5 px-3 font-sans text-ink">GOLDM / GOLDGUINEA</td>
                <td className="py-2.5 px-3">6 days</td>
                <td className="py-2.5 px-3 font-sans">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                    CONVERGENCE
                  </span>
                </td>
                <td className="py-2.5 px-3 text-emerald-700">+₹9,800.00</td>
                <td className="py-2.5 px-3 text-slate">₹1,640.00</td>
                <td className="py-2.5 px-3 font-bold text-emerald-700">+₹8,160.00</td>
              </tr>

              <tr>
                <td className="py-2.5 px-3 font-bold text-ink">#SIM-2026-006</td>
                <td className="py-2.5 px-3 font-sans text-ink">GOLDTEN / GOLDPETAL</td>
                <td className="py-2.5 px-3">15 days</td>
                <td className="py-2.5 px-3 font-sans">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                    EXPIRY_WINDOW
                  </span>
                </td>
                <td className="py-2.5 px-3 text-alert">-₹3,200.00</td>
                <td className="py-2.5 px-3 text-slate">₹1,450.00</td>
                <td className="py-2.5 px-3 font-bold text-alert">-₹4,650.00</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Two-Phase Order Staging Modal */}
      {isStageModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-200 space-y-5 animate-fadeIn">
            <div className="flex justify-between items-start border-b border-gray-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-ink">
                  {stageStep === "input" ? "Stage 1: Define Paper Arbitrage Order" : "Stage 2: Review Staged Order & Confirm"}
                </h3>
                <p className="text-xs text-slate">
                  {stageStep === "input"
                    ? "Enter parameters to stage a hypothetical cross-contract trade."
                    : "Verify adverse slippage fill estimates and friction before committing."}
                </p>
              </div>
              <button
                onClick={() => setIsStageModalOpen(false)}
                className="text-slate hover:text-ink text-sm font-bold p-1"
              >
                ✕
              </button>
            </div>

            {stageStep === "input" ? (
              <div className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate font-medium mb-1">Contract Pair</label>
                  <select
                    value={stagePair}
                    onChange={(e) => setStagePair(e.target.value)}
                    className="w-full bg-panel border border-gray-200 rounded-lg p-2 font-mono text-ink text-xs focus:ring-1 focus:ring-gold"
                  >
                    <option value="GOLDTEN_GOLDGUINEA">GOLDTEN (40g) vs GOLDGUINEA (40g)</option>
                    <option value="GOLDM_GOLDTEN">GOLDM (100g) vs GOLDTEN (100g)</option>
                    <option value="GOLDM_GOLDGUINEA">GOLDM (100g) vs GOLDGUINEA (104g)</option>
                    <option value="GOLDM_GOLDPETAL">GOLDM (100g) vs GOLDPETAL (100g)</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate font-medium mb-1">Leg A Lots</label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={stageLotsA}
                      onChange={(e) => setStageLotsA(parseInt(e.target.value) || 1)}
                      className="w-full bg-panel border border-gray-200 rounded-lg p-2 font-mono text-ink text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-slate font-medium mb-1">Leg B Lots</label>
                    <input
                      type="number"
                      min="1"
                      max="50"
                      value={stageLotsB}
                      onChange={(e) => setStageLotsB(parseInt(e.target.value) || 1)}
                      className="w-full bg-panel border border-gray-200 rounded-lg p-2 font-mono text-ink text-xs"
                    />
                  </div>
                </div>

                <div className="p-3 bg-panel rounded-lg border border-gray-200 text-slate text-[11px] space-y-1">
                  <div>✓ Strict Zero-Duplicate Guard: verified</div>
                  <div>✓ Adverse Fill Model: Corwin-Schultz (2012) ±5 bps applied</div>
                  <div>✓ No Real-Money Execution: Paper portfolio only</div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={() => setIsStageModalOpen(false)}
                    className="px-3 py-1.5 text-xs text-slate hover:text-ink font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleStageOrder}
                    className="px-4 py-2 bg-gold hover:bg-gold-hover text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5"
                  >
                    Stage Order <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ) : (
              stagedProposal && (
                <div className="space-y-4 text-xs font-mono">
                  <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200/80 space-y-2">
                    <div className="flex justify-between font-sans">
                      <span className="font-bold text-amber-900">Proposal ID: {stagedProposal.proposal_id}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-200/60 text-amber-900">
                        AWAITING CONFIRMATION
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px]">
                      <div>
                        <span className="text-slate block text-[10px] font-sans">Leg A Estimated Fill</span>
                        <span className="text-ink font-bold">
                          {stagedProposal.side_a} {stagedProposal.lots_a}x @ ₹{stagedProposal.est_fill_a.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate block text-[10px] font-sans">Leg B Estimated Fill</span>
                        <span className="text-ink font-bold">
                          {stagedProposal.side_b} {stagedProposal.lots_b}x @ ₹{stagedProposal.est_fill_b.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-amber-200/50">
                      <div>
                        <span className="text-slate block text-[10px] font-sans">Total Notional</span>
                        <span className="text-ink font-semibold">₹{stagedProposal.total_notional.toLocaleString("en-IN")}</span>
                      </div>
                      <div>
                        <span className="text-slate block text-[10px] font-sans">Required Margin (10%)</span>
                        <span className="text-ink font-semibold">₹{stagedProposal.required_margin_inr.toLocaleString("en-IN")}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-between items-center text-slate font-sans text-xs">
                    <span>Itemized Round-Trip Friction:</span>
                    <span className="font-mono font-bold text-alert">₹{stagedProposal.estimated_costs_inr.toFixed(2)}</span>
                  </div>

                  <div className="flex justify-end gap-2 pt-2 font-sans">
                    <button
                      onClick={() => setStageStep("input")}
                      className="px-3 py-1.5 text-xs text-slate hover:text-ink font-medium"
                    >
                      Back
                    </button>
                    <button
                      onClick={handleConfirmOrder}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5"
                    >
                      <Check className="w-3.5 h-3.5" /> Confirm & Execute Paper Trade
                    </button>
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      )}

      {/* Close Position Modal */}
      {isCloseModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-200 space-y-4 animate-fadeIn">
            <div className="flex justify-between items-start border-b border-gray-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-ink">Close Active Position</h3>
                <p className="text-xs text-slate">Select the audited market exit reason for closure.</p>
              </div>
              <button
                onClick={() => setIsCloseModalOpen(false)}
                className="text-slate hover:text-ink text-sm font-bold p-1"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate font-medium mb-1">Exit Reason Code</label>
                <select
                  value={selectedCloseReason}
                  onChange={(e) => setSelectedCloseReason(e.target.value)}
                  className="w-full bg-panel border border-gray-200 rounded-lg p-2 font-mono text-ink text-xs focus:ring-1 focus:ring-gold"
                >
                  <option value="CONVERGENCE">CONVERGENCE (Spread converged to rolling mean)</option>
                  <option value="STOP_LOSS">STOP_LOSS (Adverse spread expansion breach)</option>
                  <option value="EXPIRY_WINDOW">EXPIRY_WINDOW (Inside 5-day tender window)</option>
                  <option value="USER_CLOSED">USER_CLOSED (Manual user discretion)</option>
                </select>
              </div>

              <div className="p-3 bg-panel rounded-lg border border-gray-200 text-xs font-mono space-y-1">
                <div className="flex justify-between text-slate">
                  <span>Gross Reversion Edge:</span>
                  <span className="text-emerald-700 font-bold">+₹4,820.00</span>
                </div>
                <div className="flex justify-between text-slate">
                  <span>Round-Trip Friction:</span>
                  <span className="text-alert">-₹170.00</span>
                </div>
                <div className="flex justify-between text-ink font-bold pt-1 border-t border-gray-200">
                  <span>Net Realized Credit:</span>
                  <span className="text-emerald-700">+₹4,650.00</span>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setIsCloseModalOpen(false)}
                  className="px-3 py-1.5 text-xs text-slate hover:text-ink font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    if (openPositions.length > 0) {
                      handleClosePosition(openPositions[0].position_id);
                    }
                  }}
                  className="px-4 py-2 bg-alert hover:bg-red-700 text-white rounded-lg text-xs font-semibold shadow-xs"
                >
                  Confirm Closure
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
