"""
tests/engine/test_baseline.py
Integration tests for core_engine.baseline.build_baseline_projection.

Tests the full baseline pipeline: snapshot → cashflow → savings_rate → projection.
Verifies that build_baseline_projection correctly orchestrates all engine components.
"""

from core_engine.baseline import build_baseline_projection
from shared_types.models import (
    CashflowData,
    ExpensesData,
    FinancialSnapshot,
    GoalData,
    IncomeData,
    SavingsData,
)

# ---------------------------------------------------------------------------
# Test fixture factory
# ---------------------------------------------------------------------------


def make_snapshot(
    income: float = 6_000,
    fixed: float = 2_000,
    variable: float = 1_500,
    savings_balance: float = 5_000,
    savings_contribution: float = 500,
    goal_amount: float = 20_000,
    snapshot_date: str = "2026-01-01",
    deadline: str = "2027-07-01",
    goal_type: str = "emergency_fund",
    income_type: str = "stable",
    income_volatile: bool = False,
) -> FinancialSnapshot:
    """Factory for FinancialSnapshot test fixtures."""
    cashflow = income - fixed - variable
    return FinancialSnapshot(
        user_id="test-user-001",
        snapshot_date=snapshot_date,
        income=IncomeData(
            monthly=income,
            income_type=income_type,
            income_volatile=income_volatile,
        ),
        expenses=ExpensesData(fixed=fixed, variable=variable, total=fixed + variable),
        savings=SavingsData(
            balance=savings_balance,
            monthly_contribution=savings_contribution,
        ),
        cashflow=CashflowData(monthly=cashflow),
        goal=GoalData(
            target_amount=goal_amount,
            deadline=deadline,
            type=goal_type,
        ),
    )


# ---------------------------------------------------------------------------
# Normal baseline tests
# ---------------------------------------------------------------------------


class TestBuildBaselineProjectionNormal:
    """Standard baseline projection tests."""

    def test_basic_positive_cashflow_baseline(self):
        # income=6000, fixed=2000, variable=1500 → cashflow=2500
        snapshot = make_snapshot(income=6_000, fixed=2_000, variable=1_500)
        result = build_baseline_projection(snapshot)

        assert result.monthly_cashflow == 2_500.0
        assert not result.goal_already_met

    def test_savings_rate_computed_correctly(self):
        # cashflow=2500, income=6000 → savings_rate = 41.6667%
        snapshot = make_snapshot(income=6_000, fixed=2_000, variable=1_500)
        result = build_baseline_projection(snapshot)

        expected_rate = (2_500 / 6_000) * 100
        assert abs(result.savings_rate - expected_rate) < 0.001

    def test_time_to_goal_computed(self):
        # goal=20000, savings=5000, cashflow=2500 → ceil(15000/2500) = 6 months
        snapshot = make_snapshot(
            income=6_000, fixed=2_000, variable=1_500,
            savings_balance=5_000, goal_amount=20_000
        )
        result = build_baseline_projection(snapshot)
        assert result.time_to_goal_months == 6

    def test_all_fields_present(self):
        """BaselineResult must have all required fields."""
        snapshot = make_snapshot()
        result = build_baseline_projection(snapshot)

        assert hasattr(result, "monthly_cashflow")
        assert hasattr(result, "savings_rate")
        assert hasattr(result, "time_to_goal_months")
        assert hasattr(result, "monthly_savings_gap")
        assert hasattr(result, "goal_already_met")

    def test_returns_baseline_result_type(self):
        from shared_types.models import BaselineResult
        snapshot = make_snapshot()
        result = build_baseline_projection(snapshot)
        assert isinstance(result, BaselineResult)


# ---------------------------------------------------------------------------
# PRD Narrative scenario
# ---------------------------------------------------------------------------


class TestBaselineNarrativeScenario:
    """
    Test the exact narrative from MVP PRD:
    Alex, goal=$20,000 in 12 months, savings=$12,000,
    'At current rate, goal will take 18 months.'
    """

    def test_alex_narrative_cashflow(self):
        # Income $6,500, to get 18-month timeline on $8,000 remaining
        # cashflow ≈ ceil(8000/18) = 445 → let's use cashflow=444 → ceil(8000/444) = 19
        # Use cashflow that produces 18 months: 8000/18 = 444.44 → cashflow=500 → 16mo
        # Use cashflow=500, remaining=9000 (savings=11000) → 18 months
        snapshot = make_snapshot(
            income=6_500,
            fixed=2_500,
            variable=1_500,  # cashflow=2500
            savings_balance=11_000,
            goal_amount=20_000,
            snapshot_date="2026-01-01",
            deadline="2027-01-01",
        )
        result = build_baseline_projection(snapshot)
        # remaining=9000, cashflow=2500 → ceil(9000/2500)=4... let's use smaller cashflow
        # Test what actually comes out rather than forcing a number
        assert result.monthly_cashflow == 2_500.0
        assert result.time_to_goal_months is not None
        assert result.time_to_goal_months > 0

    def test_alex_18_month_scenario(self):
        # Force 18-month baseline: remaining=9000, cashflow=500 → ceil(9000/500)=18
        snapshot = make_snapshot(
            income=5_000,
            fixed=3_500,
            variable=1_000,  # cashflow=500
            savings_balance=11_000,
            goal_amount=20_000,
        )
        result = build_baseline_projection(snapshot)
        assert result.monthly_cashflow == 500.0
        assert result.time_to_goal_months == 18


