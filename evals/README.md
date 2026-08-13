# AI layer evaluation suite

56 frozen cases behind a CI gate. Answers one question: **can a number the
engine never produced reach the user, and can a number the engine did produce
be thrown away?**

```bash
make eval                      # mock mode — free, offline, deterministic
make eval-live                 # real model, needs OPENAI_API_KEY
python evals/run.py --verbose  # show every gateway rejection
```

Exit code is non-zero when any gate fails, so `evals/run.py` is the gate, not a
report about one. `tests/test_evals.py` runs the same suite under pytest.

## Two families, because a guard fails in two directions

| Family | Cases | Measures | Failure it catches |
|---|---|---|---|
| **clean** | 30 | false rejection | the gate discarding a *correct* answer and silently serving boilerplate |
| **adversarial** | 26 | detection | a *wrong* answer reaching the user |

Measuring only detection produces a brick wall — a gate that rejects
everything scores 100%. Measuring only false rejection produces a colander.
The pair is the point.

Adversarial cases are split by failure family so a gap points at a rule rather
than at a number:

- **numeric** (12) — fabricated months, understated runway, invented money and
  percentages, word numerals, vague timeframes, comma-formatted amounts,
  fractional months, weeks, off-by-one, and figures hidden in `reasoning` or
  `key_assumptions`
- **language** (5) — advisor framing, first-person advice, guarantees,
  investment suggestions
- **schema** (3) — blank fields, missing fields, wrong types
- **transport** (6) — non-JSON, JSON array, timeout, connection error, rate
  limit, empty completion

## Gates

| Gate | Threshold | Why this number |
|---|---|---|
| numeric detection | = 1.0 | A fabricated figure in a financial product has no acceptable rate. One escape invalidates the core claim. |
| language detection | = 1.0 | Advisor and guarantee phrasing is the regulatory exposure. |
| transport containment | = 1.0 | Every provider failure must surface as the deterministic template. This is "/explain never returns 5xx" as a measurement. |
| schema compliance | = 1.0 | Everything reaching the UI is schema-valid by construction. |
| false rejection | ≤ 0.02 | Small allowance for genuinely ambiguous phrasing, not for systematic over-blocking. |
| p95 latency | ≤ 3000 ms | The same budget `TimingMiddleware` warns on, from `shared_types.sla`. |

## Mock mode vs live mode

The report always prints which mode it ran in, and the mock-mode latency line
says explicitly that the number is pipeline overhead rather than user-observed
latency.

This is not a formality. Before this suite existed, the project's headline
metrics — "< 3 s latency", "~95 % schema compliance" — were measured against
`MockLLMClient(mode="valid")`, a client that answers instantly and by
construction cannot produce invalid output. Neither number described anything
that had happened. Quote latency only from a `--live` run.

## Adversaries are not drawn from the defence

The previous `MockLLMClient("hallucination")` picked the smallest integer in
`[3, 500]` absent from engine output — the exact window the guard inspected.
The adversary was built from the same assumption as the defence, so the suite
could not discover that `"your runway is 2 months"` walked straight through.

Every adversary here reproduces a failure mode reachable by a real model under
this prompt, chosen without reference to how the guard works.

## Adding a case

Clean cases are input tuples in `cases.py`. Adversarial cases need an entry in
`_ADVERSARIAL_SPECS` and a builder in `adversaries.py`. Cases must stay frozen:
anything that varies between runs cannot be a regression gate.
