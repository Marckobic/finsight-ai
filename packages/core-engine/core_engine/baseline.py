"""
core_engine/baseline.py
Complete baseline financial projection builder.

This module is the ENTRY POINT of the deterministic engine.
It orchestrates cashflow, savings_rate, and projection into a
single BaselineResult — the single source of truth for all downstream layers.

SYSTEM RULES:
  - No AI. No randomness. Fully deterministic.
  - build_baseline_projection() is the ONLY function that produces a BaselineResult.
  - No other module may create or modify BaselineResult directly.
"""

from shared_types.models import BaselineResult, FinancialSnapshot

from core_engine.cashflow import calculate_cashflow
from core_engine.projection import (
    calculate_monthly_savings_gap,
    calculate_time_to_goal,
    months_until_deadline,
)
from core_engine.savings_rate import calculate_savings_rate


def build_baseline_projection(snapshot: FinancialSnapshot) -> BaselineResult:
    """
    Build a complete baseline financial projection from a FinancialSnapshot.

    This is the SINGLE SOURCE OF TRUTH for all financial data in the system.
    The scenario engine, AI layer, and UI all derive their values from this output.

    Computation order:
      1. Monthly cashflow = income - fixed - variable
      2. Savings rate = (cashflow / income) × 100
      3. Goal check = current_savings >= goal_amount?
      4. Time to goal = ceil(remaining / cashflow)  [None if cashflow <= 0]
      5. Deadline months = months from snapshot_date to goal.deadline
      6. Monthly savings gap = max(0, needed_per_month - cashflow)

    Args:
        snapshot: A validated FinancialSnapshot containing income, expenses,
                  savings, and goal data.

    Returns:
        BaselineResult with all computed metrics. This is the truth layer output.

    Examples:
        Given a snapshot with:
          income=6000, fixed=2000, variable=1500, savings=5000,
          goal_amount=20000, snapshot_date="2026-01-01", deadline="2027-07-01"

        Returns:
          monthly_cashflow = 2500.0
          savings_rate = 41.67%
          time_to_goal_months = 6  (ceil(15000 / 2500))
          monthly_savings_gap = 0.0  (already on track)
          goal_already_met = False
    """
    # Step 1: Cashflow
    monthly_cashflow = calculate_cashflow(
        income=snapshot.income.monthly,
        fixed_expenses=snapshot.expenses.fixed,
        variable_expenses=snapshot.expenses.variable,
    )

    # Step 2: Savings rate
    savings_rate = calculate_savings_rate(
        cashflow=monthly_cashflow,
        income=snapshot.income.monthly,
    )

    # Step 3: Goal check
    goal_already_met = snapshot.savings.balance >= snapshot.goal.target_amount

    # Step 4: Time to goal
    time_to_goal = calculate_time_to_goal(
        goal_amount=snapshot.goal.target_amount,
        current_savings=snapshot.savings.balance,
        monthly_cashflow=monthly_cashflow,
    )

    # Step 5: Deadline months
    deadline_months = months_until_deadline(
        snapshot_date=snapshot.snapshot_date,
        deadline=snapshot.goal.deadline,
    )

    # Step 6: Monthly savings gap
    monthly_savings_gap = calculate_monthly_savings_gap(
        goal_amount=snapshot.goal.target_amount,
        current_savings=snapshot.savings.balance,
        deadline_months=deadline_months,
        monthly_cashflow=monthly_cashflow,
    )

    return BaselineResult(
        monthly_cashflow=monthly_cashflow,
        savings_rate=round(savings_rate, 4),
        time_to_goal_months=time_to_goal,
        monthly_savings_gap=round(monthly_savings_gap, 2),
        goal_already_met=goal_already_met,
    )
