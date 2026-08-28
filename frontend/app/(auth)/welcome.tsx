import React from "react";
import { Image, StyleSheet, View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { useAppTheme } from "@/context/ThemeContext";
import { spacing } from "@/theme/tokens";

export default function Welcome() {
  const { theme, mode, toggleMode } = useAppTheme();

  return (
    <Screen scroll={false} style={styles.container}>
      <View style={styles.top}>
        <Muted onPress={toggleMode} style={{ alignSelf: "flex-end" }}>
          {mode === "dark" ? "☀️ Light mode" : "🌙 Dark mode"}
        </Muted>
      </View>

      <View style={styles.hero}>
        <Image source={require("@/assets/logo.png")} style={styles.logo} resizeMode="contain" />
        <Body style={{ textAlign: "center", color: theme.textMuted, marginTop: spacing.sm }}>
          Meet Luna Reyes, your AI lifestyle coach for a softer, more intentional life. ✨
        </Body>
      </View>

      <View style={{ gap: spacing.md }}>
        <Button label="Start my 7-day free trial" emoji="🌷" onPress={() => router.push("/(auth)/signup")} />
        <Button label="I already have an account" variant="ghost" onPress={() => router.push("/(auth)/login")} />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: { justifyContent: "space-between" },
  top: { paddingTop: spacing.sm },
  hero: { alignItems: "center", gap: spacing.xs },
  logo: { width: 280, height: 280 },
});
