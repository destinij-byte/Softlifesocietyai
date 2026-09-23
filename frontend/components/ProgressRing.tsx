import React from "react";
import { View } from "react-native";
import Svg, { Circle } from "react-native-svg";
import { useAppTheme } from "@/context/ThemeContext";

type ProgressRingProps = {
  progress: number;
  size?: number;
  strokeWidth?: number;
  color?: string;
  trackColor?: string;
  children?: React.ReactNode;
};

export function ProgressRing({ progress, size = 180, strokeWidth = 14, color, trackColor, children }: ProgressRingProps) {
  const { theme } = useAppTheme();
  const clamped = Math.max(0, Math.min(1, progress));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  // Never a solid full track at 0% — a sliver of fill always shows so the
  // ring reads as "in progress," not broken.
  const offset = circumference * (1 - Math.max(clamped, 0.015));

  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <Svg width={size} height={size} style={{ position: "absolute" }}>
        <Circle cx={size / 2} cy={size / 2} r={radius} stroke={trackColor ?? theme.tileBackground} strokeWidth={strokeWidth} fill="none" />
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color ?? theme.primary}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          rotation="-90"
          origin={`${size / 2}, ${size / 2}`}
        />
      </Svg>
      {children}
    </View>
  );
}
