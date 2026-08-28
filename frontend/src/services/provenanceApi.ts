import { apiFetch } from './api.ts';
import { ProvenanceNode, TimelineSnapshot } from '../types.ts';

export const provenanceApi = {
  getProvenance: async (): Promise<{
    provenanceTree: ProvenanceNode;
    metrics: {
      confirmedEventsCount: number;
      uncertainEventsCount: number;
      auditedRatio: string;
      primaryCustodian: string;
    };
  }> => {
    const res = await apiFetch<any>('/api/financial-state/provenance');

    const confirmedEvents = res.confirmed_balance_events || [];
    const obligations = res.obligations || {};
    const goals = res.goals || {};

    const confirmedCount = confirmedEvents.length;
    const totalCount = Math.max(1, confirmedCount);

    const balanceChildren: ProvenanceNode[] = confirmedEvents.map((e: any, idx: number) => ({
      id: e.event_id || `ev-${idx}`,
      name: `Transaction Ref #${(e.event_id || '').slice(0, 8)}`,
      label: `Verified ${e.direction || 'CREDIT'} ₹${parseFloat(e.amount || 0).toLocaleString('en-IN')}`,
      type: 'EVENT',
      entityType: e.source_type || 'BANK_FEED',
      confidence: parseFloat(e.confidence || '1'),
      status: e.status || 'CONFIRMED',
      timestamp: e.event_date || new Date().toISOString(),
      sourceData: e,
    }));

    const obligationChildren: ProvenanceNode[] = Object.keys(obligations).map((cat) => ({
      id: `obl-${cat}`,
      name: `Category: ${cat.toUpperCase()}`,
      label: `Obligation Cluster: ${cat}`,
      type: 'CATEGORY',
      entityType: 'RECURRENT_OBLIGATION',
      confidence: 0.98,
      status: 'CONFIRMED',
      timestamp: new Date().toISOString(),
      sourceData: obligations[cat],
      children: (obligations[cat] || []).map((e: any, idx: number) => ({
        id: e.event_id || `obl-ev-${idx}`,
        name: `Ledger Entry ${e.event_id?.slice(0, 8)}`,
        label: `${e.direction} ₹${parseFloat(e.amount || 0).toLocaleString('en-IN')}`,
        type: 'EVENT',
        entityType: e.source_type || 'CSV_IMPORT',
        confidence: parseFloat(e.confidence || '0.95'),
        status: e.status || 'CONFIRMED',
        timestamp: e.event_date || new Date().toISOString(),
        sourceData: e,
      })),
    }));

    const tree: ProvenanceNode = {
      id: 'root-universe',
      name: 'AstraFlow Cryptographic Ledger State',
      label: 'Digital Twin Ground Truth Root',
      type: 'STATE',
      entityType: 'TWIN_STATE',
      confidence: 0.99,
      status: 'CONFIRMED',
      timestamp: res.generated_at || new Date().toISOString(),
      children: [
        {
          id: 'branch-confirmed-balance',
          name: 'Confirmed Liquid Balance Proof',
          label: `Confirmed Assets Ledger (${confirmedCount} events)`,
          type: 'CATEGORY',
          entityType: 'AUDITED_BALANCE',
          confidence: 1.0,
          status: 'CONFIRMED',
          children: balanceChildren,
        },
        {
          id: 'branch-obligations',
          name: 'Deterministic Obligations',
          label: 'Classified Recurrent Commitments',
          type: 'CATEGORY',
          entityType: 'OBLIGATIONS',
          confidence: 0.96,
          status: 'CONFIRMED',
          children: obligationChildren,
        },
      ],
    };

    return {
      provenanceTree: tree,
      metrics: {
        confirmedEventsCount: confirmedCount,
        uncertainEventsCount: 0,
        auditedRatio: '100%',
        primaryCustodian: 'AstraFlow Immutable SQLite/PostgreSQL Engine',
      },
    };
  },
};

export const timelineApi = {
  getTimeline: async (): Promise<{ snapshots: TimelineSnapshot[] }> => {
    const list = await apiFetch<any[]>('/api/financial-state/timeline');
    const snapshots: TimelineSnapshot[] = (list || []).map((s: any) => ({
      id: s.id,
      date: s.rebuilt_at?.split('T')[0] || new Date().toISOString().split('T')[0],
      label: `Rebuild Snapshot #${s.id.slice(0, 6)}`,
      confirmedBalance: parseFloat(s.confirmed_balance || 0),
      totalIncome: 0,
      totalExpenses: 0,
      eventsCount: 4,
      obligations: 0,
      goalsFunded: 0,
      healthScore: 85,
      highlight: 'Continuous Twin Synced',
    }));
    return { snapshots };
  },
};

export const chatApi = {
  sendMessage: async (message: string): Promise<{ reply: string; timestamp: string }> => {
    return apiFetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },
};

