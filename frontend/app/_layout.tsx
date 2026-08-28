import React, { useEffect } from "react";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import {
  useFonts as useCormorantFonts,
  CormorantGaramond_600SemiBold,
  CormorantGaramond_700Bold,
} from "@expo-google-fonts/cormorant-garamond";
import { useFonts as useDMSansFonts, DMSans_400Regular, DMSans_500Medium, DMSans_700Bold } from "@expo-google-fonts/dm-sans";
import { ThemeProvider, useAppTheme } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";

SplashScreen.preventAutoHideAsync().catch(() => {});

function RootStack() {
  const { theme } = useAppTheme();
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.background },
      }}
    />
  );
}

export default function RootLayout() {
  const [cormorantLoaded] = useCormorantFonts({ CormorantGaramond_600SemiBold, CormorantGaramond_700Bold });
  const [dmSansLoaded] = useDMSansFonts({ DMSans_400Regular, DMSans_500Medium, DMSans_700Bold });

  const fontsLoaded = cormorantLoaded && dmSansLoaded;

  useEffect(() => {
    if (fontsLoaded) {
      SplashScreen.hideAsync().catch(() => {});
    }
  }, [fontsLoaded]);

  if (!fontsLoaded) {
    return null;
  }

  return (
    <ThemeProvider>
      <AuthProvider>
        <RootStack />
      </AuthProvider>
    </ThemeProvider>
  );
}
