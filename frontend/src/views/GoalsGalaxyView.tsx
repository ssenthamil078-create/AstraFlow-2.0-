import React, { useState } from 'react';
import {
  Sparkles,
  Target,
  Calendar,
  Plus,
  TrendingUp,
  Clock,
  Trash2,
  Edit2,
  CheckCircle,
  AlertCircle,
  Zap,
} from 'lucide-react';
import { FinancialGoal } from '../types.ts';
import { goalsApi } from '../services/goalsApi.ts';

interface GoalsGalaxyViewProps {
  goals: FinancialGoal[];
  onOpenCreateGoal: () => void;
  onRefreshGoals: () => void;
  onDeleteGoal?: (id: string) => void;
  currency?: string;
}

export const GoalsGalaxyView: React.FC<GoalsGalaxyViewProps> = ({
  goals,
  onOpenCreateGoal,
  onRefreshGoals,
  onDeleteGoal,
  currency = '₹',
}) => {
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to retire this goal planet from the galaxy?')) return;
    setDeletingId(id);
    try {
      await goalsApi.deleteGoal(id);
      if (onDeleteGoal) {
        onDeleteGoal(id);
      } else {
        onRefreshGoals();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDeletingId(null);
    }
  };

  const totalTarget = goals.reduce((sum, g) => sum + g.targetAmount, 0);
  const totalSaved = goals.reduce((sum, g) => sum + g.currentAmount, 0);
  const aggregateProgress = totalTarget > 0 ? Math.round((totalSaved / totalTarget) * 100) : 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#ebb2ff] font-heading">
            Orbital Milestones
          </span>
          <h2 className="text-2xl font-extrabold text-white font-heading tracking-tight">
            Goals Galaxy
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Visualize your future milestones as planets orbiting your financial reality with required monthly velocity
          </p>
        </div>

        <button
          type="button"
          onClick={onOpenCreateGoal}
          className="px-4 py-2 rounded-xl bg-[#b600f8] hover:bg-[#a000dc] text-white font-bold text-xs flex items-center gap-2 transition-all w-fit shadow-[0_0_20px_rgba(182,0,248,0.4)]"
        >
          <Plus className="w-4 h-4" />
          <span>Launch Goal Planet</span>
        </button>
      </div>

      {/* Galaxy Aggregate Progress HUD */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-[#b600f8]">
          <span className="text-xs text-slate-400 font-medium">Galaxy Target Capital</span>
          <div className="text-2xl font-bold text-white mt-1 data-mono">
            {currency}{totalTarget.toLocaleString('en-IN')}
          </div>
          <div className="text-xs text-[#ebb2ff] mt-1 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Across {goals.length} planetary objectives</span>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-cyan-400">
          <span className="text-xs text-slate-400 font-medium">Capital Accumulated</span>
          <div className="text-2xl font-bold text-cyan-300 mt-1 data-mono">
            {currency}{totalSaved.toLocaleString('en-IN')}
          </div>
          <div className="text-xs text-cyan-400 mt-1">
            <span>{aggregateProgress}% overall galaxy completion</span>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-2xl border-l-2 border-l-emerald-400">
          <span className="text-xs text-slate-400 font-medium">Required Monthly Orbit Velocity</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1 data-mono">
            {currency}32,500 / mo
          </div>
          <div className="text-xs text-slate-400 mt-1">
            <span>Supported by your discretionary cash flow</span>
          </div>
        </div>
      </div>

      {/* Goal Planets Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {goals.map((goal) => {
          const progress = Math.min(100, Math.round((goal.currentAmount / goal.targetAmount) * 100));
          const colorHex = goal.color || '#b600f8';

          return (
            <div
              key={goal.id}
              className="glass-panel p-5 rounded-2xl border border-white/5 hover:border-cyan-500/40 transition-all flex flex-col justify-between group relative overflow-hidden shadow-lg"
            >
              {/* Planetary Visual Halo Accent */}
              <div
                className="absolute -top-12 -right-12 w-32 h-32 rounded-full opacity-20 blur-2xl pointer-events-none group-hover:opacity-40 transition-opacity"
                style={{ backgroundColor: colorHex }}
              />

              <div>
                {/* Top Row: Category + Priority + Delete */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-3 h-3 rounded-full shadow-[0_0_8px]"
                      style={{ backgroundColor: colorHex, boxShadow: `0 0 8px ${colorHex}` }}
                    />
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-heading">
                      {goal.category}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        goal.priority === 'HIGH'
                          ? 'bg-rose-500/20 text-rose-300'
                          : goal.priority === 'MEDIUM'
                          ? 'bg-amber-500/20 text-amber-300'
                          : 'bg-cyan-500/20 text-cyan-300'
                      }`}
                    >
                      {goal.priority}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDelete(goal.id)}
                      disabled={deletingId === goal.id}
                      className="p-1 text-slate-500 hover:text-rose-400 transition-colors opacity-0 group-hover:opacity-100"
                      title="Retire goal planet"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Goal Title */}
                <h3 className="text-lg font-bold text-white font-heading tracking-tight mb-2">
                  {goal.name}
                </h3>

                {/* Amounts */}
                <div className="flex items-baseline justify-between text-xs mb-3">
                  <span className="text-slate-400 font-medium">Accumulated:</span>
                  <span className="text-white font-bold data-mono text-sm">
                    {currency}{goal.currentAmount.toLocaleString('en-IN')}{' '}
                    <span className="text-slate-500 font-normal">
                      / {currency}{goal.targetAmount.toLocaleString('en-IN')}
                    </span>
                  </span>
                </div>

                {/* Visual Progress Bar */}
                <div className="space-y-1 mb-4">
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400">Completion</span>
                    <span className="font-bold text-white font-mono">{progress}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
                    <div
                      style={{ width: `${progress}%`, backgroundColor: colorHex, boxShadow: `0 0 10px ${colorHex}` }}
                      className="h-full rounded-full transition-all duration-500"
                    />
                  </div>
                </div>
              </div>

              {/* Footer info: Target Horizon */}
              <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Target: {goal.targetDate}</span>
                </span>
                <span className="text-emerald-400 font-medium flex items-center gap-0.5">
                  <Zap className="w-3 h-3" />
                  <span>On Trajectory</span>
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
