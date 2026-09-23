import React, { useCallback, useState } from "react";
import { Pressable, View } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { AsyncState } from "@/components/AsyncState";
import { Button } from "@/components/Button";
import { Icon } from "@/components/Icon";
import { TextField } from "@/components/TextField";
import { ProgressRing } from "@/components/ProgressRing";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest, apiUpload, ApiError } from "@/services/api";
import { DailySummary, FoodResult, MealSuggestion, WaterState } from "@/services/types";
import { palette, spacing } from "@/theme/tokens";

const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"] as const;
const WATER_SLOTS = 8;

type AddMode = "none" | "photo" | "search" | "manual";

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function last7Days(): Date[] {
  const today = new Date();
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(today.getDate() - (6 - i));
    return d;
  });
}

function suggestedMealType(): (typeof MEAL_TYPES)[number] {
  const hour = new Date().getHours();
  if (hour < 11) return "breakfast";
  if (hour < 15) return "lunch";
  if (hour < 20) return "dinner";
  return "snack";
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

export default function NourishAI() {
  const { theme } = useAppTheme();
  const todayIso = isoDate(new Date());
  const [selectedDate, setSelectedDate] = useState(todayIso);
  const isToday = selectedDate === todayIso;

  const [summary, setSummary] = useState<DailySummary | null>(null);
  const [water, setWater] = useState<WaterState | null>(null);
  const [waterBusy, setWaterBusy] = useState(false);
  const [addMode, setAddMode] = useState<AddMode>("none");
  const [showAddSheet, setShowAddSheet] = useState(false);
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

  const load = async (dateToLoad: string) => {
    try {
      const data = await apiRequest<DailySummary>(`/nourish/today?log_date=${dateToLoad}`);
      setSummary(data);
      if (dateToLoad === todayIso) {
        setWater(await apiRequest<WaterState>("/nourish/water"));
      }
      setLoadError(null);
    } catch (e) {
      setLoadError(e instanceof ApiError ? e.message : "Couldn't load Nourish.");
    } finally {
      setLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      load(selectedDate);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedDate])
  );

  const selectDate = (d: string) => {
    setSelectedDate(d);
    setLoading(true);
    setShowAddSheet(false);
    closeAddMode();
  };

  const setWaterCount = async (target: number) => {
    if (!water) return;
    const delta = target - water.count;
    if (delta === 0) return;
    setWaterBusy(true);
    try {
      let next = water;
      for (let i = 0; i < Math.abs(delta); i++) {
        next = await apiRequest<WaterState>(`/nourish/water/${delta > 0 ? "add" : "remove"}`, { method: "POST" });
      }
      setWater(next);
    } finally {
      setWaterBusy(false);
    }
  };

  const closeAddMode = () => {
    setAddMode("none");
    setError(null);
    setSearchResults([]);
    setSearchQuery("");
    setManualName("");
    setManualCalories("");
    setPhotoSuggestion(null);
    // The meal-builder card lives outside the addMode-gated sections, so it
    // must be cleared here too — otherwise it stays on screen with the same
    // (possibly edited) values after a successful log, inviting an
    // accidental duplicate entry on a second tap.
    setBuilderSuggestion(null);
  };

  const logFood = async (food: FoodResult, mealType: string = "snack") => {
    setBusy(true);
    try {
      await apiRequest("/nourish/entries", {
        method: "POST",
        body: { ...food, meal_type: mealType },
      });
      closeAddMode();
      setShowAddSheet(false);
      await load(selectedDate);
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
  const nextMealType = suggestedMealType();

  return (
    <Screen
      floating={
        isToday &&
        summary && (
          <Pressable
            accessibilityLabel="Log food"
            onPress={() => setShowAddSheet((v) => !v)}
            style={{
              position: "absolute",
              right: spacing.lg,
              bottom: spacing.lg,
              width: 60,
              height: 60,
              borderRadius: 30,
              borderWidth: 3,
              borderColor: theme.background,
              backgroundColor: theme.tabBarBackground,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Icon name="plus" size={26} color={theme.primary} />
          </Pressable>
        )
      }
    >
      <AsyncState loading={loading} error={loadError} onRetry={() => load(selectedDate)}>
        {summary && (
          <>
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
              <Title>Nourish 🌸</Title>
              <View style={{ backgroundColor: theme.tabBarBackground, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 8 }}>
                <Body style={{ fontSize: 14, fontWeight: "600", color: theme.primary }}>🔥 {summary.streak}</Body>
              </View>
            </View>

            <DayStrip selected={selectedDate} today={todayIso} onSelect={selectDate} />

            <View style={{ backgroundColor: theme.surfaceAlt, borderRadius: 26, padding: 22, flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
              <View style={{ gap: 4, flexShrink: 1 }}>
                <View style={{ flexDirection: "row", alignItems: "baseline", gap: 4 }}>
                  <Subtitle style={{ fontSize: 40 }}>{summary.total_calories}</Subtitle>
                  <Body style={{ fontSize: 16, color: "#5E4F53" }}>/{summary.goal_calories}</Body>
                </View>
                <Body style={{ color: "#463C3E" }}>Calories eaten</Body>
                <Body style={{ fontSize: 12, fontWeight: "600", color: palette.rose }}>
                  {remaining >= 0 ? `${remaining} left today 💕` : `${Math.abs(remaining)} over today`}
                </Body>
              </View>
              <ProgressRing
                progress={summary.goal_calories > 0 ? summary.total_calories / summary.goal_calories : 0}
                size={110}
                strokeWidth={10}
                color={theme.text}
                accessibilityLabel={`Calories, ${summary.total_calories} of ${summary.goal_calories}`}
              >
                <Body style={{ fontSize: 30 }}>🔥</Body>
              </ProgressRing>
            </View>

            <View style={{ flexDirection: "row", gap: 10 }}>
              <MacroCard label="Protein eaten" value={summary.total_protein_g} goal={summary.goal_protein_g} emoji="🍗" color={palette.petal} />
              <MacroCard label="Carbs eaten" value={summary.total_carbs_g} goal={summary.goal_carbs_g} emoji="🌾" color={palette.gold} />
              <MacroCard label="Fat eaten" value={summary.total_fat_g} goal={summary.goal_fat_g} emoji="🥑" color={theme.text} />
            </View>

            {isToday && water && (
              <Card style={{ gap: 12 }}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                  <View>
                    <Subtitle style={{ fontSize: 18 }}>💧 Water</Subtitle>
                    <Muted>
                      {water.count} of {water.goal} glasses
                    </Muted>
                  </View>
                  <Pressable
                    accessibilityLabel="Add a glass of water"
                    onPress={() => setWaterCount(Math.min(water.count + 1, WATER_SLOTS))}
                    disabled={waterBusy}
                    style={{ width: 44, height: 44, borderRadius: 22, backgroundColor: theme.surfaceAlt, alignItems: "center", justifyContent: "center" }}
                  >
                    <Body style={{ fontSize: 22 }}>+</Body>
                  </Pressable>
                </View>
                <View style={{ flexDirection: "row", gap: 6 }}>
                  {Array.from({ length: WATER_SLOTS }, (_, i) => {
                    const filled = i < water.count;
                    return (
                      <Pressable
                        key={i}
                        disabled={waterBusy}
                        onPress={() => setWaterCount(filled && i === water.count - 1 ? i : i + 1)}
                        style={{
                          flex: 1,
                          height: 34,
                          borderRadius: 10,
                          backgroundColor: filled ? theme.surfaceAlt : theme.surface,
                          borderWidth: filled ? 0 : 1.5,
                          borderColor: theme.surfaceAlt,
                          borderStyle: filled ? "solid" : "dashed",
                        }}
                      />
                    );
                  })}
                </View>
              </Card>
            )}

            <Subtitle style={{ fontSize: 22, marginTop: 4 }}>Recently logged</Subtitle>

            {summary.entries.length === 0 && <Muted>{isToday ? "Nothing logged yet today." : "Nothing logged this day."}</Muted>}

            {[...summary.entries]
              .reverse()
              .map((entry) => (
                <Card key={entry.id} style={{ flexDirection: "row", gap: 14, alignItems: "center" }}>
                  <View style={{ width: 64, height: 64, borderRadius: 16, backgroundColor: theme.tileBackground, alignItems: "center", justifyContent: "center" }}>
                    <Body style={{ fontSize: 32 }}>{entry.emoji}</Body>
                  </View>
                  <View style={{ flex: 1, gap: 3 }}>
                    <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                      <Body style={{ fontSize: 15, fontWeight: "600" }}>{entry.name}</Body>
                      <Muted>{formatTime(entry.logged_at)}</Muted>
                    </View>
                    <Body style={{ fontSize: 13, color: "#463C3E" }}>🔥 {entry.calories} cal</Body>
                    <Muted>
                      🍗 {Math.round(entry.protein_g)}g · 🌾 {Math.round(entry.carbs_g)}g · 🥑 {Math.round(entry.fat_g)}g
                    </Muted>
                  </View>
                </Card>
              ))}

            {isToday && (
              <Card style={{ backgroundColor: theme.surfaceAlt, gap: 10, borderWidth: 0 }}>
                <Body style={{ fontSize: 11, letterSpacing: 1.2, textTransform: "uppercase", color: palette.rose, fontWeight: "600" }}>
                  ✨ Luna's {nextMealType} pick
                </Body>
                {builderSuggestion ? (
                  <EstimatedMealCard
                    suggestion={builderSuggestion}
                    onConfirm={(edited) => logFood(edited, nextMealType)}
                    onDiscard={() => setBuilderSuggestion(null)}
                    busy={busy}
                    confirmLabel="Add to today"
                  />
                ) : (
                  <>
                    <Subtitle style={{ fontSize: 20 }}>What should I eat?</Subtitle>
                    <View style={{ flexDirection: "row", gap: 8 }}>
                      <Button label="Suggest a meal" onPress={() => buildMeal(nextMealType)} loading={busy} />
                    </View>
                  </>
                )}
              </Card>
            )}

            {error && <Body style={{ color: theme.danger }}>⚠️ {error}</Body>}

            {isToday && showAddSheet && (
              <Card style={{ gap: spacing.sm }}>
                <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                  <Button label="Analyze Meal" emoji="📸" variant={addMode === "photo" ? "primary" : "secondary"} onPress={() => (addMode === "photo" ? closeAddMode() : setAddMode("photo"))} />
                  <Button label="Search Food" emoji="🔎" variant={addMode === "search" ? "primary" : "secondary"} onPress={() => (addMode === "search" ? closeAddMode() : setAddMode("search"))} />
                  <Button label="Manual Entry" emoji="✍🏽" variant={addMode === "manual" ? "primary" : "secondary"} onPress={() => (addMode === "manual" ? closeAddMode() : setAddMode("manual"))} />
                </View>

                {addMode === "photo" && (
                  <View style={{ gap: spacing.sm }}>
                    <Button label="Choose photo" emoji="📷" onPress={pickPhoto} loading={busy} />
                    {photoSuggestion && (
                      <EstimatedMealCard
                        suggestion={photoSuggestion}
                        onConfirm={(edited) => logFood(edited)}
                        onDiscard={() => setPhotoSuggestion(null)}
                        busy={busy}
                        confirmLabel="Looks right, add it"
                      />
                    )}
                  </View>
                )}

                {addMode === "search" && (
                  <View style={{ gap: spacing.sm }}>
                    <TextField placeholder="Search foods..." value={searchQuery} onChangeText={runSearch} />
                    {searchResults.map((food) => (
                      <View key={food.name} style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                        <Body>
                          {food.emoji} {food.name}
                        </Body>
                        <Button label={`${food.calories} cal`} variant="secondary" onPress={() => logFood(food)} loading={busy} />
                      </View>
                    ))}
                  </View>
                )}

                {addMode === "manual" && (
                  <View style={{ gap: spacing.sm }}>
                    <TextField placeholder="What did you eat?" value={manualName} onChangeText={setManualName} />
                    <TextField placeholder="Calories" value={manualCalories} onChangeText={setManualCalories} keyboardType="number-pad" />
                    <Button label="Add" emoji="➕" onPress={addManual} loading={busy} disabled={!manualName || !manualCalories} />
                  </View>
                )}
              </Card>
            )}
          </>
        )}
      </AsyncState>
    </Screen>
  );
}

function DayStrip({ selected, today, onSelect }: { selected: string; today: string; onSelect: (d: string) => void }) {
  const { theme } = useAppTheme();
  const days = last7Days();

  return (
    <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
      {days.map((d) => {
        const iso = isoDate(d);
        const isToday = iso === today;
        const isSelected = iso === selected;
        const label = d.toLocaleDateString(undefined, { weekday: "short" });
        return (
          <Pressable
            key={iso}
            onPress={() => onSelect(iso)}
            accessibilityLabel={`View ${label} ${d.getDate()}`}
            style={[
              { alignItems: "center", gap: 6, paddingVertical: 8, paddingHorizontal: 4, borderRadius: 18, minWidth: 40 },
              isSelected && isToday ? { backgroundColor: theme.tabBarBackground } : null,
            ]}
          >
            <Body style={{ fontSize: 12, color: isSelected && isToday ? theme.background : theme.textMuted, fontWeight: isSelected ? "600" : "400" }}>{label}</Body>
            <View
              style={{
                width: 38,
                height: 38,
                borderRadius: 19,
                alignItems: "center",
                justifyContent: "center",
                borderWidth: 2,
                borderColor: isToday ? theme.primary : isSelected ? theme.text : theme.surfaceAlt,
                borderStyle: isToday || isSelected ? "solid" : "dashed",
              }}
            >
              <Body style={{ fontSize: 15, fontWeight: isSelected ? "600" : "500", color: isSelected && isToday ? theme.background : theme.text }}>{d.getDate()}</Body>
            </View>
          </Pressable>
        );
      })}
    </View>
  );
}

function MacroCard({ label, value, goal, emoji, color }: { label: string; value: number; goal: number; emoji: string; color: string }) {
  const { theme } = useAppTheme();
  return (
    <Card style={{ flex: 1, gap: 12, paddingHorizontal: 12, paddingVertical: 14 }}>
      <View style={{ gap: 2 }}>
        <View style={{ flexDirection: "row", alignItems: "baseline", gap: 2 }}>
          <Subtitle style={{ fontSize: 22 }}>{Math.round(value)}</Subtitle>
          <Muted>/{Math.round(goal)}g</Muted>
        </View>
        <Muted>{label}</Muted>
      </View>
      <View style={{ alignSelf: "center" }}>
        <ProgressRing
          progress={goal > 0 ? value / goal : 0}
          size={72}
          strokeWidth={7}
          color={color}
          accessibilityLabel={`${label}, ${Math.round(value)} of ${Math.round(goal)} grams`}
        >
          <Body style={{ fontSize: 24 }}>{emoji}</Body>
        </ProgressRing>
      </View>
    </Card>
  );
}

function EstimatedMealCard({
  suggestion,
  onConfirm,
  onDiscard,
  busy,
  confirmLabel,
}: {
  suggestion: MealSuggestion;
  onConfirm: (edited: FoodResult) => void;
  onDiscard: () => void;
  busy: boolean;
  confirmLabel: string;
}) {
  const { theme } = useAppTheme();
  const [name, setName] = useState(suggestion.name);
  const [calories, setCalories] = useState(String(suggestion.calories));
  const [protein, setProtein] = useState(String(suggestion.protein_g));
  const [carbs, setCarbs] = useState(String(suggestion.carbs_g));
  const [fat, setFat] = useState(String(suggestion.fat_g));

  const confirm = () => {
    onConfirm({
      name: name.trim() || suggestion.name,
      calories: Number(calories) || 0,
      protein_g: Number(protein) || 0,
      carbs_g: Number(carbs) || 0,
      fat_g: Number(fat) || 0,
      emoji: suggestion.emoji,
    });
  };

  return (
    <View style={{ gap: spacing.sm, backgroundColor: theme.surface, borderRadius: 18, padding: spacing.md }}>
      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
        <Subtitle style={{ fontSize: 18 }}>
          {suggestion.emoji} {name || suggestion.name}
        </Subtitle>
        <View style={{ paddingHorizontal: spacing.sm, paddingVertical: 2, borderRadius: 999, backgroundColor: theme.tileBackground }}>
          <Muted style={{ fontSize: 10 }}>ESTIMATE — REVIEW BEFORE SAVING</Muted>
        </View>
      </View>
      {(suggestion.description || suggestion.note) && <Body style={{ color: theme.textMuted }}>{suggestion.description ?? suggestion.note}</Body>}

      <TextField placeholder="Meal name" value={name} onChangeText={setName} />
      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <View style={{ flex: 1 }}>
          <Muted style={{ fontSize: 11 }}>Calories</Muted>
          <TextField value={calories} onChangeText={setCalories} keyboardType="number-pad" />
        </View>
        <View style={{ flex: 1 }}>
          <Muted style={{ fontSize: 11 }}>Protein (g)</Muted>
          <TextField value={protein} onChangeText={setProtein} keyboardType="number-pad" />
        </View>
      </View>
      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <View style={{ flex: 1 }}>
          <Muted style={{ fontSize: 11 }}>Carbs (g)</Muted>
          <TextField value={carbs} onChangeText={setCarbs} keyboardType="number-pad" />
        </View>
        <View style={{ flex: 1 }}>
          <Muted style={{ fontSize: 11 }}>Fat (g)</Muted>
          <TextField value={fat} onChangeText={setFat} keyboardType="number-pad" />
        </View>
      </View>

      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <Button label={confirmLabel} emoji="✅" onPress={confirm} loading={busy} disabled={!name.trim() || !calories} />
        <Button label="Discard" variant="ghost" onPress={onDiscard} />
      </View>
    </View>
  );
}
