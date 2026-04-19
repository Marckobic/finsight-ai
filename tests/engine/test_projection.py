"""
tests/engine/test_projection.py
Unit tests for core_engine.projection module.

Coverage target: ≥ 95%.
Tests: calculate_time_to_goal, calculate_monthly_savings_gap, months_until_deadline.

PRD Section 7.2 Testing Requirements:
  - Edge cases: zero income, zero expenses, negative cashflow, goal=$0, goal already met
  - Deterministic engine must produce identical output for identical inputs
"""

import pytest
from core_engine.projection import (
    calculate_monthly_savings_gap,
    calculate_time_to_goal,
    months_until_deadline,
)

# ---------------------------------------------------------------------------
# calculate_time_to_goal
# ---------------------------------------------------------------------------


class TestCalculateTimeToGoal:
    """Tests for calculate_time_to_goal."""

    # --- Normal cases ---

    def test_typical_goal_16_months(self):
        # remaining=8000, cashflow=500 → ceil(8000/500) = 16
        assert calculate_time_to_goal(10_000, 2_000, 500) == 16

    def test_exact_division_no_ceiling(self):
        # remaining=10000, cashflow=2000 → 10000/2000 = 5.0 → 5
        assert calculate_time_to_goal(10_000, 0, 2_000) == 5

    def test_ceiling_applied_fractional(self):
        # remaining=10000, cashflow=3000 → 3.333 → ceil = 4
        assert calculate_time_to_goal(10_000, 0, 3_000) == 4

    def test_one_month_to_goal(self):
        # remaining=500, cashflow=500 → 1
        assert calculate_time_to_goal(500, 0, 500) == 1

    def test_almost_one_month(self):
        # remaining=499, cashflow=500 → ceil(0.998) = 1
        assert calculate_time_to_goal(500, 1, 500) == 1

    def test_large_goal_long_timeline(self):
        # $1,000,000 goal, $1,000/month → 1000 months
        assert calculate_time_to_goal(1_000_000, 0, 1_000) == 1_000

    def test_high_cashflow_fast_goal(self):
        # remaining=5000, cashflow=5000 → 1 month
        assert calculate_time_to_goal(5_000, 0, 5_000) == 1

    # --- Goal already met ---

    def test_goal_exactly_met(self):
        # savings == goal → already met
        assert calculate_time_to_goal(10_000, 10_000, 500) == 0

    def test_goal_more_than_met(self):
        # savings > goal → already met
        assert calculate_time_to_goal(10_000, 15_000, 500) == 0

    def test_goal_zero_savings_zero(self):
        # goal=$0 means already met
        assert calculate_time_to_goal(0, 0, 500) == 0

    def test_goal_zero_with_savings(self):
        assert calculate_time_to_goal(0, 5_000, 500) == 0

    # --- Unreachable goal (zero or negative cashflow) ---

    def test_zero_cashflow_returns_none(self):
        assert calculate_time_to_goal(10_000, 0, 0) is None

    def test_negative_cashflow_returns_none(self):
        assert calculate_time_to_goal(10_000, 0, -500) is None

    def test_very_small_negative_cashflow_returns_none(self):
        assert calculate_time_to_goal(10_000, 0, -0.01) is None

    # --- Persona scenarios ---

    def test_persona_1_emergency_fund(self):
        # Alex: goal=$20,000, savings=$12,000, cashflow=$2,500 → ceil(8000/2500) = 4
        assert calculate_time_to_goal(20_000, 12_000, 2_500) == 4

    def test_persona_1_baseline_from_prd(self):
        # PRD narrative: 18 months at current rate
        # If goal=20000, savings=12000, need cashflow=8000/18 ≈ 444.44
        # At cashflow=500: ceil(8000/500) = 16 months
        assert calculate_time_to_goal(20_000, 12_000, 500) == 16

    def test_persona_2_constrained(self):
        # goal=50000, savings=25000, cashflow=500 → ceil(25000/500) = 50 months
        assert calculate_time_to_goal(50_000, 25_000, 500) == 50

    def test_persona_3_low_income_unreachable(self):
        # Volatile earner bad month: negative cashflow → unreachable
        assert calculate_time_to_goal(20_000, 5_000, -300) is None

    # --- Error cases ---

    def test_negative_goal_raises(self):
        with pytest.raises(ValueError, match="goal_amount must be >= 0"):
            calculate_time_to_goal(-1_000, 0, 500)

    def test_negative_savings_raises(self):
        with pytest.raises(ValueError, match="current_savings must be >= 0"):
            calculate_time_to_goal(10_000, -100, 500)

    # --- Determinism ---

    def test_100_runs_identical(self):
        results = [calculate_time_to_goal(10_000, 2_000, 500) for _ in range(100)]
        assert all(r == results[0] for r in results)

    def test_100_runs_none_result_identical(self):
        results = [calculate_time_to_goal(10_000, 0, 0) for _ in range(100)]
        assert all(r is None for r in results)


