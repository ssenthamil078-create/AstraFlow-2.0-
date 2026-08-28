import React, { useState } from 'react';
import {
  Wallet,
  ShieldCheck,
  Zap,
  RefreshCw,
  TrendingDown,
  AlertTriangle,
  Sliders,
  SlidersHorizontal,
  CheckCircle,
} from 'lucide-react';
import { FinancialEarth } from '../components/FinancialEarth.tsx';
import { FinancialState, FinancialNode } from '../types.ts';

interface FinancialTwinViewProps {
  financialState: FinancialState | null;
  onNodeClick: (node: FinancialNode) => void;
  onRebuildTwin: () => void;
  isRebuilding?: boolean;
  currency?: string;
}

export const FinancialTwinView: React.FC<FinancialTwinViewProps> = ({
  financialState,
  onNodeClick,
  onRebuildTwin,
  isRebuilding = false,
  currency = '₹',
}) => {
  // Stress Test Simulation State
  const [incomeCutPercent, setIncomeCutPercent] = useState(0);
  const [expenseHikePercent, setExpenseHikePercent] = useState(0);
  const [delayDays, setDelayDays] = useState(0);

  const baseBalance = financialState?.confirmedBalance ?? 0;
  const baseInflow = financialState?.totalIncome ?? 0;
  const baseOutflow = financialState?.obligations ?? (financialState?.totalExpenses ?? 0);

  // Stressed calculations
  const stressedInflow = Math.round(baseInflow * (1 - incomeCutPercent / 100));
  const stressedOutflow = Math.round(baseOutflow * (1 + expenseHikePercent / 100));
  const stressedNet = stressedInflow - stressedOutflow;
  const stressedRunway = stressedOutflow > 0 ? (baseBalance / stressedOutflow).toFixed(1) : (baseBalance > 0 ? '12+' : '0.0');

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-heading">
            Continuous Digital Twin Simulation
          </span>
          <h2 className="text-2xl font-extrabold text-white font-heading tracking-tight">
            The Living Financial Twin
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time digital simulation of your liquidity, debt obligations, assets, and future horizon
          </p>
        </div>

        <button
          type="button"
          onClick={onRebuildTwin}
          disabled={isRebuilding}
          className="px-4 py-2 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-bold text-xs flex items-center gap-2 transition-all w-fit shadow-[0_0_20px_rgba(0,242,255,0.3)] disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isRebuilding ? 'animate-spin' : ''}`} />
          <span>Synchronize Digital Twin</span>
        </button>
      </div>

      {/* 3D Visual Twin & Stress Testing Dual Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 3D Twin Canvas */}
        <div className="lg:col-span-7 glass-surface rounded-3xl border border-cyan-500/20 overflow-hidden relative shadow-[0_0_50px_rgba(0,242,255,0.1)]">
          <div className="absolute top-4 left-4 z-20">
            <span className="px-3 py-1 rounded-full bg-cyan-950/70 border border-cyan-400/30 text-cyan-300 text-xs font-semibold">
              Live Twin Orbit Map
            </span>
          </div>

          <div className="h-[440px] w-full">
            <FinancialEarth
              nodes={financialState?.nodes || []}
              confirmedBalance={baseBalance}
              currency={currency}
              onNodeClick={onNodeClick}
            />
          </div>
        </div>

        {/* Right Stress Test Cockpit */}
        <div className="lg:col-span-5 glass-panel p-6 rounded-3xl space-y-6">
          <div className="flex items-center gap-2 pb-2 border-b border-white/5">
            <SlidersHorizontal className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="text-base font-bold text-white font-heading">
                Cosmic Stress Test Simulator
              </h3>
              <p className="text-xs text-slate-400">Perturb the twin to assess volatility endurance</p>
            </div>
          </div>

          {/* Slider 1: Inflow Cut */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300 font-medium">Income Shock / Cut</span>
              <span className="text-rose-400 font-bold font-mono">-{incomeCutPercent}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="5"
              value={incomeCutPercent}
              onChange={(e) => setIncomeCutPercent(Number(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
          </div>

          {/* Slider 2: Expense Inflation Hike */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-slate-300 font-medium">Outflow Inflation Hike</span>
              <span className="text-amber-400 font-bold font-mono">+{expenseHikePercent}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              step="5"
              value={expenseHikePercent}
              onChange={(e) => setExpenseHikePercent(Number(e.target.value))}
              className="w-full accent-amber-400 cursor-pointer"
            />
          </div>

          {/* Stressed Outcome Card */}
          <div className="p-4 rounded-2xl bg-[#080d1a] border border-white/10 space-y-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Perturbed Outcome Under Stress
            </span>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-slate-400">Stressed Monthly Inflow:</span>
                <div className="text-sm font-bold text-white font-mono mt-0.5">
                  {currency}{stressedInflow.toLocaleString('en-IN')}
                </div>
              </div>
              <div>
                <span className="text-slate-400">Stressed Commitments:</span>
                <div className="text-sm font-bold text-white font-mono mt-0.5">
                  {currency}{stressedOutflow.toLocaleString('en-IN')}
                </div>
              </div>
              <div>
                <span className="text-slate-400">Net Monthly Buffer:</span>
                <div className={`text-sm font-bold font-mono mt-0.5 ${stressedNet >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {stressedNet >= 0 ? '+' : ''}{currency}{stressedNet.toLocaleString('en-IN')}
                </div>
              </div>
              <div>
                <span className="text-slate-400">Stressed Runway:</span>
                <div className="text-sm font-bold text-cyan-300 font-mono mt-0.5">
                  {stressedRunway} months
                </div>
              </div>
            </div>

            {stressedNet < 0 && (
              <div className="p-2.5 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-[11px] flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>Deficit detected! Emergency Fund activates with {stressedRunway} months safety.</span>
              </div>
            )}
            {stressedNet >= 0 && (
              <div className="p-2.5 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[11px] flex items-center gap-2">
                <CheckCircle className="w-4 h-4 flex-shrink-0" />
                <span>Twin remains solvent and self-sustaining even under stress parameters.</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
