"""
apps/api/events.py
Structured event logging — stdout as JSON.

All engine events are written here for Phase 3 analytics ingestion.
No DB in MVP — log lines are the persistence layer.

Events emitted:
  BASELINE_COMPUTED          → cashflow / savings_rate / time_to_goal
  SCENARIO_SIMULATED         → delta / adherence / behavior_type
  AI_EXPLANATION_GENERATED   → fallback_used / valid
  RECOMMENDATION_ACCEPTED    → user_id / scenario_delta
  RECOMMENDATION_REJECTED    → user_id
"""

import json
import sys
from datetime import datetime, timezone


def log_event(event_type: str, payload: dict) -> None:
    """
    Write a structured event record to stdout.

    Args:
        event_type: Upper-snake-case event name (e.g. "BASELINE_COMPUTED").
        payload:    Key/value context for the event.
    """
    record = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    print(json.dumps(record), flush=True)
