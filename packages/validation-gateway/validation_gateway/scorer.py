"""
validation_gateway/scorer.py
Quality scoring layer — sits AFTER validate_ai_output(), before the UI.

Scores are advisory: the UI renders with a quality badge.
status="fallback" forces the deterministic fallback template to be used.
"""

import re
from typing import Literal

from pydantic import BaseModel

from shared_types.models import (
    AIExplanationOutput,
    BaselineResult,
    ScenarioResult,
    ValidationResult,
)


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
    baseline: BaselineResult,  # noqa: ARG001 — reserved for future grounding checks
) -> AIQualityScore:
    """
    Score AI output quality across four dimensions.

    Pure function — no side effects, no DB, no logging.
    """
    reasons: list[str] = []

    # Resolve optional quality fields, falling back to primary fields
    confidence = ai_output.confidence
    key_assumptions = ai_output.key_assumptions
    summary = ai_output.summary if ai_output.summary else ai_output.recommendation
    reasoning = ai_output.reasoning  # use quality field directly; empty triggers deduction

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

    if scenario.delta_months is not None:
        month_nums = [int(n) for n in re.findall(r"\b(\d+)\b", summary)]
        for num in month_nums:
            if 3 <= num <= 500 and abs(num - scenario.delta_months) > 1:
                # Exclude dollar amounts and percentages (same heuristic as hallucination check)
                if not re.search(rf"\${num}\b|\b{num}%", summary):
                    consistency -= 15
                    reasons.append(
                        f"summary contains {num} but delta_months={scenario.delta_months} "
                        f"(expected ±1) (-15 consistency)"
                    )
                    break

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
