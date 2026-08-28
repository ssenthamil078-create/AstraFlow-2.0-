import React, { useState, useEffect } from 'react';
import {
  Search,
  Globe,
  Wallet,
  ArrowLeftRight,
  Calendar,
  Sparkles,
  Database,
  History,
  CreditCard,
  Settings,
  Bot,
  Plus,
  RefreshCw,
  X,
} from 'lucide-react';
import { NavRoute } from './Sidebar.tsx';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (route: NavRoute) => void;
  onOpenAstra: () => void;
  onOpenAddDataSource: () => void;
  onOpenCreateGoal: () => void;
  onRebuildTwin: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onNavigate,
  onOpenAstra,
  onOpenAddDataSource,
  onOpenCreateGoal,
  onRebuildTwin,
}) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onClose(); // parent handles toggling
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const commands = [
    {
      id: 'cmd_universe',
      title: 'Navigate to Universe (Dashboard)',
      category: 'Navigation',
      icon: Globe,
      action: () => {
        onNavigate('dashboard');
        onClose();
      },
    },
    {
      id: 'cmd_twin',
      title: 'View Financial Twin Model',
      category: 'Navigation',
      icon: Wallet,
      action: () => {
        onNavigate('financial-twin');
        onClose();
      },
    },
    {
      id: 'cmd_cashflow',
      title: 'Inspect Cash Flow Intelligence',
      category: 'Navigation',
      icon: ArrowLeftRight,
      action: () => {
        onNavigate('cash-flow');
        onClose();
      },
    },
    {
      id: 'cmd_events',
      title: 'Review Financial Events & Truth Layer',
      category: 'Navigation',
      icon: Calendar,
      action: () => {
        onNavigate('events');
        onClose();
      },
    },
    {
      id: 'cmd_goals',
      title: 'Explore Goals Galaxy',
      category: 'Navigation',
      icon: Sparkles,
      action: () => {
        onNavigate('goals');
        onClose();
      },
    },
    {
      id: 'cmd_income',
      title: 'Income Sources & Reliability Scores',
      category: 'Navigation',
      icon: CreditCard,
      action: () => {
        onNavigate('income');
        onClose();
      },
    },
    {
      id: 'cmd_datasources',
      title: 'Data Sources & Ingestion Center',
      category: 'Navigation',
      icon: Database,
      action: () => {
        onNavigate('data-sources');
        onClose();
      },
    },
    {
      id: 'cmd_provenance',
      title: 'Financial Evidence & Provenance Tree',
      category: 'Navigation',
      icon: History,
      action: () => {
        onNavigate('provenance');
        onClose();
      },
    },
    {
      id: 'cmd_add_data',
      title: 'Import Bank Statement (CSV / SMS / Document)',
      category: 'Quick Actions',
      icon: Plus,
      action: () => {
        onOpenAddDataSource();
        onClose();
      },
    },
    {
      id: 'cmd_create_goal',
      title: 'Create a New Financial Goal Planet',
      category: 'Quick Actions',
      icon: Plus,
      action: () => {
        onOpenCreateGoal();
        onClose();
      },
    },
    {
      id: 'cmd_rebuild',
      title: 'Rebuild Financial Twin (Recalibrate Nodes)',
      category: 'Quick Actions',
      icon: RefreshCw,
      action: () => {
        onRebuildTwin();
        onClose();
      },
    },
    {
      id: 'cmd_ask_astra',
      title: 'Open Astra Copilot (Ask Financial AI)',
      category: 'AI Copilot',
      icon: Bot,
      action: () => {
        onOpenAstra();
        onClose();
      },
    },
  ];

  const filteredCommands = commands.filter(
    (c) =>
      c.title.toLowerCase().includes(query.toLowerCase()) ||
      c.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-150">
      <div className="glass-panel w-full max-w-xl rounded-2xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.8)] border border-cyan-500/30">
        {/* Input Header */}
        <div className="p-4 border-b border-white/10 flex items-center gap-3 bg-[#0a1028]/90">
          <Search className="w-5 h-5 text-cyan-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search financial universe..."
            autoFocus
            className="flex-1 bg-transparent border-none text-white text-base placeholder-slate-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-[360px] overflow-y-auto p-2 space-y-1">
          {filteredCommands.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-sm">
              No matching commands or entities found.
            </div>
          ) : (
            filteredCommands.map((cmd) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={cmd.id}
                  type="button"
                  onClick={cmd.action}
                  className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl hover:bg-cyan-500/15 text-slate-200 hover:text-white group transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 rounded-lg bg-white/5 border border-white/10 group-hover:border-cyan-400/50 group-hover:text-cyan-300">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-medium">{cmd.title}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono px-2 py-0.5 rounded bg-white/5 uppercase">
                    {cmd.category}
                  </span>
                </button>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className="px-4 py-2 bg-[#050816] border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400">
          <span>Navigate with mouse or enter</span>
          <span>ESC to close</span>
        </div>
      </div>
    </div>
  );
};
