/**
 * app/onboarding.tsx
 * Onboarding screen — founder-focused positioning.
 *
 * Single screen, 3 value props, CTA → /goal
 */

import { MaterialIcons } from "@expo/vector-icons";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  Dimensions,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { COLORS, FONT, RADIUS, SPACING } from "../constants/theme";
import { EVENTS, track } from "../lib/analytics";

const { width } = Dimensions.get("window");

const VALUE_PROPS = [
  {
    icon: "bolt" as const,
    title: "Know your runway — exactly",
    description:
      "Not a spreadsheet estimate. A deterministic engine that models your real cashflow month by month.",
  },
  {
    icon: "insights" as const,
    title: "Simulate before you commit",
    description:
      "\"What if I cut burn by $2k?\" Run it in seconds. See the impact on your timeline before changing anything.",
  },
  {
    icon: "verified-user" as const,
    title: "AI that can't hallucinate money",
    description:
      "Every AI explanation is validated against the engine output. No invented numbers. No false confidence.",
  },
];

export default function OnboardingScreen(): React.JSX.Element {
  const [activeIndex, setActiveIndex] = useState(0);

  // Fire onboarding_started once on mount
  React.useEffect(() => { track(EVENTS.ONBOARDING_STARTED); }, []);

  function handleContinue() {
    if (activeIndex < VALUE_PROPS.length - 1) {
      setActiveIndex(activeIndex + 1);
    } else {
      track(EVENTS.ONBOARDING_COMPLETED, { slides_viewed: VALUE_PROPS.length });
      router.replace("/goal");
    }
  }

  function handleSkip() {
    track(EVENTS.ONBOARDING_SKIPPED, { slide_at: activeIndex });
    router.replace("/goal");
  }

  const prop = VALUE_PROPS[activeIndex];
  const isLast = activeIndex === VALUE_PROPS.length - 1;

  return (
    <SafeAreaView style={styles.safe} edges={["top", "bottom"]}>
      {/* ── Skip ── */}
      <View style={styles.topBar}>
        <Text style={styles.brand}>FinSight.ai</Text>
        {!isLast && (
          <TouchableOpacity onPress={handleSkip} activeOpacity={0.7}>
            <Text style={styles.skipLabel}>Skip</Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Hero badge ── */}
        <View style={styles.badgeRow}>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>For founders & freelancers</Text>
          </View>
        </View>

        {/* ── Headline ── */}
        <Text style={styles.headline}>
          Stop guessing.{"\n"}
          <Text style={styles.headlineAccent}>Start deciding.</Text>
        </Text>
        <Text style={styles.subheadline}>
          Know your runway. Know what to do. Built for founders and freelancers — not spreadsheets.
        </Text>

        {/* ── Value prop card ── */}
        <View style={styles.propCard}>
          <View style={styles.propIconWrap}>
            <MaterialIcons name={prop.icon} size={32} color={COLORS.ORANGE} />
          </View>
          <Text style={styles.propTitle}>{prop.title}</Text>
          <Text style={styles.propDesc}>{prop.description}</Text>
        </View>

        {/* ── Dot indicators ── */}
        <View style={styles.dots}>
          {VALUE_PROPS.map((_, i) => (
            <TouchableOpacity key={i} onPress={() => setActiveIndex(i)}>
              <View
                style={[
                  styles.dot,
                  i === activeIndex && styles.dotActive,
                ]}
              />
            </TouchableOpacity>
          ))}
        </View>

        {/* ── Social proof ── */}
        <View style={styles.proofRow}>
          <View style={styles.proofItem}>
            <Text style={styles.proofNum}>100%</Text>
            <Text style={styles.proofLabel}>Deterministic engine</Text>
          </View>
          <View style={styles.proofDivider} />
          <View style={styles.proofItem}>
            <Text style={styles.proofNum}>0</Text>
            <Text style={styles.proofLabel}>AI-invented numbers</Text>
          </View>
          <View style={styles.proofDivider} />
          <View style={styles.proofItem}>
            <Text style={styles.proofNum}>&lt;2min</Text>
            <Text style={styles.proofLabel}>To first insight</Text>
          </View>
        </View>
      </ScrollView>

      {/* ── CTA ── */}
      <View style={styles.ctaWrap}>
        <TouchableOpacity
          style={styles.ctaButton}
          onPress={handleContinue}
          activeOpacity={0.85}
        >
          <Text style={styles.ctaLabel}>
            {isLast ? "Get Started" : "Next"}
          </Text>
          <MaterialIcons
            name={isLast ? "bolt" : "arrow-forward"}
            size={20}
            color={COLORS.TEXT_ON_ORANGE}
          />
        </TouchableOpacity>

        {isLast && (
          <View style={styles.trustRow}>
            <MaterialIcons name="lock" size={12} color={COLORS.DISABLED} />
            <Text style={styles.trustText}>
              No account needed · Data stays on your device
            </Text>
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: COLORS.BACKGROUND },

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
  skipLabel: {
    fontSize: FONT.SIZE_SM,
    color: COLORS.DISABLED,
  },

  content: {
    paddingHorizontal: SPACING.LG,
    paddingTop: SPACING.XL,
    paddingBottom: SPACING.LG,
  },

  badgeRow: {
    flexDirection: "row",
    marginBottom: SPACING.LG,
  },
  badge: {
    backgroundColor: "rgba(255,107,0,0.12)",
    borderWidth: 1,
    borderColor: "rgba(255,107,0,0.25)",
    borderRadius: RADIUS.PILL,
    paddingHorizontal: SPACING.MD,
    paddingVertical: 5,
  },
  badgeText: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.PRIMARY,
    fontWeight: FONT.WEIGHT_SEMIBOLD,
    textTransform: "uppercase",
    letterSpacing: 1.5,
  },

  headline: {
    fontSize: 38,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_SURFACE,
    letterSpacing: -1.5,
    lineHeight: 46,
    marginBottom: SPACING.MD,
  },
  headlineAccent: {
    color: COLORS.PRIMARY,
  },
  subheadline: {
    fontSize: FONT.SIZE_MD,
    color: "rgba(255,255,255,0.5)",
    lineHeight: 22,
    marginBottom: SPACING.XL,
  },

  propCard: {
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.MD,
    padding: SPACING.XL,
    marginBottom: SPACING.XL,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
    minHeight: 180,
    justifyContent: "center",
    gap: SPACING.MD,
  },
  propIconWrap: {
    width: 52,
    height: 52,
    borderRadius: RADIUS.MD,
    backgroundColor: "rgba(255,107,0,0.1)",
    alignItems: "center",
    justifyContent: "center",
  },
  propTitle: {
    fontSize: 20,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_SURFACE,
    letterSpacing: -0.5,
    lineHeight: 26,
  },
  propDesc: {
    fontSize: FONT.SIZE_SM,
    color: "rgba(255,255,255,0.55)",
    lineHeight: 20,
  },

  dots: {
    flexDirection: "row",
    justifyContent: "center",
    gap: SPACING.SM,
    marginBottom: SPACING.XL,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: "rgba(255,255,255,0.15)",
  },
  dotActive: {
    width: 20,
    backgroundColor: COLORS.ORANGE,
    borderRadius: 3,
  },

  proofRow: {
    flexDirection: "row",
    backgroundColor: COLORS.SURFACE,
    borderRadius: RADIUS.MD,
    padding: SPACING.LG,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.05)",
  },
  proofItem: { flex: 1, alignItems: "center", gap: 4 },
  proofNum: {
    fontSize: FONT.SIZE_LG,
    fontWeight: FONT.WEIGHT_EXTRABOLD,
    color: COLORS.TEXT_ON_SURFACE,
    letterSpacing: -0.5,
  },
  proofLabel: {
    fontSize: 9,
    textTransform: "uppercase",
    letterSpacing: 1,
    color: COLORS.DISABLED,
    textAlign: "center",
  },
  proofDivider: {
    width: 1,
    backgroundColor: "rgba(255,255,255,0.07)",
    marginHorizontal: SPACING.SM,
  },

  ctaWrap: {
    paddingHorizontal: SPACING.LG,
    paddingBottom: SPACING.LG,
    paddingTop: SPACING.SM,
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.05)",
  },
  ctaButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.SM,
    backgroundColor: COLORS.ORANGE,
    borderRadius: RADIUS.SM,
    paddingVertical: 18,
    marginBottom: SPACING.SM,
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
  trustRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: SPACING.XS,
    opacity: 0.5,
  },
  trustText: {
    fontSize: FONT.SIZE_XS,
    color: COLORS.TEXT_SECONDARY,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
});
