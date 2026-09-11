import React, { useState } from "react";
import { View } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/components/Screen";
import { Title, Body, Muted } from "@/components/Themed";
import { Button } from "@/components/Button";
import { TextField } from "@/components/TextField";
import { useAuth } from "@/context/AuthContext";
import { spacing } from "@/theme/tokens";

export default function SignUp() {
  const { signUp } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await signUp(name, email, password);
      router.replace("/(tabs)/home");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <View style={{ gap: spacing.xs }}>
        <Title>Welcome, gorgeous 🌷</Title>
        <Body>Create your account to start your 7-day free trial with Luna.</Body>
      </View>

      <View style={{ gap: spacing.md }}>
        <TextField placeholder="Your name" value={name} onChangeText={setName} autoCapitalize="words" />
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

      <Button label="Create account" emoji="✨" onPress={onSubmit} loading={loading} disabled={!name || !email || !password} />
      <Muted onPress={() => router.push("/(auth)/login")} style={{ textAlign: "center" }}>
        Already have an account? Log in
      </Muted>
    </Screen>
  );
}
