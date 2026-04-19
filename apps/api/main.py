"""
apps/api/main.py
FinSight.ai — FastAPI backend entry point.

Wires all engine layers (core → scenario → AI → validation gateway) into
HTTP endpoints. Adds CORS, request timing, and structured error handling.

Run locally:
  uvicorn apps.api.main:app --reload --port 8000

All packages are added to sys.path at module load time so this file is
runnable without a pip-install step (same pattern as conftest.py).
"""

# ---------------------------------------------------------------------------
# sys.path bootstrap — MUST come before any package imports
# ---------------------------------------------------------------------------
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.normpath(os.path.join(_here, "..", ".."))

for _pkg in [
    "packages/core-engine",
    "packages/scenario-engine",
    "packages/validation-gateway",
    "packages/shared-types",
    "packages/ai-layer",
    "packages/analytics",
]:
    _path = os.path.join(_root, _pkg)
    if _path not in sys.path:
        sys.path.insert(0, _path)

# ---------------------------------------------------------------------------
# Standard library + third-party imports
# ---------------------------------------------------------------------------
import logging
import traceback
from typing import Literal

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

# ---------------------------------------------------------------------------
# Internal imports (packages now on sys.path)
# ---------------------------------------------------------------------------
from shared_types.models import ScenarioResult
from apps.api.events import log_event
from analytics.models import AnalyticsEvent
from analytics.store import insert_event
from analytics.metrics import calculate_session_summary, calculate_funnel
from validation_gateway.health import health_tracker
from apps.api.middleware.timing import TimingMiddleware
from apps.api.routers import baseline as baseline_router
from apps.api.routers import scenario as scenario_router
from apps.api.routers import explain as explain_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serializable_errors(errors: list) -> list:
    """
    Convert Pydantic v2 error dicts to JSON-safe form.

    Pydantic v2 stores exception instances (e.g. ValueError) in the ``ctx``
    key of each error dict.  Those are not JSON-serializable, so we convert
    any Exception value to its string representation.
    """
    safe = []
    for err in errors:
        safe_err = {}
        for k, v in err.items():
            if isinstance(v, Exception):
                safe_err[k] = str(v)
            elif isinstance(v, dict):
                safe_err[k] = {
                    kk: str(vv) if isinstance(vv, Exception) else vv
                    for kk, vv in v.items()
                }
            else:
                safe_err[k] = v
        safe.append(safe_err)
    return safe

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="FinSight.ai API",
    version="0.1.0",
    description="Deterministic financial engine + AI explanation layer.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Middleware (order matters — outermost is added last)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(TimingMiddleware)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request, exc: RequestValidationError) -> JSONResponse:
    """FastAPI request body / query-param validation failures → 422."""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Request validation failed.",
            "errors": _serializable_errors(exc.errors()),
            "code": "SCHEMA_ERROR",
        },
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request, exc: ValidationError) -> JSONResponse:
    """Pydantic ValidationError raised within endpoint handlers → 422."""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Data validation failed.",
            "errors": _serializable_errors(exc.errors()),
            "code": "SCHEMA_ERROR",
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError) -> JSONResponse:
    """Engine ValueError (bad inputs) → 422."""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": str(exc),
            "code": "INPUT_ERROR",
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions — log traceback, return safe 500."""
    traceback.print_exc(file=sys.stderr)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred.",
            "code": "INTERNAL_ERROR",
        },
    )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(baseline_router.router)
app.include_router(scenario_router.router)
app.include_router(explain_router.router)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.post("/events")
async def ingest_event(event: AnalyticsEvent) -> dict:
    insert_event(event)
    return {"ok": True}


@app.get("/analytics/session/{session_id}")
async def session_summary(session_id: str) -> dict:
    return calculate_session_summary(session_id)


@app.get("/analytics/funnel/{session_id}")
async def session_funnel(session_id: str) -> dict:
    return calculate_funnel(session_id)


@app.get("/analytics/ai-health")
async def ai_health() -> dict:
    return health_tracker.summary()


@app.get("/health")
async def health() -> dict:
    """Liveness probe — no dependencies, always 200."""
    return {"status": "ok", "version": "0.1.0", "phase": "mvp"}

# ---------------------------------------------------------------------------
# Decision / feedback endpoint
# ---------------------------------------------------------------------------


class DecisionEvent(BaseModel):
    user_id: str
    event_type: Literal["accepted", "rejected", "modified"]
    scenario_result: ScenarioResult
    timestamp: str  # ISO8601


@app.post("/decision")
async def decision_endpoint(event: DecisionEvent) -> dict:
    """
    Log a user decision on a recommendation.

    No DB in MVP — written as structured JSON to stdout for Phase 3 ingestion.
    """
    if event.event_type in ("accepted", "modified"):
        log_event(
            "RECOMMENDATION_ACCEPTED",
            {
                "user_id": event.user_id,
                "scenario_delta": event.scenario_result.delta_months,
            },
        )
    else:
        log_event(
            "RECOMMENDATION_REJECTED",
            {"user_id": event.user_id},
        )

    return {"status": "logged"}
