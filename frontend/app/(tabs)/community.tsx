import React, { useCallback, useState } from "react";
import { View } from "react-native";
import { useFocusEffect } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card, Title, Subtitle, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { Friend } from "@/services/types";
import { spacing } from "@/theme/tokens";

type Encouragement = { from_user_name: string; message: string };

export default function Community() {
  const { theme } = useAppTheme();
  const [friends, setFriends] = useState<Friend[]>([]);
  const [encouragements, setEncouragements] = useState<Encouragement[]>([]);
  const [friendEmail, setFriendEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cheeredIds, setCheeredIds] = useState<string[]>([]);

  const load = async () => {
    const [friendsData, encData] = await Promise.all([
      apiRequest<Friend[]>("/social/friends"),
      apiRequest<Encouragement[]>("/social/encouragements"),
    ]);
    setFriends(friendsData);
    setEncouragements(encData);
  };

  useFocusEffect(
    useCallback(() => {
      load();
    }, [])
  );

  const addFriend = async () => {
    if (!friendEmail.trim()) return;
    setError(null);
    setBusy(true);
    try {
      await apiRequest("/social/friends/add", { method: "POST", body: { email: friendEmail.trim() } });
      setFriendEmail("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't add friend");
    } finally {
      setBusy(false);
    }
  };

  const encourage = async (id: string) => {
    await apiRequest(`/social/friends/${id}/encourage`, { method: "POST" });
    setCheeredIds((prev) => [...prev, id]);
  };

  return (
    <Screen>
      <Title>💛 Community</Title>
      <Muted>Your friends & family, cheering you on.</Muted>

      <Card style={{ gap: spacing.sm }}>
        <Subtitle>Add a friend 🤍</Subtitle>
        <TextField
          placeholder="Their Soft Life Society email"
          value={friendEmail}
          onChangeText={setFriendEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        {error && <Body style={{ color: theme.danger }}>⚠️ {error}</Body>}
        <Button label="Add friend" emoji="➕" onPress={addFriend} loading={busy} disabled={!friendEmail.trim()} />
      </Card>

      {encouragements.length > 0 && (
        <Card style={{ gap: spacing.xs }}>
          <Subtitle>Cheering for you 🎉</Subtitle>
          {encouragements.map((e, i) => (
            <Body key={i}>
              {e.from_user_name}: {e.message}
            </Body>
          ))}
        </Card>
      )}

      <View style={{ gap: spacing.md }}>
        {friends.map((f) => (
          <Card key={f.id} style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
            <View>
              <Subtitle>
                {f.avatar_emoji} {f.name}
              </Subtitle>
              <Muted>{f.moved_today ? "Moved today 💪" : "Hasn't moved yet today"}</Muted>
            </View>
            <Button
              label={cheeredIds.includes(f.id) ? "Cheered! 🎉" : "Encourage"}
              emoji="👏"
              variant="secondary"
              onPress={() => encourage(f.id)}
              disabled={cheeredIds.includes(f.id)}
            />
          </Card>
        ))}
        {friends.length === 0 && <Muted>Add friends & family to share your soft life journey 🌸</Muted>}
      </View>
    </Screen>
  );
}
