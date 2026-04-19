"""
tests/ai/test_explain.py
AI Explanation Layer — test suite.

Covers:
  - build_prompt: string construction and field presence
  - call_llm: MockLLMClient modes (valid, invalid_json, hallucination)
  - generate_explanation: full pipeline behaviour across all mock modes
  - Integration: AIExplanationInput → generate_explanation → ValidationResult
"""

import pytest
from ai_layer.explain import (
    _SYSTEM_PROMPT,
    AILayerError,
    MockLLMClient,
    build_prompt,
    call_llm,
    generate_explanation,
)
from shared_types.models import AIExplanationInput, ValidationResult

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def make_input(
    baseline_months: int | None = 24,
    scenario_months: int | None = 18,
    delta_months: int | None = 6,
    monthly_change_amount: float = 300.0,
    adherence_rate: float = 0.8,
    behavior_type: str = "savings_increase",
    goal_type: str = "emergency_fund",
) -> AIExplanationInput:
    return AIExplanationInput(
        baseline_months=baseline_months,
        scenario_months=scenario_months,
        delta_months=delta_months,
        monthly_change_amount=monthly_change_amount,
        adherence_rate=adherence_rate,
        behavior_type=behavior_type,
        goal_type=goal_type,
    )


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    """Pure string construction — no LLM involved."""

    def test_returns_two_non_empty_strings(self):
        system, user = build_prompt(make_input())

        assert isinstance(system, str) and len(system) > 0
        assert isinstance(user, str) and len(user) > 0

    def test_system_prompt_contains_no_number_rule(self):
        system, _ = build_prompt(make_input())

        assert "MUST NOT generate any number" in system

    def test_system_prompt_is_constant(self):
        """system_prompt must be the immutable _SYSTEM_PROMPT constant."""
        system, _ = build_prompt(make_input())

        assert system == _SYSTEM_PROMPT

    def test_baseline_months_in_user_message(self):
        _, user = build_prompt(make_input(baseline_months=24))

        assert "24" in user

    def test_scenario_months_in_user_message(self):
        _, user = build_prompt(make_input(scenario_months=18))

        assert "18" in user

    def test_delta_months_in_user_message(self):
        _, user = build_prompt(make_input(delta_months=6))

        assert "6" in user

    def test_monthly_change_amount_in_user_message(self):
        _, user = build_prompt(make_input(monthly_change_amount=300.0))

        assert "300" in user

    def test_adherence_rate_in_user_message_as_percentage(self):
        """0.8 → 80% — must appear as percentage, not decimal."""
        _, user = build_prompt(make_input(adherence_rate=0.8))

        assert "80" in user
        assert "%" in user

    def test_all_input_numbers_appear_in_user_message(self):
        """Every number from the input must be present in the user message."""
        inp = make_input(
            baseline_months=30,
            scenario_months=22,
            delta_months=8,
            monthly_change_amount=250.0,
            adherence_rate=0.7,
        )
        _, user = build_prompt(inp)

        assert "30" in user
        assert "22" in user
        assert "8" in user
        assert "250" in user
        assert "70" in user  # 0.7 → 70%

    def test_savings_increase_action_type_in_user_message(self):
        """behavior_type='savings_increase' → 'increase' appears in user message."""
        _, user = build_prompt(make_input(behavior_type="savings_increase"))

        assert "increase" in user.lower()

    def test_expense_cut_action_type_in_user_message(self):
        """behavior_type='expense_cut' → 'cut' and 'expense' appear in user message."""
        _, user = build_prompt(make_input(behavior_type="expense_cut"))

        assert "cut" in user.lower() or "expense" in user.lower()

    def test_goal_type_in_user_message(self):
        _, user = build_prompt(make_input(goal_type="save_for_home"))

        assert "save_for_home" in user

    def test_baseline_months_none_raises_value_error(self):
        with pytest.raises(ValueError, match="baseline_months"):
            build_prompt(make_input(baseline_months=None))

    def test_scenario_months_none_raises_value_error(self):
        with pytest.raises(ValueError, match="scenario_months"):
            build_prompt(make_input(scenario_months=None))

    def test_both_months_none_raises_value_error(self):
        """baseline check fires first (fail-fast)."""
        with pytest.raises(ValueError):
            build_prompt(make_input(baseline_months=None, scenario_months=None))

    def test_dollar_sign_before_monthly_change(self):
        """monthly_change must appear as a dollar amount in the prompt."""
        _, user = build_prompt(make_input(monthly_change_amount=150.0))

        assert "$" in user
        assert "150" in user

    def test_output_format_instruction_in_system_prompt(self):
        """System prompt must specify the JSON output format."""
        system, _ = build_prompt(make_input())

        assert '"recommendation"' in system
        assert '"explanation"' in system

    def test_no_advisor_phrases_in_system_prompt(self):
        """System prompt must forbid financial-advisor language."""
        system, _ = build_prompt(make_input())

        assert "advisor" in system.lower()   # the rule references the banned word
        assert "MUST NOT" in system


