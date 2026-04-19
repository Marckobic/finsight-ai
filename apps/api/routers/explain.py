"""
apps/api/routers/explain.py
POST /explain — AI explanation generation with hard validation gate + quality scoring.

Pipeline:
  1. generate_explanation()     — AI layer (never raises; returns ValidationResult)
  2. score_ai_output()          — quality scoring (pure function)
  3. health_tracker.record()    — in-memory health metrics
  4. If score.status=="fallback" → use deterministic fallback
  5. Return ExplainResponse with quality field

SYSTEM RULE: This endpoint NEVER returns 5xx.
SLA: < 3000 ms (mock is synchronous; real LLM will be async in Phase 2).
"""

import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ai_layer.explain import generate_explanation
from shared_types.models import (
    AIExplanationInput,
    AIExplanationOutput,
    BaselineResult,
    ScenarioResult,
)
from validation_gateway.validator import _fallback_output
from validation_gateway.scorer import AIQualityScore, score_ai_output
from validation_gateway.health import health_tracker

from apps.api.events import log_event

router = APIRouter()


class ExplainValidation(BaseModel):
    valid: bool
    fallback_used: bool
    errors: list[str]


class ExplainResponse(BaseModel):
    status: str
    data: AIExplanationOutput
    validation: ExplainValidation
    quality: Optional[AIQualityScore] = None
    latency_ms: float


@router.post("/explain", response_model=ExplainResponse)
async def explain_endpoint(input: AIExplanationInput) -> ExplainResponse:
    """
    Generate a plain-language explanation of a financial scenario.

    Always returns 200 — if the AI layer fails or produces invalid output,
    the deterministic fallback template is returned with status="fallback".
    Quality score is always included; if score.status=="fallback", the
    deterministic fallback replaces any AI-generated output.
    """
    t0 = time.perf_counter()

    # Step 1: Full AI pipeline — guaranteed to return ValidationResult
    validation_result = generate_explanation(input)
    output: AIExplanationOutput = validation_result.validated_output
    status = "fallback" if validation_result.fallback_used else "ok"

    # Step 2: Reconstruct proxy objects for the quality scorer
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
        is_improvement=(input.delta_months is not None and input.delta_months > 0),
    )

    score = score_ai_output(validation_result, output, proxy_scenario, proxy_baseline)
    health_tracker.record(score)

    # Step 3: Override with fallback if quality gate fails
    if score.status == "fallback":
        output = _fallback_output()
        status = "fallback"

    # Step 4: Structured event log
    log_event(
        "AI_EXPLANATION_GENERATED",
        {
            "valid": validation_result.valid,
            "fallback_used": validation_result.fallback_used,
            "quality_status": score.status,
            "quality_total": score.total,
        },
    )

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return ExplainResponse(
        status=status,
        data=output,
        validation=ExplainValidation(
            valid=validation_result.valid,
            fallback_used=validation_result.fallback_used,
            errors=validation_result.errors,
        ),
        quality=score,
        latency_ms=latency_ms,
    )
