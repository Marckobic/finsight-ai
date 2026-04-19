"""
tests/test_integration.py
Full engine pipeline integration tests — no API, no mocks except MockLLMClient.

Pipeline under test:
    FinancialSnapshot
        → build_baseline_projection (core-engine truth layer)
        → simulate_scenario         (scenario-engine behavioral layer)
        → validate_scenario_output  (validation-gateway hard gate)
        → generate_explanation      (ai-layer + validation-gateway)

Rules:
    - No real API calls.  MockLLMClient only.
    - All tests deterministic (no random, no time.sleep).
    - Each test must complete in < 30ms.
"""


from ai_layer.explain import MockLLMClient, generate_explanation
from core_engine.baseline import build_baseline_projection
from scenario_engine.simulate import simulate_scenario
from shared_types.models import (
    AIExplanationInput,
    BehaviorChange,
    CashflowData,
    ExpensesData,
    FinancialSnapshot,
    GoalData,
    IncomeData,
    SavingsData,
    ValidationResult,
)
from validation_gateway.validator import validate_scenario_output

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_snapshot(
    income: float,
    fixed: float,
    variable: float,
    savings_balance: float,
    goal_amount: float,
    snapshot_date: str = "2026-01-01",
    deadline: str = "2030-01-01",
    goal_type: str = "emergency_fund",
) -> FinancialSnapshot:
    cashflow = income - fixed - variable
    return FinancialSnapshot(
        user_id="integration-test",
        snapshot_date=snapshot_date,
        income=IncomeData(monthly=income),
        expenses=ExpensesData(fixed=fixed, variable=variable, total=fixed + variable),
        savings=SavingsData(balance=savings_balance, monthly_contribution=0.0),
        cashflow=CashflowData(monthly=cashflow),
        goal=GoalData(target_amount=goal_amount, deadline=deadline, type=goal_type),
    )


# ---------------------------------------------------------------------------
# a) happy_path_emergency_fund
# ---------------------------------------------------------------------------


class TestHappyPathEmergencyFund:
    """
    Full pipeline with a healthy budget and a reachable emergency-fund goal.

    income=5000, fixed=3000, variable=1000 → cashflow=1000
    goal=10000, savings=0 → time_to_goal=10 months
    savings_increase $500 @ 70% adherence → effective=350, scenario=8mo, delta=2
    """

    def test_baseline_cashflow_equals_income_minus_expenses(self):
        snapshot = _make_snapshot(
            income=5000.0, fixed=3000.0, variable=1000.0,
            savings_balance=0.0, goal_amount=10000.0,
        )
        baseline = build_baseline_projection(snapshot)

        assert baseline.monthly_cashflow == 5000.0 - 3000.0 - 1000.0

    def test_scenario_delta_non_negative_when_value_positive(self):
        snapshot = _make_snapshot(
            income=5000.0, fixed=3000.0, variable=1000.0,
            savings_balance=0.0, goal_amount=10000.0,
        )
        baseline = build_baseline_projection(snapshot)
        change = BehaviorChange(type="savings_increase", value=500)

        scenario = simulate_scenario(snapshot, baseline, change, adherence_rate=0.7)

        assert scenario.delta_months >= 0

    def test_scenario_validation_passes(self):
        snapshot = _make_snapshot(
            income=5000.0, fixed=3000.0, variable=1000.0,
            savings_balance=0.0, goal_amount=10000.0,
        )
        baseline = build_baseline_projection(snapshot)
        change = BehaviorChange(type="savings_increase", value=500)
        scenario = simulate_scenario(snapshot, baseline, change, adherence_rate=0.7)

        validation = validate_scenario_output(scenario)

        assert validation.valid is True

    def test_explanation_returns_valid_result(self):
        snapshot = _make_snapshot(
            income=5000.0, fixed=3000.0, variable=1000.0,
            savings_balance=0.0, goal_amount=10000.0,
        )
        baseline = build_baseline_projection(snapshot)
        change = BehaviorChange(type="savings_increase", value=500)
        scenario = simulate_scenario(snapshot, baseline, change, adherence_rate=0.7)

        # Both months must be reachable for a meaningful explanation
        assert baseline.time_to_goal_months is not None
        assert scenario.scenario_months is not None

        ai_input = AIExplanationInput(
            baseline_months=baseline.time_to_goal_months,
            scenario_months=scenario.scenario_months,
            delta_months=scenario.delta_months,
            monthly_change_amount=float(change.value),
            adherence_rate=scenario.adherence_rate,
            behavior_type=change.type,
            goal_type=snapshot.goal.type,
        )

        explanation = generate_explanation(ai_input, client=MockLLMClient("valid"))

        assert isinstance(explanation, ValidationResult)
        assert explanation.valid is True


