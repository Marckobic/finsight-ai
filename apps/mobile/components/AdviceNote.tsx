/**
 * components/AdviceNote.tsx
 * The one line that says what this output is not.
 *
 * The landing page carries a disclaimer in its footer, but anyone who opens the
 * app link directly never sees it — and the app is where the advice-shaped text
 * actually appears. This renders under the AI explanation, on the two screens
 * that show one.
 *
 * Deliberately quiet: it is a boundary, not a warning. A loud banner on every
 * result trains people to stop reading it.
 */

import React from "react";
import { StyleSheet, Text } from "react-native";
import { COLORS, FONT, SPACING } from "../constants/theme";

export function AdviceNote(): React.JSX.Element {
  return (
    <Text style={styles.note}>
      Projections from the figures you entered. Informational only — not
      financial, investment or tax advice.
    </Text>
  );
}

const styles = StyleSheet.create({
  note: {
    fontSize: FONT.SIZE_XS,
    lineHeight: 15,
    color: COLORS.TEXT_MUTED,
    marginTop: SPACING.SM,
    marginBottom: SPACING.MD,
  },
});
