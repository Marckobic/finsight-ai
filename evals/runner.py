"""
evals/runner.py
Executes the frozen case suite through the real pipeline and reports metrics.

The pipeline under test is exactly the production one — build_prompt →
call_llm → validate_ai_output → score_ai_output — with the client swapped per
case. Nothing is stubbed inside the gate.

MODE MATTERS. The report always states whether it ran against the mock or a
live model, because a latency number measured against an instant mock is not a
latency number. Mock mode measures pipeline overhead and guard behaviour; live
mode measures what a user experiences. Both are useful; conflating them is how
"<3s latency" ends up in a CV without ever having been observed.
"""

from __future__ import annotations

import os
import statistics
import time
from dataclasses import dataclass, field
from typing import Optional

from ai_layer.explain import (
    MockLLMClient,
    build_proxy_baseline,
    build_proxy_scenario,
    generate_explanation,
    get_llm_client,
)
from evals.cases import EvalCase, all_cases
from evals.gates import evaluate
from shared_types.models import AIExplanationOutput
from validation_gateway.scorer import score_ai_output
from validation_gateway.validator import _fallback_output


@dataclass
class CaseResult:
    id: str
    category: str
    passed: bool
    valid: bool
    fallback_used: bool
    quality_status: str
    quality_total: float
    latency_ms: float
    errors: list[str] = field(default_factory=list)
    notes: str = ""


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, int(round(pct / 100 * len(ordered) + 0.5)) - 1))
    return ordered[k]


def _client_for(case: EvalCase, live: bool):
    if case.client_factory is not None:
        return case.client_factory()
    return get_llm_client() if live else MockLLMClient(mode="valid")


def run_case(case: EvalCase, live: bool) -> CaseResult:
    t0 = time.perf_counter()
    client = _client_for(case, live)

    result = generate_explanation(case.input, client=client)

    output: AIExplanationOutput = result.validated_output or _fallback_output()
    score = score_ai_output(
        result,
        output,
        build_proxy_scenario(case.input),
        build_proxy_baseline(case.input),
    )
    latency_ms = (time.perf_counter() - t0) * 1000

    if case.expect_valid:
        # A clean case passes only if the answer survived intact: the gate
        # accepted it AND the quality scorer did not silently swap it for the
        # template. Both are ways of losing the answer.
        passed = result.valid and score.status != "fallback"
    else:
        passed = not result.valid

    return CaseResult(
        id=case.id,
        category=case.category,
        passed=passed,
        valid=result.valid,
        fallback_used=result.fallback_used,
        quality_status=score.status,
        quality_total=score.total,
        latency_ms=round(latency_ms, 2),
        errors=list(result.errors),
        notes=case.notes,
    )


def _rate(results: list[CaseResult], predicate) -> Optional[float]:
    subset = [r for r in results if predicate(r)]
    if not subset:
        return None
    return round(sum(1 for r in subset if r.passed) / len(subset), 4)


def run(live: Optional[bool] = None, cases: Optional[list[EvalCase]] = None) -> dict:
    """Run the suite and return a report dict."""
    if live is None:
        live = bool(os.environ.get("OPENAI_API_KEY", "").strip()) and not os.environ.get(
            "FINSIGHT_FORCE_MOCK", ""
        ).strip()

    suite = cases if cases is not None else all_cases()
    results = [run_case(c, live=live) for c in suite]

    clean = [r for r in results if r.category == "clean"]
    latencies = [r.latency_ms for r in results]

    false_rejections = sum(1 for r in clean if not r.passed)

    metrics = {
        "numeric_detection_rate": _rate(results, lambda r: r.category == "numeric"),
        "language_detection_rate": _rate(results, lambda r: r.category == "language"),
        "transport_containment_rate": _rate(results, lambda r: r.category == "transport"),
        "schema_compliance_rate": _rate(results, lambda r: r.category == "schema"),
        "false_rejection_rate": round(false_rejections / len(clean), 4) if clean else 0.0,
        "latency_p50_ms": round(statistics.median(latencies), 2) if latencies else 0.0,
        "latency_p95_ms": round(_percentile(latencies, 95), 2),
        "latency_max_ms": round(max(latencies), 2) if latencies else 0.0,
    }

    gate_results = evaluate(metrics)

    return {
        "mode": "live" if live else "mock",
        "mode_note": (
            "Latency measured against a live model."
            if live else
            "Latency measured against the deterministic mock — this number is "
            "pipeline overhead, NOT user-observed latency. Re-run with "
            "OPENAI_API_KEY set before quoting it anywhere."
        ),
        "total_cases": len(results),
        "clean_cases": len(clean),
        "adversarial_cases": len(results) - len(clean),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "metrics": metrics,
        "gates": gate_results,
        "gates_passed": all(g["passed"] for g in gate_results),
        "failures": [
            {"id": r.id, "category": r.category, "notes": r.notes,
             "valid": r.valid, "quality_status": r.quality_status,
             "errors": r.errors[:3]}
            for r in results if not r.passed
        ],
        "results": [r.__dict__ for r in results],
    }
