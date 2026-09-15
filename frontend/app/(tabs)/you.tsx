import React from "react";
import { Pressable, View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Subtitle, Body, Muted } from "@/components/Themed";
import { Avatar } from "@/components/Avatar";
import { Button } from "@/components/Button";
import { Icon, IconName } from "@/components/Icon";
import { useAuth } from "@/context/AuthContext";
import { useAppTheme, AppearancePreference } from "@/context/ThemeContext";
import { spacing } from "@/theme/tokens";

type MenuItem = { label: string; icon: IconName; onPress: () => void };

const APPEARANCE_OPTIONS: { key: AppearancePreference; label: string; icon: IconName }[] = [
  { key: "light", label: "Light", icon: "sun" },
  { key: "dark", label: "Dark", icon: "moon" },
  { key: "system", label: "System", icon: "sliders" },
];

const STATUS_LABEL: Record<string, string> = {
  trialing: "Free trial",
  active: "Active subscriber",
  free: "Free tier",
  expired: "Trial expired",
  canceled: "Canceled",
};

function trialDaySummary(user: { trial_started_at: string; trial_ends_at: string; subscription_status: string }): string {
  if (user.subscription_status !== "trialing") return STATUS_LABEL[user.subscription_status] ?? user.subscription_status;
  const start = new Date(user.trial_started_at).getTime();
  const totalDays = Math.max(1, Math.round((new Date(user.trial_ends_at).getTime() - start) / (1000 * 60 * 60 * 24)));
  const elapsed = Math.min(totalDays, Math.max(1, Math.ceil((Date.now() - start) / (1000 * 60 * 60 * 24))));
  return `Free trial · Day ${elapsed} of ${totalDays}`;
}

export default function You() {
  const { user, logOut } = useAuth();
  const { theme, preference, setPreference } = useAppTheme();

  if (!user) return null;

  const menuItems: MenuItem[] = [
    { label: "My Blueprint", icon: "sparkle", onPress: () => router.push("/(onboarding)/blueprint") },
    { label: "Goals", icon: "target", onPress: () => router.push("/(tabs)/goals") },
    { label: "Wins", icon: "trophy", onPress: () => router.push("/(tabs)/challenges") },
    { label: "Routines", icon: "checklist", onPress: () => router.push("/(tabs)/routines") },
    { label: "Night Reset", icon: "moon", onPress: () => router.push("/(tabs)/night-reset") },
    { label: "Nutrition preferences", icon: "plate", onPress: () => router.push("/(tabs)/nourish-ai") },
    { label: "Subscription", icon: "sparkle", onPress: () => router.push("/(auth)/paywall") },
    { label: "Personal preferences", icon: "heart", onPress: () => {} },
    { label: "Notifications", icon: "bell", onPress: () => {} },
    { label: "Privacy", icon: "lock", onPress: () => {} },
  ];

  return (
    <Screen>
      <Card style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
        <Avatar name={user.name} size={56} />
        <View style={{ flex: 1 }}>
          <Subtitle style={{ fontSize: 16 }}>{user.name}</Subtitle>
          <Muted>{trialDaySummary(user)}</Muted>
        </View>
      </Card>

      <Card style={{ gap: 0 }}>
        {menuItems.map((item, i) => (
          <Pressable
            key={item.label}
            onPress={item.onPress}
            style={[styles.menuRow, i < menuItems.length - 1 ? { borderBottomWidth: 1, borderBottomColor: theme.border } : null]}
          >
            <Icon name={item.icon} size={17} color={theme.textMuted} />
            <Body style={{ flex: 1 }}>{item.label}</Body>
            <Muted>›</Muted>
          </Pressable>
        ))}
      </Card>

      <Card style={{ gap: spacing.sm }}>
        <Subtitle style={{ fontSize: 15 }}>Appearance</Subtitle>
        <View style={{ flexDirection: "row", backgroundColor: theme.surfaceAlt, borderRadius: 11, padding: 3 }}>
          {APPEARANCE_OPTIONS.map((opt) => {
            const active = preference === opt.key;
            return (
              <Pressable
                key={opt.key}
                onPress={() => setPreference(opt.key)}
                style={{
                  flex: 1,
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 5,
                  paddingVertical: 8,
                  borderRadius: 8,
                  backgroundColor: active ? theme.surface : "transparent",
                }}
              >
                <Icon name={opt.icon} size={14} color={theme.text} />
                <Body style={{ fontSize: 12 }}>{opt.label}</Body>
              </Pressable>
            );
          })}
        </View>
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
    paddingVertical: spacing.sm + 2,
  },
};
