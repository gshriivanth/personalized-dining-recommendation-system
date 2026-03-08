// components/ui/NutrientBar.tsx
// Horizontal progress bar showing consumed vs goal for a single nutrient.
import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Colors, Spacing } from "@/constants/theme";

interface Props {
  label: string;
  consumed: number;
  goal: number | null;
  color: string;
  unit?: string;
}

export function NutrientBar({ label, consumed, goal, color, unit = "g" }: Props) {
  const pct = goal ? Math.min(consumed / goal, 1) : 0;

  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.barTrack}>
        <View style={[styles.barFill, { width: `${pct * 100}%`, backgroundColor: color }]} />
      </View>
      <Text style={styles.value}>
        {Math.round(consumed)}
        {goal ? `/${Math.round(goal)}${unit}` : unit}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: Spacing.sm,
    marginBottom: Spacing.xs,
  },
  label: {
    fontSize: 12,
    color: Colors.textMuted,
    width: 50,
  },
  barTrack: {
    flex: 1,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.border,
    overflow: "hidden",
  },
  barFill: {
    height: "100%",
    borderRadius: 3,
  },
  value: {
    fontSize: 11,
    color: Colors.textMuted,
    width: 72,
    textAlign: "right",
  },
});
