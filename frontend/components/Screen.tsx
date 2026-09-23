import React from "react";
import { ScrollView, StyleSheet, View, ViewProps } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useAppTheme } from "@/context/ThemeContext";
import { spacing } from "@/theme/tokens";

type ScreenProps = ViewProps & { scroll?: boolean; floating?: React.ReactNode };

// `floating` renders outside the scroll container, anchored to the screen
// itself (e.g. a FAB) — a child placed directly in `children` would instead
// scroll away with the content, since it'd live inside the ScrollView.
export function Screen({ children, style, scroll = true, floating, ...rest }: ScreenProps) {
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
      {floating}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  content: { flexGrow: 1, padding: spacing.lg, gap: spacing.md },
});