# ---------------------------------------------------------------------------
# call_llm (MockLLMClient)
# ---------------------------------------------------------------------------


class TestCallLLM:
    """Test call_llm with explicit MockLLMClient instances."""

    def _build(self) -> tuple[str, str]:
        return build_prompt(make_input())

    def test_valid_mode_returns_dict_with_required_keys(self):
        system, user = self._build()
        client = MockLLMClient(mode="valid")

        result = call_llm(system, user, client=client)

        assert isinstance(result, dict)
        assert "recommendation" in result
        assert "explanation" in result

    def test_valid_mode_values_are_strings(self):
        system, user = self._build()
        client = MockLLMClient(mode="valid")

        result = call_llm(system, user, client=client)

        assert isinstance(result["recommendation"], str)
        assert isinstance(result["explanation"], str)

    def test_invalid_json_mode_raises_ai_layer_error(self):
        system, user = self._build()
        client = MockLLMClient(mode="invalid_json")

        with pytest.raises(AILayerError):
            call_llm(system, user, client=client)

    def test_invalid_json_error_message_is_descriptive(self):
        system, user = self._build()
        client = MockLLMClient(mode="invalid_json")

        with pytest.raises(AILayerError, match="non-JSON"):
            call_llm(system, user, client=client)

    def test_hallucination_mode_returns_dict(self):
        """Hallucination detection happens downstream in the validation gateway."""
        system, user = self._build()
        client = MockLLMClient(mode="hallucination")

        result = call_llm(system, user, client=client)

        assert isinstance(result, dict)
        assert "recommendation" in result
        assert "explanation" in result

    def test_empty_mode_returns_dict(self):
        """Empty strings pass call_llm — rejection happens in validate_ai_output."""
        system, user = self._build()
        client = MockLLMClient(mode="empty")

        result = call_llm(system, user, client=client)

        assert isinstance(result, dict)
        assert result["recommendation"] == ""
        assert result["explanation"] == ""

    def test_default_client_used_when_none_passed(self):
        """call_llm with client=None uses the module-level _llm_client."""
        system, user = self._build()

        result = call_llm(system, user)  # no client arg

        assert isinstance(result, dict)

    def test_explicit_client_overrides_module_default(self):
        """Passing an explicit client must take precedence over the module default."""
        system, user = self._build()
        client = MockLLMClient(mode="empty")

        result = call_llm(system, user, client=client)

        assert result["recommendation"] == ""

    def test_timeout_error_raises_ai_layer_error(self):
        """TimeoutError from the LLM client must be re-raised as AILayerError."""

        class _TimeoutClient:
            def call(self, system: str, user: str) -> str:  # noqa: ARG002
                raise TimeoutError("simulated network timeout")

        system, user = self._build()

        with pytest.raises(AILayerError, match="timed out"):
            call_llm(system, user, client=_TimeoutClient())


# ---------------------------------------------------------------------------
# MockLLMClient unit tests
# ---------------------------------------------------------------------------


