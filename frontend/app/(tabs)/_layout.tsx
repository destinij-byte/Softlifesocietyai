import React from "react";
import { Redirect, Tabs } from "expo-router";
import { View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Icon, IconName } from "@/components/Icon";
import { useAuth } from "@/context/AuthContext";
import { useAppTheme } from "@/context/ThemeContext";
import { fonts, radii, sizes } from "@/theme/tokens";

function TabIcon({ name, color, focused }: { name: IconName; color: string; focused: boolean }) {
  return (
    <View
      style={
        focused
          ? {
              backgroundColor: "rgba(196,149,43,0.16)",
              borderRadius: radii.md,
              paddingHorizontal: 12,
              paddingVertical: 5,
            }
          : { paddingHorizontal: 12, paddingVertical: 5 }
      }
    >
      <Icon name={name} size={20} color={color} />
    </View>
  );
}

export default function TabsLayout() {
  const { theme } = useAppTheme();
  const { user, isLoading } = useAuth();
  const insets = useSafeAreaInsets();

  // Logging out (or a 401 forcing one) clears `user` while we're still deep
  // in the tab stack — without this, the tabs stay mounted and every screen
  // just renders blank (`if (!user) return null`) instead of returning to auth.
  if (!isLoading && !user) {
    return <Redirect href="/(auth)/welcome" />;
  }

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.primary,
        tabBarInactiveTintColor: theme.tabBarInactive,
        tabBarStyle: {
          backgroundColor: theme.tabBarBackground,
          borderTopColor: "rgba(196,149,43,0.14)",
          height: sizes.tabBar + insets.bottom,
          paddingBottom: insets.bottom,
          paddingTop: 8,
        },
        tabBarLabelStyle: { fontSize: 11, fontFamily: fonts.body },
        tabBarShowLabel: true,
      }}
    >
      <Tabs.Screen
        name="home"
        options={{ title: "Home", tabBarIcon: ({ color, focused }) => <TabIcon name="home" color={color} focused={focused} /> }}
      />
      <Tabs.Screen
        name="luna"
        options={{ title: "Luna", tabBarIcon: ({ color, focused }) => <TabIcon name="plus" color={color} focused={focused} /> }}
      />
      <Tabs.Screen
        name="nourish-ai"
        options={{ title: "Nourish", tabBarIcon: ({ color, focused }) => <TabIcon name="plate" color={color} focused={focused} /> }}
      />
      <Tabs.Screen
        name="goals"
        options={{ title: "Goals", tabBarIcon: ({ color, focused }) => <TabIcon name="target" color={color} focused={focused} /> }}
      />
      <Tabs.Screen
        name="you"
        options={{ title: "More", tabBarIcon: ({ color, focused }) => <TabIcon name="dots" color={color} focused={focused} /> }}
      />
      {/* Routines and Wins are still full screens (reachable from Home's
          "Today's Ritual" and Goals' Wins link) — href:null keeps them out
          of the tab bar without removing the route or the feature. */}
      <Tabs.Screen name="routines" options={{ href: null }} />
      <Tabs.Screen name="challenges" options={{ href: null }} />
      <Tabs.Screen name="night-reset" options={{ href: null }} />
      <Tabs.Screen name="progress" options={{ href: null }} />
      <Tabs.Screen name="weekly-reset" options={{ href: null }} />
    </Tabs>
  );
}