# ---------------------------------------------------------------------------
# calculate_monthly_savings_gap
# ---------------------------------------------------------------------------


class TestCalculateMonthlySavingsGap:
    """Tests for calculate_monthly_savings_gap."""

    def test_on_track_no_gap(self):
        # Need $1,000/month to hit goal in 12 months, have $1,000 cashflow → gap=0
        assert calculate_monthly_savings_gap(12_000, 0, 12, 1_000) == 0.0

    def test_on_track_surplus(self):
        # Have more cashflow than needed → no gap (not negative)
        assert calculate_monthly_savings_gap(12_000, 0, 12, 2_000) == 0.0

    def test_behind_schedule_gap(self):
        # Need $1,000/month, have $500 → gap=$500
        assert calculate_monthly_savings_gap(12_000, 0, 12, 500) == 500.0

    def test_goal_already_met_no_gap(self):
        # savings > goal → gap=0
        assert calculate_monthly_savings_gap(10_000, 15_000, 12, 500) == 0.0

    def test_negative_cashflow_increases_gap(self):
        # Need $1,000/month but cashflow=-200 → gap = 1000 - (-200) = 1200
        result = calculate_monthly_savings_gap(12_000, 0, 12, -200)
        assert abs(result - 1_200.0) < 1e-9

    def test_partial_savings_reduces_required(self):
        # goal=12000, savings=6000, deadline=12mo, cashflow=400
        # need = 6000/12 = 500, gap = 500-400 = 100
        assert calculate_monthly_savings_gap(12_000, 6_000, 12, 400) == 100.0

    def test_long_deadline_small_gap(self):
        # goal=10000, savings=0, deadline=24mo, cashflow=400
        # need = 10000/24 ≈ 416.67, gap = 416.67 - 400 = 16.67
        result = calculate_monthly_savings_gap(10_000, 0, 24, 400)
        assert abs(result - (10_000 / 24 - 400)) < 1e-9

    def test_one_month_deadline(self):
        # Must reach goal in 1 month
        result = calculate_monthly_savings_gap(5_000, 0, 1, 3_000)
        assert result == 2_000.0

    def test_zero_goal_amount_no_gap(self):
        assert calculate_monthly_savings_gap(0, 0, 12, 500) == 0.0

    # --- Error cases ---

    def test_zero_deadline_months_raises(self):
        with pytest.raises(ValueError, match="deadline_months must be >= 1"):
            calculate_monthly_savings_gap(10_000, 0, 0, 500)

    def test_negative_deadline_raises(self):
        with pytest.raises(ValueError, match="deadline_months must be >= 1"):
            calculate_monthly_savings_gap(10_000, 0, -1, 500)

    def test_negative_goal_raises(self):
        with pytest.raises(ValueError, match="goal_amount must be >= 0"):
            calculate_monthly_savings_gap(-1_000, 0, 12, 500)

    def test_negative_savings_raises(self):
        with pytest.raises(ValueError, match="current_savings must be >= 0"):
            calculate_monthly_savings_gap(10_000, -100, 12, 500)

    # --- Determinism ---

    def test_100_runs_identical(self):
        results = [calculate_monthly_savings_gap(12_000, 0, 12, 500) for _ in range(100)]
        assert all(r == results[0] for r in results)


# ---------------------------------------------------------------------------
# months_until_deadline
# ---------------------------------------------------------------------------


class TestMonthsUntilDeadline:
    """Tests for months_until_deadline date computation."""

    def test_twelve_months(self):
        assert months_until_deadline("2026-01-01", "2027-01-01") == 12

    def test_six_months(self):
        assert months_until_deadline("2026-01-01", "2026-07-01") == 6

    def test_one_month(self):
        assert months_until_deadline("2026-01-01", "2026-02-01") == 1

    def test_cross_year_boundary(self):
        # Nov 2026 → Feb 2027 = 3 months
        assert months_until_deadline("2026-11-01", "2027-02-01") == 3

    def test_same_day_returns_minimum_one(self):
        assert months_until_deadline("2026-01-01", "2026-01-01") == 1

    def test_deadline_in_past_returns_one(self):
        # Deadline is before snapshot — return minimum 1
        assert months_until_deadline("2027-06-01", "2026-01-01") == 1

    def test_partial_month_cutoff(self):
        # snapshot Jan 15, deadline Feb 10 — day 10 < day 15, so months = 0 → clamped to 1
        assert months_until_deadline("2026-01-15", "2026-02-10") == 1

    def test_partial_month_complete(self):
        # snapshot Jan 15, deadline Feb 20 — day 20 >= day 15, months = 1
        assert months_until_deadline("2026-01-15", "2026-02-20") == 1

    def test_24_months(self):
        assert months_until_deadline("2026-01-01", "2028-01-01") == 24

    def test_18_months(self):
        assert months_until_deadline("2026-01-01", "2027-07-01") == 18

    def test_deterministic_date_computation(self):
        results = [months_until_deadline("2026-01-01", "2027-01-01") for _ in range(100)]
        assert all(r == 12 for r in results)
