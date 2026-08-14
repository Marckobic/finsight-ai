"""
tests/analytics/test_buckets.py
Nothing money-shaped survives bucketing.

The point is not that the bands are correct — bands are arbitrary. The point is
that no code path can round-trip a value back out, which is the property the
landing page's privacy claim rests on.
"""

from analytics.buckets import money_bucket, months_bucket, percent_bucket


def test_money_bands():
    assert money_bucket(0) == "0"
    assert money_bucket(1) == "1-250"
    assert money_bucket(250) == "1-250"
    assert money_bucket(250.01) == "250-500"
    assert money_bucket(1450) == "1000-2500"
    assert money_bucket(99999) == "10000+"


def test_negative_cashflow_is_its_own_band():
    """Burning more than you earn is the most important segment in the funnel
    and must not be lumped in with zero."""
    assert money_bucket(-1) == "negative"
    assert money_bucket(-5000) == "negative"


def test_percent_bands():
    assert percent_bucket(0) == "0"
    assert percent_bucket(4.9) == "0-5"
    assert percent_bucket(35) == "30-50"
    assert percent_bucket(90) == "50+"


def test_months_bands():
    assert months_bucket(2) == "0-3"
    assert months_bucket(18) == "12-24"
    assert months_bucket(600) == "60+"
    assert months_bucket(-1) == "unreachable"


def test_missing_and_malformed_values_never_raise():
    for value in (None, float("nan"), "abc", ""):
        assert money_bucket(value) == "unknown"
        assert percent_bucket(value) == "unknown"


def test_a_bucket_never_contains_the_input():
    """No band label may echo an amount that is not one of its own edges."""
    for amount in (1450.55, 6200.0, 12345.67, 299.5):
        label = money_bucket(amount)
        assert str(int(amount)) not in label
        assert str(amount) not in label
