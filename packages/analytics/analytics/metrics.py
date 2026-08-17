import json

from .store import get_all_events, get_events


def calculate_dlcr(session_id: str) -> float:
    events = get_events(session_id)
    opened = sum(1 for e in events if e["event_name"] == "scenario_opened")
    if opened == 0:
        return 0.0
    completed = sum(1 for e in events if e["event_name"] == "decision_loop_completed")
    return completed / opened


def calculate_funnel(session_id: str) -> dict:
    events = get_events(session_id)
    names = {e["event_name"] for e in events}

    decision_made = "scenario_accepted" in names or "scenario_rejected" in names

    stages = {
        "goal_created": "goal_created" in names,
        "snapshot_submitted": "snapshot_submitted" in names,
        "baseline_generated": "baseline_generated" in names,
        "scenario_opened": "scenario_opened" in names,
        "decision_made": decision_made,
    }

    drop_off = next((k for k, v in stages.items() if not v), None)
    return {"stages": stages, "drop_off": drop_off}


def calculate_session_summary(session_id: str) -> dict:
    events = get_events(session_id)

    opened = sum(1 for e in events if e["event_name"] == "scenario_opened")
    accepted = sum(1 for e in events if e["event_name"] == "scenario_accepted")
    rejected = sum(1 for e in events if e["event_name"] == "scenario_rejected")

    acceptance_rate = (accepted / (accepted + rejected)) if (accepted + rejected) > 0 else 0.0

    def _adherences(event_name: str) -> list[float]:
        vals = []
        for e in events:
            if e["event_name"] == event_name:
                props = json.loads(e["properties"]) if isinstance(e["properties"], str) else e["properties"]
                if "adherence" in props:
                    vals.append(float(props["adherence"]))
        return vals

    accept_adherences = _adherences("scenario_accepted")
    reject_adherences = _adherences("scenario_rejected")

    avg_accept = sum(accept_adherences) / len(accept_adherences) if accept_adherences else 0.0
    avg_reject = sum(reject_adherences) / len(reject_adherences) if reject_adherences else 0.0

    return {
        "scenarios_opened": opened,
        "scenarios_accepted": accepted,
        "scenarios_rejected": rejected,
        "acceptance_rate": acceptance_rate,
        "dlcr": calculate_dlcr(session_id),
        "funnel": calculate_funnel(session_id),
        "avg_adherence_at_accept": avg_accept,
        "avg_adherence_at_reject": avg_reject,
    }


# ---------------------------------------------------------------------------
# Cross-session overview
# ---------------------------------------------------------------------------

_FUNNEL_STAGES: tuple[tuple[str, str], ...] = (
    ("onboarding_started", "Opened the app"),
    ("goal_created", "Set a goal"),
    ("snapshot_submitted", "Entered finances"),
    ("baseline_generated", "Saw their runway"),
    ("scenario_opened", "Ran a scenario"),
    ("decision_made", "Made a decision"),
)


def calculate_overview() -> dict:
    """Funnel across every session, not one.

    The per-session endpoints answer "what did this person do", which is
    unanswerable in practice: you would have to collect a session_id from each
    tester by hand. This answers "where do people fall out", which is the only
    question a demo round is actually asked.

    Counts are sessions that reached a stage, not events — three scenario runs
    in one session are one session that reached the scenario.
    """
    events = get_all_events()

    by_session: dict[str, set[str]] = {}
    timestamps: list[str] = []
    for event in events:
        by_session.setdefault(event["session_id"], set()).add(event["event_name"])
        if event.get("created_at"):
            timestamps.append(event["created_at"])

    for names in by_session.values():
        if "scenario_accepted" in names or "scenario_rejected" in names:
            names.add("decision_made")

    sessions = len(by_session)
    stages = []
    previous: int | None = None
    for key, label in _FUNNEL_STAGES:
        reached = sum(1 for names in by_session.values() if key in names)
        stages.append({
            "key": key,
            "label": label,
            "sessions": reached,
            "share_of_all": round(reached / sessions, 4) if sessions else 0.0,
            # Conversion from the previous stage is what points at the leak;
            # share of all only tells you the cumulative damage.
            "conversion_from_previous": (
                round(reached / previous, 4) if previous else None
            ),
        })
        previous = reached

    # Biggest drop by sessions LOST, not by the worst ratio. A ratio picks the
    # wrong stage on small samples: with 10 → 1 → 0, the 1 → 0 step scores 0.0
    # and wins, while the step that actually cost you nine people scores 0.1.
    # Absolute loss ranks them the way a person reading the funnel would.
    worst = None
    worst_lost = 0
    running = None
    for stage in stages:
        if running is not None:
            lost = running - stage["sessions"]
            if lost > worst_lost:
                worst_lost = lost
                worst = stage
        running = stage["sessions"]

    accepted = sum(1 for n in by_session.values() if "scenario_accepted" in n)
    rejected = sum(1 for n in by_session.values() if "scenario_rejected" in n)
    opened = sum(1 for n in by_session.values() if "scenario_opened" in n)
    decided = accepted + rejected

    return {
        "sessions": sessions,
        "events": len(events),
        "first_event_at": min(timestamps) if timestamps else None,
        "last_event_at": max(timestamps) if timestamps else None,
        "stages": stages,
        "biggest_drop": (
            {
                "label": worst["label"],
                "sessions_lost": worst_lost,
                "conversion": worst["conversion_from_previous"],
            }
            if worst else None
        ),
        "scenarios_opened": opened,
        "decisions": decided,
        "accepted": accepted,
        "rejected": rejected,
        "acceptance_rate": round(accepted / decided, 4) if decided else 0.0,
        "dlcr": round(decided / opened, 4) if opened else 0.0,
    }
