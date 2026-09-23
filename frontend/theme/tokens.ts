// Exact palette from the app's style guide (Playfair Display + Poppins,
// cream/blush/ink/gold). Pink is the surface, black and gold are the
// action, rose is for small accent text only.
export const palette = {
  cream: "#FBF6F1",
  blush: "#F6C9D6",
  blushLight: "#FCE8EE",
  petal: "#E68AAA",
  rose: "#8E3558",
  ink: "#211B1C",
  gold: "#C4952B",
  muted: "#6B5F62",
  border: "#F0E2E4",
  white: "#FFFFFF",
};

export const darkPalette = {
  background: "#141112",
  card: "#211B1C",
  cardAlt: "#2C2325",
  text: "#FBF6F1",
  textMuted: "#C4B7BA",
};

export type Theme = {
  mode: "light" | "dark";
  background: string;
  surface: string;
  surfaceAlt: string;
  // Blush Light — tiles, ring tracks, inner panels. Distinct from
  // surfaceAlt (Blush), which is for hero cards, chips, and user bubbles.
  tileBackground: string;
  primary: string;
  accent: string;
  text: string;
  textMuted: string;
  border: string;
  success: string;
  danger: string;
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
  surface: palette.white,
  surfaceAlt: palette.blush,
  tileBackground: palette.blushLight,
  primary: palette.gold,
  accent: palette.rose,
  text: palette.ink,
  textMuted: palette.muted,
  border: palette.border,
  success: "#7BA98A",
  danger: "#C4665A",
  tabBarBackground: palette.ink,
  tabBarInactive: "#A99C98",
};

export const darkTheme: Theme = {
  mode: "dark",
  background: darkPalette.background,
  surface: darkPalette.card,
  surfaceAlt: darkPalette.cardAlt,
  tileBackground: darkPalette.cardAlt,
  primary: palette.gold,
  accent: palette.petal,
  text: darkPalette.text,
  textMuted: darkPalette.textMuted,
  border: "#3A2F31",
  success: "#8FC7A0",
  danger: "#E08A7D",
  tabBarBackground: "#0D0B0B",
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
  lg: 20,
  xl: 32,
  xxl: 48,
};

export const radii = {
  sm: 8,
  md: 18,
  lg: 26,
  pill: 999,
};

// Soft, dimensional shadow used sparingly on lifted surfaces so the app
// reads as editorial-flat most of the time, with a little lift where it
// counts. No gradients anywhere in this system — flat color fills only.
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
