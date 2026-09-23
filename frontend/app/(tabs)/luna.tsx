import React, { useEffect, useRef, useState } from "react";
import { Alert, FlatList, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Body, Muted, Title } from "@/components/Themed";
import { TextField } from "@/components/TextField";
import { Button } from "@/components/Button";
import { AsyncState } from "@/components/AsyncState";
import { LunaAvatar } from "@/components/LunaAvatar";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest, ApiError } from "@/services/api";
import { ChatMessage, Goal, LunaAction, LunaMode } from "@/services/types";
import { spacing, radii } from "@/theme/tokens";

const MODES: { key: LunaMode; label: string; emoji: string }[] = [
  { key: "life", label: "Life", emoji: "🌸" },
  { key: "money", label: "Money", emoji: "💰" },
  { key: "wellness", label: "Wellness", emoji: "🍓" },
  { key: "goals", label: "Goals", emoji: "🎯" },
];

export default function YourAI() {
  const { theme } = useAppTheme();
  const [mode, setMode] = useState<LunaMode>("life");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [confirmedActions, setConfirmedActions] = useState<Set<string>>(new Set());
  const [messagesLoading, setMessagesLoading] = useState(true);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const listRef = useRef<FlatList>(null);

  const loadMessages = async (m: LunaMode) => {
    setMessagesLoading(true);
    setMessagesError(null);
    try {
      const data = await apiRequest<ChatMessage[]>(`/luna/messages?mode=${m}`);
      setMessages(data);
    } catch (e) {
      setMessagesError(e instanceof ApiError ? e.message : "Couldn't load your conversation with Luna.");
    } finally {
      setMessagesLoading(false);
    }
  };

  useEffect(() => {
    loadMessages(mode);
  }, [mode]);

  const onSend = async () => {
    if (!input.trim()) return;
    const text = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text, mode, created_at: new Date().toISOString() }]);
    setSending(true);
    try {
      const reply = await apiRequest<ChatMessage>("/luna/messages", { method: "POST", body: { message: text, mode } });
      setMessages((prev) => [...prev, reply]);
    } finally {
      setSending(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }
  };

  const runAction = async (messageId: string, index: number, action: LunaAction) => {
    const key = `${messageId}:${index}`;
    try {
      if (action.type === "create_goal") {
        await apiRequest("/goals", {
          method: "POST",
          body: {
            title: String(action.payload.title ?? "New goal"),
            category: String(action.payload.category ?? "personal"),
            target: String(action.payload.target ?? ""),
            emoji: "🎯",
            timeframe: "none",
          },
        });
      } else if (action.type === "generate_breakdown") {
        const goals = await apiRequest<Goal[]>("/goals");
        const goalTitle = String(action.payload.goal_title ?? "").toLowerCase();
        const goal = goals.find((g) => g.title.toLowerCase() === goalTitle);
        if (!goal) {
          Alert.alert("Create the goal first", `I couldn't find a goal called "${action.payload.goal_title}" yet.`);
          return;
        }
        const steps = Array.isArray(action.payload.steps) ? (action.payload.steps as Record<string, unknown>[]) : [];
        for (const step of steps) {
          await apiRequest(`/goals/${goal.id}/breakdown`, {
            method: "POST",
            body: { period: String(step.period ?? "today"), label: String(step.label ?? ""), target: step.target ?? null },
          });
        }
      }
      setConfirmedActions((prev) => new Set(prev).add(key));
    } catch {
      Alert.alert("Something went sideways", "That didn't go through — try again in a moment.");
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.background }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={[styles.header, { flexDirection: "row", alignItems: "center", gap: spacing.sm }]}>
          <LunaAvatar size={44} />
          <View>
            <Title>Luna</Title>
            <Muted>Luna Reyes, however you need her today</Muted>
          </View>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.modeScroll} contentContainerStyle={styles.modeRow}>
          {MODES.map((m) => (
            <Button
              key={m.key}
              label={m.label}
              emoji={m.emoji}
              variant={mode === m.key ? "primary" : "secondary"}
              onPress={() => setMode(m.key)}
            />
          ))}
        </ScrollView>

        <AsyncState loading={messagesLoading} error={messagesError} onRetry={() => loadMessages(mode)}>
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(_, i) => String(i)}
          contentContainerStyle={{ padding: spacing.lg, gap: spacing.sm }}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
          renderItem={({ item, index }) => (
            <View
              style={[
                styles.bubble,
                {
                  alignSelf: item.role === "user" ? "flex-end" : "flex-start",
                  backgroundColor: item.role === "user" ? theme.primary : theme.surface,
                  borderColor: theme.border,
                },
              ]}
            >
              <Body style={{ color: item.role === "user" ? "#1A1A1A" : theme.text }}>{item.content}</Body>
              {(item.actions ?? []).map((action: LunaAction, actionIndex: number) => {
                const messageId = item.id ?? String(index);
                const key = `${messageId}:${actionIndex}`;
                const done = confirmedActions.has(key);
                return (
                  <Pressable
                    key={key}
                    disabled={done}
                    onPress={() => runAction(messageId, actionIndex, action)}
                    style={{
                      marginTop: spacing.sm,
                      paddingHorizontal: spacing.md,
                      paddingVertical: spacing.sm,
                      borderRadius: radii.pill,
                      borderWidth: 1,
                      borderColor: theme.primary,
                      backgroundColor: done ? "transparent" : theme.primary,
                      alignSelf: "flex-start",
                      opacity: done ? 0.6 : 1,
                    }}
                  >
                    <Body style={{ color: done ? theme.primary : "#1A1A1A", fontWeight: "600" }}>{done ? "✓ Done" : action.label}</Body>
                  </Pressable>
                );
              })}
            </View>
          )}
        />
        </AsyncState>

        <View style={styles.inputRow}>
          <View style={{ flex: 1 }}>
            <TextField
              placeholder={`Message Luna about ${mode}... 💬`}
              value={input}
              onChangeText={setInput}
              onSubmitEditing={onSend}
              returnKeyType="send"
            />
          </View>
          <Button label="Send" emoji="🌷" onPress={onSend} loading={sending} disabled={!input.trim()} />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  header: { paddingHorizontal: spacing.lg, paddingTop: spacing.md },
  modeScroll: { flexGrow: 0, flexShrink: 0 },
  modeRow: { paddingHorizontal: spacing.lg, paddingTop: spacing.md, gap: spacing.sm, alignItems: "center" },
  bubble: { maxWidth: "80%", padding: spacing.md, borderRadius: radii.lg, borderWidth: 1 },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    padding: spacing.md,
  },
});
