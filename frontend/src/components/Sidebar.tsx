import React from 'react';
import {
  Globe,
  Wallet,
  ArrowLeftRight,
  Calendar,
  CreditCard,
  Sparkles,
  Database,
  BarChart3,
  History,
  Settings,
  Bot,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { UserProfile } from '../types.ts';

export type NavRoute =
  | 'landing'
  | 'dashboard'
  | 'financial-twin'
  | 'cash-flow'
  | 'events'
  | 'income'
  | 'goals'
  | 'data-sources'
  | 'insights'
  | 'provenance'
  | 'timeline'
  | 'settings';

interface SidebarProps {
  currentRoute: NavRoute;
  onRouteChange: (route: NavRoute) => void;
  user: UserProfile | null;
  collapsed: boolean;
  setCollapsed: (c: boolean) => void;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
  onOpenAstraChat?: () => void;
  activeEventsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentRoute,
  onRouteChange,
  user,
  collapsed,
  setCollapsed,
  mobileOpen,
  setMobileOpen,
  onOpenAstraChat,
  activeEventsCount = 0,
}) => {
  const navItems: Array<{
    id: NavRoute;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string | number;
  }> = [
    { id: 'dashboard', label: 'Universe', icon: Globe },
    { id: 'financial-twin', label: 'Financial Twin', icon: Wallet },
    { id: 'cash-flow', label: 'Cash Flow', icon: ArrowLeftRight },
    {
      id: 'events',
      label: 'Events',
      icon: Calendar,
      badge: activeEventsCount > 0 ? activeEventsCount : undefined,
    },
    { id: 'income', label: 'Income Sources', icon: CreditCard },
    { id: 'goals', label: 'Goals', icon: Sparkles },
    { id: 'data-sources', label: 'Data Sources', icon: Database },
    { id: 'insights', label: 'Insights', icon: BarChart3 },
    { id: 'provenance', label: 'Provenance', icon: History },
  ];

  const handleNav = (route: NavRoute) => {
    onRouteChange(route);
    setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar Aside */}
      <aside
        className={`fixed left-0 top-0 h-full z-50 transition-all duration-300 ease-in-out flex flex-col
          bg-[#070b1f]/95 lg:bg-[#070b1f]/85 backdrop-blur-xl border-r border-[#3a494b]/40
          ${collapsed ? 'w-20' : 'w-72'}
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Brand Header */}
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <div
            onClick={() => handleNav('dashboard')}
            className="flex items-center gap-3 cursor-pointer group select-none"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-[#b600f8] p-[1.5px] shadow-[0_0_15px_rgba(0,242,255,0.4)] flex-shrink-0 group-hover:scale-105 transition-transform">
              <div className="w-full h-full rounded-full bg-[#050816] flex items-center justify-center">
                <Globe className="w-5 h-5 text-cyan-400 animate-spin-slow" />
              </div>
            </div>
            {!collapsed && (
              <div className="overflow-hidden">
                <h1 className="text-xl font-bold font-heading text-white tracking-tight flex items-center gap-1.5">
                  AstraFlow
                </h1>
                <p className="text-[11px] text-slate-400 truncate">Digital Asset Manager</p>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (onOpenAstraChat) onOpenAstraChat();
                  }}
                  className="text-[11px] text-[#ebb2ff] hover:text-white flex items-center gap-1 mt-0.5 transition-colors font-medium"
                >
                  <Bot className="w-3 h-3 text-[#b600f8]" />
                  <span>Astra AI Chat</span>
                </button>
              </div>
            )}
          </div>

          {/* Desktop Collapse Toggle */}
          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentRoute === item.id;

            return (
              <button
                key={item.id}
                type="button"
                onClick={() => handleNav(item.id)}
                className={`w-full flex items-center gap-3.5 px-3.5 py-3 rounded-xl text-sm font-medium transition-all duration-200 group relative ${
                  isActive
                    ? 'bg-[#b600f8] text-white shadow-[0_0_20px_rgba(182,0,248,0.4)] scale-[0.98]'
                    : 'text-slate-300 hover:bg-white/5 hover:text-white'
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon
                  className={`w-5 h-5 flex-shrink-0 transition-transform group-hover:scale-110 ${
                    isActive ? 'text-white' : 'text-cyan-400/90'
                  }`}
                />

                {!collapsed && (
                  <span className="truncate flex-1 text-left font-heading">{item.label}</span>
                )}

                {!collapsed && item.badge && (
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                      isActive ? 'bg-white/20 text-white' : 'bg-[#b600f8]/20 text-[#ebb2ff]'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}

                {/* Collapsed Badge indicator */}
                {collapsed && item.badge && (
                  <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#b600f8] ring-2 ring-[#070b1f]" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Bottom Actions */}
        <div className="p-3 border-t border-white/5 space-y-1.5">
          {/* Settings */}
          <button
            type="button"
            onClick={() => handleNav('settings')}
            className={`w-full flex items-center gap-3.5 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors ${
              currentRoute === 'settings'
                ? 'bg-[#b600f8] text-white'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
            title={collapsed ? 'Settings' : undefined}
          >
            <Settings className="w-5 h-5 text-slate-400 flex-shrink-0" />
            {!collapsed && <span className="font-heading">Settings</span>}
          </button>

          {/* User Profile Card */}
          {!collapsed && user && (
            <div className="pt-2">
              <div className="p-2.5 rounded-xl bg-[#0d1515]/70 border border-white/5 flex items-center gap-3">
                <img
                  src={
                    user.avatarUrl ||
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuD8J32apjWE_9Lrq4MqvXHoDraLIkKYdyiD7DaZgxtveCROf8uhwMpbT2emvllCQZTTeQkEA9hNXO4OsvnmX2X4RouZYJ_t22d9cJpkzVYEFNmiX8qzn_05JI1mIOz6HuRQ-3ITOSQtMbYZUAcT2VcOk4jpSghrCRiN1K5_EbgbUreLSdY9220EVE5Yej7Lgmap0pxHqBiCWW-c2x6_ZMlESj7D8dY4h2TnE3cW3hvvZepXamSkGQDY'
                  }
                  alt={user.name}
                  className="w-8 h-8 rounded-full object-cover ring-1 ring-cyan-400/50"
                />
                <div className="overflow-hidden flex-1">
                  <div className="text-xs font-semibold text-white truncate flex items-center gap-1">
                    {user.name}
                    <ShieldCheck className="w-3 h-3 text-cyan-400 inline" />
                  </div>
                  <div className="text-[10px] text-slate-400 truncate">{user.email}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
