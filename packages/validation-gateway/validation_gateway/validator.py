"""
validation_gateway/validator.py
Hard safety layer — sits between the AI layer and the UI.

This is a MANDATORY gate. No AI output reaches the UI without passing here.

Checks performed:
  1. Schema validation (Pydantic — required fields, correct types)
  2. Non-empty content (recommendation and explanation must not be blank)
  3. Numeric consistency (AI must not reference numbers inconsistent with engine output)
  4. Financial input sanity (user-submitted data validation, Screen 3)

Failure behavior:
  - Any check fails → valid=False, fallback_used=True
  - Fallback is a deterministic template (never None when fallback_used=True)
  - Failure event is logged for CI hallucination rate tracking

CI gate (PRD Section 16):
  - Build fails if hallucination_rate > 1% across the ≥50 test case suite
  - Schema failure rate must also stay < 1%
"""

import math
import re

from pydantic import ValidationError
from shared_types.models import (
    AIExplanationOutput,
    BaselineResult,
    ScenarioResult,
    ValidationResult,
)

# ---------------------------------------------------------------------------
# Fallback template (deterministic — no AI generated)
# ---------------------------------------------------------------------------

_FALLBACK_RECOMMENDATION = "Adjust your monthly savings contribution as shown."

_FALLBACK_EXPLANATION = (
    "Based on your financial data, this change could improve your progress "
    "toward your goal. Refer to the figures above for the precise impact on "
    "your timeline."
)


def _fallback_output() -> AIExplanationOutput:
    """Return the deterministic fallback template. Used when AI output is invalid."""
    return AIExplanationOutput(
        recommendation=_FALLBACK_RECOMMENDATION,
        explanation=_FALLBACK_EXPLANATION,
    )


# ---------------------------------------------------------------------------
# Scenario Output Validation
# ---------------------------------------------------------------------------


def validate_scenario_output(scenario_result) -> ValidationResult:
    """
    Validate ScenarioResult from the scenario engine. MANDATORY gate.

    Checks (in order — fail-fast):
      1. Schema: all required fields present with correct types
      2. NaN / Infinity: no float field may hold nan or inf
      3. Adherence bounds: adherence_rate must be in [0.1, 0.95]
      4. Non-negative effective change: effective_monthly_change >= 0
      5. Month sanity: scenario_months (if set) must be > 0 and < 1200
      6. Delta consistency: delta_months == baseline_months - scenario_months
      7. is_improvement consistency: mirrors delta direction

    Args:
        scenario_result: ScenarioResult object or raw dict from the engine.

    Returns:
        ValidationResult.
          valid=True  → validated_output=None (scenario data passes through).
          valid=False → fallback_used=True, validated_output=fallback template.
    """
    errors: list[str] = []

    # --- Check 1: Schema validation ---
    if isinstance(scenario_result, ScenarioResult):
        sr = scenario_result
    else:
        try:
            if isinstance(scenario_result, dict):
                sr = ScenarioResult(**scenario_result)
            else:
                sr = ScenarioResult.model_validate(scenario_result)
        except (ValidationError, TypeError, Exception) as exc:
            errors.append(f"Schema validation failed: {exc}")
            return ValidationResult(
                valid=False,
                errors=errors,
                fallback_used=True,
                validated_output=_fallback_output(),
            )

    # --- Check 2: NaN / Infinity on float fields ---
    _float_fields = {
        "adherence_rate": sr.adherence_rate,
        "effective_monthly_change": sr.effective_monthly_change,
        "scenario_monthly_cashflow": sr.scenario_monthly_cashflow,
    }
    for field_name, value in _float_fields.items():
        if math.isnan(value) or math.isinf(value):
            errors.append(
                f"{field_name} contains an invalid numeric value (NaN or Infinity)"
            )

    if errors:
        return ValidationResult(
            valid=False,
            errors=errors,
            fallback_used=True,
            validated_output=_fallback_output(),
        )

    # --- Check 3: Adherence bounds [0.1, 0.95] ---
    if not (0.1 <= sr.adherence_rate <= 0.95):
        errors.append(
            f"adherence_rate must be in [0.1, 0.95], got {sr.adherence_rate}"
        )
        return ValidationResult(
            valid=False,
            errors=errors,
            fallback_used=True,
            validated_output=_fallback_output(),
        )

    # --- Check 4: Non-negative effective change ---
    if sr.effective_monthly_change < 0:
        errors.append(
            f"effective_monthly_change must be >= 0, got {sr.effective_monthly_change}"
        )
        return ValidationResult(
            valid=False,
            errors=errors,
            fallback_used=True,
            validated_output=_fallback_output(),
        )

    # --- Check 5: Month sanity ---
    if sr.scenario_months is not None:
        if sr.scenario_months <= 0 or sr.scenario_months >= 1200:
            errors.append(
                f"scenario_months must be > 0 and < 1200, got {sr.scenario_months}"
            )
            return ValidationResult(
                valid=False,
                errors=errors,
                fallback_used=True,
                validated_output=_fallback_output(),
            )

    # --- Check 6: Delta consistency ---
    if sr.baseline_months is not None and sr.scenario_months is not None:
        expected_delta = sr.baseline_months - sr.scenario_months
        if sr.delta_months != expected_delta:
            errors.append(
                f"delta_months ({sr.delta_months}) must equal "
                f"baseline_months ({sr.baseline_months}) - "
                f"scenario_months ({sr.scenario_months}) = {expected_delta}"
            )
            return ValidationResult(
                valid=False,
                errors=errors,
                fallback_used=True,
                validated_output=_fallback_output(),
            )

    # --- Check 7: is_improvement consistency ---
    if sr.delta_months is not None:
        baseline_reachable = sr.baseline_months is not None
        if sr.delta_months > 0 and not sr.is_improvement:
            errors.append(
                f"is_improvement must be True when delta_months > 0 "
                f"(delta_months={sr.delta_months})"
            )
        elif sr.delta_months <= 0 and baseline_reachable and sr.is_improvement:
            errors.append(
                f"is_improvement must be False when delta_months <= 0 "
                f"and baseline was reachable (delta_months={sr.delta_months})"
            )

    if errors:
        return ValidationResult(
            valid=False,
            errors=errors,
            fallback_used=True,
            validated_output=_fallback_output(),
        )

    # All checks passed — scenario data proceeds to the AI layer
    return ValidationResult(
        valid=True,
        errors=[],
        fallback_used=False,
        validated_output=None,
    )


