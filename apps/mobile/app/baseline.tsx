/**
 * app/baseline.tsx
 * Screen 3 — Financial Baseline.
 *
 * Calls POST /baseline on mount. Displays cashflow, savings rate,
 * time to goal, and monthly gap. CTA navigates to /scenario.
 */

import { MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { BottomNav } from "../components/BottomNav";
import { COLORS, FONT, RADIUS, SPACING } from "../constants/theme";
import { fetchBaseline } from "../lib/api";
import { useStore } from "../lib/store";
import type { ApiError, BaselineResult } from "../lib/types";

// Offline fallback — used when backend is unreachable
function buildOfflineFallback(snapshot: any): BaselineResult {
  const cashflow = snapshot.cashflow?.monthly ?? 0;
  const income   = snapshot.income?.monthly ?? 1;
  const balance  = snapshot.savings?.balance ?? 0;
  const goal     = snapshot.goal?.target_amount ?? 0;
  const remaining = Math.max(0, goal - balance);
  const months = cashflow > 0 ? Math.ceil(remaining / cashflow) : null;
  return {
    monthly_cashflow: cashflow,
    savings_rate: income > 0 ? (cashflow / income) * 100 : 0,
    time_to_goal_months: months,
    monthly_savings_gap: 0,
    goal_already_met: balance >= goal,
  };
}
import { EVENTS, track } from "../lib/analytics";

function fmtCurrency(n: number): string {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}
function fmtMonths(n: number | null): string {
  if (n === null) return "Unreachable";
  if (n === 0) return "Already met!";
  return `${n} months`;
}

type Highlight = "positive" | "negative" | "neutral";

function MetricCard({
  label,
  value,
  subtext,
  highlight = "neutral",
  icon,
}: {
  label: string;
  value: string;
  subtext?: string;
  highlight?: Highlight;
  icon: keyof typeof MaterialIcons.glyphMap;
}) {
  const valueColor =
    highlight === "positive" ? COLORS.TERTIARY :
    highlight === "negative" ? COLORS.ERROR :
    COLORS.TEXT_ON_SURFACE;

  return (
    <View style={metricStyles.card}>
      <View style={metricStyles.iconWrap}>
        <MaterialIcons name={icon} size={18} color={COLORS.PRIMARY} />
      </View>
      <View style={metricStyles.body}>
        <Text style={metricStyles.label}>{label}</Text>
        <Text style={[metricStyles.value, { color: valueColor }]}>{value}</Text>
        {subtext ? <Text style={metricStyles.sub}>{subtext}</Text> : null}
      </View>
    </View>
  );
}

const metricStyles = StyleSheet.create({
  card: {
    flexDirection: "row",
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.MD,
    padding: SPACING.LG,
    marginBottom: SPACING.SM,
    borderLeftWidth: 3,
    borderLeftColor: "rgba(255,182,147,0.25)",
    gap: SPACING.MD,
    alignItems: "flex-start",
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: RADIUS.MD,
    backgroundColor: COLORS.SURFACE_HIGHEST,
    alignItems: "center",
    justifyContent: "center",
  },
  body: { flex: 1 },
  label: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 1.5,
    color: COLORS.DISABLED,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
    marginBottom: 4,
  },
  value: {
    fontSize: 26,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    letterSpacing: -0.8,
    marginBottom: 2,
  },
  sub: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.DISABLED,
  },
});

