import React, { useState } from "react";
import { Image, Pressable, StyleSheet, View } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { Card, Body, Muted, Subtitle } from "@/components/Themed";
import { Icon } from "@/components/Icon";
import { useAppTheme } from "@/context/ThemeContext";
import { apiRequest, apiUpload } from "@/services/api";
import { Goal } from "@/services/types";
import { radii, spacing } from "@/theme/tokens";

const TILE_SIZE = 100;

type VisionBoardProps = {
  goal: Goal;
  onChange: (goal: Goal) => void;
};

/**
 * A photo-collage vision board scoped to one quarterly or long-term goal —
 * she pastes in whatever she's manifesting for that specific goal, rather
 * than one generic board for the whole app.
 */
export function VisionBoard({ goal, onChange }: VisionBoardProps) {
  const { theme } = useAppTheme();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addPhoto = async () => {
    setError(null);
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setError("Photo library access is needed to build your vision board.");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({ quality: 0.7, allowsEditing: false });
    if (result.canceled || !result.assets?.[0]) return;

    setBusy(true);
    try {
      const updated = await apiUpload<Goal>(`/goals/${goal.id}/vision-images`, result.assets[0].uri, "photo");
      onChange(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't add that photo");
    } finally {
      setBusy(false);
    }
  };

  const removePhoto = async (imageId: string) => {
    const updated = await apiRequest<Goal>(`/goals/${goal.id}/vision-images/${imageId}`, { method: "DELETE" });
    onChange(updated);
  };

  return (
    <Card style={{ gap: spacing.sm }}>
      <Subtitle style={{ fontSize: 16 }}>🌠 Vision Board</Subtitle>
      <Muted>Collage the pictures that capture this goal — glance at it whenever you need the pull forward.</Muted>

      {error && <Body style={{ color: theme.danger, fontSize: 13 }}>⚠️ {error}</Body>}

      <View style={styles.grid}>
        {goal.vision_images.map((img) => (
          <View key={img.id} style={styles.tile}>
            <Image source={{ uri: img.image }} style={styles.image} />
            <Pressable
              onPress={() => removePhoto(img.id)}
              style={[styles.removeBadge, { backgroundColor: theme.background, borderColor: theme.border }]}
            >
              <Icon name="plus" size={12} color={theme.text} strokeWidth={2.2} />
            </Pressable>
          </View>
        ))}

        <Pressable
          onPress={addPhoto}
          disabled={busy}
          style={[styles.tile, styles.addTile, { borderColor: theme.accent, opacity: busy ? 0.6 : 1 }]}
        >
          <Icon name="plus" size={22} color={theme.accent} />
          <Muted style={{ marginTop: 4, fontSize: 11 }}>{busy ? "Adding…" : "Add photo"}</Muted>
        </Pressable>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  tile: {
    width: TILE_SIZE,
    height: TILE_SIZE,
    borderRadius: radii.md,
    overflow: "hidden",
  },
  image: { width: "100%", height: "100%" },
  addTile: {
    borderWidth: 1.5,
    borderStyle: "dashed",
    alignItems: "center",
    justifyContent: "center",
  },
  removeBadge: {
    position: "absolute",
    top: 4,
    right: 4,
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    transform: [{ rotate: "45deg" }],
  },
});
