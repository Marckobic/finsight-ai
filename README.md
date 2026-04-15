# FinSight.ai

> Deterministic financial engine + behavioral simulation + guardrailed AI explanation system.

## What this is

FinSight is **not** a financial advisor.  
FinSight is a **decision loop**: it computes your financial baseline, simulates what happens if you change one behavior, and explains the outcome in plain language.

```
User Input → core-engine (truth) → scenario-engine (what-if)
          → validation-gateway (hard gate) → ai-layer (explain only)
          → UI decision screen → feedback loop
```

## Core guarantee

| Guarantee                              | Enforced by               |
|----------------------------------------|---------------------------|
| AI never computes finance              | ai-layer strict prompt    |
| Engine is single source of truth       | architecture contract     |
| Scenario = simulation, not math tool   | scenario-engine interface |
| All outputs schema-validated           | Pydantic + Zod            |
| UI reflects system state only          | frontend contract         |

See [`docs/system-rules.md`](docs/system-rules.md) for the full ruleset.

## Stack

- **Backend / Engine**: Python 3.12 + FastAPI
- **Mobile**: React Native + Expo (iOS + Android)
- **Validation**: Pydantic (Python) · Zod (TypeScript)
- **AI**: OpenAI-compatible LLM — explanation only

## Project structure

```
finsight-ai/
├── apps/
│   ├── api/          # FastAPI backend
│   ├── mobile/       # React Native + Expo (iOS + Android)
│   └── worker/       # Async jobs (future)
├── packages/
│   ├── core-engine/       # Deterministic financial math
│   ├── scenario-engine/   # Behavioral simulation
│   ├── ai-layer/          # LLM wrapper (strict)
│   ├── validation-gateway/# Schema + hallucination guard
│   ├── shared-types/      # Shared data contracts
│   └── config/            # Global config
├── tests/
├── infra/
└── docs/
```

## Build order (phases)

1. `packages/core-engine` — cashflow, goal, projection
2. `packages/scenario-engine` — simulate behavior change
3. `packages/validation-gateway` — schema + safety gate
4. `packages/ai-layer` — explanation wrapper
5. `apps/api` — FastAPI endpoints
6. `apps/mobile` — React Native + Expo decision screens

## Status

🟡 Phase 1 — scaffolding complete. Awaiting PRD to begin core-engine implementation.
