import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { StaggerIn } from "@/components/StaggerIn";
import { useAuth } from "@/context/AuthContext";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { DailySummary, LeaderboardRow, MealSuggestion, MyChallenge, Routine } from "@/services/types";
import { spacing } from "@/theme/tokens";

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export default function Home() {
  const { user } = useAuth();
  const { theme } = useAppTheme();
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [focusSteps, setFocusSteps] = useState<{ id: string; label: string; routineType: "morning" | "night" }[]>([]);
  const [habitsDone, setHabitsDone] = useState(0);
  const [habitsTotal, setHabitsTotal] = useState(0);
  const [myChallenges, setMyChallenges] = useState<MyChallenge[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardRow[]>([]);
  const [suggestion, setSuggestion] = useState<MealSuggestion | null>(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    const [nourish, morning, night, challenges, board] = await Promise.all([
      apiRequest<DailySummary>("/nourish/today"),
      apiRequest<Routine>("/routines/morning"),
      apiRequest<Routine>("/routines/night"),
      apiRequest<MyChallenge[]>("/challenges/mine"),
      apiRequest<LeaderboardRow[]>("/challenges/leaderboard"),
    ]);

    setSummary(nourish);

    const allSteps = [
      ...morning.steps.map((s) => ({ ...s, routineType: "morning" as const })),
      ...night.steps.map((s) => ({ ...s, routineType: "night" as const })),
    ];
    setHabitsTotal(allSteps.length);
    setHabitsDone(allSteps.filter((s) => s.done).length);
    setFocusSteps(allSteps.filter((s) => !s.done).slice(0, 3));

    setMyChallenges(challenges);
    setLeaderboard(board);
  };

  useFocusEffect(
    useCallback(() => {
      load();
    }, [])
  );

  const toggleFocusStep = async (step: { id: string; routineType: "morning" | "night" }) => {
    await apiRequest(`/routines/${step.routineType}/steps/${step.id}/toggle`, { method: "PUT" });
    await load();
  };

  const buildDinner = async () => {
    setBusy(true);
    try {
      const result = await apiRequest<MealSuggestion>("/nourish/meal-builder?meal_type=dinner", { method: "POST" });
      setSuggestion(result);
    } finally {
      setBusy(false);
    }
  };

  if (!summary || !user) return null;

  const remaining = Math.max(summary.goal_calories - summary.total_calories, 0);
  const proteinLeft = Math.max(summary.goal_protein_g - summary.total_protein_g, 0);
  const bestChallenge = myChallenges.sort((a, b) => b.streak - a.streak)[0];
  const waterChallenge = myChallenges.find((c) => c.slug === "water-intake");

  return (
    <Screen>
      <StaggerIn index={0}>
        <Title>
          {greeting()}, {user.name.split(" ")[0]} ✨
        </Title>
      </StaggerIn>

      <StaggerIn index={1}>
        <Card style={{ gap: spacing.sm }}>
          <Subtitle>Today's Focus 🌸</Subtitle>
          {focusSteps.length === 0 && <Muted>You've cleared your routines today — beautiful work.</Muted>}
          {focusSteps.map((step) => (
            <Body key={step.id} onPress={() => toggleFocusStep(step)}>
              ⬜️ {step.label}
            </Body>
          ))}
        </Card>
      </StaggerIn>

      <StaggerIn index={2}>
        <View style={{ flexDirection: "row", gap: spacing.sm }}>
          <StatTile label="Calories left" value={`${remaining}`} theme={theme} />
          <StatTile label="Habits" value={`${habitsDone}/${habitsTotal}`} theme={theme} />
          <StatTile label="Water" value={waterChallenge ? (waterChallenge.logged_today ? "✅" : "💧") : "—"} theme={theme} />
        </View>
      </StaggerIn>

      <StaggerIn index={3}>
        <Card accent style={{ gap: spacing.xs }}>
          <Subtitle>Luna's suggestion 💛</Subtitle>
          <Body style={{ color: theme.textMuted }}>
            You have {remaining} calories left{proteinLeft > 20 ? " and still need protein" : ""}. Want me to build your dinner?
          </Body>
          {suggestion ? (
            <Card style={{ marginTop: spacing.xs }}>
              <Subtitle>
                {suggestion.emoji} {suggestion.name}
              </Subtitle>
              <Muted>
                {suggestion.calories} cal · {suggestion.protein_g}g protein
              </Muted>
              <View style={{ marginTop: spacing.sm }}>
                <Button label="Open in Nourish AI" variant="secondary" onPress={() => router.push("/(tabs)/nourish-ai")} />
              </View>
            </Card>
          ) : (
            <View style={{ marginTop: spacing.xs }}>
              <Button label="Build My Dinner" emoji="🍽️" onPress={buildDinner} loading={busy} />
            </View>
          )}
        </Card>
      </StaggerIn>

      <StaggerIn index={4}>
        <Card style={{ gap: spacing.xs }}>
          <Subtitle>Challenges 🏆</Subtitle>
          {bestChallenge ? (
            <Body style={{ color: theme.textMuted }}>
              🔥 {bestChallenge.streak} day streak on {bestChallenge.title}
              {leaderboard.length > 1 ? ` · #${leaderboard.find((r) => r.is_you)?.rank ?? "-"} on the leaderboard` : ""}
            </Body>
          ) : (
            <Body style={{ color: theme.textMuted }}>Join a challenge to start your streak 🌷</Body>
          )}
          <View style={{ marginTop: spacing.xs }}>
            <Button label="View Challenges" variant="secondary" onPress={() => router.push("/(tabs)/challenges")} />
          </View>
        </Card>
      </StaggerIn>
    </Screen>
  );
}

function StatTile({ label, value, theme }: { label: string; value: string; theme: ReturnType<typeof useAppTheme>["theme"] }) {
  return (
    <Card style={{ flex: 1, alignItems: "center", paddingVertical: spacing.md }}>
      <Subtitle style={{ fontSize: 20 }}>{value}</Subtitle>
      <Muted style={{ textAlign: "center" }}>{label}</Muted>
    </Card>
  );
}
