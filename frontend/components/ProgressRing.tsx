import React from "react";
import { View } from "react-native";
import Svg, { Circle } from "react-native-svg";
import { colors } from "@/theme/tokens";

type Props = {
  size: number;
  /** 0..1. Clamped. 0 must render as an empty track, never a full ring. */
  progress: number;
  color?: string;
  trackColor?: string;
  strokeWidth?: number;
  /** Centered content: emoji, number, or label. */
  children?: React.ReactNode;
  /** e.g. "Protein, 64 of 120 grams" */
  accessibilityLabel: string;
};

export function ProgressRing({
  size,
  progress,
  color = colors.petal,
  trackColor = colors.blushLight,
  strokeWidth = 7,
  children,
  accessibilityLabel,
}: Props) {
  const p = Math.max(0, Math.min(1, Number.isFinite(progress) ? progress : 0));
  const r = (size - strokeWidth) / 2;
  const c = 2 * Math.PI * r;

  return (
    <View
      style={{ width: size, height: size }}
      accessible
      accessibilityRole="progressbar"
      accessibilityLabel={accessibilityLabel}
      accessibilityValue={{ min: 0, max: 100, now: Math.round(p * 100) }}
    >
      <Svg width={size} height={size}>
        <Circle cx={size / 2} cy={size / 2} r={r} stroke={trackColor} strokeWidth={strokeWidth} fill="none" />
        {p > 0 && (
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke={color}
            strokeWidth={strokeWidth}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={`${c * p} ${c}`}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        )}
      </Svg>
      <View style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, alignItems: "center", justifyContent: "center" }} pointerEvents="none">
        {children}
      </View>
    </View>
  );
}

export default ProgressRing;
