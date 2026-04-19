/**
 * components/GhostButton.tsx
 * Borderless text button — secondary / skip / go-back actions.
 */

import React from "react";
import { StyleSheet, Text, TouchableOpacity } from "react-native";
import { COLORS, FONT, SPACING } from "../constants/theme";

interface Props {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  color?: string;
}

export function GhostButton({
  label,
  onPress,
  disabled = false,
  color = COLORS.TEXT_SECONDARY,
}: Props): React.JSX.Element {
  return (
    <TouchableOpacity
      style={styles.button}
      onPress={onPress}
      disabled={disabled}
      activeOpacity={0.6}
    >
      <Text style={[styles.label, { color: disabled ? COLORS.DISABLED : color }]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingVertical: SPACING.SM,
    paddingHorizontal: SPACING.MD,
    alignItems: "center",
    justifyContent: "center",
  },
  label: {
    fontSize: FONT.SIZE_MD,
    fontWeight: FONT.WEIGHT_MEDIUM,
  },
});
