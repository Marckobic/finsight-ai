# validation_gateway — Hard Safety Layer
# RULE: ALL AI output MUST pass through this gate before reaching the UI.
# RULE: If validation fails, return the deterministic fallback template.
# RULE: Invalid data NEVER reaches the UI.
from validation_gateway.health import AIHealthTracker, health_tracker
from validation_gateway.language_guard import find_advisory, find_blocking
from validation_gateway.numeric_guard import AllowedValues, build_allowed, find_unverified
from validation_gateway.scorer import AIQualityScore, score_ai_output

__all__ = [
    "AIQualityScore",
    "score_ai_output",
    "AIHealthTracker",
    "health_tracker",
    "AllowedValues",
    "build_allowed",
    "find_unverified",
    "find_advisory",
    "find_blocking",
]
