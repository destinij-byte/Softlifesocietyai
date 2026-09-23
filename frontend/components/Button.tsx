import React from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { useAppTheme } from "@/context/ThemeContext";
import { radii, spacing, typography } from "@/theme/tokens";

type ButtonProps = {
  label: string;
  emoji?: string;
  icon?: React.ReactNode;
  onPress: () => void;
  variant?: "primary" | "secondary" | "ghost";
  loading?: boolean;
  disabled?: boolean;
};

export function Button({ label, emoji, icon, onPress, variant = "primary", loading, disabled }: ButtonProps) {
  const { theme } = useAppTheme();

  // Primary is always a near-black pill with gold text in both themes — the
  // one piece of chrome (with the tab bar) that stays constant rather than
  // flipping with the surface, so it reads as the app's signature action.
  const backgroundColor = variant === "primary" ? theme.tabBarBackground : variant === "secondary" ? theme.surfaceAlt : "transparent";
  const textColor = variant === "primary" ? theme.primary : theme.text;
  const borderColor = variant === "ghost" ? theme.text : "transparent";

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor,
          borderColor,
          borderWidth: variant === "ghost" ? 1 : 0,
          opacity: pressed ? 0.85 : disabled ? 0.5 : 1,
        },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={textColor} />
      ) : (
        <View style={styles.content}>
          {icon}
          <Text style={[styles.label, { color: textColor }]}>
            {emoji ? `${emoji} ` : ""}
            {label}
          </Text>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  content: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  base: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.pill,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 48,
  },
  label: {
    fontFamily: typography.bodyBold,
    fontSize: 15,
  },
});
