import React from "react";
import { Text, View } from "react-native";
import { useAppTheme } from "@/context/ThemeContext";
import { typography } from "@/theme/tokens";

type AvatarProps = {
  name: string;
  size?: number;
};

/**
 * A soft, editorial initials avatar — a single letter in a gold-ringed
 * circle — used everywhere a user needs a face: profile header, leaderboard
 * rows, chat participants. Replaces the old random-emoji avatar.
 */
export function Avatar({ name, size = 38 }: AvatarProps) {
  const { theme } = useAppTheme();
  const initial = name.trim().charAt(0).toUpperCase() || "?";

  return (
    <View
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: theme.surfaceAlt,
        alignItems: "center",
        justifyContent: "center",
        borderWidth: 2,
        borderColor: theme.background,
      }}
    >
      <View
        style={{
          position: "absolute",
          top: -3,
          left: -3,
          right: -3,
          bottom: -3,
          borderRadius: (size + 6) / 2,
          borderWidth: 1.5,
          borderColor: theme.accent,
        }}
      />
      <Text style={{ fontFamily: typography.displayMedium, fontSize: size * 0.42, color: theme.text }}>{initial}</Text>
    </View>
  );
}
