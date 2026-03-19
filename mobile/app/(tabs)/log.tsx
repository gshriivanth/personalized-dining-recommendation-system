// app/(tabs)/log.tsx — Meal log screen
import React, { useEffect } from "react";
import { View, Text, StyleSheet, FlatList, Pressable, Alert } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Colors, Spacing, Radius, Typography, Shadow } from "@/constants/theme";
import { getConsumedToday, deleteMealLog } from "@/lib/api/profile";
import { useProfileStore } from "@/lib/store/profile";
import type { MealLogEntry } from "@/lib/types/user";

export default function LogScreen() {
  const insets = useSafeAreaInsets();
  const { setConsumedToday } = useProfileStore();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["consumed-today"],
    queryFn: () => getConsumedToday(),
  });

  useEffect(() => {
    if (!data) return;
    setConsumedToday({
      calories: data.total_calories,
      protein: data.total_protein,
      carbs: data.total_carbs,
      fat: data.total_fat,
      fiber: data.total_fiber,
    });
  }, [data, setConsumedToday]);

  const deleteMutation = useMutation({
    mutationFn: deleteMealLog,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["consumed-today"] });
    },
  });

  function confirmDelete(item: MealLogEntry) {
    Alert.alert(
      "Remove from log?",
      `Remove "${item.food_name}" from today's log?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Remove",
          style: "destructive",
          onPress: () => deleteMutation.mutate(item.log_id),
        },
      ]
    );
  }

  const entries = data?.entries ?? [];

  function renderEntry({ item }: { item: MealLogEntry }) {
    return (
      <View style={styles.entry}>
        <View style={styles.entryLeft}>
          <Text style={styles.entryName}>{item.food_name}</Text>
          <Text style={styles.entryMeta}>
            {item.meal_type ?? ""}  ·  {item.serving_size_g}g
          </Text>
        </View>
        <View style={styles.entryRight}>
          <Text style={styles.entryCal}>{Math.round(item.calories)} kcal</Text>
          <Text style={styles.entryMacros}>
            P:{Math.round(item.protein)}g  C:{Math.round(item.carbs)}g  F:{Math.round(item.fat)}g
          </Text>
          <Pressable
            style={styles.deleteBtn}
            onPress={() => confirmDelete(item)}
            hitSlop={8}
          >
            <Ionicons name="trash-outline" size={16} color={Colors.textMuted} />
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.root}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + Spacing.sm }]}>
        <Text style={styles.title}>Meal Log</Text>
        {data && (
          <View style={styles.totalRow}>
            <Text style={styles.totalLabel}>Today:</Text>
            <Text style={styles.totalVal}>{Math.round(data.total_calories)} kcal</Text>
            <Text style={styles.totalSub}>
              P:{Math.round(data.total_protein)}g · C:{Math.round(data.total_carbs)}g · F:{Math.round(data.total_fat)}g
            </Text>
          </View>
        )}
      </View>

      {/* Log entries */}
      <FlatList
        data={entries}
        keyExtractor={(item) => item.log_id}
        renderItem={renderEntry}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="restaurant-outline" size={40} color={Colors.border} />
            <Text style={styles.emptyText}>No meals logged today</Text>
            <Text style={styles.emptyHint}>Tap a recommendation card to log a food</Text>
          </View>
        }
      />

      {/* FAB — placeholder for bottom sheet log */}
      <Pressable style={[styles.fab, { bottom: insets.bottom + Spacing.md }]}>
        <Ionicons name="add" size={28} color={Colors.textInverted} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  header: {
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  title: { ...Typography.heading, marginBottom: Spacing.sm },
  totalRow: { gap: 2 },
  totalLabel: { ...Typography.label },
  totalVal: { fontSize: 20, fontWeight: "700", color: Colors.dining.primary },
  totalSub: { fontSize: 12, color: Colors.textMuted },
  list: { padding: Spacing.md, gap: Spacing.sm },
  entry: {
    flexDirection: "row",
    justifyContent: "space-between",
    backgroundColor: Colors.surface,
    borderRadius: Radius.card,
    padding: Spacing.md,
    ...Shadow.card,
  },
  entryLeft: { flex: 1, marginRight: Spacing.sm },
  entryName: { ...Typography.subheading, fontSize: 14 },
  entryMeta: { fontSize: 12, color: Colors.textMuted, marginTop: 2 },
  entryRight: { alignItems: "flex-end" },
  entryCal: { fontSize: 14, fontWeight: "700", color: Colors.macro.calorie },
  entryMacros: { fontSize: 11, color: Colors.textMuted, marginTop: 2 },
  deleteBtn: { marginTop: 6, alignSelf: "flex-end" },
  empty: { alignItems: "center", gap: Spacing.sm, paddingTop: 80 },
  emptyText: { ...Typography.subheading, color: Colors.textMuted },
  emptyHint: { ...Typography.label, textAlign: "center" },
  fab: {
    position: "absolute",
    right: Spacing.lg,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.dining.primary,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: Colors.dining.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 6,
  },
});
