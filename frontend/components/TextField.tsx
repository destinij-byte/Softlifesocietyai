import React from "react";
import { StyleSheet, TextInput, TextInputProps } from "react-native";
import { useAppTheme } from "@/context/ThemeContext";
import { radii, spacing, typography } from "@/theme/tokens";

export function TextField(props: TextInputProps) {
  const { theme } = useAppTheme();
  return (
    <TextInput
      placeholderTextColor={theme.textMuted}
      style={[
        styles.base,
        {
          backgroundColor: theme.surface,
          borderColor: theme.border,
          color: theme.text,
        },
      ]}
      {...props}
    />
  );
}

const styles = StyleSheet.create({
  base: {
    borderWidth: 1,
    borderRadius: radii.md,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    fontFamily: typography.body,
    fontSize: 15,
  },
});
