"""
packages/validation-gateway/tests/test_scorer.py
Quality scorer + health tracker tests.
"""

import pytest

from shared_types.models import (
    AIExplanationOutput,
    BaselineResult,
    ScenarioResult,
    ValidationResult,
)
from validation_gateway.scorer import AIQualityScore, score_ai_output
from validation_gateway.health import AIHealthTracker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_validation(valid: bool = True) -> ValidationResult:
    from validation_gateway.validator import _fallback_output
    return ValidationResult(
        valid=valid,
        errors=[] if valid else ["validation failed"],
        fallback_used=not valid,
        validated_output=None if valid else _fallback_output(),
    )


def make_baseline(time_to_goal: int | None = 24) -> BaselineResult:
    return BaselineResult(
        monthly_cashflow=300.0,
        savings_rate=5.0,
        time_to_goal_months=time_to_goal,
        monthly_savings_gap=100.0,
        goal_already_met=False,
    )


def make_scenario(
    baseline_months: int | None = 24,
    scenario_months: int | None = 18,
    delta_months: int | None = 6,
    adherence_rate: float = 0.8,
    is_improvement: bool = True,
) -> ScenarioResult:
    return ScenarioResult(
        baseline_months=baseline_months,
        scenario_months=scenario_months,
        delta_months=delta_months,
        adherence_rate=adherence_rate,
        effective_monthly_change=240.0,
        scenario_monthly_cashflow=540.0,
        is_improvement=is_improvement,
    )


def make_output(
    recommendation: str = "Increase monthly savings by $300 per month.",
    explanation: str = "Based on these figures, this change accelerates your timeline.",
    summary: str = "Saving $300/month reduces your timeline by 6 months.",
    confidence: str = "high",
    reasoning: str = "The adherence rate of 80% applied to the scenario is well-grounded.",
    key_assumptions: list[str] | None = None,
) -> AIExplanationOutput:
    return AIExplanationOutput(
        recommendation=recommendation,
        explanation=explanation,
        summary=summary,
        confidence=confidence,
        reasoning=reasoning,
        key_assumptions=key_assumptions if key_assumptions is not None else ["adherence stable"],
    )


# ---------------------------------------------------------------------------
# test_perfect_score
# ---------------------------------------------------------------------------


def test_perfect_score():
    """Good output + valid scenario + high confidence → total >= 80 (approved)."""
    score = score_ai_output(
        validation=make_validation(valid=True),
        ai_output=make_output(),
        scenario=make_scenario(),
        baseline=make_baseline(),
    )
    assert score.total >= 80
    assert score.status == "approved"
    assert score.grounding == 40.0
    assert score.consistency == 30.0
    assert score.completeness == 20.0
    assert score.behavioral_fit == 10.0


# ---------------------------------------------------------------------------
# test_low_adherence_penalty
# ---------------------------------------------------------------------------


def test_low_adherence_penalty():
    """adherence=0.2, confidence='high' → -5 behavioral_fit."""
    score = score_ai_output(
        validation=make_validation(valid=True),
        ai_output=make_output(confidence="high"),
        scenario=make_scenario(adherence_rate=0.2),
        baseline=make_baseline(),
    )
    assert score.behavioral_fit == 5.0
    assert any("adherence" in r for r in score.reasons)


# ---------------------------------------------------------------------------
# test_fallback_triggered
# ---------------------------------------------------------------------------


def test_fallback_triggered():
    """validation.passed=False + short summary → status == 'fallback'."""
    score = score_ai_output(
        validation=make_validation(valid=False),
        ai_output=make_output(
            summary="Bad",           # < 20 chars
            key_assumptions=[],      # empty → deductions
            reasoning="",            # empty
        ),
        scenario=make_scenario(),
        baseline=make_baseline(),
    )
    assert score.status == "fallback"
    assert score.total < 60


# ---------------------------------------------------------------------------
# test_number_consistency
# ---------------------------------------------------------------------------


def test_number_consistency():
    """delta_months=5, summary has '3 months' → -15 consistency."""
    output = make_output(
        summary="This behavioral change saves you 3 months on your timeline.",
    )
    score = score_ai_output(
        validation=make_validation(valid=True),
        ai_output=output,
        scenario=make_scenario(delta_months=5),
        baseline=make_baseline(),
    )
    assert score.consistency < 30
    assert any("consistency" in r for r in score.reasons)


