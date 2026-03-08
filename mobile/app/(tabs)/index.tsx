// app/(tabs)/index.tsx — Home / Dashboard
import React from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Pressable,
} from "react-native";
import { router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Colors, Spacing, Radius, Typography, Shadow } from "@/constants/theme";
import { NutrientBar } from "@/components/ui/NutrientBar";
import { RecommendationCard } from "@/components/ui/RecommendationCard";
import { useProfileStore } from "@/lib/store/profile";
import { useDiningRecommendations } from "@/hooks/useDiningRecommendations";
import { useExploreRecommendations } from "@/hooks/useExploreRecommendations";

export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const { name, goals, consumedToday } = useProfileStore();

  const { data: diningData } = useDiningRecommendations("brandywine");
  const { data: exploreData } = useExploreRecommendations();

  const topDining = diningData?.recommendations[0];
  const topExplore = exploreData?.recommendations[0];

  return (
    <ScrollView
      style={styles.root}
      contentContainerStyle={[styles.content, { paddingTop: insets.top + Spacing.md }]}
      showsVerticalScrollIndicator={false}
    >
      {/* Greeting */}
      <Text style={styles.greeting}>Good {getTimeOfDay()}, {name ?? "there"}</Text>
      <Text style={styles.sub}>Here's where you stand today</Text>

      {/* Daily macro progress */}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Today's Progress</Text>
        <NutrientBar
          label="Calories"
          consumed={consumedToday.calories}
          goal={goals.calories}
          color={Colors.macro.calorie}
          unit="kcal"
        />
        <NutrientBar
          label="Protein"
          consumed={consumedToday.protein}
          goal={goals.protein}
          color={Colors.macro.protein}
        />
        <NutrientBar
          label="Carbs"
          consumed={consumedToday.carbs}
          goal={goals.carbs}
          color={Colors.macro.carbs}
        />
        <NutrientBar
          label="Fat"
          consumed={consumedToday.fat}
          goal={goals.fat}
          color={Colors.macro.fat}
        />
      </View>

      {/* Dining Hall preview */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>From Dining Hall</Text>
        <Pressable onPress={() => router.push("/(tabs)/dining")}>
          <Text style={[styles.seeAll, { color: Colors.dining.primary }]}>See all</Text>
        </Pressable>
      </View>
      {topDining ? (
        <RecommendationCard
          item={topDining}
          variant="dining"
          onPress={() => router.push("/(tabs)/dining")}
        />
      ) : (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>No dining recommendations available</Text>
        </View>
      )}

      {/* Explore preview */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>For You to Explore</Text>
        <Pressable onPress={() => router.push("/(tabs)/explore")}>
          <Text style={[styles.seeAll, { color: Colors.explore.primary }]}>See all</Text>
        </Pressable>
      </View>
      {topExplore ? (
        <RecommendationCard
          item={topExplore}
          variant="explore"
          onPress={() => router.push("/(tabs)/explore")}
        />
      ) : (
        <View style={styles.emptyCard}>
          <Text style={styles.emptyText}>No explore recommendations available</Text>
        </View>
      )}
    </ScrollView>
  );
}

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return "morning";
  if (h < 17) return "afternoon";
  return "evening";
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  content: { padding: Spacing.md, paddingBottom: Spacing.xl },
  greeting: { ...Typography.heading, fontSize: 24, marginBottom: 2 },
  sub: { ...Typography.label, marginBottom: Spacing.lg },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.card,
    padding: Spacing.md,
    marginBottom: Spacing.lg,
    ...Shadow.card,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: Spacing.sm,
  },
  sectionTitle: { ...Typography.subheading },
  seeAll: { fontSize: 13, fontWeight: "600" },
  emptyCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.card,
    padding: Spacing.md,
    alignItems: "center",
    marginBottom: Spacing.lg,
    ...Shadow.card,
  },
  emptyText: { color: Colors.textMuted, fontSize: 13 },
});
