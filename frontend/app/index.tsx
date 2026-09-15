import React, { useEffect, useState } from "react";
import { ActivityIndicator, View } from "react-native";
import { Redirect } from "expo-router";
import { useAuth } from "@/context/AuthContext";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";

export default function Index() {
  const { user, isLoading } = useAuth();
  const { theme } = useAppTheme();
  const [needsOnboarding, setNeedsOnboarding] = useState<boolean | null>(null);

  const subscriptionOk = !!user && user.subscription_status !== "expired" && user.subscription_status !== "canceled";

  useEffect(() => {
    if (!subscriptionOk) {
      setNeedsOnboarding(null);
      return;
    }
    apiRequest<{ era: string | null }>("/blueprint")
      .then((bp) => setNeedsOnboarding(!bp.era))
      .catch(() => setNeedsOnboarding(false));
  }, [subscriptionOk]);

  if (isLoading || (subscriptionOk && needsOnboarding === null)) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: theme.background }}>
        <ActivityIndicator color={theme.primary} size="large" />
      </View>
    );
  }

  if (!user) {
    return <Redirect href="/(auth)/welcome" />;
  }

  if (!subscriptionOk) {
    return <Redirect href="/(auth)/paywall" />;
  }

  if (needsOnboarding) {
    return <Redirect href="/(onboarding)/blueprint" />;
  }

  return <Redirect href="/(tabs)/home" />;
}
