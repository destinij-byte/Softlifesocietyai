import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { ProgressRing } from "@/components/ProgressRing";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { Alignment } from "@/services/types";
import { spacing } from "@/theme/tokens";

export default function Progress() {
  const { theme } = useAppTheme();
  const [alignment, setAlignment] = useState<Alignment | null>(null);

  useFocusEffect(
    useCallback(() => {
      apiRequest<Alignment>("/progress/alignment").then(setAlignment);
    }, [])
  );

  if (!alignment) return null;

  return (
    <Screen>
      <View>
        <Title>Progress</Title>
        <Muted>How this week lines up with what matters most to you right now.</Muted>
      </View>

      <Card style={{ alignItems: "center", gap: spacing.sm, paddingVertical: spacing.lg }}>
        <ProgressRing progress={alignment.score} size={140} strokeWidth={12}>
          <Subtitle style={{ fontSize: 30 }}>{Math.round(alignment.score * 100)}%</Subtitle>
          <Muted style={{ fontSize: 11 }}>Alignment</Muted>
        </ProgressRing>
        <Body style={{ textAlign: "center", color: theme.textMuted, maxWidth: 280 }}>{alignment.why}</Body>
      </Card>

      <Muted style={{ textAlign: "center" }} onPress={() => router.push("/(tabs)/weekly-reset")}>
        See your full Weekly Reset ›
      </Muted>

      {alignment.pillar_scores.length > 0 && (
        <View style={{ gap: spacing.sm }}>
          <Subtitle style={{ fontSize: 15 }}>By pillar</Subtitle>
          {alignment.pillar_scores.map((p) => (
            <Card key={p.pillar} style={{ gap: spacing.xs }}>
              <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                <Body>{p.label}</Body>
                <Muted>{Math.round(p.score * 100)}%</Muted>
              </View>
              <View style={{ height: 6, borderRadius: 3, backgroundColor: theme.surfaceAlt, overflow: "hidden" }}>
                <View style={{ height: 6, borderRadius: 3, width: `${Math.round(p.score * 100)}%`, backgroundColor: theme.primary }} />
              </View>
            </Card>
          ))}
        </View>
      )}
    </Screen>
  );
}
