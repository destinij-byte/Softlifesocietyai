import React from "react";
import { Image, StyleSheet, View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { LunaAvatar } from "@/components/LunaAvatar";
import { useAppTheme } from "@/context/ThemeContext";
import { spacing } from "@/theme/tokens";

export default function Welcome() {
  const { theme } = useAppTheme();

  return (
    <Screen scroll={false} style={styles.container}>
      <View />

      <View style={styles.hero}>
        <Image source={require("@/assets/logo.png")} style={styles.logo} resizeMode="contain" />
        <Body style={{ textAlign: "center", color: theme.text, letterSpacing: 2, fontSize: 12, fontFamily: "Poppins_500Medium" }}>
          SOFT LIFE SOCIETY
        </Body>
        <View style={{ width: 34, height: 1, backgroundColor: theme.primary, marginVertical: spacing.sm }} />
        <Body style={{ textAlign: "center", fontStyle: "italic", color: theme.text, fontSize: 17 }}>
          Become the woman you're becoming.
        </Body>
        <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm, marginTop: spacing.sm, maxWidth: 300 }}>
          <LunaAvatar size={40} />
          <Body style={{ flex: 1, color: theme.textMuted }}>
            Meet Luna Reyes — your AI lifestyle coach, here to help you plan your life, glow daily, and become her.
          </Body>
        </View>
      </View>

      <View style={{ gap: spacing.md }}>
        <Button label="Start my 7-day free trial" onPress={() => router.push("/(auth)/signup")} />
        <Button label="I already have an account" variant="ghost" onPress={() => router.push("/(auth)/login")} />
        <Muted style={{ textAlign: "center" }}>No commitment. Cancel anytime.</Muted>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: { justifyContent: "space-between" },
  hero: { alignItems: "center" },
  logo: { width: 200, height: 200 },
});
