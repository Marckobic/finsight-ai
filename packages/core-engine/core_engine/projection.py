"""
core_engine/projection.py
Deterministic time-to-goal and baseline projection computations.

SYSTEM RULES:
  - No AI. No randomness. Fully deterministic.
  - Returns None (not an exception) when goal is unreachable at current cashflow.
  - Uses ceiling division: a partial month counts as a full month.

Key formulas:
  time_to_goal = ceil((goal_amount - current_savings) / monthly_cashflow)
  monthly_gap  = max(0, (remaining / deadline_months) - monthly_cashflow)
"""

import math
from datetime import date
from typing import Optional


def calculate_time_to_goal(
    goal_amount: float,
    current_savings: float,
    monthly_cashflow: float,
) -> Optional[int]:
    """
    Compute the number of months needed to reach a savings goal.

    Uses ceiling division — a partial month always counts as a full month.
    Returns 0 if the goal is already met.
    Returns None if monthly_cashflow <= 0 (goal unreachable at current rate).

    Args:
        goal_amount: Target savings amount in USD. Must be >= 0.
        current_savings: Current savings balance in USD. Must be >= 0.
        monthly_cashflow: Monthly net cashflow available toward the goal (USD).
                          Negative or zero means the goal is currently unreachable.

    Returns:
        Integer months until goal is reached (ceiling).
        0 if goal is already met (current_savings >= goal_amount).
        None if cashflow <= 0 (unreachable).

    Raises:
        ValueError: If goal_amount < 0 or current_savings < 0.

    Examples:
        >>> calculate_time_to_goal(10000, 2000, 500)
        16
        >>> calculate_time_to_goal(10000, 10000, 500)
        0
        >>> calculate_time_to_goal(10000, 0, 0)
        None
        >>> calculate_time_to_goal(10000, 0, 3000)
        4
    """
    if goal_amount < 0:
        raise ValueError(f"goal_amount must be >= 0, got {goal_amount}")
    if current_savings < 0:
        raise ValueError(f"current_savings must be >= 0, got {current_savings}")

    remaining = goal_amount - current_savings

    if remaining <= 0:
        return 0  # goal already met

    if monthly_cashflow <= 0:
        return None  # goal unreachable at current rate

    return math.ceil(remaining / monthly_cashflow)


def calculate_monthly_savings_gap(
    goal_amount: float,
    current_savings: float,
    deadline_months: int,
    monthly_cashflow: float,
) -> float:
    """
    Compute how much additional monthly savings is needed to hit the goal by deadline.

    This is the "savings gap" shown on the Baseline screen (Screen 4 in PRD):
    how much more per month the user needs to save to reach their goal on time.

    Returns 0.0 if the user is already on track or the goal is already met.

    Args:
        goal_amount: Target savings amount in USD. Must be >= 0.
        current_savings: Current savings balance in USD. Must be >= 0.
        deadline_months: Months remaining until the goal deadline. Must be >= 1.
        monthly_cashflow: Current net monthly cashflow (USD). May be negative.

    Returns:
        Additional USD per month needed to meet the deadline.
        0.0 if the user is already on track or goal is met.

    Raises:
        ValueError: If goal_amount < 0, current_savings < 0, or deadline_months < 1.

    Examples:
        >>> calculate_monthly_savings_gap(12000, 0, 12, 1000)
        0.0
        >>> calculate_monthly_savings_gap(12000, 0, 12, 500)
        500.0
        >>> calculate_monthly_savings_gap(10000, 15000, 12, 500)
        0.0
    """
    if goal_amount < 0:
        raise ValueError(f"goal_amount must be >= 0, got {goal_amount}")
    if current_savings < 0:
        raise ValueError(f"current_savings must be >= 0, got {current_savings}")
    if deadline_months < 1:
        raise ValueError(f"deadline_months must be >= 1, got {deadline_months}")

    remaining = goal_amount - current_savings

    if remaining <= 0:
        return 0.0  # goal already met

    needed_per_month = remaining / deadline_months
    gap = needed_per_month - monthly_cashflow

    return max(0.0, gap)


def months_until_deadline(snapshot_date: str, deadline: str) -> int:
    """
    Compute the number of full months from snapshot_date to the goal deadline.

    Returns at minimum 1 (even if deadline has passed or is the same day).

    Args:
        snapshot_date: ISO8601 date string (YYYY-MM-DD). Date of the financial snapshot.
        deadline: ISO8601 date string (YYYY-MM-DD). Goal deadline date.

    Returns:
        Integer number of months (minimum 1).

    Examples:
        >>> months_until_deadline("2026-01-01", "2027-01-01")
        12
        >>> months_until_deadline("2026-01-01", "2026-07-01")
        6
        >>> months_until_deadline("2026-01-15", "2026-01-20")
        1
    """
    snap = date.fromisoformat(snapshot_date)
    dead = date.fromisoformat(deadline)

    months = (dead.year - snap.year) * 12 + (dead.month - snap.month)

    # If deadline day is before snapshot day, we haven't completed the final month
    if dead.day < snap.day:
        months -= 1

    return max(1, months)
