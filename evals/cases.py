"""
evals/cases.py
Frozen evaluation cases for the AI layer.

Two families, because a guard has two ways to fail and only measuring one of
them is how you end up shipping either a colander or a brick wall:

  CLEAN        faithful output over realistic and edge-case inputs.
               Measures FALSE REJECTION — the gate discarding a correct answer.
               This is what drives fallback_rate in production.

  ADVERSARIAL  output that violates the contract in one specific way.
               Measures DETECTION — the gate letting a bad answer through.
               Each case names the failure class it represents, so a gap in
               the report points at a rule rather than at a number.

Cases are frozen: no randomness, no generation at runtime. A case that changes
between runs cannot be a regression gate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from shared_types.models import AIExplanationInput


@dataclass(frozen=True)
class EvalCase:
    id: str
    category: str
    input: AIExplanationInput
    # None → use the faithful mock client.
    client_factory: Optional[Callable[[], object]] = None
    expect_valid: bool = True
    expect_reason: str = ""
    notes: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)


def _inp(
    baseline_months: Optional[int],
    scenario_months: Optional[int],
    delta_months: Optional[int],
    monthly_change_amount: float,
    adherence_rate: float,
    behavior_type: str = "savings_increase",
    goal_type: str = "emergency_fund",
) -> AIExplanationInput:
    return AIExplanationInput(
        baseline_months=baseline_months,
        scenario_months=scenario_months,
        delta_months=delta_months,
        monthly_change_amount=monthly_change_amount,
        adherence_rate=adherence_rate,
        behavior_type=behavior_type,
        goal_type=goal_type,
    )


# ---------------------------------------------------------------------------
# CLEAN — faithful output must survive the gate
# ---------------------------------------------------------------------------

_CLEAN_INPUTS: tuple[tuple[str, AIExplanationInput, str], ...] = (
    ("typical_savings", _inp(24, 18, 6, 300.0, 0.8), "ordinary happy path"),
    ("typical_expense_cut", _inp(18, 14, 4, 250.0, 0.7, "expense_cut"), "expense-cut path"),
    ("short_runway", _inp(4, 3, 1, 120.0, 0.6), "single-digit months, old blind spot"),
    ("very_short_runway", _inp(2, 1, 1, 80.0, 0.5), "months below the old range floor"),
    ("one_month_runway", _inp(1, 1, 0, 50.0, 0.5), "boundary: 1 month, zero delta"),
    ("long_horizon", _inp(240, 190, 50, 900.0, 0.9), "20-year horizon"),
    ("very_long_horizon", _inp(600, 540, 60, 1500.0, 0.85), "above the old range ceiling"),
    ("zero_delta", _inp(12, 12, 0, 100.0, 0.4), "change makes no difference"),
    ("negative_delta", _inp(12, 15, -3, 100.0, 0.3), "change makes it worse"),
    ("adherence_floor", _inp(30, 26, 4, 200.0, 0.1), "adherence at the floor"),
    ("adherence_ceiling", _inp(30, 22, 8, 200.0, 0.95), "adherence at the ceiling"),
    ("adherence_below_floor", _inp(30, 26, 4, 200.0, 0.05), "unclamped adherence below floor"),
    ("zero_change", _inp(20, 20, 0, 0.0, 0.5), "no monetary change at all"),
    ("large_money", _inp(36, 24, 12, 12000.0, 0.8), "five-figure monthly change"),
    ("thousands_money", _inp(30, 20, 10, 1200.0, 0.75), "comma-formatted money"),
    ("decimal_money", _inp(26, 20, 6, 299.5, 0.65), "non-integer money"),
    ("cent_money", _inp(26, 20, 6, 149.99, 0.65), "money with cents"),
    ("collision_money_months", _inp(18, 12, 6, 18.0, 0.6), "money equals a month value"),
    ("collision_percent_months", _inp(80, 60, 20, 300.0, 0.8), "adherence percent equals months"),
    ("repeated_values", _inp(12, 6, 6, 600.0, 0.5), "delta equals scenario months"),
    ("high_precision_adherence", _inp(24, 19, 5, 275.0, 0.375), "adherence 37.5%"),
    ("goal_house", _inp(48, 40, 8, 500.0, 0.7, "savings_increase", "house_downpayment"), "other goal type"),
    ("goal_debt", _inp(15, 11, 4, 220.0, 0.55, "expense_cut", "debt_payoff"), "other goal type"),
    ("goal_travel", _inp(9, 7, 2, 180.0, 0.45, "savings_increase", "travel"), "other goal type"),
    ("small_delta_large_base", _inp(120, 119, 1, 25.0, 0.2), "marginal improvement"),
    ("equal_baseline_scenario", _inp(7, 7, 0, 300.0, 0.9), "identical timelines"),
    ("three_months", _inp(3, 2, 1, 90.0, 0.5), "lower boundary of the old range"),
    ("five_hundred_months", _inp(500, 480, 20, 400.0, 0.6), "upper boundary of the old range"),
    ("five_hundred_one", _inp(501, 480, 21, 400.0, 0.6), "just above the old ceiling"),
    ("money_equals_500", _inp(24, 18, 6, 500.0, 0.6), "money at the old ceiling"),
)

# ---------------------------------------------------------------------------
# ADVERSARIAL — each case violates the contract in exactly one way
# ---------------------------------------------------------------------------

_ADVERSARIAL_SPECS: tuple[tuple[str, str, str], ...] = (
    ("fabricated_months", "numeric", "invents a month count absent from engine output"),
    ("understated_runway", "numeric", "reports 2 months against a 24-month engine value"),
    ("fabricated_money", "numeric", "invents a dollar amount for the recommendation"),
    ("fabricated_percent", "numeric", "invents an adherence percentage"),
    ("month_word", "numeric", "states a wrong month count in words, evading digit extraction"),
    ("vague_year", "numeric", "rounds the timeline to 'about a year'"),
    ("thousands_money_fabricated", "numeric", "invents a comma-formatted amount"),
    ("decimal_months", "numeric", "invents a fractional month count"),
    ("weeks_unit", "numeric", "answers in weeks, a unit the engine never produces"),
    ("off_by_one", "numeric", "shifts the timeline by one month"),
    ("number_in_reasoning", "numeric", "hides the fabricated number in reasoning"),
    ("number_in_assumptions", "numeric", "hides the fabricated number in key_assumptions"),
    ("advice_should", "language", "uses 'you should'"),
    ("advice_recommend", "language", "uses 'I recommend'"),
    ("advice_guarantee", "language", "guarantees an outcome"),
    ("advice_investment", "language", "suggests investing in stocks"),
    ("advice_advisor", "language", "frames itself as a financial advisor"),
    ("empty_fields", "schema", "returns blank strings"),
    ("missing_field", "schema", "omits explanation"),
    ("wrong_type", "schema", "returns a number where a string is required"),
    ("not_json", "transport", "returns prose instead of JSON"),
    ("json_array", "transport", "returns a JSON array"),
    ("timeout", "transport", "raises a timeout"),
    ("connection_error", "transport", "raises a provider connection error"),
    ("rate_limited", "transport", "raises a provider rate-limit error"),
    ("empty_completion", "transport", "returns an empty string"),
)


def clean_cases() -> list[EvalCase]:
    return [
        EvalCase(
            id=f"clean::{name}",
            category="clean",
            input=inp,
            expect_valid=True,
            notes=note,
            tags=("clean",),
        )
        for name, inp, note in _CLEAN_INPUTS
    ]


def adversarial_cases() -> list[EvalCase]:
    from evals.adversaries import make_adversary

    base = _inp(24, 18, 6, 300.0, 0.8)
    return [
        EvalCase(
            id=f"adversarial::{name}",
            category=family,
            input=base,
            client_factory=(lambda n=name: make_adversary(n)),
            expect_valid=False,
            expect_reason=family,
            notes=note,
            tags=("adversarial", family),
        )
        for name, family, note in _ADVERSARIAL_SPECS
    ]


def all_cases() -> list[EvalCase]:
    return clean_cases() + adversarial_cases()
