// components/ui/MacroBadge.tsx
import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Colors } from "@/constants/theme";
import type { NutrientHighlight } from "@/lib/types/food";

const NUTRIENT_COLOR: Record<string, string> = {
  calories: Colors.macro.calorie,
  protein: Colors.macro.protein,
  carbs: Colors.macro.carbs,
  fat: Colors.macro.fat,
  fiber: Colors.macro.fiber,
};

const NUTRIENT_LABEL: Record<string, string> = {
  calories: "Cal",
  protein: "Pro",
  carbs: "Carbs",
  fat: "Fat",
  fiber: "Fiber",
};

interface Props {
  highlight: NutrientHighlight;
}

export function MacroBadge({ highlight }: Props) {
  const color = NUTRIENT_COLOR[highlight.nutrient] ?? Colors.textMuted;
  const label = NUTRIENT_LABEL[highlight.nutrient] ?? highlight.nutrient;

  return (
    <View style={[styles.badge, { borderColor: color }]}>
      <Text style={[styles.value, { color }]}>
        {highlight.value}
        <Text style={styles.unit}>{highlight.unit}</Text>
      </Text>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    alignItems: "center",
    minWidth: 52,
    backgroundColor: Colors.surface,
  },
  value: {
    fontSize: 13,
    fontWeight: "600",
  },
  unit: {
    fontSize: 10,
    fontWeight: "400",
  },
  label: {
    fontSize: 10,
    color: Colors.textMuted,
    marginTop: 1,
  },
});
