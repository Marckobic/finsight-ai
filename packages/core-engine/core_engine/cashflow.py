"""
core_engine/cashflow.py
Deterministic monthly cashflow calculation.

SYSTEM RULES:
  - No AI. No randomness. Fully deterministic.
  - Single source of truth for cashflow math.
  - Identical inputs MUST produce identical outputs, always.

Formula:
  cashflow = income - fixed_expenses - variable_expenses
"""


def calculate_cashflow(
    income: float,
    fixed_expenses: float,
    variable_expenses: float,
) -> float:
    """
    Compute net monthly cashflow.

    Args:
        income: Monthly take-home income in USD. Must be >= 0.
        fixed_expenses: Monthly fixed expenses in USD (rent, subscriptions, loans).
                        Must be >= 0.
        variable_expenses: Monthly variable expenses in USD (food, transport, lifestyle).
                           Must be >= 0.

    Returns:
        Net monthly cashflow in USD.
        Positive = money left over after expenses.
        Zero     = break-even (no surplus, no deficit).
        Negative = expenses exceed income (overspending).

    Raises:
        ValueError: If any input is negative.

    Examples:
        >>> calculate_cashflow(5000, 2000, 1000)
        2000.0
        >>> calculate_cashflow(3000, 2000, 1000)
        0.0
        >>> calculate_cashflow(3000, 2500, 1500)
        -1000.0
    """
    if income < 0:
        raise ValueError(f"income must be >= 0, got {income}")
    if fixed_expenses < 0:
        raise ValueError(f"fixed_expenses must be >= 0, got {fixed_expenses}")
    if variable_expenses < 0:
        raise ValueError(f"variable_expenses must be >= 0, got {variable_expenses}")

    return float(income - fixed_expenses - variable_expenses)
