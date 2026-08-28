import { IngestionBatchResult, FinancialEvent } from '../types.ts';

const API_BASE = '/api';

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('astra_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchJson<T>(url: string, options: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const j = await res.json(); detail = j.detail || JSON.stringify(j); } catch {}
    throw new Error(detail);
  }
  return res.json();
}

function normalizeIngestionResult(res: any, type: string): IngestionBatchResult {
  const rows = res.rows || res.events || [];
  const events: FinancialEvent[] = [];

  rows.forEach((r: any, idx: number) => {
    if (r.status === 'rejected') return; // Skip rejected rows (like failed SMS parsing)
    
    // Handle both CSV row structure (direct fields) and SMS row structure (parsed_fields)
    const fields = r.parsed_fields || r;
    const amountVal = fields.amount || r.amount || 0;
    const directionVal = fields.direction || r.direction || 'DEBIT';
    const dateVal = fields.event_date || fields.date || r.date || new Date().toISOString().split('T')[0];
    const merchantVal = fields.merchant || r.merchant || r.description || r.title || 'Ingested Transaction';
    
    events.push({
      id: r.event_id || r.id || `ev-${idx}`,
      title: merchantVal,
      amount: parseFloat(amountVal),
      direction: directionVal.toUpperCase() as any,
      date: dateVal,
      category: fields.category || r.category || 'General',
      confidence: Math.round(parseFloat(r.confidence || '0.9') * 100),
      status: (r.event_status || r.status || 'LIKELY').toUpperCase() as any,
      source: type,
      rawEvidence: {
        snippet: merchantVal,
        timestamp: new Date().toISOString(),
        sourceId: type,
      },
    });
  });

  return {
    batchId: res.batch_id || res.id || `batch-${Date.now()}`,
    sourceType: type,
    totalDetected: events.length,
    confirmedCount: events.filter((e) => e.status === 'CONFIRMED').length,
    likelyCount: events.filter((e) => e.status === 'LIKELY').length,
    uncertainCount: events.filter((e) => e.status === 'UNCERTAIN').length,
    events,
  };
}

export const ingestionApi = {
  /** Upload a CSV bank statement file */
  importCsvFile: async (file: File): Promise<IngestionBatchResult> => {
    const text = await file.text();
    const res = await fetchJson<any>(`${API_BASE}/import/csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ csvContent: text, fileName: file.name }),
    });
    return normalizeIngestionResult(res, 'CSV Import');
  },

  /** Upload a text file containing SMS messages (one per line) */
  importSmsFile: async (file: File): Promise<IngestionBatchResult> => {
    const text = await file.text();
    const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
    const res = await fetchJson<any>(`${API_BASE}/inputs/sms`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ messages: lines }),
    });
    return normalizeIngestionResult(res, 'SMS Import');
  },

  /** Upload a PDF or document file via multipart form */
  uploadDocumentFile: async (file: File): Promise<IngestionBatchResult> => {
    const form = new FormData();
    form.append('file', file);
    form.append('fileName', file.name);
    const res = await fetchJson<any>(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers: { ...authHeaders() },
      body: form,
    });
    
    // Handle single document response from OCR
    if (!res.rows && !res.events && res.document_id) {
      const eventList: FinancialEvent[] = [];
      if (res.linked_event_id) {
        eventList.push({
          id: res.linked_event_id,
          title: res.filename || 'Ingested Document',
          amount: parseFloat(res.extracted?.amount || '0'),
          direction: (res.extracted?.direction || 'DEBIT').toUpperCase() as any,
          date: res.extracted?.event_date || new Date().toISOString().split('T')[0],
          category: 'General',
          confidence: Math.round(parseFloat(res.ocr_mean_confidence || '0.5') * 100),
          status: 'UNCERTAIN',
          source: 'Document OCR',
          rawEvidence: {
            snippet: res.ocr_text_excerpt || 'Extracted record',
            timestamp: res.uploaded_at || new Date().toISOString(),
            sourceId: 'Document OCR',
          }
        });
      }
      return {
        batchId: res.document_id,
        sourceType: 'Document OCR',
        totalDetected: eventList.length,
        confirmedCount: 0,
        likelyCount: 0,
        uncertainCount: eventList.length,
        events: eventList,
      };
    }

    return normalizeIngestionResult(res, 'Document OCR');
  },
};


