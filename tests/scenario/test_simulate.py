"""
tests/scenario/test_simulate.py
Tests for scenario_engine.simulate module.

PRD Section 7.3 Testing Requirements:
  - Each scenario type (savings_increase, expense_cut) with ≥ 5 input permutations
  - Adherence boundary values (0.1 floor, 0.5 midpoint, 0.95 ceiling) must be tested
  - Output schema validated on every build
  - Delta calculations regression-tested against known inputs/outputs
  - Clamping: adherence < 0.1 → clamped to 0.1; adherence > 0.95 → clamped to 0.95
"""

import pytest
from scenario_engine.simulate import (
    ADHERENCE_CEILING,
    ADHERENCE_FLOOR,
    clamp_adherence,
    simulate_adherence_range,
    simulate_scenario,
)
from shared_types.models import (
    BaselineResult,
    BehaviorChange,
    CashflowData,
    ExpensesData,
    FinancialSnapshot,
    GoalData,
    IncomeData,
    SavingsData,
    ScenarioResult,
)

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def make_snapshot(
    income: float = 6_000,
    fixed: float = 2_000,
    variable: float = 1_500,
    savings_balance: float = 5_000,
    goal_amount: float = 20_000,
    snapshot_date: str = "2026-01-01",
    deadline: str = "2027-07-01",
) -> FinancialSnapshot:
    cashflow = income - fixed - variable
    return FinancialSnapshot(
        user_id="test-user-001",
        snapshot_date=snapshot_date,
        income=IncomeData(monthly=income),
        expenses=ExpensesData(fixed=fixed, variable=variable, total=fixed + variable),
        savings=SavingsData(balance=savings_balance, monthly_contribution=500),
        cashflow=CashflowData(monthly=cashflow),
        goal=GoalData(target_amount=goal_amount, deadline=deadline, type="emergency_fund"),
    )


def make_baseline(
    monthly_cashflow: float = 2_500,
    savings_rate: float = 41.67,
    time_to_goal_months: int = 6,
    monthly_savings_gap: float = 0.0,
    goal_already_met: bool = False,
) -> BaselineResult:
    return BaselineResult(
        monthly_cashflow=monthly_cashflow,
        savings_rate=savings_rate,
        time_to_goal_months=time_to_goal_months,
        monthly_savings_gap=monthly_savings_gap,
        goal_already_met=goal_already_met,
    )


# ---------------------------------------------------------------------------
# clamp_adherence unit tests
# ---------------------------------------------------------------------------


class TestClampAdherence:
    """adherence_rate must be clamped to [0.1, 0.95]."""

    def test_floor_boundary(self):
        assert clamp_adherence(0.1) == ADHERENCE_FLOOR

    def test_ceiling_boundary(self):
        assert clamp_adherence(0.95) == ADHERENCE_CEILING

    def test_below_floor_clamped(self):
        assert clamp_adherence(0.0) == ADHERENCE_FLOOR

    def test_above_ceiling_clamped(self):
        assert clamp_adherence(1.0) == ADHERENCE_CEILING

    def test_midpoint_unchanged(self):
        assert clamp_adherence(0.5) == 0.5

    def test_very_low_clamped(self):
        assert clamp_adherence(-100) == ADHERENCE_FLOOR

    def test_very_high_clamped(self):
        assert clamp_adherence(100) == ADHERENCE_CEILING

    def test_just_inside_floor(self):
        assert clamp_adherence(0.11) == 0.11

    def test_just_inside_ceiling(self):
        assert clamp_adherence(0.94) == 0.94


# ---------------------------------------------------------------------------
# savings_increase scenario — 5+ permutations
# ---------------------------------------------------------------------------


