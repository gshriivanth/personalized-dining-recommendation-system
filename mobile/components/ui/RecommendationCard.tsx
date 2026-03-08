// components/ui/RecommendationCard.tsx
// The core UI primitive for both Dining Hall and Explore recommendations.
// Pass `variant="dining"` for the dark forest theme, `variant="explore"` for navy.
import React from "react";
import { View, Text, StyleSheet, Pressable } from "react-native";
import { Colors, Radius, Shadow, Spacing, Typography } from "@/constants/theme";
import { MacroBadge } from "./MacroBadge";
import type { RecommendationItem } from "@/lib/types/food";

interface Props {
  item: RecommendationItem;
  variant?: "dining" | "explore";
  onPress?: () => void;
}

export function RecommendationCard({ item, variant = "explore", onPress }: Props) {
  const { food, explanation, nutrient_highlights, score } = item;
  const isDining = variant === "dining";

  const accentColor = isDining ? Colors.dining.accent : Colors.explore.accent;
  const labelText = isDining ? "Best Pick Now" : "Picked For You";

  return (
    <Pressable
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      onPress={onPress}
    >
      {/* Header row */}
      <View style={styles.header}>
        <View style={styles.labelPill}>
          <View style={[styles.labelDot, { backgroundColor: accentColor }]} />
          <Text style={[styles.labelText, { color: accentColor }]}>{labelText}</Text>
        </View>
        {isDining && food.station && (
          <Text style={styles.station}>{food.station}</Text>
        )}
      </View>

      {/* Food name */}
      <Text style={styles.name} numberOfLines={2}>
        {food.name}
      </Text>
      {food.brand ? (
        <Text style={styles.brand}>{food.brand}</Text>
      ) : null}

      {/* Nutrient badges row */}
      {nutrient_highlights.length > 0 && (
        <View style={styles.badgesRow}>
          {nutrient_highlights.slice(0, 4).map((nh) => (
            <MacroBadge key={nh.nutrient} highlight={nh} />
          ))}
        </View>
      )}

      {/* Explanation */}
      <Text style={styles.explanation} numberOfLines={2}>
        {explanation}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.card,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    ...Shadow.card,
  },
  pressed: {
    opacity: 0.92,
    transform: [{ scale: 0.99 }],
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: Spacing.sm,
  },
  labelPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  labelDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  labelText: {
    fontSize: 11,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  station: {
    fontSize: 11,
    color: Colors.textMuted,
  },
  name: {
    ...Typography.subheading,
    marginBottom: 2,
  },
  brand: {
    ...Typography.label,
    marginBottom: Spacing.sm,
  },
  badgesRow: {
    flexDirection: "row",
    gap: Spacing.xs,
    flexWrap: "wrap",
    marginBottom: Spacing.sm,
  },
  explanation: {
    fontSize: 12,
    color: Colors.textMuted,
    lineHeight: 17,
  },
});
