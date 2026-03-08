// components/ui/HallStatusBadge.tsx
import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Colors, Radius } from "@/constants/theme";

interface Props {
  isOpen: boolean;
  mealPeriod: string | null;
}

export function HallStatusBadge({ isOpen, mealPeriod }: Props) {
  return (
    <View style={[styles.badge, isOpen ? styles.open : styles.closed]}>
      <View style={[styles.dot, isOpen ? styles.dotOpen : styles.dotClosed]} />
      <Text style={[styles.text, isOpen ? styles.textOpen : styles.textClosed]}>
        {isOpen ? `Open · ${mealPeriod ?? ""}` : "Closed"}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: Radius.pill,
  },
  open: { backgroundColor: Colors.dining.light },
  closed: { backgroundColor: "#F1F3F5" },
  dot: { width: 6, height: 6, borderRadius: 3 },
  dotOpen: { backgroundColor: "#2D6A4F" },
  dotClosed: { backgroundColor: Colors.textMuted },
  text: { fontSize: 12, fontWeight: "500" },
  textOpen: { color: Colors.dining.primary },
  textClosed: { color: Colors.textMuted },
});