# ---------------------------------------------------------------------------
# AI Output Validation
# ---------------------------------------------------------------------------


def validate_ai_output(
    raw_output: dict,
    baseline: BaselineResult,
    scenario: ScenarioResult,
) -> ValidationResult:
    """
    Validate AI layer output. This is a HARD GATE — failure blocks UI rendering.

    Checks (in order):
      1. Schema: raw_output must match AIExplanationOutput shape
      2. Non-empty: recommendation and explanation must be non-blank strings
      3. Numeric consistency: AI text must not contain fabricated month counts

    Args:
        raw_output: Raw dict from the AI layer.
        baseline: Baseline result from the deterministic engine (truth).
        scenario: Scenario result from the scenario engine (truth).

    Returns:
        ValidationResult.
          valid=True  → validated_output contains the verified AI output.
          valid=False → fallback_used=True, validated_output contains fallback template.
    """
    errors: list[str] = []

    # --- Check 1: Schema validation ---
    try:
        validated = AIExplanationOutput(**raw_output)
    except (ValidationError, TypeError, KeyError) as exc:
        errors.append(f"Schema validation failed: {exc}")
        return ValidationResult(
            valid=False,
            errors=errors,
            fallback_used=True,
            validated_output=_fallback_output(),
        )

    # --- Check 2: Non-empty content ---
    if not validated.recommendation or not validated.recommendation.strip():
        errors.append("recommendation field is empty or whitespace-only")

    if not validated.explanation or not validated.explanation.strip():
        errors.append("explanation field is empty or whitespace-only")

    if errors:
        return ValidationResult(
            valid=False,
            errors=errors,
            fallback_used=True,
            validated_output=_fallback_output(),
        )

    # --- Check 3: Numeric consistency (hallucination detection) ---
    hallucination_errors = _check_hallucinated_month_values(
        validated, baseline, scenario
    )

    if hallucination_errors:
        errors.extend(hallucination_errors)
        return ValidationResult(
            valid=False,
            errors=errors,
            fallback_used=True,
            validated_output=_fallback_output(),
        )

    # All checks passed
    return ValidationResult(
        valid=True,
        errors=[],
        fallback_used=False,
        validated_output=validated,
    )


