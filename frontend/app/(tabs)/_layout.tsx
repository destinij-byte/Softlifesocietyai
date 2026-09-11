import React from "react";
import { Tabs } from "expo-router";
import { View } from "react-native";
import { Icon, IconName } from "@/components/Icon";
import { useAppTheme } from "@/context/ThemeContext";
import { elevation, radii } from "@/theme/tokens";

function TabIcon({ name, color, focused }: { name: IconName; color: string; focused: boolean }) {
  const { theme } = useAppTheme();
  return (
    <View
      style={
        focused
          ? {
              backgroundColor: theme.mode === "dark" ? "rgba(212,175,55,0.16)" : "rgba(212,175,55,0.14)",
              borderRadius: radii.md,
              paddingHorizontal: 12,
              paddingVertical: 5,
              ...elevation.soft,
              shadowOpacity: theme.mode === "dark" ? 0 : 0.06,
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

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.primary,
        tabBarInactiveTintColor: theme.textMuted,
        tabBarStyle: { backgroundColor: theme.surface, borderTopColor: theme.border },
        tabBarLabelStyle: { fontSize: 10 },
        tabBarShowLabel: true,
      }}
    >
      <Tabs.Screen
        name="home"
        options={{ title: "Home", tabBarIcon: ({ color, focused }) => <TabIcon name="home" color={color} focused={focused} /> }}
      />
      <Tabs.Screen
        name="your-ai"
        options={{ title: "Your AI", tabBarIcon: ({ color, focused }) => <TabIcon name="sparkle" color={color} focused={focused} /> }}
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
        name="routines"
        options={{ title: "Routines", tabBarIcon: ({ color, focused }) => <TabIcon name="checklist" color={color} focused={focused} /> }}
      />
      <Tabs.Screen
        name="challenges"
        options={{ title: "Challenges", tabBarIcon: ({ color, focused }) => <TabIcon name="trophy" color={color} focused={focused} /> }}
      />
      <Tabs.Screen
        name="me"
        options={{ title: "Me", tabBarIcon: ({ color, focused }) => <TabIcon name="person" color={color} focused={focused} /> }}
      />
    </Tabs>
  );
}
