"""
apps/api/middleware/timing.py
Request timing middleware — SLA enforcement and header injection.

Adds X-Response-Time-Ms to every response.
Logs a warning whenever a route exceeds its SLA budget.
Never blocks the response — observation only.

SLA budgets (PRD Section 13):
  /baseline  → 300 ms
  /scenario  → 1500 ms
  /explain   → 3000 ms
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# SLA thresholds in milliseconds
_SLA_MS: dict[str, int] = {
    "/baseline": 300,
    "/scenario": 1500,
    "/explain": 3000,
}


class TimingMiddleware(BaseHTTPMiddleware):
    """Measure wall-clock request duration, inject header, warn on SLA breach."""

    async def dispatch(self, request: Request, call_next) -> Response:
        t0 = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.2f}"

        limit = _SLA_MS.get(request.url.path)
        if limit is not None and elapsed_ms > limit:
            logger.warning(
                "SLA breach on %s: %.2f ms (limit %d ms)",
                request.url.path,
                elapsed_ms,
                limit,
            )

        return response