class TestMockLLMClient:
    """Direct tests on the mock client's 4 modes."""

    def _prompts(self) -> tuple[str, str]:
        return build_prompt(make_input())

    def test_valid_mode_output_is_valid_json(self):
        import json as _json
        system, user = self._prompts()
        client = MockLLMClient(mode="valid")

        raw = client.call(system, user)

        parsed = _json.loads(raw)
        assert "recommendation" in parsed
        assert "explanation" in parsed

    def test_invalid_json_mode_output_is_not_parseable(self):
        import json as _json
        system, user = self._prompts()
        client = MockLLMClient(mode="invalid_json")

        raw = client.call(system, user)

        with pytest.raises(_json.JSONDecodeError):
            _json.loads(raw)

    def test_empty_mode_output_has_blank_fields(self):
        import json as _json
        system, user = self._prompts()
        client = MockLLMClient(mode="empty")

        raw = client.call(system, user)
        parsed = _json.loads(raw)

        assert parsed["recommendation"] == ""
        assert parsed["explanation"] == ""

    def test_hallucination_mode_contains_a_number_not_in_input(self):
        """The hallucinated number must NOT be in the engine's month values."""
        import json as _json
        import re as _re

        inp = make_input(baseline_months=24, scenario_months=18, delta_months=6)
        system, user = build_prompt(inp)
        client = MockLLMClient(mode="hallucination")

        raw = client.call(system, user)
        parsed = _json.loads(raw)
        text = parsed["recommendation"] + " " + parsed["explanation"]

        # Extract standalone integers from text
        numbers = [int(n) for n in _re.findall(r'\b(\d+)\b', text)]
        engine_values = {24, 18, 6}
        suspicious = [n for n in numbers if 3 <= n <= 500 and n not in engine_values]

        assert len(suspicious) > 0, (
            f"hallucination mode must contain at least one number outside engine "
            f"values {engine_values}; found numbers: {numbers}"
        )

    def test_valid_mode_uses_baseline_months_from_prompt(self):
        """valid mode must reference the actual baseline value, not a hardcoded one."""
        system, user = build_prompt(make_input(baseline_months=36))
        client = MockLLMClient(mode="valid")

        import json as _json
        raw = client.call(system, user)
        parsed = _json.loads(raw)
        text = parsed["recommendation"] + " " + parsed["explanation"]

        assert "36" in text

    def test_valid_mode_uses_scenario_months_from_prompt(self):
        system, user = build_prompt(make_input(scenario_months=27))
        client = MockLLMClient(mode="valid")

        import json as _json
        raw = client.call(system, user)
        parsed = _json.loads(raw)
        text = parsed["recommendation"] + " " + parsed["explanation"]

        assert "27" in text

    def test_unknown_mode_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown MockLLMClient mode"):
            MockLLMClient(mode="telepathy")

    def test_valid_mode_delta_zero_hits_else_branch(self):
        """delta_months=0 → else branch in valid-mode explanation construction."""
        import json as _json
        inp = make_input(
            baseline_months=24,
            scenario_months=24,
            delta_months=0,
            monthly_change_amount=300.0,
            adherence_rate=0.8,
        )
        system, user = build_prompt(inp)
        client = MockLLMClient(mode="valid")

        raw = client.call(system, user)
        parsed = _json.loads(raw)

        assert "explanation" in parsed
        assert parsed["explanation"].strip() != ""

    def test_extract_dollar_returns_zero_when_key_absent(self):
        """_extract_dollar fallback: key not in text → '0'."""
        result = MockLLMClient._extract_dollar("no match here", "monthly_change")

        assert result == "0"

    def test_extract_pct_returns_zero_when_key_absent(self):
        """_extract_pct fallback: key not in text → '0'."""
        result = MockLLMClient._extract_pct("no match here", "adherence_rate")

        assert result == "0"


# ---------------------------------------------------------------------------
# generate_explanation
# ---------------------------------------------------------------------------


