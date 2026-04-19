import json
from .store import get_events


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
