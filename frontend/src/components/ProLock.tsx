import { useRouter } from "expo-router";
import React from "react";
import { View } from "react-native";

import { usePro } from "@/src/pro";
import { radius, spacing, useTheme } from "@/src/theme";
import { Btn, Card, Ionicons, T } from "@/src/ui";

// Renders children for Pro orgs; otherwise a locked card that leads to the plans page.
export function ProLock({ feature, children, testID }: { feature: string; children: React.ReactNode; testID: string }) {
  const { pro, isOwner } = usePro();
  const { colors } = useTheme();
  const router = useRouter();
  if (pro) return <>{children}</>;
  return (
    <Card testID={testID} style={{ gap: spacing.md, borderColor: colors.pro, borderWidth: 1.5 }}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
        <View style={{ width: 40, height: 40, borderRadius: radius.pill, backgroundColor: colors.pro, alignItems: "center", justifyContent: "center" }}>
          <Ionicons name="lock-closed" size={20} color={colors.onPro} />
        </View>
        <View style={{ flex: 1 }}>
          <T v="label">{feature}</T>
          <T v="caption">هذه الميزة متاحة في خطة Pro فقط</T>
        </View>
      </View>
      {isOwner ? (
        <Btn testID={`${testID}-upgrade`} small title="فتح الميزة بالترقية إلى Pro" icon="diamond-outline" onPress={() => router.push("/upgrade")} />
      ) : (
        <T v="caption">اطلب من مالك المؤسسة الترقية إلى Pro.</T>
      )}
    </Card>
  );
}
