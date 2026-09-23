import React, { useState } from "react";
import { View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { Screen } from "@/components/Screen";
import { Title, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { apiRequest } from "@/services/api";
import { spacing } from "@/theme/tokens";

export default function ResetPassword() {
  const params = useLocalSearchParams<{ token?: string }>();
  const [token, setToken] = useState(params.token ?? "");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const onSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await apiRequest("/auth/password-reset/confirm", { method: "POST", body: { token, new_password: newPassword }, auth: false });
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <Screen>
        <View style={{ gap: spacing.xs }}>
          <Title>Password updated 🌸</Title>
          <Body>You can now log in with your new password.</Body>
        </View>
        <Button label="Log in" emoji="🤍" onPress={() => router.replace("/(auth)/login")} />
      </Screen>
    );
  }

  return (
    <Screen>
      <View style={{ gap: spacing.xs }}>
        <Title>Choose a new password 🔐</Title>
        <Body>{params.token ? "Set a new password for your account." : "Paste the reset link's code below, then set a new password."}</Body>
      </View>

      <View style={{ gap: spacing.md }}>
        {!params.token && <TextField placeholder="Reset code" value={token} onChangeText={setToken} autoCapitalize="none" />}
        <TextField placeholder="New password" value={newPassword} onChangeText={setNewPassword} secureTextEntry />
      </View>

      {error && <Body style={{ color: "#C4665A" }}>⚠️ {error}</Body>}

      <Button label="Reset password" emoji="✨" onPress={onSubmit} loading={loading} disabled={!token || !newPassword} />
      <Muted onPress={() => router.replace("/(auth)/login")} style={{ textAlign: "center" }}>
        Back to log in
      </Muted>
    </Screen>
  );
}
