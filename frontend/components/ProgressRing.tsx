import React from "react";
import { View } from "react-native";
import Svg, { Circle, Defs, LinearGradient as SvgLinearGradient, Stop } from "react-native-svg";
import { useAppTheme } from "@/context/ThemeContext";

type ProgressRingProps = {
  progress: number;
  size?: number;
  strokeWidth?: number;
  children?: React.ReactNode;
};

export function ProgressRing({ progress, size = 180, strokeWidth = 14, children }: ProgressRingProps) {
  const { theme } = useAppTheme();
  const clamped = Math.max(0, Math.min(1, progress));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped);

  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <Svg width={size} height={size} style={{ position: "absolute" }}>
        <Defs>
          <SvgLinearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            {theme.goldGradient.map((color, i) => (
              <Stop key={color} offset={`${(i / (theme.goldGradient.length - 1)) * 100}%`} stopColor={color} />
            ))}
          </SvgLinearGradient>
        </Defs>
        <Circle cx={size / 2} cy={size / 2} r={radius} stroke={theme.surfaceAlt} strokeWidth={strokeWidth} fill="none" />
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#ringGradient)"
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
