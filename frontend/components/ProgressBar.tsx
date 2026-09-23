import React from "react";
import { StyleSheet, View } from "react-native";
import { useAppTheme } from "@/context/ThemeContext";
import { radii } from "@/theme/tokens";

export function ProgressBar({ progress, danger }: { progress: number; danger?: boolean }) {
  const { theme } = useAppTheme();
  const clamped = Math.max(0, Math.min(1, progress));

  return (
    <View style={[styles.track, { backgroundColor: theme.tileBackground }]}>
      <View style={[styles.fill, { width: `${clamped * 100}%`, backgroundColor: danger ? theme.danger : theme.primary }]} />
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    height: 10,
    borderRadius: radii.pill,
    overflow: "hidden",
  },
  fill: {
    height: "100%",
    borderRadius: radii.pill,
  },
});
