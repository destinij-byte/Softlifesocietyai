import React from "react";
import { Stack } from "expo-router";
import { useAppTheme } from "@/context/ThemeContext";

export default function AuthLayout() {
  const { theme } = useAppTheme();
  return (
    <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: theme.background } }} />
  );
}
