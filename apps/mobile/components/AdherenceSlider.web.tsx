/**
 * AdherenceSlider.web.tsx
 * Web implementation — uses HTML input[type=range] styled to match dark theme
 */
import React from "react";
import { View } from "react-native";
import { COLORS } from "../constants/theme";

interface Props {
  value: number;
  onValueChange: (v: number) => void;
  onSlidingComplete: (v: number) => void;
  style?: object;
}

export default function AdherenceSlider({ value, onValueChange, onSlidingComplete, style }: Props) {
  const pct = ((value - 0.1) / (0.95 - 0.1)) * 100;

  return (
    <View style={[{ width: "100%", height: 32, justifyContent: "center" }, style]}>
      <input
        type="range"
        min={0.1}
        max={0.95}
        step={0.05}
        value={value}
        onChange={(e) => onValueChange(parseFloat(e.target.value))}
        onMouseUp={(e) => onSlidingComplete(parseFloat((e.target as HTMLInputElement).value))}
        onTouchEnd={(e) => onSlidingComplete(parseFloat((e.target as HTMLInputElement).value))}
        style={{
          width: "100%",
          height: 4,
          appearance: "none",
          WebkitAppearance: "none",
          borderRadius: 2,
          outline: "none",
          cursor: "pointer",
          background: `linear-gradient(to right, ${COLORS.ORANGE} ${pct}%, ${COLORS.SURFACE_HIGHEST} ${pct}%)`,
        } as React.CSSProperties}
      />
      <style>{`
        input[type=range]::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: ${COLORS.ORANGE};
          cursor: pointer;
          box-shadow: 0 0 8px rgba(255,107,0,0.5);
        }
        input[type=range]::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: ${COLORS.ORANGE};
          cursor: pointer;
          border: none;
          box-shadow: 0 0 8px rgba(255,107,0,0.5);
        }
      `}</style>
    </View>
  );
}
