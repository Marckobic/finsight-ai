# 🔒 FINSIGHT.AI — SYSTEM RULES (NON-NEGOTIABLE)

> These rules govern every module in this codebase.  
> Any PR that violates them must be rejected regardless of feature intent.

---

## RULE 1 — AI NEVER CALCULATES MONEY

The LLM (ai-layer) is **strictly prohibited** from:
- Performing any arithmetic or financial computation
- Generating or modifying numeric values
- Inferring amounts, rates, timelines, or deltas

The LLM **may only**:
- Receive structured JSON produced by the core-engine or scenario-engine
- Output plain-language explanation of that data
- Use natural language to describe what the numbers mean — not produce them

Violation example (FORBIDDEN):
```
AI: "You'll save $300 more per month, which means you'll hit your goal in 9 months."
```
Correct usage:
```
AI receives: { baseline_months: 14, scenario_months: 9, delta: 5 }
AI outputs: "By cutting expenses as described, you could reach your goal 5 months earlier."
```

---

## RULE 2 — CORE ENGINE IS THE SINGLE SOURCE OF TRUTH

All financial values displayed in the UI **must originate from core-engine**.  
No module may override, adjust, or "correct" engine outputs except the engine itself.

Modules and their truth relationship:

| Module             | Can produce numbers? | Source of truth? |
|--------------------|----------------------|------------------|
| core-engine        | ✅ Yes               | ✅ Yes           |
| scenario-engine    | ✅ Yes (delta only)  | Derived only     |
| ai-layer           | ❌ Never             | ❌ Never         |
| validation-gateway | ❌ No (reads only)   | ❌ No            |
| frontend/UI        | ❌ No (displays only)| ❌ No            |

---

## RULE 3 — SCENARIO ENGINE = BEHAVIORAL SIMULATION, NOT A MATH TOOL

The scenario-engine simulates the **impact of a user behavior change** on an existing baseline.

It must:
- Accept a baseline produced by core-engine
- Accept a single behavioral change (type + value)
- Return delta values (e.g. months saved, new timeline)

It must NOT:
- Accept arbitrary financial queries
- Produce standalone projections without a baseline
- Simulate more than one behavioral change at a time (MVP)

---

## RULE 4 — ALL OUTPUTS MUST BE SCHEMA-VALIDATED

Every response leaving any internal module **must pass schema validation** before reaching the next layer.

Required for:
- core-engine → scenario-engine
- scenario-engine → validation-gateway
- ai-layer → validation-gateway
- validation-gateway → frontend

Schema tools: **Pydantic** (Python) / **Zod** (TypeScript).  
If validation fails → return fallback template. Never pass invalid data forward.

---

## RULE 5 — UI (MOBILE) ONLY REFLECTS BACKEND TRUTH

The mobile app (React Native + Expo) **may not**:
- Derive or calculate any values client-side
- Display AI output directly without passing through validation-gateway
- Render any number that was not produced by core-engine or scenario-engine

The mobile app **must**:
- Treat all data as read-only display of backend state
- Reflect the validation-gateway's pass/fail signal
- Show fallback UI when gateway rejects output
- Communicate with backend exclusively via typed API calls (shared-types contracts)

---

## RULE 6 — NO "ADVICE ONLY" WITHOUT SCENARIO DELTA

The system must never show a recommendation without an associated scenario delta.

A recommendation is only valid when it includes:
- `baseline_months`: current projection
- `scenario_months`: projection after behavior change
- `delta_months`: the difference

Textual advice without a computed delta is considered an invalid output and must be blocked by the validation-gateway.

---

## ENFORCEMENT

These rules are enforced at:
1. **Code review** — any PR violating these rules is rejected
2. **CI tests** — hallucination tests, schema tests, engine regression tests
3. **Validation gateway** — runtime enforcement at the system boundary

CI failure thresholds:
```
FAIL IF:
  hallucination_rate > 1%
  schema_failure_rate > 1%
  engine_regression_detected = true
```

---

_Last updated: 2026-04-15_  
_Owner: FinSight Architecture_
