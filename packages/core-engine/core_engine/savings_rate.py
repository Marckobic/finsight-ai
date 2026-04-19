"""
core_engine/savings_rate.py
Deterministic savings rate computation.

SYSTEM RULES:
  - No AI. No randomness. Fully deterministic.
  - Returns 0.0 when income is zero (avoids division by zero).

Formula:
  savings_rate = (cashflow / income) × 100   [percentage]
"""


def calculate_savings_rate(cashflow: float, income: float) -> float:
    """
    Compute the savings rate as a percentage of monthly income.

    Args:
        cashflow: Net monthly cashflow in USD (may be negative).
        income: Monthly take-home income in USD. Must be >= 0.

    Returns:
        Savings rate as a percentage (e.g., 40.0 means 40%).
        Returns 0.0 if income is zero (undefined rate, not an error).
        Returns a negative percentage if cashflow is negative (overspending).

    Raises:
        ValueError: If income is negative.

    Examples:
        >>> calculate_savings_rate(2000, 5000)
        40.0
        >>> calculate_savings_rate(0, 5000)
        0.0
        >>> calculate_savings_rate(-500, 5000)
        -10.0
        >>> calculate_savings_rate(0, 0)
        0.0
    """
    if income < 0:
        raise ValueError(f"income must be >= 0, got {income}")

    if income == 0:
        return 0.0

    return (cashflow / income) * 100.0
