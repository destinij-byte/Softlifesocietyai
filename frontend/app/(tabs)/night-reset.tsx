import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { NightCheckin } from "@/services/types";
import { spacing } from "@/theme/tokens";

export default function NightReset() {
  const { theme } = useAppTheme();
  const [checkin, setCheckin] = useState<NightCheckin | null>(null);
  const [win, setWin] = useState("");
  const [gratitude, setGratitude] = useState("");
  const [tomorrowFocus, setTomorrowFocus] = useState("");
  const [saving, setSaving] = useState(false);
  const [justSaved, setJustSaved] = useState(false);

  const load = async () => {
    const data = await apiRequest<NightCheckin>("/night-reset/today");
    setCheckin(data);
    setWin(data.win);
    setGratitude(data.gratitude);
    setTomorrowFocus(data.tomorrow_focus);
  };

  useFocusEffect(
    useCallback(() => {
      load();
    }, [])
  );

  const save = async () => {
    setSaving(true);
    try {
      const updated = await apiRequest<NightCheckin>("/night-reset/today", {
        method: "POST",
        body: { win, gratitude, tomorrow_focus: tomorrowFocus },
      });
      setCheckin(updated);
      setJustSaved(true);
    } finally {
      setSaving(false);
    }
  };

  if (!checkin) return null;

  const summary = checkin.day_summary;

  return (
    <Screen>
      <View>
        <Title>Night Reset</Title>
        <Muted>Close out your day, one gentle question at a time.</Muted>
      </View>

      <Card style={{ gap: spacing.sm }}>
        <Subtitle style={{ fontSize: 15 }}>Today, at a glance</Subtitle>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          <Body style={{ color: theme.textMuted }}>Ritual</Body>
          <Body>
            {summary.ritual_done}/{summary.ritual_total} steps
          </Body>
        </View>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          <Body style={{ color: theme.textMuted }}>Nourish</Body>
          <Body>
            {summary.calories_logged}/{summary.calories_goal} cal
          </Body>
        </View>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          <Body style={{ color: theme.textMuted }}>Hydrate</Body>
          <Body>
            {summary.water_count}/{summary.water_goal} glasses
          </Body>
        </View>
        {summary.mood && (
          <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
            <Body style={{ color: theme.textMuted }}>Mood</Body>
            <Body style={{ textTransform: "capitalize" }}>{summary.mood}</Body>
          </View>
        )}
      </Card>

      <View style={{ gap: spacing.md }}>
        <View style={{ gap: spacing.xs }}>
          <Muted>One win from today</Muted>
          <TextField placeholder="Small counts — showing up counts." value={win} onChangeText={setWin} multiline style={{ minHeight: 60, textAlignVertical: "top" }} />
        </View>
        <View style={{ gap: spacing.xs }}>
          <Muted>Something you're grateful for</Muted>
          <TextField placeholder="Anything, big or tiny." value={gratitude} onChangeText={setGratitude} multiline style={{ minHeight: 60, textAlignVertical: "top" }} />
        </View>
        <View style={{ gap: spacing.xs }}>
          <Muted>Tomorrow's one focus</Muted>
          <TextField placeholder="What matters most tomorrow?" value={tomorrowFocus} onChangeText={setTomorrowFocus} multiline style={{ minHeight: 60, textAlignVertical: "top" }} />
        </View>
      </View>

      {justSaved && checkin.completed ? (
        <Card style={{ alignItems: "center", gap: spacing.xs }}>
          <Body style={{ color: theme.primary, fontWeight: "600" }}>✓ Tonight's reset is saved</Body>
          <Muted style={{ textAlign: "center" }}>Rest well — Home will remember your focus for tomorrow.</Muted>
          <Button label="Back to Home" variant="secondary" onPress={() => router.push("/(tabs)/home")} />
        </Card>
      ) : (
        <Button label={checkin.completed ? "Update tonight's reset" : "Save my reset"} onPress={save} loading={saving} />
      )}
    </Screen>
  );
}
