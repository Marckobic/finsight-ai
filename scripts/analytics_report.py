#!/usr/bin/env python3
"""
scripts/analytics_report.py
Usage: python scripts/analytics_report.py [session_id]
"""

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_analytics = os.path.join(_root, "packages", "analytics")
if _analytics not in sys.path:
    sys.path.insert(0, _analytics)

from analytics.store import get_all_events, get_events
from analytics.metrics import calculate_session_summary, calculate_funnel


def _pick_session(session_id: str | None) -> str | None:
    if session_id:
        return session_id
    events = get_all_events()
    if not events:
        return None
    return events[-1]["session_id"]


def render(session_id: str) -> None:
    summary = calculate_session_summary(session_id)
    funnel = summary["funnel"]["stages"]
    drop_off = summary["funnel"]["drop_off"]

    opened = summary["scenarios_opened"]
    accepted = summary["scenarios_accepted"]
    rejected = summary["scenarios_rejected"]
    dlcr = summary["dlcr"]
    acceptance_rate = summary["acceptance_rate"]
    avg_accept = summary["avg_adherence_at_accept"]

    def stage_line(label: str, key: str, detail: str = "") -> str:
        icon = "✅" if funnel.get(key) else "❌"
        return f"│   {icon} {label}{detail}"

    scenario_detail = f" ({opened}x)" if opened else ""
    decision_detail = f" ({accepted} accepted, {rejected} rejected)" if (accepted + rejected) else ""

    width = 51
    border = "─" * (width - 2)

    lines = [
        f"┌{border}┐",
        f"│ Session: {session_id:<{width - 12}}│",
        f"│{' ' * (width - 2)}│",
        f"│ FUNNEL:{' ' * (width - 10)}│",
        stage_line("Goal created",       "goal_created") + " " * (width - 2 - len(stage_line("Goal created", "goal_created"))) + "│",
        stage_line("Snapshot submitted", "snapshot_submitted") + " " * (width - 2 - len(stage_line("Snapshot submitted", "snapshot_submitted"))) + "│",
        stage_line("Baseline generated", "baseline_generated") + " " * (width - 2 - len(stage_line("Baseline generated", "baseline_generated"))) + "│",
        stage_line("Scenario opened",    "scenario_opened", scenario_detail) + " " * (width - 2 - len(stage_line("Scenario opened", "scenario_opened", scenario_detail))) + "│",
        stage_line("Decision made",      "decision_made", decision_detail) + " " * (width - 2 - len(stage_line("Decision made", "decision_made", decision_detail))) + "│",
        f"│{' ' * (width - 2)}│",
    ]

    completed = int(dlcr * opened) if opened else 0
    dlcr_line = f"│ DLCR: {dlcr * 100:.0f}% ({completed}/{opened} loops completed)"
    lines.append(dlcr_line + " " * (width - 2 - len(dlcr_line) + 2) + "│")

    ar_line = f"│ Acceptance rate: {acceptance_rate * 100:.0f}%"
    lines.append(ar_line + " " * (width - 2 - len(ar_line) + 2) + "│")

    adh_line = f"│ Avg adherence at accept: {avg_accept:.0f}%"
    lines.append(adh_line + " " * (width - 2 - len(adh_line) + 2) + "│")

    lines.append(f"└{border}┘")

    print("\n".join(lines))


def main() -> None:
    arg_session = sys.argv[1] if len(sys.argv) > 1 else None
    session_id = _pick_session(arg_session)
    if not session_id:
        print("No events found in database.")
        sys.exit(1)
    render(session_id)


if __name__ == "__main__":
    main()
