import os
import tempfile
import pytest

# Use a temp DB for tests
os.environ.setdefault("_ANALYTICS_TEST", "1")

import analytics.store as store_mod


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    db = str(tmp_path / "test_events.db")
    monkeypatch.setattr(store_mod, "_DB_PATH", db)


from analytics.models import AnalyticsEvent
from analytics.store import insert_event, get_events
from analytics.metrics import calculate_dlcr, calculate_funnel, calculate_session_summary


SESSION = "test-session-001"


def _event(name: str, props: dict = {}) -> AnalyticsEvent:
    return AnalyticsEvent(
        event_name=name,
        session_id=SESSION,
        timestamp="2026-04-17T10:00:00Z",
        properties=props,
    )


def test_insert_and_retrieve():
    insert_event(_event("goal_created"))
    events = get_events(SESSION)
    assert len(events) == 1
    assert events[0]["event_name"] == "goal_created"


def test_empty_session_returns_empty():
    assert get_events("no-such-session") == []


def test_dlcr_no_events():
    assert calculate_dlcr("empty-session") == 0.0


def test_dlcr_calculation():
    for _ in range(3):
        insert_event(_event("scenario_opened"))
    for _ in range(2):
        insert_event(_event("decision_loop_completed"))
    assert calculate_dlcr(SESSION) == pytest.approx(2 / 3)


def test_funnel_complete():
    for name in ["goal_created", "snapshot_submitted", "baseline_generated", "scenario_opened", "scenario_accepted"]:
        insert_event(_event(name))
    result = calculate_funnel(SESSION)
    assert all(result["stages"].values())
    assert result["drop_off"] is None


def test_funnel_drop_off():
    insert_event(_event("goal_created"))
    insert_event(_event("snapshot_submitted"))
    result = calculate_funnel(SESSION)
    assert result["stages"]["goal_created"] is True
    assert result["stages"]["snapshot_submitted"] is True
    assert result["stages"]["baseline_generated"] is False
    assert result["drop_off"] == "baseline_generated"


def test_session_summary():
    insert_event(_event("scenario_opened"))
    insert_event(_event("scenario_opened"))
    insert_event(_event("scenario_accepted", {"adherence": 80}))
    insert_event(_event("scenario_rejected", {"adherence": 40}))
    insert_event(_event("decision_loop_completed", {"outcome": "accepted"}))
    insert_event(_event("decision_loop_completed", {"outcome": "rejected"}))

    summary = calculate_session_summary(SESSION)
    assert summary["scenarios_opened"] == 2
    assert summary["scenarios_accepted"] == 1
    assert summary["scenarios_rejected"] == 1
    assert summary["acceptance_rate"] == pytest.approx(0.5)
    assert summary["avg_adherence_at_accept"] == pytest.approx(80.0)
    assert summary["avg_adherence_at_reject"] == pytest.approx(40.0)
    assert summary["dlcr"] == pytest.approx(1.0)