class TestSavingsIncreaseScenario:
    """
    PRD requirement: ≥ 5 input permutations per scenario type.
    All use behavior_change.type = "savings_increase".
    """

    def test_savings_increase_basic_improvement(self):
        # baseline: cashflow=500, time_to_goal=16mo (goal=10000, savings=2000, cashflow=500)
        # change: +300/mo at 1.0 adherence → effective=300
        # scenario cashflow = 800, new time = ceil(8000/800) = 10 → delta=6
        snapshot = make_snapshot(income=5_000, fixed=3_000, variable=1_500,
                                 savings_balance=2_000, goal_amount=10_000)
        baseline = make_baseline(monthly_cashflow=500, time_to_goal_months=16)
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.95)

        assert result.scenario_months is not None
        assert result.scenario_months < 16
        assert result.delta_months > 0
        assert result.is_improvement is True

    def test_savings_increase_full_adherence_ceiling(self):
        # adherence=0.95, change=$300 → effective=$285
        snapshot = make_snapshot(savings_balance=5_000, goal_amount=20_000)
        baseline = make_baseline(monthly_cashflow=2_500, time_to_goal_months=6)
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.95)

        assert result.adherence_rate == 0.95
        assert abs(result.effective_monthly_change - 285.0) < 1e-9

    def test_savings_increase_floor_adherence(self):
        # adherence=0.1, change=$300 → effective=$30
        snapshot = make_snapshot(savings_balance=5_000, goal_amount=20_000)
        baseline = make_baseline(monthly_cashflow=2_500, time_to_goal_months=6)
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.1)

        assert result.adherence_rate == ADHERENCE_FLOOR
        assert abs(result.effective_monthly_change - 30.0) < 1e-9

    def test_savings_increase_midpoint_adherence(self):
        # adherence=0.5, change=$300 → effective=$150
        snapshot = make_snapshot(savings_balance=5_000, goal_amount=20_000)
        baseline = make_baseline(monthly_cashflow=2_500, time_to_goal_months=6)
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.5)

        assert result.adherence_rate == 0.5
        assert abs(result.effective_monthly_change - 150.0) < 1e-9

    def test_savings_increase_large_amount(self):
        # Large increase that dramatically shortens timeline
        snapshot = make_snapshot(
            income=5_000, fixed=3_000, variable=1_500,
            savings_balance=0, goal_amount=10_000
        )
        baseline = make_baseline(monthly_cashflow=500, time_to_goal_months=20)
        change = BehaviorChange(type="savings_increase", value=1_000)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.7)

        # effective = 700, scenario_cashflow = 1200
        # time = ceil(10000/1200) = 9
        assert result.effective_monthly_change == pytest.approx(700.0)
        assert result.scenario_months is not None
        assert result.is_improvement is True

    def test_savings_increase_zero_value_no_change(self):
        # $0 increase → same as baseline
        snapshot = make_snapshot(savings_balance=5_000, goal_amount=20_000)
        baseline = make_baseline(monthly_cashflow=2_500, time_to_goal_months=6)
        change = BehaviorChange(type="savings_increase", value=0)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.7)

        assert result.effective_monthly_change == 0.0
        assert result.scenario_months == baseline.time_to_goal_months
        assert result.delta_months == 0
        assert result.is_improvement is False

    def test_savings_increase_prd_narrative_scenario(self):
        """
        PRD MVP Narrative: Alex, $300/month increase → 18→11 months.
        Verify delta is significant.
        """
        # remaining=9000, cashflow=500 → 18 months baseline
        snapshot = make_snapshot(
            income=5_000, fixed=3_500, variable=1_000,
            savings_balance=11_000, goal_amount=20_000,
        )
        baseline = make_baseline(monthly_cashflow=500, time_to_goal_months=18)
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.7)

        # effective=210, scenario_cashflow=710, time=ceil(9000/710)=13
        assert result.adherence_rate == 0.7
        assert result.effective_monthly_change == pytest.approx(210.0)
        assert result.scenario_months is not None
        assert result.delta_months > 0
        assert result.is_improvement is True


# ---------------------------------------------------------------------------
# expense_cut scenario — 5+ permutations
# ---------------------------------------------------------------------------


