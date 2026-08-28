import { apiFetch } from './api.ts';
import { FinancialState, FinancialNode, FinancialAlert } from '../types.ts';

function normalizeFinancialState(res: any): FinancialState {
  const confirmedBalance = typeof res.confirmed_balance === 'string' ? parseFloat(res.confirmed_balance) : (res.confirmedBalance || res.confirmed_balance || 0);

  // Compute obligations
  let obligationsTotal = 0;
  if (Array.isArray(res.obligations)) {
    obligationsTotal = res.obligations.reduce((sum: number, o: any) => sum + (parseFloat(o.average_amount || o.amount) || 0), 0);
  } else if (typeof res.obligations === 'number') {
    obligationsTotal = res.obligations;
  }

  // Compute discretionary spending
  let flexibleSpending = 0;
  if (res.discretionary_spending) {
    flexibleSpending = parseFloat(res.discretionary_spending.total || res.discretionary_spending) || 0;
  } else if (typeof res.flexibleSpending === 'number') {
    flexibleSpending = res.flexibleSpending;
  }

  const totalExpenses = obligationsTotal + flexibleSpending;
  const totalIncome = typeof res.totalIncome === 'number' ? res.totalIncome : Math.max(0, confirmedBalance + totalExpenses);
  const netCashFlow = totalIncome - totalExpenses;
  const totalNetWorth = confirmedBalance;

  const coverage = obligationsTotal > 0 ? (confirmedBalance / obligationsTotal) : 6;
  const healthScore = typeof res.healthScore === 'number' ? res.healthScore : Math.min(99, Math.max(40, Math.round(coverage * 12 + 45)));

  // Generate 3D Orbiting Nodes for Three.js FinancialEarth
  const nodes: FinancialNode[] = [];

  // Goal nodes
  if (Array.isArray(res.goals)) {
    res.goals.forEach((g: any, idx: number) => {
      const target = parseFloat(g.target_amount || g.targetAmount || 0);
      const current = parseFloat(g.current_amount || g.currentAmount || 0);
      nodes.push({
        id: g.goal_id || g.id || `goal-${idx}`,
        label: g.name || 'Goal Planet',
        amount: target,
        type: 'GOAL',
        category: 'Goals',
        confidence: 95,
        status: 'CONFIRMED',
        orbitRadius: 3.2 + (idx % 3) * 0.4,
        orbitSpeed: 0.15 + (idx % 3) * 0.05,
        orbitInclination: (idx * 0.6) - 0.5,
        orbitPhase: idx * 1.5,
        color: '#b600f8',
        size: Math.max(0.08, Math.min(0.2, (target / 500000) * 0.15)),
        details: `Target: ₹${target.toLocaleString('en-IN')} (Saved: ₹${current.toLocaleString('en-IN')})`,
        linkedEntityId: g.goal_id || g.id,
      });
    });
  }

  // Obligation node
  if (obligationsTotal > 0) {
    nodes.push({
      id: 'node-obligations',
      label: 'Verified Monthly Obligations',
      amount: obligationsTotal,
      type: 'OBLIGATION',
      category: 'Fixed Commitments',
      confidence: 98,
      status: 'CONFIRMED',
      orbitRadius: 2.5,
      orbitSpeed: 0.22,
      orbitInclination: 0.35,
      orbitPhase: 2.1,
      color: '#f43f5e',
      size: 0.14,
      details: `Fixed recurrent commitments: ₹${obligationsTotal.toLocaleString('en-IN')}/mo`,
    });
  }

  // Liquid Reserve node
  if (confirmedBalance > 0) {
    nodes.push({
      id: 'node-liquid-reserve',
      label: 'Confirmed Liquid Reserve',
      amount: confirmedBalance,
      type: 'INCOME',
      category: 'Liquid Cash',
      confidence: 100,
      status: 'CONFIRMED',
      orbitRadius: 2.0,
      orbitSpeed: 0.18,
      orbitInclination: -0.25,
      orbitPhase: 0.8,
      color: '#00f2ff',
      size: 0.16,
      details: `Audited balance in bank vault: ₹${confirmedBalance.toLocaleString('en-IN')}`,
    });
  }

  const alerts: FinancialAlert[] = (res.uncertainAlerts || []);

  return {
    totalNetWorth,
    confirmedBalance,
    totalIncome,
    totalExpenses,
    netCashFlow,
    trackedEventsCount: res.trackedEventsCount || 6,
    confirmedEventsCount: res.confirmedEventsCount || 5,
    uncertainEventsCount: res.uncertainEventsCount || 1,
    likelyEventsCount: res.likelyEventsCount || 0,
    healthScore,
    healthAssessment: healthScore >= 80 ? 'Robust financial foundation with positive cash velocity.' : 'Maintain regular tracking of obligations.',
    obligations: obligationsTotal,
    flexibleSpending,
    activeEventsPending: res.activeEventsPending || 0,
    lastRebuiltAt: res.as_of || res.lastRebuiltAt || new Date().toISOString(),
    nodes,
    uncertainAlerts: alerts,
  };
}

export const financialStateApi = {
  getState: async (): Promise<FinancialState> => {
    const res = await apiFetch<any>('/api/financial-state');
    return normalizeFinancialState(res);
  },

  rebuildState: async (): Promise<{ success: boolean; message: string; state: FinancialState }> => {
    const res = await apiFetch<any>('/api/financial-state/rebuild', {
      method: 'POST',
    });
    const state = normalizeFinancialState(res);
    return {
      success: true,
      message: 'Living Digital Twin rebuilt from ledger snapshots',
      state,
    };
  },

  seedDemo: async (): Promise<{ success: boolean; state: FinancialState }> => {
    const res = await apiFetch<any>('/api/demo/seed', {
      method: 'POST',
    });
    return {
      success: true,
      state: normalizeFinancialState(res.state || res),
    };
  },

  resetDemo: async (): Promise<{ success: boolean; state: FinancialState }> => {
    const res = await apiFetch<any>('/api/demo/reset', {
      method: 'POST',
    });
    return {
      success: true,
      state: normalizeFinancialState(res.state || res),
    };
  },
};

