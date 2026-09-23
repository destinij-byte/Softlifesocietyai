// Soft Life Society — design tokens.
// Merged from the Sep 2026 design handoff (design/src/theme.ts) into the
// app's existing theme system rather than replacing it: `colors`/`fonts`/
// `type`/`spacing`/`radius`/`sizes`/`ringSizes` below are the handoff's own
// token names and values verbatim — the single source of truth for brand
// color, type, spacing and shape. The handoff itself is light-only; this
// app also ships a light/dark toggle, so `lightTheme`/`darkTheme` layer a
// small semantic indirection on top (background/surface/text/...) for the
// handful of things that must flip with mode. Everything else (blush,
// petal, gold, rose, the type scale, spacing, radius) is brand-fixed and
// used directly from `colors`/`type` regardless of mode.

export const colors = {
  cream: "#FBF6F1", // page background
  white: "#FFFFFF", // standard cards
  blush: "#F6C9D6", // ONE hero card per screen, chips, user chat bubbles, soft buttons
  blushLight: "#FCE8EE", // inner panels, tiles, ring/bar tracks, skeletons
  petal: "#E68AAA", // progress fills + unchecked task circles ONLY (never text)
  rose: "#8E3558", // small accent text: eyebrows, links, labels
  ink: "#211B1C", // primary text, tab bar, primary buttons, dark cards
  gold: "#C4952B", // text/icons on ink, active tab, streak chip. Restrained: never large fills on cream
  muted: "#6B5F62", // captions, secondary text
  body: "#463C3E", // long-form body text on blush/white
  onInkMuted: "#E9DDD8", // secondary text on ink cards
  tabInactive: "#A99C98", // inactive tab icons/labels
  border: "#F0E2E4", // 1px card outlines
  success: "#6FBF8E", // online dot only
} as const;

// Legacy name, kept as an alias so existing call sites keep working.
export const palette = colors;

// expo-google-fonts family names (@expo-google-fonts/playfair-display, @expo-google-fonts/poppins)
export const fonts = {
  display: "PlayfairDisplay_600SemiBold",
  displayItalic: "PlayfairDisplay_500Medium_Italic",
  body: "Poppins_400Regular",
  bodyMedium: "Poppins_500Medium",
  bodySemiBold: "Poppins_600SemiBold",
} as const;

// Legacy names, kept as aliases so existing call sites keep working.
export const typography = {
  display: fonts.display,
  displayMedium: fonts.display,
  displayItalic: fonts.displayItalic,
  body: fonts.body,
  bodyMedium: fonts.bodyMedium,
  bodyBold: fonts.bodySemiBold,
};

export const type = {
  screenTitle: { fontFamily: fonts.display, fontSize: 30, lineHeight: 35, color: colors.ink },
  sectionTitle: { fontFamily: fonts.display, fontSize: 20, lineHeight: 26, color: colors.ink },
  cardTitle: { fontFamily: fonts.display, fontSize: 18, lineHeight: 24, color: colors.ink },
  bigNumber: { fontFamily: fonts.display, fontSize: 48, lineHeight: 52, color: colors.ink },
  statNumber: { fontFamily: fonts.display, fontSize: 26, lineHeight: 30, color: colors.ink },
  quote: { fontFamily: fonts.displayItalic, fontSize: 22, lineHeight: 30, color: colors.ink },
  quoteSmall: { fontFamily: fonts.displayItalic, fontSize: 18, lineHeight: 25, color: colors.ink },
  body: { fontFamily: fonts.body, fontSize: 14, lineHeight: 21, color: colors.body },
  bodyStrong: { fontFamily: fonts.bodyMedium, fontSize: 14, lineHeight: 21, color: colors.ink },
  label: { fontFamily: fonts.bodySemiBold, fontSize: 14, lineHeight: 20, color: colors.ink },
  button: { fontFamily: fonts.bodySemiBold, fontSize: 15, lineHeight: 20 },
  buttonSmall: { fontFamily: fonts.bodySemiBold, fontSize: 13, lineHeight: 18 },
  caption: { fontFamily: fonts.body, fontSize: 12, lineHeight: 17, color: colors.muted },
  eyebrow: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 11,
    lineHeight: 15,
    letterSpacing: 1.3,
    textTransform: "uppercase" as const,
    color: colors.rose,
  },
  tabLabel: { fontFamily: fonts.body, fontSize: 11, lineHeight: 14 },
} as const;

export const spacing = {
  xxs: 4,
  xs: 8,
  sm: 10,
  md: 12,
  lg: 16, // default gap between sections/cards, card padding
  xl: 20, // screen horizontal padding, hero card padding
  xxl: 28, // screen top padding
} as const;

export const radius = {
  tile: 16,
  chipTile: 18,
  card: 22,
  hero: 26,
  pill: 999,
} as const;

// Legacy name/shape, kept as an alias so existing call sites keep working.
export const radii = {
  sm: radius.tile,
  md: radius.chipTile,
  lg: radius.hero,
  pill: radius.pill,
};

export const sizes = {
  minTap: 44, // every tappable element is at least 44x44
  button: 48, // full-size button height
  tabBar: 78,
  iconButton: 44,
  fab: 60,
  avatarSm: 36,
  avatarMd: 44,
  avatarLg: 56,
} as const;

export const ringSizes = { sm: 56, md: 64, lg: 72, xl: 96, hero: 120 } as const;

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
  // Long-form paragraph text — distinct from `text` (ink), matching
  // colors.body. Same value as `text` in dark mode (no separate dark body
  // tone was specified).
  bodyText: string;
  // Secondary text specifically on ink-background cards.
  onInkMuted: string;
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
  background: colors.cream,
  surface: colors.white,
  surfaceAlt: colors.blush,
  tileBackground: colors.blushLight,
  primary: colors.gold,
  accent: colors.rose,
  text: colors.ink,
  textMuted: colors.muted,
  bodyText: colors.body,
  onInkMuted: colors.onInkMuted,
  border: colors.border,
  success: colors.success,
  danger: "#C4665A",
  tabBarBackground: colors.ink,
  tabBarInactive: colors.tabInactive,
};

const darkPalette = {
  background: "#141112",
  card: "#211B1C",
  cardAlt: "#2C2325",
  text: "#FBF6F1",
  textMuted: "#C4B7BA",
};

export const darkTheme: Theme = {
  mode: "dark",
  background: darkPalette.background,
  surface: darkPalette.card,
  surfaceAlt: darkPalette.cardAlt,
  tileBackground: darkPalette.cardAlt,
  primary: colors.gold,
  accent: colors.petal,
  text: darkPalette.text,
  textMuted: darkPalette.textMuted,
  bodyText: darkPalette.text,
  onInkMuted: darkPalette.textMuted,
  border: "#3A2F31",
  success: "#8FC7A0",
  danger: "#E08A7D",
  tabBarBackground: "#0D0B0B",
  tabBarInactive: "#8A8286",
};

// Soft, dimensional shadow used sparingly on lifted surfaces so the app
// reads as editorial-flat most of the time, with a little lift where it
// counts. No gradients anywhere in this system — flat color fills only.
// Not used by any of the officially-specced components (which never use a
// shadow), only by a handful of pre-existing screen-level accents.
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

export const theme = { colors, fonts, type, spacing, radius, sizes, ringSizes };
export default theme;
