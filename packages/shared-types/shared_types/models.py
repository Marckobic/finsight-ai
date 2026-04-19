"""
shared_types/models.py
FinSight.ai — Shared data contracts (DTOs).

These Pydantic models are the ONLY data shapes that flow between layers.
Every module speaks this language. Nothing else passes between layers.

Data flow:
  ManualInputProvider → FinancialSnapshot
  FinancialSnapshot   → BaselineResult        (core-engine)
  BaselineResult      → ScenarioResult        (scenario-engine)
  ScenarioResult      → AIExplanationInput    (ai-layer)
  AIExplanationOutput → ValidationResult      (validation-gateway)
  ValidationResult    → UI                    (mobile app)
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, field_validator, model_validator

# ---------------------------------------------------------------------------
# LAYER 1 — Input / Financial Snapshot
# ---------------------------------------------------------------------------


class IncomeData(BaseModel):
    """User's monthly income data."""

    monthly: float
    income_type: Literal["stable", "variable"] = "stable"
    income_volatile: bool = False

    @field_validator("monthly")
    @classmethod
    def monthly_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"income.monthly must be >= 0, got {v}")
        return v


class ExpensesData(BaseModel):
    """User's monthly expense breakdown."""

    fixed: float      # rent, subscriptions, loans
    variable: float   # food, transport, lifestyle
    total: float      # must equal fixed + variable

    @field_validator("fixed", "variable", "total")
    @classmethod
    def must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"expense values must be >= 0, got {v}")
        return v

    @model_validator(mode="after")
    def total_must_match(self) -> ExpensesData:
        expected = round(self.fixed + self.variable, 10)
        if abs(self.total - expected) > 1e-6:
            raise ValueError(
                f"expenses.total ({self.total}) must equal fixed ({self.fixed}) "
                f"+ variable ({self.variable}) = {expected}"
            )
        return self


class SavingsData(BaseModel):
    """User's savings state."""

    balance: float                # current savings balance (USD)
    monthly_contribution: float   # current monthly savings contribution (USD)

    @field_validator("balance", "monthly_contribution")
    @classmethod
    def must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"savings values must be >= 0, got {v}")
        return v


class CashflowData(BaseModel):
    """Computed monthly cashflow (stored in snapshot for reference)."""

    monthly: float  # can be negative


class GoalData(BaseModel):
    """User's financial goal."""

    target_amount: float
    deadline: str   # ISO8601 date string (YYYY-MM-DD)
    type: str       # "emergency_fund" | "pay_off_debt" | "save_for_home" | "build_wealth" | "custom"

    @field_validator("target_amount")
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"goal.target_amount must be >= 0, got {v}")
        return v


class FinancialSnapshot(BaseModel):
    """
    Normalized financial state — the single input to the deterministic engine.

    This schema is provider-agnostic. In MVP, ManualInputProvider populates it.
    When PlaidProvider is activated, it maps to the same schema — zero engine changes.
    """

    user_id: str
    snapshot_date: str   # ISO8601 date string (YYYY-MM-DD)
    income: IncomeData
    expenses: ExpensesData
    savings: SavingsData
    cashflow: CashflowData
    goal: GoalData


# ---------------------------------------------------------------------------
# LAYER 2 — Deterministic Engine Output (Baseline)
# ---------------------------------------------------------------------------


class BaselineResult(BaseModel):
    """
    Output of the deterministic financial engine (TRUTH LAYER).

    RULE: These values are the ONLY valid source of financial truth.
    No other layer may override or modify these values.
    """

    monthly_cashflow: float          # income - fixed - variable (USD)
    savings_rate: float              # (cashflow / income) * 100 — percentage
    time_to_goal_months: Optional[int]  # None if cashflow <= 0 (unreachable)
    monthly_savings_gap: float       # how much more/month needed to hit deadline
    goal_already_met: bool           # True if current_savings >= goal_amount


# ---------------------------------------------------------------------------
# LAYER 3 — Scenario Engine Input/Output
# ---------------------------------------------------------------------------


