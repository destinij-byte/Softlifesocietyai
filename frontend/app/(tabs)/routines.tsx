import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { apiRequest } from "@/services/api";
import { Routine } from "@/services/types";
import { spacing } from "@/theme/tokens";

export default function Routines() {
  const [type, setType] = useState<"morning" | "night">("morning");
  const [routine, setRoutine] = useState<Routine | null>(null);
  const [newStep, setNewStep] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async (routineType: "morning" | "night") => {
    const data = await apiRequest<Routine>(`/routines/${routineType}`);
    setRoutine(data);
  };

  useFocusEffect(
    useCallback(() => {
      load(type);
    }, [type])
  );

  const toggleStep = async (stepId: string) => {
    const updated = await apiRequest<Routine>(`/routines/${type}/steps/${stepId}/toggle`, { method: "PUT" });
    setRoutine(updated);
  };

  const addStep = async () => {
    if (!newStep.trim()) return;
    setBusy(true);
    try {
      const updated = await apiRequest<Routine>(`/routines/${type}/steps`, { method: "POST", body: { label: newStep.trim() } });
      setRoutine(updated);
      setNewStep("");
    } finally {
      setBusy(false);
    }
  };

  const removeStep = async (stepId: string) => {
    const updated = await apiRequest<Routine>(`/routines/${type}/steps/${stepId}`, { method: "DELETE" });
    setRoutine(updated);
  };

  const doneCount = routine?.steps.filter((s) => s.done).length ?? 0;

  return (
    <Screen>
      <Title>📋 Routines</Title>
      <Muted>
        {doneCount}/{routine?.steps.length ?? 0} done today
      </Muted>

      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <Button label="Morning" emoji="🌅" variant={type === "morning" ? "primary" : "secondary"} onPress={() => setType("morning")} />
        <Button label="Night" emoji="🌙" variant={type === "night" ? "primary" : "secondary"} onPress={() => setType("night")} />
      </View>

      <View style={{ gap: spacing.sm }}>
        {routine?.steps.map((step) => (
          <Card key={step.id} style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
            <Body onPress={() => toggleStep(step.id)} style={{ flex: 1 }}>
              {step.done ? "✅" : "⬜️"} {step.label}
            </Body>
            <Body onPress={() => removeStep(step.id)}>🗑️</Body>
          </Card>
        ))}
      </View>

      <View style={{ flexDirection: "row", gap: spacing.sm, alignItems: "center" }}>
        <View style={{ flex: 1 }}>
          <TextField placeholder="Add a step" value={newStep} onChangeText={setNewStep} />
        </View>
        <Button label="Add" emoji="➕" onPress={addStep} loading={busy} disabled={!newStep.trim()} />
      </View>
    </Screen>
  );
}
