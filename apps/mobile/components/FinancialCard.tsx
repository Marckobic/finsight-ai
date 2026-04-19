/**
 * components/FinancialCard.tsx
 * Dark card for displaying financial metrics.
 *
 * Usage:
 *   <FinancialCard label="Monthly cashflow" value="$2,500" />
 *   <FinancialCard label="Time to goal" value="18 months" highlight="positive" />
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { COLORS, FONT, RADIUS, SPACING } from "../constants/theme";

interface Props {
  label: string;
  value: string;
  subtext?: string;
  highlight?: "positive" | "negative" | "neutral";
}

export function FinancialCard({
  label,
  value,
  subtext,
  highlight = "neutral",
}: Props): React.JSX.Element {
  const valueColor =
    highlight === "positive"
      ? COLORS.POSITIVE
      : highlight === "negative"
      ? COLORS.NEGATIVE
      : COLORS.WHITE;

  return (
    <View style={styles.card}>
      <Text style={styles.label}>{label}</Text>
      <Text style={[styles.value, { color: valueColor }]}>{value}</Text>
      {subtext ? <Text style={styles.subtext}>{subtext}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: COLORS.CARD,
    borderRadius: RADIUS.MD,
    borderWidth: 1,
    borderColor: COLORS.CARD_BORDER,
    paddingVertical: SPACING.MD,
    paddingHorizontal: SPACING.LG,
    marginBottom: SPACING.MD,
  },
  label: {
    color: COLORS.TEXT_MUTED_ON_CARD,
    fontSize: FONT.SIZE_SM,
    fontWeight: FONT.WEIGHT_MEDIUM,
    marginBottom: SPACING.XS,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  value: {
    fontSize: FONT.SIZE_XL,
    fontWeight: FONT.WEIGHT_BOLD,
  },
  subtext: {
    color: COLORS.TEXT_MUTED_ON_CARD,
    fontSize: FONT.SIZE_SM,
    marginTop: SPACING.XS,
  },
});
