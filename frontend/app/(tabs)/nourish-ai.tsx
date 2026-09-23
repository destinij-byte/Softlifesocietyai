import React, { useCallback, useState } from "react";
import { View } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { AsyncState } from "@/components/AsyncState";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { ProgressBar } from "@/components/ProgressBar";
import { ProgressRing } from "@/components/ProgressRing";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest, apiUpload, ApiError } from "@/services/api";
import { DailySummary, FoodResult, MealSuggestion, WaterState } from "@/services/types";
import { spacing } from "@/theme/tokens";

const MEAL_EMOJI: Record<string, string> = { breakfast: "🥐", lunch: "🥗", dinner: "🍽️", snack: "🍓" };
const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"] as const;

type AddMode = "none" | "photo" | "search" | "manual";

export default function NourishAI() {
  const { theme } = useAppTheme();
  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [water, setWater] = useState<WaterState | null>(null);
  const [waterBusy, setWaterBusy] = useState(false);
  const [addMode, setAddMode] = useState<AddMode>("none");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<FoodResult[]>([]);

  const [manualName, setManualName] = useState("");
  const [manualCalories, setManualCalories] = useState("");

  const [photoSuggestion, setPhotoSuggestion] = useState<MealSuggestion | null>(null);
  const [builderSuggestion, setBuilderSuggestion] = useState<MealSuggestion | null>(null);

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const load = async () => {
    try {
      const [data, waterData] = await Promise.all([
        apiRequest<DailySummary>("/nourish/today"),
        apiRequest<WaterState>("/nourish/water"),
      ]);
      setSummary(data);
      setWater(waterData);
      setLoadError(null);
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : "Couldn't load Nourish AI.");
    } finally {
      setLoading(false);
    }
  };

  const addWater = async () => {
    setWaterBusy(true);
    try {
      setWater(await apiRequest<WaterState>("/nourish/water/add", { method: "POST" }));
    } finally {
      setWaterBusy(false);
    }
  };

  const removeWater = async () => {
    setWaterBusy(true);
    try {
      setWater(await apiRequest<WaterState>("/nourish/water/remove", { method: "POST" }));
    } finally {
      setWaterBusy(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      load();
    }, [])
  );

  const closeAddMode = () => {
    setAddMode("none");
    setError(null);
    setSearchResults([]);
    setSearchQuery("");
    setManualName("");
    setManualCalories("");
    setPhotoSuggestion(null);
  };

  const logFood = async (food: FoodResult, mealType: string = "snack") => {
    setBusy(true);
    try {
      await apiRequest("/nourish/entries", {
        method: "POST",
        body: { ...food, meal_type: mealType },
      });
      closeAddMode();
      await load();
    } finally {
      setBusy(false);
    }
  };

  const runSearch = async (q: string) => {
    setSearchQuery(q);
    if (!q.trim()) {
      setSearchResults([]);
      return;
    }
    const results = await apiRequest<FoodResult[]>(`/nourish/search?q=${encodeURIComponent(q)}`);
    setSearchResults(results);
  };

  const addManual = async () => {
    if (!manualName.trim() || !manualCalories) return;
    await logFood({ name: manualName.trim(), calories: Number(manualCalories), protein_g: 0, carbs_g: 0, fat_g: 0, emoji: "🍽️" });
  };

  const pickPhoto = async () => {
    setError(null);
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setError("Photo library access is needed to analyze a meal.");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({ quality: 0.6 });
    if (result.canceled || !result.assets?.[0]) return;

    setBusy(true);
    try {
      const suggestion = await apiUpload<MealSuggestion>("/nourish/analyze-meal", result.assets[0].uri);
      setPhotoSuggestion(suggestion);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't analyze that photo");
    } finally {
      setBusy(false);
    }
  };

  const buildMeal = async (mealType: string) => {
    setBusy(true);
    try {
      const suggestion = await apiRequest<MealSuggestion>(`/nourish/meal-builder?meal_type=${mealType}`, { method: "POST" });
      setBuilderSuggestion(suggestion);
    } finally {
      setBusy(false);
    }
  };

  const remaining = summary ? summary.goal_calories - summary.total_calories : 0;
  const grouped = summary ? MEAL_TYPES.map((type) => ({ type, entries: summary.entries.filter((e) => e.meal_type === type) })) : [];

  return (
    <Screen>
      <Title>Nourish AI</Title>

      <AsyncState loading={loading} error={loadError} onRetry={load}>
      {summary && (
      <>
      <Card style={{ alignItems: "center", gap: spacing.sm }}>
        <ProgressRing progress={summary.total_calories / summary.goal_calories} size={160}>
          <Subtitle style={{ fontSize: 26 }}>{summary.total_calories}</Subtitle>
          <Muted>of {summary.goal_calories}</Muted>
        </ProgressRing>

        <View style={{ width: "100%", gap: spacing.sm, marginTop: spacing.sm }}>
          <MacroRow label="🥩 Protein" value={summary.total_protein_g} goal={summary.goal_protein_g} unit="g" />
          <MacroRow label="🍚 Carbs" value={summary.total_carbs_g} goal={summary.goal_carbs_g} unit="g" />
          <MacroRow label="🥑 Fat" value={summary.total_fat_g} goal={summary.goal_fat_g} unit="g" />
        </View>
      </Card>

      {water && (
        <Card style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
          <View>
            <Subtitle style={{ fontSize: 15 }}>💧 Water</Subtitle>
            <Muted>
              {water.count} / {water.goal} glasses
            </Muted>
          </View>
          <View style={{ flexDirection: "row", gap: spacing.sm }}>
            <Button label="−" variant="secondary" onPress={removeWater} loading={waterBusy} disabled={water.count === 0} />
            <Button label="+" onPress={addWater} loading={waterBusy} />
          </View>
        </Card>
      )}

      <Card accent style={{ gap: spacing.xs }}>
        <Subtitle>What should I eat? 💛</Subtitle>
        <Body style={{ color: theme.textMuted }}>
          You have {Math.max(remaining, 0)} calories left. Let Luna build your next meal.
        </Body>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          {MEAL_TYPES.map((type) => (
            <Button key={type} label={type} variant="secondary" onPress={() => buildMeal(type)} loading={busy} />
          ))}
        </View>
        {builderSuggestion && (
          <Card style={{ marginTop: spacing.sm }}>
            <Subtitle>
              {builderSuggestion.emoji} {builderSuggestion.name}
            </Subtitle>
            <Muted>
              {builderSuggestion.calories} cal · {builderSuggestion.protein_g}g protein
            </Muted>
            {builderSuggestion.description && <Body style={{ marginTop: spacing.xs }}>{builderSuggestion.description}</Body>}
            <View style={{ marginTop: spacing.sm }}>
              <Button label="Add to log" emoji="➕" onPress={() => logFood(builderSuggestion)} loading={busy} />
            </View>
          </Card>
        )}
      </Card>

      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
        <Button label="Analyze Meal" emoji="📸" variant={addMode === "photo" ? "primary" : "secondary"} onPress={() => (addMode === "photo" ? closeAddMode() : setAddMode("photo"))} />
        <Button label="Search Food" emoji="🔎" variant={addMode === "search" ? "primary" : "secondary"} onPress={() => (addMode === "search" ? closeAddMode() : setAddMode("search"))} />
        <Button label="Manual Entry" emoji="✍🏽" variant={addMode === "manual" ? "primary" : "secondary"} onPress={() => (addMode === "manual" ? closeAddMode() : setAddMode("manual"))} />
      </View>

      {error && <Body style={{ color: theme.danger }}>⚠️ {error}</Body>}

      {addMode === "photo" && (
        <Card style={{ gap: spacing.sm }}>
          <Button label="Choose photo" emoji="📷" onPress={pickPhoto} loading={busy} />
          {photoSuggestion && (
            <>
              <Subtitle>
                {photoSuggestion.emoji} {photoSuggestion.name}
              </Subtitle>
              <Muted>
                {photoSuggestion.calories} cal · P {photoSuggestion.protein_g}g · C {photoSuggestion.carbs_g}g · F {photoSuggestion.fat_g}g
              </Muted>
              {photoSuggestion.note && <Muted>{photoSuggestion.note}</Muted>}
              <Button label="Looks right, add it" emoji="✅" onPress={() => logFood(photoSuggestion)} loading={busy} />
            </>
          )}
        </Card>
      )}

      {addMode === "search" && (
        <Card style={{ gap: spacing.sm }}>
          <TextField placeholder="Search foods..." value={searchQuery} onChangeText={runSearch} />
          {searchResults.map((food) => (
            <View key={food.name} style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
              <Body>
                {food.emoji} {food.name}
              </Body>
              <Button label={`${food.calories} cal`} variant="secondary" onPress={() => logFood(food)} loading={busy} />
            </View>
          ))}
        </Card>
      )}

      {addMode === "manual" && (
        <Card style={{ gap: spacing.sm }}>
          <TextField placeholder="What did you eat?" value={manualName} onChangeText={setManualName} />
          <TextField placeholder="Calories" value={manualCalories} onChangeText={setManualCalories} keyboardType="number-pad" />
          <Button label="Add" emoji="➕" onPress={addManual} loading={busy} disabled={!manualName || !manualCalories} />
        </Card>
      )}

      {grouped.map(
        ({ type, entries }) =>
          entries.length > 0 && (
            <View key={type} style={{ gap: spacing.sm }}>
              <Muted style={{ textTransform: "capitalize" }}>
                {MEAL_EMOJI[type]} {type}
              </Muted>
              {entries.map((entry) => (
                <Card key={entry.id} style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                  <Body>
                    {entry.emoji} {entry.name}
                  </Body>
                  <Muted>{entry.calories} cal</Muted>
                </Card>
              ))}
            </View>
          )
      )}
      </>
      )}
      </AsyncState>
    </Screen>
  );
}

function MacroRow({ label, value, goal, unit }: { label: string; value: number; goal: number; unit: string }) {
  const over = goal > 0 && value > goal;
  return (
    <View style={{ gap: 4 }}>
      <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
        <Muted>{label}</Muted>
        <Muted>
          {Math.round(value)}
          {unit} / {Math.round(goal)}
          {unit}
        </Muted>
      </View>
      <ProgressBar progress={goal > 0 ? value / goal : 0} danger={over} />
    </View>
  );
}
