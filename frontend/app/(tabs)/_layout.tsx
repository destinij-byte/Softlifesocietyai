import React from "react";
import { Tabs } from "expo-router";
import { Text } from "react-native";
import { useAppTheme } from "@/context/ThemeContext";

function TabIcon({ emoji }: { emoji: string }) {
  return <Text style={{ fontSize: 20 }}>{emoji}</Text>;
}

export default function TabsLayout() {
  const { theme } = useAppTheme();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.primary,
        tabBarInactiveTintColor: theme.textMuted,
        tabBarStyle: { backgroundColor: theme.surface, borderTopColor: theme.border },
      }}
    >
      <Tabs.Screen name="luna" options={{ title: "Luna", tabBarIcon: () => <TabIcon emoji="🌸" /> }} />
      <Tabs.Screen name="track" options={{ title: "Track", tabBarIcon: () => <TabIcon emoji="📊" /> }} />
      <Tabs.Screen name="meals" options={{ title: "Meals", tabBarIcon: () => <TabIcon emoji="🍽️" /> }} />
      <Tabs.Screen name="challenges" options={{ title: "Challenges", tabBarIcon: () => <TabIcon emoji="🏆" /> }} />
      <Tabs.Screen name="community" options={{ title: "Community", tabBarIcon: () => <TabIcon emoji="💛" /> }} />
      <Tabs.Screen name="profile" options={{ title: "Profile", tabBarIcon: () => <TabIcon emoji="⚙️" /> }} />
    </Tabs>
  );
}
