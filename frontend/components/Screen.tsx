import React from "react";
import { ScrollView, StyleSheet, View, ViewProps } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useAppTheme } from "@/context/ThemeContext";
import { spacing } from "@/theme/tokens";

type ScreenProps = ViewProps & { scroll?: boolean };

export function Screen({ children, style, scroll = true, ...rest }: ScreenProps) {
  const { theme } = useAppTheme();

  const Container = scroll ? ScrollView : View;

  return (
    <SafeAreaView style={[styles.safeArea, { backgroundColor: theme.background }]}>
      <Container
        style={scroll ? undefined : [styles.content, style]}
        contentContainerStyle={scroll ? [styles.content, style] : undefined}
        {...(rest as any)}
      >
        {children}
      </Container>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  content: { flexGrow: 1, padding: spacing.lg, gap: spacing.md },
});
