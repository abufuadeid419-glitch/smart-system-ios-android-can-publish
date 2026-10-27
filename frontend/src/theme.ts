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
  surface: "#F3F5FA",
  onSurface: "#18181B",
  surfaceSecondary: "#FFFFFF",
  onSurfaceSecondary: "#3F3F46",
  surfaceTertiary: "#F4F4F5",
  onSurfaceTertiary: "#27272A",
  surfaceInverse: "#18181B",
  onSurfaceInverse: "#F3F5FA",
  brand: "#1F2A4D",
  brandPrimary: "#1F2A4D",
  onBrandPrimary: "#FFFFFF",
  brandSecondary: "#C9D2EC",
  onBrandSecondary: "#0F1631",
  brandTertiary: "#E8ECF7",
  onBrandTertiary: "#1F2A4D",
  // Coral accent used for primary CTAs / FABs (see reference image).
  accent: "#F2545B",
  onAccent: "#FFFFFF",
  accentSoft: "#FDE6E7",
  onAccentSoft: "#B23A41",
  success: "#2E7D32",
  onSuccess: "#FFFFFF",
  warning: "#C25700",
  onWarning: "#FFFFFF",
  error: "#D32F2F",
  onError: "#FFFFFF",
  info: "#455A64",
  onInfo: "#FFFFFF",
  border: "#E4E4E7",
  borderStrong: "#D4D4D8",
  divider: "#EEF1F7",
  muted: "#71717A",
  onBrand: "#FFFFFF",
  overlay: "rgba(0,0,0,0.4)",
  pro: "#F2545B",
  onPro: "#FFFFFF",
  // Deep-navy strip used inside the dark header (unselected tab background etc).
  headerDeep: "#141B36",
  onHeaderDeep: "#B8C1DE",
};

export type ThemeColors = typeof light;

const dark: ThemeColors = {
  surface: "#0E1324",
  onSurface: "#EEF1F8",
  surfaceSecondary: "#171E35",
  onSurfaceSecondary: "#C4CBDE",
  surfaceTertiary: "#212A47",
  onSurfaceTertiary: "#DCE2F0",
  surfaceInverse: "#EEF1F8",
  onSurfaceInverse: "#111522",
  brand: "#4F5FB0",
  brandPrimary: "#4F5FB0",
  onBrandPrimary: "#FFFFFF",
  brandSecondary: "#2A3566",
  onBrandSecondary: "#DCE3F6",
  brandTertiary: "#222B4E",
  onBrandTertiary: "#AEBAE6",
  // Coral accent used for primary CTAs / FABs (see reference image).
  accent: "#FF6B72",
  onAccent: "#FFFFFF",
  accentSoft: "#3A2026",
  onAccentSoft: "#FF9FA4",
  success: "#4CAF86",
  onSuccess: "#06130D",
  warning: "#E0A24A",
  onWarning: "#1A1206",
  error: "#E5737B",
  onError: "#1A0608",
  info: "#7E8CA8",
  onInfo: "#0B0F1A",
  border: "#2A3350",
  borderStrong: "#3A4568",
  divider: "#222A42",
  muted: "#8B93AD",
  onBrand: "#FFFFFF",
  overlay: "rgba(0,0,0,0.6)",
  pro: "#FF6B72",
  onPro: "#FFFFFF",
  // Deep strip inside the indigo header (unselected tab track etc).
  headerDeep: "#3A4584",
  onHeaderDeep: "#C3CBE8",
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
