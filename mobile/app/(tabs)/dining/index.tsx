// app/(tabs)/dining/index.tsx
// Dining Hall tab — navy header, hall toggle, meal period tabs, ranked recs.
import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Pressable,
  ActivityIndicator,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Colors, Spacing, Radius, Typography } from "@/constants/theme";
import { RecommendationCard } from "@/components/ui/RecommendationCard";
import { FoodDetailModal } from "@/components/ui/FoodDetailModal";
import { HallStatusBadge } from "@/components/ui/HallStatusBadge";
import { useDiningRecommendations } from "@/hooks/useDiningRecommendations";
import { useQuery } from "@tanstack/react-query";
import { fetchHalls } from "@/lib/api/dining";
import type { RecommendationItem } from "@/lib/types/food";

const HALLS = [
  { id: "brandywine", label: "Brandywine" },
  { id: "anteatery", label: "Anteatery" },
];

const MEAL_PERIODS = [
  { id: undefined, label: "Now" },
  { id: "breakfast", label: "Breakfast" },
  { id: "lunch", label: "Lunch" },
  { id: "dinner", label: "Dinner" },
] as const;

export default function DiningScreen() {
  const insets = useSafeAreaInsets();
  const [selectedHall, setSelectedHall] = useState("brandywine");
  const [selectedPeriod, setSelectedPeriod] = useState<string | undefined>(undefined);
  const [selectedItem, setSelectedItem] = useState<RecommendationItem | null>(null);

  const { data: halls } = useQuery({ queryKey: ["halls"], queryFn: fetchHalls });
  const hallStatus = halls?.find((h) => h.id === selectedHall);

  const { data, isLoading, error } = useDiningRecommendations(selectedHall, selectedPeriod);

  return (
    <View style={styles.root}>
      {/* Dark header */}
      <View style={[styles.header, { paddingTop: insets.top + Spacing.sm }]}>
        <View style={styles.headerRow}>
          <Text style={styles.headerTitle}>Dining Hall</Text>
          {hallStatus && (
            <HallStatusBadge
              isOpen={hallStatus.is_open}
              mealPeriod={hallStatus.current_meal_period}
            />
          )}
        </View>

        {/* Hall toggle */}
        <View style={styles.hallToggle}>
          {HALLS.map((hall) => (
            <Pressable
              key={hall.id}
              style={[styles.hallBtn, selectedHall === hall.id && styles.hallBtnActive]}
              onPress={() => setSelectedHall(hall.id)}
            >
              <Text style={[styles.hallBtnText, selectedHall === hall.id && styles.hallBtnTextActive]}>
                {hall.label}
              </Text>
            </Pressable>
          ))}
        </View>

        {/* Meal period pills */}
        <View style={styles.periodRow}>
          {MEAL_PERIODS.map((p) => (
            <Pressable
              key={String(p.id)}
              style={[styles.periodPill, selectedPeriod === p.id && styles.periodPillActive]}
              onPress={() => setSelectedPeriod(p.id as string | undefined)}
            >
              <Text style={[styles.periodText, selectedPeriod === p.id && styles.periodTextActive]}>
                {p.label}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      {/* Recommendations list */}
      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={Colors.dining.primary} size="large" />
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error.message}</Text>
        </View>
      ) : (
        <FlatList
          data={data?.recommendations ?? []}
          keyExtractor={(item) => `${item.food.source}:${item.food.food_id}`}
          renderItem={({ item }) => (
            <RecommendationCard
              item={item}
              variant="dining"
              onPress={() => setSelectedItem(item)}
            />
          )}
          contentContainerStyle={styles.list}
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyText}>No recommendations available right now.</Text>
            </View>
          }
        />
      )}

      <FoodDetailModal
        item={selectedItem}
        visible={selectedItem !== null}
        onClose={() => setSelectedItem(null)}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  header: {
    backgroundColor: Colors.dining.primary,
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.md,
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: Spacing.md,
  },
  headerTitle: { ...Typography.heading, color: Colors.textInverted },
  hallToggle: {
    flexDirection: "row",
    backgroundColor: Colors.dining.surface,
    borderRadius: Radius.pill,
    padding: 3,
    marginBottom: Spacing.sm,
  },
  hallBtn: {
    flex: 1,
    paddingVertical: 6,
    borderRadius: Radius.pill,
    alignItems: "center",
  },
  hallBtnActive: { backgroundColor: Colors.dining.accent },
  hallBtnText: { color: Colors.textInverted, fontSize: 13, fontWeight: "500" },
  hallBtnTextActive: { color: Colors.dining.primary, fontWeight: "700" },
  periodRow: { flexDirection: "row", gap: Spacing.xs },
  periodPill: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: Radius.pill,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.3)",
  },
  periodPillActive: { backgroundColor: Colors.dining.accent, borderColor: Colors.dining.accent },
  periodText: { color: "rgba(255,255,255,0.8)", fontSize: 12, fontWeight: "500" },
  periodTextActive: { color: Colors.dining.primary, fontWeight: "700" },
  list: { padding: Spacing.md },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: Spacing.xl },
  emptyText: { color: Colors.textMuted, fontSize: 14 },
  errorText: { color: "#E07A5F", fontSize: 14, textAlign: "center" },
});
