/**
 * lib/analytics.ts
 * Product analytics — funnel + decision loop tracking.
 *
 * Works immediately with console logging (zero setup).
 * PostHog-ready: set EXPO_PUBLIC_POSTHOG_KEY to activate cloud analytics.
 * Fire-and-forget: never blocks UI, never throws.
 *
 * To activate PostHog:
 *   1. npx expo install posthog-react-native
 *   2. Set EXPO_PUBLIC_POSTHOG_KEY in .env
 *   3. Uncomment PostHog lines below
 */

import { Platform } from "react-native";

// ── Session ID (one per app launch) ──────────────────────────────────────────
function generateId(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

export const SESSION_ID = generateId();

// ── Event catalogue ───────────────────────────────────────────────────────────
export const EVENTS = {
  ONBOARDING_STARTED:   "onboarding_started",
  ONBOARDING_COMPLETED: "onboarding_completed",
  ONBOARDING_SKIPPED:   "onboarding_skipped",
  GOAL_CREATED:         "goal_created",
  SNAPSHOT_SUBMITTED:   "snapshot_submitted",
  BASELINE_GENERATED:   "baseline_generated",
  BASELINE_OFFLINE:     "baseline_offline",
  SCENARIO_OPENED:      "scenario_opened",
  SCENARIO_ADJUSTED:    "scenario_adjusted",
  SCENARIO_ACCEPTED:    "scenario_accepted",
  SCENARIO_REJECTED:    "scenario_rejected",
  DECISION_LOOP_DONE:   "decision_loop_completed",
} as const;

export type EventName = typeof EVENTS[keyof typeof EVENTS];

// ── In-memory store ───────────────────────────────────────────────────────────
const _events: Array<{ name: string; ts: number; props: Record<string, unknown> }> = [];

// ── Coarsening ────────────────────────────────────────────────────────────────
//
// Nothing money-shaped leaves the device. The landing page promises "no data
// sharing — numbers stay in-session only", and this file was posting
// target_amount, monthly_cashflow and savings_rate to /events, where they were
// written to a database keyed by session_id.
//
// Bands answer the questions the funnel is actually asked — do people with a
// thin surplus drop out earlier? — without a personal figure ever being stored.
// Edges match analytics/buckets.py on the backend; change both together.

const MONEY_EDGES: Array<[number, string]> = [
  [0, "0"], [250, "1-250"], [500, "250-500"], [1000, "500-1000"],
  [2500, "1000-2500"], [5000, "2500-5000"], [10000, "5000-10000"],
];

const PERCENT_EDGES: Array<[number, string]> = [
  [0, "0"], [5, "0-5"], [10, "5-10"], [20, "10-20"], [30, "20-30"], [50, "30-50"],
];

function band(
  value: number | null | undefined,
  edges: Array<[number, string]>,
  top: string
): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "unknown";
  const n = Number(value);
  if (n < 0) return "negative";
  for (const [edge, label] of edges) if (n <= edge) return label;
  return top;
}

/** USD per month → a band label. Never returns the input. */
export function moneyBucket(value: number | null | undefined): string {
  return band(value, MONEY_EDGES, "10000+");
}

/** A rate already expressed in percent (5 === 5%). */
export function percentBucket(value: number | null | undefined): string {
  return band(value, PERCENT_EDGES, "50+");
}

// ── Core track function ───────────────────────────────────────────────────────
export function track(
  eventName: EventName | string,
  properties: Record<string, unknown> = {}
): void {
  try {
    const payload = {
      event_name: eventName,
      session_id: SESSION_ID,
      timestamp: new Date().toISOString(),
      platform: Platform.OS,
      properties,
    };

    // 1. In-memory (always)
    _events.push({ name: eventName, ts: Date.now(), props: properties });

    // 2. Console in dev (visible in Expo debugger / terminal)
    if (__DEV__) {
      console.log(`📊 [Analytics] ${eventName}`, properties);
    }

    // 3. Backend (when running — fire-and-forget)
    const BASE_URL =
      process.env.EXPO_PUBLIC_API_URL?.trim() ||
      (__DEV__ ? "http://localhost:8000" : "");
    if (!BASE_URL) return; // analytics is best-effort; never throw from track()
    fetch(`${BASE_URL}/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).catch(() => { /* backend may not be running */ });

    // 4. PostHog — uncomment when EXPO_PUBLIC_POSTHOG_KEY is set
    // import PostHog from "posthog-react-native";
    // if (process.env.EXPO_PUBLIC_POSTHOG_KEY) posthog.capture(eventName, payload);

  } catch {
    // Analytics must never crash the app
  }
}

// ── Session summary (shown on Decision screen) ────────────────────────────────
export function getSessionSummary() {
  const count = (name: string) => _events.filter((e) => e.name === name).length;

  const opened   = count(EVENTS.SCENARIO_OPENED);
  const accepted = count(EVENTS.SCENARIO_ACCEPTED);
  const rejected = count(EVENTS.SCENARIO_REJECTED);

  return {
    sessionId: SESSION_ID,
    funnel: {
      onboarding:  count(EVENTS.ONBOARDING_COMPLETED) + count(EVENTS.ONBOARDING_SKIPPED) > 0,
      goalCreated: count(EVENTS.GOAL_CREATED) > 0,
      snapshot:    count(EVENTS.SNAPSHOT_SUBMITTED) > 0,
      baseline:    count(EVENTS.BASELINE_GENERATED) > 0,
      scenario:    opened > 0,
      decision:    accepted + rejected > 0,
    },
    dlcr: opened > 0 ? (accepted + rejected) / opened : 0,
    accepted,
    rejected,
    totalEvents: _events.length,
  };
}
