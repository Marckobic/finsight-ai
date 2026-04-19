# validation_gateway — Hard Safety Layer
# RULE: ALL AI output MUST pass through this gate before reaching the UI.
# RULE: If validation fails, return the deterministic fallback template.
# RULE: Invalid data NEVER reaches the UI.
from validation_gateway.scorer import AIQualityScore, score_ai_output
from validation_gateway.health import AIHealthTracker, health_tracker

__all__ = [
    "AIQualityScore",
    "score_ai_output",
    "AIHealthTracker",
    "health_tracker",
]
