"""
tests/ai/test_resilience.py
The "/explain never returns 5xx" guarantee, expressed as tests.

The old code caught only the built-in TimeoutError in call_llm. Every OpenAI
SDK exception (APIConnectionError, RateLimitError, AuthenticationError,
APIStatusError) inherits from openai.OpenAIError, not from TimeoutError — so
each of them travelled through generate_explanation, past a router with no
try/except, into the catch-all handler, and out as a 500. Invisible while the
mock was in place, because the mock raised nothing.
"""

import os

from ai_layer.explain import (
    AILayerError,
    MockLLMClient,
    generate_explanation,
    get_llm_client,
    reset_llm_client,
)
from shared_types.models import AIExplanationInput

import pytest


def make_input(**kw) -> AIExplanationInput:
    base = dict(
        baseline_months=24, scenario_months=18, delta_months=6,
        monthly_change_amount=300.0, adherence_rate=0.8,
        behavior_type="savings_increase", goal_type="emergency_fund",
    )
    base.update(kw)
    return AIExplanationInput(**base)


class _Boom:
    def __init__(self, exc):
        self.exc = exc

    def call(self, system, user):  # noqa: ARG002
        raise self.exc


class _ProviderError(Exception):
    """Any provider exception that is not a TimeoutError."""


def test_provider_exception_becomes_fallback_not_a_crash():
    result = generate_explanation(make_input(), client=_Boom(_ProviderError("connection reset")))

    assert result.valid is False
    assert result.fallback_used is True
    assert result.validated_output is not None


def test_every_exception_type_is_contained():
    for exc in (
        _ProviderError("rate limited"),
        TimeoutError("timeout"),
        ValueError("bad payload"),
        KeyError("missing"),
        RuntimeError("unknown"),
    ):
        result = generate_explanation(make_input(), client=_Boom(exc))
        assert result.fallback_used is True, exc


def test_non_string_response_is_contained():
    class _Weird:
        def call(self, system, user):  # noqa: ARG002
            return {"not": "a string"}

    result = generate_explanation(make_input(), client=_Weird())
    assert result.fallback_used is True


def test_json_array_response_is_contained():
    class _Array:
        def call(self, system, user):  # noqa: ARG002
            return "[1, 2, 3]"

    result = generate_explanation(make_input(), client=_Array())
    assert result.fallback_used is True


def test_call_llm_wraps_provider_errors_in_ai_layer_error():
    from ai_layer.explain import build_prompt, call_llm

    system, user = build_prompt(make_input())
    with pytest.raises(AILayerError):
        call_llm(system, user, client=_Boom(_ProviderError("boom")))


# ---------------------------------------------------------------------------
# Client resolution
# ---------------------------------------------------------------------------


def test_missing_api_key_resolves_to_mock_instead_of_raising():
    """A missing Railway variable must not be able to take the process down."""
    reset_llm_client()
    previous = os.environ.pop("OPENAI_API_KEY", None)
    try:
        client = get_llm_client()
        assert isinstance(client, MockLLMClient)
    finally:
        if previous is not None:
            os.environ["OPENAI_API_KEY"] = previous
        reset_llm_client()


def test_force_mock_pins_the_mock_even_with_a_key():
    """CI and the eval suite must stay free and offline regardless of env."""
    reset_llm_client()
    os.environ["FINSIGHT_FORCE_MOCK"] = "1"
    os.environ["OPENAI_API_KEY"] = "sk-not-a-real-key"
    try:
        assert isinstance(get_llm_client(), MockLLMClient)
    finally:
        os.environ.pop("FINSIGHT_FORCE_MOCK", None)
        os.environ.pop("OPENAI_API_KEY", None)
        reset_llm_client()


def test_broken_client_construction_falls_back_to_mock():
    """openai missing from the image, malformed key: still serves answers."""
    reset_llm_client()
    os.environ["OPENAI_API_KEY"] = "sk-not-a-real-key"
    os.environ.pop("FINSIGHT_FORCE_MOCK", None)
    try:
        client = get_llm_client()
        # Without the openai package installed this degrades to the mock; with
        # it installed the client constructs fine. Either way, no exception.
        assert client is not None
    finally:
        os.environ.pop("OPENAI_API_KEY", None)
        reset_llm_client()
