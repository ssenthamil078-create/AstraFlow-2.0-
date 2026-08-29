/**
 * AstraFlow - The Living Financial Cosmos
 * Next-Generation Autonomous Financial Intelligence Platform
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, Sparkles, AlertCircle } from 'lucide-react';
import { Sidebar, NavRoute } from './components/Sidebar.tsx';
import { TopBar } from './components/TopBar.tsx';
import { AstraCopilot } from './components/AstraCopilot.tsx';
import { CommandPalette } from './components/CommandPalette.tsx';
import { NodeDetailModal } from './components/NodeDetailModal.tsx';
import { IngestionModal } from './components/IngestionModal.tsx';
import { CreateGoalModal } from './components/CreateGoalModal.tsx';

// Views
import { UniverseDashboard } from './views/UniverseDashboard.tsx';
import { FinancialTwinView } from './views/FinancialTwinView.tsx';
import { CashFlowView } from './views/CashFlowView.tsx';
import { EventsTruthView } from './views/EventsTruthView.tsx';
import { IncomeReliabilityView } from './views/IncomeReliabilityView.tsx';
import { GoalsGalaxyView } from './views/GoalsGalaxyView.tsx';
import { DataSourcesView } from './views/DataSourcesView.tsx';
import { ProvenanceView } from './views/ProvenanceView.tsx';
import { SettingsView } from './views/SettingsView.tsx';
import { InsightsView } from './views/InsightsView.tsx';

// Services & Types
import { authApi } from './services/authApi.ts';
import { financialStateApi } from './services/financialStateApi.ts';
import { eventsApi } from './services/eventsApi.ts';
import { incomeApi } from './services/incomeApi.ts';
import { goalsApi } from './services/goalsApi.ts';
import {
  UserProfile,
  FinancialState,
  FinancialEvent,
  IncomeSource,
  FinancialGoal,
  FinancialNode,
} from './types.ts';

export default function App() {
  const navigate = useNavigate();

  // Navigation & Shell State
  const [currentRoute, setCurrentRoute] = useState<NavRoute>('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Modals & Drawers
  const [isAstraOpen, setIsAstraOpen] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isIngestionOpen, setIsIngestionOpen] = useState(false);
  const [isCreateGoalOpen, setIsCreateGoalOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<FinancialNode | null>(null);

  // Application Data
  const [user, setUser] = useState<UserProfile | null>(null);
  const [financialState, setFinancialState] = useState<FinancialState | null>(null);
  const [events, setEvents] = useState<FinancialEvent[]>([]);
  const [incomeSources, setIncomeSources] = useState<IncomeSource[]>([]);
  const [goals, setGoals] = useState<FinancialGoal[]>([]);
  const [currency, setCurrency] = useState<string>('₹');

  // Loading & Sync States
  const [loading, setLoading] = useState(true);
  const [isRebuilding, setIsRebuilding] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initial Data Fetch
  const loadAllData = useCallback(async () => {
    const token = localStorage.getItem('astra_token');
    if (!token) {
      navigate('/login');
      return;
    }

    try {
      const [userRes, stateRes, eventsRes, incomeRes, goalsRes] = await Promise.all([
        authApi.getProfile().catch(() => ({ user: null })),
        financialStateApi.getState().catch(() => null),
        eventsApi.getEvents().catch(() => ({ events: [] })),
        incomeApi.getIncomeSources().catch(() => ({ incomeSources: [] })),
        goalsApi.getGoals().catch(() => ({ goals: [] })),
      ]);

      if (userRes && (userRes as any).user) {
        setUser((userRes as any).user);
        if ((userRes as any).user.currency) {
          setCurrency((userRes as any).user.currency);
        }
      }
      if (stateRes) setFinancialState(stateRes);
      if (eventsRes?.events) setEvents(eventsRes.events);
      if (incomeRes?.incomeSources) setIncomeSources(incomeRes.incomeSources);
      if (goalsRes?.goals) setGoals(goalsRes.goals);
    } catch (err: any) {
      console.error('Failed to load initial AstraFlow state', err);
      setErrorMessage(err.message || 'Failed to initialize financial cosmos');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // Global Event Handlers
  const handleConfirmEvent = async (id: string) => {
    try {
      await eventsApi.confirmEvent(id);
      // Refresh events and state
      const [eventsRes, stateRes] = await Promise.all([
        eventsApi.getEvents(),
        financialStateApi.getState(),
      ]);
      if (eventsRes?.events) setEvents(eventsRes.events);
      if (stateRes) setFinancialState(stateRes);
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleRejectEvent = async (id: string) => {
    try {
      await eventsApi.rejectEvent(id);
      const [eventsRes, stateRes] = await Promise.all([
        eventsApi.getEvents(),
        financialStateApi.getState(),
      ]);
      if (eventsRes?.events) setEvents(eventsRes.events);
      if (stateRes) setFinancialState(stateRes);
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleRebuildTwin = async () => {
    setIsRebuilding(true);
    try {
      const res = await financialStateApi.rebuildState();
      if (res.state) {
        setFinancialState(res.state);
      }
      const eventsRes = await eventsApi.getEvents();
      if (eventsRes?.events) setEvents(eventsRes.events);
    } catch (err: any) {
      console.error(err);
    } finally {
      setIsRebuilding(false);
    }
  };

  const handleSeedDemo = async () => {
    setLoading(true);
    try {
      await financialStateApi.seedDemo();
      await loadAllData();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleResetDemo = async () => {
    if (!confirm('Reset all financial events, twin nodes, and income sources to empty state?')) return;
    setLoading(true);
    try {
      await financialStateApi.resetDemo();
      await loadAllData();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = () => {
    const dataBlob = new Blob(
      [
        JSON.stringify(
          {
            user,
            financialState,
            events,
            incomeSources,
            goals,
            exportedAt: new Date().toISOString(),
          },
          null,
          2
        ),
      ],
      { type: 'application/json' }
    );
    const url = URL.createObjectURL(dataBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `AstraFlow_Export_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Compute Page Title
  const getPageTitle = () => {
    switch (currentRoute) {
      case 'dashboard':
        return 'Universe Overview';
      case 'financial-twin':
        return 'The Financial Twin';
      case 'cash-flow':
        return 'Cash Flow Intelligence';
      case 'events':
        return 'Events & Truth Layer';
      case 'income':
        return 'Income Sources & Reliability';
      case 'goals':
        return 'Goals Galaxy';
      case 'data-sources':
        return 'Data Sources & Ingestion';
      case 'insights':
        return 'Insights & Intelligence';
      case 'provenance':
        return 'Evidence & Provenance';
      case 'settings':
        return 'System Settings';
      default:
        return 'AstraFlow';
    }
  };

  const pendingEventsCount = events.filter((e) => e.status === 'UNCERTAIN' || e.status === 'LIKELY').length;

  return (
    <div className="min-h-screen bg-[#030615] text-slate-100 flex flex-col selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* 1. Sidebar Navigation */}
      <Sidebar
        currentRoute={currentRoute}
        onRouteChange={setCurrentRoute}
        user={user}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
        onOpenAstraChat={() => setIsAstraOpen(true)}
        activeEventsCount={pendingEventsCount}
      />

      {/* 2. Top Header Bar */}
      <TopBar
        title={getPageTitle()}
        user={user}
        onToggleMobileMenu={() => setMobileOpen(!mobileOpen)}
        onOpenSearch={() => setIsCommandPaletteOpen(true)}
        onOpenAstra={() => setIsAstraOpen(true)}
        onRebuildTwin={handleRebuildTwin}
        onSeedDemo={handleSeedDemo}
        onResetDemo={handleResetDemo}
        isRebuilding={isRebuilding}
        alertsCount={pendingEventsCount}
        sidebarCollapsed={sidebarCollapsed}
      />

      {/* 3. Main Content Container */}
      <main
        className={`flex-1 transition-all duration-300 ease-in-out pt-20 pb-16 px-4 sm:px-6 lg:px-8
          ${sidebarCollapsed ? 'lg:pl-24' : 'lg:pl-80'}
        `}
      >
        {errorMessage && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        )}

        {/* View Router */}
        {currentRoute === 'dashboard' && (
          <UniverseDashboard
            financialState={financialState}
            events={events}
            onNodeClick={(node) => setSelectedNode(node)}
            onNavigate={setCurrentRoute}
            onOpenIngestion={() => setIsIngestionOpen(true)}
            onOpenCreateGoal={() => setIsCreateGoalOpen(true)}
            onConfirmEvent={handleConfirmEvent}
            currency={currency}
          />
        )}

        {currentRoute === 'financial-twin' && (
          <FinancialTwinView
            financialState={financialState}
            onNodeClick={(node) => setSelectedNode(node)}
            onRebuildTwin={handleRebuildTwin}
            isRebuilding={isRebuilding}
            currency={currency}
          />
        )}

        {currentRoute === 'cash-flow' && (
          <CashFlowView
            financialState={financialState}
            events={events}
            currency={currency}
            onNavigateToEvents={() => setCurrentRoute('events')}
          />
        )}

        {currentRoute === 'events' && (
          <EventsTruthView
            events={events}
            onConfirmEvent={handleConfirmEvent}
            onRejectEvent={handleRejectEvent}
            currency={currency}
          />
        )}

        {currentRoute === 'income' && (
          <IncomeReliabilityView
            incomeSources={incomeSources}
            onRefreshSources={loadAllData}
            currency={currency}
          />
        )}

        {currentRoute === 'goals' && (
          <GoalsGalaxyView
            goals={goals}
            onOpenCreateGoal={() => setIsCreateGoalOpen(true)}
            onRefreshGoals={loadAllData}
            onDeleteGoal={(id) => setGoals((prev) => prev.filter((g) => g.id !== id))}
            currency={currency}
          />
        )}

        {currentRoute === 'data-sources' && (
          <DataSourcesView onOpenIngestion={() => setIsIngestionOpen(true)} />
        )}

        {currentRoute === 'insights' && (
          <InsightsView
            financialState={financialState}
            events={events}
            goals={goals}
            incomeSources={incomeSources}
            currency={currency}
          />
        )}

        {currentRoute === 'provenance' && <ProvenanceView />}

        {currentRoute === 'settings' && (
          <SettingsView
            user={user}
            currency={currency}
            onChangeCurrency={setCurrency}
            onSeedDemo={handleSeedDemo}
            onResetDemo={handleResetDemo}
            onExportData={handleExportData}
          />
        )}
      </main>

      {/* 4. Floating Astra Copilot Orb Button (Bottom Right) */}
      <button
        type="button"
        onClick={() => setIsAstraOpen(true)}
        className="fixed bottom-6 right-6 z-40 p-3.5 rounded-full bg-gradient-to-tr from-cyan-400 to-[#b600f8] shadow-[0_0_25px_rgba(0,242,255,0.6)] hover:scale-110 active:scale-95 transition-all group flex items-center gap-2"
        title="Open Astra AI Copilot"
      >
        <div className="w-6 h-6 rounded-full bg-[#050816] flex items-center justify-center">
          <Bot className="w-4 h-4 text-cyan-400 group-hover:rotate-12 transition-transform" />
        </div>
        <span className="hidden sm:inline text-xs font-bold font-heading text-slate-950 pr-1">
          Ask Astra
        </span>
      </button>

      {/* 5. Modals & Dialogs */}
      <AstraCopilot
        isOpen={isAstraOpen}
        onClose={() => setIsAstraOpen(false)}
        onNavigate={setCurrentRoute}
        user={user}
      />

      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onNavigate={setCurrentRoute}
        onOpenAstra={() => setIsAstraOpen(true)}
        onOpenAddDataSource={() => setIsIngestionOpen(true)}
        onOpenCreateGoal={() => setIsCreateGoalOpen(true)}
        onRebuildTwin={handleRebuildTwin}
      />

      <NodeDetailModal
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
        onNavigateToEvents={() => setCurrentRoute('events')}
        onNavigateToGoals={() => setCurrentRoute('goals')}
        onNavigateToIncome={() => setCurrentRoute('income')}
      />

      <IngestionModal
        isOpen={isIngestionOpen}
        onClose={() => setIsIngestionOpen(false)}
        onSuccess={() => {
          loadAllData();
        }}
      />

      <CreateGoalModal
        isOpen={isCreateGoalOpen}
        onClose={() => setIsCreateGoalOpen(false)}
        onGoalCreated={(newGoal) => {
          setGoals((prev) => [newGoal, ...prev]);
          setIsCreateGoalOpen(false);
        }}
      />
    </div>
  );
}
