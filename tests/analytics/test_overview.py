"""
tests/analytics/test_overview.py
The cross-session funnel — the only view that answers "where do people fall out".
"""


import analytics.store as store_mod
import pytest


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "_DB_PATH", str(tmp_path / "overview.db"))
    monkeypatch.setattr(store_mod, "_initialised", set())


from analytics.metrics import calculate_overview  # noqa: E402
from analytics.models import AnalyticsEvent  # noqa: E402
from analytics.store import insert_event  # noqa: E402


def _session(session_id: str, *names: str, at: str = "2026-08-14T10:00:00Z"):
    for name in names:
        insert_event(AnalyticsEvent(
            event_name=name, session_id=session_id, timestamp=at, properties={},
        ))


def test_empty_store_reports_zeroes_without_dividing_by_zero():
    o = calculate_overview()
    assert o["sessions"] == 0
    assert o["acceptance_rate"] == 0.0
    assert o["dlcr"] == 0.0
    assert all(s["sessions"] == 0 for s in o["stages"])


def test_counts_sessions_not_events():
    """Three scenario runs in one session are one session that reached it."""
    _session("s1", "onboarding_started", "scenario_opened",
             "scenario_opened", "scenario_opened")

    stages = {s["key"]: s["sessions"] for s in calculate_overview()["stages"]}
    assert stages["scenario_opened"] == 1


def test_decision_is_derived_from_accept_or_reject():
    _session("s1", "onboarding_started", "scenario_opened", "scenario_accepted")
    _session("s2", "onboarding_started", "scenario_opened", "scenario_rejected")
    _session("s3", "onboarding_started", "scenario_opened")

    o = calculate_overview()
    stages = {s["key"]: s["sessions"] for s in o["stages"]}
    assert stages["decision_made"] == 2
    assert o["accepted"] == 1 and o["rejected"] == 1
    assert o["acceptance_rate"] == 0.5
    assert o["dlcr"] == pytest.approx(2 / 3, rel=1e-3)


def test_conversion_is_from_the_previous_stage():
    for i in range(10):
        _session(f"s{i}", "onboarding_started")
    for i in range(5):
        _session(f"s{i}", "goal_created")
    for i in range(1):
        _session(f"s{i}", "snapshot_submitted")

    stages = {s["key"]: s for s in calculate_overview()["stages"]}
    assert stages["goal_created"]["conversion_from_previous"] == 0.5
    assert stages["snapshot_submitted"]["conversion_from_previous"] == 0.2
    assert stages["goal_created"]["share_of_all"] == 0.5


def test_biggest_drop_points_at_the_worst_step():
    for i in range(10):
        _session(f"s{i}", "onboarding_started", "goal_created")
    _session("s0", "snapshot_submitted")   # 10 → 1 is the cliff

    o = calculate_overview()
    assert o["biggest_drop"]["label"] == "Entered finances"
    assert o["biggest_drop"]["sessions_lost"] == 9
    assert o["biggest_drop"]["conversion"] == 0.1


def test_a_trailing_empty_stage_does_not_win_the_biggest_drop():
    """Ranking by ratio would pick 1 -> 0 (scores 0.0) over 10 -> 1 (scores
    0.1), and point at the stage nobody reached instead of the one that cost
    nine people."""
    for i in range(10):
        _session(f"s{i}", "onboarding_started", "goal_created")
    _session("s0", "snapshot_submitted")

    o = calculate_overview()
    stages = {s["key"]: s for s in o["stages"]}
    assert stages["baseline_generated"]["conversion_from_previous"] == 0.0
    assert o["biggest_drop"]["label"] != "Saw their runway"


def test_first_stage_has_no_conversion_ratio():
    _session("s1", "onboarding_started")
    assert calculate_overview()["stages"][0]["conversion_from_previous"] is None
