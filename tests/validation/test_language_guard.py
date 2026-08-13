"""
tests/validation/test_language_guard.py
Regulatory phrasing enforcement.

The system prompt already forbids this language. These tests are the difference
between forbidding it and preventing it: a prompt is a request to the model,
this is a property of the system.
"""

from validation_gateway.language_guard import find_advisory, find_blocking


def test_you_should_is_blocking():
    assert find_blocking("You should increase your savings.")


def test_first_person_advice_is_blocking():
    assert find_blocking("I recommend keeping this change.")
    assert find_blocking("We advise holding the contribution.")


def test_advisor_framing_is_blocking():
    assert find_blocking("As your financial advisor, keep this in place.")


def test_guarantee_language_is_blocking():
    assert find_blocking("This guaranteed approach reaches the goal.")
    assert find_blocking("A risk-free way to close the gap.")


def test_investment_advice_is_blocking():
    assert find_blocking("Invest in stocks to close the gap faster.")


def test_hedged_engine_phrasing_is_clean():
    """The phrasing the prompt actually asks for must survive."""
    assert not find_blocking(
        "Based on these figures, at this rate the timeline shifts from 24 months "
        "to 18 months if this change is maintained."
    )


def test_soft_directives_are_advisory_not_blocking():
    """Scored, not blocked: hard-gating these raises fallbacks without
    reducing regulatory exposure."""
    assert not find_blocking("Consider keeping the change in place.")
    assert find_advisory("Consider keeping the change in place.")


def test_case_insensitive():
    assert find_blocking("YOU SHOULD save more.")
