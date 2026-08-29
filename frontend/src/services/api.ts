/**
 * Base API Client for AstraFlow
 */

import {
  mockUser,
  mockState,
  mockEvents,
  mockIncomeSources,
  mockGoals,
  mockProvenance,
} from './mockData.ts';

// Force empty API base to keep endpoints relative
const API_BASE_URL = '';

function resolveUrl(endpoint: string): string {
  if (/^https?:\/\//i.test(endpoint)) return endpoint;
  return `${API_BASE_URL}${endpoint}`;
}

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

// Intercept all API calls and return mock data locally (Backend Disconnected)
export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 600));

  console.log(`[MOCK API] ${options.method || 'GET'} ${endpoint}`);

  if (endpoint.includes('/api/auth/login') || endpoint.includes('/api/auth/register')) {
    return { user: mockUser, token: 'mock-token-123' } as any;
  }
  
  if (endpoint.includes('/api/auth/me')) {
    return { user: mockUser, authenticated: true } as any;
  }

  if (endpoint.includes('/api/auth/verify-email') || endpoint.includes('/api/auth/onboarding')) {
    return { success: true, user: mockUser } as any;
  }

  if (endpoint.includes('/api/financial-state/provenance')) {
    return mockProvenance as any;
  }

  if (endpoint.includes('/api/financial-state')) {
    return mockState as any;
  }

  if (endpoint.includes('/api/events')) {
    if (endpoint.includes('/confirm')) {
      return { success: true, event: { status: 'CONFIRMED' } } as any;
    }
    if (endpoint.includes('/reject')) {
      return { success: true, event: { status: 'REJECTED' } } as any;
    }
    return { events: mockEvents } as any;
  }

  if (endpoint.includes('/api/goals')) {
    // DELETE /api/goals/:id
    if (options.method === 'DELETE') {
      return { success: true, message: 'Goal retired from galaxy.' } as any;
    }
    // POST /api/goals — create new goal
    if (options.method === 'POST') {
      let body: any = {};
      try { body = JSON.parse(options.body as string); } catch {}
      const newGoal = {
        id: `goal-${Date.now()}`,
        name: body.name || 'New Goal',
        target_amount: body.target_amount || '100000.00',
        current_amount: body.current_amount || '0.00',
        target_date: body.target_date || '2027-06-30T00:00:00Z',
        linked_category: body.linked_category || 'Other',
        priority: body.priority || 'MEDIUM',
        color: body.color || '#b600f8',
        created_at: new Date().toISOString(),
      };
      return { goal: newGoal } as any;
    }
    // GET /api/goals
    return mockGoals as any;
  }

  if (endpoint.includes('/api/income-sources')) {
    if (endpoint.includes('/recalculate')) {
      const parts = endpoint.split('/');
      const id = parts[parts.length - 2];
      const source = mockIncomeSources.find((s) => s.id === id) || mockIncomeSources[0];
      return { success: true, source: { ...source, reliability_score: Math.min(100, source.reliability_score + 5) } } as any;
    }
    if (endpoint.includes('/reliability')) {
      const parts = endpoint.split('/');
      const id = parts[parts.length - 2];
      const source = mockIncomeSources.find((s) => s.id === id) || mockIncomeSources[0];
      return { source, reliability_score: source.reliability_score, amount_consistency_score: source.amount_consistency_score, timeliness_score: source.timeliness_score, data_confidence_score: source.data_confidence_score, observation_count: source.observation_count } as any;
    }
    if (options.method === 'POST') {
      let body: any = {};
      try { body = JSON.parse(options.body as string); } catch {}
      const newSource = {
        id: `src-${Date.now()}`,
        name: body.name || 'New Income Stream',
        category: body.category || 'other',
        typical_amount: String(body.typical_amount || 0),
        reliability_score: 50.0,
        observation_count: 1,
        is_provisional: true,
        amount_consistency_score: 50.0,
        timeliness_score: 50.0,
        data_confidence_score: 50.0,
      };
      return { source: newSource } as any;
    }
    return { incomeSources: mockIncomeSources } as any;
  }

  if (endpoint.includes('/api/chat')) {
    let body = "";
    try {
      body = options.body ? JSON.parse(options.body as string).message.toLowerCase() : "";
    } catch {}

    let reply = "Based on my analysis of your financial digital twin, your confirmed liquid balance is **₹1,45,000.00** with **₹65,000.00** in fixed commitments.\n\n💡 **Recommendation:** Your discretionary spending capacity is ₹80,000.00. Given your reliable income sources, I recommend reviewing your active goals to ensure optimal cash flow allocation. How can I assist you with specific simulations today?";

    if (body.includes("balance") || body.includes("change") || body.includes("why did")) {
      reply = "Your confirmed liquid balance is **₹1,45,000.00**. Here is a breakdown of this month:\n\n📥 **Credits:** ₹2,22,000.00 (Salary + Freelance)\n📤 **Debits:** ₹1,38,450.50 (Rent, SIP, Groceries, Gym, Netflix)\n\n⚠️ **Attention:** 1 transaction (₹50,000 to UPI-INVEST91) is flagged as **UNCERTAIN** and is not yet counted in your confirmed balance.";
    } else if (body.includes("expense") || body.includes("spending") || body.includes("increased")) {
      reply = "Here is your spending breakdown for this month:\n\n🏠 **Housing:** ₹65,000.00 (Penthouse Lease)\n📈 **Investments:** ₹35,000.00 (SIP - Nifty 50)\n🛒 **Groceries:** ₹8,450.50 (Whole Foods)\n💪 **Health & Fitness:** ₹15,000.00 (Gold's Gym)\n🎬 **Entertainment:** ₹649.00 (Netflix)\n\nTotal fixed spending this month is **₹1,24,099.50**. Investments are your largest outflow category.";
    } else if (body.includes("uncertain") || body.includes("alert") || body.includes("pending") || body.includes("review")) {
      reply = "You have **1 transaction pending review:**\n\n🔍 **UPI Transfer to INVEST91** — ₹50,000.00 on 26 Aug\n- Confidence: 62% (Low)\n- Source: SMS Import\n- Status: ⚠️ UNCERTAIN\n\nThis transaction could not be automatically verified. Please head to the **Events** tab to confirm or reject it. Confirming it will immediately update your digital twin.";
    } else if (body.includes("income") || body.includes("salary") || body.includes("reliable") || body.includes("reliability")) {
      reply = "Your primary income source **'Primary Tech Salary (Infosys)'** has a high **reliability score of 96%**.\n\n📊 **Reliability Details:**\n- Amount Consistency: 98%\n- Timeliness Score: 95%\n- Data Confidence: 99%\n- Observations: 18 months\n- Typical Inflow: ₹2,10,000/month\n\n🧠 **Insight:** This consistency significantly reduces your overall financial uncertainty, allowing for more aggressive allocations toward your 'Emergency Runway Reserve' goal.";
    } else if (body.includes("goal") || body.includes("save") || body.includes("target") || body.includes("close")) {
      reply = "Your primary target **'Emergency Runway Reserve'** is currently **29% funded** (₹1,45,000.00 of ₹5,00,000.00).\n\n📈 **Trajectory Analysis:** Based on your current net cash flow, your trajectory is healthy. If you allocate 20% of your remaining discretionary spending (₹16,000/month) to this goal, you will hit the **₹5,00,000 target in approximately 22 months**.";
    }

    return {
      reply,
      timestamp: new Date().toLocaleTimeString(),
    } as any;
  }

  if (endpoint.includes('/api/demo/seed') || endpoint.includes('/api/demo/reset')) {
    return { success: true, state: mockState } as any;
  }

  // Fallback for ingestion or other endpoints
  if (endpoint.includes('/api/import/csv') || endpoint.includes('/api/inputs/sms')) {
    return {
      batch_id: "mock-batch",
      rows: mockEvents,
    } as any;
  }

  return {} as any;
}
