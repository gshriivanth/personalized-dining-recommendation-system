// app/(tabs)/explore/index.tsx
// Explore (non-dining) tab — navy header, search bar, personalized recommendations.
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  FlatList,
  Pressable,
  ActivityIndicator,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { Colors, Spacing, Radius, Typography } from "@/constants/theme";
import { RecommendationCard } from "@/components/ui/RecommendationCard";
import { useExploreRecommendations } from "@/hooks/useExploreRecommendations";

const MEAL_FILTERS = ["Any", "Breakfast", "Lunch", "Dinner", "Snack"] as const;

export default function ExploreScreen() {
  const insets = useSafeAreaInsets();
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState<string | undefined>(undefined);
  const [mealFilter, setMealFilter] = useState<string | undefined>(undefined);

  const { data, isLoading, error } = useExploreRecommendations(submittedQuery, mealFilter);

  function handleSearch() {
    setSubmittedQuery(query.trim() || undefined);
  }

  return (
    <View style={styles.root}>
      {/* Navy header */}
      <View style={[styles.header, { paddingTop: insets.top + Spacing.sm }]}>
        <Text style={styles.headerTitle}>Explore Foods</Text>
        <Text style={styles.headerSub}>Personalized picks beyond the dining hall</Text>

        {/* Search bar */}
        <View style={styles.searchRow}>
          <Ionicons name="search" size={16} color={Colors.textMuted} style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search foods..."
            placeholderTextColor={Colors.textMuted}
            value={query}
            onChangeText={setQuery}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
          {query.length > 0 && (
            <Pressable onPress={() => { setQuery(""); setSubmittedQuery(undefined); }}>
              <Ionicons name="close-circle" size={16} color={Colors.textMuted} />
            </Pressable>
          )}
        </View>

        {/* Meal type filter */}
        <View style={styles.filterRow}>
          {MEAL_FILTERS.map((f) => {
            const val = f === "Any" ? undefined : f.toLowerCase();
            const active = mealFilter === val;
            return (
              <Pressable
                key={f}
                style={[styles.filterPill, active && styles.filterPillActive]}
                onPress={() => setMealFilter(val)}
              >
                <Text style={[styles.filterText, active && styles.filterTextActive]}>{f}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* Results */}
      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={Colors.explore.primary} size="large" />
        </View>
      ) : error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error.message}</Text>
        </View>
      ) : (
        <FlatList
          data={data?.recommendations ?? []}
          keyExtractor={(item) => `${item.food.source}:${item.food.food_id}`}
          renderItem={({ item }) => <RecommendationCard item={item} variant="explore" />}
          contentContainerStyle={styles.list}
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyText}>
                {submittedQuery
                  ? `No results for "${submittedQuery}"`
                  : "Favorite a non-dining food to see it here, or search above"}
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  header: {
    backgroundColor: Colors.explore.primary,
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.md,
  },
  headerTitle: { ...Typography.heading, color: Colors.textInverted, marginBottom: 2 },
  headerSub: { fontSize: 13, color: "rgba(255,255,255,0.7)", marginBottom: Spacing.md },
  searchRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surface,
    borderRadius: Radius.input,
    paddingHorizontal: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  searchIcon: { marginRight: Spacing.xs },
  searchInput: { flex: 1, paddingVertical: 10, fontSize: 14, color: Colors.text },
  filterRow: { flexDirection: "row", gap: Spacing.xs, flexWrap: "wrap" },
  filterPill: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: Radius.pill,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.3)",
  },
  filterPillActive: { backgroundColor: Colors.explore.accent, borderColor: Colors.explore.accent },
  filterText: { color: "rgba(255,255,255,0.8)", fontSize: 12, fontWeight: "500" },
  filterTextActive: { color: Colors.explore.primary, fontWeight: "700" },
  list: { padding: Spacing.md },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: Spacing.xl },
  emptyText: { color: Colors.textMuted, fontSize: 14, textAlign: "center" },
  errorText: { color: "#E07A5F", fontSize: 14, textAlign: "center" },
});
