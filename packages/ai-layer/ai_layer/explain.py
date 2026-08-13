"""
ai_layer/explain.py
AI Explanation Layer — structured prompt construction, LLM orchestration,
and validation gateway integration.

SYSTEM RULES:
  - AI layer is NOT a financial engine.
  - It fires ONLY after the scenario engine produces output.
  - It NEVER initiates. It ONLY responds to structured engine data.
  - It NEVER generates numbers. It MAY ONLY reference numbers
    received in the structured input JSON.

Data flow:
  AIExplanationInput → build_prompt → call_llm → validate_ai_output
                                                       ↓
                                               ValidationResult → UI

Failure behavior:
  - Any step fails → log error, return ValidationResult with fallback.
  - generate_explanation() NEVER raises. It always returns ValidationResult.

Real LLM integration:
  - Production client goes in ai_layer/llm_client.py (NOT here).
  - explain.py knows only the interface (.call(system, user) → str).
  - Search for # SWAP THIS to find the one-line swap point.
"""

import json
import logging
import os
import re
from typing import Any

from shared_types.models import (
    AIExplanationInput,
    BaselineResult,
    ScenarioResult,
    ValidationResult,
)
from validation_gateway.validator import validate_ai_output

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AILayerError(Exception):
    """Raised when the AI layer encounters an unrecoverable error.

    Covers: JSON parse failure, LLM timeout, transport errors.
    generate_explanation() catches this and returns a fallback ValidationResult.
    """


# ---------------------------------------------------------------------------
# System prompt (immutable — never modified by user data)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a financial explanation engine for FinSight.ai.

YOUR ONLY JOB: explain what the numbers mean in plain language.

STRICT RULES — violation causes your output to be rejected:
1. You MUST NOT generate any number not present in the input JSON.
   Every figure you write is checked against the engine output before
   it reaches the user. An unverifiable number discards your whole answer.
2. You MUST NOT use phrases like "you should", "I recommend",
   "consider", or "advisor". You are not a financial advisor.
3. You MUST NOT express certainty. Use: "based on these figures",
   "at this rate", "if this change is maintained".
4. Your explanation must be 2-3 sentences maximum.
5. You MUST reference only: baseline_months, scenario_months,
   delta_months, monthly_change, adherence_rate from the input.
6. You MUST write numbers as digits ("18 months", never "eighteen months")
   and MUST NOT round or approximate them ("about a year" is rejected).

OUTPUT FORMAT — return JSON only, no prose outside the JSON object:
{
  "recommendation": "one-line action summary",
  "explanation": "2-3 sentence explanation using only input numbers",
  "summary": "one sentence naming the timeline change, 20 characters or more",
  "confidence": "high" | "medium" | "low",
  "reasoning": "one sentence on why this projection follows from the figures",
  "key_assumptions": ["short assumption", "short assumption"]
}

