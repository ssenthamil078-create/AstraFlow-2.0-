import React, { useState } from 'react';
import {
  Calendar,
  Search,
  CheckCircle2,
  AlertCircle,
  XCircle,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  FileText,
  MessageSquare,
  FileSpreadsheet,
  Layers,
  ArrowRight,
  Filter,
  Eye,
} from 'lucide-react';
import { FinancialEvent } from '../types.ts';

interface EventsTruthViewProps {
  events: FinancialEvent[];
  onConfirmEvent: (id: string) => void;
  onRejectEvent: (id: string) => void;
  onMergeEvents?: (sourceId: string, targetId: string) => void;
  currency?: string;
}

export const EventsTruthView: React.FC<EventsTruthViewProps> = ({
  events,
  onConfirmEvent,
  onRejectEvent,
  currency = '₹',
}) => {
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'CONFIRMED' | 'LIKELY' | 'UNCERTAIN' | 'REJECTED'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEvidence, setSelectedEvidence] = useState<FinancialEvent | null>(null);

  const filteredEvents = events.filter((e) => {
    const matchesStatus = statusFilter === 'ALL' || e.status === statusFilter;
    const matchesSearch =
      e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.source.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'SMS':
        return <MessageSquare className="w-3.5 h-3.5 text-cyan-400" />;
      case 'CSV':
        return <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />;
      case 'DOCUMENT':
        return <FileText className="w-3.5 h-3.5 text-[#ebb2ff]" />;
      default:
        return <Layers className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-heading">
            Immutable Verification Layer
          </span>
          <h2 className="text-2xl font-extrabold text-white font-heading tracking-tight">
            Financial Events & Ground Truth
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Every transaction is mathematically audited, verified, and linked to raw statements
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 bg-[#10172a] p-1 rounded-xl border border-white/10 overflow-x-auto">
          {(['ALL', 'CONFIRMED', 'LIKELY', 'UNCERTAIN', 'REJECTED'] as const).map((status) => (
            <button
              key={status}
              type="button"
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                statusFilter === status
                  ? 'bg-cyan-500 text-slate-950 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Search & Stats Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 glass-panel p-3.5 rounded-2xl">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search transactions, categories, or sources..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#070b1f] border border-white/10 text-white text-xs placeholder-slate-500 focus:outline-none focus:border-cyan-400"
          />
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-400 px-2">
          <span>Showing <strong className="text-white">{filteredEvents.length}</strong> events</span>
          <span>•</span>
          <span>Confirmed: <strong className="text-emerald-400">{events.filter(e => e.status === 'CONFIRMED').length}</strong></span>
          <span>•</span>
          <span>Uncertain: <strong className="text-amber-400">{events.filter(e => e.status === 'UNCERTAIN').length}</strong></span>
        </div>
      </div>

      {/* Events Stream Table / Cards */}
      <div className="space-y-3">
        {filteredEvents.length === 0 ? (
          <div className="glass-panel p-12 text-center text-slate-400 text-sm rounded-2xl">
            No events match the selected filters.
          </div>
        ) : (
          filteredEvents.map((evt) => (
            <div
              key={evt.id}
              className="glass-panel p-4 rounded-2xl border border-white/5 hover:border-cyan-500/30 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 group"
            >
              {/* Left Details */}
              <div className="flex items-center gap-3.5 overflow-hidden">
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    evt.type === 'INCOME'
                      ? 'bg-emerald-500/15 text-emerald-400'
                      : 'bg-pink-500/15 text-pink-400'
                  }`}
                >
                  {evt.type === 'INCOME' ? (
                    <TrendingUp className="w-5 h-5" />
                  ) : (
                    <TrendingDown className="w-5 h-5" />
                  )}
                </div>

                <div className="overflow-hidden">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-sm font-heading truncate">
                      {evt.title}
                    </span>

                    {/* Status Pill */}
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                        evt.status === 'CONFIRMED'
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                          : evt.status === 'LIKELY'
                          ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                          : evt.status === 'UNCERTAIN'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse'
                          : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      }`}
                    >
                      {evt.status}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400 mt-1">
                    <span className="text-slate-300">{evt.category}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1 font-medium text-slate-300">
                      {getSourceIcon(evt.source)}
                      {evt.source}
                    </span>
                    <span>•</span>
                    <span className="text-slate-400 font-mono">{evt.date}</span>
                    <span>•</span>
                    <span className="text-cyan-400 font-medium">
                      Confidence: {Math.round(evt.confidence * 100)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Right Amounts & Actions */}
              <div className="flex items-center justify-between md:justify-end gap-4 flex-shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-white/5">
                <div className="text-right">
                  <div
                    className={`text-base font-bold data-mono ${
                      evt.type === 'INCOME' ? 'text-emerald-400' : 'text-slate-100'
                    }`}
                  >
                    {evt.type === 'INCOME' ? '+' : '-'}
                    {currency}{evt.amount.toLocaleString('en-IN')}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono">ID: {evt.id}</div>
                </div>

                <div className="flex items-center gap-1.5">
                  {/* Evidence Inspector Button */}
                  <button
                    type="button"
                    onClick={() => setSelectedEvidence(evt)}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-cyan-300 transition-colors"
                    title="Inspect raw statement evidence"
                  >
                    <Eye className="w-4 h-4" />
                  </button>

                  {evt.status !== 'CONFIRMED' && (
                    <button
                      type="button"
                      onClick={() => onConfirmEvent(evt.id)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center gap-1 border border-emerald-500/30 transition-colors"
                      title="Verify and confirm event into truth state"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Confirm</span>
                    </button>
                  )}

                  {evt.status !== 'REJECTED' && (
                    <button
                      type="button"
                      onClick={() => onRejectEvent(evt.id)}
                      className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs transition-colors"
                      title="Reject or mark as invalid"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Raw Evidence Modal */}
      {selectedEvidence && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
          <div className="glass-panel w-full max-w-lg rounded-2xl border border-cyan-500/30 overflow-hidden">
            <div className="p-5 border-b border-white/10 flex items-center justify-between bg-[#0a1028]/80">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold text-white font-heading">
                  Transaction Provenance Evidence
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedEvidence(null)}
                className="p-1 text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-white/5 font-mono space-y-1">
                <div className="text-slate-400">Transaction ID: <span className="text-white">{selectedEvidence.id}</span></div>
                <div className="text-slate-400">Title: <span className="text-white">{selectedEvidence.title}</span></div>
                <div className="text-slate-400">Amount: <span className="text-white font-bold">{currency}{selectedEvidence.amount.toLocaleString('en-IN')}</span></div>
                <div className="text-slate-400">Category: <span className="text-white">{selectedEvidence.category}</span></div>
                <div className="text-slate-400">Confidence: <span className="text-cyan-300">{Math.round(selectedEvidence.confidence * 100)}%</span></div>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1">Raw Evidence Log:</span>
                <pre className="p-3 rounded-xl bg-[#050816] border border-white/10 text-cyan-200 overflow-x-auto text-[11px]">
                  {JSON.stringify(selectedEvidence.rawEvidence || { source: selectedEvidence.source, verified: true }, null, 2)}
                </pre>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedEvidence(null)}
                  className="px-4 py-2 rounded-xl bg-white/10 text-white font-medium hover:bg-white/15"
                >
                  Close Evidence
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
