# FinSight.ai

**How many months can you live on what you have?**

A runway calculator for founders and freelancers. A deterministic engine does
the arithmetic; an LLM only explains what the engine already computed, and
every figure it writes is verified against that engine output before it renders.

[Landing](https://finsight-landing.vercel.app) · [App](https://finsight-ai-tawny.vercel.app)

---

## The problem this is actually solving

The hard part of a financial AI product is not the model. It is that a
non-technical founder has no way to tell a correct number from a plausible one,
and one wrong figure about their own money costs you the user permanently.

So the AI is not allowed near the arithmetic:

```
User input
  → core-engine        deterministic maths: cashflow, runway, projection
  → scenario-engine    one behavioural "what if"
  → validation-gateway schema + numeric + language gates
  → ai-layer           the LLM explains; it never computes
  → UI
```

That is a product decision before it is an architectural one. It is also worth
nothing as a promise, so the rest of this README is about how it is enforced.

---

## How the guarantee is enforced

### Every number is checked against the engine

The system prompt authorises the model to reference exactly five values:
`baseline_months`, `scenario_months`, `delta_months`, `monthly_change`,
`adherence_rate`. `validation_gateway/numeric_guard.py` enforces exactly that
set — a whitelist, not a heuristic. Anything else fails and the user gets a
deterministic template instead.

Magnitude is irrelevant, and that matters. An earlier version flagged integers
in `[3, 500]` that did not match the month values, and exempted anything
prefixed `$` or suffixed `%`. It let through:

| Model output | Why it survived |
|---|---|
| `your runway is 2 months` | below the range floor — and an understated runway is the most damaging thing this product can say |
| `cut $900 of spending` | `$` was exempt, so the recommendation's own number was never checked |
| `at 85% adherence` | `%` was exempt |
| `roughly eighteen months` | digit-only extraction cannot see words |
| `about a year away` | no digits at all |

...and falsely rejected `$1,200`, splitting it on the comma into a hallucinated
"200 months". The guard now parses money, percentages, digit and word
durations, vague timeframes, and checks every model-authored field including
`reasoning` and `key_assumptions`.

### Advisor language is blocked, not requested

The prompt forbids "you should", "I recommend", "guaranteed", "financial
advisor". `language_guard.py` makes that a property of the system rather than
an instruction to the model: the blocking tier forces the fallback, softer
directives are scored instead. A prompt is a request; this is a gate.

### `/explain` cannot return 5xx

Not "does not" — cannot. Every provider exception funnels into one error type,
the router wraps the whole pipeline, and the client resolves lazily so a
missing API key degrades to deterministic output instead of raising at import
and taking `/health` down with the app.

---

## The eval suite

**56 frozen cases behind six CI gates** (`evals/`). It answers one question:
can a number the engine never produced reach the user, and can a number the
engine did produce be thrown away?

| Family | Cases | Measures |
|---|---|---|
| clean | 30 | **false rejection** — the gate discarding a correct answer |
| adversarial | 26 | **detection** — a wrong answer reaching the user |

Measuring only detection produces a brick wall: a gate that rejects everything
scores 100%. Measuring only false rejection produces a colander. The pair is
the point.

Adversarial cases are split by failure class — numeric (12), regulatory
language (5), schema (3), transport (6) — so a gap points at a rule rather than
at a number.

**The adversaries are not drawn from the defence.** The previous mock picked
the smallest integer in `[3, 500]` absent from engine output — precisely the
window the guard inspected. Built from the same assumption as the defence, it
could not have discovered that `"your runway is 2 months"` walked straight
through. The current cases were written without reference to how the guard
works, and the first run found a real gap.

```bash
make eval        # mock mode: free, offline, deterministic — the CI gate
make eval-live   # against a real model; the only run whose latency means anything
```

Gates: numeric / language / transport / schema detection = 100%, false
rejection ≤ 2%, p95 within the `/explain` SLA.

---

## Running it

```bash
pip install -r requirements.txt
uvicorn apps.api.main:app --reload --port 8000     # backend

cd apps/mobile && npx expo start --web             # frontend
```

Tests and gates:

```bash
pytest tests/ packages/ -q
FINSIGHT_FORCE_MOCK=1 python evals/run.py --mock
```

No API key required. Without one the AI layer serves deterministic explanations
and every endpoint keeps working — that is the same fallback path the gates
exercise, not a special dev mode.

Any OpenAI-compatible provider works (`FINSIGHT_LLM_BASE_URL` +
`FINSIGHT_LLM_MODEL`) — OpenAI, Groq, Cerebras, OpenRouter, a local Ollama —
because `ai_layer` only ever knows `.call(system, user)`.

Full environment reference: [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

---

## Layout

```
packages/
├── core-engine/         deterministic maths
├── scenario-engine/     behavioural simulation
├── ai-layer/            prompt, transport, mock — never computes
├── validation-gateway/  numeric guard, language guard, schema, quality scoring
├── shared-types/        Pydantic models + SLA budgets
└── analytics/           events, buckets, funnel
apps/
├── api/                 FastAPI
└── mobile/              React Native + Expo (web today)
evals/                   56 frozen cases + gates
```

Full ruleset: [`docs/system-rules.md`](docs/system-rules.md).

---

## On the data

Figures are **transmitted, not stored.** `/baseline` and `/scenario` receive
the real numbers because the engine runs server-side; nothing money-shaped is
persisted or logged. Analytics events carry bands — `cashflow_bucket:
"1000-2500"`, never `1450` — with matching edges in `analytics/buckets.py` and
`lib/analytics.ts`.

That distinction is deliberate. "Numbers never leave your browser" would
require shipping the engine to the client, which would mean two implementations
of the same arithmetic and a live risk of them disagreeing — against a product
whose entire premise is that the engine is the single source of truth.

---

## Status, honestly

Working: engine, scenario simulation, validation gates, eval suite, funnel
analytics, web app.

Not yet: no live users, so no behavioural data. Latency and fallback rates are
therefore **unmeasured against a real model** — the numbers exist only from
mock runs, which measure pipeline overhead rather than anything a user
experiences, and are not quoted here for that reason. Native builds are not
started.

---

## Author

Built by [Mark Kobets](https://github.com/Marckobic) — product and AI layer.

The parts worth reading if you are evaluating the thinking rather than the
feature list: `packages/validation-gateway/validation_gateway/numeric_guard.py`,
`evals/cases.py`, and `evals/README.md`.
