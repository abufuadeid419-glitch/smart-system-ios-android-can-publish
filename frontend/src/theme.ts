// Design tokens for this app. Light theme only.Always modify the colors and theme to Dark, Light or Dark and Light according to the design guidelines.
//
// The keys match the "color" block of /app/design_guidelines.json. Fill the
// values from that file (or from the user's brand colors). Keep every key; do
// not add a second theme or colors file; do not write color literals in
// components.
//
// How the names work: a plain key is a background, and its `on` partner is the
// text or icon color that sits on top of it. Always use them as a pair.
//   <View style={{ backgroundColor: colors.brandPrimary }}>
//     <Text style={{ color: colors.onBrandPrimary }}>Continue</Text>
//   </View>
//
// Styling a screen or component: build the sheet with makeStyles so colors
// and layout live together and follow the active scheme:
//   const useStyles = makeStyles((colors) => ({
//     card: { backgroundColor: colors.surfaceSecondary, padding: 16 },
//     title: { color: colors.onSurfaceSecondary, fontSize: 16 },
//   }));
//   function Screen() {
//     const styles = useStyles();
//     return <View style={styles.card}><Text style={styles.title}>Hi</Text></View>;
//   }
// For color props that are not styles (icon color, placeholderTextColor,
// ActivityIndicator) read useTheme().colors inside the component.
// Never call StyleSheet.create with color values at module level; it cannot
// follow the scheme.
//
// To support dark mode later: add `dark` to `themes` with every key filled.
// Nothing else changes; the device setting takes over automatically.
// Feel free to add as many new colors as you need to support the design guidelines.

import { useMemo, useSyncExternalStore } from "react";
import { Appearance, StyleSheet } from "react-native";

import { storage } from "@/src/utils/storage";

export type ColorScheme = "light" | "dark";

const light = {
  surface: "#FFFFFF",
  onSurface: "#1A1A1A",
  surfaceSecondary: "#F5F5F5",
  onSurfaceSecondary: "#333333",
  surfaceTertiary: "#EBEBEB",
  onSurfaceTertiary: "#4D4D4D",
  surfaceInverse: "#1A1A1A",
  onSurfaceInverse: "#FFFFFF",
  brand: "#2D6A4F",
  onBrand: "#FFFFFF",
  brandPrimary: "#40916C",
  onBrandPrimary: "#FFFFFF",
  brandSecondary: "#52B788",
  onBrandSecondary: "#1A1A1A",
  brandTertiary: "#D8F3E6",
  onBrandTertiary: "#1B4332",
  accent: "#40916C",
  onAccent: "#FFFFFF",
  accentSoft: "#D8F3E6",
  onAccentSoft: "#1B4332",
  success: "#28A745",
  onSuccess: "#FFFFFF",
  warning: "#FFB703",
  onWarning: "#1A1A1A",
  error: "#D00000",
  onError: "#FFFFFF",
  info: "#8D99AE",
  onInfo: "#FFFFFF",
  border: "#E0E0E0",
  borderStrong: "#CCCCCC",
  divider: "#EEEEEE",
  muted: "#757575",
  overlay: "rgba(0,0,0,0.4)",
  pro: "#D4AF37",
  onPro: "#1A1A1A",
  headerDeep: "#1B4332",
  onHeaderDeep: "#B7E4C7",
};

export type ThemeColors = typeof light;

const dark: ThemeColors = {
  surface: "#121212",
  onSurface: "#E0E0E0",
  surfaceSecondary: "#1E1E1E",
  onSurfaceSecondary: "#CCCCCC",
  surfaceTertiary: "#2A2A2A",
  onSurfaceTertiary: "#B3B3B3",
  surfaceInverse: "#E0E0E0",
  onSurfaceInverse: "#121212",
  brand: "#40916C",
  onBrand: "#FFFFFF",
  brandPrimary: "#52B788",
  onBrandPrimary: "#121212",
  brandSecondary: "#74C69D",
  onBrandSecondary: "#121212",
  brandTertiary: "#1B4332",
  onBrandTertiary: "#D8F3E6",
  accent: "#52B788",
  onAccent: "#121212",
  accentSoft: "#1B4332",
  onAccentSoft: "#D8F3E6",
  success: "#38B000",
  onSuccess: "#FFFFFF",
  warning: "#FFB703",
  onWarning: "#121212",
  error: "#FF4D4D",
  onError: "#FFFFFF",
  info: "#8D99AE",
  onInfo: "#121212",
  border: "#333333",
  borderStrong: "#444444",
  divider: "#222222",
  muted: "#888888",
  overlay: "rgba(0,0,0,0.7)",
  pro: "#F3E5AB",
  onPro: "#121212",
  headerDeep: "#1B4332",
  onHeaderDeep: "#B7E4C7",
};

