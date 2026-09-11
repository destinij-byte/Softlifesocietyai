import React from "react";
import { Image, StyleSheet, View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Body } from "@/components/Themed";
import { Button } from "@/components/Button";
import { useAppTheme } from "@/context/ThemeContext";
import { spacing } from "@/theme/tokens";

export default function Welcome() {
  const { theme } = useAppTheme();

  return (
    <Screen scroll={false} style={styles.container}>
      <View />

      <View style={styles.hero}>
        <Image source={require("@/assets/logo.png")} style={styles.logo} resizeMode="contain" />
        <Body style={{ textAlign: "center", fontStyle: "italic", color: theme.text, marginTop: spacing.sm, fontSize: 16 }}>
          Become the woman you've been working toward.
        </Body>
        <Body style={{ textAlign: "center", color: theme.textMuted, marginTop: spacing.xs }}>
          Meet Luna Reyes, your AI lifestyle coach. ✨
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
  hero: { alignItems: "center", gap: spacing.xs },
  logo: { width: 280, height: 280 },
});
