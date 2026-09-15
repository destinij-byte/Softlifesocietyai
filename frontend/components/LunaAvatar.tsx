import React from "react";
import { Image, View } from "react-native";
import { useAppTheme } from "@/context/ThemeContext";

type LunaAvatarProps = {
  size?: number;
};

/** Luna Reyes' face — same gold-ringed circular frame language as the user
 * Avatar component, so she reads as a peer presence in the chat and on Home,
 * not a generic icon badge. */
export function LunaAvatar({ size = 38 }: LunaAvatarProps) {
  const { theme } = useAppTheme();

  return (
    <View style={{ width: size, height: size }}>
      <View
        style={{
          position: "absolute",
          top: -3,
          left: -3,
          right: -3,
          bottom: -3,
          borderRadius: (size + 6) / 2,
          borderWidth: 1.5,
          borderColor: theme.accent,
        }}
      />
      <View
        style={{
          width: size,
          height: size,
          borderRadius: size / 2,
          overflow: "hidden",
          borderWidth: 2,
          borderColor: theme.background,
        }}
      >
        <Image source={require("@/assets/luna-avatar.png")} style={{ width: size, height: size }} resizeMode="cover" />
      </View>
    </View>
  );
}
