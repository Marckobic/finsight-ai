/**
 * components/BottomNav.tsx
 * Mobile bottom navigation bar — 4 tabs: Goal / Input / Baseline / Scenario
 */

import { MaterialIcons } from "@expo/vector-icons";
import { usePathname, useRouter } from "expo-router";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { COLORS } from "../constants/theme";

type Tab = {
  route: string;
  label: string;
  icon: keyof typeof MaterialIcons.glyphMap;
};

const TABS: Tab[] = [
  { route: "/goal",     label: "Goal",    icon: "flag" },
  { route: "/input",    label: "Input",   icon: "edit-note" },
  { route: "/baseline", label: "Base",    icon: "account-balance" },
  { route: "/scenario", label: "Scenario", icon: "insights" },
];

export function BottomNav(): React.JSX.Element {
  const router = useRouter();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.bar, { paddingBottom: insets.bottom + 8 }]}>
      {TABS.map((tab) => {
        const active = pathname === tab.route || pathname.startsWith(tab.route);
        return (
          <TouchableOpacity
            key={tab.route}
            style={styles.tab}
            onPress={() => router.push(tab.route as any)}
            activeOpacity={0.7}
          >
            <MaterialIcons
              name={tab.icon}
              size={22}
              color={active ? COLORS.ORANGE : "rgba(255,255,255,0.55)"}
            />
            <Text style={[styles.label, active && styles.labelActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: "row",
    backgroundColor: COLORS.SURFACE_LOW,
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.05)",
    paddingTop: 12,
    paddingHorizontal: 8,
  },
  tab: {
    flex: 1,
    alignItems: "center",
    gap: 4,
  },
  label: {
    fontSize: 9,
    letterSpacing: 1,
    textTransform: "uppercase",
    color: "rgba(255,255,255,0.55)",
    fontWeight: "600",
  },
  labelActive: {
    color: COLORS.ORANGE,
  },
});
