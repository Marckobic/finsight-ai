"""
apps/api/routers/baseline.py
POST /baseline — deterministic financial baseline computation.

Pipeline:
  1. validate_financial_inputs() — hard gate on user data
  2. build_baseline_projection()  — core engine, single source of truth
  3. log_event(BASELINE_COMPUTED)
  4. Return BaselineResponse with latency_ms

SLA: < 300 ms (enforced by TimingMiddleware header; this layer is deterministic
     and should complete well within budget).
"""

import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core_engine.baseline import build_baseline_projection
from shared_types.models import BaselineResult, FinancialSnapshot
from validation_gateway.validator import validate_financial_inputs

from analytics.buckets import money_bucket, percent_bucket

from apps.api.events import log_event

router = APIRouter()


class BaselineResponse(BaseModel):
    status: str
    data: BaselineResult
    latency_ms: float


@router.post("/baseline", response_model=BaselineResponse)
async def baseline_endpoint(snapshot: FinancialSnapshot) -> BaselineResponse | JSONResponse:
    """
    Compute a deterministic baseline financial projection.

    Returns 422 if financial inputs are invalid (income ≤ 0, negative fields,
    goal_amount ≤ 0).  Sanity warnings (expenses > 3× income) do not block.
    """
    t0 = time.perf_counter()

    # Step 1: Hard validation gate on user-submitted data
    validation = validate_financial_inputs(
        income=snapshot.income.monthly,
        fixed_expenses=snapshot.expenses.fixed,
        variable_expenses=snapshot.expenses.variable,
        current_savings=snapshot.savings.balance,
        monthly_savings_contribution=snapshot.savings.monthly_contribution,
        goal_amount=snapshot.goal.target_amount,
    )
    if not validation.valid:
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "errors": validation.errors,
                "code": "VALIDATION_ERROR",
            },
        )

    # Step 2: Deterministic engine — single source of truth
    result = build_baseline_projection(snapshot)

    # Step 3: Structured event log.
    #
    # Bucketed, not exact. This line used to carry the user's monthly cashflow
    # and savings rate next to their user_id, into stdout, which on Railway is
    # retained log output. A band answers every operational question the log is
    # read for ("are people with thin surplus erroring out?") and stores none of
    # anyone's finances.
    log_event(
        "BASELINE_COMPUTED",
        {
            "user_id": snapshot.user_id,
            "cashflow_bucket": money_bucket(result.monthly_cashflow),
            "savings_rate_bucket": percent_bucket(result.savings_rate),
            "time_to_goal_months": result.time_to_goal_months,
        },
    )

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return BaselineResponse(status="ok", data=result, latency_ms=latency_ms)