class TestExpenseCutScenario:
    """≥ 5 permutations for expense_cut scenario type."""

    def test_expense_cut_basic_improvement(self):
        snapshot = make_snapshot(savings_balance=2_000, goal_amount=10_000)
        baseline = make_baseline(monthly_cashflow=500, time_to_goal_months=16)
        change = BehaviorChange(type="expense_cut", value=200)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.7)

        assert result.is_improvement is True
        assert result.delta_months is not None
        assert result.delta_months > 0

    def test_expense_cut_at_floor_adherence(self):
        snapshot = make_snapshot(savings_balance=5_000, goal_amount=20_000)
        baseline = make_baseline(monthly_cashflow=2_500, time_to_goal_months=6)
        change = BehaviorChange(type="expense_cut", value=500)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.1)

        assert result.adherence_rate == ADHERENCE_FLOOR
        assert result.effective_monthly_change == pytest.approx(50.0)

    def test_expense_cut_at_ceiling_adherence(self):
        snapshot = make_snapshot(savings_balance=5_000, goal_amount=20_000)
        baseline = make_baseline(monthly_cashflow=2_500, time_to_goal_months=6)
        change = BehaviorChange(type="expense_cut", value=500)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.95)

        assert result.adherence_rate == ADHERENCE_CEILING
        assert result.effective_monthly_change == pytest.approx(475.0)

    def test_expense_cut_midpoint_adherence(self):
        snapshot = make_snapshot(savings_balance=5_000, goal_amount=20_000)
        baseline = make_baseline(monthly_cashflow=2_500, time_to_goal_months=6)
        change = BehaviorChange(type="expense_cut", value=200)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.5)

        assert result.effective_monthly_change == pytest.approx(100.0)
        assert result.scenario_monthly_cashflow == pytest.approx(2_600.0)

    def test_expense_cut_large_cut_accelerates_goal(self):
        # Cut $1,500/month at 80% adherence on a tight budget
        snapshot = make_snapshot(
            income=5_000, fixed=3_000, variable=1_500,
            savings_balance=0, goal_amount=6_000
        )
        baseline = make_baseline(monthly_cashflow=500, time_to_goal_months=12)
        change = BehaviorChange(type="expense_cut", value=1_000)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.8)

        assert result.effective_monthly_change == pytest.approx(800.0)
        assert result.scenario_months is not None
        assert result.scenario_months < 12

    def test_expense_cut_persona_1_dining_reduction(self):
        """PRD Persona 1: 'cutting $150/month in dining gets you there 3 months sooner'"""
        snapshot = make_snapshot(
            income=6_500, fixed=2_200, variable=1_200,
            savings_balance=5_000, goal_amount=20_000
        )
        # cashflow=3100, remaining=15000 → time=ceil(15000/3100)=5mo
        baseline = make_baseline(monthly_cashflow=3_100, time_to_goal_months=5)
        change = BehaviorChange(type="expense_cut", value=150)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.6)

        assert result.delta_months >= 0


# ---------------------------------------------------------------------------
# Output schema validation
# ---------------------------------------------------------------------------


class TestScenarioOutputSchema:
    """PRD requirement: scenario output schema validated on every build."""

    def test_result_is_scenario_result_type(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, 0.7)

        assert isinstance(result, ScenarioResult)

    def test_all_required_fields_present(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, 0.7)

        assert hasattr(result, "baseline_months")
        assert hasattr(result, "scenario_months")
        assert hasattr(result, "delta_months")
        assert hasattr(result, "adherence_rate")
        assert hasattr(result, "effective_monthly_change")
        assert hasattr(result, "scenario_monthly_cashflow")
        assert hasattr(result, "is_improvement")

    def test_adherence_rate_in_valid_range(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        for raw_rate in [0.0, 0.1, 0.5, 0.95, 1.0]:
            result = simulate_scenario(snapshot, baseline, change, raw_rate)
            assert ADHERENCE_FLOOR <= result.adherence_rate <= ADHERENCE_CEILING

    def test_effective_change_non_negative(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, 0.7)
        assert result.effective_monthly_change >= 0

    def test_scenario_cashflow_greater_than_baseline(self):
        snapshot = make_snapshot()
        baseline = make_baseline(monthly_cashflow=2_500)
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, 0.7)
        assert result.scenario_monthly_cashflow > 2_500.0


# ---------------------------------------------------------------------------
# Adherence boundary regression tests
# ---------------------------------------------------------------------------


