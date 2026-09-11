import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { ProgressBar } from "@/components/ProgressBar";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { Goal } from "@/services/types";
import { spacing } from "@/theme/tokens";

const CATEGORIES: { key: Goal["category"]; label: string; emoji: string }[] = [
  { key: "money", label: "Money", emoji: "💰" },
  { key: "wellness", label: "Wellness", emoji: "💪" },
  { key: "career", label: "Career", emoji: "💼" },
  { key: "personal", label: "Personal", emoji: "✨" },
];

export default function Goals() {
  const { theme } = useAppTheme();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [creating, setCreating] = useState(false);
  const [category, setCategory] = useState<Goal["category"]>("personal");
  const [title, setTitle] = useState("");
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [milestoneDrafts, setMilestoneDrafts] = useState<Record<string, string>>({});

  const load = async () => {
    const data = await apiRequest<Goal[]>("/goals");
    setGoals(data);
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
      await apiRequest("/goals", { method: "POST", body: { title: title.trim(), category, target: target.trim(), emoji } });
      setTitle("");
      setTarget("");
      setCreating(false);
      await load();
    } finally {
      setBusy(false);
    }
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
      <Title>🎯 Goals</Title>
      <Muted>Money, Wellness, Career, Personal — broken into small steps.</Muted>

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
              </Card>
            ))}
          </View>
        );
      })}

      {goals.length === 0 && !creating && <Muted>No goals yet — start with something small 🌷</Muted>}
    </Screen>
  );
}
