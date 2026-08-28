import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { MealPlan } from "@/services/types";
import { spacing } from "@/theme/tokens";

const MEAL_LABELS: Record<string, string> = {
  breakfast: "🥐 Breakfast",
  lunch: "🥗 Lunch",
  dinner: "🍽️ Dinner",
  snack: "🍓 Snack",
};

export default function Meals() {
  const { theme } = useAppTheme();
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [activePlan, setActivePlan] = useState<MealPlan | null>(null);
  const [busySlug, setBusySlug] = useState<string | null>(null);

  const load = async () => {
    const [allPlans, active] = await Promise.all([
      apiRequest<MealPlan[]>("/meal-plans"),
      apiRequest<{ active_plan: MealPlan | null }>("/meal-plans/active"),
    ]);
    setPlans(allPlans);
    setActivePlan(active.active_plan);
  };

  useFocusEffect(
    useCallback(() => {
      load();
    }, [])
  );

  const activate = async (id: string) => {
    setBusySlug(id);
    try {
      const res = await apiRequest<{ active_plan: MealPlan }>(`/meal-plans/${id}/activate`, { method: "POST" });
      setActivePlan(res.active_plan);
    } finally {
      setBusySlug(null);
    }
  };

  return (
    <Screen>
      <Title>🍽️ Meal Plans</Title>
      <Muted>Structured, soft-life nourishment — pick a plan that fits your week.</Muted>

      {activePlan && (
        <Card style={{ borderColor: theme.primary, borderWidth: 2 }}>
          <Subtitle>
            {activePlan.emoji} {activePlan.title} · Active
          </Subtitle>
          <Body style={{ color: theme.textMuted, marginTop: spacing.xs }}>{activePlan.description}</Body>
          <View style={{ marginTop: spacing.sm, gap: spacing.xs }}>
            {Object.entries(activePlan.meals).map(([type, meal]) => (
              <Body key={type}>
                {MEAL_LABELS[type] ?? type}: {meal}
              </Body>
            ))}
          </View>
        </Card>
      )}

      <View style={{ gap: spacing.md }}>
        {plans
          .filter((p) => p.id !== activePlan?.id)
          .map((plan) => (
            <Card key={plan.id} style={{ gap: spacing.xs }}>
              <Subtitle>
                {plan.emoji} {plan.title}
              </Subtitle>
              <Body style={{ color: theme.textMuted }}>{plan.description}</Body>
              <Muted>{plan.days} days</Muted>
              <Button
                label="Set as my plan"
                emoji="🌸"
                variant="secondary"
                onPress={() => activate(plan.id)}
                loading={busySlug === plan.id}
              />
            </Card>
          ))}
      </View>
    </Screen>
  );
}
