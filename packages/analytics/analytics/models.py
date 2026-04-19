from typing import Literal
from pydantic import BaseModel

EventName = Literal[
    "goal_created",
    "snapshot_submitted",
    "baseline_generated",
    "scenario_opened",
    "scenario_adjusted",
    "scenario_accepted",
    "scenario_rejected",
    "decision_loop_completed",
]


class AnalyticsEvent(BaseModel):
    event_name: str
    user_id: str = "demo-user"
    session_id: str
    timestamp: str
    properties: dict = {}
