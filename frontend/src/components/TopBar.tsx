import React from 'react';
import { Menu, Search, Bell, Sparkles, RefreshCw, Database } from 'lucide-react';
import { UserProfile } from '../types.ts';

interface TopBarProps {
  title: string;
  user: UserProfile | null;
  onToggleMobileMenu: () => void;
  onOpenSearch: () => void;
  onOpenAstra: () => void;
  onRebuildTwin?: () => void;
  onSeedDemo?: () => void;
  onResetDemo?: () => void;
  isRebuilding?: boolean;
  alertsCount?: number;
  sidebarCollapsed: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  title,
  user,
  onToggleMobileMenu,
  onOpenSearch,
  onOpenAstra,
  onRebuildTwin,
  onSeedDemo,
  onResetDemo,
  isRebuilding = false,
  alertsCount = 0,
  sidebarCollapsed,
}) => {
  return (
    <header
      className={`fixed top-0 right-0 h-16 z-40 transition-all duration-300 ease-in-out
        bg-[#070b1f]/80 backdrop-blur-xl border-b border-white/5 flex items-center justify-between px-4 lg:px-8
        ${sidebarCollapsed ? 'left-0 lg:left-20' : 'left-0 lg:left-72'}
      `}
    >
      {/* Left: Mobile Toggle + Title */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 rounded-xl text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <h2 className="text-lg md:text-xl font-bold font-heading text-white tracking-tight flex items-center gap-2">
            {title}
          </h2>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Quick Search / Command Palette Input */}
        <button
          type="button"
          onClick={onOpenSearch}
          className="hidden sm:flex items-center gap-3 px-3.5 py-1.5 rounded-full bg-[#192122]/70 border border-cyan-500/20 text-slate-400 hover:border-cyan-400/50 hover:text-slate-200 transition-all group shadow-sm"
        >
          <Search className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
          <span className="text-xs font-medium pr-2">Ask Astra anything...</span>
          <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-white/10 text-slate-300 font-mono">
            ⌘K
          </kbd>
        </button>

        {/* Demo Controls Pill */}
        <div className="flex items-center gap-1 bg-[#10172a]/80 p-1 rounded-xl border border-white/10">
          {onRebuildTwin && (
            <button
              type="button"
              onClick={onRebuildTwin}
              disabled={isRebuilding}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 transition-all disabled:opacity-50"
              title="Recalculate financial state and twin"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRebuilding ? 'animate-spin' : ''}`} />
              <span className="hidden md:inline">Sync Twin</span>
            </button>
          )}

          {onSeedDemo && (
            <button
              type="button"
              onClick={onSeedDemo}
              className="flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
              title="Load demo state (Nisha's portfolio)"
            >
              <Sparkles className="w-3 h-3 text-[#ebb2ff]" />
              <span className="hidden lg:inline">Demo</span>
            </button>
          )}

          {onResetDemo && (
            <button
              type="button"
              onClick={onResetDemo}
              className="flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium text-slate-400 hover:text-rose-300 hover:bg-white/5 transition-colors"
              title="Reset to empty database"
            >
              <Database className="w-3 h-3 text-slate-500" />
              <span className="hidden lg:inline">Reset</span>
            </button>
          )}
        </div>

        {/* Notification Bell */}
        <button
          type="button"
          onClick={onOpenSearch}
          className="relative p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
          title="Notifications & Alerts"
        >
          <Bell className="w-5 h-5" />
          {alertsCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#b600f8] animate-ping" />
          )}
          {alertsCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#b600f8]" />
          )}
        </button>

        {/* User Avatar */}
        <div
          onClick={onOpenAstra}
          className="w-9 h-9 rounded-full overflow-hidden border border-cyan-400/50 p-0.5 shadow-[0_0_10px_rgba(0,242,255,0.3)] cursor-pointer hover:border-cyan-300 transition-colors"
          title="Profile & Astra Copilot"
        >
          <img
            src={
              user?.avatarUrl ||
              'https://lh3.googleusercontent.com/aida-public/AB6AXuD8J32apjWE_9Lrq4MqvXHoDraLIkKYdyiD7DaZgxtveCROf8uhwMpbT2emvllCQZTTeQkEA9hNXO4OsvnmX2X4RouZYJ_t22d9cJpkzVYEFNmiX8qzn_05JI1mIOz6HuRQ-3ITOSQtMbYZUAcT2VcOk4jpSghrCRiN1K5_EbgbUreLSdY9220EVE5Yej7Lgmap0pxHqBiCWW-c2x6_ZMlESj7D8dY4h2TnE3cW3hvvZepXamSkGQDY'
            }
            alt={user?.name || 'User'}
            className="w-full h-full object-cover rounded-full"
          />
        </div>
      </div>
    </header>
  );
};
