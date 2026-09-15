import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { WeeklyReset } from "@/services/types";
import { spacing } from "@/theme/tokens";

export default function WeeklyResetScreen() {
  const { theme } = useAppTheme();
  const [data, setData] = useState<WeeklyReset | null>(null);

  useFocusEffect(
    useCallback(() => {
      apiRequest<WeeklyReset>("/weekly-reset/summary").then(setData);
    }, [])
  );

  if (!data) return null;

  return (
    <Screen>
      <View>
        <Title>Weekly Reset</Title>
        <Muted>
          {new Date(data.week_start).toLocaleDateString(undefined, { month: "short", day: "numeric" })} –{" "}
          {new Date(data.week_end).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
        </Muted>
      </View>

      <Card style={{ gap: spacing.sm }}>
        <Subtitle style={{ fontSize: 15 }}>This week's alignment</Subtitle>
        <Body style={{ color: theme.primary, fontSize: 22, fontWeight: "700" }}>{Math.round(data.alignment.score * 100)}%</Body>
        <Muted>{data.alignment.why}</Muted>
      </Card>

      <Card style={{ gap: spacing.sm }}>
        <Subtitle style={{ fontSize: 15 }}>The week, at a glance</Subtitle>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          <Body style={{ color: theme.textMuted }}>Hydrate average</Body>
          <Body>{data.water_avg_pct}%</Body>
        </View>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          <Body style={{ color: theme.textMuted }}>Days you nourished</Body>
          <Body>{data.nourish_days_logged}/7</Body>
        </View>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          <Body style={{ color: theme.textMuted }}>Days you checked in on mood</Body>
          <Body>{data.mood_days_logged}/7</Body>
        </View>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          <Body style={{ color: theme.textMuted }}>Night Resets completed</Body>
          <Body>{data.checkins_completed}/7</Body>
        </View>
        {data.best_day && (
          <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
            <Body style={{ color: theme.textMuted }}>Your best day</Body>
            <Body>{data.best_day}</Body>
          </View>
        )}
      </Card>

      {data.challenges.length > 0 && (
        <View style={{ gap: spacing.sm }}>
          <Subtitle style={{ fontSize: 15 }}>Challenges</Subtitle>
          {data.challenges.map((c) => (
            <Card key={c.slug} style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
              <Body>
                {c.emoji} {c.title}
              </Body>
              <Muted>{c.check_ins_this_week}/7 days</Muted>
            </Card>
          ))}
        </View>
      )}

      {data.goals_overview.length > 0 && (
        <View style={{ gap: spacing.sm }}>
          <Subtitle style={{ fontSize: 15 }}>Goals</Subtitle>
          {data.goals_overview.map((g) => (
            <Card key={g.title} style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
              <Body style={{ flex: 1 }}>{g.title}</Body>
              <Muted>{Math.round(g.progress * 100)}%</Muted>
            </Card>
          ))}
        </View>
      )}
    </Screen>
  );
}
