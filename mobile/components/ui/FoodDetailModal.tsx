// components/ui/FoodDetailModal.tsx
// Bottom-sheet modal showing a full nutrition label for a food.
// Provides "Favorite" toggle and "Add to Log" actions.
import React, { useState } from "react";
import {
  Modal,
  View,
  Text,
  StyleSheet,
  Pressable,
  ScrollView,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useQueryClient } from "@tanstack/react-query";
import { Colors, Spacing, Radius, Typography } from "@/constants/theme";
import { useProfileStore } from "@/lib/store/profile";
import { addFavorite, removeFavorite, logMeal } from "@/lib/api/profile";
import type { RecommendationItem } from "@/lib/types/food";

const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"] as const;
type MealType = (typeof MEAL_TYPES)[number];

interface Props {
  item: RecommendationItem | null;
  visible: boolean;
  onClose: () => void;
}

export function FoodDetailModal({ item, visible, onClose }: Props) {
  const { favorites, addFavorite: storeFav, removeFavorite: storeUnfav } = useProfileStore();
  const queryClient = useQueryClient();

  const [selectedMealType, setSelectedMealType] = useState<MealType>("lunch");
  const [logging, setLogging] = useState(false);
  const [favLoading, setFavLoading] = useState(false);

  if (!item) return null;

  const { food, serving_size_g } = item;
  const compoundId = `${food.source}:${food.food_id}`;
  const isFavorited = favorites.has(compoundId);

  // Scale per-100g values to the serving size
  const s = serving_size_g / 100;
  const scale = (v: number | null) => (v != null ? +(v * s).toFixed(1) : null);
  const fmt = (v: number | null, dec = 1) =>
    v != null ? (dec === 0 ? Math.round(v).toString() : v.toFixed(dec)) : null;

  const cal = Math.round((food.calories ?? 0) * s);

  async function handleFavoriteToggle() {
    setFavLoading(true);
    try {
      if (isFavorited) {
        await removeFavorite(food.source, food.food_id);
        storeUnfav(compoundId);
      } else {
        await addFavorite(food.source, food.food_id, food.name);
        storeFav(compoundId);
      }
    } catch (err: any) {
      Alert.alert("Error", err.message ?? "Could not update favorite.");
    } finally {
      setFavLoading(false);
    }
  }

  async function handleAddToLog() {
    setLogging(true);
    try {
      await logMeal({
        source: food.source,
        food_id: food.food_id,
        food_name: food.name,
        serving_size_g,
        calories: (food.calories ?? 0) * s,
        protein: (food.protein ?? 0) * s,
        carbs: (food.carbs ?? 0) * s,
        fat: (food.fat ?? 0) * s,
        fiber: (food.fiber ?? 0) * s,
        meal_type: selectedMealType,
      });
      await queryClient.invalidateQueries({ queryKey: ["consumed-today"] });
      Alert.alert("Logged!", `${food.name} added to your ${selectedMealType} log.`);
      onClose();
    } catch (err: any) {
      Alert.alert("Error", err.message ?? "Could not log meal.");
    } finally {
      setLogging(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose} />
      <View style={styles.sheet}>
        <View style={styles.handle} />
        <Pressable style={styles.closeBtn} onPress={onClose}>
          <Ionicons name="close" size={22} color={Colors.textMuted} />
        </Pressable>

        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
          {/* Food name & brand */}
          <Text style={styles.foodName} numberOfLines={3}>{food.name}</Text>
          {food.brand ? <Text style={styles.brand}>{food.brand}</Text> : null}
          <Text style={styles.serving}>Per {serving_size_g}g serving</Text>

          {/* ── Nutrition Facts label ── */}
          <View style={styles.labelBox}>
            <Text style={styles.labelTitle}>Nutrition Facts</Text>
            <View style={styles.thickBar} />

            {/* Calories — large row */}
            <View style={styles.calRow}>
              <Text style={styles.calLabel}>Calories</Text>
              <Text style={styles.calValue}>{cal}</Text>
            </View>
            <View style={styles.thickBar} />

            <Text style={styles.dvNote}>% Daily Value*</Text>
            <View style={styles.divider} />

            <LabelRow label="Total Fat" value={fmt(scale(food.fat))} unit="g" indent={0} />
            <LabelRow label="Saturated Fat" value={fmt(scale(food.saturated_fat))} unit="g" indent={1} />
            <LabelRow label="Trans Fat" value={fmt(scale(food.trans_fat))} unit="g" indent={1} italic />
            <View style={styles.divider} />
            <LabelRow label="Cholesterol" value={fmt(scale(food.cholesterol), 0)} unit="mg" indent={0} />
            <View style={styles.divider} />
            <LabelRow label="Sodium" value={fmt(scale(food.sodium), 0)} unit="mg" indent={0} />
            <View style={styles.divider} />
            <LabelRow label="Total Carbohydrate" value={fmt(scale(food.carbs))} unit="g" indent={0} />
            <LabelRow label="Dietary Fiber" value={fmt(scale(food.fiber))} unit="g" indent={1} />
            <LabelRow label="Total Sugars" value={fmt(scale(food.sugars))} unit="g" indent={1} />
            {food.added_sugars != null && (
              <LabelRow label="Includes Added Sugars" value={fmt(scale(food.added_sugars))} unit="g" indent={2} />
            )}
            <View style={styles.divider} />
            <LabelRow label="Protein" value={fmt(scale(food.protein))} unit="g" indent={0} bold />

            <View style={styles.thickBar} />

            <LabelRow label="Vitamin D" value={fmt(scale(food.vitamin_d))} unit="mcg" indent={0} />
            <View style={styles.divider} />
            <LabelRow label="Calcium" value={fmt(scale(food.calcium), 0)} unit="mg" indent={0} />
            <View style={styles.divider} />
            <LabelRow label="Iron" value={fmt(scale(food.iron))} unit="mg" indent={0} />
            <View style={styles.divider} />
            <LabelRow label="Potassium" value={fmt(scale(food.potassium), 0)} unit="mg" indent={0} />

            <View style={styles.thickBar} />
            <Text style={styles.dvFooter}>
              * The % Daily Value tells you how much a nutrient in a serving of food contributes to a daily diet.
            </Text>
          </View>

          {/* Meal type selector */}
          <Text style={styles.sectionLabel}>Log as</Text>
          <View style={styles.mealTypeRow}>
            {MEAL_TYPES.map((mt) => (
              <Pressable
                key={mt}
                style={[styles.mealPill, selectedMealType === mt && styles.mealPillActive]}
                onPress={() => setSelectedMealType(mt)}
              >
                <Text style={[styles.mealPillText, selectedMealType === mt && styles.mealPillTextActive]}>
                  {mt.charAt(0).toUpperCase() + mt.slice(1)}
                </Text>
              </Pressable>
            ))}
          </View>

          {/* Action buttons */}
          <View style={styles.actions}>
            <Pressable
              style={[styles.logBtn, logging && styles.btnDisabled]}
              onPress={handleAddToLog}
              disabled={logging}
            >
              {logging ? (
                <ActivityIndicator color={Colors.textInverted} size="small" />
              ) : (
                <>
                  <Ionicons name="add-circle-outline" size={18} color={Colors.textInverted} />
                  <Text style={styles.logBtnText}>Add to Log</Text>
                </>
              )}
            </Pressable>

            <Pressable
              style={[styles.favBtn, isFavorited && styles.favBtnActive, favLoading && styles.btnDisabled]}
              onPress={handleFavoriteToggle}
              disabled={favLoading}
            >
              {favLoading ? (
                <ActivityIndicator color={isFavorited ? Colors.textInverted : Colors.explore.primary} size="small" />
              ) : (
                <>
                  <Ionicons
                    name={isFavorited ? "heart" : "heart-outline"}
                    size={18}
                    color={isFavorited ? Colors.textInverted : Colors.explore.primary}
                  />
                  <Text style={[styles.favBtnText, isFavorited && styles.favBtnTextActive]}>
                    {isFavorited ? "Favorited" : "Favorite"}
                  </Text>
                </>
              )}
            </Pressable>
          </View>
        </ScrollView>
      </View>
    </Modal>
  );
}

// A single row on the nutrition label
function LabelRow({
  label,
  value,
  unit,
  indent = 0,
  bold = false,
  italic = false,
}: {
  label: string;
  value: string | null;
  unit: string;
  indent?: 0 | 1 | 2;
  bold?: boolean;
  italic?: boolean;
}) {
  const display = value != null ? `${value}${unit}` : "N/A";
  return (
    <View style={[rowStyles.row, { paddingLeft: indent * 14 }]}>
      <Text style={[rowStyles.label, bold && rowStyles.bold, italic && rowStyles.italic]}>
        {label}
      </Text>
      <Text style={[rowStyles.value, bold && rowStyles.bold]}>{display}</Text>
    </View>
  );
}

const rowStyles = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 3,
  },
  label: { fontSize: 13, color: Colors.text, flex: 1, flexWrap: "wrap" },
  value: { fontSize: 13, color: Colors.text, marginLeft: 8 },
  bold: { fontWeight: "700" },
  italic: { fontStyle: "italic" },
});

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)" },
  sheet: {
    backgroundColor: Colors.surface,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: Spacing.md,
    paddingBottom: Spacing.xl,
    maxHeight: "88%",
  },
  handle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: Colors.border,
    alignSelf: "center",
    marginTop: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  closeBtn: { position: "absolute", top: Spacing.md, right: Spacing.md, padding: 4, zIndex: 1 },
  content: { paddingBottom: Spacing.lg },
  foodName: { ...Typography.heading, fontSize: 20, marginBottom: 2, paddingRight: 32 },
  brand: { ...Typography.label, marginBottom: 2 },
  serving: { fontSize: 12, color: Colors.textMuted, marginBottom: Spacing.md },
  labelBox: {
    borderWidth: 2,
    borderColor: Colors.text,
    borderRadius: 4,
    padding: Spacing.sm,
    marginBottom: Spacing.md,
  },
  labelTitle: { fontSize: 26, fontWeight: "900", color: Colors.text, lineHeight: 28 },
  thickBar: { height: 8, backgroundColor: Colors.text, marginVertical: 4 },
  calRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    paddingVertical: 4,
  },
  calLabel: { fontSize: 16, fontWeight: "700", color: Colors.text },
  calValue: { fontSize: 36, fontWeight: "900", color: Colors.text, lineHeight: 38 },
  dvNote: { fontSize: 11, fontWeight: "700", color: Colors.text, textAlign: "right", marginBottom: 2 },
  divider: { height: 1, backgroundColor: Colors.border, marginVertical: 1 },
  dvFooter: { fontSize: 10, color: Colors.textMuted, marginTop: 4, lineHeight: 13 },
  sectionLabel: { ...Typography.label, marginBottom: Spacing.xs, marginTop: 4 },
  mealTypeRow: { flexDirection: "row", gap: Spacing.xs, marginBottom: Spacing.md },
  mealPill: {
    flex: 1,
    paddingVertical: 6,
    borderRadius: Radius.pill,
    borderWidth: 1,
    borderColor: Colors.explore.primary,
    alignItems: "center",
  },
  mealPillActive: { backgroundColor: Colors.explore.primary },
  mealPillText: { fontSize: 12, color: Colors.explore.primary, fontWeight: "500" },
  mealPillTextActive: { color: Colors.textInverted, fontWeight: "700" },
  actions: { flexDirection: "row", gap: Spacing.sm },
  logBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    backgroundColor: Colors.explore.primary,
    borderRadius: Radius.pill,
    paddingVertical: Spacing.sm,
  },
  logBtnText: { color: Colors.textInverted, fontWeight: "600", fontSize: 14 },
  favBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    borderWidth: 1.5,
    borderColor: Colors.explore.primary,
    borderRadius: Radius.pill,
    paddingVertical: Spacing.sm,
  },
  favBtnActive: { backgroundColor: Colors.explore.primary, borderColor: Colors.explore.primary },
  favBtnText: { color: Colors.explore.primary, fontWeight: "600", fontSize: 14 },
  favBtnTextActive: { color: Colors.textInverted },
  btnDisabled: { opacity: 0.5 },
});
