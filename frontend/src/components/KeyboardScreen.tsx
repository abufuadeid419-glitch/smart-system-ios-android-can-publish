import { BottomTabBarHeightContext } from "expo-router/build/react-navigation/bottom-tabs";
import React, { useContext, useState } from "react";
import { StyleProp, View, ViewStyle } from "react-native";
import { KeyboardAwareScrollView, KeyboardStickyView } from "react-native-keyboard-controller";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { usesNativeTabs } from "@/src/navigation";
import { spacing, useTheme } from "@/src/theme";

type Props = {
  children: React.ReactNode;
  /** Fixed, non-scrolling content above the form (headers, heroes). */
  header?: React.ReactNode;
  /** Primary actions / error text that must stay visible right above the keyboard. */
  footer?: React.ReactNode;
  /** Space below the footer when the keyboard is closed (defaults to the bottom safe-area inset). */
  bottomInset?: number;
  /** Gap kept between the focused input and the keyboard / sticky footer. */
  gap?: number;
  contentContainerStyle?: StyleProp<ViewStyle>;
  backgroundColor?: string;
  testID?: string;
};

// One keyboard strategy for every form screen:
// - the form scrolls (KeyboardAwareScrollView) and auto-scrolls the focused input into view,
// - the footer (CTA + error) rides on top of the keyboard (KeyboardStickyView) instead of being hidden,
// - nothing is resized/squished: the layout keeps its shape and only translates.
export function KeyboardScreen({ children, header, footer, bottomInset, gap = spacing.lg, contentContainerStyle, backgroundColor, testID }: Props) {
  const { colors } = useTheme();
  const insets = useSafeAreaInsets();
  const tabBar = useContext(BottomTabBarHeightContext) as number | undefined;
  const [footerH, setFooterH] = useState(0);
  const pad = bottomInset ?? insets.bottom;
  // When open, the footer must rise by (keyboard − what already sits below it): its own bottom pad
  // plus a JS tab bar (NativeTabs already include the bar in the inset).
  const below = pad + (usesNativeTabs ? 0 : tabBar ?? 0);
  const bg = backgroundColor ?? colors.surface;

  return (
    <View style={{ flex: 1, backgroundColor: bg }} testID={testID}>
      {header}
      <KeyboardAwareScrollView
        style={{ flex: 1 }}
        bottomOffset={(footer ? footerH : 0) + gap}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[{ flexGrow: 1, paddingBottom: footer ? spacing.lg : pad + spacing.lg }, contentContainerStyle]}
      >
        {children}
      </KeyboardAwareScrollView>
      {footer && (
        <KeyboardStickyView offset={{ closed: 0, opened: below }}>
          <View
            testID={testID ? `${testID}-footer` : undefined}
            onLayout={(e) => setFooterH(e.nativeEvent.layout.height)}
            style={{ paddingHorizontal: spacing.xl, paddingTop: spacing.md, paddingBottom: pad + spacing.md, gap: spacing.sm, backgroundColor: bg, borderTopWidth: 1, borderTopColor: colors.divider }}
          >
            {footer}
          </View>
        </KeyboardStickyView>
      )}
    </View>
  );
}
