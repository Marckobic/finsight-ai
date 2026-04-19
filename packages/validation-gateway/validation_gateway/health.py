"""
validation_gateway/health.py
In-memory AI health tracker. Thread-safe. Resets on server restart.
"""

import threading
from collections import Counter

from validation_gateway.scorer import AIQualityScore


class AIHealthTracker:
    """Thread-safe in-memory tracker. No DB, no persistence."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._scores: list[float] = []
        self._statuses: list[str] = []
        self._reasons: list[str] = []

    def record(self, score: AIQualityScore) -> None:
        with self._lock:
            self._scores.append(score.total)
            self._statuses.append(score.status)
            self._reasons.extend(score.reasons)

    def summary(self) -> dict:
        with self._lock:
            n = len(self._scores)
            if n == 0:
                return {
                    "total_evaluations": 0,
                    "avg_score": 0.0,
                    "approved_rate": 0.0,
                    "degraded_rate": 0.0,
                    "fallback_rate": 0.0,
                    "top_failure_reasons": [],
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
            }


# Singleton — import this from api/main.py and routers
health_tracker = AIHealthTracker()
