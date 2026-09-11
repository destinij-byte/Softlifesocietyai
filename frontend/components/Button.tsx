import React, { useEffect, useRef } from "react";
import { ActivityIndicator, Animated, Pressable, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useAppTheme } from "@/context/ThemeContext";
import { radii, spacing, typography } from "@/theme/tokens";

type ButtonProps = {
  label: string;
  emoji?: string;
  icon?: React.ReactNode;
  onPress: () => void;
  variant?: "primary" | "secondary" | "ghost";
  loading?: boolean;
  disabled?: boolean;
};

export function Button({ label, emoji, icon, onPress, variant = "primary", loading, disabled }: ButtonProps) {
  const { theme } = useAppTheme();
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (variant !== "primary") return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 2200, useNativeDriver: true }),
        Animated.timing(shimmer, { toValue: 0, duration: 0, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [variant, shimmer]);

  const shimmerTranslate = shimmer.interpolate({ inputRange: [0, 1], outputRange: [-140, 220] });

  if (variant === "primary") {
    return (
      <Pressable onPress={onPress} disabled={disabled || loading} style={{ opacity: disabled ? 0.5 : 1 }}>
        <LinearGradient colors={theme.goldGradient as [string, string, string]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.base}>
          <Animated.View
            pointerEvents="none"
            style={[styles.shimmer, { transform: [{ translateX: shimmerTranslate }, { rotate: "20deg" }] }]}
          />
          {loading ? (
            <ActivityIndicator color="#1A1A1A" />
          ) : (
            <View style={styles.content}>
              {icon}
              <Text style={[styles.label, { color: "#1A1A1A" }]}>
                {emoji ? `${emoji} ` : ""}
                {label}
              </Text>
            </View>
          )}
        </LinearGradient>
      </Pressable>
    );
  }

  const backgroundColor = variant === "secondary" ? theme.surfaceAlt : "transparent";
  const textColor = theme.text;
  const borderColor = variant === "ghost" ? theme.border : "transparent";

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.base,
        {
          backgroundColor,
          borderColor,
          borderWidth: variant === "ghost" ? 1 : 0,
          opacity: pressed ? 0.85 : disabled ? 0.5 : 1,
        },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={textColor} />
      ) : (
        <View style={styles.content}>
          {icon}
          <Text style={[styles.label, { color: textColor }]}>
            {emoji ? `${emoji} ` : ""}
            {label}
          </Text>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  content: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  base: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.pill,
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
  label: {
    fontFamily: typography.bodyBold,
    fontSize: 16,
  },
  shimmer: {
    position: "absolute",
    top: -40,
    bottom: -40,
    width: 60,
    backgroundColor: "rgba(255,255,255,0.35)",
  },
});
