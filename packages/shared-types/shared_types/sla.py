"""
shared_types/sla.py
Latency budgets — one definition, imported everywhere they are enforced.

These numbers appear in the middleware that measures requests, in the LLM
client that has to finish inside them, and in the eval gates that fail the
build when they are exceeded. Keeping three copies in sync by hand is how a
"SLA in code" quietly becomes a comment.
"""

from __future__ import annotations

# Wall-clock budget per endpoint, milliseconds.
SLA_MS: dict[str, int] = {
    "/baseline": 300,
    "/scenario": 1500,
    "/explain": 3000,
}

# Share of the /explain budget the model call may consume. The remainder pays
# for prompt construction, the validation gate, quality scoring, serialisation
# and the hop back to the client.
LLM_DEADLINE_FRACTION = 0.8

# Per-attempt ceiling, so a stalled first attempt still leaves room for a retry.
LLM_ATTEMPT_FRACTION = 0.55


def llm_deadline_ms() -> int:
    return int(SLA_MS["/explain"] * LLM_DEADLINE_FRACTION)


def llm_attempt_timeout_ms() -> int:
    return int(SLA_MS["/explain"] * LLM_ATTEMPT_FRACTION)
