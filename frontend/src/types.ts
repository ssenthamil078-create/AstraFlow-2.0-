/**
 * AstraFlow - Financial Universe Core TypeScript Definitions
 */

export type EventDirection = 'CREDIT' | 'DEBIT';
export type EventStatus = 'CONFIRMED' | 'LIKELY' | 'UNCERTAIN' | 'REJECTED';
export type EventSource = 'CSV Import' | 'SMS Import' | 'Document OCR' | 'Manual';

export interface RawEvidence {
  snippet: string;
  timestamp: string;
  sourceId: string;
  account?: string;
  referenceId?: string;
  detectedPatterns?: string[];
  originalFile?: string;
}

export interface FinancialEvent {
  id: string;
  title: string;
  amount: number;
  direction: EventDirection;
  date: string;
  category: string;
  confidence: number; // 0 to 100
  status: EventStatus;
  source: EventSource;
  rawEvidence: RawEvidence;
  notes?: string;
  mergedWith?: string[];
  linkedIncomeSourceId?: string;
  linkedGoalId?: string;
}

export type FinancialNodeType = 'INCOME' | 'EXPENSE' | 'GOAL' | 'OBLIGATION' | 'UNCERTAIN' | 'RESERVE';

export interface FinancialNode {
  id: string;
  label: string;
  amount: number;
  type: FinancialNodeType;
  category: string;
  confidence: number; // 0 to 100
  status: 'CONFIRMED' | 'LIKELY' | 'UNCERTAIN';
  orbitRadius: number; // e.g. 2.2 to 4.8
  orbitSpeed: number; // radians per frame or rotation factor
  orbitInclination: number; // tilt angle in radians
  orbitPhase: number; // initial angular offset
  color: string;
  size: number;
  details: string;
  linkedEntityId?: string;
  secondaryInfo?: string;
}

export interface FinancialAlert {
  id: string;
  title: string;
  message: string;
  type: 'WARNING' | 'MARKET' | 'OPPORTUNITY' | 'UNCERTAINTY';
  amount?: number;
  date: string;
  actionLabel?: string;
  linkedEventId?: string;
  read?: boolean;
}

export interface FinancialGoal {
  id: string;
  name: string;
  targetAmount: number;
  currentAmount: number;
  targetDate: string;
  category: 'Emergency Reserve' | 'House Downpayment' | 'Travel & Adventure' | 'Tech & Mobility' | 'Retirement / Freedom' | 'Education' | 'Other';
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  color?: string;
  createdAt: string;
  notes?: string;
}

export interface IncomeSource {
  id: string;
  name: string;
  category: string;
  typicalAmount: number;
  reliabilityScore: number; // 0-100
  observationCount: number;
  status: 'ESTABLISHED' | 'PROVISIONAL';
  amountConsistency: number; // 0-100
  timeliness: number; // 0-100
  confidence: number; // 0-100
  frequency: 'Monthly' | 'Bi-weekly' | 'Weekly' | 'Irregular';
  lastReceivedDate: string;
  history: Array<{
    date: string;
    amount: number;
    onTime: boolean;
    reference?: string;
  }>;
}

export interface TimelineSnapshot {
  id: string;
  date: string;
  label: string;
  confirmedBalance: number;
  totalIncome: number;
  totalExpenses: number;
  eventsCount: number;
  obligations: number;
  goalsFunded: number;
  healthScore: number;
  highlight: string;
}

export interface FinancialState {
  totalNetWorth: number;
  confirmedBalance: number;
  totalIncome: number;
  totalExpenses: number;
  netCashFlow: number;
  trackedEventsCount: number;
  confirmedEventsCount: number;
  uncertainEventsCount: number;
  likelyEventsCount: number;
  healthScore: number; // 0-100
  healthAssessment: string;
  obligations: number;
  flexibleSpending: number;
  activeEventsPending: number;
  lastRebuiltAt: string;
  nodes: FinancialNode[];
  uncertainAlerts: FinancialAlert[];
}

export interface ProvenanceNode {
  id: string;
  name: string;
  label?: string;
  type?: 'STATE' | 'CATEGORY' | 'EVENT' | 'SOURCE' | 'RAW' | string;
  entityType?: string;
  value?: number;
  confidence?: number;
  status?: string;
  details?: string;
  timestamp?: string;
  rawSnippet?: string;
  sourceData?: any;
  children?: ProvenanceNode[];
}

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  emailVerified: boolean;
  currency: string;
  onboardingCompleted: boolean;
  avatarUrl?: string;
  createdAt: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  suggestedAction?: {
    label: string;
    route: string;
  };
}

export interface IngestionBatchResult {
  batchId: string;
  sourceType: EventSource;
  totalDetected: number;
  confirmedCount: number;
  likelyCount: number;
  uncertainCount: number;
  events: FinancialEvent[];
}
