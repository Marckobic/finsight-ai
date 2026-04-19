"""
tests/engine/test_cashflow.py
Unit tests for core_engine.cashflow.calculate_cashflow.

Coverage target: ≥ 95% (PRD Section 7.2 Testing Requirements).
Determinism guarantee: identical inputs MUST produce identical outputs, 100% of runs.

Test categories:
  - Normal cases (positive, zero, negative cashflow)
  - Edge cases (zero income, zero expenses, very large values)
  - Persona-representative inputs (Early-Career, Constrained Planner, Volatile Earner)
  - Error cases (negative inputs → ValueError)
  - Determinism validation (100 runs with same input)
"""

import pytest
from core_engine.cashflow import calculate_cashflow


class TestCalculateCashflowNormal:
    """Standard cashflow calculations."""

    def test_typical_positive_cashflow(self):
        # income=5000, fixed=2000, variable=1000 → surplus=2000
        result = calculate_cashflow(5000, 2000, 1000)
        assert result == 2000.0

    def test_exact_break_even(self):
        # expenses equal income exactly
        result = calculate_cashflow(3000, 2000, 1000)
        assert result == 0.0

    def test_negative_cashflow_overspending(self):
        # expenses exceed income by 1000
        result = calculate_cashflow(3000, 2500, 1500)
        assert result == -1000.0

    def test_only_fixed_expenses(self):
        result = calculate_cashflow(5000, 3000, 0)
        assert result == 2000.0

    def test_only_variable_expenses(self):
        result = calculate_cashflow(5000, 0, 2000)
        assert result == 3000.0

    def test_float_inputs(self):
        result = calculate_cashflow(5000.50, 1999.99, 500.01)
        assert abs(result - 2500.50) < 1e-9

    def test_large_income(self):
        result = calculate_cashflow(200_000, 80_000, 40_000)
        assert result == 80_000.0

    def test_high_expense_ratio(self):
        # Almost all income goes to expenses
        result = calculate_cashflow(10_000, 9_000, 900)
        assert result == 100.0


class TestCalculateCashflowEdgeCases:
    """Edge cases including zero values."""

    def test_zero_income_zero_expenses(self):
        # No income, no expenses → zero cashflow (valid state)
        result = calculate_cashflow(0, 0, 0)
        assert result == 0.0

    def test_zero_income_zero_variable(self):
        result = calculate_cashflow(5000, 5000, 0)
        assert result == 0.0

    def test_all_zeros(self):
        result = calculate_cashflow(0, 0, 0)
        assert result == 0.0

    def test_very_small_values(self):
        result = calculate_cashflow(0.01, 0.005, 0.003)
        assert abs(result - 0.002) < 1e-12

    def test_integer_inputs_return_float(self):
        result = calculate_cashflow(5000, 2000, 1000)
        assert isinstance(result, float)


class TestCalculateCashflowPersonas:
    """Persona-representative inputs from PRD Section 4.3."""

    def test_persona_1_early_career_optimizer(self):
        # Take-home $6,500, fixed $2,200, variable $1,200 → surplus $3,100
        result = calculate_cashflow(6500, 2200, 1200)
        assert result == 3100.0

    def test_persona_1_lower_bound(self):
        # Monthly take-home $5,000, fixed $1,800, variable $800 → $2,400
        result = calculate_cashflow(5000, 1800, 800)
        assert result == 2400.0

    def test_persona_2_constrained_planner(self):
        # Household $10,000, fixed $5,500, variable $2,000 → $2,500
        result = calculate_cashflow(10_000, 5_500, 2_000)
        assert result == 2500.0

    def test_persona_2_tight_budget(self):
        # Fixed obligations consume most income
        result = calculate_cashflow(7_500, 5_000, 2_000)
        assert result == 500.0

    def test_persona_3_volatile_earner_high_month(self):
        # Good month: $16,000 income, fixed $3,000, variable $2,000 → $11,000
        result = calculate_cashflow(16_000, 3_000, 2_000)
        assert result == 11_000.0

    def test_persona_3_volatile_earner_low_month(self):
        # Bad month: $3,000 income, fixed $2,500, variable $800 → -$300
        result = calculate_cashflow(3_000, 2_500, 800)
        assert result == -300.0

    def test_narrative_alex_from_mvp_prd(self):
        # PRD Narrative: Alex earns $78,000/year → ~$6,500/month
        # Assume fixed=$2,500, variable=$1,500 → cashflow=$2,500
        result = calculate_cashflow(6_500, 2_500, 1_500)
        assert result == 2_500.0


class TestCalculateCashflowErrors:
    """Negative inputs must raise ValueError."""

    def test_negative_income_raises(self):
        with pytest.raises(ValueError, match="income must be >= 0"):
            calculate_cashflow(-100, 0, 0)

    def test_negative_fixed_raises(self):
        with pytest.raises(ValueError, match="fixed_expenses must be >= 0"):
            calculate_cashflow(5000, -500, 0)

    def test_negative_variable_raises(self):
        with pytest.raises(ValueError, match="variable_expenses must be >= 0"):
            calculate_cashflow(5000, 0, -500)

    def test_all_negative_raises_on_income_first(self):
        # income is checked first
        with pytest.raises(ValueError, match="income must be >= 0"):
            calculate_cashflow(-100, -100, -100)

    def test_negative_value_with_valid_others(self):
        with pytest.raises(ValueError):
            calculate_cashflow(5000, 2000, -1)


class TestCalculateCashflowDeterminism:
    """
    Determinism guarantee — PRD Section 7.2:
    'Deterministic engine must produce identical output for identical inputs
    across 100% of test runs (no variance allowed).'
    """

    def test_100_runs_identical_output(self):
        inputs = (5000.0, 2000.0, 1000.0)
        results = [calculate_cashflow(*inputs) for _ in range(100)]
        assert all(r == results[0] for r in results), (
            "DETERMINISM VIOLATION: engine produced different results for identical inputs"
        )

    def test_100_runs_negative_cashflow_identical(self):
        inputs = (3000.0, 2500.0, 1500.0)
        results = [calculate_cashflow(*inputs) for _ in range(100)]
        assert all(r == results[0] for r in results)

    def test_100_runs_zero_cashflow_identical(self):
        inputs = (5000.0, 3000.0, 2000.0)
        results = [calculate_cashflow(*inputs) for _ in range(100)]
        assert all(r == results[0] for r in results)
