/**
 * AdherenceSlider.native.tsx
 * Native implementation — uses @react-native-community/slider
 */
import Slider from "@react-native-community/slider";
import React from "react";
import { COLORS } from "../constants/theme";

interface Props {
  value: number;
  onValueChange: (v: number) => void;
  onSlidingComplete: (v: number) => void;
  style?: object;
}

export default function AdherenceSlider({ value, onValueChange, onSlidingComplete, style }: Props) {
  return (
    <Slider
      style={[{ width: "100%", height: 32 }, style]}
      minimumValue={0.1}
      maximumValue={0.95}
      value={value}
      onValueChange={onValueChange}
      onSlidingComplete={onSlidingComplete}
      minimumTrackTintColor={COLORS.ORANGE}
      maximumTrackTintColor={COLORS.SURFACE_HIGHEST}
      thumbTintColor={COLORS.ORANGE}
      step={0.05}
    />
  );
}
