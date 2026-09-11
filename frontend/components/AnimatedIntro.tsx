import React, { useEffect, useRef } from "react";
import { Animated, Easing, Pressable, StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useAppTheme } from "@/context/ThemeContext";
import { typography } from "@/theme/tokens";

const AUTO_ADVANCE_MS = 2600;

export function AnimatedIntro({ onDone }: { onDone: () => void }) {
  const { theme } = useAppTheme();
  const logoScale = useRef(new Animated.Value(0.72)).current;
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const taglineOpacity = useRef(new Animated.Value(0)).current;
  const taglineTranslate = useRef(new Animated.Value(14)).current;
  const glowOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.sequence([
      Animated.timing(glowOpacity, { toValue: 1, duration: 500, useNativeDriver: true }),
      Animated.parallel([
        Animated.spring(logoScale, { toValue: 1, friction: 6, tension: 60, useNativeDriver: true }),
        Animated.timing(logoOpacity, { toValue: 1, duration: 650, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
      ]),
      Animated.parallel([
        Animated.timing(taglineOpacity, { toValue: 1, duration: 500, useNativeDriver: true }),
        Animated.timing(taglineTranslate, { toValue: 0, duration: 500, easing: Easing.out(Easing.cubic), useNativeDriver: true }),
      ]),
    ]).start();

    const timer = setTimeout(onDone, AUTO_ADVANCE_MS);
    return () => clearTimeout(timer);
  }, []);

  return (
    <Pressable style={styles.flex} onPress={onDone}>
      <LinearGradient
        colors={[theme.background, theme.surfaceAlt, theme.background]}
        style={styles.flex}
      >
        <View style={styles.center}>
          <Animated.View
            style={[
              styles.glow,
              {
                backgroundColor: theme.accent,
                opacity: Animated.multiply(glowOpacity, 0.22),
              },
            ]}
          />
          <Animated.Image
            source={require("@/assets/logo.png")}
            resizeMode="contain"
            style={[styles.logo, { opacity: logoOpacity, transform: [{ scale: logoScale }] }]}
          />
          <Animated.Text
            style={[
              styles.tagline,
              { color: theme.text, opacity: taglineOpacity, transform: [{ translateY: taglineTranslate }] },
            ]}
          >
            Plan your life. Glow daily. Become her.
          </Animated.Text>
        </View>
      </LinearGradient>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  glow: {
    position: "absolute",
    width: 420,
    height: 420,
    borderRadius: 210,
  },
  logo: { width: 260, height: 260 },
  tagline: {
    fontFamily: typography.displayMedium,
    fontStyle: "italic",
    fontSize: 17,
    marginTop: 18,
    letterSpacing: 0.3,
  },
});
