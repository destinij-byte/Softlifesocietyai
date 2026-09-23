import React, { useEffect, useState } from "react";
import { Alert, Pressable, View } from "react-native";
import { router } from "expo-router";
import type { PurchasesOffering, PurchasesPackage } from "react-native-purchases";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { useAuth } from "@/context/AuthContext";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { configureBilling, getCurrentOffering, isAvailable, purchasePackage, syncSubscription, unavailableMessage } from "@/services/billing";
import { spacing } from "@/theme/tokens";

type Tier = { label: string; price_usd: number; emoji: string };
type Tiers = Record<string, Tier>;

// RevenueCat package identifiers must be configured in the dashboard to
// match these keys exactly (same convention as the backend's
// ENTITLEMENT_TIER_MAP in app/services/revenuecat.py) — this is how we find
// the right purchasable package for the tier the user tapped.
const PACKAGE_IDENTIFIERS: Record<string, string> = {
  monthly: "monthly",
  annual: "annual",
  founding: "founding",
};

function trialDaysLeft(trialEndsAt: string): number {
  const diffMs = new Date(trialEndsAt).getTime() - Date.now();
  return Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
}

export default function Paywall() {
  const { user, refreshUser, logOut } = useAuth();
  const { theme } = useAppTheme();
  const [tiers, setTiers] = useState<Tiers>({});
  const [offering, setOffering] = useState<PurchasesOffering | null>(null);
  const [selected, setSelected] = useState<string>("annual");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiRequest<Tiers>("/subscriptions/tiers", { auth: false }).then(setTiers).catch(() => {});
  }, []);

  useEffect(() => {
    if (!user) return;
    (async () => {
      await configureBilling(user.id);
      if (isAvailable()) {
        try {
          setOffering(await getCurrentOffering());
        } catch {
          setOffering(null);
        }
      }
    })();
  }, [user?.id]);

  const daysLeft = user ? trialDaysLeft(user.trial_ends_at) : 0;
  const isExpired = user?.subscription_status === "expired";

  const findPackage = (tierKey: string): PurchasesPackage | undefined => {
    const identifier = PACKAGE_IDENTIFIERS[tierKey];
    return offering?.availablePackages.find((pkg) => pkg.identifier === identifier);
  };

  const onSubscribe = async () => {
    if (selected === "free") {
      router.replace("/");
      return;
    }

    if (!isAvailable()) {
      Alert.alert("Not available here", unavailableMessage() ?? "Purchases aren't available in this build.");
      return;
    }

    const pkg = findPackage(selected);
    if (!pkg) {
      Alert.alert("Plan unavailable", "This plan isn't set up yet — please try another or check back soon.");
      return;
    }

    setLoading(true);
    try {
      await purchasePackage(pkg);
      await syncSubscription();
      await refreshUser();
      router.replace("/");
    } catch (error: unknown) {
      const cancelled = (error as { userCancelled?: boolean } | null)?.userCancelled;
      if (!cancelled) {
        const message = error instanceof Error ? error.message : "Something went wrong with your purchase.";
        Alert.alert("Purchase failed", message);
      }
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
                {tier.price_usd === 0 ? "Free forever" : `$${tier.price_usd.toFixed(2)} ${key === "monthly" ? "/ month" : "/ year"}`}
              </Body>
            </Card>
          </Pressable>
        ))}
      </View>

      {!isAvailable() && selected !== "free" && (
        <Body style={{ color: theme.textMuted, textAlign: "center" }}>
          {unavailableMessage() ?? "Purchases aren't available in this preview build."}
        </Body>
      )}

      <Button label={selected === "free" ? "Continue" : "Confirm subscription"} emoji="💛" onPress={onSubscribe} loading={loading} disabled={!selected} />
      <Muted onPress={logOut} style={{ textAlign: "center" }}>
        Log out
      </Muted>
    </Screen>
  );
}
