"""
tests/test_numeric_consistency.py
Numeric consistency guard — verifies mathematical invariants across the engine.

Invariants checked for any (income, fixed, variable):
    1. savings_rate + expense_rate == 100.0  (±1e-9)  when income > 0
    2. time_to_goal always rounds UP (math.ceil), never down
    3. monthly_savings_gap >= 0 for all valid inputs

All tests are deterministic.  No randomness, no time.sleep, no network calls.
"""

import math

import pytest
from core_engine.cashflow import calculate_cashflow
from core_engine.projection import calculate_monthly_savings_gap, calculate_time_to_goal
from core_engine.savings_rate import calculate_savings_rate

# ---------------------------------------------------------------------------
# Parametrized test combinations
# ---------------------------------------------------------------------------
# Each entry is (income, fixed, variable).
# Covers: standard budgets, tight budgets, high earners, break-even (cashflow=0),
# floats with many decimals, tiny income, very large income, and edge cases
# where income=0 (all-zero) or cashflow is negative.
# ---------------------------------------------------------------------------

_PARAMS = [
    # (income, fixed, variable)
    (5000.0, 2000.0, 1000.0),               # standard positive cashflow
    (3000.0, 2000.0, 500.0),                # tight budget, small surplus
    (10000.0, 5000.0, 3000.0),              # high income, moderate expenses
    (1500.0, 800.0, 400.0),                 # constrained planner
    (50000.0, 20000.0, 15000.0),            # high earner
    (2500.50, 1000.25, 750.75),             # floats with many decimals
    (0.01, 0.0, 0.0),                       # near-zero income (edge)
    (999999.99, 0.0, 0.0),                  # very large income
    (1000.0, 600.0, 400.0),                 # break-even: cashflow == 0
    (7777.77, 3333.33, 1111.11),            # many decimal places
    (0.0, 0.0, 0.0),                        # all-zero (income=0 edge case)
    (1000.123456789, 500.111111111, 200.222222222),  # extreme float precision
]

# Fixed goal parameters used for projection tests
_GOAL_AMOUNT = 10000.0
_CURRENT_SAVINGS = 1000.0
_DEADLINE_MONTHS = 24


# ---------------------------------------------------------------------------
# 1. savings_rate + expense_rate == 100.0
# ---------------------------------------------------------------------------


class TestRatioIdentity:
    """
    savings_rate + expense_rate must equal 100.0 (within floating-point tolerance).

    Mathematical identity:
        savings_rate  = (cashflow / income) × 100
                      = ((income - expenses) / income) × 100
        expense_rate  = (expenses / income) × 100
        sum           = income / income × 100 = 100.0
    """

    @pytest.mark.parametrize("income, fixed, variable", _PARAMS)
    def test_savings_rate_plus_expense_rate_equals_100(self, income, fixed, variable):
        if income <= 0:
            pytest.skip("Ratio is undefined when income=0")

        cashflow = calculate_cashflow(income, fixed, variable)
        savings_rate = calculate_savings_rate(cashflow, income)
        expense_rate = (fixed + variable) / income * 100.0

        assert abs(savings_rate + expense_rate - 100.0) < 1e-9, (
            f"savings_rate={savings_rate} + expense_rate={expense_rate} "
            f"≠ 100.0 for income={income}, fixed={fixed}, variable={variable}"
        )


# ---------------------------------------------------------------------------
# 2. time_to_goal uses ceiling division (rounds UP, never down)
# ---------------------------------------------------------------------------


class TestTimeToGoalCeilingDivision:
    """
    calculate_time_to_goal must use math.ceil — a partial month is a full month.

    Verifies:
        result == math.ceil(remaining / cashflow)
        result >= remaining / cashflow   (never rounded down)
    """

    @pytest.mark.parametrize("income, fixed, variable", _PARAMS)
    def test_time_to_goal_rounds_up(self, income, fixed, variable):
        cashflow = calculate_cashflow(income, fixed, variable)
        result = calculate_time_to_goal(_GOAL_AMOUNT, _CURRENT_SAVINGS, cashflow)

        if cashflow <= 0:
            # Unreachable goal — must return None
            assert result is None
            return

        remaining = _GOAL_AMOUNT - _CURRENT_SAVINGS

        if remaining <= 0:
            assert result == 0
            return

        # Ceiling property: result must equal math.ceil of exact division
        exact = remaining / cashflow
        assert result == math.ceil(exact), (
            f"time_to_goal={result} != math.ceil({exact})={math.ceil(exact)} "
            f"for cashflow={cashflow}"
        )
        # And it must never be strictly below the exact value (no floor rounding)
        assert result >= exact, (
            f"time_to_goal={result} < exact={exact}: rounding down detected"
        )

    def test_non_integer_division_rounds_up(self):
        """Explicit check: 10001 / 1000 = 10.001 → ceil = 11, not 10."""
        result = calculate_time_to_goal(
            goal_amount=11001.0,
            current_savings=0.0,
            monthly_cashflow=1000.0,
        )
        # 11001 / 1000 = 11.001 → ceil = 12
        assert result == 12

    def test_exact_integer_division_no_extra_month(self):
        """When division is exact (e.g. 10000 / 1000 = 10), result is 10, not 11."""
        result = calculate_time_to_goal(
            goal_amount=10000.0,
            current_savings=0.0,
            monthly_cashflow=1000.0,
        )
        assert result == 10


# ---------------------------------------------------------------------------
# 3. monthly_savings_gap >= 0 for all valid inputs
# ---------------------------------------------------------------------------


class TestMonthlySavingsGapNonNegative:
    """
    calculate_monthly_savings_gap must never return a negative value.
    Even when cashflow greatly exceeds the required pace, the gap is 0.0.
    """

    @pytest.mark.parametrize("income, fixed, variable", _PARAMS)
    def test_gap_never_negative(self, income, fixed, variable):
        cashflow = calculate_cashflow(income, fixed, variable)

        gap = calculate_monthly_savings_gap(
            goal_amount=_GOAL_AMOUNT,
            current_savings=_CURRENT_SAVINGS,
            deadline_months=_DEADLINE_MONTHS,
            monthly_cashflow=cashflow,
        )

        assert gap >= 0, (
            f"monthly_savings_gap={gap} is negative for "
            f"income={income}, fixed={fixed}, variable={variable}"
        )

    def test_gap_is_zero_when_on_track(self):
        """User already saving more per month than needed — gap must be 0.0."""
        # required = 10000/12 = 833.33/mo; cashflow=2000 > needed → gap=0
        gap = calculate_monthly_savings_gap(
            goal_amount=10000.0,
            current_savings=0.0,
            deadline_months=12,
            monthly_cashflow=2000.0,
        )
        assert gap == 0.0

    def test_gap_is_zero_when_goal_already_met(self):
        """current_savings >= goal_amount → remaining <= 0 → gap = 0.0."""
        gap = calculate_monthly_savings_gap(
            goal_amount=5000.0,
            current_savings=8000.0,
            deadline_months=12,
            monthly_cashflow=100.0,
        )
        assert gap == 0.0

    def test_gap_positive_when_behind_schedule(self):
        """Cashflow of $0 with a real deadline → gap equals full required pace."""
        # required = 12000 / 12 = 1000/mo; cashflow=0 → gap=1000
        gap = calculate_monthly_savings_gap(
            goal_amount=12000.0,
            current_savings=0.0,
            deadline_months=12,
            monthly_cashflow=0.0,
        )
        assert abs(gap - 1000.0) < 1e-9
