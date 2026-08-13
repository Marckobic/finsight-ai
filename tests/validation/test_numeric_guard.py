"""
tests/validation/test_numeric_guard.py
Unit tests for the numeric whitelist.

Each test names the production failure it prevents. The old range heuristic
passed all of the "escapes" below and failed the two "false positives".
"""

from shared_types.models import BaselineResult, ScenarioResult
from validation_gateway.numeric_guard import build_allowed, find_unverified


def _truth(baseline=24, scenario=18, delta=6, money=300.0, adherence=0.8):
    return (
        BaselineResult(
            monthly_cashflow=0.0, savings_rate=0.0,
            time_to_goal_months=baseline, monthly_savings_gap=0.0,
            goal_already_met=False,
        ),
        ScenarioResult(
            baseline_months=baseline, scenario_months=scenario, delta_months=delta,
            adherence_rate=adherence, effective_monthly_change=money,
            scenario_monthly_cashflow=0.0, is_improvement=delta > 0,
        ),
    )


def _check(text, **kw):
    allowed = build_allowed(*_truth(**kw))
    return find_unverified(text, allowed)


# --- escapes the old heuristic allowed -------------------------------------


def test_month_count_below_three_is_caught():
    assert _check("your runway is 2 months")


def test_month_count_above_five_hundred_is_caught():
    assert _check("that is 720 months away")


def test_fabricated_money_is_caught():
    assert _check("cut $900 of spending")


def test_fabricated_percent_is_caught():
    assert _check("at 45% adherence")


def test_word_numeral_with_wrong_value_is_caught():
    assert _check("roughly thirty months out")


def test_weeks_are_always_unverified():
    assert _check("about 26 weeks from now")


def test_vague_year_is_caught():
    assert _check("your goal is about a year away")


def test_fractional_month_is_caught():
    assert _check("roughly 17.5 months away")


def test_number_hidden_in_any_field_is_caught():
    """The gate reads every model-authored field, not just the two visible ones."""
    assert _check("income stays at $6,200 per month")


# --- false positives the old heuristic produced -----------------------------


def test_thousands_separator_is_not_split():
    assert not _check("set aside $1,200 monthly", money=1200.0)


def test_engine_money_is_accepted():
    assert not _check("a monthly change of $300")


def test_engine_percent_is_accepted():
    assert not _check("at 80% adherence")


def test_engine_months_are_accepted():
    assert not _check("shifts from 24 months to 18 months, a gap of 6 months")


def test_cents_are_accepted():
    assert not _check("a monthly change of $149.99", money=149.99)


def test_correct_word_numeral_is_not_blocked():
    """18 written as a word is a format issue, not a fabricated number.

    Blocking it would replace a numerically correct answer with boilerplate —
    the failure mode the false-rejection gate exists to catch.
    """
    assert not _check("about eighteen months out")


def test_small_bare_counts_are_allowed():
    assert not _check("start with 1 small change and 2 adjustments")


def test_year_form_resolves_to_months():
    assert not _check("that is 2 years away", baseline=24)


def test_empty_text_is_clean():
    assert not _check("")
