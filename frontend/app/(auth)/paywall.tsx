import React, { useEffect, useState } from "react";
import { Pressable, View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { useAuth } from "@/context/AuthContext";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { spacing } from "@/theme/tokens";

type Tier = { label: string; price_usd: number; emoji: string };
type Tiers = Record<string, Tier>;

function trialDaysLeft(trialEndsAt: string): number {
  const diffMs = new Date(trialEndsAt).getTime() - Date.now();
  return Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
}

export default function Paywall() {
  const { user, refreshUser, logOut } = useAuth();
  const { theme } = useAppTheme();
  const [tiers, setTiers] = useState<Tiers>({});
  const [selected, setSelected] = useState<string>("annual");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiRequest<Tiers>("/subscriptions/tiers", { auth: false }).then(setTiers).catch(() => {});
  }, []);

  const daysLeft = user ? trialDaysLeft(user.trial_ends_at) : 0;
  const isExpired = user?.subscription_status === "expired";

  const onSubscribe = async () => {
    setLoading(true);
    try {
      await apiRequest("/subscriptions/subscribe", { method: "POST", body: { tier: selected } });
      await refreshUser();
      router.replace("/(tabs)/home");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <View style={{ gap: spacing.xs }}>
        <Title>{isExpired ? "Your trial has ended 🌙" : "Your Soft Life Blueprint™"}</Title>
        <Body style={{ color: theme.textMuted }}>
          {isExpired
            ? "Continue your journey with Luna by choosing a plan below."
            : `${daysLeft} day${daysLeft === 1 ? "" : "s"} left in your free trial ✨`}
        </Body>
      </View>

      <View style={{ gap: spacing.md }}>
        {Object.entries(tiers).map(([key, tier]) => (
          <Pressable key={key} onPress={() => setSelected(key)}>
            <Card
              style={{
                borderColor: selected === key ? theme.primary : theme.border,
                borderWidth: selected === key ? 2 : 1,
              }}
            >
              <Subtitle>
                {tier.emoji} {tier.label}
              </Subtitle>
              <Body style={{ color: theme.textMuted }}>
                {tier.price_usd === 0 ? "Free forever" : `$${tier.price_usd.toFixed(2)} ${key === "annual" ? "/ year" : "/ month"}`}
              </Body>
            </Card>
          </Pressable>
        ))}
      </View>

      <Button label="Confirm subscription" emoji="💛" onPress={onSubscribe} loading={loading} disabled={!selected} />
      <Muted onPress={logOut} style={{ textAlign: "center" }}>
        Log out
      </Muted>
    </Screen>
  );
}
