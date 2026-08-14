/**
 * components/DateField.tsx
 * A deadline field with an actual date picker on web.
 *
 * The previous field was a plain TextInput expecting MM/DD/YYYY, with a
 * calendar icon next to it that had no onPress and opened nothing. The icon
 * promised a picker the screen did not have — and on a phone, typing
 * "12/31/2027" into a text field is the worst possible way to enter a date.
 *
 * On web this renders a real <input type="date">, which gets the platform's
 * own picker for free — the wheel on iOS, the calendar on Android and desktop —
 * with no dependency added. Its native value format is YYYY-MM-DD, which is
 * exactly what the backend wants, so the manual MM/DD/YYYY parsing goes away
 * along with the class of "enter deadline as MM/DD/YYYY" errors it produced.
 *
 * Native keeps the typed field until a picker library is worth adding; it is
 * not, while every user is on the web build.
 */

import { MaterialIcons } from "@expo/vector-icons";
import React from "react";
import { Platform, StyleSheet, TextInput, View } from "react-native";
import { COLORS, FONT, RADIUS, SPACING } from "../constants/theme";

type Props = {
  /** ISO date, YYYY-MM-DD. Empty string when unset. */
  value: string;
  onChange: (iso: string) => void;
  onSubmit?: () => void;
};

/** YYYY-MM-DD → MM/DD/YYYY, for the native text fallback. */
function toDisplay(iso: string): string {
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return m ? `${m[2]}/${m[3]}/${m[1]}` : iso;
}

/** MM/DD/YYYY → YYYY-MM-DD, or "" when incomplete. */
function toIso(display: string): string {
  const m = display.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (!m) return "";
  return `${m[3]}-${m[1].padStart(2, "0")}-${m[2].padStart(2, "0")}`;
}

export function DateField({ value, onChange, onSubmit }: Props): React.JSX.Element {
  if (Platform.OS === "web") {
    // react-native-web renders to the DOM, so a raw input is available. The
    // page sets color-scheme: dark, which is what makes the browser's own
    // calendar and its icon render dark rather than a white rectangle.
    return (
      <View style={styles.row}>
        {React.createElement("input", {
          type: "date",
          // The browser localises this widget to ITS OWN locale, not the
          // document's — a Russian Chrome renders "ДД.ММ.ГГГГ" and Russian
          // month names inside an English app. lang pins the field to en-US so
          // the app reads as one language. A user abroad still gets their own
          // calendar conventions from the OS picker on mobile, which is the
          // part that should stay local.
          lang: "en-US",
          value,
          min: new Date().toISOString().slice(0, 10),
          onChange: (event: { target: { value: string } }) => onChange(event.target.value),
          style: {
            flex: 1,
            width: "100%",
            padding: SPACING.MD,
            border: "none",
            outline: "none",
            background: "transparent",
            color: COLORS.TEXT_ON_SURFACE,
            fontSize: FONT.SIZE_LG,
            fontWeight: FONT.WEIGHT_BOLD,
            fontFamily: "inherit",
            colorScheme: "dark",
          },
        })}
      </View>
    );
  }

  return (
    <View style={styles.row}>
      <TextInput
        style={styles.input}
        value={toDisplay(value)}
        onChangeText={(text) => onChange(toIso(text) || text)}
        placeholder="12/31/2027"
        placeholderTextColor="rgba(255,255,255,0.4)"
        keyboardType="numbers-and-punctuation"
        returnKeyType="done"
        onSubmitEditing={onSubmit}
      />
      <MaterialIcons
        name="calendar-today"
        size={20}
        color={COLORS.DISABLED}
        style={styles.icon}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.SURFACE_HIGHEST,
    borderRadius: RADIUS.MD,
  },
  input: {
    flex: 1,
    fontSize: FONT.SIZE_LG,
    fontWeight: FONT.WEIGHT_BOLD,
    color: COLORS.TEXT_ON_SURFACE,
    padding: SPACING.MD,
  },
  icon: { marginRight: SPACING.MD },
});
