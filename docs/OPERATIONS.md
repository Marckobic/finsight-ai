# Operations

Everything the backend reads from the environment, and what happens when it is
missing. The design rule throughout: **a missing variable degrades the product,
it never takes the service down.**

## Backend (Railway)

| Variable | Default | Effect when unset |
|---|---|---|
| `OPENAI_API_KEY` | — | AI layer serves deterministic mock output. `/explain` keeps returning 200. |
| `FINSIGHT_FORCE_MOCK` | unset | Set to `1` to pin the mock even with a key present. CI and the eval suite use this to stay free and offline. |
| `FINSIGHT_LLM_MODEL` | `gpt-4o-mini` | — |
| `FINSIGHT_LLM_DEADLINE_MS` | 80 % of the `/explain` SLA (2400 ms) | — |
| `FINSIGHT_DB_PATH` | `./.data/finsight_events.db` | **Set this to a mounted volume in production.** See below. |
| `FINSIGHT_ALLOWED_ORIGINS` | `*` | Comma-separated origin list to lock CORS down without a code change. |
| `FINSIGHT_EXPLAIN_IP_HOURLY` | 20 | Per-IP `/explain` calls per hour before 429. |
| `FINSIGHT_EXPLAIN_DAILY_BUDGET` | 2000 | Global paid calls per day. Past the cap the endpoint serves the deterministic template — the product degrades, the bill does not. |

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

`EXPO_PUBLIC_*` values are inlined at **build** time — and in this project the
build runs on your machine, not on Vercel:

```
cd apps/mobile
npx expo export --platform web --clear   # <- .env is read HERE
vercel --prod                            # <- uploads the finished dist/
```

`vercel.json` sets `outputDirectory: dist` and `package.json` has no build
script, so Vercel serves a pre-built bundle and never runs a build. **A variable
set in the Vercel dashboard has no effect.** The value that ships is whatever
`apps/mobile/.env` contained when `expo export` ran.

There is no localhost fallback in production builds. A missing value surfaces as
a `CONFIG_ERROR` in the app's error card rather than shipping a bundle that
points at a developer's laptop — which is what made every deployed request fail
at the most expensive step, immediately after the user entered their finances.

`apps/mobile/app.json` also carries `extra.apiUrl`. Nothing reads it; the app
uses `process.env.EXPO_PUBLIC_API_URL` only. Keep the two in sync or drop the
`extra.apiUrl` field, otherwise it reads like configuration that works.

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
