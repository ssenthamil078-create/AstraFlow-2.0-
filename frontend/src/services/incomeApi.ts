import { apiFetch } from './api.ts';
import { IncomeSource } from '../types.ts';

export interface ReliabilityDetails {
  source: IncomeSource;
  metrics: {
    score: number;
    observationCount: number;
    amountConsistency: number;
    timeliness: number;
    confidence: number;
    varianceCoefficient: string;
    status: 'ESTABLISHED' | 'PROVISIONAL';
    recommendation: string;
  };
}

function normalizeIncomeSource(s: any): IncomeSource {
  const typical = typeof s.typical_amount === 'string' ? parseFloat(s.typical_amount) : (s.typical_amount || s.typicalAmount || 0);
  const score = typeof s.reliability_score === 'string' ? parseFloat(s.reliability_score) : (s.reliability_score || s.reliabilityScore || 85);
  const obsCount = s.observation_count ?? s.observationCount ?? 0;
  const isProv = s.is_provisional ?? (obsCount < 3);

  return {
    id: s.id || s.income_source_id,
    name: s.name || 'Income Stream',
    category: s.category || 'Salary',
    typicalAmount: typical,
    reliabilityScore: Math.round(score),
    observationCount: obsCount,
    status: isProv ? 'PROVISIONAL' : 'ESTABLISHED',
    amountConsistency: Math.round(typeof s.amount_consistency_score === 'string' ? parseFloat(s.amount_consistency_score) : (s.amount_consistency_score || 85)),
    timeliness: Math.round(typeof s.timeliness_score === 'string' ? parseFloat(s.timeliness_score) : (s.timeliness_score || 80)),
    confidence: Math.round(typeof s.data_confidence_score === 'string' ? parseFloat(s.data_confidence_score) : (s.data_confidence_score || 90)),
    frequency: 'Monthly',
    lastReceivedDate: s.created_at?.split('T')[0] || '2026-08-01',
    history: [],
  };
}

export const incomeApi = {
  getIncomeSources: async (): Promise<{ incomeSources: IncomeSource[] }> => {
    const res = await apiFetch<any>('/api/income-sources');
    const list = Array.isArray(res) ? res : (res?.incomeSources || []);
    return {
      incomeSources: list.map(normalizeIncomeSource),
    };
  },

  getReliability: async (id: string): Promise<ReliabilityDetails> => {
    const res = await apiFetch<any>(`/api/income-sources/${id}/reliability`);
    const score = typeof res.reliability_score === 'string' ? parseFloat(res.reliability_score) : (res.reliability_score || 85);
    const obsCount = res.observation_count || 0;
    const isProv = res.is_provisional ?? (obsCount < 3);

    const source = normalizeIncomeSource(res.source || res);

    return {
      source,
      metrics: {
        score: Math.round(score),
        observationCount: obsCount,
        amountConsistency: Math.round(typeof res.amount_consistency_score === 'string' ? parseFloat(res.amount_consistency_score) : (res.amount_consistency_score || 85)),
        timeliness: Math.round(typeof res.timeliness_score === 'string' ? parseFloat(res.timeliness_score) : (res.timeliness_score || 80)),
        confidence: Math.round(typeof res.data_confidence_score === 'string' ? parseFloat(res.data_confidence_score) : (res.data_confidence_score || 90)),
        varianceCoefficient: '0.08',
        status: isProv ? 'PROVISIONAL' : 'ESTABLISHED',
        recommendation: score >= 85 ? 'Highly established cash foundation.' : 'Healthy recurring flow.',
      },
    };
  },

  recalculateReliability: async (id: string): Promise<{ success: boolean; source: IncomeSource }> => {
    const res = await apiFetch<any>(`/api/income-sources/${id}/recalculate`, {
      method: 'POST',
    });
    return { success: true, source: normalizeIncomeSource(res.source || res) };
  },

  createIncomeSource: async (data: { name: string; category: string; typicalAmount: number; frequency?: string }): Promise<{ source: IncomeSource }> => {
    // Map frontend labels to backend IncomeSourceCategory enum values (vocabulary.py)
    const categoryMap: Record<string, string> = {
      // Exact backend enum values pass through unchanged
      'salaried_employer': 'salaried_employer',
      'freelance_client': 'freelance_client',
      'platform_gig': 'platform_gig',
      'rental_income': 'rental_income',
      'investment_return': 'investment_return',
      'other': 'other',
      // Human-readable labels mapped to enum values
      'Salary': 'salaried_employer',
      'salary_primary': 'salaried_employer',
      'salary_secondary': 'salaried_employer',
      'Consulting': 'freelance_client',
      'Freelance': 'freelance_client',
      'contractor_1099': 'freelance_client',
      'Contractor': 'platform_gig',
      'Gig': 'platform_gig',
      'Rental': 'rental_income',
      'rental_property': 'rental_income',
      'Investment': 'investment_return',
      'investment_dividends': 'investment_return',
      'Dividends': 'investment_return',
      'Business': 'other',
      'business_owner': 'other',
      'pension_annuity': 'other',
      'government_benefit': 'other',
      'Other': 'other',
    };

    const payload = {
      name: data.name,
      category: categoryMap[data.category] ?? 'other',
      currency: 'INR',
      typical_amount: data.typicalAmount,
    };
    const res = await apiFetch<any>('/api/income-sources', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return { source: normalizeIncomeSource(res.source || res) };
  },
};

