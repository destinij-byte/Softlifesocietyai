import React, { useEffect, useRef, useState } from "react";
import { FlatList, KeyboardAvoidingView, Platform, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Body, Muted, Title } from "@/components/Themed";
import { TextField } from "@/components/TextField";
import { Button } from "@/components/Button";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest } from "@/services/api";
import { ChatMessage } from "@/services/types";
import { spacing, radii } from "@/theme/tokens";

export default function LunaChat() {
  const { theme } = useAppTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const listRef = useRef<FlatList>(null);

  const loadMessages = async () => {
    const data = await apiRequest<ChatMessage[]>("/luna/messages");
    setMessages(data);
  };

  useEffect(() => {
    loadMessages();
  }, []);

  const onSend = async () => {
    if (!input.trim()) return;
    const text = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text, created_at: new Date().toISOString() }]);
    setSending(true);
    try {
      const reply = await apiRequest<ChatMessage>("/luna/messages", { method: "POST", body: { message: text } });
      setMessages((prev) => [...prev, reply]);
    } finally {
      setSending(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.background }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={styles.header}>
          <Title>🌸 Luna</Title>
          <Muted>Your Soft Life coach</Muted>
        </View>

        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(_, i) => String(i)}
          contentContainerStyle={{ padding: spacing.lg, gap: spacing.sm }}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
          renderItem={({ item }) => (
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
              <Body style={{ color: item.role === "user" ? "#FFFFFF" : theme.text }}>{item.content}</Body>
            </View>
          )}
        />

        <View style={styles.inputRow}>
          <View style={{ flex: 1 }}>
            <TextField
              placeholder="Message Luna... 💬"
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
  bubble: { maxWidth: "80%", padding: spacing.md, borderRadius: radii.lg, borderWidth: 1 },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    padding: spacing.md,
  },
});