def _check_hallucinated_month_values(
    output: AIExplanationOutput,
    baseline: BaselineResult,
    scenario: ScenarioResult,
) -> list[str]:
    """
    Detect hallucinated month values in AI text output.

    Strategy: Extract all standalone integers from AI text. Flag any integer
    that looks like a month count (> 2, < 500) but does not match engine outputs.

    This is a heuristic first layer. Full hallucination detection is enforced
    by the ≥50-case CI regression suite (PRD Section 16).

    Args:
        output: Validated AIExplanationOutput to check.
        baseline: Truth layer baseline result.
        scenario: Truth layer scenario result.

    Returns:
        List of error strings if hallucinated values detected. Empty list if clean.
    """
    errors: list[str] = []

    # Collect all integers from AI text
    text = f"{output.recommendation} {output.explanation}"
    numbers_in_text = [int(n) for n in re.findall(r'\b(\d+)\b', text)]

    # Build the set of valid numbers from engine outputs (truth layer)
    valid_engine_values: set[int] = set()

    if baseline.time_to_goal_months is not None:
        valid_engine_values.add(baseline.time_to_goal_months)
    if scenario.baseline_months is not None:
        valid_engine_values.add(scenario.baseline_months)
    if scenario.scenario_months is not None:
        valid_engine_values.add(scenario.scenario_months)
    if scenario.delta_months is not None:
        valid_engine_values.add(abs(scenario.delta_months))

    # Also allow small common numbers (days of week, round percentages, etc.)
    # and large USD values — we only flag suspicious month-range integers
    for num in numbers_in_text:
        # Numbers in the "month count" range (3–500) that don't match engine truth
        if 3 <= num <= 500 and num not in valid_engine_values:
            # Additional heuristic: skip if preceded by '$' (dollar amount)
            pattern = rf'\${num}\b|\b{num}%'
            if not re.search(pattern, text):
                errors.append(
                    f"Potential hallucinated value: {num} months not found in engine "
                    f"outputs (valid: {sorted(valid_engine_values)})"
                )

    return errors


# ---------------------------------------------------------------------------
# Financial Input Validation (Screen 3 — PRD Section 10.1)
# ---------------------------------------------------------------------------


def validate_financial_inputs(
    income: float,
    fixed_expenses: float,
    variable_expenses: float,
    current_savings: float,
    monthly_savings_contribution: float,
    goal_amount: float,
) -> ValidationResult:
    """
    Validate user-submitted financial inputs from Screen 3.

    Rules (PRD Section 10.1):
      - All values must be non-negative floats
      - income must be > 0
      - current_savings must be >= 0
      - goal_amount must be > 0
      - fixed + variable > income × 3 → sanity warning (non-blocking)

    Args:
        income: Monthly take-home income (USD).
        fixed_expenses: Monthly fixed expenses (USD).
        variable_expenses: Monthly variable expenses (USD).
        current_savings: Current savings balance (USD).
        monthly_savings_contribution: Current monthly savings contribution (USD).
        goal_amount: Financial goal target amount (USD).

    Returns:
        ValidationResult.
          valid=True  → inputs are acceptable (errors may contain sanity warnings).
          valid=False → hard validation failure, errors contains blocking issues.
    """
    errors: list[str] = []

    # Hard validation rules
    if income <= 0:
        errors.append("income must be greater than $0")
    if fixed_expenses < 0:
        errors.append("fixed_expenses must be >= 0")
    if variable_expenses < 0:
        errors.append("variable_expenses must be >= 0")
    if current_savings < 0:
        errors.append("current_savings cannot be negative")
    if monthly_savings_contribution < 0:
        errors.append("monthly_savings_contribution must be >= 0")
    if goal_amount <= 0:
        errors.append("goal_amount must be greater than $0")

    if errors:
        return ValidationResult(
            valid=False,
            errors=errors,
            fallback_used=False,
            validated_output=None,
        )

    # Sanity warnings (non-blocking — flag for review, do not reject)
    warnings: list[str] = []
    total_expenses = fixed_expenses + variable_expenses
    if income > 0 and total_expenses > income * 3:
        warnings.append(
            f"Total expenses (${total_expenses:,.0f}) exceed 3× income "
            f"(${income * 3:,.0f}). Please verify your inputs."
        )

    return ValidationResult(
        valid=True,
        errors=warnings,  # sanity warnings, not blocking errors
        fallback_used=False,
        validated_output=None,
    )
