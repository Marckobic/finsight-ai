"""
tests/test_evals.py
The eval suite as a CI gate.

This is what makes the evals a gate rather than a report someone might run.
It executes in mock mode, so it is free, offline and deterministic — a live
run against a real model is a separate, deliberate command.
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from evals.cases import all_cases  # noqa: E402
from evals.runner import run  # noqa: E402


def test_suite_has_enough_cases():
    """PRD Section 16 requires at least 50 cases behind the CI gate."""
    assert len(all_cases()) >= 50


def test_every_failure_family_is_covered():
    """A gate that only tests one failure class measures one failure class."""
    categories = {c.category for c in all_cases()}
    assert {"clean", "numeric", "language", "schema", "transport"} <= categories


def test_all_gates_pass_in_mock_mode():
    report = run(live=False)
    failing = [g["label"] for g in report["gates"] if not g["passed"]]
    assert not failing, (
        f"eval gates failed: {failing}\n"
        + "\n".join(f"  {f['id']}: {f['errors'][:1]}" for f in report["failures"])
    )


def test_no_numeric_hallucination_escapes():
    report = run(live=False)
    assert report["metrics"]["numeric_detection_rate"] == 1.0


def test_faithful_answers_are_not_discarded():
    """The gate must not quietly replace correct answers with the template."""
    report = run(live=False)
    assert report["metrics"]["false_rejection_rate"] <= 0.02
