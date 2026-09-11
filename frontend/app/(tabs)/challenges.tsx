import React, { useCallback, useState } from "react";
import { Share, View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { ProgressBar } from "@/components/ProgressBar";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { ChallengeTemplate, LeaderboardRow, MyChallenge } from "@/services/types";
import { spacing } from "@/theme/tokens";

const INTENSITIES = [
  { key: "hard", label: "Hard", emoji: "🔥" },
  { key: "medium", label: "Medium", emoji: "🌤" },
  { key: "easy", label: "Easy", emoji: "🌱" },
];

const MEDALS = ["🥇", "🥈", "🥉"];

export default function Challenges() {
  const { theme } = useAppTheme();
  const [templates, setTemplates] = useState<ChallengeTemplate[]>([]);
  const [mine, setMine] = useState<MyChallenge[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardRow[]>([]);
  const [pickingIntensity, setPickingIntensity] = useState<string | null>(null);
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [redeemCode, setRedeemCode] = useState("");
  const [busySlug, setBusySlug] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    const [t, m, l] = await Promise.all([
      apiRequest<ChallengeTemplate[]>("/challenges/templates"),
      apiRequest<MyChallenge[]>("/challenges/mine"),
      apiRequest<LeaderboardRow[]>("/challenges/leaderboard"),
    ]);
    setTemplates(t);
    setMine(m);
    setLeaderboard(l);
  };

  useFocusEffect(
    useCallback(() => {
      load();
    }, [])
  );

  const join = async (slug: string, intensity?: string) => {
    setBusySlug(slug);
    try {
      await apiRequest(`/challenges/${slug}/join`, { method: "POST", body: { intensity } });
      setPickingIntensity(null);
      await load();
    } finally {
      setBusySlug(null);
    }
  };

  const logToday = async (slug: string) => {
    setBusySlug(slug);
    try {
      await apiRequest(`/challenges/${slug}/log-today`, { method: "POST" });
      await load();
    } finally {
      setBusySlug(null);
    }
  };

  const myChallengeSlugs = new Set(mine.map((c) => c.slug));

  const shareInvite = async () => {
    let code = inviteCode;
    if (!code) {
      const res = await apiRequest<{ code: string; invite_link: string }>("/social/invite-code");
      code = res.code;
      setInviteCode(code);
    }
    await Share.share({ message: `Join my Soft Life Society challenges! Use invite code: ${code} 🌸` });
  };

  const redeemInvite = async () => {
    if (!redeemCode.trim()) return;
    setError(null);
    try {
      await apiRequest("/social/invite/redeem", { method: "POST", body: { code: redeemCode.trim() } });
      setRedeemCode("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't redeem that code");
    }
  };

  return (
    <Screen>
      <Title>Challenges</Title>

      {mine.length > 0 && (
        <View style={{ gap: spacing.sm }}>
          <Muted>My Challenges</Muted>
          {mine.map((c) => (
            <Card key={c.slug} style={{ gap: spacing.xs }}>
              <Subtitle>
                {c.emoji} {c.title} {c.intensity ? `(${c.intensity})` : ""}
              </Subtitle>
              <Muted>
                Day {c.day_count}
                {c.duration_days < 9999 ? ` / ${c.duration_days}` : ""} · 🔥 {c.streak} day streak · {c.points} pts
              </Muted>
              {c.duration_days < 9999 && <ProgressBar progress={c.progress} />}
              <Button
                label={c.logged_today ? "Logged today ✅" : "Log Today"}
                emoji={c.logged_today ? undefined : "📍"}
                variant={c.logged_today ? "secondary" : "primary"}
                disabled={c.logged_today}
                onPress={() => logToday(c.slug)}
                loading={busySlug === c.slug}
              />
            </Card>
          ))}
        </View>
      )}

      <View style={{ gap: spacing.sm }}>
        <Muted>Join a Challenge</Muted>
        {templates
          .filter((t) => !myChallengeSlugs.has(t.slug))
          .map((t) => (
            <Card key={t.slug} style={{ gap: spacing.xs }}>
              <Subtitle>
                {t.emoji} {t.title}
              </Subtitle>
              {t.description && <Body style={{ color: theme.textMuted }}>{t.description}</Body>}
              {t.needs_intensity ? (
                pickingIntensity === t.slug ? (
                  <View style={{ flexDirection: "row", gap: spacing.sm, flexWrap: "wrap" }}>
                    {INTENSITIES.map((i) => (
                      <Button key={i.key} label={i.label} emoji={i.emoji} variant="secondary" onPress={() => join(t.slug, i.key)} loading={busySlug === t.slug} />
                    ))}
                  </View>
                ) : (
                  <Button label="Join" emoji="🌷" onPress={() => setPickingIntensity(t.slug)} />
                )
              ) : (
                <Button label="Join" emoji="🌷" onPress={() => join(t.slug)} loading={busySlug === t.slug} />
              )}
            </Card>
          ))}
      </View>

      <Card style={{ gap: spacing.sm }}>
        <Subtitle>💛 Family & Friends Leaderboard</Subtitle>
        {leaderboard.map((row) => (
          <View key={row.id} style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
            <Body style={{ fontWeight: row.is_you ? "700" : "400", color: row.is_you ? theme.primary : theme.text }}>
              {row.rank <= 3 ? MEDALS[row.rank - 1] : `#${row.rank}`} {row.avatar_emoji} {row.is_you ? "You" : row.name}
            </Body>
            <Muted>
              {row.points} pts · 🔥{row.streak}
            </Muted>
          </View>
        ))}
        {leaderboard.length <= 1 && <Muted>Invite family & friends to see the board come alive 🌸</Muted>}
      </Card>

      <Card style={{ gap: spacing.sm }}>
        <Subtitle>Invite Family & Friends</Subtitle>
        <Button label="Share invite link" emoji="🔗" variant="secondary" onPress={shareInvite} />
        <View style={{ flexDirection: "row", gap: spacing.sm, alignItems: "center" }}>
          <View style={{ flex: 1 }}>
            <TextField placeholder="Have a code? Enter it" value={redeemCode} onChangeText={setRedeemCode} autoCapitalize="none" />
          </View>
          <Button label="Join" onPress={redeemInvite} disabled={!redeemCode.trim()} />
        </View>
        {error && <Body style={{ color: theme.danger }}>⚠️ {error}</Body>}
      </Card>
    </Screen>
  );
}