export default function BaselineScreen(): React.JSX.Element {
  const { state, dispatch } = useStore();
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);

  // Personal Runway: if income dropped to $0 tomorrow, how many months on savings?
  const personalRunway: number | null = (() => {
    const snap = state.snapshot;
    if (!snap) return null;
    const burn = snap.expenses.total;
    if (burn <= 0) return null;
    return Math.floor(snap.savings.balance / burn);
  })();
  const isFounderGoal = state.snapshot?.goal?.type === "extend_runway";

  const load = useCallback(async () => {
    if (!state.snapshot) { setApiError("No snapshot found. Please go back."); return; }
    setLoading(true);
    setApiError(null);
    try {
      const res = await fetchBaseline(state.snapshot);
      dispatch({ type: "SET_BASELINE", payload: res.data });
      setIsOffline(false);
      track(EVENTS.BASELINE_GENERATED, {
        time_to_goal: res.data.time_to_goal_months,
        cashflow: res.data.monthly_cashflow,
        savings_rate: res.data.savings_rate,
      });
    } catch (err) {
      const e = err as ApiError;
      const msg = e.message?.toLowerCase() ?? "";
      const isNetworkErr = msg.includes("network") || msg.includes("fetch") ||
                           msg.includes("failed") || msg.includes("connect");
      if (isNetworkErr) {
        // Backend offline — compute baseline client-side from snapshot
        const fallback = buildOfflineFallback(state.snapshot);
        dispatch({ type: "SET_BASELINE", payload: fallback });
        setIsOffline(true);
        track(EVENTS.BASELINE_OFFLINE, { cashflow: fallback.monthly_cashflow });
      } else {
        setApiError(e.message ?? "Failed to compute baseline.");
      }
    } finally {
      setLoading(false);
    }
  }, [state.snapshot, dispatch]);

  useEffect(() => { if (!state.baseline) load(); }, []);

  const b = state.baseline;

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      {/* ── Top bar ── */}
      <View style={styles.topBar}>
        <Text style={styles.brand}>FinSight.ai</Text>
        <View style={styles.navLinks}>
          <Text style={styles.navInactive}>Goal</Text>
          <Text style={styles.navInactive}>Input</Text>
          <Text style={styles.navActive}>Baseline</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* ── Header ── */}
        <View style={styles.header}>
          <Text style={styles.moduleLabel}>Intelligence Layer</Text>
          <Text style={styles.heading}>Your Financial{"\n"}Baseline</Text>
          <Text style={styles.subheading}>This is where you stand today — before any changes.</Text>
        </View>

        {/* ── Offline banner ── */}
        {isOffline && (
          <View style={styles.offlineBanner}>
            <MaterialIcons name="offline-bolt" size={14} color={COLORS.PRIMARY} />
            <Text style={styles.offlineText}>
              Offline mode — results computed locally. Start backend for full accuracy.
            </Text>
          </View>
        )}

        {/* ── Loading ── */}
        {loading && (
          <View style={styles.loadingWrap}>
            <ActivityIndicator size="large" color={COLORS.ORANGE} />
            <Text style={styles.loadingText}>Computing your baseline...</Text>
          </View>
        )}

        {/* ── Error ── */}
        {apiError && (
          <View style={styles.errorCard}>
            <MaterialIcons name="error-outline" size={20} color={COLORS.ERROR} />
            <Text style={styles.errorText}>{apiError}</Text>
          </View>
        )}

        {/* ── Metrics ── */}
        {!loading && b && (
          <>
            <MetricCard
              icon="swap-horiz"
              label="Monthly Cashflow"
              value={fmtCurrency(b.monthly_cashflow)}
              highlight={b.monthly_cashflow >= 0 ? "positive" : "negative"}
            />
            <MetricCard
              icon="percent"
              label="Savings Rate"
              value={`${b.savings_rate.toFixed(1)}%`}
              subtext="of monthly income"
              highlight={b.savings_rate >= 20 ? "positive" : b.savings_rate > 0 ? "neutral" : "negative"}
            />
            <MetricCard
              icon="schedule"
              label="Time to Goal"
              value={fmtMonths(b.time_to_goal_months)}
              subtext={b.goal_already_met ? "🎉 Already achieved!" : undefined}
              highlight={b.goal_already_met ? "positive" : b.time_to_goal_months === null ? "negative" : "neutral"}
            />

            {/* ── Personal Runway (always shown, critical for founders) ── */}
            {personalRunway !== null && (
              <MetricCard
                icon="flight-takeoff"
                label="Personal Runway"
                value={fmtMonths(personalRunway)}
                subtext={
                  isFounderGoal
                    ? "months you can survive if revenue drops to $0"
                    : "months of expenses covered by savings"
                }
                highlight={
                  personalRunway >= 12 ? "positive" :
                  personalRunway >= 6  ? "neutral" : "negative"
                }
              />
            )}

            {!b.goal_already_met && b.monthly_savings_gap > 0 && (
              <MetricCard
                icon="trending-down"
                label="Monthly Savings Gap"
                value={fmtCurrency(b.monthly_savings_gap)}
                subtext="extra needed to hit your deadline"
                highlight="negative"
              />
            )}

            {/* ── Probability insight ── */}
            <View style={styles.insightCard}>
              <View style={styles.insightHeader}>
                <MaterialIcons name="bolt" size={16} color={COLORS.TERTIARY} />
                <Text style={styles.insightTitle}>AI Baseline Analysis</Text>
              </View>
              <Text style={styles.insightText}>
                {isFounderGoal && personalRunway !== null
                  ? personalRunway >= 12
                    ? `Your personal runway is ${personalRunway} months — solid pre-fundraising buffer. Simulate a burn reduction to extend it further before your next raise.`
                    : `Your personal runway is only ${personalRunway} months. This limits your negotiating power with investors. Simulate a expense cut to extend your runway now.`
                  : b.monthly_cashflow > 0
                    ? `With a monthly cashflow of ${fmtCurrency(b.monthly_cashflow)}, your current trajectory places your goal at ${fmtMonths(b.time_to_goal_months)}. Simulating a behavioral change can accelerate this.`
                    : "Your current expenses exceed income. A scenario simulation can identify the fastest path to a positive cashflow."}
              </Text>
            </View>

            {/* ── CTA ── */}
            <TouchableOpacity style={styles.ctaButton} onPress={() => router.push("/scenario")} activeOpacity={0.85}>
              <Text style={styles.ctaLabel}>Simulate a Change</Text>
              <MaterialIcons name="insights" size={20} color={COLORS.TEXT_ON_ORANGE} />
            </TouchableOpacity>

            <TouchableOpacity style={styles.ghostBtn} onPress={load} activeOpacity={0.7}>
              <MaterialIcons name="refresh" size={16} color={COLORS.DISABLED} />
              <Text style={styles.ghostLabel}>Recalculate</Text>
            </TouchableOpacity>
          </>
        )}

        {/* ── No data ── */}
        {!loading && !b && !apiError && (
          <TouchableOpacity style={styles.ctaButton} onPress={load} activeOpacity={0.85}>
            <Text style={styles.ctaLabel}>Load Baseline</Text>
            <MaterialIcons name="bolt" size={20} color={COLORS.TEXT_ON_ORANGE} />
          </TouchableOpacity>
        )}
      </ScrollView>
      <BottomNav />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.BACKGROUND },

  topBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: SPACING.LG,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(255,255,255,0.05)",
  },
  brand: {
    fontSize: 20,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.ORANGE,
    letterSpacing: -0.5,
  },
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
    fontSize: 34,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_SURFACE,
    letterSpacing: -1.2,
    lineHeight: 40,
    marginBottom: SPACING.SM,
  },
  subheading: {
    fontSize: FONT.SIZE_MD,
    color: COLORS.TEXT_SECONDARY,
    lineHeight: 22,
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
  loadingWrap: { alignItems: "center", paddingVertical: SPACING.XXL, gap: SPACING.MD },
  loadingText: { color: COLORS.DISABLED, fontSize: FONT.SIZE_SM, letterSpacing: 1 },

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
  errorText: { flex: 1, color: COLORS.ERROR, fontSize: FONT.SIZE_SM, lineHeight: 18 },

  insightCard: {
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.MD,
    padding: SPACING.LG,
    marginTop: SPACING.SM,
    marginBottom: SPACING.LG,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.TERTIARY,
  },
  insightHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.XS,
    marginBottom: SPACING.SM,
  },
  insightTitle: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 1.5,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TERTIARY,
  },
  insightText: {
    fontSize: FONT.SIZE_SM,
    color: COLORS.TEXT_SECONDARY,
    lineHeight: 20,
  },

  ctaButton: {
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
  ctaLabel: {
    fontSize: FONT.SIZE_MD,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_ORANGE,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  ghostBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.XS,
    paddingVertical: 12,
    marginBottom: SPACING.MD,
  },
  ghostLabel: { fontSize: FONT.SIZE_SM, color: COLORS.DISABLED },
});