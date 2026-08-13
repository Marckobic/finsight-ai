"""
evals/gates.py
CI thresholds for the AI layer.

Each gate is a number the build refuses to cross. They are deliberately
asymmetric: detection is absolute, false rejection has a small allowance, and
latency is measured against the same SLA the middleware enforces.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared_types.sla import SLA_MS


@dataclass(frozen=True)
class Gate:
    key: str
    label: str
    # "max" → value must be <= threshold; "min" → value must be >= threshold
    direction: str
    threshold: float
    rationale: str


GATES: tuple[Gate, ...] = (
    Gate(
        "numeric_detection_rate",
        "Numeric hallucinations caught",
        "min", 1.0,
        "A fabricated figure in a financial product is not a quality issue with "
        "an acceptable rate. One escape invalidates the product's core claim.",
    ),
    Gate(
        "language_detection_rate",
        "Prohibited phrasing caught",
        "min", 1.0,
        "Advisor and guarantee phrasing is the regulatory exposure. Same logic: "
        "no tolerable escape rate.",
    ),
    Gate(
        "transport_containment_rate",
        "Provider failures contained",
        "min", 1.0,
        "Every provider error must surface as the deterministic template, never "
        "as an exception. This is the '/explain never returns 5xx' guarantee "
        "expressed as a measurement.",
    ),
    Gate(
        "schema_compliance_rate",
        "Responses matching the output schema",
        "min", 1.0,
        "Anything reaching the UI is schema-valid by construction; the fallback "
        "counts as compliant because it is a valid response.",
    ),
    Gate(
        "false_rejection_rate",
        "Faithful answers wrongly rejected",
        "max", 0.02,
        "The gate discarding correct answers is the failure mode that silently "
        "replaces the product with boilerplate. Small allowance for genuinely "
        "ambiguous phrasing, not for systematic over-blocking.",
    ),
    Gate(
        "latency_p95_ms",
        "p95 end-to-end latency",
        "max", float(SLA_MS["/explain"]),
        "Measured against the same budget the middleware warns on.",
    ),
)


def evaluate(metrics: dict) -> list[dict]:
    """Return one verdict per gate."""
    results = []
    for gate in GATES:
        value = metrics.get(gate.key)
        if value is None:
            results.append({
                "key": gate.key, "label": gate.label, "value": None,
                "threshold": gate.threshold, "direction": gate.direction,
                "passed": False, "reason": "metric not produced",
            })
            continue
        passed = value <= gate.threshold if gate.direction == "max" else value >= gate.threshold
        results.append({
            "key": gate.key, "label": gate.label, "value": value,
            "threshold": gate.threshold, "direction": gate.direction,
            "passed": bool(passed), "rationale": gate.rationale,
        })
    return results
