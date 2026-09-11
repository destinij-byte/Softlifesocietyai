import React, { useEffect, useState } from "react";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import {
  useFonts as usePlayfairFonts,
  PlayfairDisplay_600SemiBold,
  PlayfairDisplay_600SemiBold_Italic,
  PlayfairDisplay_700Bold,
} from "@expo-google-fonts/playfair-display";
import { useFonts as usePoppinsFonts, Poppins_400Regular, Poppins_500Medium, Poppins_600SemiBold } from "@expo-google-fonts/poppins";
import { ThemeProvider, useAppTheme } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
import { AnimatedIntro } from "@/components/AnimatedIntro";

SplashScreen.preventAutoHideAsync().catch(() => {});

function RootStack() {
  const { theme } = useAppTheme();
  const [introDone, setIntroDone] = useState(false);

  if (!introDone) {
    return <AnimatedIntro onDone={() => setIntroDone(true)} />;
  }

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
  const [playfairLoaded] = usePlayfairFonts({ PlayfairDisplay_600SemiBold, PlayfairDisplay_600SemiBold_Italic, PlayfairDisplay_700Bold });
  const [poppinsLoaded] = usePoppinsFonts({ Poppins_400Regular, Poppins_500Medium, Poppins_600SemiBold });

  const fontsLoaded = playfairLoaded && poppinsLoaded;

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
