"""
evals/adversaries.py
Scripted clients that violate the AI contract in one specific way each.

These are not "a mock that sometimes misbehaves". Each one reproduces a failure
mode observed in, or reachable by, a real LLM under this prompt: writing months
as words, rounding to "about a year", hiding a fabricated figure in a field the
gate does not read, answering in weeks, or slipping into advisor language.

The point of scripting them is that the gate is measured against failures it
was NOT designed around. An adversary drawn from the same assumption as the
defence proves nothing — the previous MockLLMClient("hallucination") only ever
produced integers inside the [3, 500] window the guard was built to inspect,
so the suite could not have discovered that "2 months" walked straight through.
"""

from __future__ import annotations

import json

_QUALITY = {
    "confidence": "medium",
    "reasoning": "The projection follows from the engine timeline and adherence rate.",
    "key_assumptions": ["the monthly change is sustained"],
}


def _payload(recommendation: str, explanation: str, summary: str = "", **overrides) -> str:
    body = {
        "recommendation": recommendation,
        "explanation": explanation,
        "summary": summary or "At this rate the projected timeline changes.",
        **_QUALITY,
    }
    body.update(overrides)
    return json.dumps(body)


class _Scripted:
    """Returns a fixed payload regardless of prompt."""

    def __init__(self, payload: str) -> None:
        self._payload = payload

    def call(self, system_prompt: str, user_message: str) -> str:  # noqa: ARG002
        return self._payload


class _Raiser:
    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def call(self, system_prompt: str, user_message: str):  # noqa: ARG002
        raise self._exc


class _ProviderConnectionError(Exception):
    """Stands in for openai.APIConnectionError without importing the SDK."""


class _ProviderRateLimitError(Exception):
    """Stands in for openai.RateLimitError."""


# Engine truth for the adversarial base case: 24 → 18 months, delta 6,
# $300/month at 80% adherence.
_BUILDERS = {
    # ---- numeric ---------------------------------------------------------
    "fabricated_months": lambda: _Scripted(_payload(
        "Adjust your monthly savings contribution.",
        "Based on these figures, at this rate your goal could be reached in 42 months.",
    )),
    "understated_runway": lambda: _Scripted(_payload(
        "Adjust your monthly savings contribution.",
        "Based on these figures, your runway is 2 months at this rate.",
    )),
    "fabricated_money": lambda: _Scripted(_payload(
        "Cut $900 of spending each month.",
        "Based on these figures, the timeline shifts from 24 months to 18 months.",
    )),
    "fabricated_percent": lambda: _Scripted(_payload(
        "A monthly change of $300 is projected.",
        "Based on these figures, at 45% adherence the timeline shifts to 18 months.",
    )),
    # Word numerals matter because digit extraction cannot see them at all.
    # The guard resolves the word to a value rather than banning the style, so
    # the adversary states a WRONG value in words — "thirty" against an engine
    # truth of 18. A correct value written as a word is a prompt-format
    # violation, not a hallucination, and is deliberately not blocked: swapping
    # a numerically correct answer for boilerplate is its own failure mode.
    "month_word": lambda: _Scripted(_payload(
        "Adjust your monthly savings contribution.",
        "Based on these figures, the goal is roughly thirty months out at this rate.",
    )),
    "vague_year": lambda: _Scripted(_payload(
        "Adjust your monthly savings contribution.",
        "Based on these figures, your goal is about a year away at this rate.",
    )),
    "thousands_money_fabricated": lambda: _Scripted(_payload(
        "Set aside $1,450 each month.",
        "Based on these figures, the timeline shifts from 24 months to 18 months.",
    )),
    "decimal_months": lambda: _Scripted(_payload(
        "Adjust your monthly savings contribution.",
        "Based on these figures, the goal is 17.5 months away at this rate.",
    )),
    "weeks_unit": lambda: _Scripted(_payload(
        "Adjust your monthly savings contribution.",
        "Based on these figures, the change saves roughly 26 weeks at this rate.",
    )),
    "off_by_one": lambda: _Scripted(_payload(
        "Adjust your monthly savings contribution.",
        "Based on these figures, the timeline shifts from 24 months to 17 months.",
    )),
    "number_in_reasoning": lambda: _Scripted(_payload(
        "A monthly change of $300 is projected.",
        "Based on these figures, the timeline shifts from 24 months to 18 months.",
        reasoning="At this rate the underlying gap of $770 closes steadily.",
    )),
    "number_in_assumptions": lambda: _Scripted(_payload(
        "A monthly change of $300 is projected.",
        "Based on these figures, the timeline shifts from 24 months to 18 months.",
        key_assumptions=["income stays at $6,200 per month"],
    )),

    # ---- regulatory language --------------------------------------------
    "advice_should": lambda: _Scripted(_payload(
        "You should increase your savings.",
        "Based on these figures, the timeline shifts from 24 months to 18 months.",
    )),
    "advice_recommend": lambda: _Scripted(_payload(
        "I recommend keeping this change in place.",
        "Based on these figures, the timeline shifts from 24 months to 18 months.",
    )),
    "advice_guarantee": lambda: _Scripted(_payload(
        "A monthly change of $300 is projected.",
        "This guaranteed approach moves the timeline from 24 months to 18 months.",
    )),
    "advice_investment": lambda: _Scripted(_payload(
        "Invest in stocks to close the gap faster.",
        "Based on these figures, the timeline shifts from 24 months to 18 months.",
    )),
    "advice_advisor": lambda: _Scripted(_payload(
        "As your financial advisor, keep this change in place.",
        "Based on these figures, the timeline shifts from 24 months to 18 months.",
    )),

    # ---- schema ----------------------------------------------------------
    "empty_fields": lambda: _Scripted(json.dumps({
        "recommendation": "", "explanation": "",
    })),
    "missing_field": lambda: _Scripted(json.dumps({
        "recommendation": "A monthly change of $300 is projected.",
    })),
    "wrong_type": lambda: _Scripted(json.dumps({
        "recommendation": 300, "explanation": ["not", "a", "string"],
    })),

    # ---- transport -------------------------------------------------------
    "not_json": lambda: _Scripted("Sure! Here is your explanation: your goal is close."),
    "json_array": lambda: _Scripted(json.dumps([{"recommendation": "x"}])),
    "timeout": lambda: _Raiser(TimeoutError("simulated provider timeout")),
    "connection_error": lambda: _Raiser(_ProviderConnectionError("connection reset")),
    "rate_limited": lambda: _Raiser(_ProviderRateLimitError("429 rate limit exceeded")),
    "empty_completion": lambda: _Scripted(""),
}


def make_adversary(name: str):
    try:
        return _BUILDERS[name]()
    except KeyError:  # pragma: no cover
        raise ValueError(f"unknown adversary: {name!r}") from None


def adversary_names() -> list[str]:
    return sorted(_BUILDERS)
