import React from 'react';
import {
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  Sparkles,
  AlertTriangle,
  Plus,
  Zap,
  CheckCircle,
  Calendar,
  Layers,
  ChevronRight,
  Compass,
} from 'lucide-react';
import { FinancialEarth } from '../components/FinancialEarth.tsx';
import { FinancialState, FinancialNode, FinancialEvent } from '../types.ts';
import { NavRoute } from '../components/Sidebar.tsx';

interface UniverseDashboardProps {
  financialState: FinancialState | null;
  events: FinancialEvent[];
  onNodeClick: (node: FinancialNode) => void;
  onNavigate: (route: NavRoute) => void;
  onOpenIngestion: () => void;
  onOpenCreateGoal: () => void;
  onConfirmEvent: (eventId: string) => void;
  currency?: string;
}

export const UniverseDashboard: React.FC<UniverseDashboardProps> = ({
  financialState,
  events,
  onNodeClick,
  onNavigate,
  onOpenIngestion,
  onOpenCreateGoal,
  onConfirmEvent,
  currency = '₹',
}) => {
  const pendingEvents = events.filter((e) => e.status === 'UNCERTAIN' || e.status === 'LIKELY').slice(0, 4);
  const confirmedBalance = financialState?.confirmedBalance ?? 0;
  const healthScore = financialState?.healthScore ?? 85;
  const nodes = financialState?.nodes || [];
  const projectedInflow = financialState?.totalIncome ?? 0;
  const certainOutflows = financialState?.obligations ?? (financialState?.totalExpenses ?? 0);
  const runwayMonths = financialState?.obligations && financialState.obligations > 0
    ? (confirmedBalance / financialState.obligations).toFixed(1)
    : (confirmedBalance > 0 ? '12+' : '0.0');

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* 1. Top HUD Overview Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Confirmed Net Worth */}
        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-cyan-400 relative overflow-hidden group hover:border-cyan-400/50 transition-all">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Confirmed Assets</span>
            <span className="p-1 rounded-lg bg-cyan-500/10 text-cyan-400">
              <ShieldCheck className="w-3.5 h-3.5" />
            </span>
          </div>
          <div className="text-2xl lg:text-3xl font-extrabold text-white font-heading tracking-tight data-mono">
            {currency}{confirmedBalance.toLocaleString('en-IN')}
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-400">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Verified from append-only ledger</span>
          </div>
        </div>

        {/* Metric 2: Monthly Inflows */}
        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-emerald-400 relative overflow-hidden group hover:border-emerald-400/50 transition-all">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Projected Inflow</span>
            <span className="p-1 rounded-lg bg-emerald-500/10 text-emerald-400">
              <TrendingUp className="w-3.5 h-3.5" />
            </span>
          </div>
          <div className="text-2xl lg:text-3xl font-extrabold text-white font-heading tracking-tight data-mono">
            {currency}{projectedInflow.toLocaleString('en-IN')}
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
            <span>Reliability:</span>
            <span className="text-emerald-300 font-semibold">Active Streams</span>
          </div>
        </div>

        {/* Metric 3: Certain Outflows */}
        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-pink-400 relative overflow-hidden group hover:border-pink-400/50 transition-all">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Certain Outflows</span>
            <span className="p-1 rounded-lg bg-pink-500/10 text-pink-400">
              <TrendingDown className="w-3.5 h-3.5" />
            </span>
          </div>
          <div className="text-2xl lg:text-3xl font-extrabold text-white font-heading tracking-tight data-mono">
            {currency}{certainOutflows.toLocaleString('en-IN')}
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400">
            <span>Monthly commitments</span>
          </div>
        </div>

        {/* Metric 4: Health Index / Runway */}
        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-[#b600f8] relative overflow-hidden group hover:border-[#b600f8]/50 transition-all">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider text-[11px]">Financial Health</span>
            <span className="p-1 rounded-lg bg-[#b600f8]/20 text-[#ebb2ff]">
              <Sparkles className="w-3.5 h-3.5" />
            </span>
          </div>
          <div className="text-2xl lg:text-3xl font-extrabold text-[#ebb2ff] font-heading tracking-tight data-mono flex items-baseline gap-1">
            {healthScore}
            <span className="text-sm font-normal text-slate-400">/100</span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-cyan-300 font-medium">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>Runway: {runwayMonths} months</span>
          </div>
        </div>
      </div>

      {/* 2. Hero 3D Financial Earth Section */}
      <div className="glass-surface rounded-3xl border border-cyan-500/20 overflow-hidden relative shadow-[0_0_80px_rgba(0,242,255,0.12)]">
        {/* Corner HUD tags */}
        <div className="absolute top-4 left-4 z-20 flex items-center gap-2">
          <div className="px-3 py-1 rounded-full bg-cyan-950/70 border border-cyan-400/30 text-cyan-300 text-xs font-semibold flex items-center gap-1.5 backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>AstraFlow Living Financial Earth</span>
          </div>
          <span className="text-[11px] text-slate-400 hidden sm:inline-block">
            {nodes.length} Orbiting Financial Entities
          </span>
        </div>

        <div className="absolute top-4 right-4 z-20 flex items-center gap-2">
          <button
            type="button"
            onClick={onOpenIngestion}
            className="px-3 py-1.5 rounded-xl bg-cyan-400/15 hover:bg-cyan-400/25 border border-cyan-400/40 text-cyan-200 text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Ingest Data</span>
          </button>
          <button
            type="button"
            onClick={onOpenCreateGoal}
            className="px-3 py-1.5 rounded-xl bg-[#b600f8]/20 hover:bg-[#b600f8]/30 border border-[#b600f8]/40 text-[#ebb2ff] text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>New Goal</span>
          </button>
        </div>

        {/* 3D WebGL Canvas */}
        <div className="h-[460px] md:h-[520px] w-full">
          <FinancialEarth
            nodes={nodes}
            confirmedBalance={confirmedBalance}
            currency={currency}
            onNodeClick={onNodeClick}
          />
        </div>

        {/* Bottom Legend Pill */}
        <div className="p-3.5 bg-[#050816]/80 border-t border-white/5 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
              Node Trajectories:
            </span>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#00f2ff]" />
              <span className="text-slate-300">Income Inflow</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-pink-500 shadow-[0_0_6px_#ff007f]" />
              <span className="text-slate-300">Expenses</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500 shadow-[0_0_6px_#b600f8]" />
              <span className="text-slate-300">Goals</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-[0_0_6px_#f59e0b] animate-pulse" />
              <span className="text-slate-300">Uncertain Pending</span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onNavigate('financial-twin')}
            className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1 text-xs"
          >
            <span>Inspect Twin Architecture</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 3. Lower Dual Bento: Pending Truth Stream & Cosmic Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Financial Events Truth Stream */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400">
                <Calendar className="w-4 h-4" />
              </span>
              <div>
                <h3 className="font-bold text-white font-heading text-sm">Truth Layer Verification Stream</h3>
                <p className="text-xs text-slate-400">Pending events requiring user confirmation or audit</p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onNavigate('events')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1"
            >
              <span>View All Events ({events.length})</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Event Cards */}
          <div className="space-y-2.5">
            {pendingEvents.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                All events verified. Universe is in mathematical synchronization.
              </div>
            ) : (
              pendingEvents.map((evt) => (
                <div
                  key={evt.id}
                  className="p-3.5 rounded-xl bg-white/[0.03] border border-white/5 hover:border-cyan-500/30 transition-all flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                        evt.status === 'UNCERTAIN'
                          ? 'bg-amber-500/15 text-amber-300'
                          : 'bg-cyan-500/15 text-cyan-300'
                      }`}
                    >
                      {evt.type === 'INCOME' ? (
                        <TrendingUp className="w-4 h-4" />
                      ) : (
                        <TrendingDown className="w-4 h-4" />
                      )}
                    </div>
                    <div className="overflow-hidden">
                      <div className="text-sm font-semibold text-white truncate flex items-center gap-2">
                        <span>{evt.title}</span>
                        <span
                          className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full uppercase ${
                            evt.status === 'UNCERTAIN'
                              ? 'bg-amber-500/20 text-amber-300'
                              : 'bg-cyan-500/20 text-cyan-300'
                          }`}
                        >
                          {evt.status}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                        <span>{evt.category}</span>
                        <span>•</span>
                        <span>Source: {evt.source}</span>
                        <span>•</span>
                        <span className="text-cyan-400">{Math.round(evt.confidence * 100)}% Match</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 flex-shrink-0">
                    <div className="text-right">
                      <div
                        className={`text-sm font-bold data-mono ${
                          evt.type === 'INCOME' ? 'text-emerald-400' : 'text-slate-200'
                        }`}
                      >
                        {evt.type === 'INCOME' ? '+' : '-'}
                        {currency}{evt.amount.toLocaleString('en-IN')}
                      </div>
                      <div className="text-[10px] text-slate-500">{evt.date}</div>
                    </div>

                    {evt.status !== 'CONFIRMED' && (
                      <button
                        type="button"
                        onClick={() => onConfirmEvent(evt.id)}
                        className="px-2.5 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center gap-1 border border-emerald-500/30 transition-colors"
                        title="Confirm as verified truth"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">Confirm</span>
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right 1 Col: Cosmic Insights & Quick Navigation */}
        <div className="glass-panel p-5 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-[#b600f8]/20 text-[#ebb2ff]">
                <Compass className="w-4 h-4" />
              </span>
              <h3 className="font-bold text-white font-heading text-sm">Cosmic Portals</h3>
            </div>
          </div>

          <div className="space-y-2">
            <button
              type="button"
              onClick={() => onNavigate('cash-flow')}
              className="w-full p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:border-cyan-500/30 hover:bg-cyan-500/5 flex items-center justify-between text-left transition-all group"
            >
              <div>
                <div className="text-xs font-bold text-white group-hover:text-cyan-300">
                  Cash Flow Simulation
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  12-month forward predictive liquidity curve
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-300 group-hover:translate-x-0.5 transition-transform" />
            </button>

            <button
              type="button"
              onClick={() => onNavigate('income')}
              className="w-full p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:border-emerald-500/30 hover:bg-emerald-500/5 flex items-center justify-between text-left transition-all group"
            >
              <div>
                <div className="text-xs font-bold text-white group-hover:text-emerald-300">
                  Income Reliability Matrix
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Variance coefficient & observation history
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-emerald-300 group-hover:translate-x-0.5 transition-transform" />
            </button>

            <button
              type="button"
              onClick={() => onNavigate('goals')}
              className="w-full p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:border-[#b600f8]/30 hover:bg-[#b600f8]/5 flex items-center justify-between text-left transition-all group"
            >
              <div>
                <div className="text-xs font-bold text-white group-hover:text-[#ebb2ff]">
                  Goals Galaxy Exploration
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Orbiting milestone planets & required velocity
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-[#ebb2ff] group-hover:translate-x-0.5 transition-transform" />
            </button>

            <button
              type="button"
              onClick={() => onNavigate('provenance')}
              className="w-full p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:border-cyan-500/30 hover:bg-cyan-500/5 flex items-center justify-between text-left transition-all group"
            >
              <div>
                <div className="text-xs font-bold text-white group-hover:text-cyan-300">
                  Provenance & Evidence Tree
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5">
                  Trace any number back to raw statements
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-300 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          {/* AI Observation Card */}
          <div className="p-3.5 rounded-xl bg-gradient-to-br from-cyan-950/40 via-[#070b1f] to-[#b600f8]/20 border border-cyan-500/20 space-y-2">
            <div className="flex items-center gap-1.5 text-xs text-cyan-300 font-bold">
              <Sparkles className="w-3.5 h-3.5 text-[#ebb2ff]" />
              <span>Astra Intelligence Note</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Your primary salary stream (Infosys) displays a 98% reliability score with zero variance. Your Emergency Fund goal planet is on track for completion 3 months ahead of schedule.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