class TestAdherenceBoundaries:
    """PRD: Boundary values (0.1, 0.5, 0.95) must be explicitly tested."""

    def setup_method(self):
        self.snapshot = make_snapshot(savings_balance=2_000, goal_amount=10_000)
        self.baseline = make_baseline(monthly_cashflow=500, time_to_goal_months=16)
        self.change = BehaviorChange(type="savings_increase", value=500)

    def test_adherence_floor_0_1(self):
        # At minimum adherence (10%): effective = 500 × 0.1 = 50
        result = simulate_scenario(self.snapshot, self.baseline, self.change, 0.1)
        assert result.adherence_rate == 0.1
        assert result.effective_monthly_change == pytest.approx(50.0)
        # cashflow = 550, remaining=8000 → ceil(8000/550) = 15 → delta=1
        assert result.delta_months == 1

    def test_adherence_midpoint_0_5(self):
        # At midpoint adherence (50%): effective = 500 × 0.5 = 250
        result = simulate_scenario(self.snapshot, self.baseline, self.change, 0.5)
        assert result.adherence_rate == 0.5
        assert result.effective_monthly_change == pytest.approx(250.0)
        # cashflow = 750, remaining=8000 → ceil(8000/750) = 11 → delta=5
        assert result.delta_months == 5

    def test_adherence_ceiling_0_95(self):
        # At maximum adherence (95%): effective = 500 × 0.95 = 475
        result = simulate_scenario(self.snapshot, self.baseline, self.change, 0.95)
        assert result.adherence_rate == 0.95
        assert result.effective_monthly_change == pytest.approx(475.0)
        # cashflow = 975, remaining=8000 → ceil(8000/975) = 9 → delta=7
        assert result.delta_months == 7

    def test_higher_adherence_means_fewer_months(self):
        """Core behavioral truth: higher compliance → faster goal attainment."""
        results = [
            simulate_scenario(self.snapshot, self.baseline, self.change, rate)
            for rate in [0.1, 0.3, 0.5, 0.7, 0.95]
        ]
        months = [r.scenario_months for r in results]
        # Each subsequent result should have fewer or equal months
        for i in range(len(months) - 1):
            assert months[i] >= months[i + 1], (
                f"Higher adherence should not increase scenario_months: "
                f"{months[i]} at rate {results[i].adherence_rate} vs "
                f"{months[i+1]} at rate {results[i+1].adherence_rate}"
            )


# ---------------------------------------------------------------------------
# Delta regression tests — known inputs and expected outputs
# ---------------------------------------------------------------------------


class TestDeltaRegressions:
    """Regression tests with fixed known inputs and expected delta values."""

    def test_regression_case_1(self):
        """
        Input:  cashflow=500, goal=10000, savings=2000 (remaining=8000), change=300, adherence=0.7
        Expect: effective=210, scenario_cashflow=710, scenario_months=ceil(8000/710)=12, delta=4
        """
        snapshot = make_snapshot(savings_balance=2_000, goal_amount=10_000)
        baseline = make_baseline(monthly_cashflow=500, time_to_goal_months=16)
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, 0.7)

        assert result.effective_monthly_change == pytest.approx(210.0)
        assert result.scenario_monthly_cashflow == pytest.approx(710.0)
        assert result.scenario_months == 12
        assert result.delta_months == 4

    def test_regression_case_2(self):
        """
        Input:  cashflow=1000, goal=20000, savings=5000 (remaining=15000), change=500, adherence=0.5
        Expect: effective=250, scenario_cashflow=1250, scenario_months=ceil(15000/1250)=12, delta=3
        baseline: ceil(15000/1000)=15
        """
        snapshot = make_snapshot(savings_balance=5_000, goal_amount=20_000)
        baseline = make_baseline(monthly_cashflow=1_000, time_to_goal_months=15)
        change = BehaviorChange(type="savings_increase", value=500)

        result = simulate_scenario(snapshot, baseline, change, 0.5)

        assert result.effective_monthly_change == pytest.approx(250.0)
        assert result.scenario_monthly_cashflow == pytest.approx(1_250.0)
        assert result.scenario_months == 12
        assert result.delta_months == 3

    def test_regression_case_3_expense_cut(self):
        """
        Input:  cashflow=800, goal=12000, savings=0 (remaining=12000), change=200, adherence=0.6
        Expect: effective=120, scenario_cashflow=920, scenario_months=ceil(12000/920)=14, delta=1
        baseline: ceil(12000/800)=15
        """
        snapshot = make_snapshot(savings_balance=0, goal_amount=12_000)
        baseline = make_baseline(monthly_cashflow=800, time_to_goal_months=15)
        change = BehaviorChange(type="expense_cut", value=200)

        result = simulate_scenario(snapshot, baseline, change, 0.6)

        assert result.effective_monthly_change == pytest.approx(120.0)
        assert result.scenario_monthly_cashflow == pytest.approx(920.0)
        assert result.scenario_months == 14
        assert result.delta_months == 1

    def test_regression_case_4_no_improvement_at_floor(self):
        """
        Input:  cashflow=990, change=10 at adherence=0.1 → effective=1, scenario=991
        baseline: ceil(8000/990)=9, scenario: ceil(8000/991)=9 → delta=0
        """
        snapshot = make_snapshot(savings_balance=2_000, goal_amount=10_000)
        baseline = make_baseline(monthly_cashflow=990, time_to_goal_months=9)
        change = BehaviorChange(type="savings_increase", value=10)

        result = simulate_scenario(snapshot, baseline, change, 0.1)

        assert result.effective_monthly_change == pytest.approx(1.0)
        # scenario_months might be same as baseline (minimal change)
        assert result.scenario_months is not None
        assert result.delta_months >= 0

    def test_regression_case_5_negative_baseline_becomes_reachable(self):
        """
        Baseline cashflow=-300 (unreachable), change=$400 at adherence=0.95
        effective=380, scenario_cashflow=80 → reachable → is_improvement=True
        """
        snapshot = make_snapshot(
            income=3_000, fixed=2_500, variable=800,
            savings_balance=2_000, goal_amount=10_000
        )
        baseline = make_baseline(monthly_cashflow=-300, time_to_goal_months=None)
        change = BehaviorChange(type="expense_cut", value=400)

        result = simulate_scenario(snapshot, baseline, change, 0.95)

        assert result.effective_monthly_change == pytest.approx(380.0)
        assert result.scenario_monthly_cashflow == pytest.approx(80.0)
        assert result.scenario_months is not None
        assert result.is_improvement is True


