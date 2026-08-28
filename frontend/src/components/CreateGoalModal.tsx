import React, { useState } from 'react';
import { X, Sparkles, Loader2, Target, Calendar, DollarSign } from 'lucide-react';
import { goalsApi } from '../services/goalsApi.ts';
import { FinancialGoal } from '../types.ts';

interface CreateGoalModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGoalCreated: (goal: FinancialGoal) => void;
}

export const CreateGoalModal: React.FC<CreateGoalModalProps> = ({
  isOpen,
  onClose,
  onGoalCreated,
}) => {
  const [name, setName] = useState('');
  const [targetAmount, setTargetAmount] = useState<number | ''>(500000);
  const [currentAmount, setCurrentAmount] = useState<number | ''>(125000);
  const [targetDate, setTargetDate] = useState('2027-06-30');
  const [category, setCategory] = useState('SAVINGS');
  const [priority, setPriority] = useState<'HIGH' | 'MEDIUM' | 'LOW'>('HIGH');
  const [color, setColor] = useState('#b600f8');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const colorPalette = [
    { label: 'Nebula Purple', hex: '#b600f8' },
    { label: 'Electric Cyan', hex: '#00f2ff' },
    { label: 'Starlight Magenta', hex: '#ff007f' },
    { label: 'Aurora Emerald', hex: '#10b981' },
    { label: 'Solar Amber', hex: '#f59e0b' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Please provide a goal name.');
      return;
    }
    if (!targetAmount || Number(targetAmount) <= 0) {
      setError('Please provide a valid target amount.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await goalsApi.createGoal({
        name,
        targetAmount: Number(targetAmount),
        currentAmount: Number(currentAmount) || 0,
        targetDate,
        category,
        priority,
        color,
      });
      onGoalCreated(res.goal);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create goal planet');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
      <div className="glass-panel w-full max-w-lg rounded-2xl border border-[#b600f8]/30 overflow-hidden shadow-[0_0_50px_rgba(182,0,248,0.3)]">
        {/* Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between bg-[#0a1028]/80">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-[#b600f8]/20 text-[#ebb2ff]">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#ebb2ff] font-heading">
                Goals Galaxy
              </span>
              <h3 className="text-lg font-bold text-white font-heading">Construct Goal Planet</h3>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Goal Planet Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., European Sabbatical, Tesla Model Y, Emergency Fund"
              className="w-full p-2.5 rounded-xl bg-[#080d1a] border border-white/10 text-white text-sm focus:outline-none focus:border-[#b600f8]"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Target Amount (₹)</label>
              <input
                type="number"
                required
                value={targetAmount}
                onChange={(e) => setTargetAmount(e.target.value ? Number(e.target.value) : '')}
                className="w-full p-2.5 rounded-xl bg-[#080d1a] border border-white/10 text-white text-sm focus:outline-none focus:border-[#b600f8] font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Currently Saved (₹)</label>
              <input
                type="number"
                value={currentAmount}
                onChange={(e) => setCurrentAmount(e.target.value ? Number(e.target.value) : '')}
                className="w-full p-2.5 rounded-xl bg-[#080d1a] border border-white/10 text-white text-sm focus:outline-none focus:border-[#b600f8] font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Target Horizon Date</label>
              <input
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[#080d1a] border border-white/10 text-white text-sm focus:outline-none focus:border-[#b600f8]"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Priority Trajectory</label>
              <select
                value={priority}
                onChange={(e: any) => setPriority(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[#080d1a] border border-white/10 text-white text-sm focus:outline-none focus:border-[#b600f8]"
              >
                <option value="HIGH">High Priority</option>
                <option value="MEDIUM">Medium Priority</option>
                <option value="LOW">Low Priority</option>
              </select>
            </div>
          </div>

          {/* Planet Orbit Aura */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Planet Spectral Color</label>
            <div className="flex items-center gap-3">
              {colorPalette.map((p) => (
                <button
                  key={p.hex}
                  type="button"
                  onClick={() => setColor(p.hex)}
                  className={`w-8 h-8 rounded-full transition-transform ${
                    color === p.hex ? 'ring-2 ring-white scale-110' : 'opacity-70 hover:opacity-100'
                  }`}
                  style={{ backgroundColor: p.hex, boxShadow: `0 0 10px ${p.hex}` }}
                  title={p.label}
                />
              ))}
            </div>
          </div>

          <div className="pt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-xl bg-[#b600f8] text-white font-bold text-xs hover:bg-[#a000dc] shadow-[0_0_20px_rgba(182,0,248,0.5)] transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating Planet...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Launch Goal Planet
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
