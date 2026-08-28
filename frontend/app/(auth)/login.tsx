import React, { useState } from "react";
import { View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Title, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { useAuth } from "@/context/AuthContext";
import { spacing } from "@/theme/tokens";

export default function Login() {
  const { logIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await logIn(email, password);
      router.replace("/(tabs)/luna");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <View style={{ gap: spacing.xs }}>
        <Title>Welcome back 🤍</Title>
        <Body>Log in to continue your soft life journey.</Body>
      </View>

      <View style={{ gap: spacing.md }}>
        <TextField
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        <TextField placeholder="Password" value={password} onChangeText={setPassword} secureTextEntry />
      </View>

      {error && <Body style={{ color: "#C4665A" }}>⚠️ {error}</Body>}

      <Button label="Log in" emoji="🌸" onPress={onSubmit} loading={loading} disabled={!email || !password} />
      <Muted onPress={() => router.push("/(auth)/signup")} style={{ textAlign: "center" }}>
        New here? Start your free trial
      </Muted>
    </Screen>
  );
}
