/**
 * app/goal.tsx
 * Screen 1 — Define Your Objective.
 *
 * User selects a goal type, enters target amount + deadline.
 * Dispatches SET_GOAL and navigates to /input.
 */

import { MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useState } from "react";
import {
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
import { BottomNav } from "../components/BottomNav";
import { COLORS, FONT, RADIUS, SPACING } from "../constants/theme";
import { EVENTS, track } from "../lib/analytics";
import { useStore } from "../lib/store";
import type { GoalData } from "../lib/types";

type GoalType = GoalData["type"];

const GOAL_OPTIONS: {
  type: GoalType;
  label: string;
  description: string;
  icon: keyof typeof MaterialIcons.glyphMap;
  founderTag?: boolean;
}[] = [
  { type: "extend_runway",  label: "Extend Runway",   description: "Build personal runway to survive pre-revenue.", icon: "flight-takeoff", founderTag: true },
  { type: "emergency_fund", label: "Emergency Fund",  description: "Liquid capital for unforeseen volatility.", icon: "savings" },
  { type: "build_wealth",   label: "Build Wealth",    description: "Long-term capital appreciation.", icon: "trending-up" },
  { type: "pay_off_debt",   label: "Pay Off Debt",    description: "Eliminate high-interest liabilities.", icon: "credit-card-off" },
  { type: "custom",         label: "Custom Objective", description: "Define your own parameters.", icon: "architecture" },
];

export default function GoalScreen(): React.JSX.Element {
  const { dispatch } = useStore();
  const [selectedType, setSelectedType] = useState<GoalType | null>(null);
  const [targetAmount, setTargetAmount] = useState("");
  const [deadline, setDeadline] = useState("");
  const [error, setError] = useState<string | null>(null);

  function parseDeadline(raw: string): string | null {
    // Accept MM/DD/YYYY → convert to YYYY-MM-DD for backend
    const match = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (!match) return null;
    const [, mm, dd, yyyy] = match;
    return `${yyyy}-${mm.padStart(2, "0")}-${dd.padStart(2, "0")}`;
  }

  function validate(): GoalData | null {
    if (!selectedType) { setError("Select a goal type."); return null; }
    const amount = parseFloat(targetAmount.replace(/,/g, ""));
    if (isNaN(amount) || amount <= 0) { setError("Enter a valid target amount."); return null; }
    const isoDeadline = parseDeadline(deadline);
    if (!isoDeadline) { setError("Enter deadline as MM/DD/YYYY."); return null; }
    setError(null);
    return { type: selectedType, target_amount: amount, deadline: isoDeadline };
  }

  function handleContinue() {
    const goal = validate();
    if (!goal) return;
    dispatch({ type: "SET_GOAL", payload: goal });
    track("goal_created", { goal_type: goal.type, target_amount: goal.target_amount });
    router.push("/input");
  }

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        {/* ── Top bar ── */}
        <View style={styles.topBar}>
          <Text style={styles.brand}>FinSight.ai</Text>
          <MaterialIcons name="account-circle" size={26} color={COLORS.DISABLED} />
        </View>

        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          {/* ── Header ── */}
          <View style={styles.header}>
            <Text style={styles.moduleLabel}>Step 1 of 3</Text>
            <Text style={styles.heading}>What are you{"\n"}working toward?</Text>
          </View>

          {/* ── Goal cards ── */}
          <Text style={styles.sectionLabel}>Pick your focus</Text>
          <View style={styles.cardGrid}>
            {GOAL_OPTIONS.slice(0, 4).map((opt) => {
              const active = selectedType === opt.type;
              return (
                <TouchableOpacity
                  key={opt.type}
                  style={[styles.goalCard, active && styles.goalCardActive]}
                  onPress={() => setSelectedType(opt.type)}
                  activeOpacity={0.75}
                >
                  <MaterialIcons name={opt.icon} size={24} color={active ? COLORS.ORANGE : COLORS.PRIMARY} />
                  <Text style={[styles.goalLabel, active && styles.goalLabelActive]}>{opt.label}</Text>
                  <Text style={styles.goalDesc}>{opt.description}</Text>
                  {opt.founderTag && (
                    <View style={styles.founderBadge}>
                      <Text style={styles.founderBadgeText}>FOR FOUNDERS</Text>
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Custom (full-width) */}
          {(() => {
            const opt = GOAL_OPTIONS[4];
            const active = selectedType === opt.type;
            return (
              <TouchableOpacity
                style={[styles.goalCardWide, active && styles.goalCardActive]}
                onPress={() => setSelectedType(opt.type)}
                activeOpacity={0.75}
              >
                <MaterialIcons name={opt.icon} size={24} color={active ? COLORS.ORANGE : COLORS.PRIMARY} />
                <View style={styles.wideText}>
                  <Text style={[styles.goalLabel, active && styles.goalLabelActive]}>{opt.label}</Text>
                  <Text style={styles.goalDesc}>{opt.description}</Text>
                </View>
              </TouchableOpacity>
            );
          })()}

          {/* ── Target capital ── */}
          <View style={styles.inputSection}>
            <Text style={styles.fieldLabel}>Target Amount</Text>
            <View style={styles.amountRow}>
              <Text style={styles.dollarSign}>$</Text>
              <TextInput
                style={styles.amountInput}
                value={targetAmount}
                onChangeText={setTargetAmount}
                placeholder="0.00"
                placeholderTextColor="rgba(255,255,255,0.4)"
                keyboardType="numeric"
                returnKeyType="next"
              />
            </View>
          </View>

          {/* ── Deadline ── */}
          <View style={styles.inputSection}>
            <Text style={styles.fieldLabel}>By when? (MM/DD/YYYY)</Text>
            <View style={styles.dateRow}>
              <TextInput
                style={styles.dateInput}
                value={deadline}
                onChangeText={setDeadline}
                placeholder="12/31/2027"
                placeholderTextColor="rgba(255,255,255,0.4)"
                keyboardType="numbers-and-punctuation"
                returnKeyType="done"
                onSubmitEditing={handleContinue}
              />
              <MaterialIcons name="calendar-today" size={20} color={COLORS.DISABLED} style={styles.calIcon} />
            </View>
          </View>

          {error ? <Text style={styles.errorText}>{error}</Text> : null}

          {/* ── CTA ── */}
          <TouchableOpacity style={styles.ctaButton} onPress={handleContinue} activeOpacity={0.85}>
            <Text style={styles.ctaLabel}>Set Goal</Text>
            <MaterialIcons name="bolt" size={20} color={COLORS.TEXT_ON_ORANGE} />
          </TouchableOpacity>

          {/* ── Encryption note ── */}
          <View style={styles.securityRow}>
            <MaterialIcons name="lock" size={12} color={COLORS.DISABLED} />
            <Text style={styles.securityText}>End-to-End Encryption Active</Text>
          </View>
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
  brand: {
    fontSize: 20,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.ORANGE,
    letterSpacing: -0.5,
  },

  content: {
    paddingHorizontal: SPACING.LG,
    paddingBottom: 40,
  },

  header: {
    paddingTop: SPACING.XL,
    marginBottom: SPACING.XL,
  },
  moduleLabel: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.TEXT_SECONDARY,
    textTransform: "uppercase",
    letterSpacing: 2,
    marginBottom: SPACING.SM,
  },
  heading: {
    fontSize: 38,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_SURFACE,
    letterSpacing: -1.5,
    lineHeight: 44,
  },

  sectionLabel: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.PRIMARY,
    textTransform: "uppercase",
    letterSpacing: 2,
    marginBottom: SPACING.MD,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
  },

  cardGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: SPACING.SM,
    marginBottom: SPACING.SM,
  },
  goalCard: {
    width: "48%",
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.MD,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
    padding: SPACING.MD,
    gap: SPACING.XS,
  },
  goalCardWide: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.MD,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
    padding: SPACING.MD,
    gap: SPACING.MD,
    marginBottom: SPACING.XL,
  },
  goalCardActive: {
    borderColor: COLORS.ORANGE,
    backgroundColor: "rgba(255,107,0,0.08)",
  },
  wideText: { flex: 1 },
  goalLabel: {
    fontSize: FONT.SIZE_MD,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_ON_SURFACE,
  },
  goalLabelActive: { color: COLORS.PRIMARY },
  goalDesc: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.TEXT_SECONDARY,
    lineHeight: 16,
    marginTop: 2,
  },
  founderBadge: {
    alignSelf: "flex-start",
    backgroundColor: "rgba(255,107,0,0.15)",
    borderWidth: 1,
    borderColor: "rgba(255,107,0,0.3)",
    borderRadius: RADIUS.PILL,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginTop: SPACING.XS,
  },
  founderBadgeText: {
    fontSize: 8,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.ORANGE,
    letterSpacing: 1.2,
  },

  inputSection: { marginBottom: SPACING.LG },
  fieldLabel: {
    fontSize: FONT.SIZE_XS,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
    color: COLORS.TEXT_SECONDARY,
    textTransform: "uppercase",
    letterSpacing: 2,
    marginBottom: SPACING.SM,
  },

  amountRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.MD,
    overflow: "hidden",
  },
  dollarSign: {
    fontSize: 28,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.PRIMARY,
    paddingLeft: SPACING.MD,
  },
  amountInput: {
    flex: 1,
    fontSize: 28,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_SURFACE,
    padding: SPACING.MD,
  },

  dateRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.MD,
  },
  dateInput: {
    flex: 1,
    fontSize: FONT.SIZE_LG,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_ON_SURFACE,
    padding: SPACING.MD,
  },
  calIcon: { marginRight: SPACING.MD },

  errorText: {
    color: COLORS.ERROR,
    fontSize: FONT.SIZE_SM,
    marginBottom: SPACING.MD,
  },

  ctaButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.SM,
    backgroundColor: COLORS.ORANGE,
    borderRadius: RADIUS.SM,
    paddingVertical: 18,
    marginBottom: SPACING.MD,
    shadowColor: COLORS.ORANGE,
    shadowOpacity: 0.35,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 6 },
    elevation: 8,
  },
  ctaLabel: {
    fontSize: FONT.SIZE_LG,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_ORANGE,
    letterSpacing: -0.3,
  },

  securityRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.XS,
    opacity: 0.5,
    marginTop: SPACING.SM,
  },
  securityText: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.TEXT_SECONDARY,
    textTransform: "uppercase",
    letterSpacing: 1.5,
  },
});
