"""
apps/api/routers/explain.py
POST /explain — AI explanation generation with hard validation gate + quality scoring.

Pipeline:
  1. generate_explanation()     — AI layer (never raises; returns ValidationResult)
  2. score_ai_output()          — quality scoring (pure function)
  3. health_tracker.record()    — in-memory health metrics incl. latency
  4. If score.status=="fallback" → use deterministic fallback
  5. Return ExplainResponse with quality field

SYSTEM RULE: This endpoint NEVER returns 5xx.

That rule is enforced here, not assumed. generate_explanation() is documented
as never raising, but "the callee promises not to throw" is not a guarantee —
it is a dependency. The whole pipeline is wrapped, so a provider exception, a
schema change or a bug in the gate degrades to the deterministic template
instead of surfacing as a 500 on a screen holding the user's finances.

SLA: < 3000 ms (shared_types.sla.SLA_MS). Latency is recorded per response so
the number can be reported from measurement rather than from intent.
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ai_layer.explain import (
    build_proxy_baseline,
    build_proxy_scenario,
    generate_explanation,
)
from shared_types.models import AIExplanationInput, AIExplanationOutput
from validation_gateway.validator import _fallback_output
from validation_gateway.scorer import AIQualityScore, score_ai_output
from validation_gateway.health import health_tracker

from apps.api.events import log_event
from apps.api.ratelimit import explain_budget

logger = logging.getLogger(__name__)

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


def _degraded_response(reason: str, latency_ms: float) -> ExplainResponse:
    """Last-resort response. Used only when the pipeline itself failed."""
    return ExplainResponse(
        status="fallback",
        data=_fallback_output(),
        validation=ExplainValidation(valid=False, fallback_used=True, errors=[reason]),
        quality=None,
        latency_ms=latency_ms,
    )


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

    # Cost guard. Past the daily budget the product keeps working and serves
    # the deterministic template — degrade the answer, never the bill.
    if not explain_budget.consume():
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.warning("daily /explain budget exhausted — serving deterministic template")
        log_event("AI_EXPLANATION_GENERATED", {
            "valid": False, "fallback_used": True,
            "quality_status": "fallback", "reason": "daily_budget_exhausted",
            "latency_ms": latency_ms,
        })
        return _degraded_response("daily AI budget exhausted", latency_ms)

    try:
        # Step 1: Full AI pipeline — guaranteed to return ValidationResult
        validation_result = generate_explanation(input)
        output: AIExplanationOutput = validation_result.validated_output or _fallback_output()
        status = "fallback" if validation_result.fallback_used else "ok"

        # Step 2: Engine-truth views, built once in the AI layer so the gate
        # and the scorer cannot drift apart.
        proxy_baseline = build_proxy_baseline(input)
        proxy_scenario = build_proxy_scenario(input)

        score = score_ai_output(validation_result, output, proxy_scenario, proxy_baseline)

        # Step 3: Override with fallback if quality gate fails
        if score.status == "fallback":
            output = _fallback_output()
            status = "fallback"

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        numeric_ok = not any(
            "Numeric hallucination" in e for e in validation_result.errors
        )
        health_tracker.record(
            score,
            latency_ms=latency_ms,
            numeric_ok=numeric_ok,
            fallback_used=(status == "fallback"),
        )

        # Step 4: Structured event log
        log_event(
            "AI_EXPLANATION_GENERATED",
            {
                "valid": validation_result.valid,
                "fallback_used": validation_result.fallback_used,
                "quality_status": score.status,
                "quality_total": score.total,
                "numeric_ok": numeric_ok,
                "latency_ms": latency_ms,
            },
        )

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

    except Exception as exc:  # noqa: BLE001 — the endpoint contract is "never 5xx"
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.exception("/explain pipeline failed — serving deterministic fallback")
        log_event(
            "AI_EXPLANATION_GENERATED",
            {
                "valid": False,
                "fallback_used": True,
                "quality_status": "fallback",
                "pipeline_error": type(exc).__name__,
                "latency_ms": latency_ms,
            },
        )
        return _degraded_response(f"pipeline error: {type(exc).__name__}", latency_ms)
