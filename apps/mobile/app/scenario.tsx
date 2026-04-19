/**
 * app/scenario.tsx
 * Screen 4 — Scenario Simulation & Decision.
 *
 * User selects behavior type, enters monthly amount, adjusts adherence.
 * Calls /scenario + /explain. Shows Baseline vs Scenario comparison.
 * Accept or Reject with sticky action bar.
 */

import { MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import AdherenceSlider from "../components/AdherenceSlider";
import { BottomNav } from "../components/BottomNav";
import { COLORS, FONT, RADIUS, SPACING } from "../constants/theme";
import { fetchExplanation, fetchScenario } from "../lib/api";
import { useStore } from "../lib/store";
import type { AIQualitySummary, ApiError, BehaviorType } from "../lib/types";
import { EVENTS, track } from "../lib/analytics";
import type { ScenarioResult, AIExplanationOutput } from "../lib/types";

// ── Offline fallbacks ────────────────────────────────────────────────────────

function buildOfflineScenario(
  b: import("../lib/types").BaselineResult,
  amountNum: number,
  adherence: number,
  behaviorType: import("../lib/types").BehaviorType
): ScenarioResult {
  const effectiveChange = amountNum * adherence;
  const newCashflow = b.monthly_cashflow + effectiveChange;
  // Estimate remaining capital from baseline (cashflow * months ≈ gap)
  const remaining = b.time_to_goal_months !== null && b.monthly_cashflow > 0
    ? b.monthly_cashflow * b.time_to_goal_months
    : null;
  const scenarioMonths = remaining !== null && newCashflow > 0
    ? Math.ceil(remaining / newCashflow)
    : null;
  const deltaMonths =
    b.time_to_goal_months !== null && scenarioMonths !== null
      ? b.time_to_goal_months - scenarioMonths
      : null;
  return {
    baseline_months: b.time_to_goal_months,
    scenario_months: scenarioMonths,
    delta_months: deltaMonths,
    adherence_rate: adherence,
    effective_monthly_change: effectiveChange,
    scenario_monthly_cashflow: newCashflow,
    is_improvement: deltaMonths !== null && deltaMonths > 0,
  };
}

function buildOfflineExplanation(
  amountNum: number,
  adherence: number,
  behaviorType: import("../lib/types").BehaviorType,
  deltaMonths: number | null
): AIExplanationOutput {
  const action = behaviorType === "savings_increase" ? "saving" : "cutting";
  const effective = Math.round(amountNum * adherence);
  const impact = deltaMonths !== null && deltaMonths > 0
    ? `This accelerates your goal by ${deltaMonths} month${deltaMonths > 1 ? "s" : ""}.`
    : "This will not meaningfully accelerate your goal at this level.";
  return {
    recommendation: `By ${action} $${amountNum.toLocaleString()}/month at ${Math.round(adherence * 100)}% adherence, you add $${effective.toLocaleString()} effective monthly cashflow. ${impact}`,
    explanation: `Effective change = $${amountNum.toLocaleString()} × ${Math.round(adherence * 100)}% adherence = $${effective.toLocaleString()}/month added to your cashflow.`,
  };
}

const BEHAVIOR_OPTIONS: {
  type: BehaviorType;
  label: string;
  description: string;
  icon: keyof typeof MaterialIcons.glyphMap;
}[] = [
  { type: "savings_increase", label: "Save More",   description: "Increase monthly savings contribution", icon: "savings" },
  { type: "expense_cut",      label: "Spend Less",  description: "Reduce a recurring monthly expense",    icon: "trending-down" },
];

export default function ScenarioScreen(): React.JSX.Element {
  const { state, dispatch } = useStore();

  const [behaviorType, setBehaviorType] = useState<BehaviorType>("savings_increase");
  const [amount, setAmount] = useState("");
  // Seed from adaptive adherence history — updates after every Accept/Reject
  const [adherence, setAdherence] = useState(state.adherence.current);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [quality, setQuality] = useState<AIQualitySummary | null>(null);
  const [qualityDismissed, setQualityDismissed] = useState(false);

  const { accepted, rejected } = state.adherence;
  const hasHistory = accepted + rejected > 0;

  const b = state.baseline;
  const s = state.scenario;
  const explanation = state.explanation;

  const amountNum = parseFloat(amount.replace(/,/g, "")) || 0;

  async function handleSimulate() {
    if (!state.snapshot || !b) { setApiError("Missing data. Please go back."); return; }
    if (amountNum <= 0) { setApiError("Enter a positive monthly amount."); return; }
    track("scenario_opened", { behavior_type: behaviorType, amount: amountNum });
    setLoading(true);
    setApiError(null);
    setIsOffline(false);
    try {
      const scenarioRes = await fetchScenario({
        financial_snapshot: state.snapshot,
        baseline: b,
        behavior_change: { type: behaviorType, value: amountNum },
        adherence_rate: adherence,
      });
      dispatch({ type: "SET_SCENARIO", payload: scenarioRes.data });

      const explainRes = await fetchExplanation({
        baseline_months: scenarioRes.data.baseline_months,
        scenario_months: scenarioRes.data.scenario_months,
        delta_months: scenarioRes.data.delta_months,
        monthly_change_amount: amountNum,
        adherence_rate: adherence,
        behavior_type: behaviorType,
        goal_type: state.snapshot.goal.type,
      });
      dispatch({
        type: "SET_EXPLANATION",
        payload: { output: explainRes.data, validation: explainRes.validation },
      });
      setQuality(explainRes.quality ?? null);
      setQualityDismissed(false);
    } catch (err) {
      const e = err as ApiError;
      const msg = e.message?.toLowerCase() ?? "";
      const isNetworkErr = msg.includes("network") || msg.includes("fetch") ||
                           msg.includes("failed") || msg.includes("connect");
      if (isNetworkErr && b) {
        // Backend offline — compute scenario client-side
        const offlineScenario = buildOfflineScenario(b, amountNum, adherence, behaviorType);
        dispatch({ type: "SET_SCENARIO", payload: offlineScenario });
        const offlineExplanation = buildOfflineExplanation(amountNum, adherence, behaviorType, offlineScenario.delta_months);
        dispatch({
          type: "SET_EXPLANATION",
          payload: {
            output: offlineExplanation,
            validation: { valid: true, fallback_used: true, errors: [] },
          },
        });
        setIsOffline(true);
        track(EVENTS.BASELINE_OFFLINE, { amount: amountNum });
      } else {
        setApiError(e.message ?? "Simulation failed.");
      }
    } finally {
      setLoading(false);
    }
  }

  function handleAccept() {
    const delta_months = s?.delta_months ?? null;
    track("scenario_accepted", { adherence: Math.round(adherence * 100), delta_months });
    track("decision_loop_completed", { outcome: "accepted" });
    dispatch({ type: "ACCEPT_SCENARIO" });
    router.push("/decision");
  }

  function handleReject() {
    track("scenario_rejected", { adherence: Math.round(adherence * 100) });
    track("decision_loop_completed", { outcome: "rejected" });
    dispatch({ type: "REJECT_SCENARIO" });
    setAmount("");
    setAdherence(state.adherence.current - 0.05 < 0.10 ? 0.10 : state.adherence.current - 0.05);
  }

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        {/* ── Top bar ── */}
        <View style={styles.topBar}>
          <Text style={styles.brand}>FinSight.ai</Text>
          <View style={styles.navLinks}>
            <Text style={styles.navInactive}>Baseline</Text>
            <Text style={styles.navActive}>Scenario</Text>
          </View>
        </View>

        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          {/* ── Header ── */}
          <View style={styles.header}>
            <Text style={styles.moduleLabel}>Simulation Layer v2.4</Text>
            {s ? (
              <Text style={styles.heading}>
                What if you {behaviorType === "savings_increase" ? "save" : "cut"} an extra{" "}
                <Text style={styles.headingAccent}>${amountNum.toLocaleString()}/month?</Text>
              </Text>
            ) : (
              <Text style={styles.heading}>What Would{"\n"}You Change?</Text>
            )}
          </View>

          {/* ── Session history chip ── */}
          {hasHistory && (
            <View style={styles.historyChip}>
              <Text style={styles.historyText}>
                ✓ {accepted} accepted · ✕ {rejected} rejected
              </Text>
              <Text style={styles.historySub}>
                Suggested adherence adapted to {Math.round(state.adherence.current * 100)}%
              </Text>
            </View>
          )}

          {/* ── Offline banner ── */}
          {isOffline && (
            <View style={styles.offlineBanner}>
              <MaterialIcons name="offline-bolt" size={14} color={COLORS.PRIMARY} />
              <Text style={styles.offlineText}>
                Offline mode — simulation computed locally. Start backend for full accuracy.
              </Text>
            </View>
          )}

          {/* ── AI Explanation banner ── */}
          {explanation && s && (
            <View style={styles.explainBanner}>
              <MaterialIcons name="bolt" size={16} color={COLORS.TERTIARY} style={{ marginTop: 1 }} />
              <Text style={styles.explainText}>
                <Text style={styles.explainLabel}>AI Insight: </Text>
                {explanation.recommendation}
              </Text>
            </View>
          )}

          {/* ── AI Quality banner ── */}
          {quality && s && !qualityDismissed && quality.status === "degraded" && (
            <View style={styles.qualityBannerWarn}>
              <Text style={styles.qualityBannerText}>
                ⚠ AI confidence reduced — verify with your advisor
              </Text>
              <TouchableOpacity onPress={() => setQualityDismissed(true)} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
                <MaterialIcons name="close" size={14} color={COLORS.ORANGE} />
              </TouchableOpacity>
            </View>
          )}
          {quality && s && quality.status === "fallback" && (
            <View style={styles.qualityBannerInfo}>
              <Text style={styles.qualityBannerInfoText}>⚡ Using deterministic explanation</Text>
            </View>
          )}

          {/* ── Behavior type ── */}
          {!s && (
            <>
              <Text style={styles.sectionLabel}>Select Change Type</Text>
              <View style={styles.behaviorRow}>
                {BEHAVIOR_OPTIONS.map((opt) => {
                  const active = behaviorType === opt.type;
                  return (
                    <TouchableOpacity
                      key={opt.type}
                      style={[styles.behaviorCard, active && styles.behaviorCardActive]}
                      onPress={() => setBehaviorType(opt.type)}
                      activeOpacity={0.75}
                    >
                      <MaterialIcons name={opt.icon} size={22} color={active ? COLORS.ORANGE : COLORS.PRIMARY} />
                      <Text style={[styles.behaviorLabel, active && styles.behaviorLabelActive]}>{opt.label}</Text>
                      <Text style={styles.behaviorDesc}>{opt.description}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              {/* ── Amount ── */}
              <Text style={styles.sectionLabel}>Monthly Amount</Text>
              <View style={styles.amountRow}>
                <Text style={styles.dollarSign}>$</Text>
                <TextInput
                  style={styles.amountInput}
                  value={amount}
                  onChangeText={setAmount}
                  placeholder="0.00"
                  placeholderTextColor="rgba(255,255,255,0.4)"
                  keyboardType="numeric"
                  returnKeyType="done"
                />
              </View>
            </>
          )}

          {/* ── Baseline vs Scenario comparison ── */}
          {b && (
            <View style={styles.comparisonGrid}>
              {/* Baseline */}
              <View style={styles.baselineCard}>
                <Text style={styles.cardTag}>Baseline Strategy</Text>
                <Text style={styles.bigNumber}>
                  {b.time_to_goal_months !== null ? b.time_to_goal_months : "∞"}
                </Text>
                <Text style={styles.bigNumberSub}>Months to Target</Text>
                <View style={styles.divider} />
                <View style={styles.statRow}>
                  <Text style={styles.statLabel}>Monthly Cashflow</Text>
                  <Text style={styles.statValue}>
                    ${Math.abs(b.monthly_cashflow).toLocaleString()}
                  </Text>
                </View>
                <View style={styles.statRow}>
                  <Text style={styles.statLabel}>Savings Rate</Text>
                  <Text style={styles.statValue}>{b.savings_rate.toFixed(1)}%</Text>
                </View>
                <View style={styles.activeBadge}>
                  <View style={styles.activeDot} />
                  <Text style={styles.activeBadgeText}>Current Active Plan</Text>
                </View>
              </View>

              {/* Scenario (shown after simulation) */}
              {s && (
                <View style={styles.scenarioCard}>
                  <View style={styles.scenCardHeader}>
                    <Text style={styles.scenCardTag}>Simulated Scenario</Text>
                    <MaterialIcons name="new-releases" size={18} color={COLORS.PRIMARY} />
                  </View>
                  <View style={styles.scenMonthsRow}>
                    <Text style={styles.bigNumberLight}>
                      {s.scenario_months !== null ? s.scenario_months : "∞"}
                    </Text>
                    {s.delta_months !== null && s.delta_months > 0 && (
                      <Text style={styles.deltaLabel}>-{s.delta_months}m</Text>
                    )}
                  </View>
                  <Text style={styles.bigNumberSubLight}>Projected Months</Text>
                  <View style={styles.dividerLight} />
                  <View style={styles.statRow}>
                    <Text style={styles.statLabelLight}>Adjusted Cashflow</Text>
                    <Text style={styles.statValueLight}>
                      ${Math.abs(s.scenario_monthly_cashflow).toLocaleString()}
                    </Text>
                  </View>
                  <View style={styles.statRow}>
                    <Text style={styles.statLabelLight}>Improvement</Text>
                    <Text style={[styles.statValueLight, s.is_improvement && { color: COLORS.TERTIARY }]}>
                      {s.is_improvement ? "Yes ✓" : "No"}
                    </Text>
                  </View>
                </View>
              )}
            </View>
          )}

          {/* ── Adherence slider ── */}
          <View style={styles.adherenceCard}>
            <View style={styles.adherenceHeader}>
              <Text style={styles.sectionLabel}>Tactical Adherence</Text>
              <Text style={styles.adherenceValue}>{Math.round(adherence * 100)}%</Text>
            </View>
            <AdherenceSlider
              value={adherence}
              onValueChange={setAdherence}
              onSlidingComplete={(v) => track("scenario_adjusted", { adherence: Math.round(v * 100) })}
            />
            <View style={styles.sliderLabels}>
              <Text style={styles.sliderLabelText}>Relaxed (10%)</Text>
              <Text style={styles.sliderLabelText}>Aggressive (95%)</Text>
            </View>
          </View>

          {/* ── Metrics grid (post-simulation) ── */}
          {s && (
            <View style={styles.metricsGrid}>
              <View style={styles.metricTile}>
                <Text style={styles.metricTileLabel}>Liquidity Delta</Text>
                <Text style={[styles.metricTileValue, { color: COLORS.ERROR }]}>
                  -${(amountNum * 12).toLocaleString()}
                </Text>
                <Text style={styles.metricTileSub}>Annual reduction</Text>
              </View>
              <View style={styles.metricTile}>
                <Text style={styles.metricTileLabel}>Time Saved</Text>
                <Text style={[styles.metricTileValue, { color: COLORS.TERTIARY }]}>
                  {s.delta_months !== null && s.delta_months > 0 ? `${s.delta_months}m` : "—"}
                </Text>
                <Text style={styles.metricTileSub}>Months accelerated</Text>
              </View>
              <View style={[styles.metricTile, styles.metricTileWide]}>
                <Text style={styles.metricTileLabel}>Stress Test</Text>
                <View style={styles.metricVerifiedRow}>
                  <Text style={styles.metricTileValue}>
                    {adherence >= 0.7 ? "Optimal" : adherence >= 0.5 ? "Moderate" : "Cautious"}
                  </Text>
                  <MaterialIcons
                    name="verified-user"
                    size={16}
                    color={adherence >= 0.7 ? COLORS.TERTIARY : COLORS.PRIMARY}
                  />
                </View>
              </View>
            </View>
          )}

          {apiError && (
            <View style={styles.errorCard}>
              <MaterialIcons name="error-outline" size={16} color={COLORS.ERROR} />
              <Text style={styles.errorText}>{apiError}</Text>
            </View>
          )}

          {loading && (
            <View style={styles.loadingWrap}>
              <ActivityIndicator size="large" color={COLORS.ORANGE} />
              <Text style={styles.loadingText}>Running simulation...</Text>
            </View>
          )}

          {/* ── Run simulation CTA (pre-result) ── */}
          {!loading && !s && (
            <TouchableOpacity style={styles.simButton} onPress={handleSimulate} activeOpacity={0.85}>
              <Text style={styles.simButtonLabel}>Run Simulation</Text>
              <MaterialIcons name="play-arrow" size={20} color={COLORS.TEXT_ON_ORANGE} />
            </TouchableOpacity>
          )}

          {/* ── Accept / Reject (post-result) ── */}
          {!loading && s && (
            <View style={styles.actionBar}>
              <TouchableOpacity style={styles.rejectBtn} onPress={handleReject} activeOpacity={0.8}>
                <Text style={styles.rejectLabel}>Reject</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.acceptBtn} onPress={handleAccept} activeOpacity={0.85}>
                <Text style={styles.acceptLabel}>Accept Simulation</Text>
              </TouchableOpacity>
            </View>
          )}

          <View style={{ height: 20 }} />
        </ScrollView>
      </KeyboardAvoidingView>
      <BottomNav />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.BACKGROUND },
  flex: { flex: 1 },

  topBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: SPACING.LG,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.05)",
  },
  brand: { fontSize: 20, fontWeight: FONT.WEIGHT_BOLD, color: COLORS.ORANGE, letterSpacing: -0.5 },
  navLinks: { flexDirection: "row", gap: SPACING.MD },
  navActive: {
    fontSize: FONT.SIZE_SM,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.ORANGE,
    borderBottomWidth: 2,
    borderBottomColor: COLORS.ORANGE,
    paddingBottom: 2,
  },
  navInactive: { fontSize: FONT.SIZE_SM, color: COLORS.DISABLED },

  content: { paddingHorizontal: SPACING.LG, paddingBottom: 40 },

  header: { paddingTop: SPACING.XL, marginBottom: SPACING.XL },
  moduleLabel: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.PRIMARY,
    textTransform: "uppercase",
    letterSpacing: 2,
    fontWeight: FONT.WEIGHT_BOLD,
    marginBottom: 6,
  },
  heading: {
    fontSize: 30,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_SURFACE,
    letterSpacing: -1,
    lineHeight: 38,
  },
  headingAccent: { color: COLORS.PRIMARY },

  historyChip: {
    backgroundColor: "rgba(255,182,147,0.08)",
    borderRadius: RADIUS.MD,
    borderWidth: 1,
    borderColor: "rgba(255,182,147,0.15)",
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    marginBottom: SPACING.MD,
  },
  historyText: {
    fontSize: FONT.SIZE_SM,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
    color: COLORS.PRIMARY,
    letterSpacing: 0.5,
  },
  historySub: {
    fontSize: FONT.SIZE_XS,
    color: "rgba(255,255,255,0.4)",
    marginTop: 3,
  },

  offlineBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.XS,
    backgroundColor: "rgba(255,182,147,0.08)",
    borderRadius: RADIUS.MD,
    borderWidth: 1,
    borderColor: "rgba(255,182,147,0.15)",
    paddingHorizontal: SPACING.MD,
    paddingVertical: SPACING.SM,
    marginBottom: SPACING.MD,
  },
  offlineText: {
    flex: 1,
    fontSize: FONT.SIZE_XS,
    color: COLORS.PRIMARY,
    lineHeight: 16,
  },

  explainBanner: {
    flexDirection: "row",
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.MD,
    padding: SPACING.MD,
    marginBottom: SPACING.LG,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.TERTIARY,
    gap: SPACING.SM,
    alignItems: "flex-start",
  },
  explainText: { flex: 1, fontSize: FONT.SIZE_SM, color: COLORS.TEXT_SECONDARY, lineHeight: 20 },
  explainLabel: { color: COLORS.TEXT_ON_SURFACE, fontWeight: FONT.WEIGHT_SEMIBOLD },

  sectionLabel: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 2,
    color: COLORS.DISABLED,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
    marginBottom: SPACING.SM,
  },

  behaviorRow: { flexDirection: "row", gap: SPACING.SM, marginBottom: SPACING.XL },
  behaviorCard: {
    flex: 1,
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.MD,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
    padding: SPACING.MD,
    gap: 4,
  },
  behaviorCardActive: { borderColor: COLORS.ORANGE, backgroundColor: "rgba(255,107,0,0.08)" },
  behaviorLabel: {
    fontSize: FONT.SIZE_MD,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_ON_SURFACE,
    marginTop: 4,
  },
  behaviorLabelActive: { color: COLORS.PRIMARY },
  behaviorDesc: { fontSize: FONT.SIZE_XS, color: COLORS.TEXT_SECONDARY, lineHeight: 16 },

  amountRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.MD,
    marginBottom: SPACING.XL,
  },
  dollarSign: { paddingLeft: SPACING.MD, fontSize: 24, fontWeight: FONT.WEIGHT_BOLD, color: COLORS.PRIMARY },
  amountInput: {
    flex: 1,
    fontSize: 24,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_SURFACE,
    padding: SPACING.MD,
  },

  comparisonGrid: { gap: SPACING.SM, marginBottom: SPACING.MD },

  // Baseline card
  baselineCard: {
    backgroundColor: COLORS.SURFACE_LOW,
    borderRadius: RADIUS.MD,
    padding: SPACING.LG,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
  },
  cardTag: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 2,
    color: COLORS.DISABLED,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
    marginBottom: SPACING.MD,
  },
  bigNumber: {
    fontSize: 52,
    fontWeight: FONT.WEIGHT_BOLD,
    color: "rgba(255,255,255,0.75)",
    letterSpacing: -2,
    lineHeight: 56,
  },
  bigNumberSub: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 2,
    color: "rgba(255,255,255,0.55)",
    marginBottom: SPACING.MD,
  },
  divider: { height: 1, backgroundColor: "rgba(255,255,255,0.05)", marginVertical: SPACING.MD },
  statRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 6,
  },
  statLabel: { fontSize: FONT.SIZE_XS, textTransform: "uppercase", color: COLORS.DISABLED, letterSpacing: 1 },
  statValue: { fontSize: FONT.SIZE_MD, fontWeight: FONT.WEIGHT_BOLD, color: COLORS.TEXT_ON_SURFACE },
  activeBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: SPACING.MD,
    backgroundColor: COLORS.SURFACE_HIGHEST,
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 100,
  },
  activeDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: COLORS.DISABLED },
  activeBadgeText: { fontSize: FONT.SIZE_XS, color: COLORS.DISABLED, textTransform: "uppercase", letterSpacing: 1 },

  // Scenario card
  scenarioCard: {
    backgroundColor: "rgba(255,255,255,0.03)",
    borderRadius: RADIUS.MD,
    padding: SPACING.LG,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.1)",
  },
  scenCardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: SPACING.MD,
  },
  scenCardTag: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 2,
    color: COLORS.PRIMARY,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
  },
  scenMonthsRow: { flexDirection: "row", alignItems: "baseline", gap: SPACING.MD },
  bigNumberLight: {
    fontSize: 52,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_ON_SURFACE,
    letterSpacing: -2,
    lineHeight: 56,
  },
  deltaLabel: {
    fontSize: 24,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TERTIARY,
    letterSpacing: -0.5,
  },
  bigNumberSubLight: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 2,
    color: "rgba(255,255,255,0.4)",
    marginBottom: SPACING.MD,
  },
  dividerLight: { height: 1, backgroundColor: "rgba(255,255,255,0.1)", marginVertical: SPACING.MD },
  statLabelLight: { fontSize: FONT.SIZE_XS, textTransform: "uppercase", color: "rgba(255,255,255,0.4)", letterSpacing: 1 },
  statValueLight: { fontSize: FONT.SIZE_MD, fontWeight: FONT.WEIGHT_BOLD, color: COLORS.TEXT_ON_SURFACE },

  // Adherence
  adherenceCard: {
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.MD,
    padding: SPACING.LG,
    marginBottom: SPACING.MD,
  },
  adherenceHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: SPACING.SM,
  },
  adherenceValue: {
    fontSize: FONT.SIZE_LG,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.PRIMARY,
  },
  slider: { width: "100%", height: 32 },
  sliderLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 2,
  },
  sliderLabelText: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.DISABLED,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },

  // Metrics grid
  metricsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: SPACING.SM,
    marginBottom: SPACING.MD,
  },
  metricTile: {
    flex: 1,
    minWidth: "45%",
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.MD,
    padding: SPACING.MD,
  },
  metricTileWide: { minWidth: "100%", flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  metricTileLabel: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 1.5,
    color: COLORS.DISABLED,
    marginBottom: 4,
  },
  metricTileValue: { fontSize: 22, fontWeight: FONT.WEIGHT_BOLD, color: COLORS.TEXT_ON_SURFACE },
  metricTileSub: { fontSize: FONT.SIZE_XS, color: COLORS.DISABLED, marginTop: 2 },
  metricVerifiedRow: { flexDirection: "row", alignItems: "center", gap: 6 },

  errorCard: {
    flexDirection: "row",
    gap: SPACING.SM,
    backgroundColor: "rgba(255,180,171,0.1)",
    borderRadius: RADIUS.MD,
    borderWidth: 1,
    borderColor: "rgba(255,180,171,0.2)",
    padding: SPACING.MD,
    marginBottom: SPACING.MD,
    alignItems: "center",
  },
  errorText: { flex: 1, color: COLORS.ERROR, fontSize: FONT.SIZE_SM },

  qualityBannerWarn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "rgba(255,107,0,0.08)",
    borderRadius: RADIUS.SM,
    borderWidth: 1,
    borderColor: "rgba(255,107,0,0.2)",
    paddingHorizontal: SPACING.MD,
    paddingVertical: 6,
    marginBottom: SPACING.SM,
  },
  qualityBannerText: {
    flex: 1,
    fontSize: FONT.SIZE_XS,
    color: COLORS.ORANGE,
    letterSpacing: 0.3,
  },
  qualityBannerInfo: {
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.SM,
    paddingHorizontal: SPACING.MD,
    paddingVertical: 6,
    marginBottom: SPACING.SM,
  },
  qualityBannerInfoText: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.DISABLED,
    letterSpacing: 0.3,
  },

  loadingWrap: { alignItems: "center", paddingVertical: SPACING.XL, gap: SPACING.SM },
  loadingText: { color: COLORS.DISABLED, fontSize: FONT.SIZE_SM, letterSpacing: 1 },

  simButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.SM,
    backgroundColor: COLORS.ORANGE,
    borderRadius: RADIUS.SM,
    paddingVertical: 18,
    marginBottom: SPACING.SM,
    shadowColor: COLORS.ORANGE,
    shadowOpacity: 0.3,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 6 },
    elevation: 8,
  },
  simButtonLabel: {
    fontSize: FONT.SIZE_MD,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_ORANGE,
    textTransform: "uppercase",
    letterSpacing: 1,
  },

  actionBar: {
    flexDirection: "row",
    gap: SPACING.SM,
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.LG,
    padding: SPACING.SM,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.1)",
    marginBottom: SPACING.SM,
  },
  rejectBtn: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: RADIUS.SM,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.2)",
    alignItems: "center",
    justifyContent: "center",
  },
  rejectLabel: {
    fontSize: FONT.SIZE_SM,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_ON_SURFACE,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  acceptBtn: {
    flex: 2,
    paddingVertical: 14,
    borderRadius: RADIUS.SM,
    backgroundColor: COLORS.ORANGE,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: COLORS.ORANGE,
    shadowOpacity: 0.3,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
  acceptLabel: {
    fontSize: FONT.SIZE_SM,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_ORANGE,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
});
