"""
validation_gateway/language_guard.py
Regulatory phrasing enforcement.

The ai-layer system prompt forbids advisor language and expressions of certainty.
A prompt states an intention; this module makes it a property of the system.

Two tiers, deliberately separated:

  BLOCKING  — phrasing that reads as personalised financial advice or as a
              guarantee. Forces the deterministic fallback. These are the
              phrases that create regulatory exposure, not style problems.

  ADVISORY  — softer directive phrasing. Scored, not blocked, because a hard
              gate here would push fallback_rate up without reducing risk.
"""

from __future__ import annotations

import re

_BLOCKING_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\byou\s+should\b", "directive advice ('you should')"),
    (r"\byou\s+must\b", "directive advice ('you must')"),
    (r"\bi\s+(?:recommend|advise|suggest)\b", "first-person advice"),
    (r"\bwe\s+(?:recommend|advise)\b", "first-person advice"),
    (r"\bmy\s+advice\b", "first-person advice"),
    (r"\b(?:financial|investment)\s+advisor\b", "advisor framing"),
    (r"\bguarantee(?:d|s)?\b", "guarantee language"),
    (r"\brisk[- ]free\b", "guarantee language"),
    (r"\bwill\s+definitely\b", "certainty language"),
    (r"\byou\s+are\s+guaranteed\b", "guarantee language"),
    (r"\b(?:invest|buy|sell)\s+in\s+(?:stocks|crypto|bonds|etfs?)\b", "investment advice"),
)

_ADVISORY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bconsider\b", "soft directive ('consider')"),
    (r"\bmake\s+sure\b", "soft directive ('make sure')"),
    (r"\bneed\s+to\b", "soft directive ('need to')"),
    (r"\bwill\s+(?:reach|hit|achieve)\b", "unhedged certainty"),
)

_BLOCKING = tuple((re.compile(p, re.IGNORECASE), label) for p, label in _BLOCKING_PATTERNS)
_ADVISORY = tuple((re.compile(p, re.IGNORECASE), label) for p, label in _ADVISORY_PATTERNS)


def find_blocking(text: str) -> list[str]:
    """Phrases that must force a fallback. Empty list means clean."""
    hits: list[str] = []
    for pattern, label in _BLOCKING:
        m = pattern.search(text)
        if m:
            hits.append(f"Prohibited phrasing {m.group(0)!r} — {label}")
    return hits


def find_advisory(text: str) -> list[str]:
    """Phrases worth a score deduction but not a fallback."""
    hits: list[str] = []
    for pattern, label in _ADVISORY:
        m = pattern.search(text)
        if m:
            hits.append(f"Soft directive {m.group(0)!r} — {label}")
    return hits
