/**
 * components/OrangeButton.tsx
 * Orange filled button — confirmation / CTA action (accept recommendation).
 */

import React from "react";
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
} from "react-native";
import { COLORS, FONT, RADIUS, SPACING } from "../constants/theme";

interface Props {
  label: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
}

export function OrangeButton({
  label,
  onPress,
  loading = false,
  disabled = false,
}: Props): React.JSX.Element {
  const isDisabled = disabled || loading;

  return (
    <TouchableOpacity
      style={[styles.button, isDisabled && styles.disabled]}
      onPress={onPress}
      disabled={isDisabled}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator color={COLORS.WHITE} size="small" />
      ) : (
        <Text style={styles.label}>{label}</Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: COLORS.ORANGE,
    borderRadius: RADIUS.MD,
    paddingVertical: SPACING.MD,
    paddingHorizontal: SPACING.XL,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 52,
  },
  disabled: {
    backgroundColor: COLORS.DISABLED_BG,
  },
  label: {
    color: COLORS.WHITE,
    fontSize: FONT.SIZE_MD,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
  },
});
