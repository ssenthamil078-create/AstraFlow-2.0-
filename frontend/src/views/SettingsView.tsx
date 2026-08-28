import React, { useState } from 'react';
import {
  Settings,
  Sparkles,
  Database,
  Shield,
  Download,
  Check,
  RefreshCw,
} from 'lucide-react';
import { UserProfile } from '../types.ts';

interface SettingsViewProps {
  user: UserProfile | null;
  currency: string;
  onChangeCurrency: (c: string) => void;
  onSeedDemo: () => void;
  onResetDemo: () => void;
  onExportData: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  user,
  currency,
  onChangeCurrency,
  onSeedDemo,
  onResetDemo,
  onExportData,
}) => {
  const [autonomy, setAutonomy] = useState<'ASSISTED' | 'SUPERVISED' | 'AUTOPILOT'>('SUPERVISED');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const currencies = [
    { symbol: '₹', code: 'INR', name: 'Indian Rupee' },
    { symbol: '$', code: 'USD', name: 'US Dollar' },
    { symbol: '€', code: 'EUR', name: 'Euro' },
    { symbol: '£', code: 'GBP', name: 'British Pound' },
  ];

  const handleCurrencySelect = (sym: string) => {
    onChangeCurrency(sym);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-heading">
          System Preferences
        </span>
        <h2 className="text-2xl font-extrabold text-white font-heading tracking-tight">
          AstraFlow Engine Settings
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Configure financial twin parameters, currency representations, and autonomous agent rules
        </p>
      </div>

      {savedSuccess && (
        <div className="p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
          <Check className="w-4 h-4" />
          <span>Settings successfully synchronized with local state!</span>
        </div>
      )}

      {/* Currency Preferences */}
      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <h3 className="text-base font-bold text-white font-heading">Base Financial Currency</h3>
        <p className="text-xs text-slate-400">
          Select the primary unit of account for the Financial Earth and Twin projections.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {currencies.map((c) => (
            <button
              key={c.code}
              type="button"
              onClick={() => handleCurrencySelect(c.symbol)}
              className={`p-3.5 rounded-2xl border text-left transition-all ${
                currency === c.symbol
                  ? 'bg-cyan-500/15 border-cyan-400 text-white shadow-[0_0_15px_rgba(0,242,255,0.2)]'
                  : 'bg-white/5 border-white/5 text-slate-300 hover:border-white/20'
              }`}
            >
              <div className="text-2xl font-bold font-mono text-cyan-300 mb-1">{c.symbol}</div>
              <div className="text-xs font-bold text-white">{c.code}</div>
              <div className="text-[10px] text-slate-400">{c.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* AI Autonomy Mode */}
      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <h3 className="text-base font-bold text-white font-heading">Astra AI Autonomy Policy</h3>
        <p className="text-xs text-slate-400">
          Define the level of autonomy granted to Astra Copilot when classifying incoming SMS and bank feeds.
        </p>

        <div className="space-y-3">
          {[
            {
              id: 'ASSISTED',
              title: 'Assisted (Human Verification Required)',
              desc: 'Astra flags events but never marks them confirmed without explicit manual click.',
            },
            {
              id: 'SUPERVISED',
              title: 'Supervised (High Confidence Auto-Confirm)',
              desc: 'Transactions with >95% confidence from verified banks are confirmed; uncertain are highlighted.',
            },
            {
              id: 'AUTOPILOT',
              title: 'Autonomous Twin Synchronization',
              desc: 'Continuously updates the living twin and goals orbits automatically in real-time.',
            },
          ].map((mode) => (
            <div
              key={mode.id}
              onClick={() => setAutonomy(mode.id as any)}
              className={`p-4 rounded-2xl border cursor-pointer transition-all flex items-start gap-3 ${
                autonomy === mode.id
                  ? 'bg-[#b600f8]/15 border-[#b600f8] text-white'
                  : 'bg-white/5 border-white/5 text-slate-400 hover:border-white/20'
              }`}
            >
              <input
                type="radio"
                name="autonomy"
                checked={autonomy === mode.id}
                onChange={() => setAutonomy(mode.id as any)}
                className="mt-1 accent-[#b600f8]"
              />
              <div>
                <div className="text-xs font-bold text-white">{mode.title}</div>
                <div className="text-[11px] text-slate-400 mt-0.5">{mode.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Data Management & Sandbox */}
      <div className="glass-panel p-6 rounded-3xl space-y-4 border-rose-500/20">
        <h3 className="text-base font-bold text-white font-heading">Portfolio Sandbox & Data Controls</h3>
        <p className="text-xs text-slate-400">
          Quickly switch between Nisha Patel's rich demonstration universe or start from a clean slate.
        </p>

        <div className="flex flex-wrap gap-3 pt-2">
          <button
            type="button"
            onClick={onSeedDemo}
            className="px-4 py-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-xs font-semibold flex items-center gap-2 border border-cyan-500/30 transition-colors"
          >
            <Sparkles className="w-4 h-4 text-cyan-300" />
            <span>Load Demo Portfolio (Nisha Patel)</span>
          </button>

          <button
            type="button"
            onClick={onExportData}
            className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white text-xs font-semibold flex items-center gap-2 border border-white/10 transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Export State JSON</span>
          </button>

          <button
            type="button"
            onClick={onResetDemo}
            className="px-4 py-2 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 text-xs font-semibold flex items-center gap-2 border border-rose-500/30 transition-colors"
          >
            <Database className="w-4 h-4" />
            <span>Reset to Clean Slate</span>
          </button>
        </div>
      </div>
    </div>
  );
};
