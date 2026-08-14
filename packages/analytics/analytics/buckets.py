"""
analytics/buckets.py
Coarsening for anything money-shaped before it is stored or logged.

WHY
---
The landing page promises "no data sharing — numbers stay in-session only", and
the app was posting `target_amount`, `monthly_cashflow`, `savings_rate` and
`time_to_goal` to /events, where they were written to a database keyed by
session_id. The backend's own stdout log carried `cashflow` and `savings_rate`
next to `user_id`. With no users that was a theoretical mismatch; with demo
users it is a public promise the system does not keep.

Buckets answer every analytical question the funnel actually asks — do people
with a thin surplus drop out earlier? does adherence differ by income band? —
without a single personal figure leaving the device or landing in a log.

Note what buckets do NOT fix: /baseline and /scenario must receive the real
numbers, because the engine runs server-side. Transmission is inherent to the
architecture; persistence is not. The honest claim is "we do not store your
financial data", and the landing copy should say that rather than implying the
numbers never leave the browser.
"""

from __future__ import annotations

# Monthly-money bands. Deliberately coarse at the bottom, where a founder's
# surplus actually varies, and open-ended at the top.
_MONEY_EDGES: tuple[tuple[float, str], ...] = (
    (0, "0"),
    (250, "1-250"),
    (500, "250-500"),
    (1000, "500-1000"),
    (2500, "1000-2500"),
    (5000, "2500-5000"),
    (10000, "5000-10000"),
)
_MONEY_TOP = "10000+"

_PERCENT_EDGES: tuple[tuple[float, str], ...] = (
    (0, "0"),
    (5, "0-5"),
    (10, "5-10"),
    (20, "10-20"),
    (30, "20-30"),
    (50, "30-50"),
)
_PERCENT_TOP = "50+"

_MONTH_EDGES: tuple[tuple[float, str], ...] = (
    (3, "0-3"),
    (6, "3-6"),
    (12, "6-12"),
    (24, "12-24"),
    (60, "24-60"),
)
_MONTH_TOP = "60+"


def _band(value: float | None, edges, top: str, negative: str = "negative") -> str:
    if value is None:
        return "unknown"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if number != number:  # NaN
        return "unknown"
    if number < 0:
        return negative
    for edge, label in edges:
        if number <= edge:
            return label
    return top


def money_bucket(value: float | None) -> str:
    """USD per month → a band label. Never returns the input."""
    return _band(value, _MONEY_EDGES, _MONEY_TOP)


def percent_bucket(value: float | None) -> str:
    """A rate already expressed in percent (5.0 == 5%)."""
    return _band(value, _PERCENT_EDGES, _PERCENT_TOP)


def months_bucket(value: float | None) -> str:
    """Months are a duration, not an amount — kept exact elsewhere; this is for
    grouping in reports."""
    return _band(value, _MONTH_EDGES, _MONTH_TOP, negative="unreachable")
