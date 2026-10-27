import { useEffect, useState } from "react";
import { Pressable, View } from "react-native";

import { convex } from "@/src/convex";
import { useSyncState } from "@/src/offline";
import { radius, spacing, useTheme } from "@/src/theme";
import { SyncReportSheet } from "@/src/components/SyncReport";
import { T } from "@/src/ui";

// Small live indicator: cloud connection + offline queue state.
// Shown on the dark header as a compact deep-navy pill with status dot.
export function SyncBadge() {
  const { colors } = useTheme();
  const { pending, online, syncing } = useSyncState();
  const [open, setOpen] = useState(false);
  const [cx, setCx] = useState(() => convex.connectionState().isWebSocketConnected);

  useEffect(() => convex.subscribeToConnectionState((s) => setCx(s.isWebSocketConnected)), []);

  const state = !online || !cx ? "offline" : syncing || pending.length ? "syncing" : "synced";
  const color = state === "offline" ? colors.error : state === "syncing" ? colors.warning : colors.success;
  return (
    <>
    <Pressable
      testID="sync-status-badge"
      accessibilityLabel={state}
      onPress={() => setOpen(true)}
      hitSlop={6}
      style={({ pressed }) => ({ opacity: pressed ? 0.7 : 1, width: 36, height: 36, borderRadius: radius.md, backgroundColor: colors.headerDeep, alignItems: "center", justifyContent: "center" })}
    >
      <View testID={`sync-status-${state}`} style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: color }} />
      {state === "syncing" && pending.length > 0 && (
        <View style={{ position: "absolute", top: -4, left: -4, minWidth: 16, height: 16, borderRadius: 8, backgroundColor: colors.warning, alignItems: "center", justifyContent: "center", paddingHorizontal: 3 }}>
          <T v="caption" style={{ color: colors.onWarning, fontSize: 10, lineHeight: 14 }}>{pending.length}</T>
        </View>
      )}
    </Pressable>
    <SyncReportSheet visible={open} onClose={() => setOpen(false)} />
    </>
  );
}
