import React from "react";
import { ActivityIndicator, View } from "react-native";
import { Body, Card, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { useAppTheme } from "@/context/ThemeContext";
import { spacing } from "@/theme/tokens";

type AsyncStateProps = {
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
  empty?: boolean;
  emptyIcon?: string;
  emptyTitle?: string;
  emptyMessage?: string;
  children: React.ReactNode;
};

/**
 * The one shared loading/empty/error+retry wrapper every data-fetching
 * screen should use instead of a bare `if (!data) return null` (which
 * renders nothing at all, forever, on a failed request) or an ad hoc inline
 * error message with no way to recover except leaving the screen.
 */
export function AsyncState({
  loading,
  error,
  onRetry,
  empty,
  emptyIcon = "🌸",
  emptyTitle = "Nothing here yet",
  emptyMessage,
  children,
}: AsyncStateProps) {
  const { theme } = useAppTheme();

  if (loading) {
    return (
      <View style={{ paddingVertical: spacing.xxl, alignItems: "center" }}>
        <ActivityIndicator color={theme.primary} />
      </View>
    );
  }

  if (error) {
    return (
      <Card style={{ alignItems: "center", gap: spacing.sm }}>
        <Body style={{ textAlign: "center", color: theme.danger }}>⚠️ {error}</Body>
        {onRetry && <Button label="Try again" variant="secondary" onPress={onRetry} />}
      </Card>
    );
  }

  if (empty) {
    return (
      <Card style={{ alignItems: "center", gap: spacing.xs, paddingVertical: spacing.lg }}>
        <Body style={{ fontSize: 24 }}>{emptyIcon}</Body>
        <Body style={{ fontWeight: "600" }}>{emptyTitle}</Body>
        {emptyMessage && <Muted style={{ textAlign: "center" }}>{emptyMessage}</Muted>}
      </Card>
    );
  }

  return <>{children}</>;
}
