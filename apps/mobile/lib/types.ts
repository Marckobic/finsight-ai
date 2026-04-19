/**
 * lib/types.ts
 * TypeScript interfaces mirroring all Pydantic models in shared_types/models.py.
 *
 * Keep in sync with packages/shared-types/shared_types/models.py.
 * These are the ONLY shapes that flow between the mobile app and the API.
 */

// ---------------------------------------------------------------------------
// Layer 1 — Input / Financial Snapshot
// ---------------------------------------------------------------------------

export interface IncomeData {
  monthly: number;
  income_type: "stable" | "variable";
  income_volatile: boolean;
}

export interface ExpensesData {
  fixed: number;
  variable: number;
  total: number; // must equal fixed + variable
}

export interface SavingsData {
  balance: number;
  monthly_contribution: number;
}

export interface CashflowData {
  monthly: number; // can be negative
}

export interface GoalData {
  target_amount: number;
  deadline: string; // ISO8601 date YYYY-MM-DD
  type:
    | "emergency_fund"
    | "extend_runway"
    | "pay_off_debt"
    | "save_for_home"
    | "build_wealth"
    | "custom";
}

export interface FinancialSnapshot {
  user_id: string;
  snapshot_date: string; // ISO8601 date YYYY-MM-DD
  income: IncomeData;
  expenses: ExpensesData;
  savings: SavingsData;
  cashflow: CashflowData;
  goal: GoalData;
}

// ---------------------------------------------------------------------------
// Layer 2 — Baseline
// ---------------------------------------------------------------------------

export interface BaselineResult {
  monthly_cashflow: number;
  savings_rate: number; // percentage
  time_to_goal_months: number | null;
  monthly_savings_gap: number;
  goal_already_met: boolean;
}

export interface BaselineResponse {
  status: string;
  data: BaselineResult;
  latency_ms: number;
}

// ---------------------------------------------------------------------------
// Layer 3 — Scenario
// ---------------------------------------------------------------------------

export type BehaviorType = "savings_increase" | "expense_cut";

export interface BehaviorChange {
  type: BehaviorType;
  value: number; // USD per month, positive
}

export interface ScenarioInput {
  financial_snapshot: FinancialSnapshot;
  baseline: BaselineResult;
  behavior_change: BehaviorChange;
  adherence_rate: number; // 0.1–0.95
}

export interface ScenarioResult {
  baseline_months: number | null;
  scenario_months: number | null;
  delta_months: number | null;
  adherence_rate: number;
  effective_monthly_change: number;
  scenario_monthly_cashflow: number;
  is_improvement: boolean;
}

export interface ValidationSummary {
  valid: boolean;
  errors: string[];
}

export interface ScenarioResponse {
  status: string;
  data: ScenarioResult;
  validation: ValidationSummary;
  latency_ms: number;
}

// ---------------------------------------------------------------------------
// Layer 4 — AI Explanation
// ---------------------------------------------------------------------------

export interface AIExplanationInput {
  baseline_months: number | null;
  scenario_months: number | null;
  delta_months: number | null;
  monthly_change_amount: number;
  adherence_rate: number;
  behavior_type: BehaviorType;
  goal_type: string;
}

export interface AIExplanationOutput {
  recommendation: string;
  explanation: string;
}

export interface ExplainValidation {
  valid: boolean;
  fallback_used: boolean;
  errors: string[];
}

export interface AIQualitySummary {
  total: number;
  status: "approved" | "degraded" | "fallback";
  reasons: string[];
}

export interface ExplainResponse {
  status: string;
  data: AIExplanationOutput;
  validation: ExplainValidation;
  quality?: AIQualitySummary;
  latency_ms: number;
}

// ---------------------------------------------------------------------------
// Decision / Feedback
// ---------------------------------------------------------------------------

export type DecisionEventType = "accepted" | "rejected" | "modified";

export interface DecisionEvent {
  user_id: string;
  event_type: DecisionEventType;
  scenario_result: ScenarioResult;
  timestamp: string; // ISO8601
}

// ---------------------------------------------------------------------------
// API error shape
// ---------------------------------------------------------------------------

export interface ApiError {
  status: "error";
  message: string;
  code: string;
  errors?: unknown[];
}
