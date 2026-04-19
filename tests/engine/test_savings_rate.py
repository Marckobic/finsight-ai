"""
tests/engine/test_savings_rate.py
Unit tests for core_engine.savings_rate.calculate_savings_rate.

Coverage target: ≥ 95%.
"""

import pytest
from core_engine.savings_rate import calculate_savings_rate


class TestCalculateSavingsRateNormal:
    """Standard savings rate calculations."""

    def test_forty_percent_savings_rate(self):
        # cashflow=2000, income=5000 → 40%
        assert calculate_savings_rate(2000, 5000) == 40.0

    def test_zero_cashflow_zero_rate(self):
        # Break-even → 0% saved
        assert calculate_savings_rate(0, 5000) == 0.0

    def test_full_income_saved(self):
        # All income saved → 100%
        assert calculate_savings_rate(5000, 5000) == 100.0

    def test_negative_cashflow_negative_rate(self):
        # Overspending → negative savings rate
        result = calculate_savings_rate(-500, 5000)
        assert result == -10.0

    def test_twenty_five_percent(self):
        assert calculate_savings_rate(2500, 10000) == 25.0

    def test_float_precision(self):
        result = calculate_savings_rate(3100, 6500)
        expected = (3100 / 6500) * 100
        assert abs(result - expected) < 1e-9

    def test_small_savings_large_income(self):
        # Only 5% saved
        result = calculate_savings_rate(500, 10000)
        assert result == 5.0


class TestCalculateSavingsRateEdgeCases:
    """Edge cases including zero income."""

    def test_zero_income_returns_zero(self):
        # Avoid division by zero — return 0.0 per spec
        assert calculate_savings_rate(0, 0) == 0.0

    def test_zero_cashflow_zero_income(self):
        assert calculate_savings_rate(0, 0) == 0.0

    def test_very_small_income(self):
        result = calculate_savings_rate(0.01, 0.10)
        assert abs(result - 10.0) < 1e-9

    def test_high_savings_rate(self):
        # Very frugal user: 90% savings rate
        result = calculate_savings_rate(9000, 10000)
        assert result == 90.0


class TestCalculateSavingsRatePersonas:
    """Persona-representative values from PRD."""

    def test_persona_1_early_career(self):
        # cashflow=3100, income=6500 → ~47.69%
        result = calculate_savings_rate(3100, 6500)
        assert abs(result - 47.6923076923) < 1e-6

    def test_persona_2_constrained_planner(self):
        # cashflow=2500, income=10000 → 25%
        assert calculate_savings_rate(2500, 10000) == 25.0

    def test_persona_3_low_month_negative_rate(self):
        # cashflow=-300, income=3000 → -10%
        assert calculate_savings_rate(-300, 3000) == -10.0

    def test_narrative_alex_mvp_prd(self):
        # Alex: cashflow=2500, income=6500 → ~38.46%
        result = calculate_savings_rate(2500, 6500)
        assert abs(result - 38.4615384615) < 1e-6


class TestCalculateSavingsRateErrors:
    """Negative income must raise ValueError."""

    def test_negative_income_raises(self):
        with pytest.raises(ValueError, match="income must be >= 0"):
            calculate_savings_rate(1000, -500)

    def test_negative_income_with_negative_cashflow_raises(self):
        with pytest.raises(ValueError, match="income must be >= 0"):
            calculate_savings_rate(-500, -1000)


class TestCalculateSavingsRateDeterminism:
    """Determinism guarantee."""

    def test_100_runs_identical(self):
        results = [calculate_savings_rate(2000, 5000) for _ in range(100)]
        assert all(r == results[0] for r in results)

    def test_100_runs_zero_income(self):
        results = [calculate_savings_rate(0, 0) for _ in range(100)]
        assert all(r == results[0] for r in results)
