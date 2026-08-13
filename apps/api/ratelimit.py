"""
apps/api/ratelimit.py
Abuse and cost control for the public endpoints.

Why this exists: /explain is unauthenticated by product design ("no signup"),
and once a real LLM key is configured every call spends money. An open,
unauthenticated, paid endpoint whose URL is about to be posted publicly is
found by scanners in hours, not weeks.

Two independent limits:

  per-IP sliding window  — stops one client hammering the endpoint
  global daily budget    — caps total paid calls per day; past the cap the
                           endpoint keeps working and serves the deterministic
                           template. Degrade the product, never the bill.

In-process and therefore per-replica: two replicas allow twice the traffic.
That is the right trade for an MVP with no Redis, and it is deliberate rather
than accidental — set the budget accordingly, and keep a hard spend cap on the
provider account as the real backstop.
"""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

EXPLAIN_PER_IP_PER_HOUR = int(os.environ.get("FINSIGHT_EXPLAIN_IP_HOURLY", "20"))
EXPLAIN_GLOBAL_DAILY = int(os.environ.get("FINSIGHT_EXPLAIN_DAILY_BUDGET", "2000"))

_WINDOW_S = 3600
_DAY_S = 86400


class SlidingWindowLimiter:
    """Per-key sliding window. Bounded memory: idle keys are evicted on sweep."""

    def __init__(self, limit: int, window_s: int = _WINDOW_S) -> None:
        self.limit = limit
        self.window_s = window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._last_sweep = 0.0

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            self._sweep(now)
            bucket = self._hits[key]
            cutoff = now - self.window_s
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            return True

    def _sweep(self, now: float) -> None:
        if now - self._last_sweep < 60:
            return
        self._last_sweep = now
        cutoff = now - self.window_s
        for key in [k for k, v in self._hits.items() if not v or v[-1] < cutoff]:
            del self._hits[key]


class DailyBudget:
    """Global counter that resets on a rolling 24h boundary."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._count = 0
        self._window_start = time.monotonic()
        self._lock = threading.Lock()

    def consume(self) -> bool:
        with self._lock:
            now = time.monotonic()
            if now - self._window_start >= _DAY_S:
                self._window_start = now
                self._count = 0
            if self._count >= self.limit:
                return False
            self._count += 1
            return True

    def state(self) -> dict:
        with self._lock:
            return {
                "used": self._count,
                "limit": self.limit,
                "remaining": max(0, self.limit - self._count),
            }


explain_ip_limiter = SlidingWindowLimiter(EXPLAIN_PER_IP_PER_HOUR)
explain_budget = DailyBudget(EXPLAIN_GLOBAL_DAILY)


def client_key(request) -> str:
    """Best-effort client identity behind Railway's proxy."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return getattr(getattr(request, "client", None), "host", "unknown") or "unknown"
