import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { AsyncState } from "@/components/AsyncState";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { ProgressBar } from "@/components/ProgressBar";
import { VisionBoard } from "@/components/VisionBoard";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest, ApiError } from "@/services/api";
import { Goal, GoalTimeframe } from "@/services/types";
import { spacing } from "@/theme/tokens";

const CATEGORIES: { key: Goal["category"]; label: string; emoji: string }[] = [
  { key: "money", label: "Money", emoji: "💰" },
  { key: "wellness", label: "Wellness", emoji: "💪" },
  { key: "career", label: "Career", emoji: "💼" },
  { key: "personal", label: "Personal", emoji: "✨" },
];

const TIMEFRAMES: { key: GoalTimeframe; label: string; emoji: string }[] = [
  { key: "none", label: "No timeframe", emoji: "🎯" },
  { key: "quarterly", label: "Quarterly", emoji: "🗓️" },
  { key: "long_term", label: "Long-term", emoji: "🌠" },
];

export default function Goals() {
  const { theme } = useAppTheme();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [creating, setCreating] = useState(false);
  const [category, setCategory] = useState<Goal["category"]>("personal");
  const [timeframe, setTimeframe] = useState<GoalTimeframe>("none");
  const [title, setTitle] = useState("");
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [milestoneDrafts, setMilestoneDrafts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Mutations (bump progress, add/toggle milestones) already refresh the
  // list in the background via this same load() without disturbing the rest
  // of the screen — so only the *first* load blocks with a spinner; a later
  // failure shows as a small inline banner instead of wiping the list.
  const load = async () => {
    try {
      const data = await apiRequest<Goal[]>("/goals");
      setGoals(data);
      setLoadError(null);
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : "Couldn't refresh your goals.");
    } finally {
      setLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      load();
    }, [])
  );

  const createGoal = async () => {
    if (!title.trim() || !target.trim()) return;
    setBusy(true);
    try {
      const emoji = CATEGORIES.find((c) => c.key === category)?.emoji ?? "🎯";
      await apiRequest("/goals", {
        method: "POST",
        body: { title: title.trim(), category, target: target.trim(), emoji, timeframe },
      });
      setTitle("");
      setTarget("");
      setTimeframe("none");
      setCreating(false);
      await load();
    } finally {
      setBusy(false);
    }
  };

  const updateGoalInState = (updated: Goal) => {
    setGoals((prev) => prev.map((g) => (g.id === updated.id ? updated : g)));
  };

  const bumpProgress = async (goal: Goal, delta: number) => {
    const next = Math.max(0, Math.min(1, goal.progress + delta));
    await apiRequest(`/goals/${goal.id}/progress?progress=${next}`, { method: "PUT" });
    await load();
  };

  const addMilestone = async (goal: Goal) => {
    const draft = milestoneDrafts[goal.id]?.trim();
    if (!draft) return;
    await apiRequest(`/goals/${goal.id}/milestones`, { method: "POST", body: { title: draft } });
    setMilestoneDrafts((prev) => ({ ...prev, [goal.id]: "" }));
    await load();
  };

  const toggleMilestone = async (goal: Goal, milestoneId: string) => {
    await apiRequest(`/goals/${goal.id}/milestones/${milestoneId}/toggle`, { method: "PUT" });
    await load();
  };

  return (
    <Screen>
      <Title>Goals</Title>
      <Muted>Money, Wellness, Career, Personal — broken into small steps.</Muted>

      {loadError && goals.length > 0 && <Muted style={{ color: theme.danger }}>⚠️ {loadError}</Muted>}

      <AsyncState loading={loading && goals.length === 0} error={goals.length === 0 ? loadError : null} onRetry={load}>
      {creating ? (
        <Card style={{ gap: spacing.sm }}>
          <Subtitle>New goal</Subtitle>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
            {CATEGORIES.map((c) => (
              <Button
                key={c.key}
                label={c.label}
                emoji={c.emoji}
                variant={category === c.key ? "primary" : "secondary"}
                onPress={() => setCategory(c.key)}
              />
            ))}
          </View>
          <TextField placeholder="Goal title" value={title} onChangeText={setTitle} />
          <TextField placeholder="Target (e.g. Save $5,000)" value={target} onChangeText={setTarget} />

          <Muted>Timeframe (unlocks a vision board)</Muted>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
            {TIMEFRAMES.map((t) => (
              <Button
                key={t.key}
                label={t.label}
                emoji={t.emoji}
                variant={timeframe === t.key ? "primary" : "secondary"}
                onPress={() => setTimeframe(t.key)}
              />
            ))}
          </View>

          <View style={{ flexDirection: "row", gap: spacing.sm }}>
            <Button label="Create" emoji="✨" onPress={createGoal} loading={busy} disabled={!title || !target} />
            <Button label="Cancel" variant="ghost" onPress={() => setCreating(false)} />
          </View>
        </Card>
      ) : (
        <Button label="New goal" emoji="➕" onPress={() => setCreating(true)} />
      )}

      {CATEGORIES.map((c) => {
        const categoryGoals = goals.filter((g) => g.category === c.key);
        if (categoryGoals.length === 0) return null;
        return (
          <View key={c.key} style={{ gap: spacing.sm }}>
            <Muted>
              {c.emoji} {c.label}
            </Muted>
            {categoryGoals.map((goal) => (
              <Card key={goal.id} style={{ gap: spacing.sm }}>
                <Subtitle>
                  {goal.emoji} {goal.title}
                </Subtitle>
                <Body style={{ color: theme.textMuted }}>{goal.target}</Body>
                {goal.timeframe !== "none" && (
                  <Muted>{TIMEFRAMES.find((t) => t.key === goal.timeframe)?.emoji} {TIMEFRAMES.find((t) => t.key === goal.timeframe)?.label} goal</Muted>
                )}
                <ProgressBar progress={goal.progress} />
                <View style={{ flexDirection: "row", gap: spacing.sm }}>
                  <Button label="-10%" variant="secondary" onPress={() => bumpProgress(goal, -0.1)} />
                  <Button label="+10%" variant="secondary" onPress={() => bumpProgress(goal, 0.1)} />
                </View>

                {goal.milestones.map((m) => (
                  <Body key={m.id} onPress={() => toggleMilestone(goal, m.id)}>
                    {m.done ? "☑️" : "⬜️"} {m.title}
                  </Body>
                ))}
                <View style={{ flexDirection: "row", gap: spacing.sm, alignItems: "center" }}>
                  <View style={{ flex: 1 }}>
                    <TextField
                      placeholder="Add a milestone"
                      value={milestoneDrafts[goal.id] ?? ""}
                      onChangeText={(t) => setMilestoneDrafts((prev) => ({ ...prev, [goal.id]: t }))}
                    />
                  </View>
                  <Button label="Add" variant="secondary" onPress={() => addMilestone(goal)} />
                </View>

                {goal.timeframe !== "none" && <VisionBoard goal={goal} onChange={updateGoalInState} />}
              </Card>
            ))}
          </View>
        );
      })}

      {goals.length === 0 && !creating && <Muted>No goals yet — start with something small 🌷</Muted>}
      </AsyncState>
    </Screen>
  );
}
