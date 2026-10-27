import { QueryClientProvider } from "@tanstack/react-query";
import { ConvexProvider } from "convex/react";
import { useFonts } from "expo-font";
import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useEffect } from "react";
import { ActivityIndicator, I18nManager, LogBox, Platform, View } from "react-native";
import { KeyboardProvider } from "react-native-keyboard-controller";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import { homeFor, useAuth, AuthProvider } from "@/src/auth";
import { ErrorBoundary } from "@/src/components/error-boundary";
import { convex } from "@/src/convex";
import { queryClient } from "@/src/query-client";
import { useTheme } from "@/src/theme";
import { ToastProvider } from "@/src/ui";
import { UpdateGate } from "@/src/components/UpdateGate";
import { BtPrintHost } from "@/src/components/BtPrintHost";

// Disable logbox errors etc so that users can see the app
// and agent works as expected.
LogBox.ignoreAllLogs(true);

// Arabic-only app: lock RTL.
if (Platform.OS === "web") {
  if (typeof document !== "undefined") {
    document.documentElement.setAttribute("dir", "rtl");
    document.documentElement.setAttribute("lang", "ar");
  }
} else {
  I18nManager.allowRTL(true);
  I18nManager.forceRTL(true);
}

function Gate() {
  const { user } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  const { colors } = useTheme();

  useEffect(() => {
    if (user === undefined) return;
    const target = homeFor(user);
    const seg = segments[0] as string | undefined;
    // Shared stack screens reachable from inside the app.
    const allowed =
      (seg === "reports" && ["owner", "acct"].includes(target)) ||
      (seg === "journal" && ["owner", "acct"].includes(target)) ||
      (seg === "upgrade" && user?.role === "OWNER") ||
      seg === "legal" ||
      seg === "goodbye" ||
      false ||
      (seg === "agents-map" && target === "owner");
    if (seg !== target && !allowed) router.replace(`/${target}` as any);
  }, [user, segments, router]);

  if (user === undefined) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: colors.brandPrimary }}>
        <ActivityIndicator color={colors.onBrandPrimary} size="large" />
      </View>
    );
  }
  return <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.surface } }} />;
}

export default function RootLayout() {
  const [loaded] = useFonts({
    Cairo: require("../assets/fonts/Cairo-Regular.ttf"),
    "Cairo-SemiBold": require("../assets/fonts/Cairo-SemiBold.ttf"),
    "Cairo-Bold": require("../assets/fonts/Cairo-Bold.ttf"),
  });
  if (!loaded) return null;
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
    <ErrorBoundary>
      <ConvexProvider client={convex}>
        <QueryClientProvider client={queryClient}>
          <KeyboardProvider>
            <AuthProvider>
              <ToastProvider>
                <StatusBar style="light" />
                <UpdateGate>
                  <Gate />
                </UpdateGate>
                <BtPrintHost />
              </ToastProvider>
            </AuthProvider>
          </KeyboardProvider>
        </QueryClientProvider>
      </ConvexProvider>
    </ErrorBoundary>
    </GestureHandlerRootView>
  );
}
