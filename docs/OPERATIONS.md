# Operations

Everything the backend reads from the environment, and what happens when it is
missing. The design rule throughout: **a missing variable degrades the product,
it never takes the service down.**

## Backend (Railway)

| Variable | Default | Effect when unset |
|---|---|---|
| `FINSIGHT_LLM_API_KEY` / `OPENAI_API_KEY` | — | AI layer serves deterministic mock output. `/explain` keeps returning 200. |
| `FINSIGHT_LLM_BASE_URL` | OpenAI | Point at any OpenAI-compatible provider (see below). |
| `FINSIGHT_FORCE_MOCK` | unset | Set to `1` to pin the mock even with a key present. CI and the eval suite use this to stay free and offline. |
| `FINSIGHT_LLM_MODEL` | `gpt-4o-mini` | **Required** when `FINSIGHT_LLM_BASE_URL` is set. |
| `FINSIGHT_LLM_DEADLINE_MS` | 80 % of the `/explain` SLA (2400 ms) | — |
| `FINSIGHT_DB_PATH` | `./.data/finsight_events.db` | **Set this to a mounted volume in production.** See below. |
| `FINSIGHT_ALLOWED_ORIGINS` | `*` | Comma-separated origin list to lock CORS down without a code change. |
| `FINSIGHT_EXPLAIN_IP_HOURLY` | 20 | Per-IP `/explain` calls per hour before 429. |
| `FINSIGHT_ANALYTICS_TOKEN` | — | **Required to read analytics.** Unset, every `/analytics/*` endpoint returns 503. |
| `FINSIGHT_EXPLAIN_DAILY_BUDGET` | 2000 | Global paid calls per day. Past the cap the endpoint serves the deterministic template — the product degrades, the bill does not. |

### Using a provider other than OpenAI

`ai_layer` knows only `.call(system, user)`, so any OpenAI-compatible endpoint
works without touching the pipeline — Groq, Cerebras, OpenRouter, Together, a
local Ollama. Two variables:

```
FINSIGHT_LLM_BASE_URL=https://api.groq.com/openai/v1
FINSIGHT_LLM_API_KEY=gsk_...
FINSIGHT_LLM_MODEL=llama-3.3-70b-versatile
```

The model name is **required** with a custom base URL and the client refuses to
start without it. Defaulting to `gpt-4o-mini` against a provider that has never
heard of it would 404 every request, and the transport would faithfully turn
each 404 into a deterministic fallback — a product quietly serving templates,
with nothing in the response to say why.

Two things to keep in mind when switching provider:

* **JSON mode.** The client sends `response_format={"type": "json_object"}` and
  refuses to call when the prompt lacks the word "json". Both OpenAI and Groq
  require the instruction to be in the prompt, and the system prompt satisfies
  it — `test_the_system_prompt_satisfies_json_mode` pins that.
* **Rate limits.** Free tiers are tight (Groq: 30 requests/minute at the time of
  writing). A 429 arrives as `openai.RateLimitError`, which the client treats as
  transient: one retry inside the deadline, then the deterministic fallback. The
  product degrades, it does not break — but set `FINSIGHT_EXPLAIN_DAILY_BUDGET`
  below the provider's daily cap so your own limiter trips first and the reason
  shows up in the logs.

### Reading the analytics

`GET /analytics/dashboard?token=…` is a single page you can open on a phone:
session counts, the funnel by stage, conversion from the previous stage, and
which step lost the most people. `GET /analytics/overview?token=…` is the same
data as JSON.

Everything under `/analytics/*` is behind `FINSIGHT_ANALYTICS_TOKEN`. With the
variable unset the endpoints return 503 rather than serving openly: these
responses describe real people's behaviour, the API is public, and "open unless
someone remembers to configure it" is how internal dashboards end up indexed.

The token is accepted as `?token=` as well as an `X-Analytics-Token` header,
because the point is opening it on a phone. A query token leaks into browser
history and proxy logs — fine for a personal dashboard over a demo round, not a
pattern to carry further.

Generate one with `python -c "import secrets;print(secrets.token_urlsafe(32))"`.

### What is stored about a user

Nothing money-shaped. Amounts are coarsened to bands
(`analytics/buckets.py` and the matching helpers in `lib/analytics.ts`) before
they are stored or logged: `cashflow_bucket: "1000-2500"`, never `1450`. The
`/baseline` stdout log was carrying the user's cashflow and savings rate next to
their `user_id`; it now carries bands.

What buckets do **not** change: `/baseline` and `/scenario` receive the real
figures, because the engine runs server-side. Transmission is inherent to the
architecture, persistence is not. The accurate public claim is **"we do not
store your financial data"** — the landing page's "numbers stay in-session only"
implies they never leave the browser, which was never true and cannot be made
true without moving the engine into the client.

### The analytics volume

`FINSIGHT_DB_PATH` defaulted to `/tmp/finsight_events.db`. On Railway the
container filesystem is ephemeral: `/tmp` is wiped on every deploy and every
restart. Events were accepted, indexed and served by `/analytics/*` — and
silently erased, with nothing anywhere indicating the loss.

Attach a Railway volume and point the variable at it:

```
FINSIGHT_DB_PATH=/data/finsight_events.db
```

Without a volume, treat `/analytics/*` as a live probe of the current replica,
not as a record of anything.

### Cost control

Rate limiting is in-process and therefore per-replica: two replicas allow twice
the traffic. That is a deliberate MVP trade, not an oversight — set the budget
accordingly and keep a hard monthly spend cap on the OpenAI account as the real
backstop. `/analytics/ai-health` reports `daily_ai_budget` so the remaining
allowance is visible without reading logs.

## Frontend (Vercel)

| Variable | Notes |
|---|---|
| `EXPO_PUBLIC_API_URL` | **Required in production.** |
| `EXPO_PUBLIC_POSTHOG_KEY` | Optional; activates PostHog in `lib/analytics.ts`. |

`EXPO_PUBLIC_*` values are inlined at **build** time. Editing `apps/mobile/.env`
does not change a deployed app: set the variable in the Vercel project settings
and redeploy. There is no longer a localhost fallback in production builds — a
missing value throws at startup rather than shipping an app that points at a
developer's laptop, which is what made every deployed request fail at the most
expensive step, immediately after the user entered their finances.

## Health and metrics

`GET /analytics/ai-health` returns:

```
numeric_fidelity_rate   share of responses where every figure traced to engine output
fallback_rate_observed  share served from the deterministic template
latency_p50_ms          measured, per replica
latency_p95_ms          measured, per replica
daily_ai_budget         used / limit / remaining
```

These are per-process and reset on deploy. Read them as a live probe.

## Before quoting a latency number

Run the eval suite in live mode:

```bash
OPENAI_API_KEY=... make eval-live
```

Mock-mode latency is pipeline overhead, not user-observed latency. The report
labels which mode produced it, precisely so the two are never conflated again.
