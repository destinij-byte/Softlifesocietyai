import React, { useCallback, useState } from "react";
import { Share, StyleSheet, View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { ProgressBar } from "@/components/ProgressBar";
import { Avatar } from "@/components/Avatar";
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

function IntensityBadge({ intensity }: { intensity: string }) {
  const { theme } = useAppTheme();
  if (intensity === "hard") {
    return (
      <View style={[styles.badge, { backgroundColor: theme.danger }]}>
        <Body style={styles.badgeText}>HARD</Body>
      </View>
    );
  }
  if (intensity === "easy") {
    return (
      <View style={[styles.badge, { backgroundColor: theme.surfaceAlt }]}>
        <Body style={[styles.badgeText, { color: theme.primary }]}>EASY</Body>
      </View>
    );
  }
  return (
    <View style={[styles.badge, { backgroundColor: theme.primary }]}>
      <Body style={[styles.badgeText, { color: theme.text }]}>MEDIUM</Body>
    </View>
  );
}

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
      <View style={{ gap: 6 }}>
        <Title>Wins</Title>
        <View style={[styles.goldRule, { backgroundColor: theme.primary }]} />
        <Muted>Do hard things, together.</Muted>
      </View>

      {mine.length > 0 && (
        <View style={{ gap: spacing.sm }}>
          <Muted>My Challenges</Muted>
          {mine.map((c) => (
            <Card key={c.slug} style={{ gap: spacing.xs }}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                <Subtitle style={{ fontSize: 15 }}>
                  {c.emoji} {c.title}
                </Subtitle>
                {c.intensity && <IntensityBadge intensity={c.intensity} />}
              </View>
              {c.duration_days < 9999 && <ProgressBar progress={c.progress} />}
              <Muted>
                Day {c.day_count}
                {c.duration_days < 9999 ? ` of ${c.duration_days}` : ""} · 🔥 {c.streak} day streak · {c.points} pts
              </Muted>
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
        <Subtitle style={{ fontSize: 15 }}>🏆 Family & Friends Leaderboard</Subtitle>
        {leaderboard.map((row) => (
          <View
            key={row.id}
            style={[
              styles.lbRow,
              row.is_you ? { backgroundColor: theme.surfaceAlt, borderRadius: 10, paddingHorizontal: spacing.sm } : null,
            ]}
          >
            <Muted style={{ width: 20, textAlign: "center" }}>{row.rank <= 3 ? MEDALS[row.rank - 1] : `#${row.rank}`}</Muted>
            <Avatar name={row.is_you ? "You" : row.name} size={26} />
            <Body style={{ flex: 1, fontWeight: row.is_you ? "700" : "400" }}>{row.is_you ? "You" : row.name}</Body>
            <Muted style={{ color: row.is_you ? theme.primary : theme.textMuted, fontWeight: "700" }}>
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

const styles = StyleSheet.create({
  goldRule: { width: 30, height: 3, borderRadius: 3 },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 999 },
  badgeText: { fontSize: 9, fontWeight: "800" as const, color: "#FFFFFF", letterSpacing: 0.4 },
  lbRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingVertical: 6 },
});
