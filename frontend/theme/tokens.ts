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
  // The bottom nav is a deliberate departure from the content surfaces —
  // always a near-black bar with gold accents, in both themes. It's the one
  // piece of chrome that stays constant so it reads as a signature, not
  // just "whatever the current theme's surface color is."
  tabBarBackground: string;
  tabBarInactive: string;
};

export const lightTheme: Theme = {
  mode: "light",
  background: palette.cream,
  surface: "#FFFFFF",
  surfaceAlt: palette.blush,
  primary: palette.gold,
  accent: palette.gold,
  text: palette.black,
  textMuted: "#7A6E72",
  border: "#F0DCE3",
  success: "#7BA98A",
  danger: "#C4665A",
  goldGradient: goldGradientLight,
  tabBarBackground: palette.black,
  tabBarInactive: "#8A8286",
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
  tabBarBackground: "#0D0D0D",
  tabBarInactive: "#8A8286",
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

// Soft, dimensional shadows used sparingly on hero/accent surfaces so the app
// reads as editorial-flat most of the time, with a little lift where it counts.
export const elevation = {
  soft: {
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  lifted: {
    shadowColor: "#000",
    shadowOpacity: 0.14,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 8 },
    elevation: 7,
  },
};