# ---------------------------------------------------------------------------
# b) negative_cashflow_returns_none_time_to_goal
# ---------------------------------------------------------------------------


class TestNegativeCashflowReturnsNoneTimeToGoal:
    """
    When expenses exceed income, cashflow is negative and the goal is unreachable.
    baseline.time_to_goal_months must be None.
    """

    def test_negative_cashflow_time_to_goal_is_none(self):
        # income=1000, fixed=800, variable=400 → cashflow = -200
        snapshot = _make_snapshot(
            income=1000.0, fixed=800.0, variable=400.0,
            savings_balance=500.0, goal_amount=5000.0,
        )
        baseline = build_baseline_projection(snapshot)

        assert baseline.monthly_cashflow == -200.0
        assert baseline.time_to_goal_months is None


# ---------------------------------------------------------------------------
# c) goal_already_met
# ---------------------------------------------------------------------------


class TestGoalAlreadyMet:
    """
    When current savings >= goal amount, goal_already_met is True.
    """

    def test_goal_already_met_flag_is_true(self):
        snapshot = _make_snapshot(
            income=6000.0, fixed=2000.0, variable=1500.0,
            savings_balance=25000.0, goal_amount=20000.0,
        )
        baseline = build_baseline_projection(snapshot)

        assert baseline.goal_already_met is True

    def test_goal_not_yet_met_flag_is_false(self):
        snapshot = _make_snapshot(
            income=6000.0, fixed=2000.0, variable=1500.0,
            savings_balance=5000.0, goal_amount=20000.0,
        )
        baseline = build_baseline_projection(snapshot)

        assert baseline.goal_already_met is False


# ---------------------------------------------------------------------------
# d) hallucination_blocked
# ---------------------------------------------------------------------------


class TestHallucinationBlocked:
    """
    MockLLMClient("hallucination") invents a month count not in engine outputs.
    The validation gateway must reject it: valid=False, error mentions hallucination.
    """

    def test_hallucinated_output_is_rejected(self):
        ai_input = AIExplanationInput(
            baseline_months=10,
            scenario_months=8,
            delta_months=2,
            monthly_change_amount=300.0,
            adherence_rate=0.7,
            behavior_type="expense_cut",
            goal_type="emergency_fund",
        )

        validation = generate_explanation(ai_input, client=MockLLMClient("hallucination"))

        assert validation.valid is False
        # Error message should reference a hallucinated / fabricated value
        assert any("hallucin" in e.lower() for e in validation.errors)

    def test_hallucinated_output_uses_fallback(self):
        ai_input = AIExplanationInput(
            baseline_months=10,
            scenario_months=8,
            delta_months=2,
            monthly_change_amount=300.0,
            adherence_rate=0.7,
            behavior_type="savings_increase",
            goal_type="emergency_fund",
        )

        validation = generate_explanation(ai_input, client=MockLLMClient("hallucination"))

        assert validation.fallback_used is True
        assert validation.validated_output is not None


# ---------------------------------------------------------------------------
# e) adherence_clamp_boundaries
# ---------------------------------------------------------------------------


class TestAdherenceClampBoundaries:
    """
    adherence_rate is clamped to [0.1, 0.95].
    - 0.0  → effective = 0.10 × value
    - 1.5  → effective = 0.95 × value
    """

    def setup_method(self):
        self.snapshot = _make_snapshot(
            income=5000.0, fixed=3000.0, variable=1000.0,
            savings_balance=0.0, goal_amount=10000.0,
        )
        self.baseline = build_baseline_projection(self.snapshot)
        self.change = BehaviorChange(type="savings_increase", value=400)

    def test_floor_clamp_zero_adherence(self):
        result = simulate_scenario(
            self.snapshot, self.baseline, self.change, adherence_rate=0.0
        )
        assert abs(result.effective_monthly_change - 0.1 * 400) < 1e-9

    def test_ceiling_clamp_above_one_adherence(self):
        result = simulate_scenario(
            self.snapshot, self.baseline, self.change, adherence_rate=1.5
        )
        assert abs(result.effective_monthly_change - 0.95 * 400) < 1e-9

    def test_floor_clamp_negative_adherence(self):
        result = simulate_scenario(
            self.snapshot, self.baseline, self.change, adherence_rate=-1.0
        )
        assert abs(result.effective_monthly_change - 0.1 * 400) < 1e-9

    def test_in_range_adherence_not_clamped(self):
        result = simulate_scenario(
            self.snapshot, self.baseline, self.change, adherence_rate=0.6
        )
        assert abs(result.effective_monthly_change - 0.6 * 400) < 1e-9
