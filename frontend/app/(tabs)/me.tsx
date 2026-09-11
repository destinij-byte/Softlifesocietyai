import React from "react";
import { Pressable, View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { Icon, IconName } from "@/components/Icon";
import { useAuth } from "@/context/AuthContext";
import { useAppTheme, AppearancePreference } from "@/context/ThemeContext";
import { elevation, spacing } from "@/theme/tokens";

const MENU_ITEMS: { label: string; icon: IconName }[] = [
  { label: "Nutrition preferences", icon: "plate" },
  { label: "Personal preferences", icon: "heart" },
  { label: "Notifications", icon: "bell" },
  { label: "Privacy", icon: "lock" },
];

const APPEARANCE_OPTIONS: { key: AppearancePreference; label: string; icon: IconName }[] = [
  { key: "light", label: "Light", icon: "sun" },
  { key: "dark", label: "Dark", icon: "moon" },
  { key: "system", label: "System", icon: "sliders" },
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
        <View
          style={{
            width: 76,
            height: 76,
            borderRadius: 38,
            backgroundColor: theme.surface,
            borderWidth: 1.5,
            borderColor: theme.primary,
            alignItems: "center",
            justifyContent: "center",
            ...elevation.soft,
          }}
        >
          <Body style={{ fontSize: 30 }}>{user.avatar_emoji}</Body>
        </View>
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
          {APPEARANCE_OPTIONS.map((opt) => {
            const active = preference === opt.key;
            return (
              <Button
                key={opt.key}
                label={opt.label}
                icon={<Icon name={opt.icon} size={16} color={active ? "#1A1A1A" : theme.text} />}
                variant={active ? "primary" : "secondary"}
                onPress={() => setPreference(opt.key)}
              />
            );
          })}
        </View>
      </Card>

      <Card style={{ gap: 0 }}>
        <Subtitle style={{ marginBottom: spacing.sm }}>Goals & Routines</Subtitle>
        <Pressable onPress={() => router.push("/(tabs)/goals")} style={styles.menuRow}>
          <Icon name="target" size={18} color={theme.text} />
          <Body>Goals</Body>
        </Pressable>
        <Pressable onPress={() => router.push("/(tabs)/routines")} style={styles.menuRow}>
          <Icon name="checklist" size={18} color={theme.text} />
          <Body>Routines</Body>
        </Pressable>
      </Card>

      <Card style={{ gap: 0 }}>
        {MENU_ITEMS.map((item) => (
          <View key={item.label} style={styles.menuRow}>
            <Icon name={item.icon} size={18} color={theme.textMuted} />
            <Body style={{ color: theme.textMuted }}>{item.label}</Body>
          </View>
        ))}
      </Card>

      <Button label="Log out" variant="ghost" onPress={logOut} />
    </Screen>
  );
}

const styles = {
  menuRow: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    gap: spacing.sm,
    paddingVertical: spacing.sm,
  },
};
