export const mockUser = {
  id: "user-123",
  email: "demo@astraflow.com",
  name: "Commander",
  currency: "INR",
  is_verified: true,
};

export const mockState = {
  currency: "INR",
  confirmed_balance: "145000.00",
  unconfirmed_balance: "50000.00",
  total_balance: "195000.00",
  last_updated: new Date().toISOString(),
  obligations: [
    { category: "Housing", average_amount: "65000.00", frequency: "monthly", is_active: true }
  ],
  discretionary_spending: { total: "80000.00" },
  projected_eom_balance: "85000.00",
  health_score: "92.5",
};

export const mockEvents = [
  {
    id: "evt-1",
    title: "Monthly Executive Salary",
    amount: 210000.00,
    direction: "CREDIT",
    date: new Date().toISOString(),
    category: "Salary",
    confidence: 99,
    status: "CONFIRMED",
    source: "CSV Import",
  },
  {
    id: "evt-2",
    title: "Penthouse Apartment Lease",
    amount: 65000.00,
    direction: "DEBIT",
    date: new Date(Date.now() - 86400000 * 2).toISOString(),
    category: "Housing",
    confidence: 96,
    status: "CONFIRMED",
    source: "CSV Import",
  },
  {
    id: "evt-3",
    title: "Uncategorized Transfer to UPI-INVEST91",
    amount: 50000.00,
    direction: "DEBIT",
    date: new Date(Date.now() - 86400000 * 5).toISOString(),
    category: "Transfers",
    confidence: 62,
    status: "UNCERTAIN",
    source: "SMS Import",
  },
  {
    id: "evt-4",
    title: "Whole Foods Market - Groceries",
    amount: 8450.50,
    direction: "DEBIT",
    date: new Date(Date.now() - 86400000 * 8).toISOString(),
    category: "Groceries",
    confidence: 99,
    status: "CONFIRMED",
    source: "CSV Import",
  },
  {
    id: "evt-5",
    title: "Freelance Design (Logo)",
    amount: 12000.00,
    direction: "CREDIT",
    date: new Date(Date.now() - 86400000 * 1).toISOString(),
    category: "Freelance",
    confidence: 95,
    status: "CONFIRMED",
    source: "CSV Import",
  },
];

export const mockIncomeSources = [
  {
    id: "src-1",
    name: "Primary Tech Salary (Infosys)",
    category: "Salary",
    typical_amount: "210000.00",
    reliability_score: 96.0,
    observation_count: 18,
    is_provisional: false,
    amount_consistency_score: 98.0,
    timeliness_score: 95.0,
    data_confidence_score: 99.0,
  }
];

export const mockGoals = [
  {
    id: "goal-1",
    name: "Emergency Runway Reserve",
    goal_type: "savings_target",
    target_amount: "500000.00",
    current_amount: "145000.00",
    currency: "INR",
    linked_category: "Rent",
    created_at: new Date().toISOString(),
  }
];

export const mockProvenance = {
  provenanceTree: {
    id: "root",
    type: "balance",
    label: "Confirmed Balance (INR 145,000.00)",
    value: 145000,
    children: [
      {
        id: "evt-1",
        type: "credit",
        label: "Monthly Executive Salary",
        value: 210000,
        children: []
      },
      {
        id: "evt-2",
        type: "debit",
        label: "Penthouse Apartment Lease",
        value: -65000,
        children: []
      }
    ]
  },
  metrics: {
    confirmedEventsCount: 4,
    uncertainEventsCount: 1,
    auditedRatio: "80.0",
    primaryCustodian: "HDFC Bank (Assumed)"
  }
};
