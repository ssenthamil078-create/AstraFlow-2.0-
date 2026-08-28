import React from 'react';
import {
  Database,
  Plus,
  FileSpreadsheet,
  MessageSquare,
  FileText,
  ShieldCheck,
  CheckCircle2,
  UploadCloud,
  ArrowUpRight,
} from 'lucide-react';

interface DataSourcesViewProps {
  onOpenIngestion: () => void;
}

export const DataSourcesView: React.FC<DataSourcesViewProps> = ({ onOpenIngestion }) => {
  const connectedSources = [
    {
      id: 'src_hdfc',
      name: 'HDFC Bank (Salary Account)',
      type: 'BANK_ACCOUNT',
      lastSynced: '2 hours ago',
      status: 'ACTIVE',
      eventsCount: 42,
      icon: Database,
    },
    {
      id: 'src_zerodha',
      name: 'Zerodha Broking (Investments)',
      type: 'PORTFOLIO',
      lastSynced: 'Yesterday',
      status: 'ACTIVE',
      eventsCount: 18,
      icon: FileSpreadsheet,
    },
    {
      id: 'src_sms',
      name: 'Android Banking SMS Ingestion Feed',
      type: 'LIVE_FEED',
      lastSynced: '10 mins ago',
      status: 'STREAMING',
      eventsCount: 124,
      icon: MessageSquare,
    },
    {
      id: 'src_docs',
      name: 'Tax Invoices & Statement Documents',
      type: 'DOCUMENTS',
      lastSynced: 'Aug 24, 2026',
      status: 'ACTIVE',
      eventsCount: 15,
      icon: FileText,
    },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-heading">
            Multimodal Data Fabric
          </span>
          <h2 className="text-2xl font-extrabold text-white font-heading tracking-tight">
            Data Sources & Ingestion Center
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Connect external accounts, upload statements, and stream live transaction telemetry
          </p>
        </div>

        <button
          type="button"
          onClick={onOpenIngestion}
          className="px-4 py-2 rounded-xl bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-bold text-xs flex items-center gap-2 transition-all w-fit shadow-[0_0_20px_rgba(0,242,255,0.3)]"
        >
          <Plus className="w-4 h-4" />
          <span>Upload Statement / Evidence</span>
        </button>
      </div>

      {/* Ingestion Methods Banner Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          onClick={onOpenIngestion}
          className="glass-panel p-5 rounded-2xl border border-white/5 hover:border-cyan-500/40 cursor-pointer transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-white text-sm font-heading">Bank Statement CSV</h3>
          <p className="text-xs text-slate-400 mt-1">
            Import multi-month exported CSV or Excel statements from any banking institution.
          </p>
          <div className="mt-3 flex items-center gap-1 text-xs text-cyan-400 font-semibold">
            <span>Import CSV</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </div>
        </div>

        <div
          onClick={onOpenIngestion}
          className="glass-panel p-5 rounded-2xl border border-white/5 hover:border-emerald-500/40 cursor-pointer transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <MessageSquare className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-white text-sm font-heading">SMS Ingestion</h3>
          <p className="text-xs text-slate-400 mt-1">
            Instant parsing of UPI, Debit, and Credit SMS alerts with regex confidence extraction.
          </p>
          <div className="mt-3 flex items-center gap-1 text-xs text-emerald-400 font-semibold">
            <span>Paste SMS</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </div>
        </div>

        <div
          onClick={onOpenIngestion}
          className="glass-panel p-5 rounded-2xl border border-white/5 hover:border-[#b600f8]/40 cursor-pointer transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-[#b600f8]/10 text-[#ebb2ff] flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <FileText className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-white text-sm font-heading">PDF & Documents</h3>
          <p className="text-xs text-slate-400 mt-1">
            Optical character recognition for tax invoices, property deeds, and mutual fund sheets.
          </p>
          <div className="mt-3 flex items-center gap-1 text-xs text-[#ebb2ff] font-semibold">
            <span>Upload Document</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </div>
        </div>
      </div>

      {/* Connected Feeds Table */}
      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <h3 className="text-base font-bold text-white font-heading">Connected Data Feeds</h3>

        <div className="divide-y divide-white/5">
          {connectedSources.map((source) => {
            const Icon = source.icon;
            return (
              <div key={source.id} className="py-3.5 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-white/5 flex items-center justify-center text-cyan-400">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-bold text-white font-heading">{source.name}</div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      Last synchronized: {source.lastSynced} • {source.eventsCount} events created
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {source.status}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
