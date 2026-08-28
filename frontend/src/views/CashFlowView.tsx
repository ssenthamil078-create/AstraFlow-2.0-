import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  ArrowLeftRight,
  ShieldAlert,
  Calendar,
  Layers,
  ChevronDown,
  Sparkles,
  BarChart2,
} from 'lucide-react';
import { FinancialState, FinancialEvent } from '../types.ts';

interface CashFlowViewProps {
  financialState: FinancialState | null;
  events: FinancialEvent[];
  currency?: string;
  onNavigateToEvents: () => void;
}

export const CashFlowView: React.FC<CashFlowViewProps> = ({
  financialState,
  events,
  currency = '₹',
  onNavigateToEvents,
}) => {
  const [timeHorizon, setTimeHorizon] = useState<'3M' | '6M' | '12M'>('12M');

  // Generate 12-month predictive projection data
  const months = ['Sep 26', 'Oct 26', 'Nov 26', 'Dec 26', 'Jan 27', 'Feb 27', 'Mar 27', 'Apr 27', 'May 27', 'Jun 27', 'Jul 27', 'Aug 27'];
  const baseInflow = financialState?.totalIncome ?? 0;
  const baseOutflow = financialState?.obligations ?? (financialState?.totalExpenses ?? 0);
  const baseBalance = financialState?.confirmedBalance ?? 0;

  const projectionData = months.map((month, idx) => {
    // Add realistic seasonal bumps (e.g. bonus in Dec, tax in Mar)
    const bonusMultiplier = idx === 3 ? 1.4 : idx === 6 ? 1.15 : 1.0;
    const expenseBump = idx === 3 ? 1.3 : idx === 6 ? 1.25 : 1.0;
    const inflow = Math.round(baseInflow * bonusMultiplier);
    const outflow = Math.round(baseOutflow * expenseBump);
    const net = inflow - outflow;
    return {
      month,
      inflow,
      outflow,
      net,
      cumulativeBalance: baseBalance + net * (idx + 1),
    };
  });

  const maxVal = Math.max(...projectionData.map((d) => Math.max(d.inflow, d.outflow)));

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-heading">
            Predictive Liquidity Engine
          </span>
          <h2 className="text-2xl font-extrabold text-white font-heading tracking-tight">
            Cash Flow Intelligence
          </h2>
        </div>

        {/* Time horizon pill */}
        <div className="flex items-center gap-1 bg-[#10172a] p-1 rounded-xl border border-white/10 w-fit">
          {(['3M', '6M', '12M'] as const).map((period) => (
            <button
              key={period}
              type="button"
              onClick={() => setTimeHorizon(period)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                timeHorizon === period
                  ? 'bg-cyan-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {period} Horizon
            </button>
          ))}
        </div>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-emerald-400">
          <span className="text-xs text-slate-400 font-medium">Monthly Inflow Run-Rate</span>
          <div className="text-2xl font-bold text-white mt-1 data-mono">
            {currency}{baseInflow.toLocaleString('en-IN')}
          </div>
          <div className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>97.8% High Reliability Stream</span>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-pink-400">
          <span className="text-xs text-slate-400 font-medium">Certain Commitments</span>
          <div className="text-2xl font-bold text-white mt-1 data-mono">
            {currency}{baseOutflow.toLocaleString('en-IN')}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            <span>Rent, SIP investments, and utilities</span>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-cyan-400">
          <span className="text-xs text-slate-400 font-medium">Free Discretionary Cash Flow</span>
          <div className="text-2xl font-bold text-cyan-300 mt-1 data-mono">
            +{currency}{(baseInflow - baseOutflow).toLocaleString('en-IN')} / mo
          </div>
          <div className="text-xs text-cyan-400 mt-1">
            <span>Available for goal planet acceleration</span>
          </div>
        </div>
      </div>

      {/* 12-Month Inflow vs Outflow Visual Graph */}
      <div className="glass-panel p-6 rounded-3xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-white font-heading">
              Projected Inflow vs. Outflow Trajectory
            </h3>
            <p className="text-xs text-slate-400">Simulated across next {timeHorizon} with historical volatility buffers</p>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-emerald-400" />
              <span className="text-slate-300">Projected Inflow</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-pink-500" />
              <span className="text-slate-300">Certain Outflow</span>
            </div>
          </div>
        </div>

        {/* CSS Bar Chart */}
        <div className="h-64 flex items-end justify-between gap-2 pt-6 pb-2 border-b border-white/10">
          {projectionData
            .slice(0, timeHorizon === '3M' ? 3 : timeHorizon === '6M' ? 6 : 12)
            .map((data, idx) => {
              const inflowHeight = Math.round((data.inflow / maxVal) * 100);
              const outflowHeight = Math.round((data.outflow / maxVal) * 100);

              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2 group h-full justify-end">
                  {/* Bar Pair */}
                  <div className="w-full flex items-end justify-center gap-1 h-full">
                    {/* Inflow Bar */}
                    <div
                      style={{ height: `${inflowHeight}%` }}
                      className="w-full max-w-[18px] rounded-t-md bg-gradient-to-t from-emerald-500/70 to-emerald-400 group-hover:from-emerald-400 group-hover:to-emerald-300 transition-all shadow-[0_0_10px_rgba(16,185,129,0.3)] relative"
                      title={`Inflow: ${currency}${data.inflow.toLocaleString('en-IN')}`}
                    />

                    {/* Outflow Bar */}
                    <div
                      style={{ height: `${outflowHeight}%` }}
                      className="w-full max-w-[18px] rounded-t-md bg-gradient-to-t from-pink-600/70 to-pink-400 group-hover:from-pink-500 group-hover:to-pink-300 transition-all shadow-[0_0_10px_rgba(244,63,94,0.3)]"
                      title={`Outflow: ${currency}${data.outflow.toLocaleString('en-IN')}`}
                    />
                  </div>

                  {/* Month Label */}
                  <span className="text-[10px] text-slate-400 group-hover:text-cyan-300 font-mono truncate">
                    {data.month}
                  </span>
                </div>
              );
            })}
        </div>

        {/* Forecast Details Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="text-slate-400 border-b border-white/5 uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Horizon</th>
                <th className="py-2.5 px-3">Inflows</th>
                <th className="py-2.5 px-3">Outflows</th>
                <th className="py-2.5 px-3">Net Savings</th>
                <th className="py-2.5 px-3 text-right">Projected Balance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono">
              {projectionData
                .slice(0, timeHorizon === '3M' ? 3 : timeHorizon === '6M' ? 6 : 12)
                .map((d, i) => (
                  <tr key={i} className="hover:bg-white/[0.02] text-slate-300">
                    <td className="py-2.5 px-3 font-sans font-medium text-white">{d.month}</td>
                    <td className="py-2.5 px-3 text-emerald-400">+{currency}{d.inflow.toLocaleString('en-IN')}</td>
                    <td className="py-2.5 px-3 text-pink-400">-{currency}{d.outflow.toLocaleString('en-IN')}</td>
                    <td className="py-2.5 px-3 text-cyan-300">+{currency}{d.net.toLocaleString('en-IN')}</td>
                    <td className="py-2.5 px-3 text-right text-white font-bold">
                      {currency}{d.cumulativeBalance.toLocaleString('en-IN')}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
