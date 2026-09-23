import React, { useCallback, useState } from "react";
import { Pressable, View } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import Svg, { Circle, Path } from "react-native-svg";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { AsyncState } from "@/components/AsyncState";
import { Button } from "@/components/Button";
import { Icon } from "@/components/Icon";
import { LunaAvatar } from "@/components/LunaAvatar";
import { ProgressRing } from "@/components/ProgressRing";
import { StaggerIn } from "@/components/StaggerIn";
import { useAuth } from "@/context/AuthContext";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { Alignment, AffirmationState, CatalogEntry, DailySummary, HomeContext, LeaderboardRow, MealSuggestion, MyChallenge, Routine, WaterState } from "@/services/types";
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
  const [water, setWater] = useState<WaterState | null>(null);
  const [ritual, setRitual] = useState<Routine | null>(null);
  const [myChallenges, setMyChallenges] = useState<MyChallenge[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardRow[]>([]);
  const [moodOptions, setMoodOptions] = useState<Record<string, CatalogEntry>>({});
  const [mood, setMood] = useState<string | null>(null);
  const [homeContext, setHomeContext] = useState<HomeContext | null>(null);
  const [alignment, setAlignment] = useState<Alignment | null>(null);
  const [affirmation, setAffirmation] = useState<AffirmationState | null>(null);

  const [suggestion, setSuggestion] = useState<MealSuggestion | null>(null);
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const load = async () => {
    // Each card's data loads independently — one endpoint failing (e.g. the
    // leaderboard) must never blank the whole screen, only that one card.
    const results = await Promise.allSettled([
      apiRequest<DailySummary>("/nourish/today"),
      apiRequest<WaterState>("/nourish/water"),
      apiRequest<Routine>("/routines/morning"),
      apiRequest<MyChallenge[]>("/challenges/mine"),
      apiRequest<LeaderboardRow[]>("/challenges/leaderboard"),
      apiRequest<Record<string, CatalogEntry>>("/home/mood/options", { auth: false }),
      apiRequest<{ mood: string | null }>("/home/mood"),
      apiRequest<HomeContext>("/home/context"),
      apiRequest<Alignment>("/progress/alignment"),
      apiRequest<AffirmationState>("/affirmations/morning"),
    ]);

    if (results[0].status === "fulfilled") setSummary(results[0].value);
    if (results[1].status === "fulfilled") setWater(results[1].value);
    if (results[2].status === "fulfilled") setRitual(results[2].value);
    if (results[3].status === "fulfilled") setMyChallenges(results[3].value);
    if (results[4].status === "fulfilled") setLeaderboard(results[4].value);
    if (results[5].status === "fulfilled") setMoodOptions(results[5].value);
    if (results[6].status === "fulfilled") setMood(results[6].value.mood);
    if (results[7].status === "fulfilled") setHomeContext(results[7].value);
    if (results[8].status === "fulfilled") setAlignment(results[8].value);
    if (results[9].status === "fulfilled") setAffirmation(results[9].value);
    setLoaded(true);
  };

  useFocusEffect(
    useCallback(() => {
      load();
    }, [])
  );

  const toggleRitualStep = async (stepId: string) => {
    const updated = await apiRequest<Routine>(`/routines/morning/steps/${stepId}/toggle`, { method: "PUT" });
    setRitual(updated);
  };

  const pickMood = async (key: string) => {
    setMood(key);
    try {
      await apiRequest("/home/mood", { method: "POST", body: { mood: key } });
    } catch {
      // Keep the optimistic selection — a failed save here isn't worth
      // interrupting her with an error over.
    }
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

  if (!loaded || !user) {
    return (
      <Screen>
        <AsyncState loading error={null}>
          {null}
        </AsyncState>
      </Screen>
    );
  }

  const ritualDone = ritual?.steps.filter((s) => s.done).length ?? 0;
  const ritualTotal = ritual?.steps.length ?? 0;
  const ritualProgress = ritualTotal > 0 ? ritualDone / ritualTotal : 0;
  const bestChallenge = [...myChallenges].sort((a, b) => b.streak - a.streak)[0];
  const remaining = summary ? Math.max(summary.goal_calories - summary.total_calories, 0) : null;

  // Era → priority weighting, not content-swapping: the tiles never change,
  // only their order — ranked by how closely each one's pillar matches the
  // Blueprint's current top priorities, so a "Money Era" user still sees
  // Nourish and Hydrate, just not necessarily first.
  const topPillarKeys = homeContext?.top_pillars.map((p) => p.pillar) ?? [];
  const pillarRank = (pillar: string) => {
    const idx = topPillarKeys.indexOf(pillar as (typeof topPillarKeys)[number]);
    return idx === -1 ? topPillarKeys.length : idx;
  };
  const glanceTiles = [
    { key: "nourish", pillar: "body", node: <GlanceTile icon={<Icon name="plate" size={16} color={theme.primary} />} label="Nourish" value={summary ? `${summary.total_calories}` : "—"} sub={summary ? `of ${summary.goal_calories} cal` : "unavailable"} /> },
    { key: "hydrate", pillar: "body", node: <GlanceTile icon={<Body style={{ fontSize: 16 }}>💧</Body>} label="Hydrate" value={water ? `${water.count}` : "—"} sub={water ? `of ${water.goal} glasses` : "unavailable"} /> },
    { key: "ritual", pillar: "mind", node: <GlanceTile icon={<Icon name="target" size={16} color={theme.primary} />} label="Ritual" value={`${ritualDone}/${ritualTotal}`} sub="today" /> },
  ].sort((a, b) => pillarRank(a.pillar) - pillarRank(b.pillar));

  return (
    <Screen>
      <StaggerIn index={0}>
        <View>
          <Muted>{new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}</Muted>
          <Title>
            {greeting()}, {user.name.split(" ")[0]}.
          </Title>
          {homeContext?.era_label && (
            <View style={{ flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: 6, marginTop: 4 }}>
              <Body style={{ fontSize: 12, color: theme.primary, fontWeight: "600", letterSpacing: 1 }}>{homeContext.era_label.toUpperCase()}</Body>
              {homeContext.top_pillars.length > 0 && (
                <Muted style={{ fontSize: 12 }}>· Prioritizing {homeContext.top_pillars.map((p) => p.label).join(", ")}</Muted>
              )}
            </View>
          )}
        </View>
      </StaggerIn>

      {affirmation && (
        <StaggerIn index={1}>
          <Card accent style={{ gap: 4 }}>
            <Muted style={{ fontSize: 11, letterSpacing: 1 }}>✨ TODAY'S AFFIRMATION</Muted>
            <Body style={{ fontStyle: "italic", fontSize: 15, lineHeight: 21 }}>"{affirmation.daily_affirmation}"</Body>
          </Card>
        </StaggerIn>
      )}

      {Object.keys(moodOptions).length > 0 && (
        <StaggerIn index={2}>
          <View style={{ gap: spacing.sm }}>
            <Subtitle style={{ fontSize: 14 }}>How are you feeling today?</Subtitle>
            <View style={{ flexDirection: "row", gap: spacing.xs }}>
              {Object.entries(moodOptions).map(([key, entry]) => {
                const selected = mood === key;
                return (
                  <Pressable
                    key={key}
                    onPress={() => pickMood(key)}
                    accessibilityRole="button"
                    accessibilityLabel={entry.label}
                    style={{
                      flex: 1,
                      alignItems: "center",
                      paddingVertical: spacing.sm,
                      borderRadius: 16,
                      backgroundColor: selected ? theme.primary : theme.surfaceAlt,
                    }}
                  >
                    <Body style={{ fontSize: 11, color: selected ? "#1A1A1A" : theme.textMuted }}>{entry.label}</Body>
                  </Pressable>
                );
              })}
            </View>
          </View>
        </StaggerIn>
      )}

      <StaggerIn index={3}>
        <Card style={{ gap: spacing.sm }}>
          <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
            <Subtitle style={{ fontSize: 15 }}>Today's Ritual</Subtitle>
            <Muted onPress={() => router.push("/(tabs)/routines")}>See all ›</Muted>
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.md }}>
            <View style={{ flex: 1, gap: spacing.sm }}>
              {ritualTotal === 0 && <Muted>Set up your morning routine to see it here.</Muted>}
              {(ritual?.steps ?? []).slice(0, 4).map((step) => (
                <Pressable
                  key={step.id}
                  onPress={() => toggleRitualStep(step.id)}
                  accessibilityRole="checkbox"
                  accessibilityState={{ checked: step.done }}
                  style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm }}
                >
                  <StepCheckbox done={step.done} color={theme.primary} track={theme.border} />
                  <Body style={{ flex: 1, textDecorationLine: step.done ? "line-through" : "none", color: step.done ? theme.textMuted : theme.text }}>
                    {step.label}
                  </Body>
                </Pressable>
              ))}
            </View>
            {ritualTotal > 0 && (
              <ProgressRing progress={ritualProgress} size={64} strokeWidth={6}>
                <Subtitle style={{ fontSize: 15 }}>
                  {ritualDone}/{ritualTotal}
                </Subtitle>
              </ProgressRing>
            )}
          </View>
        </Card>
      </StaggerIn>

      <StaggerIn index={3}>
        <View style={{ gap: spacing.sm }}>
          <Subtitle style={{ fontSize: 15 }}>Your Day at a Glance</Subtitle>
          <View style={{ flexDirection: "row", gap: spacing.sm }}>
            {glanceTiles.map((t) => (
              <React.Fragment key={t.key}>{t.node}</React.Fragment>
            ))}
          </View>
        </View>
      </StaggerIn>

      <StaggerIn index={4}>
        <Card style={{ backgroundColor: theme.mode === "dark" ? theme.surfaceAlt : "#1A1A1A", gap: spacing.sm }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm }}>
            <LunaAvatar size={28} />
            <Subtitle style={{ fontSize: 13, color: theme.primary }}>LUNA</Subtitle>
          </View>
          <Body style={{ color: "#FFF9F6" }}>
            {summary && remaining !== null
              ? `${remaining} calories left today — want me to build a dinner that fits?`
              : "I'm here whenever you want to plan today together."}
          </Body>
          {suggestion ? (
            <Card style={{ marginTop: spacing.xs }}>
              <Subtitle style={{ fontSize: 14 }}>
                {suggestion.emoji} {suggestion.name}
              </Subtitle>
              <Muted>
                {suggestion.calories} cal · {suggestion.protein_g}g protein
              </Muted>
            </Card>
          ) : (
            <View style={{ flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs }}>
              <Button label="Build my dinner" onPress={buildDinner} loading={busy} />
              <Pressable
                onPress={() => router.push("/(tabs)/luna")}
                style={{
                  paddingHorizontal: spacing.md,
                  paddingVertical: spacing.sm + 2,
                  borderRadius: 999,
                  borderWidth: 1,
                  borderColor: theme.primary,
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Body style={{ color: theme.primary, fontWeight: "600" }}>Ask Luna</Body>
              </Pressable>
            </View>
          )}
        </Card>
      </StaggerIn>

      <StaggerIn index={5}>
        <Card style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm, flex: 1 }}>
            <Icon name="trophy" size={17} color={theme.primary} />
            {bestChallenge ? (
              <Body style={{ flex: 1 }}>
                {bestChallenge.streak}-day streak on {bestChallenge.title}
                {leaderboard.length > 1 ? ` · #${leaderboard.find((r) => r.is_you)?.rank ?? "-"}` : ""}
              </Body>
            ) : (
              <Body style={{ flex: 1, color: theme.textMuted }}>Join a challenge to start your streak</Body>
            )}
          </View>
          <Muted onPress={() => router.push("/(tabs)/challenges")}>View ›</Muted>
        </Card>
      </StaggerIn>

      {alignment && (
        <StaggerIn index={6}>
          <Pressable onPress={() => router.push("/(tabs)/progress")}>
            <Card style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
              <View style={{ flex: 1 }}>
                <Body>{Math.round(alignment.score * 100)}% aligned this week</Body>
                <Muted style={{ fontSize: 11 }} numberOfLines={1}>
                  {alignment.why}
                </Muted>
              </View>
              <Muted>›</Muted>
            </Card>
          </Pressable>
        </StaggerIn>
      )}

      <StaggerIn index={7}>
        <Pressable onPress={() => router.push("/(tabs)/night-reset")}>
          <Card style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: spacing.sm, flex: 1 }}>
              <Icon name="moon" size={17} color={theme.primary} />
              <View style={{ flex: 1 }}>
                <Body>Night Reset</Body>
                {homeContext?.yesterday_focus ? (
                  <Muted style={{ fontSize: 11 }}>Yesterday's focus: {homeContext.yesterday_focus}</Muted>
                ) : (
                  <Muted style={{ fontSize: 11 }}>Close out your day</Muted>
                )}
              </View>
            </View>
            <Muted>›</Muted>
          </Card>
        </Pressable>
      </StaggerIn>
    </Screen>
  );
}

function StepCheckbox({ done, color, track }: { done: boolean; color: string; track: string }) {
  return (
    <Svg width={18} height={18} viewBox="0 0 24 24">
      {done ? (
        <>
          <Circle cx="12" cy="12" r="10" fill={color} />
          <Path d="M7.5 12.5 10.3 15.3 16.5 9" stroke="#1A1A1A" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </>
      ) : (
        <Circle cx="12" cy="12" r="9.3" stroke={track} strokeWidth={1.6} fill="none" />
      )}
    </Svg>
  );
}

function GlanceTile({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub: string }) {
  const { theme } = useAppTheme();
  return (
    <Card style={{ flex: 1, alignItems: "center", gap: 4, paddingVertical: spacing.md }}>
      {icon}
      <Subtitle style={{ fontSize: 18 }}>{value}</Subtitle>
      <Muted style={{ fontSize: 10, textAlign: "center" }}>{label}</Muted>
      <Muted style={{ fontSize: 9, textAlign: "center", color: theme.textMuted }}>{sub}</Muted>
    </Card>
  );
}
