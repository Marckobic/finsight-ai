/**
 * app/input.tsx
 * Screen 2 — Capture Current Reality.
 *
 * Income streams, fixed/variable expenses, current liquidity.
 * Live cashflow preview. Dispatches SET_SNAPSHOT → navigates /baseline.
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
import type { FinancialSnapshot } from "../lib/types";

type FieldKey = "income" | "taxRate" | "rent" | "utilities" | "debt" | "groceries" | "lifestyle" | "travel" | "savingsBalance" | "emergencyReserve";

const FIELD_DEFAULTS: Record<FieldKey, string> = {
  income: "",
  taxRate: "",
  rent: "",
  utilities: "",
  debt: "",
  groceries: "",
  lifestyle: "",
  travel: "",
  savingsBalance: "",
  emergencyReserve: "",
};

function InputField({
  label,
  value,
  onChange,
  prefix = "$",
  suffix,
  placeholder = "0.00",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  prefix?: string | null;
  suffix?: string;
  placeholder?: string;
}) {
  return (
    <View style={fieldStyles.wrap}>
      <Text style={fieldStyles.label}>{label}</Text>
      <View style={fieldStyles.row}>
        {prefix ? <Text style={fieldStyles.prefix}>{prefix}</Text> : null}
        <TextInput
          style={fieldStyles.input}
          value={value}
          onChangeText={onChange}
          placeholder={placeholder}
          placeholderTextColor="rgba(255,255,255,0.4)"
          keyboardType="numeric"
          returnKeyType="next"
        />
        {suffix ? <Text style={fieldStyles.suffix}>{suffix}</Text> : null}
      </View>
    </View>
  );
}

const fieldStyles = StyleSheet.create({
  wrap: { marginBottom: SPACING.LG },
  label: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 1.5,
    color: "rgba(255,255,255,0.45)",
    marginBottom: 6,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.SM,
  },
  prefix: {
    paddingLeft: SPACING.MD,
    fontSize: FONT.SIZE_LG,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.PRIMARY,
  },
  suffix: {
    paddingRight: SPACING.MD,
    fontSize: FONT.SIZE_LG,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.PRIMARY,
  },
  input: {
    flex: 1,
    fontSize: FONT.SIZE_LG,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_ON_SURFACE,
    padding: SPACING.MD,
  },
});

export default function InputScreen(): React.JSX.Element {
  const { state, dispatch } = useStore();
  const [values, setValues] = useState<Record<FieldKey, string>>(FIELD_DEFAULTS);
  const [incomeVolatile, setIncomeVolatile] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function n(key: FieldKey) { return parseFloat(values[key].replace(/,/g, "")) || 0; }
  function set(key: FieldKey) { return (t: string) => setValues((v) => ({ ...v, [key]: t })); }

  const grossAnnual   = n("income");
  const taxRate       = Math.min(Math.max(n("taxRate"), 0), 99); // clamp 0–99%
  const taxAmount     = grossAnnual * (taxRate / 100);
  const netAnnual     = grossAnnual - taxAmount;
  const monthlyIncome = netAnnual / 12;             // after-tax annual → monthly
  const totalFixed    = n("rent") + n("utilities") + n("debt");
  const totalVariable = n("groceries") + n("lifestyle") + n("travel");
  const totalOutflow  = totalFixed + totalVariable;
  const surplus       = monthlyIncome - totalOutflow;
  const savingsRate   = monthlyIncome > 0 ? ((surplus / monthlyIncome) * 100).toFixed(1) : "0.0";

  function validate(): FinancialSnapshot | null {
    if (!state.goal) { setError("Goal missing. Please go back."); return null; }
    if (n("income") <= 0) { setError("Annual income must be > 0."); return null; }
    setError(null);
    return {
      user_id: "user-mvp",
      snapshot_date: new Date().toISOString().split("T")[0],
      income: {
        monthly: monthlyIncome,
        income_type: incomeVolatile ? "variable" : "stable",
        income_volatile: incomeVolatile,
      },
      expenses: {
        fixed: totalFixed,
        variable: totalVariable,
        total: totalOutflow,
      },
      savings: {
        balance: n("savingsBalance"),
        monthly_contribution: Math.max(0, surplus),
      },
      cashflow: { monthly: surplus },
      goal: state.goal,
    };
  }

  function handleContinue() {
    const snapshot = validate();
    if (!snapshot) return;
    dispatch({ type: "SET_SNAPSHOT", payload: snapshot });
    track("snapshot_submitted", { monthly_cashflow: surplus });
    router.push("/baseline");
  }

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        {/* ── Top bar ── */}
        <View style={styles.topBar}>
          <Text style={styles.brand}>FinSight.ai</Text>
          <View style={styles.navLinks}>
            <Text style={styles.navInactive}>Goal</Text>
            <Text style={styles.navActive}>Input</Text>
            <Text style={styles.navInactive}>Baseline</Text>
          </View>
        </View>

        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          {/* ── Header ── */}
          <View style={styles.header}>
            <Text style={styles.moduleLabel}>Reality Layer</Text>
            <Text style={styles.heading}>Capture Current{"\n"}Reality</Text>
            <Text style={styles.subheading}>Precision here drives accuracy of your intelligence baseline.</Text>
          </View>

          {/* ── Income Streams ── */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <View>
                <Text style={styles.sectionLabel}>Annual Inflow</Text>
                <Text style={styles.sectionTitle}>Income Streams</Text>
                {state.goal?.type === "extend_runway" && (
                  <Text style={styles.founderHint}>Pre-revenue? Enter $0 — runway is calculated from savings.</Text>
                )}
              </View>
              <View style={styles.toggleRow}>
                <TouchableOpacity
                  style={[styles.toggleBtn, !incomeVolatile && styles.toggleBtnActive]}
                  onPress={() => setIncomeVolatile(false)}
                  activeOpacity={0.8}
                >
                  <Text style={[styles.toggleLabel, !incomeVolatile && styles.toggleLabelActive]}>Stable</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.toggleBtn, incomeVolatile && styles.toggleBtnActive]}
                  onPress={() => setIncomeVolatile(true)}
                  activeOpacity={0.8}
                >
                  <Text style={[styles.toggleLabel, incomeVolatile && styles.toggleLabelActive]}>Variable</Text>
                </TouchableOpacity>
              </View>
            </View>
            <InputField label="Annual Salary (Gross)" value={values.income} onChange={set("income")} />
            <InputField
              label="Estimated Tax Rate"
              value={values.taxRate}
              onChange={set("taxRate")}
              prefix={null}
              suffix="%"
              placeholder="25"
            />
          </View>

          {/* ── Fixed Expenses ── */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>Fixed Liabilities</Text>
            <InputField label="Rent / Mortgage"   value={values.rent}      onChange={set("rent")} />
            <InputField label="Utilities & Comms" value={values.utilities} onChange={set("utilities")} />
            <InputField label="Debt Service"       value={values.debt}      onChange={set("debt")} />
          </View>

          {/* ── Variable Expenses ── */}
          <View style={styles.section}>
            <Text style={styles.sectionLabel}>Variable Lifestyle</Text>
            <InputField label="Groceries & Food" value={values.groceries} onChange={set("groceries")} />
            <InputField label="Lifestyle & Fun"  value={values.lifestyle} onChange={set("lifestyle")} />
            <InputField label="Travel Fund"       value={values.travel}    onChange={set("travel")} />
          </View>

          {/* ── Current Liquidity ── */}
          <View style={styles.section}>
            <View style={styles.liquidityHeader}>
              <MaterialIcons name="account-balance-wallet" size={20} color={COLORS.PRIMARY} />
              <Text style={styles.sectionTitle}>Current Liquidity</Text>
            </View>
            <View style={styles.liquidityGrid}>
              <View style={styles.liquidityCard}>
                <Text style={styles.liquidityLabel}>Savings Balance</Text>
                <View style={fieldStyles.row}>
                  <Text style={fieldStyles.prefix}>$</Text>
                  <TextInput
                    style={fieldStyles.input}
                    value={values.savingsBalance}
                    onChangeText={set("savingsBalance")}
                    placeholder="0.00"
                    placeholderTextColor="rgba(255,255,255,0.4)"
                    keyboardType="numeric"
                  />
                </View>
              </View>
              <View style={styles.liquidityCard}>
                <Text style={styles.liquidityLabel}>Emergency Reserve</Text>
                <View style={fieldStyles.row}>
                  <Text style={fieldStyles.prefix}>$</Text>
                  <TextInput
                    style={fieldStyles.input}
                    value={values.emergencyReserve}
                    onChangeText={set("emergencyReserve")}
                    placeholder="0.00"
                    placeholderTextColor="rgba(255,255,255,0.4)"
                    keyboardType="numeric"
                  />
                </View>
              </View>
            </View>
          </View>

          {/* ── Intelligence Preview ── */}
          <View style={styles.previewCard}>
            <Text style={styles.previewTitle}>Intelligence Preview</Text>
            <View style={styles.previewRow}>
              <Text style={styles.previewRowLabel}>Gross Annual</Text>
              <Text style={styles.previewRowValue}>${grossAnnual.toLocaleString()}</Text>
            </View>
            {taxRate > 0 && (
              <View style={styles.previewRow}>
                <Text style={styles.previewRowLabel}>Tax ({taxRate}%)</Text>
                <Text style={[styles.previewRowValue, { color: COLORS.ERROR }]}>
                  -${Math.round(taxAmount).toLocaleString()}
                </Text>
              </View>
            )}
            <View style={styles.previewRow}>
              <Text style={styles.previewRowLabel}>Net Monthly</Text>
              <Text style={styles.previewRowValue}>${Math.round(monthlyIncome).toLocaleString()}</Text>
            </View>
            <View style={styles.divider} />
            <View style={styles.previewRow}>
              <Text style={styles.previewRowLabel}>Total Outflow</Text>
              <Text style={styles.previewRowValue}>-${totalOutflow.toLocaleString()}</Text>
            </View>
            <View style={styles.divider} />
            <View style={styles.surplusRow}>
              <View>
                <Text style={styles.surplusLabel}>Monthly Surplus</Text>
                <Text style={[styles.surplusValue, surplus < 0 && styles.surplusNegative]}>
                  {surplus >= 0 ? "+" : "-"}${Math.abs(surplus).toLocaleString()}
                </Text>
              </View>
              <View style={[styles.badge, surplus < 0 && styles.badgeNegative]}>
                <Text style={[styles.badgeText, surplus < 0 && styles.badgeTextNegative]}>{savingsRate}%</Text>
              </View>
            </View>
            {surplus > 0 && (
              <Text style={styles.previewNote}>
                "Your surplus capacity is healthy. This provides a high probability of success for your goal."
              </Text>
            )}
          </View>

          {error ? <Text style={styles.errorText}>{error}</Text> : null}

          {/* ── CTA ── */}
          <TouchableOpacity style={styles.ctaButton} onPress={handleContinue} activeOpacity={0.85}>
            <Text style={styles.ctaLabel}>Build My Baseline</Text>
            <MaterialIcons name="arrow-forward" size={20} color={COLORS.TEXT_ON_ORANGE} />
          </TouchableOpacity>

          {/* ── Security ── */}
          <View style={styles.secCard}>
            <MaterialIcons name="security" size={20} color={COLORS.DISABLED} />
            <View>
              <Text style={styles.secTitle}>Bank-Grade Encryption</Text>
              <Text style={styles.secDesc}>Secured using AES-256 protocols and local-first encryption.</Text>
            </View>
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
  navLinks: { flexDirection: "row", gap: SPACING.MD },
  navActive: {
    fontSize: FONT.SIZE_SM,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.ORANGE,
    borderBottomWidth: 2,
    borderBottomColor: COLORS.ORANGE,
    paddingBottom: 2,
  },
  navInactive: {
    fontSize: FONT.SIZE_SM,
    color: COLORS.DISABLED,
  },

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
    maxWidth: 280,
  },
  founderHint: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.PRIMARY,
    lineHeight: 16,
    marginTop: 6,
    fontStyle: "italic",
  },

  section: {
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.MD,
    padding: SPACING.LG,
    marginBottom: SPACING.MD,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: SPACING.LG,
  },
  sectionLabel: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 2,
    color: COLORS.TEXT_SECONDARY,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
    marginBottom: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_ON_SURFACE,
  },
  toggleRow: {
    flexDirection: "row",
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.SM,
    padding: 3,
  },
  toggleBtn: {
    paddingHorizontal: SPACING.MD,
    paddingVertical: 6,
    borderRadius: RADIUS.SM,
  },
  toggleBtnActive: { backgroundColor: COLORS.ORANGE },
  toggleLabel: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 1,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_SECONDARY,
  },
  toggleLabelActive: { color: COLORS.TEXT_ON_ORANGE },

  liquidityHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.SM,
    marginBottom: SPACING.LG,
  },
  liquidityGrid: { gap: SPACING.SM },
  liquidityCard: {
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.SM,
    padding: SPACING.MD,
    borderBottomWidth: 2,
    borderBottomColor: "rgba(255,182,147,0.2)",
  },
  liquidityLabel: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 1.5,
    color: COLORS.DISABLED,
    marginBottom: 6,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
  },

  previewCard: {
    backgroundColor: COLORS.SURFACE_HIGH,
    borderRadius: RADIUS.MD,
    padding: SPACING.LG,
    marginBottom: SPACING.MD,
    shadowColor: "#000",
    shadowOpacity: 0.4,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 8 },
    elevation: 10,
  },
  previewTitle: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 2,
    color: COLORS.TEXT_SECONDARY,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
    marginBottom: SPACING.LG,
  },
  previewRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: SPACING.SM,
  },
  previewRowLabel: { fontSize: FONT.SIZE_SM, color: COLORS.DISABLED },
  previewRowValue: {
    fontSize: FONT.SIZE_MD,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_ON_SURFACE,
  },
  divider: {
    height: 1,
    backgroundColor: "rgba(255,255,255,0.05)",
    marginVertical: 4,
  },
  surplusRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    paddingTop: SPACING.MD,
  },
  surplusLabel: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 1.5,
    color: COLORS.DISABLED,
    marginBottom: 4,
  },
  surplusValue: {
    fontSize: 32,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TERTIARY_CONTAINER,
    letterSpacing: -1,
  },
  surplusNegative: { color: COLORS.ERROR },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 100,
    backgroundColor: "rgba(120,220,119,0.1)",
    borderWidth: 1,
    borderColor: "rgba(120,220,119,0.2)",
  },
  badgeNegative: {
    backgroundColor: "rgba(255,180,171,0.1)",
    borderColor: "rgba(255,180,171,0.2)",
  },
  badgeText: {
    fontSize: FONT.SIZE_XS,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TERTIARY,
  },
  badgeTextNegative: { color: COLORS.ERROR },
  previewNote: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.DISABLED,
    fontStyle: "italic",
    lineHeight: 18,
    marginTop: SPACING.MD,
  },

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

  secCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: SPACING.MD,
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.MD,
    padding: SPACING.MD,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
  },
  secTitle: {
    fontSize: FONT.SIZE_XS,
    textTransform: "uppercase",
    letterSpacing: 1.5,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_SECONDARY,
  },
  secDesc: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.DISABLED,
    marginTop: 2,
    lineHeight: 16,
  },
});
