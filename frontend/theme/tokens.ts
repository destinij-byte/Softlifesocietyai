export const palette = {
  ivory: "#FBF6EF",
  cream: "#F5EAD9",
  blush: "#F3D8D3",
  gold: "#C9A24B",
  rose: "#B5657A",
  ink: "#2B2320",
};

export const darkPalette = {
  ivoryDark: "#181410",
  creamDark: "#221C17",
  blushDark: "#3A2A2A",
  goldDark: "#D9B968",
  roseDark: "#D98CA0",
  inkLight: "#F3ECE3",
};

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
};

export const lightTheme: Theme = {
  mode: "light",
  background: palette.ivory,
  surface: palette.cream,
  surfaceAlt: palette.blush,
  primary: palette.rose,
  accent: palette.gold,
  text: palette.ink,
  textMuted: "#6B5E54",
  border: "#E7D9C8",
  success: "#7BA98A",
  danger: "#C4665A",
};

export const darkTheme: Theme = {
  mode: "dark",
  background: darkPalette.ivoryDark,
  surface: darkPalette.creamDark,
  surfaceAlt: darkPalette.blushDark,
  primary: darkPalette.roseDark,
  accent: darkPalette.goldDark,
  text: darkPalette.inkLight,
  textMuted: "#C9BCB0",
  border: "#3A2F27",
  success: "#8FC7A0",
  danger: "#E08A7D",
};

export const typography = {
  display: "CormorantGaramond_700Bold",
  displayMedium: "CormorantGaramond_600SemiBold",
  body: "DMSans_400Regular",
  bodyMedium: "DMSans_500Medium",
  bodyBold: "DMSans_700Bold",
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
