import React from "react";
import { Tabs } from "expo-router";
import { Text } from "react-native";
import { useAppTheme } from "@/context/ThemeContext";

function TabIcon({ emoji }: { emoji: string }) {
  return <Text style={{ fontSize: 18 }}>{emoji}</Text>;
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
        tabBarLabelStyle: { fontSize: 10 },
      }}
    >
      <Tabs.Screen name="home" options={{ title: "Home", tabBarIcon: () => <TabIcon emoji="🏠" /> }} />
      <Tabs.Screen name="your-ai" options={{ title: "Your AI", tabBarIcon: () => <TabIcon emoji="✨" /> }} />
      <Tabs.Screen name="nourish-ai" options={{ title: "Nourish", tabBarIcon: () => <TabIcon emoji="🍽️" /> }} />
      <Tabs.Screen name="goals" options={{ title: "Goals", tabBarIcon: () => <TabIcon emoji="🎯" /> }} />
      <Tabs.Screen name="routines" options={{ title: "Routines", tabBarIcon: () => <TabIcon emoji="📋" /> }} />
      <Tabs.Screen name="challenges" options={{ title: "Challenges", tabBarIcon: () => <TabIcon emoji="🏆" /> }} />
      <Tabs.Screen name="me" options={{ title: "Me", tabBarIcon: () => <TabIcon emoji="👤" /> }} />
    </Tabs>
  );
}