class BehaviorChange(BaseModel):
    """
    A single behavioral change to simulate.

    RULE: Scenario engine simulates ONE change at a time (MVP).
    Multi-action scenarios are out of scope for MVP.
    """

    type: Literal["savings_increase", "expense_cut"]
    value: float   # USD per month (positive)

    @field_validator("value")
    @classmethod
    def must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"behavior_change.value must be >= 0, got {v}")
        return v


class ScenarioInput(BaseModel):
    """Full input to the scenario engine."""

    financial_snapshot: FinancialSnapshot
    baseline: BaselineResult
    behavior_change: BehaviorChange
    adherence_rate: float   # 0.1–0.95 (clamped by engine if out of range)


class ScenarioResult(BaseModel):
    """
    Output of the scenario engine (BEHAVIORAL SIMULATION LAYER).

    RULE: These values derive from baseline + adherence modeling.
    They are deterministic given the same inputs + adherence_rate.
    The 'probabilistic' UI effect comes from the adherence slider, not from
    randomness in the engine.
    """

    baseline_months: Optional[int]         # from deterministic engine
    scenario_months: Optional[int]         # projected with behavior change
    delta_months: Optional[int]            # baseline - scenario (positive = improvement)
    adherence_rate: float                  # clamped to [0.1, 0.95]
    effective_monthly_change: float        # value × adherence_rate (USD)
    scenario_monthly_cashflow: float       # baseline_cashflow + effective_change
    is_improvement: bool                   # True if scenario is better than baseline


# ---------------------------------------------------------------------------
# LAYER 4 — AI Layer Contracts (STRICT)
# ---------------------------------------------------------------------------


class AIExplanationInput(BaseModel):
    """
    Structured input to the AI layer.

    RULE: AI receives ONLY this schema. No raw financial data.
    No strings. No free-form context. Structured JSON only.
    """

    baseline_months: Optional[int]
    scenario_months: Optional[int]
    delta_months: Optional[int]
    monthly_change_amount: float   # USD (the behavior_change.value)
    adherence_rate: float
    behavior_type: str             # "savings_increase" | "expense_cut"
    goal_type: str


class AIExplanationOutput(BaseModel):
    """
    Output of the AI layer.

    RULE: AI outputs ONLY these text fields.
    No numbers generated by AI. No financial calculations.
    All numeric values in the explanation must come from AIExplanationInput.
    """

    recommendation: str    # e.g. "Increase monthly savings by $300"
    explanation: str       # natural language explanation of the scenario result
    # Quality scoring fields — optional for backward compatibility
    summary: str = ""
    confidence: Literal["high", "medium", "low"] = "medium"
    reasoning: str = ""
    key_assumptions: list[str] = []


# ---------------------------------------------------------------------------
# LAYER 5 — Validation Gateway Output
# ---------------------------------------------------------------------------


class ValidationResult(BaseModel):
    """
    Output of the validation gateway (HARD SAFETY LAYER).

    If valid=False, fallback_used=True and validated_output contains
    the deterministic fallback template — never None if fallback_used=True.
    """

    valid: bool
    errors: list[str]
    fallback_used: bool
    validated_output: Optional[AIExplanationOutput]


# ---------------------------------------------------------------------------
# FEEDBACK LOOP (Post-MVP EWMA — schema defined now, logic in Phase 3)
# ---------------------------------------------------------------------------


class FeedbackEvent(BaseModel):
    """
    A single user feedback event (accept/reject/modify).

    EWMA adherence update formula (α = 0.3):
        new_rate = (0.3 × observed_execution) + (0.7 × prior_rate)
    Minimum 3 events per category before rates update.
    """

    user_id: str
    event_type: Literal["accepted", "rejected", "modified"]
    category: str                  # e.g. "dining", "savings", "subscriptions"
    execution_rate: float          # 1.0=fully / 0.5=partially / 0.0=not at all
    prior_adherence_rate: float
    timestamp: str                 # ISO8601


class AdherenceState(BaseModel):
    """Per-category adherence rates for a user."""

    user_id: str
    categories: dict[str, float]   # category → current adherence rate
    event_counts: dict[str, int]   # category → number of feedback events
    last_updated: str              # ISO8601
