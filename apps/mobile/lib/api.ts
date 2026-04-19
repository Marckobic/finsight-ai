/**
 * lib/api.ts
 * Typed fetch client for the FinSight.ai API.
 *
 * Rules:
 * - 10 s timeout on every request (AbortController)
 * - Throws ApiError on non-2xx or network failure
 * - All functions are typed end-to-end against shared_types mirrors in lib/types.ts
 */

import type {
  AIExplanationInput,
  ApiError,
  BaselineResponse,
  DecisionEvent,
  ExplainResponse,
  FinancialSnapshot,
  ScenarioInput,
  ScenarioResponse,
} from "./types";

const BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

const TIMEOUT_MS = 10_000;

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

async function apiFetch<T>(
  path: string,
  body: unknown
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (err) {
    throw {
      status: "error",
      message:
        err instanceof Error && err.name === "AbortError"
          ? "Request timed out after 10 s."
          : "Network error — check your connection.",
      code: err instanceof Error && err.name === "AbortError"
        ? "TIMEOUT"
        : "NETWORK_ERROR",
    } satisfies ApiError;
  } finally {
    clearTimeout(timer);
  }

  const json = await response.json().catch(() => ({
    status: "error",
    message: "Server returned non-JSON response.",
    code: "PARSE_ERROR",
  }));

  if (!response.ok) {
    throw json as ApiError;
  }

  return json as T;
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

/**
 * POST /baseline
 * Compute a deterministic financial baseline projection.
 */
export async function fetchBaseline(
  snapshot: FinancialSnapshot
): Promise<BaselineResponse> {
  return apiFetch<BaselineResponse>("/baseline", snapshot);
}

/**
 * POST /scenario
 * Simulate the financial impact of a single behavioral change.
 */
export async function fetchScenario(
  input: ScenarioInput
): Promise<ScenarioResponse> {
  return apiFetch<ScenarioResponse>("/scenario", input);
}

/**
 * POST /explain
 * Generate a plain-language AI explanation of a scenario result.
 * Always returns 200 — fallback is indicated by response.status === "fallback".
 */
export async function fetchExplanation(
  input: AIExplanationInput
): Promise<ExplainResponse> {
  return apiFetch<ExplainResponse>("/explain", input);
}

/**
 * POST /decision
 * Log a user accept/reject/modify decision.
 */
export async function postDecision(
  event: DecisionEvent
): Promise<{ status: string }> {
  return apiFetch<{ status: string }>("/decision", event);
}
