import React, { useCallback, useEffect, useState } from "react";
import { View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { ProgressBar } from "@/components/ProgressBar";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { DailySummary, Workout } from "@/services/types";
import { spacing } from "@/theme/tokens";

const MEAL_EMOJI: Record<string, string> = { breakfast: "🥐", lunch: "🥗", dinner: "🍽️", snack: "🍓" };
const WORKOUT_EMOJI = ["🏋️‍♀️", "🧘‍♀️", "🏃‍♀️", "🚴‍♀️", "🩰", "🥊"];

export default function Track() {
  const { theme } = useAppTheme();
  const [tab, setTab] = useState<"calories" | "workouts">("calories");

  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [foodName, setFoodName] = useState("");
  const [foodCalories, setFoodCalories] = useState("");

  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [streak, setStreak] = useState(0);
  const [workoutName, setWorkoutName] = useState("");
  const [workoutMinutes, setWorkoutMinutes] = useState("");

  const [busy, setBusy] = useState(false);

  const loadCalories = async () => {
    const data = await apiRequest<DailySummary>("/nutrition/today");
    setSummary(data);
  };

  const loadWorkouts = async () => {
    const data = await apiRequest<Workout[]>("/workouts");
    setWorkouts(data);
    const s = await apiRequest<{ streak_days: number }>("/workouts/streak");
    setStreak(s.streak_days);
  };

  useFocusEffect(
    useCallback(() => {
      loadCalories();
      loadWorkouts();
    }, [])
  );

  const addFood = async () => {
    if (!foodName.trim() || !foodCalories) return;
    setBusy(true);
    try {
      await apiRequest("/nutrition/entries", {
        method: "POST",
        body: { name: foodName.trim(), calories: Number(foodCalories), meal_type: "snack", emoji: "🍽️" },
      });
      setFoodName("");
      setFoodCalories("");
      await loadCalories();
    } finally {
      setBusy(false);
    }
  };

  const addWorkout = async () => {
    if (!workoutName.trim() || !workoutMinutes) return;
    setBusy(true);
    try {
      const emoji = WORKOUT_EMOJI[Math.floor(Math.random() * WORKOUT_EMOJI.length)];
      await apiRequest("/workouts", {
        method: "POST",
        body: { name: workoutName.trim(), workout_type: "movement", duration_minutes: Number(workoutMinutes), emoji },
      });
      setWorkoutName("");
      setWorkoutMinutes("");
      await loadWorkouts();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Screen>
      <Title>📊 Your Tracking</Title>

      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <Button label="🍓 Calories" variant={tab === "calories" ? "primary" : "ghost"} onPress={() => setTab("calories")} />
        <Button label="💪 Workouts" variant={tab === "workouts" ? "primary" : "ghost"} onPress={() => setTab("workouts")} />
      </View>

      {tab === "calories" && summary && (
        <>
          <Card>
            <Subtitle>
              {summary.total_calories} / {summary.goal_calories} cal
            </Subtitle>
            <View style={{ marginTop: spacing.sm }}>
              <ProgressBar progress={summary.total_calories / summary.goal_calories} />
            </View>
          </Card>

          <Card style={{ gap: spacing.sm }}>
            <Subtitle>Log a bite 🍓</Subtitle>
            <TextField placeholder="What did you eat?" value={foodName} onChangeText={setFoodName} />
            <TextField placeholder="Calories" value={foodCalories} onChangeText={setFoodCalories} keyboardType="number-pad" />
            <Button label="Add" emoji="➕" onPress={addFood} loading={busy} disabled={!foodName || !foodCalories} />
          </Card>

          <View style={{ gap: spacing.sm }}>
            {summary.entries.map((entry) => (
              <Card key={entry.id} style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                <Body>
                  {MEAL_EMOJI[entry.meal_type] ?? "🍽️"} {entry.name}
                </Body>
                <Muted>{entry.calories} cal</Muted>
              </Card>
            ))}
            {summary.entries.length === 0 && <Muted>Nothing logged yet today 🌿</Muted>}
          </View>
        </>
      )}

      {tab === "workouts" && (
        <>
          <Card>
            <Subtitle>🔥 {streak} day streak</Subtitle>
            <Muted>{workouts.length} workouts logged</Muted>
          </Card>

          <Card style={{ gap: spacing.sm }}>
            <Subtitle>Log a workout 💪</Subtitle>
            <TextField placeholder="What did you do?" value={workoutName} onChangeText={setWorkoutName} />
            <TextField placeholder="Minutes" value={workoutMinutes} onChangeText={setWorkoutMinutes} keyboardType="number-pad" />
            <Button label="Add" emoji="➕" onPress={addWorkout} loading={busy} disabled={!workoutName || !workoutMinutes} />
          </Card>

          <View style={{ gap: spacing.sm }}>
            {workouts.map((w) => (
              <Card key={w.id} style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                <Body>
                  {w.emoji} {w.name}
                </Body>
                <Muted>{w.duration_minutes} min</Muted>
              </Card>
            ))}
            {workouts.length === 0 && <Muted>No workouts yet — let's get moving! 🌟</Muted>}
          </View>
        </>
      )}
    </Screen>
  );
}
