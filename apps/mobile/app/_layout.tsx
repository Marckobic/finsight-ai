/**
 * app/_layout.tsx
 * Root layout — wraps every screen in the global store provider.
 * Dark #131313 shell.
 */

import { Stack } from "expo-router";
import React from "react";
import { Platform, StyleSheet, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { COLORS } from "../constants/theme";
import { StoreProvider } from "../lib/store";

export default function RootLayout(): React.JSX.Element {
  return (
    <SafeAreaProvider>
      <StoreProvider>
        <View style={styles.shell}>
          <Stack
            screenOptions={{
              headerShown: false,
              contentStyle: { backgroundColor: COLORS.BACKGROUND },
              animation: Platform.OS === "web" ? "none" : "slide_from_right",
            }}
          />
        </View>
      </StoreProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  shell: {
    flex: 1,
    backgroundColor: COLORS.BACKGROUND,
  },
});
