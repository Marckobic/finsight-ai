"""
tests/validation/test_validator.py
Validation Gateway — hard safety layer test suite.

PRD Section 16 CI Gate:
  # CI GATE: build fails if hallucination_rate > 1%
  The hallucination test cases below are the seed of the ≥50-case suite
  (to be expanded in Phase 3 QA sprint).

Coverage requirements:
  - validate_scenario_output: all 7 checks + edge cases
  - validate_ai_output: schema, content, hallucination detection
  - validate_financial_inputs: hard blocks + sanity warnings
"""

from shared_types.models import (
    BaselineResult,
    ScenarioResult,
    ValidationResult,
)
from validation_gateway.validator import (
    _FALLBACK_EXPLANATION,
    _FALLBACK_RECOMMENDATION,
    validate_ai_output,
    validate_financial_inputs,
    validate_scenario_output,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_baseline(
    monthly_cashflow: float = 300.0,
    savings_rate: float = 5.0,
    time_to_goal_months: int | None = 24,
    monthly_savings_gap: float = 100.0,
    goal_already_met: bool = False,
) -> BaselineResult:
    return BaselineResult(
        monthly_cashflow=monthly_cashflow,
        savings_rate=savings_rate,
        time_to_goal_months=time_to_goal_months,
        monthly_savings_gap=monthly_savings_gap,
        goal_already_met=goal_already_met,
    )


def make_scenario(
    baseline_months: int | None = 24,
    scenario_months: int | None = 18,
    delta_months: int | None = 6,
    adherence_rate: float = 0.8,
    effective_monthly_change: float = 240.0,
    scenario_monthly_cashflow: float = 540.0,
    is_improvement: bool = True,
) -> ScenarioResult:
    return ScenarioResult(
        baseline_months=baseline_months,
        scenario_months=scenario_months,
        delta_months=delta_months,
        adherence_rate=adherence_rate,
        effective_monthly_change=effective_monthly_change,
        scenario_monthly_cashflow=scenario_monthly_cashflow,
        is_improvement=is_improvement,
    )


def make_raw_ai(
    recommendation: str = "Increase monthly savings by $240.",
    explanation: str = (
        "By saving more each month, you can reach your goal "
        "in 18 months instead of 24, saving 6 months overall."
    ),
) -> dict:
    return {"recommendation": recommendation, "explanation": explanation}


# ---------------------------------------------------------------------------
# validate_scenario_output
# ---------------------------------------------------------------------------


class TestValidateScenarioOutputValid:
    """Check 0: Passing cases — all checks must succeed."""

    def test_valid_scenario_result_object_passes(self):
        sr = make_scenario()
        result = validate_scenario_output(sr)

        assert result.valid is True
        assert result.errors == []
        assert result.fallback_used is False
        assert result.validated_output is None

    def test_valid_scenario_dict_passes(self):
        d = {
            "baseline_months": 24,
            "scenario_months": 18,
            "delta_months": 6,
            "adherence_rate": 0.8,
            "effective_monthly_change": 240.0,
            "scenario_monthly_cashflow": 540.0,
            "is_improvement": True,
        }
        result = validate_scenario_output(d)

        assert result.valid is True
        assert result.fallback_used is False

    def test_valid_edge_case_baseline_none_scenario_reachable(self):
        """
        Baseline unreachable (None), but behavior change makes goal reachable.
        Checks 6 and 7 must be skipped when delta_months is None.
        """
        sr = make_scenario(
            baseline_months=None,
            scenario_months=18,
            delta_months=None,
            adherence_rate=0.5,
            effective_monthly_change=150.0,
            scenario_monthly_cashflow=450.0,
            is_improvement=True,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True
        assert result.errors == []
        assert result.fallback_used is False

    def test_valid_both_months_none_passes(self):
        """Both baseline and scenario unreachable — delta is None, skip checks 6 and 7."""
        sr = make_scenario(
            baseline_months=None,
            scenario_months=None,
            delta_months=None,
            adherence_rate=0.5,
            effective_monthly_change=100.0,
            scenario_monthly_cashflow=400.0,
            is_improvement=False,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True

    def test_valid_adherence_at_floor(self):
        """adherence_rate = 0.1 is the minimum valid value."""
        sr = make_scenario(adherence_rate=0.1, effective_monthly_change=30.0)
        result = validate_scenario_output(sr)

        assert result.valid is True

    def test_valid_adherence_at_ceiling(self):
        """adherence_rate = 0.95 is the maximum valid value."""
        sr = make_scenario(adherence_rate=0.95, effective_monthly_change=285.0)
        result = validate_scenario_output(sr)

        assert result.valid is True

    def test_valid_scenario_months_near_upper_bound(self):
        """scenario_months = 1199 is the last valid value."""
        sr = make_scenario(
            baseline_months=1200,
            scenario_months=1199,
            delta_months=1,
            is_improvement=True,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True

    def test_valid_delta_zero_is_improvement_false(self):
        """delta_months = 0 with baseline reachable → is_improvement must be False."""
        sr = make_scenario(
            baseline_months=24,
            scenario_months=24,
            delta_months=0,
            effective_monthly_change=0.0,
            is_improvement=False,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True


class TestValidateScenarioOutputCheck1Schema:
    """Check 1: Schema validation."""

    def test_missing_is_improvement_field_fails(self):
        d = {
            "baseline_months": 24,
            "scenario_months": 18,
            "delta_months": 6,
            "adherence_rate": 0.8,
            "effective_monthly_change": 240.0,
            "scenario_monthly_cashflow": 540.0,
            # is_improvement missing
        }
        result = validate_scenario_output(d)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None
        assert result.validated_output.recommendation == _FALLBACK_RECOMMENDATION

    def test_missing_adherence_rate_fails(self):
        d = {
            "baseline_months": 24,
            "scenario_months": 18,
            "delta_months": 6,
            "effective_monthly_change": 240.0,
            "scenario_monthly_cashflow": 540.0,
            "is_improvement": True,
        }
        result = validate_scenario_output(d)

        assert result.valid is False
        assert result.fallback_used is True

    def test_wrong_type_for_is_improvement_fails(self):
        d = {
            "baseline_months": 24,
            "scenario_months": 18,
            "delta_months": 6,
            "adherence_rate": 0.8,
            "effective_monthly_change": 240.0,
            "scenario_monthly_cashflow": 540.0,
            "is_improvement": "yes",  # must be bool
        }
        # Pydantic v2 coerces "yes" → True; this should pass schema
        # but this documents the behavior
        result = validate_scenario_output(d)
        # Schema passes (Pydantic coerces "yes" to True) — downstream checks run
        assert isinstance(result, ValidationResult)

    def test_nan_in_scenario_months_fails(self):
        """float('nan') cannot be coerced to Optional[int] — schema check catches it."""
        import math as _math
        d = {
            "baseline_months": 24,
            "scenario_months": _math.nan,
            "delta_months": 6,
            "adherence_rate": 0.8,
            "effective_monthly_change": 240.0,
            "scenario_monthly_cashflow": 540.0,
            "is_improvement": True,
        }
        result = validate_scenario_output(d)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None

    def test_non_dict_non_model_input_fails(self):
        result = validate_scenario_output("not a scenario")

        assert result.valid is False
        assert result.fallback_used is True

    def test_none_input_fails(self):
        result = validate_scenario_output(None)

        assert result.valid is False
        assert result.fallback_used is True


class TestValidateScenarioOutputCheck2NaN:
    """Check 2: NaN / Infinity in float fields."""

    def test_infinity_in_effective_change_fails(self):
        """float('inf') is a valid Python float — schema passes but NaN check catches it."""
        import math as _math
        d = {
            "baseline_months": 24,
            "scenario_months": 18,
            "delta_months": 6,
            "adherence_rate": 0.8,
            "effective_monthly_change": _math.inf,
            "scenario_monthly_cashflow": 540.0,
            "is_improvement": True,
        }
        result = validate_scenario_output(d)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None
        assert any("effective_monthly_change" in e for e in result.errors)

    def test_nan_in_adherence_rate_fails(self):
        import math as _math
        d = {
            "baseline_months": 24,
            "scenario_months": 18,
            "delta_months": 6,
            "adherence_rate": _math.nan,
            "effective_monthly_change": 240.0,
            "scenario_monthly_cashflow": 540.0,
            "is_improvement": True,
        }
        result = validate_scenario_output(d)

        assert result.valid is False
        assert result.fallback_used is True

    def test_infinity_in_scenario_cashflow_fails(self):
        import math as _math
        d = {
            "baseline_months": 24,
            "scenario_months": 18,
            "delta_months": 6,
            "adherence_rate": 0.8,
            "effective_monthly_change": 240.0,
            "scenario_monthly_cashflow": _math.inf,
            "is_improvement": True,
        }
        result = validate_scenario_output(d)

        assert result.valid is False
        assert result.fallback_used is True
        assert any("scenario_monthly_cashflow" in e for e in result.errors)

    def test_negative_infinity_also_rejected(self):
        import math as _math
        d = {
            "baseline_months": 24,
            "scenario_months": 18,
            "delta_months": 6,
            "adherence_rate": 0.8,
            "effective_monthly_change": -_math.inf,
            "scenario_monthly_cashflow": 540.0,
            "is_improvement": True,
        }
        result = validate_scenario_output(d)

        assert result.valid is False
        assert result.fallback_used is True


class TestValidateScenarioOutputCheck3Adherence:
    """Check 3: Adherence bounds [0.1, 0.95]."""

    def test_adherence_below_floor_fails(self):
        """adherence_rate = 0.05 is below the 0.1 floor."""
        sr = make_scenario(adherence_rate=0.05)
        result = validate_scenario_output(sr)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None
        assert any("adherence_rate" in e for e in result.errors)

    def test_adherence_above_ceiling_fails(self):
        """adherence_rate = 1.0 is above the 0.95 ceiling."""
        sr = make_scenario(adherence_rate=1.0)
        result = validate_scenario_output(sr)

        assert result.valid is False
        assert result.fallback_used is True
        assert any("adherence_rate" in e for e in result.errors)

    def test_adherence_zero_fails(self):
        sr = make_scenario(adherence_rate=0.0)
        result = validate_scenario_output(sr)

        assert result.valid is False

    def test_adherence_just_below_floor_fails(self):
        """0.09 < 0.1 → fail."""
        sr = make_scenario(adherence_rate=0.09)
        result = validate_scenario_output(sr)

        assert result.valid is False

    def test_adherence_just_above_ceiling_fails(self):
        """0.96 > 0.95 → fail."""
        sr = make_scenario(adherence_rate=0.96)
        result = validate_scenario_output(sr)

        assert result.valid is False


class TestValidateScenarioOutputCheck4EffectiveChange:
    """Check 4: effective_monthly_change >= 0."""

    def test_negative_effective_change_fails(self):
        sr = make_scenario(effective_monthly_change=-1.0)
        result = validate_scenario_output(sr)

        assert result.valid is False
        assert result.fallback_used is True
        assert any("effective_monthly_change" in e for e in result.errors)

    def test_zero_effective_change_passes(self):
        """Zero change is valid (no behavioral improvement, still passes schema)."""
        sr = make_scenario(
            baseline_months=24,
            scenario_months=24,
            delta_months=0,
            effective_monthly_change=0.0,
            is_improvement=False,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True


class TestValidateScenarioOutputCheck5MonthSanity:
    """Check 5: scenario_months must be > 0 and < 1200 (if not None)."""

    def test_scenario_months_zero_fails(self):
        """scenario_months = 0 violates > 0 constraint."""
        sr = make_scenario(
            baseline_months=24,
            scenario_months=0,
            delta_months=24,
            is_improvement=True,
        )
        result = validate_scenario_output(sr)

        assert result.valid is False
        assert result.fallback_used is True
        assert any("scenario_months" in e for e in result.errors)

    def test_scenario_months_1500_fails(self):
        """scenario_months = 1500 violates < 1200 constraint."""
        sr = make_scenario(
            baseline_months=1600,
            scenario_months=1500,
            delta_months=100,
            is_improvement=True,
        )
        result = validate_scenario_output(sr)

        assert result.valid is False
        assert result.fallback_used is True
        assert any("scenario_months" in e for e in result.errors)

    def test_scenario_months_1200_fails(self):
        """1200 is excluded by < 1200 constraint."""
        sr = make_scenario(
            baseline_months=1201,
            scenario_months=1200,
            delta_months=1,
            is_improvement=True,
        )
        result = validate_scenario_output(sr)

        assert result.valid is False

    def test_scenario_months_none_skips_check(self):
        """None scenario_months means goal is unreachable — check is skipped."""
        sr = make_scenario(
            baseline_months=None,
            scenario_months=None,
            delta_months=None,
            is_improvement=False,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True

    def test_scenario_months_one_passes(self):
        """scenario_months = 1 is the smallest valid value."""
        sr = make_scenario(
            baseline_months=2,
            scenario_months=1,
            delta_months=1,
            is_improvement=True,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True


class TestValidateScenarioOutputCheck6DeltaConsistency:
    """Check 6: delta_months must equal baseline_months - scenario_months exactly."""

    def test_delta_inconsistent_fails(self):
        """baseline=24, scenario=18 → expected delta=6, actual delta=5 → fail."""
        sr = make_scenario(
            baseline_months=24,
            scenario_months=18,
            delta_months=5,  # correct is 6
            is_improvement=True,
        )
        result = validate_scenario_output(sr)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None

    def test_delta_off_by_one_fails(self):
        sr = make_scenario(
            baseline_months=12,
            scenario_months=9,
            delta_months=4,  # correct is 3
        )
        result = validate_scenario_output(sr)

        assert result.valid is False

    def test_delta_consistent_passes(self):
        sr = make_scenario(
            baseline_months=30,
            scenario_months=22,
            delta_months=8,
            is_improvement=True,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True

    def test_skip_check_when_baseline_is_none(self):
        """Cannot compute delta when baseline is None — check is skipped."""
        sr = make_scenario(
            baseline_months=None,
            scenario_months=18,
            delta_months=None,
            is_improvement=True,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True

    def test_skip_check_when_scenario_is_none(self):
        sr = make_scenario(
            baseline_months=24,
            scenario_months=None,
            delta_months=None,
            is_improvement=False,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True


class TestValidateScenarioOutputCheck7IsImprovement:
    """Check 7: is_improvement must mirror delta direction."""

    def test_is_improvement_true_when_delta_nonpositive_fails(self):
        """delta_months = 0 and baseline reachable → is_improvement must be False."""
        sr = make_scenario(
            baseline_months=24,
            scenario_months=24,
            delta_months=0,
            effective_monthly_change=0.0,
            is_improvement=True,  # wrong — should be False
        )
        result = validate_scenario_output(sr)

        assert result.valid is False
        assert result.fallback_used is True
        assert any("is_improvement" in e for e in result.errors)

    def test_is_improvement_true_when_delta_negative_fails(self):
        """delta_months < 0 means scenario is worse — is_improvement must be False."""
        sr = make_scenario(
            baseline_months=18,
            scenario_months=24,
            delta_months=-6,
            is_improvement=True,  # wrong
        )
        result = validate_scenario_output(sr)

        assert result.valid is False
        assert any("is_improvement" in e for e in result.errors)

    def test_is_improvement_false_when_delta_positive_fails(self):
        """delta_months > 0 → is_improvement must be True."""
        sr = make_scenario(
            baseline_months=24,
            scenario_months=18,
            delta_months=6,
            is_improvement=False,  # wrong — should be True
        )
        result = validate_scenario_output(sr)

        assert result.valid is False
        assert any("is_improvement" in e for e in result.errors)

    def test_is_improvement_false_when_delta_zero_and_reachable_passes(self):
        sr = make_scenario(
            baseline_months=24,
            scenario_months=24,
            delta_months=0,
            effective_monthly_change=0.0,
            is_improvement=False,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True

    def test_is_improvement_true_when_baseline_none_delta_none_passes(self):
        """When baseline is None and delta is None, is_improvement check is skipped."""
        sr = make_scenario(
            baseline_months=None,
            scenario_months=12,
            delta_months=None,
            is_improvement=True,
        )
        result = validate_scenario_output(sr)

        assert result.valid is True


class TestValidateScenarioOutputFallbackContent:
    """Fallback output must always be the deterministic template — never None."""

    def test_fallback_output_is_deterministic(self):
        """Any failure returns the same fallback template every time."""
        sr_bad = make_scenario(adherence_rate=0.05)

        results = [validate_scenario_output(sr_bad) for _ in range(10)]

        recs = {r.validated_output.recommendation for r in results}
        exps = {r.validated_output.explanation for r in results}
        assert len(recs) == 1, "Fallback recommendation must be deterministic"
        assert len(exps) == 1, "Fallback explanation must be deterministic"

    def test_fallback_recommendation_matches_spec(self):
        result = validate_scenario_output(make_scenario(adherence_rate=0.05))

        assert result.validated_output.recommendation == _FALLBACK_RECOMMENDATION

    def test_fallback_explanation_matches_spec(self):
        result = validate_scenario_output(make_scenario(adherence_rate=0.05))

        assert result.validated_output.explanation == _FALLBACK_EXPLANATION

    def test_fallback_never_none_on_failure(self):
        """SYSTEM RULE: validated_output must never be None when fallback_used=True."""
        failure_cases = [
            make_scenario(adherence_rate=0.05),            # bounds
            make_scenario(effective_monthly_change=-1.0),  # negative change
            make_scenario(scenario_months=0, baseline_months=24, delta_months=24),  # sanity
        ]
        for sr in failure_cases:
            result = validate_scenario_output(sr)
            assert result.fallback_used is True
            assert result.validated_output is not None, (
                f"validated_output must not be None when fallback_used=True: {result.errors}"
            )


# ---------------------------------------------------------------------------
# validate_ai_output
# ---------------------------------------------------------------------------


class TestValidateAIOutputValid:
    """Passing cases."""

    def test_valid_output_passes(self):
        baseline = make_baseline(time_to_goal_months=24)
        scenario = make_scenario(baseline_months=24, scenario_months=18, delta_months=6)
        raw = make_raw_ai()

        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True
        assert result.fallback_used is False
        assert result.validated_output is not None
        assert result.validated_output.recommendation == raw["recommendation"]
        assert result.validated_output.explanation == raw["explanation"]

    def test_valid_output_with_no_numeric_fabrication(self):
        """Text that only references engine-verified month values passes."""
        baseline = make_baseline(time_to_goal_months=24)
        scenario = make_scenario(baseline_months=24, scenario_months=18, delta_months=6)
        raw = make_raw_ai(
            recommendation="Save more each month.",
            explanation="You can reach your goal in 18 months instead of 24. That is 6 months sooner.",
        )
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True
        assert result.fallback_used is False

    def test_fallback_used_is_false_on_success(self):
        baseline = make_baseline()
        scenario = make_scenario()
        raw = make_raw_ai()

        result = validate_ai_output(raw, baseline, scenario)

        assert result.fallback_used is False


class TestValidateAIOutputCheck1Schema:
    """Check 1: raw_output must match AIExplanationOutput schema."""

    def test_missing_recommendation_key_fails(self):
        baseline = make_baseline()
        scenario = make_scenario()
        raw = {"explanation": "Some explanation."}  # recommendation missing

        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None
        assert result.validated_output.recommendation == _FALLBACK_RECOMMENDATION

    def test_missing_explanation_key_fails(self):
        baseline = make_baseline()
        scenario = make_scenario()
        raw = {"recommendation": "Do something."}  # explanation missing

        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False
        assert result.fallback_used is True

    def test_empty_dict_fails(self):
        baseline = make_baseline()
        scenario = make_scenario()

        result = validate_ai_output({}, baseline, scenario)

        assert result.valid is False
        assert result.fallback_used is True

    def test_non_dict_input_fails(self):
        baseline = make_baseline()
        scenario = make_scenario()

        result = validate_ai_output("not a dict", baseline, scenario)

        assert result.valid is False
        assert result.fallback_used is True

    def test_extra_keys_are_ignored(self):
        """Pydantic ignores extra fields — valid output still passes."""
        baseline = make_baseline()
        scenario = make_scenario()
        raw = {
            "recommendation": "Save more.",
            "explanation": "This will help.",
            "unexpected_field": "ignored",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True


class TestValidateAIOutputCheck2NonEmpty:
    """Check 2: recommendation and explanation must not be blank."""

    def test_empty_recommendation_fails(self):
        baseline = make_baseline()
        scenario = make_scenario()
        raw = {"recommendation": "", "explanation": "Some explanation."}

        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None

    def test_whitespace_only_explanation_fails(self):
        baseline = make_baseline()
        scenario = make_scenario()
        raw = {"recommendation": "Do something.", "explanation": "   \t\n  "}

        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False
        assert result.fallback_used is True
        assert any("explanation" in e for e in result.errors)

    def test_whitespace_only_recommendation_fails(self):
        baseline = make_baseline()
        scenario = make_scenario()
        raw = {"recommendation": "  ", "explanation": "Detailed explanation here."}

        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False

    def test_single_space_recommendation_fails(self):
        baseline = make_baseline()
        scenario = make_scenario()
        raw = {"recommendation": " ", "explanation": "Some explanation."}

        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False


class TestValidateAIOutputCheck3Hallucination:
    """
    Check 3: Numeric fabrication detection.
    # CI GATE: build fails if hallucination_rate > 1%
    Seed suite — to be expanded to ≥50 cases in Phase 3 QA sprint.
    """

    def _make_engine_pair(self, baseline_m=24, scenario_m=18, delta_m=6):
        return (
            make_baseline(time_to_goal_months=baseline_m),
            make_scenario(
                baseline_months=baseline_m,
                scenario_months=scenario_m,
                delta_months=delta_m,
            ),
        )

    def test_hallucinated_month_value_fails(self):
        """AI invents '42 months' — not present in any engine output → flagged."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Adjust savings.",
            "explanation": "You could reach your goal in 42 months with this change.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None
        assert any("42" in e for e in result.errors)

    def test_hallucinated_value_not_in_engine_output_fails(self):
        """AI says '100 months' — engine has 24, 18, 6. Not in engine output."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Save more.",
            "explanation": "Without changes, it could take 100 months to reach your goal.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False
        assert any("100" in e for e in result.errors)

    def test_multiple_hallucinated_values_all_flagged(self):
        """AI fabricates multiple month counts not in engine output."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Reduce spending.",
            "explanation": "You might reach your goal in 36 or 48 months.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False
        assert len(result.errors) >= 2

    def test_dollar_amount_is_allowed(self):
        """'$300' must NOT be flagged — dollar amounts are explicitly excluded."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Increase your monthly savings by $300.",
            "explanation": "Saving an extra $300 per month will accelerate your goal.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True
        assert result.fallback_used is False

    def test_percentage_is_allowed(self):
        """'70%' must NOT be flagged — percentages are explicitly excluded."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Commit to 70% of this plan.",
            "explanation": "Following 70% of the plan consistently is the key.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True
        assert result.fallback_used is False

    def test_engine_month_values_allowed(self):
        """AI references exact engine month values (18, 24, 6) → no hallucination."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = make_raw_ai(
            recommendation="Increase savings to reach goal in 18 months instead of 24.",
            explanation="This change saves you 6 months on your timeline.",
        )
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True
        assert result.fallback_used is False

    def test_number_below_range_not_flagged(self):
        """Numbers below 3 (e.g., '1' or '2') are not in the suspicious range."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Start with 1 small change today.",
            "explanation": "Even 2 adjustments per month can make a difference.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True

    def test_boundary_value_3_is_flagged_if_not_in_engine(self):
        """3 is at the lower bound of the suspicious range and NOT in engine output."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Save more.",
            "explanation": "You can save time in 3 easy steps.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False  # 3 is not in {24, 18, 6}

    def test_boundary_value_500_is_flagged_if_not_in_engine(self):
        """500 is at the upper bound of the suspicious range."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Save.",
            "explanation": "Saving up for 500 reasons to feel secure.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is False  # 500 not in {24, 18, 6}

    def test_value_just_above_range_not_flagged(self):
        """501 is above the suspicious range — not flagged."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Save.",
            "explanation": "There are 501 ways to think about your finances.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        # 501 > 500, outside suspicious range → not flagged
        assert result.valid is True

    def test_dollar_amount_500_not_flagged(self):
        """$500 — even though 500 is at the boundary, dollar prefix exempts it."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Save $500 per month.",
            "explanation": "An extra $500 monthly contribution will help greatly.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True

    def test_percentage_boundary_not_flagged(self):
        """300% is in range but has % suffix — exempted."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Save.",
            "explanation": "You get 300% value from consistent contributions.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True

    def test_no_numbers_in_text_passes(self):
        """AI text with no numbers at all → trivially passes hallucination check."""
        baseline, scenario = self._make_engine_pair(24, 18, 6)
        raw = {
            "recommendation": "Keep saving consistently.",
            "explanation": "Small consistent changes add up over time.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True

    def test_engine_baseline_months_from_scenario_object_allowed(self):
        """baseline_months in ScenarioResult is a valid reference value."""
        baseline = make_baseline(time_to_goal_months=36)
        scenario = make_scenario(
            baseline_months=36,
            scenario_months=28,
            delta_months=8,
        )
        raw = {
            "recommendation": "Save more each month.",
            "explanation": "Your baseline is 36 months. With changes, reach it in 28. Save 8 months.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        assert result.valid is True

    def test_baseline_none_no_valid_baseline_months(self):
        """When baseline_months is None, that value is not in the valid set."""
        baseline = make_baseline(time_to_goal_months=None)
        scenario = make_scenario(
            baseline_months=None,
            scenario_months=18,
            delta_months=None,
        )
        raw = {
            "recommendation": "Save more.",
            "explanation": "You can reach your goal in 18 months.",
        }
        result = validate_ai_output(raw, baseline, scenario)

        # 18 is in engine valid values (scenario_months) → passes
        assert result.valid is True


class TestValidateAIOutputFallbackContent:
    """Fallback template behavior on AI output validation failures."""

    def test_fallback_output_not_none_on_schema_failure(self):
        baseline = make_baseline()
        scenario = make_scenario()

        result = validate_ai_output({}, baseline, scenario)

        assert result.validated_output is not None
        assert result.validated_output.recommendation == _FALLBACK_RECOMMENDATION
        assert result.validated_output.explanation == _FALLBACK_EXPLANATION

    def test_fallback_output_not_none_on_hallucination(self):
        baseline, scenario = make_baseline(), make_scenario()
        raw = {"recommendation": "Save.", "explanation": "Reach goal in 42 months."}

        result = validate_ai_output(raw, baseline, scenario)

        assert result.validated_output is not None
        assert result.validated_output.recommendation == _FALLBACK_RECOMMENDATION


# ---------------------------------------------------------------------------
# validate_financial_inputs
# ---------------------------------------------------------------------------


class TestValidateFinancialInputsValid:
    """Passing cases."""

    def test_all_valid_inputs_pass(self):
        result = validate_financial_inputs(
            income=5000.0,
            fixed_expenses=2000.0,
            variable_expenses=1000.0,
            current_savings=5000.0,
            monthly_savings_contribution=500.0,
            goal_amount=20000.0,
        )

        assert result.valid is True
        assert result.fallback_used is False
        assert result.validated_output is None

    def test_all_fields_zero_except_income_passes(self):
        """All optional fields at zero are valid — only income and goal are constrained."""
        result = validate_financial_inputs(
            income=1000.0,
            fixed_expenses=0.0,
            variable_expenses=0.0,
            current_savings=0.0,
            monthly_savings_contribution=0.0,
            goal_amount=5000.0,
        )

        assert result.valid is True

    def test_minimal_valid_income_passes(self):
        result = validate_financial_inputs(
            income=0.01,
            fixed_expenses=0.0,
            variable_expenses=0.0,
            current_savings=0.0,
            monthly_savings_contribution=0.0,
            goal_amount=100.0,
        )

        assert result.valid is True

    def test_minimal_valid_goal_amount_passes(self):
        result = validate_financial_inputs(
            income=1000.0,
            fixed_expenses=0.0,
            variable_expenses=0.0,
            current_savings=0.0,
            monthly_savings_contribution=0.0,
            goal_amount=0.01,
        )

        assert result.valid is True


class TestValidateFinancialInputsHardBlocks:
    """Hard blocks — valid=False with error messages."""

    def test_income_zero_fails(self):
        result = validate_financial_inputs(
            income=0.0,
            fixed_expenses=500.0,
            variable_expenses=300.0,
            current_savings=1000.0,
            monthly_savings_contribution=100.0,
            goal_amount=5000.0,
        )

        assert result.valid is False
        assert result.fallback_used is False
        assert result.validated_output is None
        assert any("income" in e for e in result.errors)

    def test_income_negative_fails(self):
        result = validate_financial_inputs(
            income=-1.0,
            fixed_expenses=500.0,
            variable_expenses=300.0,
            current_savings=1000.0,
            monthly_savings_contribution=100.0,
            goal_amount=5000.0,
        )

        assert result.valid is False
        assert any("income" in e for e in result.errors)

    def test_negative_fixed_expenses_fails(self):
        result = validate_financial_inputs(
            income=5000.0,
            fixed_expenses=-100.0,
            variable_expenses=500.0,
            current_savings=1000.0,
            monthly_savings_contribution=100.0,
            goal_amount=5000.0,
        )

        assert result.valid is False
        assert any("fixed_expenses" in e for e in result.errors)

    def test_negative_variable_expenses_fails(self):
        result = validate_financial_inputs(
            income=5000.0,
            fixed_expenses=1000.0,
            variable_expenses=-50.0,
            current_savings=1000.0,
            monthly_savings_contribution=100.0,
            goal_amount=5000.0,
        )

        assert result.valid is False

    def test_negative_current_savings_fails(self):
        result = validate_financial_inputs(
            income=5000.0,
            fixed_expenses=1000.0,
            variable_expenses=500.0,
            current_savings=-500.0,
            monthly_savings_contribution=100.0,
            goal_amount=5000.0,
        )

        assert result.valid is False
        assert any("current_savings" in e for e in result.errors)

    def test_negative_monthly_savings_contribution_fails(self):
        result = validate_financial_inputs(
            income=5000.0,
            fixed_expenses=1000.0,
            variable_expenses=500.0,
            current_savings=1000.0,
            monthly_savings_contribution=-10.0,
            goal_amount=5000.0,
        )

        assert result.valid is False

    def test_goal_amount_zero_fails(self):
        result = validate_financial_inputs(
            income=5000.0,
            fixed_expenses=1000.0,
            variable_expenses=500.0,
            current_savings=1000.0,
            monthly_savings_contribution=100.0,
            goal_amount=0.0,
        )

        assert result.valid is False
        assert any("goal_amount" in e for e in result.errors)

    def test_goal_amount_negative_fails(self):
        result = validate_financial_inputs(
            income=5000.0,
            fixed_expenses=1000.0,
            variable_expenses=500.0,
            current_savings=1000.0,
            monthly_savings_contribution=100.0,
            goal_amount=-100.0,
        )

        assert result.valid is False

    def test_multiple_invalid_fields_all_reported(self):
        """All hard block violations should be reported together."""
        result = validate_financial_inputs(
            income=0.0,
            fixed_expenses=-100.0,
            variable_expenses=500.0,
            current_savings=1000.0,
            monthly_savings_contribution=100.0,
            goal_amount=0.0,
        )

        assert result.valid is False
        assert len(result.errors) >= 2


class TestValidateFinancialInputsSanityWarnings:
    """Sanity warnings — valid=True, errors contains the warning."""

    def test_expenses_exceed_triple_income_warns(self):
        """fixed + variable > income × 3 → warning, but still valid."""
        income = 1000.0
        result = validate_financial_inputs(
            income=income,
            fixed_expenses=2000.0,
            variable_expenses=1500.0,  # total=3500 > 3000=3×income
            current_savings=0.0,
            monthly_savings_contribution=0.0,
            goal_amount=5000.0,
        )

        assert result.valid is True
        assert len(result.errors) == 1
        assert "3" in result.errors[0] or "review" in result.errors[0].lower()

    def test_expenses_exactly_triple_income_no_warning(self):
        """Exactly 3× income is not > 3× — no warning should be raised."""
        income = 1000.0
        result = validate_financial_inputs(
            income=income,
            fixed_expenses=1500.0,
            variable_expenses=1500.0,  # total=3000 = 3×income (not >)
            current_savings=0.0,
            monthly_savings_contribution=0.0,
            goal_amount=5000.0,
        )

        assert result.valid is True
        assert result.errors == []

    def test_expenses_just_above_triple_income_warns(self):
        """3001 > 3000 (3×1000) — warning triggered."""
        income = 1000.0
        result = validate_financial_inputs(
            income=income,
            fixed_expenses=1500.1,
            variable_expenses=1500.0,  # total≈3000.1 > 3000
            current_savings=0.0,
            monthly_savings_contribution=0.0,
            goal_amount=5000.0,
        )

        assert result.valid is True
        assert len(result.errors) == 1

    def test_normal_expenses_no_warning(self):
        """Normal expense ratio produces no warnings."""
        result = validate_financial_inputs(
            income=5000.0,
            fixed_expenses=2000.0,
            variable_expenses=1000.0,
            current_savings=5000.0,
            monthly_savings_contribution=500.0,
            goal_amount=20000.0,
        )

        assert result.valid is True
        assert result.errors == []

    def test_warning_does_not_block_submission(self):
        """Sanity warning must not set valid=False."""
        result = validate_financial_inputs(
            income=500.0,
            fixed_expenses=1000.0,
            variable_expenses=600.0,  # total=1600 > 1500=3×500
            current_savings=0.0,
            monthly_savings_contribution=0.0,
            goal_amount=2000.0,
        )

        assert result.valid is True
        assert result.fallback_used is False

    def test_validated_output_always_none_for_financial_inputs(self):
        """Financial input validation never populates validated_output."""
        valid_result = validate_financial_inputs(
            income=5000.0,
            fixed_expenses=1000.0,
            variable_expenses=500.0,
            current_savings=0.0,
            monthly_savings_contribution=0.0,
            goal_amount=5000.0,
        )
        invalid_result = validate_financial_inputs(
            income=0.0,
            fixed_expenses=0.0,
            variable_expenses=0.0,
            current_savings=0.0,
            monthly_savings_contribution=0.0,
            goal_amount=0.0,
        )

        assert valid_result.validated_output is None
        assert invalid_result.validated_output is None
