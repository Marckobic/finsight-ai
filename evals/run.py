"""
evals/run.py
CLI entry point.

    python evals/run.py                # mock mode (free, offline, CI default)
    OPENAI_API_KEY=... python evals/run.py   # live mode

Exit code is 0 only when every gate passes, so this doubles as the CI gate.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _pkg in [
    "packages/core-engine", "packages/scenario-engine", "packages/validation-gateway",
    "packages/shared-types", "packages/ai-layer", "packages/analytics", "",
]:
    _p = os.path.join(_ROOT, _pkg)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from evals.runner import run  # noqa: E402


def _fmt(value) -> str:
    return "n/a" if value is None else (
        f"{value:.4g}" if isinstance(value, float) else str(value)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="FinSight.ai AI-layer evaluation suite")
    parser.add_argument("--live", action="store_true", help="force live model mode")
    parser.add_argument("--mock", action="store_true", help="force mock mode")
    parser.add_argument("--json", dest="json_path", default="evals/report.json")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--verbose", action="store_true",
                        help="show the gateway's per-rejection log lines")
    args = parser.parse_args()

    # Rejections are the expected outcome for 26 of the cases; logging each one
    # buries the report. --verbose brings them back when debugging a gap.
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.CRITICAL)

    live = True if args.live else (False if args.mock else None)
    report = run(live=live)

    if not args.quiet:
        print(f"\nFinSight.ai — AI layer evaluation  [{report['mode'].upper()} MODE]")
        print(report["mode_note"])
        print(
            f"\n{report['total_cases']} cases "
            f"({report['clean_cases']} clean, {report['adversarial_cases']} adversarial)  "
            f"passed={report['passed']}  failed={report['failed']}\n"
        )
        print(f"{'GATE':<38}{'VALUE':>12}{'THRESHOLD':>12}   RESULT")
        print("-" * 78)
        for gate in report["gates"]:
            arrow = "<=" if gate["direction"] == "max" else ">="
            print(
                f"{gate['label']:<38}{_fmt(gate['value']):>12}"
                f"{arrow + ' ' + _fmt(gate['threshold']):>12}   "
                f"{'PASS' if gate['passed'] else 'FAIL'}"
            )
        if report["failures"]:
            print("\nFailing cases:")
            for failure in report["failures"]:
                print(f"  - {failure['id']}  ({failure['notes']})")
                for err in failure["errors"]:
                    print(f"      {err[:140]}")

    os.makedirs(os.path.dirname(os.path.abspath(args.json_path)), exist_ok=True)
    with open(args.json_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    if not args.quiet:
        print(f"\nreport → {args.json_path}")

    return 0 if report["gates_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
