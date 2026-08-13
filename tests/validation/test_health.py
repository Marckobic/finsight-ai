"""
tests/validation/test_health.py
The numbers /analytics/ai-health reports.

These are the metrics that replace the ones measured against a mock, so the
arithmetic behind them is worth pinning: a percentile that is quietly wrong is
worse than no percentile at all.
"""

from shared_types.models import (
    AIExplanationOutput,
    BaselineResult,
    ScenarioResult,
    ValidationResult,
)
from validation_gateway.health import AIHealthTracker
from validation_gateway.scorer import score_ai_output


def _score(valid=True):
    output = AIExplanationOutput(
        recommendation="A monthly change of $240 is projected.",
        explanation="Based on these figures, the timeline shifts to 18 months.",
        summary="At this rate the timeline shifts from 24 months to 18 months.",
        confidence="high",
        reasoning="The projection follows from the engine timeline.",
        key_assumptions=["the change is sustained"],
    )
    validation = ValidationResult(
        valid=valid, errors=[] if valid else ["nope"],
        fallback_used=not valid, validated_output=output,
    )
    baseline = BaselineResult(
        monthly_cashflow=0.0, savings_rate=0.0, time_to_goal_months=24,
        monthly_savings_gap=0.0, goal_already_met=False,
    )
    scenario = ScenarioResult(
        baseline_months=24, scenario_months=18, delta_months=6,
        adherence_rate=0.8, effective_monthly_change=240.0,
        scenario_monthly_cashflow=0.0, is_improvement=True,
    )
    return score_ai_output(validation, output, scenario, baseline)


def test_empty_tracker_reports_perfect_fidelity_not_zero():
    """No responses yet is not the same as every response being wrong."""
    summary = AIHealthTracker().summary()
    assert summary["responses"] == 0
    assert summary["numeric_fidelity_rate"] == 1.0
    assert summary["fallback_rate_observed"] == 0.0
    assert summary["latency_p95_ms"] == 0.0


def test_latency_percentiles():
    tracker = AIHealthTracker()
    for ms in [100, 200, 300, 400, 5000]:
        tracker.record(_score(), latency_ms=ms, numeric_ok=True, fallback_used=False)

    summary = tracker.summary()
    assert summary["latency_samples"] == 5
    assert summary["latency_p50_ms"] == 300.0
    assert summary["latency_p95_ms"] == 5000.0
    assert summary["latency_max_ms"] == 5000.0


def test_numeric_fidelity_and_fallback_rates():
    tracker = AIHealthTracker()
    for _ in range(8):
        tracker.record(_score(), latency_ms=100, numeric_ok=True, fallback_used=False)
    for _ in range(2):
        tracker.record(_score(valid=False), latency_ms=90, numeric_ok=False, fallback_used=True)

    summary = tracker.summary()
    assert summary["responses"] == 10
    assert summary["numeric_fidelity_rate"] == 0.8
    assert summary["fallback_rate_observed"] == 0.2


def test_recording_a_score_without_response_context_still_works():
    """Quality can be scored outside a request; it must not skew the rates."""
    tracker = AIHealthTracker()
    tracker.record(_score())
    summary = tracker.summary()

    assert summary["total_evaluations"] == 1
    assert summary["responses"] == 0
    assert summary["numeric_fidelity_rate"] == 1.0


def test_sample_lists_stay_bounded():
    """A long-lived process must not grow a list per request forever."""
    from validation_gateway import health as health_mod

    tracker = AIHealthTracker()
    limit = health_mod._MAX_SAMPLES
    for _ in range(limit + 50):
        tracker.record(_score(), latency_ms=10, numeric_ok=True, fallback_used=False)

    assert tracker.summary()["latency_samples"] == limit
    assert tracker.summary()["total_evaluations"] == limit
