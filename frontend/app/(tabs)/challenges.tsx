import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { Challenge } from "@/services/types";
import { spacing } from "@/theme/tokens";

export default function Challenges() {
  const { theme } = useAppTheme();
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [busySlug, setBusySlug] = useState<string | null>(null);

  const load = async () => {
    const data = await apiRequest<Challenge[]>("/challenges");
    setChallenges(data);
  };

  useFocusEffect(
    useCallback(() => {
      load();
    }, [])
  );

  const join = async (slug: string) => {
    setBusySlug(slug);
    try {
      await apiRequest(`/challenges/${slug}/join`, { method: "POST" });
      await load();
    } finally {
      setBusySlug(null);
    }
  };

  const complete = async (slug: string) => {
    setBusySlug(slug);
    try {
      await apiRequest(`/challenges/${slug}/complete`, { method: "POST" });
      await load();
    } finally {
      setBusySlug(null);
    }
  };

  return (
    <Screen>
      <Title>🏆 Challenges</Title>
      <Muted>Small, soft commitments — done together.</Muted>

      <View style={{ gap: spacing.md }}>
        {challenges.map((c) => (
          <Card key={c.slug} style={{ gap: spacing.xs }}>
            <Subtitle>
              {c.emoji} {c.title}
            </Subtitle>
            <Body style={{ color: theme.textMuted }}>{c.description}</Body>
            <Muted>
              {c.duration_days} days · {c.participant_count} joined
            </Muted>

            {c.completed ? (
              <Body style={{ color: theme.success }}>✅ Completed — you did it!</Body>
            ) : c.joined ? (
              <Button label="Mark complete" emoji="🎉" variant="secondary" onPress={() => complete(c.slug)} loading={busySlug === c.slug} />
            ) : (
              <Button label="Join challenge" emoji="🌷" onPress={() => join(c.slug)} loading={busySlug === c.slug} />
            )}
          </Card>
        ))}
      </View>
    </Screen>
  );
}
