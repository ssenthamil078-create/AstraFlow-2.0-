import React, { useState } from 'react';
import {
  CreditCard,
  TrendingUp,
  ShieldCheck,
  AlertCircle,
  Plus,
  RefreshCw,
  Clock,
  Sparkles,
  BarChart,
  CheckCircle2,
  Calendar,
} from 'lucide-react';
import { IncomeSource } from '../types.ts';
import { incomeApi, ReliabilityDetails } from '../services/incomeApi.ts';

interface IncomeReliabilityViewProps {
  incomeSources: IncomeSource[];
  onRefreshSources: () => void;
  currency?: string;
}

export const IncomeReliabilityView: React.FC<IncomeReliabilityViewProps> = ({
  incomeSources,
  onRefreshSources,
  currency = '₹',
}) => {
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [reliabilityData, setReliabilityData] = useState<ReliabilityDetails | null>(null);
  const [loadingReliability, setLoadingReliability] = useState(false);
  const [recalculatingId, setRecalculatingId] = useState<string | null>(null);
  const [isAddOpen, setIsAddOpen] = useState(false);

  // New source form state
  const [newName, setNewName] = useState('');
  const [newAmount, setNewAmount] = useState<number | ''>(65000);
  const [newCategory, setNewCategory] = useState('salaried_employer');
  const [newFrequency, setNewFrequency] = useState('MONTHLY');
  const [creating, setCreating] = useState(false);

  const handleInspect = async (id: string) => {
    setSelectedSourceId(id);
    setLoadingReliability(true);
    try {
      const data = await incomeApi.getReliability(id);
      setReliabilityData(data);
    } catch (err) {
      console.error('Failed to get reliability', err);
    } finally {
      setLoadingReliability(false);
    }
  };

  const handleRecalculate = async (id: string) => {
    setRecalculatingId(id);
    try {
      await incomeApi.recalculateReliability(id);
      onRefreshSources();
      if (selectedSourceId === id) {
        handleInspect(id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setRecalculatingId(null);
    }
  };

  const handleCreateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName || !newAmount) return;
    setCreating(true);
    try {
      await incomeApi.createIncomeSource({
        name: newName,
        category: newCategory,
        typicalAmount: Number(newAmount),
        frequency: newFrequency,
      });
      setIsAddOpen(false);
      setNewName('');
      onRefreshSources();
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const totalMonthlyIncome = incomeSources.reduce((acc, curr) => acc + curr.typicalAmount, 0);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 font-heading">
            Probability & Variance Matrix
          </span>
          <h2 className="text-2xl font-extrabold text-white font-heading tracking-tight">
            Income Sources & Reliability
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            AstraFlow rates incoming cash flow confidence using mathematical regularity and timeliness analysis
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsAddOpen(true)}
          className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center gap-2 transition-all w-fit shadow-[0_0_20px_rgba(16,185,129,0.3)]"
        >
          <Plus className="w-4 h-4" />
          <span>Add Income Stream</span>
        </button>
      </div>

      {/* Aggregate Overview HUD */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-emerald-400">
          <span className="text-xs text-slate-400 font-medium">Aggregate Monthly Inflow</span>
          <div className="text-2xl font-bold text-white mt-1 data-mono">
            {currency}{totalMonthlyIncome.toLocaleString('en-IN')}
          </div>
          <div className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Across {incomeSources.length} distinct income streams</span>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-cyan-400">
          <span className="text-xs text-slate-400 font-medium">Weighted Reliability Score</span>
          <div className="text-2xl font-bold text-cyan-300 mt-1 data-mono">
            94.8% <span className="text-xs text-slate-400 font-normal">Established</span>
          </div>
          <div className="text-xs text-cyan-400 mt-1">
            <span>Low default probability detected</span>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-[#b600f8]">
          <span className="text-xs text-slate-400 font-medium">Predictive Safety Buffer</span>
          <div className="text-2xl font-bold text-[#ebb2ff] mt-1 data-mono">
            {currency}1,40,000
          </div>
          <div className="text-xs text-slate-400 mt-1">
            <span>Automated variance cushion</span>
          </div>
        </div>
      </div>

      {/* Income Streams Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {incomeSources.map((source) => {
          const isHighReliability = source.reliabilityScore >= 85;

          return (
            <div
              key={source.id}
              className={`glass-panel p-5 rounded-2xl border transition-all relative overflow-hidden ${
                selectedSourceId === source.id
                  ? 'border-emerald-400/60 shadow-[0_0_30px_rgba(16,185,129,0.2)]'
                  : 'border-white/5 hover:border-white/20'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      isHighReliability ? 'bg-emerald-500/15 text-emerald-400' : 'bg-amber-500/15 text-amber-300'
                    }`}
                  >
                    <CreditCard className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-white font-heading">{source.name}</h4>
                    <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
                      <span>{source.category}</span>
                      <span>•</span>
                      <span className="capitalize">{source.frequency.toLowerCase()}</span>
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-lg font-bold text-white data-mono">
                    {currency}{source.typicalAmount.toLocaleString('en-IN')}
                  </div>
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                      isHighReliability
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'bg-amber-500/20 text-amber-300'
                    }`}
                  >
                    {Math.round(source.reliabilityScore)}% Reliability
                  </span>
                </div>
              </div>

              {/* Reliability Progress Bar */}
              <div className="mt-4 space-y-1">
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>Confidence Level</span>
                  <span className="text-white font-mono">{source.reliabilityScore}%</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-white/10 overflow-hidden">
                  <div
                    style={{ width: `${source.reliabilityScore}%` }}
                    className={`h-full rounded-full ${
                      isHighReliability ? 'bg-emerald-400' : 'bg-amber-400'
                    }`}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                <span className="text-[11px] text-slate-400 flex items-center gap-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  <span>Observed 12 cycles</span>
                </span>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleRecalculate(source.id)}
                    disabled={recalculatingId === source.id}
                    className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-emerald-300 transition-colors"
                    title="Recalculate variance metrics"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${recalculatingId === source.id ? 'animate-spin' : ''}`} />
                  </button>

                  <button
                    type="button"
                    onClick={() => handleInspect(source.id)}
                    className="px-3 py-1 rounded-lg text-xs font-semibold bg-white/5 hover:bg-emerald-500/20 hover:text-emerald-300 text-slate-200 transition-colors"
                  >
                    Inspect Variance
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Source Deep Breakdown Modal / Card */}
      {reliabilityData && (
        <div className="glass-panel p-6 rounded-3xl border border-emerald-400/40 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-white font-heading">
                Reliability Audit: {reliabilityData.source.name}
              </h3>
            </div>
            <button
              type="button"
              onClick={() => setReliabilityData(null)}
              className="text-slate-400 hover:text-white text-xs"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="p-3 rounded-xl bg-white/5">
              <span className="text-slate-400">Timeliness Consistency</span>
              <div className="text-lg font-bold text-emerald-400 mt-1 font-mono">
                {Math.round(reliabilityData.metrics.timeliness * 100)}%
              </div>
            </div>
            <div className="p-3 rounded-xl bg-white/5">
              <span className="text-slate-400">Amount Consistency</span>
              <div className="text-lg font-bold text-cyan-300 mt-1 font-mono">
                {Math.round(reliabilityData.metrics.amountConsistency * 100)}%
              </div>
            </div>
            <div className="p-3 rounded-xl bg-white/5">
              <span className="text-slate-400">Variance Coefficient</span>
              <div className="text-lg font-bold text-white mt-1 font-mono">
                {reliabilityData.metrics.varianceCoefficient}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-white/5">
              <span className="text-slate-400">Observation Count</span>
              <div className="text-lg font-bold text-white mt-1 font-mono">
                {reliabilityData.metrics.observationCount} records
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/20 text-xs text-emerald-200">
            <strong>Astra Recommendation:</strong> {reliabilityData.metrics.recommendation}
          </div>
        </div>
      )}

      {/* Add Income Stream Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
          <div className="glass-panel w-full max-w-md rounded-2xl border border-emerald-500/30 overflow-hidden shadow-[0_0_50px_rgba(16,185,129,0.2)]">
            <div className="p-5 border-b border-white/10 flex items-center justify-between bg-[#0a1028]/80">
              <h3 className="text-base font-bold text-white font-heading">Register Income Stream</h3>
              <button
                type="button"
                onClick={() => setIsAddOpen(false)}
                className="p-1 text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSource} className="p-6 space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Source / Employer Name</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Google India, Upwork Consulting, Freelance"
                  className="w-full p-2.5 rounded-xl bg-[#080d1a] border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-400"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Typical Inflow Amount ({currency})</label>
                <input
                  type="number"
                  required
                  value={newAmount}
                  onChange={(e) => setNewAmount(e.target.value ? Number(e.target.value) : '')}
                  className="w-full p-2.5 rounded-xl bg-[#080d1a] border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-400 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[#080d1a] border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-400"
                  >
                    <option value="salaried_employer">Salary / Employer</option>
                    <option value="freelance_client">Freelance / Consulting</option>
                    <option value="platform_gig">Gig / Platform Payout</option>
                    <option value="rental_income">Rental Income</option>
                    <option value="investment_return">Investment / Dividends</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Frequency</label>
                  <select
                    value={newFrequency}
                    onChange={(e) => setNewFrequency(e.target.value)}
                    className="w-full p-2.5 rounded-xl bg-[#080d1a] border border-white/10 text-white text-xs focus:outline-none focus:border-emerald-400"
                  >
                    <option value="MONTHLY">Monthly</option>
                    <option value="BIWEEKLY">Bi-weekly</option>
                    <option value="QUARTERLY">Quarterly</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 rounded-xl bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400 transition-colors"
                >
                  {creating ? 'Registering...' : 'Register Stream'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
