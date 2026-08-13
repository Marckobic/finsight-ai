"""
tests/ai/test_llm_client.py
Transport behaviour: deadline, retry, truncation, degradation.

This is the layer that decides whether a slow or broken provider becomes a
deterministic template or a 500 on the user's screen, so it is tested directly
rather than through the pipeline. A fake transport is injected — no openai
package, no key, no network — which keeps the suite free and offline while
still exercising the real retry and deadline logic.
"""

import pytest

from ai_layer.llm_client import DEFAULT_MODEL, LLMResult, LLMUnavailable, OpenAIClient

PROMPT = "Return JSON only."
USER = 'Financial scenario data: {"baseline_months": 24}'


class _Choice:
    def __init__(self, content, finish_reason="stop"):
        self.message = type("M", (), {"content": content})()
        self.finish_reason = finish_reason


class _Usage:
    prompt_tokens = 120
    completion_tokens = 40


class _Response:
    def __init__(self, content, finish_reason="stop", usage=True):
        self.choices = [_Choice(content, finish_reason)]
        self.usage = _Usage() if usage else None


class _Transport:
    """Stands in for openai.OpenAI. Replays a scripted sequence of outcomes."""

    def __init__(self, *outcomes):
        self._outcomes = list(outcomes)
        self.calls = []
        completions = type("C", (), {"create": self._create})()
        self.chat = type("Chat", (), {"completions": completions})()

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self._outcomes.pop(0) if self._outcomes else self._outcomes
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _client(*outcomes, **kw):
    return OpenAIClient(transport=_Transport(*outcomes), **kw)


class _Transient(Exception):
    pass


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_missing_key_raises_llm_unavailable_not_key_error():
    """Never a bare KeyError: that is what took the FastAPI app down on import."""
    with pytest.raises(LLMUnavailable, match="OPENAI_API_KEY"):
        OpenAIClient(api_key="")


def test_defaults_come_from_the_shared_sla():
    from shared_types.sla import SLA_MS

    client = _client()
    assert client.model == DEFAULT_MODEL
    assert client.deadline_ms < SLA_MS["/explain"]
    assert client.attempt_timeout_ms <= client.deadline_ms


# ---------------------------------------------------------------------------
# Prompt contract
# ---------------------------------------------------------------------------


def test_prompt_without_the_word_json_is_rejected_before_spending_a_call():
    """response_format=json_object 400s without it — cheaper to catch here."""
    client = _client(_Response('{"ok": 1}'))
    with pytest.raises(LLMUnavailable, match="json"):
        client.call("You explain finances.", "no magic word here")
    assert client._client.calls == []


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_successful_call_returns_text_and_telemetry():
    client = _client(_Response('{"recommendation": "x"}'))
    result = client.call(PROMPT, USER)

    assert isinstance(result, LLMResult)
    assert result.text == '{"recommendation": "x"}'
    assert result.attempts == 1
    assert result.prompt_tokens == 120
    assert result.completion_tokens == 40
    assert result.latency_ms >= 0
    assert str(result) == result.text          # explain.py treats it as a string
    assert "latency_ms" in result.as_event_payload()


def test_request_parameters_are_pinned():
    """temperature=0 keeps evals measuring the model, not sampling noise."""
    client = _client(_Response('{"ok": 1}'))
    client.call(PROMPT, USER)
    sent = client._client.calls[0]

    assert sent["temperature"] == 0.0
    assert sent["response_format"] == {"type": "json_object"}
    assert sent["max_tokens"] == client.max_tokens
    assert sent["timeout"] <= client.attempt_timeout_ms / 1000
    assert [m["role"] for m in sent["messages"]] == ["system", "user"]


def test_missing_usage_object_does_not_break_the_result():
    client = _client(_Response('{"ok": 1}', usage=False))
    assert client.call(PROMPT, USER).prompt_tokens == 0


# ---------------------------------------------------------------------------
# Degradation
# ---------------------------------------------------------------------------


def test_truncated_completion_is_refused():
    """A cut-off JSON fragment cannot pass the gate; fail cleanly instead."""
    client = _client(_Response('{"recommendation": "x', finish_reason="length"))
    with pytest.raises(LLMUnavailable, match="truncated"):
        client.call(PROMPT, USER)


def test_empty_completion_is_refused():
    client = _client(_Response("   "), max_attempts=1)
    with pytest.raises(LLMUnavailable, match="empty"):
        client.call(PROMPT, USER)


def test_non_transient_error_does_not_retry():
    client = _client(ValueError("bad request"), _Response('{"ok": 1}'))
    with pytest.raises(LLMUnavailable):
        client.call(PROMPT, USER)
    assert len(client._client.calls) == 1


def test_transient_error_retries_within_budget():
    client = _client(_Transient("connection reset"), _Response('{"ok": 1}'))
    client._is_transient = lambda exc: True

    result = client.call(PROMPT, USER)

    assert result.attempts == 2
    assert len(client._client.calls) == 2


def test_transient_error_gives_up_at_max_attempts():
    client = _client(_Transient("a"), _Transient("b"), max_attempts=2)
    client._is_transient = lambda exc: True

    with pytest.raises(LLMUnavailable, match="2 attempt"):
        client.call(PROMPT, USER)


def test_exhausted_deadline_does_not_start_a_call():
    """The point of a deadline: no request that cannot finish inside the SLA."""
    client = _client(_Response('{"ok": 1}'), deadline_ms=1)
    with pytest.raises(LLMUnavailable):
        client.call(PROMPT, USER)
    assert client._client.calls == []


def test_retry_is_skipped_when_the_deadline_leaves_no_room():
    client = _client(_Transient("a"), _Response('{"ok": 1}'), deadline_ms=250)
    client._is_transient = lambda exc: True

    with pytest.raises(LLMUnavailable):
        client.call(PROMPT, USER)
    assert len(client._client.calls) == 1


def test_is_transient_is_false_without_the_openai_module():
    assert _client()._is_transient(ValueError("x")) is False


# ---------------------------------------------------------------------------
# Integration with the AI layer
# ---------------------------------------------------------------------------


def test_explain_layer_accepts_an_llm_result_object():
    """call_llm reads .text, so a rich result works wherever a string did."""
    from ai_layer.explain import build_prompt, call_llm
    from shared_types.models import AIExplanationInput

    class _Wrapper:
        def call(self, system, user):  # noqa: ARG002
            return LLMResult(
                text='{"recommendation": "A monthly change of $300 is projected.",'
                     ' "explanation": "Based on these figures, the timeline shifts'
                     ' from 24 months to 18 months."}',
                model="test", latency_ms=12, attempts=1,
                prompt_tokens=1, completion_tokens=1,
            )

    system, user = build_prompt(AIExplanationInput(
        baseline_months=24, scenario_months=18, delta_months=6,
        monthly_change_amount=300.0, adherence_rate=0.8,
        behavior_type="savings_increase", goal_type="emergency_fund",
    ))
    parsed = call_llm(system, user, client=_Wrapper())
    assert parsed["recommendation"].startswith("A monthly change")
