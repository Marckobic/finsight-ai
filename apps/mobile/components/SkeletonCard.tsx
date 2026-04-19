/**
 * components/SkeletonCard.tsx
 * Loading placeholder — shown while API calls are in flight.
 * Uses a simple opacity pulse animation (no external dependencies).
 */

import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, View } from "react-native";
import { COLORS, RADIUS, SPACING } from "../constants/theme";

interface Props {
  height?: number;
  width?: string | number;
}

export function SkeletonCard({
  height = 80,
  width = "100%",
}: Props): React.JSX.Element {
  const opacity = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 0.9,
          duration: 700,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.4,
          duration: 700,
          useNativeDriver: true,
        }),
      ])
    );
    pulse.start();
    return () => pulse.stop();
  }, [opacity]);

  return (
    <Animated.View
      style={[styles.skeleton, { height, width: width as number, opacity }]}
    />
  );
}

const styles = StyleSheet.create({
  skeleton: {
    backgroundColor: COLORS.CARD,
    borderRadius: RADIUS.MD,
    marginBottom: SPACING.MD,
  },
});
