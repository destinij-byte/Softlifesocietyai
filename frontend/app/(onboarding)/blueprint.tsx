import React, { useEffect, useState } from "react";
import { Pressable, View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { ProgressBar } from "@/components/ProgressBar";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { Blueprint, CatalogEntry, CoachingStyle, Era, MotivationStyle, NutritionPreferences, Pillar } from "@/services/types";
import { spacing } from "@/theme/tokens";

const STEP_COUNT = 5;

export default function BlueprintOnboarding() {
  const { theme } = useAppTheme();
  const [step, setStep] = useState(0);

  const [eras, setEras] = useState<Record<string, CatalogEntry>>({});
  const [pillars, setPillars] = useState<Record<string, CatalogEntry>>({});
  const [coachingStyles, setCoachingStyles] = useState<Record<string, CatalogEntry>>({});
  const [motivationStyles, setMotivationStyles] = useState<Record<string, CatalogEntry>>({});

  const [era, setEra] = useState<Era | null>(null);
  const [currentState, setCurrentState] = useState("");
  const [becoming, setBecoming] = useState("");
  const [priorities, setPriorities] = useState<Record<string, number>>({});
  const [preferredName, setPreferredName] = useState("");
  const [coachingStyle, setCoachingStyle] = useState<CoachingStyle | null>(null);
  const [motivationStyle, setMotivationStyle] = useState<MotivationStyle | null>(null);

  // Fields this wizard doesn't edit directly (owned by Affirmations /
  // Manifestations / Nourish preferences screens) but must round-trip
  // unchanged, since PUT /blueprint is a full upsert — without this, saving
  // here would silently wipe out preferences set elsewhere.
  const [affirmationCategories, setAffirmationCategories] = useState<string[]>([]);
  const [manifestationCategories, setManifestationCategories] = useState<string[]>([]);
  const [nutritionPreferences, setNutritionPreferences] = useState<NutritionPreferences>({ dietary_style: null, notes: "" });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiRequest<Record<string, CatalogEntry>>("/blueprint/eras", { auth: false }),
      apiRequest<Record<string, CatalogEntry>>("/blueprint/pillars", { auth: false }),
      apiRequest<Record<string, CatalogEntry>>("/blueprint/coaching-styles", { auth: false }),
      apiRequest<Record<string, CatalogEntry>>("/blueprint/motivation-styles", { auth: false }),
      apiRequest<Blueprint>("/blueprint"),
    ]).then(([e, p, cs, ms, existing]) => {
      setEras(e);
      setPillars(p);
      setCoachingStyles(cs);
      setMotivationStyles(ms);

      // Pre-fill from whatever's already saved — this screen doubles as the
      // edit flow (You → My Blueprint), not just first-time onboarding.
      setEra(existing.era);
      setCurrentState(existing.current_state);
      setBecoming(existing.becoming);
      setPriorities(Object.fromEntries(existing.pillars.map((p) => [p.pillar, p.priority])));
      setPreferredName(existing.preferred_name ?? "");
      setCoachingStyle(existing.coaching_style);
      setMotivationStyle(existing.motivation_style);
      setAffirmationCategories(existing.affirmation_categories);
      setManifestationCategories(existing.manifestation_categories);
      setNutritionPreferences(existing.nutrition_preferences);
    });
  }, []);

  const next = () => setStep((s) => Math.min(s + 1, STEP_COUNT - 1));
  const back = () => setStep((s) => Math.max(s - 1, 0));

  const setPriority = (pillar: string, value: number) => {
    setPriorities((prev) => ({ ...prev, [pillar]: value }));
  };

  const finish = async () => {
    setError(null);
    setSaving(true);
    try {
      const payload: Blueprint = {
        era,
        current_state: currentState.trim(),
        becoming: becoming.trim(),
        pillars: Object.entries(priorities)
          .filter(([, priority]) => priority > 0)
          .map(([pillar, priority]) => ({ pillar: pillar as Pillar, priority })),
        preferred_name: preferredName.trim() || null,
        coaching_style: coachingStyle,
        motivation_style: motivationStyle,
        affirmation_categories: affirmationCategories,
        manifestation_categories: manifestationCategories,
        nutrition_preferences: nutritionPreferences,
      };
      await apiRequest("/blueprint", { method: "PUT", body: payload });
      router.replace("/(tabs)/home");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong saving your Blueprint");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Screen>
      <View style={{ gap: spacing.xs }}>
        <ProgressBar progress={(step + 1) / STEP_COUNT} />
        <Muted>
          Step {step + 1} of {STEP_COUNT}
        </Muted>
      </View>

      {step === 0 && (
        <View style={{ gap: spacing.md }}>
          <View style={{ gap: spacing.xs }}>
            <Title>What era are you stepping into?</Title>
            <Body style={{ color: theme.textMuted }}>This shapes how Luna coaches you — you can change it any time.</Body>
          </View>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
            {Object.entries(eras).map(([key, entry]) => (
              <Pressable key={key} onPress={() => setEra(key as Era)} style={{ width: "47%" }}>
                <Card
                  style={{
                    alignItems: "center",
                    paddingVertical: spacing.lg,
                    borderColor: era === key ? theme.primary : theme.border,
                    borderWidth: era === key ? 2 : 1,
                  }}
                >
                  <Subtitle style={{ fontSize: 26 }}>{entry.emoji}</Subtitle>
                  <Body style={{ marginTop: spacing.xs, textAlign: "center" }}>{entry.label}</Body>
                </Card>
              </Pressable>
            ))}
          </View>
        </View>
      )}

      {step === 1 && (
        <View style={{ gap: spacing.md }}>
          <View style={{ gap: spacing.xs }}>
            <Title>Who are you becoming?</Title>
            <Body style={{ color: theme.textMuted }}>A few words is plenty — Luna uses this to understand your direction, not to judge where you are.</Body>
          </View>
          <View style={{ gap: spacing.sm }}>
            <Muted>Who you are right now</Muted>
            <TextField
              placeholder="e.g. Overwhelmed but ready for a change"
              value={currentState}
              onChangeText={setCurrentState}
              multiline
              style={{ minHeight: 70, textAlignVertical: "top" }}
            />
          </View>
          <View style={{ gap: spacing.sm }}>
            <Muted>Who you're becoming</Muted>
            <TextField
              placeholder="e.g. Disciplined, confident, financially secure"
              value={becoming}
              onChangeText={setBecoming}
              multiline
              style={{ minHeight: 70, textAlignVertical: "top" }}
            />
          </View>
        </View>
      )}

      {step === 2 && (
        <View style={{ gap: spacing.md }}>
          <View style={{ gap: spacing.xs }}>
            <Title>What matters most right now?</Title>
            <Body style={{ color: theme.textMuted }}>Tap to set how much focus each area deserves. Skip any that don't apply yet.</Body>
          </View>
          <View style={{ gap: spacing.md }}>
            {Object.entries(pillars).map(([key, entry]) => (
              <View key={key} style={{ gap: spacing.xs }}>
                <Body>
                  {entry.emoji} {entry.label}
                </Body>
                <View style={{ flexDirection: "row", gap: spacing.sm }}>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <Pressable
                      key={n}
                      onPress={() => setPriority(key, n)}
                      accessibilityRole="button"
                      accessibilityLabel={`${entry.label} priority ${n} of 5`}
                      style={{
                        width: 28,
                        height: 28,
                        borderRadius: 14,
                        backgroundColor: (priorities[key] ?? 0) >= n ? theme.primary : theme.surfaceAlt,
                        borderWidth: 1,
                        borderColor: theme.border,
                      }}
                    />
                  ))}
                </View>
              </View>
            ))}
          </View>
        </View>
      )}

      {step === 3 && (
        <View style={{ gap: spacing.md }}>
          <View style={{ gap: spacing.xs }}>
            <Title>How should Luna show up for you?</Title>
            <Body style={{ color: theme.textMuted }}>Optional — helps her match your tone and what actually gets you moving.</Body>
          </View>
          <View style={{ gap: spacing.sm }}>
            <Muted>What should Luna call you?</Muted>
            <TextField placeholder="e.g. Des (defaults to your name)" value={preferredName} onChangeText={setPreferredName} />
          </View>
          <View style={{ gap: spacing.sm }}>
            <Muted>Coaching style</Muted>
            <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
              {Object.entries(coachingStyles).map(([key, entry]) => (
                <Button
                  key={key}
                  label={entry.label}
                  emoji={entry.emoji}
                  variant={coachingStyle === key ? "primary" : "secondary"}
                  onPress={() => setCoachingStyle(coachingStyle === key ? null : (key as CoachingStyle))}
                />
              ))}
            </View>
          </View>
          <View style={{ gap: spacing.sm }}>
            <Muted>What motivates you most?</Muted>
            <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
              {Object.entries(motivationStyles).map(([key, entry]) => (
                <Button
                  key={key}
                  label={entry.label}
                  emoji={entry.emoji}
                  variant={motivationStyle === key ? "primary" : "secondary"}
                  onPress={() => setMotivationStyle(motivationStyle === key ? null : (key as MotivationStyle))}
                />
              ))}
            </View>
          </View>
        </View>
      )}

      {step === 4 && (
        <View style={{ gap: spacing.md }}>
          <View style={{ gap: spacing.xs }}>
            <Title>Your Blueprint</Title>
            <Body style={{ color: theme.textMuted }}>This is the foundation Luna builds your daily plan from — you can refine it any time from More.</Body>
          </View>
          <Card style={{ gap: spacing.sm }}>
            <Body>
              {era ? `${eras[era]?.emoji} ${eras[era]?.label}` : "No era selected"}
            </Body>
            {becoming ? <Muted>Becoming: {becoming}</Muted> : null}
            {Object.entries(priorities).filter(([, p]) => p > 0).length > 0 && (
              <Muted>
                Focus areas:{" "}
                {Object.entries(priorities)
                  .filter(([, p]) => p > 0)
                  .map(([key]) => pillars[key]?.label)
                  .join(", ")}
              </Muted>
            )}
            {coachingStyle && <Muted>Coaching style: {coachingStyles[coachingStyle]?.label}</Muted>}
            {motivationStyle && <Muted>Motivated by: {motivationStyles[motivationStyle]?.label}</Muted>}
          </Card>
          {error && <Body style={{ color: theme.danger }}>⚠️ {error}</Body>}
        </View>
      )}

      <View style={{ flexDirection: "row", gap: spacing.sm, marginTop: "auto" }}>
        {step > 0 && <Button label="Back" variant="secondary" onPress={back} />}
        {step < STEP_COUNT - 1 ? (
          <Button label="Continue" onPress={next} disabled={step === 0 && !era} />
        ) : (
          <Button label="Enter Your Era" emoji="✨" onPress={finish} loading={saving} />
        )}
      </View>
    </Screen>
  );
}