class TestGenerateExplanation:
    """End-to-end pipeline tests — always returns ValidationResult, never raises."""

    def test_valid_mode_returns_valid_result(self):
        inp = make_input()
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert result.fallback_used is False

    def test_valid_mode_validated_output_is_not_none(self):
        client = MockLLMClient(mode="valid")

        result = generate_explanation(make_input(), client=client)

        assert result.validated_output is not None

    def test_valid_mode_recommendation_is_non_empty(self):
        client = MockLLMClient(mode="valid")

        result = generate_explanation(make_input(), client=client)

        assert result.validated_output.recommendation.strip() != ""

    def test_valid_mode_explanation_non_empty(self):
        client = MockLLMClient(mode="valid")

        result = generate_explanation(make_input(), client=client)

        assert result.validated_output.explanation.strip() != ""

    def test_valid_mode_explanation_sentence_count(self):
        """Rough check: explanation must have between 1 and 4 periods."""
        client = MockLLMClient(mode="valid")

        result = generate_explanation(make_input(), client=client)

        period_count = result.validated_output.explanation.count(".")
        assert 1 <= period_count <= 4, (
            f"Expected 1-4 periods in explanation, got {period_count}: "
            f"{result.validated_output.explanation!r}"
        )

    def test_valid_mode_output_contains_only_input_numbers(self):
        """
        All standalone integers in the AI output must either be in engine
        values or be dollar/percentage amounts.
        """
        import re as _re
        inp = make_input(baseline_months=24, scenario_months=18, delta_months=6)
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        text = (
            result.validated_output.recommendation + " "
            + result.validated_output.explanation
        )
        engine_values = {24, 18, 6}
        numbers = [int(n) for n in _re.findall(r'\b(\d+)\b', text)]
        for num in numbers:
            if 3 <= num <= 500 and num not in engine_values:
                # Must be preceded by $ or followed by %
                pattern = rf'\${num}\b|\b{num}%'
                assert _re.search(pattern, text), (
                    f"Number {num} in AI output is not a valid engine value "
                    f"and is not a dollar/percentage amount. "
                    f"Engine values: {engine_values}. Text: {text!r}"
                )

    def test_hallucination_mode_returns_fallback(self):
        client = MockLLMClient(mode="hallucination")

        result = generate_explanation(make_input(), client=client)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None

    def test_empty_mode_returns_fallback(self):
        client = MockLLMClient(mode="empty")

        result = generate_explanation(make_input(), client=client)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None

    def test_invalid_json_mode_returns_fallback(self):
        """AILayerError from call_llm must be caught — fallback returned."""
        client = MockLLMClient(mode="invalid_json")

        result = generate_explanation(make_input(), client=client)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None

    def test_never_raises_on_valid(self):
        client = MockLLMClient(mode="valid")

        result = generate_explanation(make_input(), client=client)  # must not raise

        assert isinstance(result, ValidationResult)

    def test_never_raises_on_invalid_json(self):
        client = MockLLMClient(mode="invalid_json")

        result = generate_explanation(make_input(), client=client)  # must not raise

        assert isinstance(result, ValidationResult)

    def test_never_raises_on_hallucination(self):
        client = MockLLMClient(mode="hallucination")

        result = generate_explanation(make_input(), client=client)  # must not raise

        assert isinstance(result, ValidationResult)

    def test_never_raises_on_empty(self):
        client = MockLLMClient(mode="empty")

        result = generate_explanation(make_input(), client=client)  # must not raise

        assert isinstance(result, ValidationResult)

    def test_baseline_none_returns_fallback_without_raising(self):
        """ValueError from build_prompt must be caught — fallback returned."""
        inp = make_input(baseline_months=None)
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None

    def test_scenario_months_none_returns_fallback_without_raising(self):
        inp = make_input(scenario_months=None)
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        assert result.valid is False
        assert result.fallback_used is True

    def test_errors_list_non_empty_on_failure(self):
        """On any failure mode, errors must contain at least one message."""
        for mode in ("hallucination", "empty", "invalid_json"):
            client = MockLLMClient(mode=mode)
            result = generate_explanation(make_input(), client=client)
            assert len(result.errors) > 0, f"errors must be non-empty for mode={mode!r}"

    def test_errors_list_empty_on_success(self):
        client = MockLLMClient(mode="valid")

        result = generate_explanation(make_input(), client=client)

        assert result.errors == []

    def test_fallback_output_never_none_on_failure(self):
        """SYSTEM RULE: validated_output must never be None when fallback_used=True."""
        for mode in ("hallucination", "empty", "invalid_json"):
            client = MockLLMClient(mode=mode)
            result = generate_explanation(make_input(), client=client)
            assert result.validated_output is not None, (
                f"validated_output must not be None when fallback_used=True "
                f"(mode={mode!r})"
            )

    def test_expense_cut_behavior_type_works(self):
        inp = make_input(behavior_type="expense_cut")
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        assert result.valid is True

    def test_different_goal_types_all_pass(self):
        for goal_type in ("emergency_fund", "pay_off_debt", "save_for_home", "build_wealth"):
            inp = make_input(goal_type=goal_type)
            client = MockLLMClient(mode="valid")
            result = generate_explanation(inp, client=client)
            assert result.valid is True, f"Failed for goal_type={goal_type!r}"

    def test_adherence_boundary_floor_works(self):
        inp = make_input(adherence_rate=0.1)
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        assert result.valid is True

    def test_adherence_boundary_ceiling_works(self):
        inp = make_input(adherence_rate=0.95)
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        assert result.valid is True

    def test_deterministic_on_repeated_calls(self):
        """Same input → same valid/fallback outcome every time."""
        inp = make_input()
        client = MockLLMClient(mode="valid")

        results = [generate_explanation(inp, client=client) for _ in range(10)]

        valids = {r.valid for r in results}
        assert len(valids) == 1, "generate_explanation must be deterministic"

    def test_delta_zero_valid_pipeline(self):
        """delta_months=0 (no improvement) must still produce a valid result."""
        inp = make_input(
            baseline_months=24,
            scenario_months=24,
            delta_months=0,
            monthly_change_amount=50.0,
            adherence_rate=0.5,
        )
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        assert result.valid is True
        assert result.validated_output is not None
        assert result.validated_output.explanation.strip() != ""


