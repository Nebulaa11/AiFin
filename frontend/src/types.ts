export type Loan = { name: string; amount: number; interest_rate: number; emi: number };
export type Asset = { type: string; value: number; expected_return: number };
export type Goal = {
  name: string;
  target_amount: number;
  target_years: number;
  goal_type: "savings" | "debt_free" | "investment" | "custom";
};

export type UserProfile = {
  age: number;
  income_monthly: number;
  expenses_monthly: number;
  savings: number;
  loans: Loan[];
  assets: Asset[];
  risk_tolerance: "low" | "medium" | "high";
  financial_goals: Goal[];
  dependents: number;
};

export type AuthUser = {
  id: number;
  email: string;
  name: string;
  picture_url: string | null;
};

export type AnalyzeResponse = {
  emergency_fund_target: number;
  emergency_fund_months: number;
  recommended_monthly_investment: number;
  best_loan_repayment_order: string[];
  projected_net_worth_best: number;
  strategies: {
    name: string;
    description: string;
    future_net_worth: number;
    risk_score: number;
    cash_flow_stability: number;
    composite_score: number;
    monthly_investment_suggested: number;
    loan_prepayment_monthly: number;
    goal_fit_score: number;
  }[];
  best_strategy_name: string;
  explanation: string;
  engine_summary: {
    monthly_surplus: number;
    months_of_expenses_in_savings: number;
    total_assets: number;
  };
  goal_progress: {
    name: string;
    target_amount: number;
    target_years: number;
    projected_amount: number;
    on_track: boolean;
    gap: number;
  }[];
  debt_vs_invest: {
    recommendation: string;
    highest_loan_rate: number;
    expected_return: number;
    rationale: string;
  };
  next_actions: string[];
  assumptions: {
    horizon_years: number;
    market_return_pct: number;
    emergency_fund_months: number;
    inflation_pct: number;
    tax_included: boolean;
  };
  timeline: {
    month: number;
    net_worth: number;
    investments: number;
    total_debt: number;
    liquid_savings: number;
  }[];
  sensitivity: { label: string; return_pct: number; projected_net_worth: number }[];
  ml_strategy_hint: string | null;
};

export type ChatSession = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type ChatMessage = {
  id: number;
  role: string;
  content: string;
  created_at: string;
};

export type Tab = "dashboard" | "assets" | "debts" | "strategy";

export function fmt(n: number) {
  return `₹ ${n.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

export function defaultProfile(): UserProfile {
  return {
    age: 28,
    income_monthly: 80000,
    expenses_monthly: 40000,
    savings: 200000,
    loans: [{ name: "car loan", amount: 500000, interest_rate: 10, emi: 12000 }],
    assets: [],
    risk_tolerance: "medium",
    financial_goals: [{ name: "Emergency + invest", target_amount: 1000000, target_years: 5, goal_type: "investment" }],
    dependents: 0,
  };
}

export function totalDebt(profile: UserProfile) {
  return profile.loans.reduce((s, l) => s + l.amount, 0);
}

export function totalAssets(profile: UserProfile) {
  return profile.assets.reduce((s, a) => s + a.value, 0) + profile.savings;
}

export function netWorth(profile: UserProfile) {
  return totalAssets(profile) - totalDebt(profile);
}
