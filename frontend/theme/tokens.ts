export const palette = {
  blush: "#F6C8D8",
  softPink: "#FCEEF3",
  gold: "#D4AF37",
  black: "#1A1A1A",
  cream: "#FFF9F6",
};

export const darkPalette = {
  background: "#111111",
  card: "#1A1A1A",
  cardAlt: "#242024",
  text: "#FFF9F6",
  textMuted: "#C9BEC3",
};

export const goldGradientLight = ["#F6E2A0", "#D4AF37", "#A87A1F"];
export const goldGradientDark = ["#F6E2A0", "#D4AF37", "#9C7A2E"];

export type Theme = {
  mode: "light" | "dark";
  background: string;
  surface: string;
  surfaceAlt: string;
  primary: string;
  accent: string;
  text: string;
  textMuted: string;
  border: string;
  success: string;
  danger: string;
  goldGradient: string[];
};

export const lightTheme: Theme = {
  mode: "light",
  background: palette.cream,
  surface: palette.softPink,
  surfaceAlt: palette.blush,
  primary: palette.gold,
  accent: palette.gold,
  text: palette.black,
  textMuted: "#7A6E72",
  border: "#F0DCE3",
  success: "#7BA98A",
  danger: "#C4665A",
  goldGradient: goldGradientLight,
};

export const darkTheme: Theme = {
  mode: "dark",
  background: darkPalette.background,
  surface: darkPalette.card,
  surfaceAlt: darkPalette.cardAlt,
  primary: palette.gold,
  accent: palette.blush,
  text: darkPalette.text,
  textMuted: darkPalette.textMuted,
  border: "#2E2A2C",
  success: "#8FC7A0",
  danger: "#E08A7D",
  goldGradient: goldGradientDark,
};

export const typography = {
  display: "PlayfairDisplay_700Bold",
  displayMedium: "PlayfairDisplay_600SemiBold",
  displayItalic: "PlayfairDisplay_600SemiBold_Italic",
  body: "Poppins_400Regular",
  bodyMedium: "Poppins_500Medium",
  bodyBold: "Poppins_600SemiBold",
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const radii = {
  sm: 8,
  md: 16,
  lg: 24,
  pill: 999,
};
