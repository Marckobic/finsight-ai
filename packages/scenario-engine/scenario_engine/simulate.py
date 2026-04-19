"""
scenario_engine/simulate.py
Behavioral simulation engine — the "What If?" layer.

This module simulates the impact of a SINGLE behavioral change on the user's
financial trajectory. It is NOT a general math tool. It does not accept arbitrary
financial queries — only a baseline + one change type + an adherence assumption.

SYSTEM RULES:
  - Input MUST include a pre-computed BaselineResult from core-engine (truth).
  - Output is deterministic given the same inputs + adherence_rate.
  - The 'probabilistic' UI effect (Screen 6 adherence slider) comes from the user
    adjusting adherence_rate, not from randomness in this engine.
  - adherence_rate is clamped to [0.1, 0.95] — system never assumes zero or
    perfect compliance (PRD Section 7.6).

Adherence model:
  effective_change = behavior_change.value × adherence_rate
  scenario_cashflow = baseline.monthly_cashflow + effective_change

  Example: $300/month savings increase at 70% adherence
    → effective_change = $300 × 0.70 = $210/month
    → scenario_cashflow = baseline_cashflow + $210
    → This models realistic partial compliance.

Supported behavior change types (MVP):
  - savings_increase: User saves more each month
  - expense_cut: User reduces spending (both increase available cashflow)
"""


from core_engine.projection import calculate_time_to_goal
from shared_types.models import (
    BaselineResult,
    BehaviorChange,
    FinancialSnapshot,
    ScenarioResult,
)

# PRD Section 7.6: adherence bounds
ADHERENCE_FLOOR: float = 0.1
ADHERENCE_CEILING: float = 0.95


def clamp_adherence(rate: float) -> float:
    """
    Clamp adherence rate to the valid range [0.1, 0.95].

    PRD guarantee: system never assumes zero compliance (floor=0.1)
    and never assumes perfect compliance (ceiling=0.95).

    Args:
        rate: Raw adherence rate input (e.g., from UI slider).

    Returns:
        Clamped rate in [0.1, 0.95].
    """
    return max(ADHERENCE_FLOOR, min(ADHERENCE_CEILING, rate))


def simulate_scenario(
    financial_snapshot: FinancialSnapshot,
    baseline: BaselineResult,
    behavior_change: BehaviorChange,
    adherence_rate: float,
) -> ScenarioResult:
    """
    Simulate the financial impact of a single behavioral change.

    This is a behavioral simulation — it answers: "If the user makes this change
    with this level of consistency, how does their goal timeline change?"

    The adherence_rate is the key parameter. It maps to the orange slider on
    Screen 6 (PRD UX). At 50% adherence, only half the change is executed on
    average. At 95%, almost all of it is.

    Args:
        financial_snapshot: User's current financial state (from truth layer).
                            Used to compute goal timeline with scenario cashflow.
        baseline: Pre-computed BaselineResult from the deterministic engine.
                  This is the "before" state. MUST be from core-engine.
        behavior_change: The single behavioral change to simulate.
                         type: "savings_increase" | "expense_cut"
                         value: USD per month (positive).
        adherence_rate: Expected compliance rate. 0.1 = 10%, 0.95 = 95%.
                        Clamped automatically. Passed directly from UI slider.

    Returns:
        ScenarioResult with:
          - baseline_months: the pre-change timeline (from deterministic engine)
          - scenario_months: projected timeline with this change + adherence
          - delta_months: improvement (positive = faster, negative = slower)
          - effective_monthly_change: the USD change actually modeled
          - is_improvement: True if scenario is better than baseline

    Examples:
        >>> simulate_scenario(
        ...     snapshot, baseline_with_cashflow_500,
        ...     BehaviorChange(type="savings_increase", value=300),
        ...     adherence_rate=0.70
        ... )
        # effective_change = 300 × 0.70 = 210
        # scenario_cashflow = 500 + 210 = 710
        # scenario_months = ceil(remaining / 710)
    """
    if behavior_change.value < 0:
        raise ValueError(
            f"behavior_change.value must be >= 0, got {behavior_change.value}"
        )

    # Clamp adherence to valid bounds (SYSTEM RULE)
    clamped_rate = clamp_adherence(adherence_rate)

    # Compute effective change: how much of the behavioral change is actually executed
    effective_change = behavior_change.value * clamped_rate

    # Both savings_increase and expense_cut increase available cashflow for goal
    scenario_cashflow = baseline.monthly_cashflow + effective_change

    # Compute scenario time-to-goal using the deterministic engine
    scenario_months = calculate_time_to_goal(
        goal_amount=financial_snapshot.goal.target_amount,
        current_savings=financial_snapshot.savings.balance,
        monthly_cashflow=scenario_cashflow,
    )

    baseline_months = baseline.time_to_goal_months

    # Compute delta (positive = faster = improvement)
    if baseline_months is not None and scenario_months is not None:
        delta_months = baseline_months - scenario_months
    else:
        delta_months = None

    # Determine improvement:
    # - Positive delta = scenario is faster (improvement)
    # - baseline was None (unreachable) and scenario is reachable = improvement
    is_improvement = (
        (delta_months is not None and delta_months > 0)
        or (baseline_months is None and scenario_months is not None)
    )

    return ScenarioResult(
        baseline_months=baseline_months,
        scenario_months=scenario_months,
        delta_months=delta_months,
        adherence_rate=clamped_rate,
        effective_monthly_change=round(effective_change, 2),
        scenario_monthly_cashflow=round(scenario_cashflow, 2),
        is_improvement=is_improvement,
    )


def simulate_adherence_range(
    financial_snapshot: FinancialSnapshot,
    baseline: BaselineResult,
    behavior_change: BehaviorChange,
    adherence_steps: int = 5,
) -> list[ScenarioResult]:
    """
    Simulate a range of adherence rates to produce the full slider spectrum.

    Used by the UI to pre-compute the scenario curve for Screen 6.
    Returns adherence_steps evenly-spaced results between FLOOR and CEILING.

    Args:
        financial_snapshot: User's current financial state.
        baseline: Pre-computed baseline from deterministic engine.
        behavior_change: The behavioral change to simulate.
        adherence_steps: Number of points on the adherence curve (default: 5).

    Returns:
        List of ScenarioResult, one per adherence step, ordered low → high.
    """
    if adherence_steps < 2:
        raise ValueError(f"adherence_steps must be >= 2, got {adherence_steps}")

    step_size = (ADHERENCE_CEILING - ADHERENCE_FLOOR) / (adherence_steps - 1)
    rates = [
        round(ADHERENCE_FLOOR + i * step_size, 4)
        for i in range(adherence_steps)
    ]

    return [
        simulate_scenario(financial_snapshot, baseline, behavior_change, rate)
        for rate in rates
    ]