def test_number_within_tolerance_not_penalized():
    """delta_months=5, summary has '4 months' → |4-5|=1, within ±1, no deduction."""
    output = make_output(
        summary="This change saves you 4 months off your timeline goal.",
    )
    score = score_ai_output(
        validation=make_validation(valid=True),
        ai_output=output,
        scenario=make_scenario(delta_months=5),
        baseline=make_baseline(),
    )
    assert score.consistency == 30.0


# ---------------------------------------------------------------------------
# test_health_tracker
# ---------------------------------------------------------------------------


def test_health_tracker():
    """Record 10 scores → summary returns correct rates."""
    tracker = AIHealthTracker()

    perfect = score_ai_output(
        make_validation(), make_output(), make_scenario(), make_baseline()
    )
    fallback_out = make_output(summary="Bad", key_assumptions=[], reasoning="")
    bad = score_ai_output(
        make_validation(valid=False), fallback_out, make_scenario(), make_baseline()
    )

    # 6 approved, 4 fallback
    for _ in range(6):
        tracker.record(perfect)
    for _ in range(4):
        tracker.record(bad)

    summary = tracker.summary()
    assert summary["total_evaluations"] == 10
    assert summary["approved_rate"] == pytest.approx(0.6)
    assert summary["fallback_rate"] == pytest.approx(0.4)
    assert summary["degraded_rate"] == pytest.approx(0.0)
    assert isinstance(summary["top_failure_reasons"], list)
    assert summary["avg_score"] > 0


def test_health_tracker_empty():
    """Empty tracker returns zero summary."""
    tracker = AIHealthTracker()
    s = tracker.summary()
    assert s["total_evaluations"] == 0
    assert s["avg_score"] == 0.0
    assert s["top_failure_reasons"] == []


# ---------------------------------------------------------------------------
# Additional edge-case tests
# ---------------------------------------------------------------------------


def test_low_confidence_deducts_grounding():
    score = score_ai_output(
        make_validation(), make_output(confidence="low"), make_scenario(), make_baseline()
    )
    assert score.grounding <= 20.0
    assert any("low" in r for r in score.reasons)


def test_empty_key_assumptions_deducts_both_dimensions():
    score = score_ai_output(
        make_validation(),
        make_output(key_assumptions=[]),
        make_scenario(),
        make_baseline(),
    )
    assert score.grounding < 40.0
    assert score.completeness < 20.0


def test_no_improvement_high_confidence_penalized():
    score = score_ai_output(
        make_validation(),
        make_output(confidence="high"),
        make_scenario(is_improvement=False, delta_months=0),
        make_baseline(),
    )
    assert score.behavioral_fit < 10.0
    assert any("improvement" in r for r in score.reasons)


def test_degraded_status():
    """confidence=low + empty key_assumptions → total ~60, status=degraded."""
    score = score_ai_output(
        validation=make_validation(valid=True),
        ai_output=make_output(
            confidence="low",
            key_assumptions=[],
            # reasoning="" intentionally omitted; default in make_output is non-empty
        ),
        scenario=make_scenario(),
        baseline=make_baseline(),
    )
    # grounding: 40-20(low)-10(no assumptions) = 10
    # consistency: 30 (valid, no bad number)
    # completeness: 20-10(no assumptions) = 10  (reasoning non-empty from default)
    # behavioral_fit: 10
    # total = 60
    assert 60 <= score.total < 80
    assert score.status == "degraded"


def test_short_reasoning_deducts_completeness():
    """reasoning < 10 chars → -10 completeness."""
    score = score_ai_output(
        validation=make_validation(valid=True),
        ai_output=make_output(reasoning="Too short"),  # 9 chars
        scenario=make_scenario(),
        baseline=make_baseline(),
    )
    assert score.completeness < 20.0
    assert any("reasoning" in r for r in score.reasons)


def test_score_model_fields_present():
    """AIQualityScore exposes all required fields."""
    score = score_ai_output(
        make_validation(), make_output(), make_scenario(), make_baseline()
    )
    assert hasattr(score, "total")
    assert hasattr(score, "grounding")
    assert hasattr(score, "consistency")
    assert hasattr(score, "completeness")
    assert hasattr(score, "behavioral_fit")
    assert hasattr(score, "status")
    assert hasattr(score, "reasons")
    assert score.status in ("approved", "degraded", "fallback")
