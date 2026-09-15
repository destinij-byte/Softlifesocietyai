import React from "react";
import { Text as RNText, TextProps, View as RNView, ViewProps } from "react-native";
import { useAppTheme } from "@/context/ThemeContext";
import { elevation, typography } from "@/theme/tokens";

export function Card({ style, accent, elevated, ...rest }: ViewProps & { accent?: boolean; elevated?: boolean }) {
  const { theme } = useAppTheme();
  return (
    <RNView
      style={[
        {
          backgroundColor: theme.surface,
          borderRadius: 20,
          padding: 16,
          borderWidth: 1,
          borderColor: theme.border,
          ...(accent ? { borderLeftWidth: 4, borderLeftColor: theme.accent } : {}),
          ...(elevated ? { ...elevation.soft, borderWidth: 0 } : {}),
        },
        style,
      ]}
      {...rest}
    />
  );
}

export function Title({ style, ...rest }: TextProps) {
  const { theme } = useAppTheme();
  return (
    <RNText
      style={[{ fontFamily: typography.display, fontSize: 28, color: theme.text }, style]}
      {...rest}
    />
  );
}

export function Subtitle({ style, ...rest }: TextProps) {
  const { theme } = useAppTheme();
  return (
    <RNText
      style={[{ fontFamily: typography.displayMedium, fontSize: 20, color: theme.text }, style]}
      {...rest}
    />
  );
}

export function Body({ style, ...rest }: TextProps) {
  const { theme } = useAppTheme();
  return (
    <RNText style={[{ fontFamily: typography.body, fontSize: 15, color: theme.text }, style]} {...rest} />
  );
}

export function Muted({ style, ...rest }: TextProps) {
  const { theme } = useAppTheme();
  return (
    <RNText
      style={[{ fontFamily: typography.body, fontSize: 13, color: theme.textMuted }, style]}
      {...rest}
    />
  );
}
