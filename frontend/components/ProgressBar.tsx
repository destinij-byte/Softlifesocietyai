import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useAppTheme } from "@/context/ThemeContext";
import { radii } from "@/theme/tokens";

export function ProgressBar({ progress }: { progress: number }) {
  const { theme } = useAppTheme();
  const clamped = Math.max(0, Math.min(1, progress));

  return (
    <View style={[styles.track, { backgroundColor: theme.surfaceAlt, borderColor: theme.accent }]}>
      <LinearGradient
        colors={theme.goldGradient as [string, string, string]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
        style={[styles.fill, { width: `${clamped * 100}%` }]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    height: 10,
    borderRadius: radii.pill,
    overflow: "hidden",
    borderWidth: 1,
  },
  fill: {
    height: "100%",
    borderRadius: radii.pill,
  },
});