All six fields are required. Rules 1-3 apply to every one of them."""


# ---------------------------------------------------------------------------
# Mock LLM client (deterministic — no network calls)
# ---------------------------------------------------------------------------


class MockLLMClient:
    """
    Deterministic mock for testing. No network calls.

    Simulates 4 behaviours via the ``mode`` parameter:
      "valid"         → returns correct output using only input numbers
      "hallucination" → invents a number not present in input (triggers rejection)
      "empty"         → returns empty strings (triggers rejection)
      "invalid_json"  → returns malformed JSON (triggers AILayerError)

    Interface matches the real LLM client: a single ``.call(system, user)``
    method that returns a raw string. Swap with one line — see # SWAP THIS.
    """

    def __init__(self, mode: str = "valid") -> None:
        if mode not in ("valid", "hallucination", "empty", "invalid_json"):
            raise ValueError(
                f"Unknown MockLLMClient mode: {mode!r}. "
                "Must be one of: valid, hallucination, empty, invalid_json."
            )
        self.mode = mode

    def call(self, system_prompt: str, user_message: str) -> str:  # noqa: ARG002
        """Return a raw JSON string simulating the LLM response."""
        if self.mode == "invalid_json":
            return "not valid json {"

        if self.mode == "empty":
            return json.dumps({"recommendation": "", "explanation": ""})

        # Quality fields the scorer measures. Kept free of numbers so the mock
        # exercises the happy path rather than the numeric guard.
        _quality = {
            "confidence": "medium",
            "reasoning": (
                "The projection follows directly from the engine timeline and the "
                "adherence rate supplied in the input."
            ),
            "key_assumptions": [
                "the monthly change is sustained",
                "income and fixed expenses stay level",
            ],
        }

        # Extract engine numbers from the formatted user message
        baseline = self._extract_int(user_message, "baseline_months")
        scenario = self._extract_int(user_message, "scenario_months")
        delta = self._extract_int(user_message, "delta_months")
        monthly = self._extract_dollar(user_message, "monthly_change")
        adherence = self._extract_pct(user_message, "adherence_rate")

        if self.mode == "hallucination":
            # Pick the smallest integer in [3, 500] not present in engine outputs.
            # This guarantees the validation gateway will flag it as hallucinated.
            engine_vals = {v for v in (baseline, scenario, delta) if v is not None}
            fake = next(n for n in range(3, 501) if n not in engine_vals)
            return json.dumps({
                "recommendation": "Adjust your monthly savings contribution.",
                "explanation": (
                    f"Based on these figures, at this rate your goal could be "
                    f"reached in {fake} months if this change is maintained."
                ),
                "summary": "The projected timeline changes under this scenario.",
                **_quality,
            })

        # mode == "valid" — use only numbers extracted from the input
        rec = (
            f"A ${monthly} monthly change at {adherence}% adherence is projected."
        )

        if delta is not None and delta > 0:
            explanation = (
                f"Based on these figures, this change is projected to affect "
                f"your timeline. "
                f"At this rate, the timeline shifts from {baseline} months to "
                f"{scenario} months, a reduction of {delta} months. "
                f"If this change is maintained, progress toward your goal "
                f"may accelerate."
            )
            summary = (
                f"At this rate the timeline shifts from {baseline} months "
                f"to {scenario} months."
            )
        else:
            explanation = (
                f"Based on these figures, this change may affect your timeline. "
                f"At this rate, the projected scenario is {scenario} months. "
                f"If this change is maintained, your progress may remain steady."
            )
            summary = f"At this rate the projected timeline is {scenario} months."

        return json.dumps({
            "recommendation": rec,
            "explanation": explanation,
            "summary": summary,
            **_quality,
        })

    # ------------------------------------------------------------------
    # Private helpers — parse numbers from the formatted user message
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_int(text: str, key: str) -> int | None:
        m = re.search(rf'"{key}":\s*(\d+)', text)
        return int(m.group(1)) if m else None

    @staticmethod
    def _extract_dollar(text: str, key: str) -> str:
        m = re.search(rf'"{key}":\s*\$([0-9.]+)', text)
        if not m:
            return "0"
        # Strip trailing zeros for clean display ($300.00 → "300")
        return f"{float(m.group(1)):g}"

    @staticmethod
    def _extract_pct(text: str, key: str) -> str:
        m = re.search(rf'"{key}":\s*([0-9.]+)%', text)
        if not m:
            return "0"
        return f"{float(m.group(1)):g}"


# ---------------------------------------------------------------------------
# Client resolution
# ---------------------------------------------------------------------------
#
# There is no swap point any more. The client is resolved lazily on first use:
#
#   OPENAI_API_KEY set  → real client (ai_layer.llm_client.OpenAIClient)
#   otherwise           → MockLLMClient("valid")
#
# Resolution is lazy and never raises, so a missing or malformed key degrades
# to deterministic explanations instead of taking the process down at import
# time. FINSIGHT_FORCE_MOCK=1 pins the mock even when a key is present, which
# is what CI and the eval suite use to stay free and offline.

_resolved_client: Any | None = None
_client_resolved = False


def get_llm_client() -> Any:
    """Return the active LLM client. Never raises; falls back to the mock."""
    global _resolved_client, _client_resolved
    if _client_resolved:
        return _resolved_client

    _client_resolved = True

    if os.environ.get("FINSIGHT_FORCE_MOCK", "").strip() in ("1", "true", "True"):
        logger.info("FINSIGHT_FORCE_MOCK set — using MockLLMClient")
        _resolved_client = MockLLMClient(mode="valid")
        return _resolved_client

    has_key = bool(
        os.environ.get("FINSIGHT_LLM_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
    )
    if not has_key:
        logger.warning(
            "no LLM API key set — /explain will serve deterministic mock output"
        )
        _resolved_client = MockLLMClient(mode="valid")
        return _resolved_client

    try:
        from ai_layer.llm_client import OpenAIClient
        _resolved_client = OpenAIClient()
        logger.info(
            "LLM client active: model=%s base_url=%s",
            _resolved_client.model, _resolved_client.base_url or "openai default",
        )
    except Exception as exc:  # noqa: BLE001 — must not break process startup
        logger.error("failed to construct LLM client (%s) — falling back to mock", exc)
        _resolved_client = MockLLMClient(mode="valid")

    return _resolved_client


def reset_llm_client() -> None:
    """Clear the cached client. Tests use this after changing the environment."""
    global _resolved_client, _client_resolved
    _resolved_client = None
    _client_resolved = False


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def build_prompt(input: AIExplanationInput) -> tuple[str, str]:
    """
    Construct the (system_prompt, user_message) pair for the LLM.

    Pure string construction — no LLM call, no side effects.

    Args:
        input: Structured engine data to translate into a prompt.

    Returns:
        (system_prompt, user_message) tuple.

    Raises:
        ValueError: If baseline_months or scenario_months is None.
                    Both must be present for a meaningful explanation.
    """
    if input.baseline_months is None:
        raise ValueError(
            "baseline_months must not be None — AI explanation requires a "
            "reachable baseline timeline."
        )
    if input.scenario_months is None:
        raise ValueError(
            "scenario_months must not be None — AI explanation requires a "
            "reachable scenario timeline."
        )

    adherence_pct = f"{input.adherence_rate * 100:g}"
    monthly_fmt = f"{input.monthly_change_amount:g}"

    user_message = (
        f'Financial scenario data:\n'
        f'{{\n'
        f'  "baseline_months": {input.baseline_months},\n'
        f'  "scenario_months": {input.scenario_months},\n'
        f'  "delta_months": {input.delta_months},\n'
        f'  "monthly_change": ${monthly_fmt},\n'
        f'  "adherence_rate": {adherence_pct}%,\n'
        f'  "action_type": "{input.behavior_type}",\n'
        f'  "goal_type": "{input.goal_type}"\n'
        f'}}\n'
        f'\n'
        f'Explain what this means for the user. Follow all rules above.'
    )

    return _SYSTEM_PROMPT, user_message


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def call_llm(
    system_prompt: str,
    user_message: str,
    client: Any | None = None,
) -> dict:
    """
    Call the LLM and return the parsed JSON response as a dict.

    Args:
        system_prompt: Immutable system instruction string.
        user_message:  User turn populated from AIExplanationInput.
        client:        LLM client with .call(system, user) → str interface.
                       Defaults to the lazily resolved client.

    Returns:
        Parsed dict from the LLM response.

    Raises:
        AILayerError: On JSON parse failure or ANY transport error.

    Every transport exception is funnelled into AILayerError. Catching only
    TimeoutError here used to leak provider exceptions (APIConnectionError,
    RateLimitError, AuthenticationError) past generate_explanation and out of
    the endpoint as a 500 — which is exactly what the "/explain never returns
    5xx" guarantee promises cannot happen.
    """
    _client = client if client is not None else get_llm_client()

    try:
        raw_str = _client.call(system_prompt, user_message)
    except Exception as exc:  # noqa: BLE001 — deliberate funnel, see docstring
        name = type(exc).__name__
        if isinstance(exc, TimeoutError) or "Timeout" in name:
            raise AILayerError(f"LLM request timed out: {exc}") from exc
        raise AILayerError(f"LLM transport error: {name}: {exc}") from exc

    # Real clients may return a rich result object rather than a bare string.
    raw_str = getattr(raw_str, "text", raw_str)

    if not isinstance(raw_str, str):
        raise AILayerError(f"LLM returned {type(raw_str).__name__}, expected str")

    try:
        parsed = json.loads(raw_str)
    except json.JSONDecodeError as exc:
        raise AILayerError(
            f"LLM returned non-JSON response: {raw_str[:120]!r}"
        ) from exc

    if not isinstance(parsed, dict):
        raise AILayerError(
            f"LLM returned JSON {type(parsed).__name__}, expected an object"
        )

    return parsed


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def generate_explanation(
    input: AIExplanationInput,
    client: Any | None = None,
) -> ValidationResult:
    """
    Full pipeline: structured input → LLM → validated output.

    Never raises. Always returns a ValidationResult — either with the
    verified AI output or with the deterministic fallback template.

    Pipeline steps:
      1. build_prompt(input)            — pure string construction
      2. call_llm(system, user)         — LLM call, returns raw dict
      3. validate_ai_output(raw, ...)   — hard validation gate
      4. Return ValidationResult        — valid or fallback, never None

    Args:
        input:  Structured engine data (AIExplanationInput).
        client: Optional LLM client override for testing.

    Returns:
        ValidationResult. valid=True means the AI output passed all checks.
        valid=False means fallback_used=True and validated_output is the
        deterministic fallback template.
    """
    # Step 1: Build prompt
    try:
        system_prompt, user_message = build_prompt(input)
    except ValueError as exc:
        logger.error("build_prompt failed: %s", exc)
        return _fallback_result(str(exc))

    # Step 2: Call LLM
    try:
        raw = call_llm(system_prompt, user_message, client=client)
    except AILayerError as exc:
        logger.error("call_llm failed: %s", exc)
        return _fallback_result(str(exc))

    # Step 3 + 4: Validate through the hard safety gate
    # Construct proxy objects so the validation gateway can check numeric
    # consistency against the source-of-truth engine values.
    proxy_baseline = build_proxy_baseline(input)
    proxy_scenario = build_proxy_scenario(input)

    try:
        result = validate_ai_output(raw, proxy_baseline, proxy_scenario)
    except Exception as exc:  # noqa: BLE001 — the gate must not be able to crash /explain
        logger.exception("validate_ai_output raised unexpectedly")
        return _fallback_result(f"validation gateway error: {exc}")

    if not result.valid:
        logger.error(
            "validate_ai_output rejected AI output (fallback in use): %s",
            result.errors,
        )

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def build_proxy_scenario(input: AIExplanationInput) -> ScenarioResult:
    """Rebuild the engine-truth view the gate and the scorer both check against.

    Single source of truth for this projection: it used to be duplicated in
    explain.py and in the /explain router, and both copies clamped adherence
    into [0.1, 0.95]. That made the gate verify a number the user was never
    shown — a request with adherence 0.05 renders "5%" but was checked against
    10%. No clamping here: the checks compare against what actually happened.
    """
    return ScenarioResult(
        baseline_months=input.baseline_months,
        scenario_months=input.scenario_months,
        delta_months=input.delta_months,
        adherence_rate=input.adherence_rate,
        effective_monthly_change=input.monthly_change_amount,
        scenario_monthly_cashflow=0.0,
        is_improvement=(
            input.delta_months is not None and input.delta_months > 0
        ),
    )


def build_proxy_baseline(input: AIExplanationInput) -> BaselineResult:
    """Engine-truth baseline view used by the gate and the scorer."""
    return BaselineResult(
        monthly_cashflow=0.0,
        savings_rate=0.0,
        time_to_goal_months=input.baseline_months,
        monthly_savings_gap=0.0,
        goal_already_met=False,
    )


def _fallback_result(reason: str) -> ValidationResult:
    """Return a ValidationResult with the deterministic fallback template."""
    from validation_gateway.validator import _fallback_output  # local import avoids circular
    return ValidationResult(
        valid=False,
        errors=[reason],
        fallback_used=True,
        validated_output=_fallback_output(),
    )
