import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { Icon } from "@/components/Icon";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { AffirmationState, Routine } from "@/services/types";
import { spacing } from "@/theme/tokens";

export default function Routines() {
  const { theme } = useAppTheme();
  const [type, setType] = useState<"morning" | "night">("morning");
  const [routine, setRoutine] = useState<Routine | null>(null);
  const [newStep, setNewStep] = useState("");
  const [busy, setBusy] = useState(false);

  const [affirmations, setAffirmations] = useState<AffirmationState | null>(null);
  const [journalDraft, setJournalDraft] = useState("");
  const [journalSaving, setJournalSaving] = useState(false);
  const [newAffirmation, setNewAffirmation] = useState("");

  const load = async (routineType: "morning" | "night") => {
    const [routineData, affirmationData] = await Promise.all([
      apiRequest<Routine>(`/routines/${routineType}`),
      apiRequest<AffirmationState>(`/affirmations/${routineType}`),
    ]);
    setRoutine(routineData);
    setAffirmations(affirmationData);
    setJournalDraft(affirmationData.journal_entry);
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

  const saveJournal = async () => {
    setJournalSaving(true);
    try {
      const updated = await apiRequest<AffirmationState>(`/affirmations/${type}/journal`, {
        method: "PUT",
        body: { text: journalDraft },
      });
      setAffirmations(updated);
    } finally {
      setJournalSaving(false);
    }
  };

  const addAffirmation = async () => {
    if (!newAffirmation.trim()) return;
    const updated = await apiRequest<AffirmationState>(`/affirmations/${type}/custom`, {
      method: "POST",
      body: { text: newAffirmation.trim() },
    });
    setAffirmations(updated);
    setNewAffirmation("");
  };

  const removeAffirmation = async (id: string) => {
    const updated = await apiRequest<AffirmationState>(`/affirmations/${type}/custom/${id}`, { method: "DELETE" });
    setAffirmations(updated);
  };

  const doneCount = routine?.steps.filter((s) => s.done).length ?? 0;

  return (
    <Screen>
      <Title>Routines</Title>
      <Muted>
        {doneCount}/{routine?.steps.length ?? 0} done today
      </Muted>

      <View style={{ flexDirection: "row", gap: spacing.sm }}>
        <Button
          label="Morning"
          icon={<Icon name="sun" size={16} color={type === "morning" ? "#1A1A1A" : theme.text} />}
          variant={type === "morning" ? "primary" : "secondary"}
          onPress={() => setType("morning")}
        />
        <Button
          label="Night"
          icon={<Icon name="moon" size={16} color={type === "night" ? "#1A1A1A" : theme.text} />}
          variant={type === "night" ? "primary" : "secondary"}
          onPress={() => setType("night")}
        />
      </View>

      {affirmations && (
        <Card elevated style={{ gap: spacing.sm }}>
          <Subtitle style={{ fontSize: 16 }}>✨ Today's Affirmation</Subtitle>
          <Body style={{ fontStyle: "italic" }}>"{affirmations.daily_affirmation}"</Body>

          <View style={{ height: 1, backgroundColor: theme.border, marginVertical: spacing.xs }} />

          <Muted>Manifestation prompt</Muted>
          <Body>{affirmations.manifestation_prompt}</Body>
          <TextField
            placeholder="Write whatever comes up..."
            value={journalDraft}
            onChangeText={setJournalDraft}
            onBlur={saveJournal}
            multiline
            style={{ minHeight: 70, textAlignVertical: "top" }}
          />
          <Button label={journalSaving ? "Saving…" : "Save"} variant="secondary" onPress={saveJournal} loading={journalSaving} />

          {affirmations.custom.length > 0 && (
            <View style={{ gap: spacing.xs, marginTop: spacing.xs }}>
              <Muted>Your own affirmations</Muted>
              {affirmations.custom.map((a) => (
                <View key={a.id} style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                  <Body style={{ flex: 1 }}>💛 {a.text}</Body>
                  <Body onPress={() => removeAffirmation(a.id)}>🗑️</Body>
                </View>
              ))}
            </View>
          )}

          <View style={{ flexDirection: "row", gap: spacing.sm, alignItems: "center", marginTop: spacing.xs }}>
            <View style={{ flex: 1 }}>
              <TextField placeholder="Write your own affirmation" value={newAffirmation} onChangeText={setNewAffirmation} />
            </View>
            <Button label="Add" onPress={addAffirmation} disabled={!newAffirmation.trim()} />
          </View>
        </Card>
      )}

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
