import { apiFetch } from './api.ts';
import { FinancialEvent } from '../types.ts';

export interface EventsResponse {
  events: FinancialEvent[];
  total: number;
  counts: {
    all: number;
    confirmed: number;
    likely: number;
    uncertain: number;
    rejected: number;
  };
}

function normalizeEvent(e: any): FinancialEvent {
  const amount = typeof e.amount === 'string' ? parseFloat(e.amount) : (e.amount || 0);
  const rawConf = typeof e.confidence === 'string' ? parseFloat(e.confidence) : (e.confidence || 1);
  const confidence = rawConf <= 1 ? Math.round(rawConf * 100) : rawConf;

  return {
    id: e.id || e.event_id,
    title: e.title || e.description || 'Ledger Transaction',
    amount: Math.abs(amount),
    direction: (e.direction || 'DEBIT').toUpperCase() as any,
    date: e.date_occurred || e.event_date || e.date || new Date().toISOString().split('T')[0],
    category: e.category || 'General',
    confidence,
    status: (e.status || 'CONFIRMED').toUpperCase() as any,
    source: e.source_type || e.source || 'CSV Import',
    rawEvidence: e.raw_evidence || e.rawEvidence || {
      snippet: e.title || 'Verified Transaction Record',
      timestamp: e.created_at || new Date().toISOString(),
      sourceId: e.source || 'ledger',
    },
    notes: e.notes,
  };
}

export const eventsApi = {
  getEvents: async (params?: { status?: string; category?: string; search?: string }): Promise<EventsResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.append('status', params.status);
    if (params?.category) searchParams.append('category', params.category);
    if (params?.search) searchParams.append('search', params.search);

    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    const res = await apiFetch<any>(`/api/events${query}`);

    let rawList: any[] = [];
    if (Array.isArray(res)) {
      rawList = res;
    } else if (res && Array.isArray(res.events)) {
      rawList = res.events;
    }

    const events = rawList.map(normalizeEvent);

    return {
      events,
      total: events.length,
      counts: {
        all: events.length,
        confirmed: events.filter((e) => e.status === 'CONFIRMED').length,
        likely: events.filter((e) => e.status === 'LIKELY').length,
        uncertain: events.filter((e) => e.status === 'UNCERTAIN').length,
        rejected: events.filter((e) => e.status === 'REJECTED').length,
      },
    };
  },

  confirmEvent: async (id: string): Promise<{ success: boolean; event: FinancialEvent }> => {
    const res = await apiFetch<any>(`/api/events/${id}/confirm`, {
      method: 'POST',
    });
    return { success: true, event: normalizeEvent(res.event || res) };
  },

  rejectEvent: async (id: string): Promise<{ success: boolean; event: FinancialEvent }> => {
    const res = await apiFetch<any>(`/api/events/${id}/reject`, {
      method: 'POST',
    });
    return { success: true, event: normalizeEvent(res.event || res) };
  },

  mergeEvents: async (sourceId: string, targetEventId: string): Promise<{ success: boolean; mergedEvent: FinancialEvent }> => {
    const res = await apiFetch<any>(`/api/events/${sourceId}/merge`, {
      method: 'POST',
      body: JSON.stringify({ surviving_event_id: targetEventId }),
    });
    return { success: true, mergedEvent: normalizeEvent(res.mergedEvent || res) };
  },

  getEvidence: async (id: string): Promise<{ eventId: string; title: string; rawEvidence: any; status: string; confidence: number; source: string }> => {
    return apiFetch(`/api/events/${id}/evidence`);
  },
};

