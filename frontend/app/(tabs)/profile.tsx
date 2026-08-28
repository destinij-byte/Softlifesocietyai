import React from "react";
import { View } from "react-native";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { useAuth } from "@/context/AuthContext";
import { useAppTheme } from "@/context/ThemeContext";
import { spacing } from "@/theme/tokens";

export default function Profile() {
  const { user, logOut } = useAuth();
  const { theme, mode, toggleMode } = useAppTheme();

  if (!user) return null;

  const statusLabel: Record<string, string> = {
    trialing: "🌷 Free trial",
    active: "✨ Active subscriber",
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
        <Subtitle>Membership</Subtitle>
        <Body style={{ marginTop: spacing.xs }}>{statusLabel[user.subscription_status] ?? user.subscription_status}</Body>
        {user.subscription_tier && <Muted>{user.subscription_tier} plan</Muted>}
      </Card>

      <Card style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
        <Body>{mode === "dark" ? "🌙 Dark mode" : "☀️ Light mode"}</Body>
        <Button label="Toggle" onPress={toggleMode} variant="secondary" />
      </Card>

      <Button label="Log out" emoji="👋" variant="ghost" onPress={logOut} />
    </Screen>
  );
}
