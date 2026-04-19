/**
 * lib/store.tsx
 * React Context + useReducer global state store.
 *
 * Actions:
 *   SET_GOAL         — user sets goal type + target amount
 *   SET_SNAPSHOT     — user submits financial input form
 *   SET_BASELINE     — API baseline result received
 *   SET_SCENARIO     — API scenario result received
 *   SET_EXPLANATION  — AI explanation received
 *   ACCEPT_SCENARIO  — user accepts: adherence +0.05, accepted++
 *   REJECT_SCENARIO  — user rejects: adherence -0.05, rejected++
 *   RESET            — return to initial state (start over)
 */

import React, { createContext, useContext, useReducer } from "react";
import type {
  AIExplanationOutput,
  BaselineResult,
  ExplainValidation,
  FinancialSnapshot,
  GoalData,
  ScenarioResult,
} from "./types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function clamp(v: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, v));
}

const ADHERENCE_MIN = 0.10;
const ADHERENCE_MAX = 0.95;
const ADHERENCE_STEP = 0.05;

// ---------------------------------------------------------------------------
// State shape
// ---------------------------------------------------------------------------

export interface AdherenceHistory {
  current: number;   // suggested rate for next simulation
  accepted: number;  // accepted this session
  rejected: number;  // rejected this session
}

export interface AppState {
  goal: GoalData | null;
  snapshot: FinancialSnapshot | null;
  baseline: BaselineResult | null;
  scenario: ScenarioResult | null;
  explanation: AIExplanationOutput | null;
  explanationValidation: ExplainValidation | null;
  adherence: AdherenceHistory;
}

const INITIAL_STATE: AppState = {
  goal: null,
  snapshot: null,
  baseline: null,
  scenario: null,
  explanation: null,
  explanationValidation: null,
  adherence: { current: 0.70, accepted: 0, rejected: 0 },
};

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

type Action =
  | { type: "SET_GOAL"; payload: GoalData }
  | { type: "SET_SNAPSHOT"; payload: FinancialSnapshot }
  | { type: "SET_BASELINE"; payload: BaselineResult }
  | { type: "SET_SCENARIO"; payload: ScenarioResult }
  | { type: "SET_EXPLANATION"; payload: { output: AIExplanationOutput; validation: ExplainValidation } }
  | { type: "ACCEPT_SCENARIO" }
  | { type: "REJECT_SCENARIO" }
  | { type: "RESET" };

// ---------------------------------------------------------------------------
// Reducer
// ---------------------------------------------------------------------------

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "SET_GOAL":
      return { ...state, goal: action.payload };

    case "SET_SNAPSHOT":
      return {
        ...state,
        snapshot: action.payload,
        baseline: null,
        scenario: null,
        explanation: null,
        explanationValidation: null,
      };

    case "SET_BASELINE":
      return {
        ...state,
        baseline: action.payload,
        scenario: null,
        explanation: null,
        explanationValidation: null,
      };

    case "SET_SCENARIO":
      return {
        ...state,
        scenario: action.payload,
        explanation: null,
        explanationValidation: null,
      };

    case "SET_EXPLANATION":
      return {
        ...state,
        explanation: action.payload.output,
        explanationValidation: action.payload.validation,
      };

    // ── Feedback loop ──────────────────────────────────────────────────────
    case "ACCEPT_SCENARIO":
      return {
        ...state,
        scenario: null,
        explanation: null,
        explanationValidation: null,
        adherence: {
          current: clamp(state.adherence.current + ADHERENCE_STEP, ADHERENCE_MIN, ADHERENCE_MAX),
          accepted: state.adherence.accepted + 1,
          rejected: state.adherence.rejected,
        },
      };

    case "REJECT_SCENARIO":
      return {
        ...state,
        scenario: null,
        explanation: null,
        explanationValidation: null,
        adherence: {
          current: clamp(state.adherence.current - ADHERENCE_STEP, ADHERENCE_MIN, ADHERENCE_MAX),
          accepted: state.adherence.accepted,
          rejected: state.adherence.rejected + 1,
        },
      };

    case "RESET":
      // Keep adherence history across resets so it persists through the session
      return { ...INITIAL_STATE, adherence: state.adherence };

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

interface StoreContextValue {
  state: AppState;
  dispatch: React.Dispatch<Action>;
}

const StoreContext = createContext<StoreContextValue | null>(null);

export function StoreProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  return (
    <StoreContext.Provider value={{ state, dispatch }}>
      {children}
    </StoreContext.Provider>
  );
}

export function useStore(): StoreContextValue {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore must be used within a StoreProvider");
  return ctx;
}