# ---------------------------------------------------------------------------
# Integration test — full pipeline
# ---------------------------------------------------------------------------


class TestIntegration:
    """
    Full pipeline: AIExplanationInput → generate_explanation → ValidationResult.
    These tests exercise the complete data flow without mocking internal steps.
    """

    def test_full_pipeline_valid_mock_passes(self):
        """
        Standard happy path.
        AIExplanationInput with concrete values → valid ValidationResult.
        """
        inp = make_input(
            baseline_months=24,
            scenario_months=18,
            delta_months=6,
            monthly_change_amount=300.0,
            adherence_rate=0.8,
            behavior_type="savings_increase",
            goal_type="emergency_fund",
        )
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        assert result.valid is True
        assert result.fallback_used is False
        assert result.validated_output is not None

    def test_full_pipeline_validated_output_recommendation_not_none(self):
        client = MockLLMClient(mode="valid")

        result = generate_explanation(make_input(), client=client)

        assert result.validated_output.recommendation is not None
        assert len(result.validated_output.recommendation) > 0

    def test_full_pipeline_explanation_references_delta_months(self):
        """
        The validated explanation must reference the actual delta_months value.
        Uses delta=7 (distinctive, unlikely to appear accidentally).
        """
        inp = make_input(
            baseline_months=30,
            scenario_months=23,
            delta_months=7,
        )
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        assert str(inp.delta_months) in result.validated_output.explanation, (
            f"Expected delta_months={inp.delta_months} to appear in explanation: "
            f"{result.validated_output.explanation!r}"
        )

    def test_full_pipeline_hallucination_triggers_fallback(self):
        client = MockLLMClient(mode="hallucination")

        result = generate_explanation(make_input(), client=client)

        assert result.valid is False
        assert result.fallback_used is True
        assert result.validated_output is not None

    def test_full_pipeline_result_is_always_validation_result_type(self):
        for mode in ("valid", "hallucination", "empty", "invalid_json"):
            client = MockLLMClient(mode=mode)
            result = generate_explanation(make_input(), client=client)
            assert isinstance(result, ValidationResult), (
                f"generate_explanation must always return ValidationResult "
                f"(mode={mode!r}, got {type(result).__name__})"
            )

    def test_full_pipeline_valid_output_survives_validation_gateway(self):
        """
        Valid mock output must pass validate_ai_output.
        This confirms the mock and the gateway's hallucination rules are consistent.
        """
        inp = make_input(
            baseline_months=12,
            scenario_months=9,
            delta_months=3,
            monthly_change_amount=200.0,
            adherence_rate=0.6,
        )
        client = MockLLMClient(mode="valid")

        result = generate_explanation(inp, client=client)

        assert result.valid is True, (
            f"Valid mock output failed validation gateway: {result.errors}"
        )
