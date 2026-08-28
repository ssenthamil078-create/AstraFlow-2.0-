import React from 'react';
import { X, ShieldCheck, AlertCircle, ArrowUpRight, CheckCircle2, History } from 'lucide-react';
import { FinancialNode } from '../types.ts';

interface NodeDetailModalProps {
  node: FinancialNode | null;
  onClose: () => void;
  onNavigateToEvents?: () => void;
  onNavigateToGoals?: () => void;
  onNavigateToIncome?: () => void;
}

export const NodeDetailModal: React.FC<NodeDetailModalProps> = ({
  node,
  onClose,
  onNavigateToEvents,
  onNavigateToGoals,
  onNavigateToIncome,
}) => {
  if (!node) return null;

  const getStatusBadge = () => {
    switch (node.status) {
      case 'CONFIRMED':
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Confirmed Truth
          </span>
        );
      case 'LIKELY':
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" />
            High Confidence
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1.5 animate-pulse">
            <AlertCircle className="w-3.5 h-3.5" />
            Uncertain / Pending Verification
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
      <div className="glass-panel w-full max-w-lg rounded-2xl border border-cyan-500/30 overflow-hidden shadow-[0_0_50px_rgba(0,242,255,0.25)]">
        {/* Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between bg-[#0a1028]/80">
          <div className="flex items-center gap-3">
            <div
              className="w-4 h-4 rounded-full shadow-[0_0_12px]"
              style={{ backgroundColor: node.color || '#00f2ff', boxShadow: `0 0 12px ${node.color || '#00f2ff'}` }}
            />
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-heading">
                {node.type} NODE
              </span>
              <h3 className="text-lg font-bold text-white font-heading">{node.label}</h3>
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

        {/* Content Body */}
        <div className="p-6 space-y-5">
          {/* Key Metrics Row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
              <span className="text-xs text-slate-400 font-medium">Node Value</span>
              <div className="text-2xl font-bold text-white mt-1 data-mono">
                ₹{node.amount.toLocaleString('en-IN')}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/5">
              <span className="text-xs text-slate-400 font-medium">Verification Status</span>
              <div className="mt-1.5">{getStatusBadge()}</div>
            </div>
          </div>

          {/* Details Table */}
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-2 border-b border-white/5">
              <span className="text-slate-400">Confidence Score</span>
              <span className="text-white font-semibold">{Math.round(node.confidence * 100)}%</span>
            </div>
            <div className="flex justify-between py-2 border-b border-white/5">
              <span className="text-slate-400">Node Archetype</span>
              <span className="text-cyan-300 font-medium">{node.type}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-white/5">
              <span className="text-slate-400">Orbital Trajectory</span>
              <span className="text-slate-300 font-mono">
                Radius {node.orbitRadius?.toFixed(2) || '3.50'} • Speed {node.orbitSpeed?.toFixed(2) || '0.35'}
              </span>
            </div>
            {node.secondaryInfo && (
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-slate-400">Metadata</span>
                <span className="text-slate-300">{node.secondaryInfo}</span>
              </div>
            )}
          </div>

          {/* Provenance note */}
          <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/20 text-xs text-cyan-200/90 leading-relaxed flex items-start gap-2.5">
            <History className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
            <span>
              This node is continuously synchronized with the AstraFlow truth engine. Every state shift is backed by immutable transaction evidence.
            </span>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
            >
              Dismiss
            </button>
            {node.type === 'INCOME' && onNavigateToIncome && (
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onNavigateToIncome();
                }}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all flex items-center gap-1.5"
              >
                Inspect Income Reliability <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            )}
            {node.type === 'GOAL' && onNavigateToGoals && (
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onNavigateToGoals();
                }}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-[#b600f8] text-white hover:bg-[#a000dc] transition-all flex items-center gap-1.5"
              >
                View in Goals Galaxy <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            )}
            {node.type !== 'INCOME' && node.type !== 'GOAL' && onNavigateToEvents && (
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onNavigateToEvents();
                }}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-cyan-500 text-slate-950 hover:bg-cyan-400 transition-all flex items-center gap-1.5"
              >
                Inspect Source Events <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
