"""
validation_gateway/scorer.py
Quality scoring layer — sits AFTER validate_ai_output(), before the UI.

Scores are advisory: the UI renders with a quality badge.
status="fallback" forces the deterministic fallback template to be used.

CALIBRATION
-----------
Every dimension here must correspond to something the system prompt actually
asks the model to produce. When it does not, the scorer measures the prompt's
omissions rather than the model's quality: before the prompt was extended to
six fields, key_assumptions and reasoning were always empty, every response
lost 30 points, and no answer could ever be "approved". A scorer that cannot
return its own top grade is not scoring anything.

The consistency dimension delegates to numeric_guard, so scorer and validator
apply one definition of "this number came from the engine". It previously
compared against delta_months alone, which penalised the model for correctly
naming baseline_months — the better the answer followed the prompt, the more
likely it was to be discarded.
"""

from typing import Literal

from pydantic import BaseModel

from shared_types.models import (
    AIExplanationOutput,
    BaselineResult,
    ScenarioResult,
    ValidationResult,
)
from validation_gateway.language_guard import find_advisory
from validation_gateway.numeric_guard import build_allowed, find_unverified


class AIQualityScore(BaseModel):
    total: float           # 0.0–100.0
    grounding: float       # 0–40
    consistency: float     # 0–30
    completeness: float    # 0–20
    behavioral_fit: float  # 0–10
    status: Literal["approved", "degraded", "fallback"]
    reasons: list[str]


def score_ai_output(
    validation: ValidationResult,
    ai_output: AIExplanationOutput,
    scenario: ScenarioResult,
    baseline: BaselineResult,
) -> AIQualityScore:
    """
    Score AI output quality across four dimensions.

    Pure function — no side effects, no DB, no logging.
    """
    reasons: list[str] = []

    confidence = ai_output.confidence
    key_assumptions = ai_output.key_assumptions
    summary = ai_output.summary if ai_output.summary else ai_output.recommendation
    reasoning = ai_output.reasoning

    # ── grounding (0–40) ────────────────────────────────────────────────────
    grounding = 40.0

    if confidence == "low":
        grounding -= 20
        reasons.append("confidence is low (-20 grounding)")

    if not key_assumptions:
        grounding -= 10
        reasons.append("key_assumptions empty (-10 grounding)")

    if len(summary) < 20:
        grounding -= 10
        reasons.append("summary < 20 chars (-10 grounding)")

    # ── consistency (0–30) ──────────────────────────────────────────────────
    consistency = 30.0

    if not validation.valid:
        consistency -= 15
        reasons.append("validation failed (-15 consistency)")

    allowed = build_allowed(baseline, scenario)
    unverified = find_unverified(summary, allowed)
    if unverified:
        consistency -= 15
        first = unverified[0]
        reasons.append(
            f"summary contains {first.text!r}, which is not an engine value "
            f"(months={sorted(allowed.months)}, money={list(allowed.money)}, "
            f"percent={list(allowed.percent)}) (-15 consistency)"
        )

    consistency = max(consistency, 0.0)

    # ── completeness (0–20) ─────────────────────────────────────────────────
    completeness = 20.0

    if not reasoning or len(reasoning.strip()) < 10:
        completeness -= 10
        reasons.append("reasoning empty or < 10 chars (-10 completeness)")

    if not key_assumptions:
        completeness -= 10
        reasons.append("key_assumptions empty (-10 completeness)")

    # ── behavioral_fit (0–10) ───────────────────────────────────────────────
    behavioral_fit = 10.0

    if scenario.adherence_rate < 0.3 and confidence == "high":
        behavioral_fit -= 5
        reasons.append("overconfident at low adherence rate (-5 behavioral_fit)")

    if not scenario.is_improvement and confidence == "high":
        behavioral_fit -= 5
        reasons.append("high confidence despite no improvement (-5 behavioral_fit)")

    # Soft directive phrasing. The blocking tier lives in the validator; this
    # tier is scored so that style drift is visible without inflating fallbacks.
    advisory = find_advisory(f"{ai_output.recommendation} {ai_output.explanation}")
    if advisory and behavioral_fit > 0:
        behavioral_fit -= 5
        reasons.append(f"{advisory[0]} (-5 behavioral_fit)")

    behavioral_fit = max(behavioral_fit, 0.0)

    # ── total + status ───────────────────────────────────────────────────────
    total = grounding + consistency + completeness + behavioral_fit

    if total >= 80:
        status: Literal["approved", "degraded", "fallback"] = "approved"
    elif total >= 60:
        status = "degraded"
    else:
        status = "fallback"

    return AIQualityScore(
        total=total,
        grounding=grounding,
        consistency=consistency,
        completeness=completeness,
        behavioral_fit=behavioral_fit,
        status=status,
        reasons=reasons,
    )
