"""
apps/api/routers/scenario.py
POST /scenario — behavioral scenario simulation.

Pipeline:
  1. simulate_scenario()         — deterministic engine
  2. validate_scenario_output()  — hard safety gate
  3. log_event(SCENARIO_SIMULATED)
  4. Return ScenarioResponse

Data is always returned, even when validation.valid=False.
The UI uses the data to show a fallback — it is never hidden from the client.

SLA: < 1500 ms (synchronous engine; well within budget).
"""

import time

from fastapi import APIRouter
from pydantic import BaseModel

from scenario_engine.simulate import simulate_scenario
from shared_types.models import (
    BaselineResult,
    BehaviorChange,
    FinancialSnapshot,
    ScenarioResult,
    ScenarioInput,
)
from validation_gateway.validator import validate_scenario_output

from apps.api.events import log_event

router = APIRouter()


class ValidationSummary(BaseModel):
    valid: bool
    errors: list[str]


class ScenarioResponse(BaseModel):
    status: str
    data: ScenarioResult
    validation: ValidationSummary
    latency_ms: float


@router.post("/scenario", response_model=ScenarioResponse)
async def scenario_endpoint(request: ScenarioInput) -> ScenarioResponse:
    """
    Simulate the financial impact of a single behavioral change.

    adherence_rate is clamped to [0.1, 0.95] by the engine — values outside
    that range are accepted and clamped, never rejected.

    The response always includes data regardless of validation outcome.
    Check validation.valid to decide whether to show fallback content.
    """
    t0 = time.perf_counter()

    # Step 1: Deterministic simulation
    result = simulate_scenario(
        request.financial_snapshot,
        request.baseline,
        request.behavior_change,
        request.adherence_rate,
    )

    # Step 2: Hard safety gate on engine output
    validation_result = validate_scenario_output(result)

    # Step 3: Structured event log
    log_event(
        "SCENARIO_SIMULATED",
        {
            "user_id": request.financial_snapshot.user_id,
            "delta_months": result.delta_months,
            "adherence_rate": result.adherence_rate,
            "behavior_type": request.behavior_change.type,
        },
    )

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return ScenarioResponse(
        status="ok",
        data=result,
        validation=ValidationSummary(
            valid=validation_result.valid,
            errors=validation_result.errors,
        ),
        latency_ms=latency_ms,
    )
