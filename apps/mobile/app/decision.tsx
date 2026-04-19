/**
 * app/decision.tsx
 * Screen 5 — Decision Confirmed.
 *
 * Shown after user accepts a scenario.
 * Displays recap + session feedback stats (accepted/rejected/adherence).
 * "Run Another Simulation" → /scenario
 * "Start Over" → RESET + /goal
 */

import { MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";
import React from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { BottomNav } from "../components/BottomNav";
import { COLORS, FONT, RADIUS, SPACING } from "../constants/theme";
import { useStore } from "../lib/store";

function fmtMonths(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return `${n} month${n !== 1 ? "s" : ""}`;
}

export default function DecisionScreen(): React.JSX.Element {
  const { state, dispatch } = useStore();
  const { adherence } = state;
  const scenario = state.scenario;
  const explanation = state.explanation;

  const total = adherence.accepted + adherence.rejected;
  const acceptRate = total > 0 ? Math.round((adherence.accepted / total) * 100) : null;

  function handleNewSimulation() {
    router.push("/scenario");
  }

  function handleStartOver() {
    dispatch({ type: "RESET" });
    router.replace("/goal");
  }

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      {/* ── Top bar ── */}
      <View style={styles.topBar}>
        <Text style={styles.brand}>FinSight.ai</Text>
        <Text style={styles.navActive}>Decision</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* ── Success header ── */}
        <View style={styles.successHeader}>
          <View style={styles.checkCircle}>
            <MaterialIcons name="check" size={36} color={COLORS.TERTIARY} />
          </View>
          <Text style={styles.heading}>Simulation Accepted</Text>
          <Text style={styles.subheading}>
            This scenario has been logged. Your adherence profile has been updated for the next simulation.
          </Text>
        </View>

        {/* ── Accepted scenario recap ── */}
        {scenario && (
          <View style={styles.recapCard}>
            <Text style={styles.recapTitle}>What You Committed To</Text>

            <View style={styles.recapRow}>
              <Text style={styles.recapLabel}>Time Saved</Text>
              <Text style={[styles.recapValue, { color: COLORS.TERTIARY }]}>
                {scenario.delta_months !== null && scenario.delta_months > 0
                  ? `−${scenario.delta_months} months`
                  : "No change"}
              </Text>
            </View>
            <View style={styles.divider} />

            <View style={styles.recapRow}>
              <Text style={styles.recapLabel}>New Timeline</Text>
              <Text style={styles.recapValue}>{fmtMonths(scenario.scenario_months)}</Text>
            </View>
            <View style={styles.divider} />

            <View style={styles.recapRow}>
              <Text style={styles.recapLabel}>Adjusted Cashflow</Text>
              <Text style={styles.recapValue}>
                ${Math.abs(scenario.scenario_monthly_cashflow).toLocaleString()}/mo
              </Text>
            </View>

            {explanation && (
              <View style={styles.explainRow}>
                <MaterialIcons name="bolt" size={14} color={COLORS.TERTIARY} />
                <Text style={styles.explainText}>{explanation.recommendation}</Text>
              </View>
            )}
          </View>
        )}

        {/* ── Session feedback stats ── */}
        <View style={styles.statsCard}>
          <Text style={styles.statsTitle}>Session Intelligence</Text>

          <View style={styles.statsGrid}>
            <View style={styles.statTile}>
              <Text style={[styles.statNum, { color: COLORS.TERTIARY }]}>{adherence.accepted}</Text>
              <Text style={styles.statLabel}>Accepted</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statTile}>
              <Text style={[styles.statNum, { color: COLORS.ERROR }]}>{adherence.rejected}</Text>
              <Text style={styles.statLabel}>Rejected</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statTile}>
              <Text style={[styles.statNum, { color: COLORS.PRIMARY }]}>
                {Math.round(adherence.current * 100)}%
              </Text>
              <Text style={styles.statLabel}>Next Adherence</Text>
            </View>
          </View>

          {acceptRate !== null && (
            <View style={styles.acceptRateRow}>
              <View style={styles.acceptRateBar}>
                <View style={[styles.acceptRateFill, { width: `${acceptRate}%` as any }]} />
              </View>
              <Text style={styles.acceptRateLabel}>{acceptRate}% acceptance rate this session</Text>
            </View>
          )}

          <Text style={styles.adaptNote}>
            Your next simulation will start at {Math.round(adherence.current * 100)}% adherence based on your history.
          </Text>
        </View>

        {/* ── Actions ── */}
        <TouchableOpacity style={styles.primaryBtn} onPress={handleNewSimulation} activeOpacity={0.85}>
          <MaterialIcons name="insights" size={18} color={COLORS.TEXT_ON_ORANGE} />
          <Text style={styles.primaryBtnLabel}>Run Another Simulation</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.ghostBtn} onPress={handleStartOver} activeOpacity={0.7}>
          <MaterialIcons name="refresh" size={16} color="rgba(255,255,255,0.4)" />
          <Text style={styles.ghostBtnLabel}>Start Over with New Goal</Text>
        </TouchableOpacity>
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
  brand: { fontSize: 20, fontWeight: FONT.WEIGHT_BOLD, color: COLORS.ORANGE, letterSpacing: -0.5 },
  navActive: {
    fontSize: FONT.SIZE_SM,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.ORANGE,
    borderBottomWidth: 2,
    borderBottomColor: COLORS.ORANGE,
    paddingBottom: 2,
  },

  content: { paddingHorizontal: SPACING.LG, paddingBottom: 40 },

  successHeader: {
    alignItems: "center",
    paddingTop: SPACING.XXL,
    paddingBottom: SPACING.XL,
  },
  checkCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: "rgba(120,220,119,0.12)",
    borderWidth: 2,
    borderColor: "rgba(120,220,119,0.3)",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: SPACING.LG,
  },
  heading: {
    fontSize: 30,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_SURFACE,
    letterSpacing: -1,
    marginBottom: SPACING.SM,
    textAlign: "center",
  },
  subheading: {
    fontSize: FONT.SIZE_SM,
    color: "rgba(255,255,255,0.45)",
    textAlign: "center",
    lineHeight: 20,
    maxWidth: 280,
  },

  recapCard: {
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.MD,
    padding: SPACING.LG,
    marginBottom: SPACING.MD,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.TERTIARY,
  },
  recapTitle: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 2,
    color: "rgba(255,255,255,0.4)",
    fontWeight: FONT.WEIGHT_SEMIBOLD,
    marginBottom: SPACING.MD,
  },
  recapRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: SPACING.SM,
  },
  recapLabel: { fontSize: FONT.SIZE_SM, color: "rgba(255,255,255,0.45)" },
  recapValue: {
    fontSize: FONT.SIZE_MD,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_ON_SURFACE,
  },
  divider: { height: 1, backgroundColor: "rgba(255,255,255,0.05)" },
  explainRow: {
    flexDirection: "row",
    gap: SPACING.XS,
    marginTop: SPACING.MD,
    alignItems: "flex-start",
    backgroundColor: "rgba(120,220,119,0.06)",
    borderRadius: RADIUS.SM,
    padding: SPACING.SM,
  },
  explainText: {
    flex: 1,
    fontSize: FONT.SIZE_XS,
    color: "rgba(255,255,255,0.55)",
    lineHeight: 18,
  },

  statsCard: {
    backgroundColor: COLORS.SURFACE_HIGH,
    borderRadius: RADIUS.MD,
    padding: SPACING.LG,
    marginBottom: SPACING.LG,
  },
  statsTitle: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 2,
    color: "rgba(255,255,255,0.4)",
    fontWeight: FONT.WEIGHT_SEMIBOLD,
    marginBottom: SPACING.LG,
  },
  statsGrid: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: SPACING.LG,
  },
  statTile: { flex: 1, alignItems: "center" },
  statNum: { fontSize: 28, fontWeight: FONT.WEIGHT_EXTRABOLD, letterSpacing: -0.5 },
  statLabel: {
    fontSize: FONT.SIZE_XS,
    color: "rgba(255,255,255,0.4)",
    textTransform: "uppercase",
    letterSpacing: 1,
    marginTop: 4,
  },
  statDivider: {
    width: 1,
    height: 40,
    backgroundColor: "rgba(255,255,255,0.08)",
  },

  acceptRateRow: { marginBottom: SPACING.MD },
  acceptRateBar: {
    height: 4,
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: 2,
    overflow: "hidden",
    marginBottom: 6,
  },
  acceptRateFill: {
    height: "100%",
    backgroundColor: COLORS.TERTIARY,
    borderRadius: 2,
  },
  acceptRateLabel: {
    fontSize: FONT.SIZE_XS,
    color: "rgba(255,255,255,0.4)",
    textAlign: "right",
  },
  adaptNote: {
    fontSize: FONT.SIZE_XS,
    color: "rgba(255,255,255,0.35)",
    lineHeight: 18,
    fontStyle: "italic",
  },

  primaryBtn: {
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
  primaryBtnLabel: {
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
    paddingVertical: 14,
  },
  ghostBtnLabel: {
    fontSize: FONT.SIZE_SM,
    color: "rgba(255,255,255,0.4)",
  },
});
