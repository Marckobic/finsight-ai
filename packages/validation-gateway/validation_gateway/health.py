"""
validation_gateway/health.py
In-memory AI health tracker. Thread-safe. Resets on server restart.

Tracks the three numbers that describe whether the AI layer is working:

  numeric_fidelity_rate — share of responses where every figure traced back to
                          engine output. Target 1.0, no tolerance: this is the
                          product's core promise, not a quality preference.
  fallback_rate         — share of responses served from the deterministic
                          template. Expected to be non-zero; it is the safety
                          net doing its job, and it is what makes the fidelity
                          number trustworthy.
  latency p50 / p95     — measured, not asserted. "< 3000 ms" claimed against a
                          mock that answers instantly means nothing.

In-memory means per-process and reset on deploy. That is honest for an MVP,
but it does mean /analytics/ai-health reports the current replica only — read
it as a live probe, not as a historical record.
"""

import threading
from collections import Counter

from validation_gateway.scorer import AIQualityScore

# Keep memory bounded on a long-lived process.
_MAX_SAMPLES = 5000


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Nearest-rank percentile. No numpy dependency for six lines of arithmetic."""
    if not sorted_values:
        return 0.0
    k = max(0, min(len(sorted_values) - 1, int(round(pct / 100 * len(sorted_values) + 0.5)) - 1))
    return sorted_values[k]


class AIHealthTracker:
    """Thread-safe in-memory tracker. No DB, no persistence."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._scores: list[float] = []
        self._statuses: list[str] = []
        self._reasons: list[str] = []
        self._latencies: list[float] = []
        self._numeric_failures = 0
        self._fallbacks = 0
        self._responses = 0

    def record(
        self,
        score: AIQualityScore,
        latency_ms: float | None = None,
        numeric_ok: bool | None = None,
        fallback_used: bool | None = None,
    ) -> None:
        with self._lock:
            self._scores.append(score.total)
            self._statuses.append(score.status)
            self._reasons.extend(score.reasons)

            if latency_ms is not None:
                self._latencies.append(float(latency_ms))
                if len(self._latencies) > _MAX_SAMPLES:
                    del self._latencies[: len(self._latencies) - _MAX_SAMPLES]

            if numeric_ok is not None or fallback_used is not None:
                self._responses += 1
                if numeric_ok is False:
                    self._numeric_failures += 1
                if fallback_used:
                    self._fallbacks += 1

            if len(self._scores) > _MAX_SAMPLES:
                cut = len(self._scores) - _MAX_SAMPLES
                del self._scores[:cut]
                del self._statuses[:cut]

    def summary(self) -> dict:
        with self._lock:
            n = len(self._scores)
            latencies = sorted(self._latencies)
            responses = self._responses

            latency_block = {
                "latency_samples": len(latencies),
                "latency_p50_ms": round(_percentile(latencies, 50), 2),
                "latency_p95_ms": round(_percentile(latencies, 95), 2),
                "latency_max_ms": round(latencies[-1], 2) if latencies else 0.0,
            }
            fidelity_block = {
                "responses": responses,
                "numeric_fidelity_rate": (
                    round((responses - self._numeric_failures) / responses, 4)
                    if responses else 1.0
                ),
                "fallback_rate_observed": (
                    round(self._fallbacks / responses, 4) if responses else 0.0
                ),
            }

            if n == 0:
                return {
                    "total_evaluations": 0,
                    "avg_score": 0.0,
                    "approved_rate": 0.0,
                    "degraded_rate": 0.0,
                    "fallback_rate": 0.0,
                    "top_failure_reasons": [],
                    **latency_block,
                    **fidelity_block,
                }

            avg = sum(self._scores) / n
            counts = Counter(self._statuses)
            top = [r for r, _ in Counter(self._reasons).most_common(3)]
            return {
                "total_evaluations": n,
                "avg_score": round(avg, 2),
                "approved_rate": round(counts["approved"] / n, 4),
                "degraded_rate": round(counts["degraded"] / n, 4),
                "fallback_rate": round(counts["fallback"] / n, 4),
                "top_failure_reasons": top,
                **latency_block,
                **fidelity_block,
            }


# Singleton — import this from api/main.py and routers
health_tracker = AIHealthTracker()
