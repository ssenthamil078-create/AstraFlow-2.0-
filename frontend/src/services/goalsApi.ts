import { apiFetch } from './api.ts';
import { FinancialGoal } from '../types.ts';

function normalizeGoal(g: any): FinancialGoal {
  const target = typeof g.target_amount === 'string' ? parseFloat(g.target_amount) : (g.target_amount || g.targetAmount || 0);
  const current = typeof g.current_amount === 'string' ? parseFloat(g.current_amount) : (g.current_amount || g.currentAmount || 0);

  return {
    id: g.id || g.goal_id,
    name: g.name || 'Goal Planet',
    targetAmount: target,
    currentAmount: current,
    targetDate: g.target_date || g.targetDate || new Date(Date.now() + 180 * 86400000).toISOString().split('T')[0],
    category: g.linked_category || g.category || 'Other',
    priority: g.priority || 'MEDIUM',
    color: g.color || '#b600f8',
    createdAt: g.created_at || new Date().toISOString(),
    notes: g.notes,
  };
}

export const goalsApi = {
  getGoals: async (): Promise<{ goals: FinancialGoal[] }> => {
    const res = await apiFetch<any>('/api/goals');
    const list = Array.isArray(res) ? res : (res?.goals || []);
    return {
      goals: list.map(normalizeGoal),
    };
  },

  createGoal: async (goal: Partial<FinancialGoal>): Promise<{ goal: FinancialGoal }> => {
    const payload = {
      name: goal.name,
      goal_type: 'savings_target',
      currency: 'INR',
      linked_category: 'emergency_savings',
      target_amount: String(goal.targetAmount || 0),
      target_date: goal.targetDate ? `${goal.targetDate}T00:00:00Z` : undefined,
    };
    const res = await apiFetch<any>('/api/goals', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return { goal: normalizeGoal(res.goal || res) };
  },

  updateGoal: async (id: string, updates: Partial<FinancialGoal>): Promise<{ goal: FinancialGoal }> => {
    const payload: any = {};
    if (updates.name) payload.name = updates.name;
    if (updates.targetAmount !== undefined) payload.target_amount = String(updates.targetAmount);
    if (updates.targetDate) payload.target_date = `${updates.targetDate}T00:00:00Z`;

    const res = await apiFetch<any>(`/api/goals/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
    return { goal: normalizeGoal(res.goal || res) };
  },

  deleteGoal: async (id: string): Promise<{ success: boolean; message: string }> => {
    return apiFetch<{ success: boolean; message: string }>(`/api/goals/${id}`, {
      method: 'DELETE',
    });
  },
};

