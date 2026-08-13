/**
 * app/_layout.tsx
 * Root layout — wraps every screen in the global store provider.
 *
 * On web the app is constrained to a phone-width column and centred. Without
 * it the React Native styles, which are all written mobile-first with no
 * maxWidth anywhere, stretch a 38px headline and a full-bleed CTA across a
 * 1400px desktop window: not a desktop layout, a mobile one with the brakes
 * off. The frame keeps the product looking like the app it is, on any screen.
 *
 * Native is untouched — the constraint only applies to Platform.OS === "web".
 */

import { Stack } from "expo-router";
import React from "react";
import { Platform, StyleSheet, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { COLORS } from "../constants/theme";
import { StoreProvider } from "../lib/store";

/** Wider than an iPhone 16 Pro Max (440pt) so nothing reflows on a real phone. */
const MAX_APP_WIDTH = 480;

const isWeb = Platform.OS === "web";

export default function RootLayout(): React.JSX.Element {
  return (
    <SafeAreaProvider>
      <StoreProvider>
        <View style={styles.page}>
          <View style={styles.appFrame}>
            <Stack
              screenOptions={{
                headerShown: false,
                contentStyle: { backgroundColor: COLORS.BACKGROUND },
                animation: isWeb ? "none" : "slide_from_right",
              }}
            />
          </View>
        </View>
      </StoreProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  page: {
    flex: 1,
    alignItems: "center",
    // Slightly darker than the app itself, so the frame reads as a device
    // rather than as an unexplained gap.
    backgroundColor: isWeb ? COLORS.SURFACE_LOWEST : COLORS.BACKGROUND,
  },
  appFrame: {
    flex: 1,
    width: "100%",
    maxWidth: isWeb ? MAX_APP_WIDTH : undefined,
    backgroundColor: COLORS.BACKGROUND,
    ...(isWeb
      ? {
          borderLeftWidth: 1,
          borderRightWidth: 1,
          borderColor: "rgba(255,255,255,0.06)",
        }
      : null),
  },
});