# ---------------------------------------------------------------------------
# simulate_adherence_range
# ---------------------------------------------------------------------------


class TestSimulateAdherenceRange:
    """Tests for simulate_adherence_range helper."""

    def test_returns_correct_number_of_results(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        results = simulate_adherence_range(snapshot, baseline, change, adherence_steps=5)
        assert len(results) == 5

    def test_first_result_at_floor(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        results = simulate_adherence_range(snapshot, baseline, change, adherence_steps=5)
        assert results[0].adherence_rate == pytest.approx(ADHERENCE_FLOOR)

    def test_last_result_at_ceiling(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        results = simulate_adherence_range(snapshot, baseline, change, adherence_steps=5)
        assert results[-1].adherence_rate == pytest.approx(ADHERENCE_CEILING)

    def test_results_ordered_by_adherence(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        results = simulate_adherence_range(snapshot, baseline, change, adherence_steps=5)
        rates = [r.adherence_rate for r in results]
        assert rates == sorted(rates)

    def test_invalid_steps_raises(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        with pytest.raises(ValueError, match="adherence_steps must be >= 2"):
            simulate_adherence_range(snapshot, baseline, change, adherence_steps=1)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestSimulateErrors:
    """Invalid inputs must raise ValueError."""

    def test_negative_behavior_change_raises(self):
        with pytest.raises(ValueError, match="must be >= 0"):
            BehaviorChange(type="savings_increase", value=-100)

    def test_adherence_below_floor_clamped(self):
        # Should not raise — clamped automatically
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=0.0)
        assert result.adherence_rate == ADHERENCE_FLOOR

    def test_adherence_above_ceiling_clamped(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        result = simulate_scenario(snapshot, baseline, change, adherence_rate=2.0)
        assert result.adherence_rate == ADHERENCE_CEILING


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestSimulateDeterminism:
    """Simulate the same scenario 100 times, identical results every time."""

    def test_100_runs_identical(self):
        snapshot = make_snapshot()
        baseline = make_baseline()
        change = BehaviorChange(type="savings_increase", value=300)

        results = [simulate_scenario(snapshot, baseline, change, 0.7) for _ in range(100)]
        first = results[0]
        for r in results[1:]:
            assert r.scenario_months == first.scenario_months
            assert r.delta_months == first.delta_months
            assert r.effective_monthly_change == first.effective_monthly_change
            assert r.adherence_rate == first.adherence_rate
