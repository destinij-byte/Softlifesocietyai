import React from "react";
import { View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { useAuth } from "@/context/AuthContext";
import { useAppTheme, AppearancePreference } from "@/context/ThemeContext";
import { spacing } from "@/theme/tokens";

const MENU_ITEMS = [
  { label: "Nutrition preferences", emoji: "🍽️" },
  { label: "Personal preferences", emoji: "🌸" },
  { label: "Notifications", emoji: "🔔" },
  { label: "Privacy", emoji: "🔒" },
];

const APPEARANCE_OPTIONS: { key: AppearancePreference; label: string; emoji: string }[] = [
  { key: "light", label: "Light", emoji: "☀️" },
  { key: "dark", label: "Dark", emoji: "🌙" },
  { key: "system", label: "System", emoji: "⚙️" },
];

export default function Me() {
  const { user, logOut } = useAuth();
  const { theme, preference, setPreference } = useAppTheme();

  if (!user) return null;

  const statusLabel: Record<string, string> = {
    trialing: "🌷 Free trial",
    active: "✨ Active subscriber",
    free: "🤍 Free tier",
    expired: "🌙 Trial expired",
    canceled: "Canceled",
  };

  return (
    <Screen>
      <View style={{ alignItems: "center", gap: spacing.xs }}>
        <Body style={{ fontSize: 48 }}>{user.avatar_emoji}</Body>
        <Title>{user.name}</Title>
        <Muted>{user.email}</Muted>
      </View>

      <Card>
        <Subtitle>Subscription</Subtitle>
        <Body style={{ marginTop: spacing.xs }}>{statusLabel[user.subscription_status] ?? user.subscription_status}</Body>
        {user.subscription_tier && <Muted>{user.subscription_tier} plan</Muted>}
        <View style={{ marginTop: spacing.sm }}>
          <Button label="Manage subscription" variant="secondary" onPress={() => router.push("/(auth)/paywall")} />
        </View>
      </Card>

      <Card style={{ gap: spacing.sm }}>
        <Subtitle>Appearance</Subtitle>
        <View style={{ flexDirection: "row", gap: spacing.sm }}>
          {APPEARANCE_OPTIONS.map((opt) => (
            <Button
              key={opt.key}
              label={opt.label}
              emoji={opt.emoji}
              variant={preference === opt.key ? "primary" : "secondary"}
              onPress={() => setPreference(opt.key)}
            />
          ))}
        </View>
      </Card>

      <Card style={{ gap: 0 }}>
        <Subtitle style={{ marginBottom: spacing.sm }}>Goals & Routines</Subtitle>
        <Body onPress={() => router.push("/(tabs)/goals")} style={{ paddingVertical: spacing.sm }}>
          🎯 Goals
        </Body>
        <Body onPress={() => router.push("/(tabs)/routines")} style={{ paddingVertical: spacing.sm }}>
          📋 Routines
        </Body>
      </Card>

      <Card style={{ gap: 0 }}>
        {MENU_ITEMS.map((item) => (
          <Body key={item.label} style={{ paddingVertical: spacing.sm, color: theme.textMuted }}>
            {item.emoji} {item.label}
          </Body>
        ))}
      </Card>

      <Button label="Log out" emoji="👋" variant="ghost" onPress={logOut} />
    </Screen>
  );
}
