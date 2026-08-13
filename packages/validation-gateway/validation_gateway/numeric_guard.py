"""
validation_gateway/numeric_guard.py
Numeric fidelity enforcement — the mechanism behind "AI never computes finances".

CONTRACT
--------
The ai-layer system prompt authorises the model to reference exactly five values:

    baseline_months, scenario_months, delta_months, monthly_change, adherence_rate

This module enforces exactly that contract. Every numeric token the model emits
must resolve to one of those values (or to a harmless natural-language count).
Anything else is unverified and forces the deterministic fallback.

WHY NOT A RANGE HEURISTIC
-------------------------
The previous implementation flagged integers in [3, 500] that did not match the
month values, and exempted anything prefixed with '$' or suffixed with '%'.
That let through the two categories the recommendation is actually made of:

    "Cut $900 of spending"     → money never checked
    "at 85% adherence"         → percentage never checked
    "your runway is 2 months"  → below the range floor
    "about eighteen months"    → digits only

and false-flagged legitimate formatting:

    "$1,200"                   → parsed as a bare 200

Whitelisting removes the guesswork: a number is either traceable to the engine
or it is not. Magnitude is irrelevant.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Tolerances. Money is compared to the cent; percentages to half a point, since
# the prompt renders adherence as a rounded integer.
_MONEY_TOL = 0.01
_PERCENT_TOL = 0.5

# Bare integers that carry no financial claim ("1 small change", "a couple").
# Anything attached to a unit is handled by the duration rules below, so this
# does not create a hole for "2 months".
_HARMLESS_BARE = frozenset({0, 1, 2})

_NUMBER_WORDS: dict[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
}

_MONTHS_PER = {"month": 1, "months": 1, "year": 12, "years": 12}

# Vague timeframes: not traceable to any engine value by construction.
_VAGUE_TIMEFRAME = re.compile(
    r"\b(?:a|half\s+a|about\s+a|roughly\s+a)\s+year\b"
    r"|\b(?:a\s+few|a\s+couple\s+of|several)\s+(?:months|years|weeks)\b",
    re.IGNORECASE,
)

_MONEY = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)|(\d[\d,]*(?:\.\d+)?)\s*(?:dollars|usd)\b", re.I)
_PERCENT = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(?:%|percent\b)", re.I)
_DURATION = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)[\s-]*(months?|years?|weeks?|days?)\b", re.I
)
_WORD_DURATION = re.compile(
    r"\b(" + "|".join(_NUMBER_WORDS) + r")[\s-]+(months?|years?|weeks?|days?)\b", re.I
)
_BARE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _to_float(raw: str) -> float:
    return float(raw.replace(",", ""))


@dataclass(frozen=True)
class AllowedValues:
    """The exact numeric surface the model is permitted to reproduce."""

    months: frozenset[int] = field(default_factory=frozenset)
    money: tuple[float, ...] = ()
    percent: tuple[float, ...] = ()

    def all_scalars(self) -> tuple[float, ...]:
        return tuple(self.months) + self.money + self.percent


@dataclass(frozen=True)
class Finding:
    kind: str      # "money" | "percent" | "duration" | "bare" | "vague"
    text: str      # the offending token as written
    value: float | None

    def describe(self, allowed: AllowedValues) -> str:
        if self.kind == "vague":
            return (
                f"Numeric hallucination — unverifiable timeframe {self.text!r}, "
                f"not derived from engine output (allowed months: {sorted(allowed.months)})"
            )
        return (
            f"Numeric hallucination — unverified {self.kind} value {self.text!r}, "
            f"not present in engine output (months={sorted(allowed.months)}, "
            f"money={list(allowed.money)}, percent={list(allowed.percent)})"
        )


def build_allowed(baseline, scenario) -> AllowedValues:
    """Derive the permitted numeric surface from engine truth.

    Only the five prompt-authorised values are included. Deliberately excludes
    monthly_cashflow, savings_rate and monthly_savings_gap: the prompt does not
    authorise them, so their appearance in AI text is a contract violation even
    though the engine computed them.
    """
    months: set[int] = set()
    for value in (
        getattr(baseline, "time_to_goal_months", None),
        getattr(scenario, "baseline_months", None),
        getattr(scenario, "scenario_months", None),
    ):
        if value is not None:
            months.add(int(value))

    delta = getattr(scenario, "delta_months", None)
    if delta is not None:
        months.add(abs(int(delta)))

    money: list[float] = []
    change = getattr(scenario, "effective_monthly_change", None)
    if change is not None:
        money.append(round(float(change), 2))

    percent: list[float] = []
    adherence = getattr(scenario, "adherence_rate", None)
    if adherence is not None:
        percent.append(round(float(adherence) * 100, 2))

    return AllowedValues(
        months=frozenset(months),
        money=tuple(sorted(set(money))),
        percent=tuple(sorted(set(percent))),
    )


def _matches(value: float, candidates, tol: float) -> bool:
    return any(abs(value - c) <= tol for c in candidates)


def find_unverified(text: str, allowed: AllowedValues) -> list[Finding]:
    """Return every numeric token in ``text`` that engine output cannot account for.

    Tokens are consumed in priority order (money → percent → duration → words),
    each match masked out of the string, so a single number is judged once under
    the most specific rule that applies.
    """
    findings: list[Finding] = []
    masked = text

    def mask(span: tuple[int, int], source: str) -> str:
        start, end = span
        return source[:start] + (" " * (end - start)) + source[end:]

    # 1. Money — must match monthly_change.
    for m in list(_MONEY.finditer(masked)):
        raw = m.group(1) or m.group(2)
        value = _to_float(raw)
        if not _matches(value, allowed.money, _MONEY_TOL):
            findings.append(Finding("money", m.group(0).strip(), value))
        masked = mask(m.span(), masked)

    # 2. Percent — must match adherence_rate.
    for m in list(_PERCENT.finditer(masked)):
        value = _to_float(m.group(1))
        if not _matches(value, allowed.percent, _PERCENT_TOL):
            findings.append(Finding("percent", m.group(0).strip(), value))
        masked = mask(m.span(), masked)

    # 3. Durations in digits — normalised to months. Weeks and days can never
    #    match an engine value, so they are always unverified.
    for m in list(_DURATION.finditer(masked)):
        value = _to_float(m.group(1))
        unit = m.group(2).lower()
        factor = _MONTHS_PER.get(unit if unit.endswith("s") else unit + "s")
        if factor is None:
            factor = _MONTHS_PER.get(unit)
        if factor is None:
            findings.append(Finding("duration", m.group(0).strip(), value))
        else:
            as_months = value * factor
            if not (as_months.is_integer() and int(as_months) in allowed.months):
                findings.append(Finding("duration", m.group(0).strip(), value))
        masked = mask(m.span(), masked)

    # 4. Durations written as words — the model does this constantly under a
    #    "plain language" instruction, and digit-only extraction misses it.
    for m in list(_WORD_DURATION.finditer(masked)):
        value = float(_NUMBER_WORDS[m.group(1).lower()])
        unit = m.group(2).lower()
        factor = _MONTHS_PER.get(unit if unit.endswith("s") else unit + "s")
        if factor is None or not float(value * factor).is_integer() or \
                int(value * factor) not in allowed.months:
            findings.append(Finding("duration", m.group(0).strip(), value))
        masked = mask(m.span(), masked)

    # 5. Vague timeframes — "about a year", "a few months".
    for m in list(_VAGUE_TIMEFRAME.finditer(masked)):
        findings.append(Finding("vague", m.group(0).strip(), None))
        masked = mask(m.span(), masked)

    # 6. Anything numeric left over must still trace back to an engine value.
    scalars = allowed.all_scalars()
    for m in _BARE.finditer(masked):
        value = _to_float(m.group(0))
        if value.is_integer() and int(value) in _HARMLESS_BARE:
            continue
        if _matches(value, scalars, _MONEY_TOL):
            continue
        findings.append(Finding("bare", m.group(0), value))

    return findings


def describe_all(findings: list[Finding], allowed: AllowedValues) -> list[str]:
    return [f.describe(allowed) for f in findings]
