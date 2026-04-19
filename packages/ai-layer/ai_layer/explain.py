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
2. You MUST NOT use phrases like "you should", "I recommend",
   "consider", or "advisor". You are not a financial advisor.
3. You MUST NOT express certainty. Use: "based on these figures",
   "at this rate", "if this change is maintained".
4. Your explanation must be 2-3 sentences maximum.
5. You MUST reference only: baseline_months, scenario_months,
   delta_months, monthly_change_amount, adherence_rate from the input.

OUTPUT FORMAT (JSON only — no prose outside JSON):
{
  "recommendation": "one-line action summary",
  "explanation": "2-3 sentence explanation using only input numbers"
}"""


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
        else:
            explanation = (
                f"Based on these figures, this change may affect your timeline. "
                f"At this rate, the projected scenario is {scenario} months. "
                f"If this change is maintained, your progress may remain steady."
            )

        return json.dumps({"recommendation": rec, "explanation": explanation})

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
# Module-level client — # SWAP THIS when real API key is available
# ---------------------------------------------------------------------------

_llm_client = MockLLMClient(mode="valid")  # SWAP THIS


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
                       Defaults to the module-level _llm_client (# SWAP THIS).

    Returns:
        Parsed dict from the LLM response.

    Raises:
        AILayerError: On JSON parse failure or LLM transport error (timeout, etc.).
    """
    _client = client if client is not None else _llm_client  # SWAP THIS

    try:
        raw_str = _client.call(system_prompt, user_message)
    except TimeoutError as exc:
        raise AILayerError(f"LLM request timed out: {exc}") from exc

    try:
        return json.loads(raw_str)
    except json.JSONDecodeError as exc:
        raise AILayerError(
            f"LLM returned non-JSON response: {raw_str[:120]!r}"
        ) from exc


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
    proxy_baseline = BaselineResult(
        monthly_cashflow=0.0,
        savings_rate=0.0,
        time_to_goal_months=input.baseline_months,
        monthly_savings_gap=0.0,
        goal_already_met=False,
    )
    proxy_scenario = ScenarioResult(
        baseline_months=input.baseline_months,
        scenario_months=input.scenario_months,
        delta_months=input.delta_months,
        adherence_rate=max(0.1, min(0.95, input.adherence_rate)),
        effective_monthly_change=max(0.0, input.monthly_change_amount),
        scenario_monthly_cashflow=0.0,
        is_improvement=(
            input.delta_months is not None and input.delta_months > 0
        ),
    )

    result = validate_ai_output(raw, proxy_baseline, proxy_scenario)

    if not result.valid:
        logger.error(
            "validate_ai_output rejected AI output (fallback in use): %s",
            result.errors,
        )

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fallback_result(reason: str) -> ValidationResult:
    """Return a ValidationResult with the deterministic fallback template."""
    from validation_gateway.validator import _fallback_output  # local import avoids circular
    return ValidationResult(
        valid=False,
        errors=[reason],
        fallback_used=True,
        validated_output=_fallback_output(),
    )