# ---------------------------------------------------------------------------
# Edge case: goal already met
# ---------------------------------------------------------------------------


class TestBaselineGoalAlreadyMet:
    """Goal-already-met state (PRD Screen 4 error state)."""

    def test_goal_already_met_flag(self):
        snapshot = make_snapshot(savings_balance=25_000, goal_amount=20_000)
        result = build_baseline_projection(snapshot)
        assert result.goal_already_met is True

    def test_goal_already_met_time_zero(self):
        snapshot = make_snapshot(savings_balance=25_000, goal_amount=20_000)
        result = build_baseline_projection(snapshot)
        assert result.time_to_goal_months == 0

    def test_goal_exactly_met(self):
        snapshot = make_snapshot(savings_balance=20_000, goal_amount=20_000)
        result = build_baseline_projection(snapshot)
        assert result.goal_already_met is True
        assert result.time_to_goal_months == 0

    def test_goal_not_yet_met_flag(self):
        snapshot = make_snapshot(savings_balance=5_000, goal_amount=20_000)
        result = build_baseline_projection(snapshot)
        assert result.goal_already_met is False


# ---------------------------------------------------------------------------
# Edge case: negative cashflow
# ---------------------------------------------------------------------------


class TestBaselineNegativeCashflow:
    """Negative cashflow → goal is unreachable at current rate."""

    def test_negative_cashflow_time_to_goal_none(self):
        # Persona 3 bad month
        snapshot = make_snapshot(
            income=3_000, fixed=2_500, variable=800,  # cashflow=-300
        )
        result = build_baseline_projection(snapshot)
        assert result.monthly_cashflow == -300.0
        assert result.time_to_goal_months is None

    def test_negative_cashflow_negative_savings_rate(self):
        snapshot = make_snapshot(
            income=3_000, fixed=2_500, variable=800,  # cashflow=-300
        )
        result = build_baseline_projection(snapshot)
        assert result.savings_rate < 0

    def test_zero_cashflow_unreachable(self):
        snapshot = make_snapshot(
            income=5_000, fixed=3_000, variable=2_000,  # cashflow=0
        )
        result = build_baseline_projection(snapshot)
        assert result.monthly_cashflow == 0.0
        assert result.time_to_goal_months is None


# ---------------------------------------------------------------------------
# Savings gap tests
# ---------------------------------------------------------------------------


class TestBaselineSavingsGap:
    """Monthly savings gap computation."""

    def test_gap_when_behind_schedule(self):
        # goal=20000, savings=5000, deadline=6mo, cashflow=1000
        # need = 15000/6 = 2500/mo, gap = 2500-1000 = 1500
        snapshot = make_snapshot(
            income=5_000, fixed=2_500, variable=1_500,  # cashflow=1000
            savings_balance=5_000, goal_amount=20_000,
            snapshot_date="2026-01-01",
            deadline="2026-07-01",  # 6 months
        )
        result = build_baseline_projection(snapshot)
        assert result.monthly_cashflow == 1_000.0
        assert result.monthly_savings_gap == 1_500.0

    def test_no_gap_when_on_track(self):
        # goal=6000, savings=0, deadline=6mo, cashflow=1000 → on track
        snapshot = make_snapshot(
            income=5_000, fixed=2_500, variable=1_500,  # cashflow=1000
            savings_balance=0, goal_amount=6_000,
            snapshot_date="2026-01-01",
            deadline="2026-07-01",  # 6 months
        )
        result = build_baseline_projection(snapshot)
        assert result.monthly_savings_gap == 0.0


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestBaselineDeterminism:
    """Build the same snapshot 100 times, get identical results."""

    def test_100_runs_identical(self):
        snapshot = make_snapshot()
        results = [build_baseline_projection(snapshot) for _ in range(100)]

        first = results[0]
        for r in results[1:]:
            assert r.monthly_cashflow == first.monthly_cashflow
            assert r.savings_rate == first.savings_rate
            assert r.time_to_goal_months == first.time_to_goal_months
            assert r.monthly_savings_gap == first.monthly_savings_gap
            assert r.goal_already_met == first.goal_already_met
