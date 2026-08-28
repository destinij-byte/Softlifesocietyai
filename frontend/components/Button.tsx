import React from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";
import { useAppTheme } from "@/context/ThemeContext";
import { radii, spacing, typography } from "@/theme/tokens";

type ButtonProps = {
  label: string;
  emoji?: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "ghost";
  loading?: boolean;
  disabled?: boolean;
};

export function Button({ label, emoji, onPress, variant = "primary", loading, disabled }: ButtonProps) {
  const { theme } = useAppTheme();

  const backgroundColor =
    variant === "primary" ? theme.primary : variant === "secondary" ? theme.surfaceAlt : "transparent";
  const textColor = variant === "primary" ? "#FFFFFF" : theme.text;
  const borderColor = variant === "ghost" ? theme.border : "transparent";

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
        <Text style={[styles.label, { color: textColor }]}>
          {emoji ? `${emoji} ` : ""}
          {label}
        </Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.pill,
    alignItems: "center",
    justifyContent: "center",
  },
  label: {
    fontFamily: typography.bodyBold,
    fontSize: 16,
  },
});
