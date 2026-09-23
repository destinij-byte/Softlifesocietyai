import React, { useState } from "react";
import { View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Title, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { apiRequest } from "@/services/api";
import { spacing } from "@/theme/tokens";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  const onSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await apiRequest("/auth/password-reset/request", { method: "POST", body: { email }, auth: false });
      setSent(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <Screen>
        <View style={{ gap: spacing.xs }}>
          <Title>Check your email 💌</Title>
          <Body>If that email has an account, we've sent reset instructions. The link expires in 30 minutes.</Body>
        </View>
        <Muted onPress={() => router.replace("/(auth)/login")} style={{ textAlign: "center" }}>
          Back to log in
        </Muted>
      </Screen>
    );
  }

  return (
    <Screen>
      <View style={{ gap: spacing.xs }}>
        <Title>Forgot your password? 🤍</Title>
        <Body>Enter your email and we'll send you a link to reset it.</Body>
      </View>

      <TextField placeholder="Email" value={email} onChangeText={setEmail} autoCapitalize="none" keyboardType="email-address" />

      {error && <Body style={{ color: "#C4665A" }}>⚠️ {error}</Body>}

      <Button label="Send reset link" emoji="🌸" onPress={onSubmit} loading={loading} disabled={!email} />
      <Muted onPress={() => router.back()} style={{ textAlign: "center" }}>
        Back to log in
      </Muted>
    </Screen>
  );
}