export const defaultScheme = "light" satisfies ColorScheme;

export const themes: { light: ThemeColors; dark?: ThemeColors } = { light, dark };

// User preference: "system" follows the device; persisted across launches.
export type ThemePref = "system" | "light" | "dark";
export const THEME_PREF_KEY = "theme_pref";

// ---------------------------------------------------------------------------
// Reactive theme store.
//
// We do NOT drive the UI from React Native's `useColorScheme()` /
// `Appearance.setColorScheme()`, because react-native-web does not implement
// `setColorScheme`, so an in-app toggle never propagated there (and even on
// native the override was not guaranteed to re-render instantly). Instead we
// keep the preference in a tiny external store and subscribe every `useTheme()`
// consumer with `useSyncExternalStore`, so flipping the theme updates the whole
// app in real time on every platform.
// ---------------------------------------------------------------------------

let pref: ThemePref = "system";
const listeners = new Set<() => void>();

function systemScheme(): ColorScheme {
  return Appearance.getColorScheme?.() === "dark" && themes.dark ? "dark" : "light";
}

function resolve(): ColorScheme {
  if ((pref === "light" || pref === "dark") && themes[pref]) return pref;
  return systemScheme();
}

let current: ColorScheme = resolve();

function recompute() {
  const next = resolve();
  current = next;
  // Keep native chrome (status bar, pickers, alerts) in step where supported.
  setColorScheme(pref === "system" ? null : next);
  listeners.forEach((l) => l());
}

// When the user is on "system", follow live OS appearance changes.
Appearance.addChangeListener?.(() => {
  if (pref === "system") recompute();
});

export function applyThemePref(p: ThemePref) {
  pref = p;
  storage.setItem(THEME_PREF_KEY, p);
  recompute();
}

export function getThemePref(): ThemePref {
  return pref;
}

// In-app theme override. Call setColorScheme("dark" | "light") or null to follow
// the device. Optional because react-native-web does not implement it; the
// reactive store above is what actually re-themes the app.
export function setColorScheme(scheme: ColorScheme | null) {
  // RN 0.86 re-reads the device scheme only for the literal "unspecified";
  // null would pin useColorScheme() to null and the app to light.
  Appearance.setColorScheme?.(scheme ?? "unspecified");
}

// Restore the saved preference on launch (then notify consumers).
storage.getItem<ThemePref>(THEME_PREF_KEY, "system").then((p) => {
  if (p && p !== pref) applyThemePref(p);
});

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}
function getSnapshot(): ColorScheme {
  return current;
}

export function useTheme(): { scheme: ColorScheme; colors: ThemeColors } {
  const scheme = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  return { scheme, colors: themes[scheme] ?? themes.light };
}

// Subscribe to the current preference (for the appearance picker UI).
export function useThemePref(): ThemePref {
  return useSyncExternalStore(subscribe, getThemePref, getThemePref);
}

// Themed StyleSheet: returns a hook that builds the sheet from the active
// scheme's colors and memoizes it until the scheme changes.
export function makeStyles<T extends StyleSheet.NamedStyles<T> | StyleSheet.NamedStyles<any>>(
  factory: (colors: ThemeColors) => T & StyleSheet.NamedStyles<any>,
): () => T {
  return function useStyles(): T {
    const { colors } = useTheme();
    return useMemo(() => StyleSheet.create(factory(colors)), [colors]);
  };
}



export const fonts = { regular: "Cairo", semibold: "Cairo-SemiBold", bold: "Cairo-Bold" };
export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 };
export const radius = { sm: 6, md: 12, lg: 20, xl: 28, pill: 999 };
