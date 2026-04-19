/**
 * components/ErrorCard.tsx
 * Inline error display — shown when an API call fails or validation errors exist.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { COLORS, FONT, RADIUS, SPACING } from "../constants/theme";

interface Props {
  message: string;
  errors?: string[];
}

export function ErrorCard({ message, errors = [] }: Props): React.JSX.Element {
  return (
    <View style={styles.card}>
      <Text style={styles.message}>{message}</Text>
      {errors.length > 0 && (
        <View style={styles.errorList}>
          {errors.map((err, i) => (
            <Text key={i} style={styles.errorItem}>
              {"• "}
              {err}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#2A0A0A",
    borderRadius: RADIUS.MD,
    borderWidth: 1,
    borderColor: COLORS.NEGATIVE,
    paddingVertical: SPACING.MD,
    paddingHorizontal: SPACING.LG,
    marginBottom: SPACING.MD,
  },
  message: {
    color: COLORS.NEGATIVE,
    fontSize: FONT.SIZE_MD,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
  },
  errorList: {
    marginTop: SPACING.SM,
  },
  errorItem: {
    color: COLORS.NEGATIVE,
    fontSize: FONT.SIZE_SM,
    lineHeight: 20,
  },
});
