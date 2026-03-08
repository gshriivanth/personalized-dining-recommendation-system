// app/(auth)/onboarding.tsx
// 3-step onboarding: name → goal preset → confirmation.
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  Pressable,
  ScrollView,
  Alert,
} from "react-native";
import { router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Colors, Spacing, Radius, Typography } from "@/constants/theme";
import { useProfileStore } from "@/lib/store/profile";
import { createProfile } from "@/lib/api/profile";
import type { NutritionGoals } from "@/lib/types/user";

const GOAL_PRESETS: { label: string; description: string; goals: NutritionGoals }[] = [
  {
    label: "Balanced",
    description: "General healthy eating for a busy student",
    goals: { calories: 2000, protein: 100, carbs: 250, fat: 65, fiber: 28 },
  },
  {
    label: "High Protein",
    description: "Optimized for muscle building and recovery",
    goals: { calories: 2200, protein: 160, carbs: 220, fat: 65, fiber: 30 },
  },
  {
    label: "Light",
    description: "Lighter eating with a calorie deficit",
    goals: { calories: 1600, protein: 100, carbs: 180, fat: 50, fiber: 25 },
  },
];

type Step = 0 | 1 | 2;

export default function OnboardingScreen() {
  const insets = useSafeAreaInsets();
  const { setProfile } = useProfileStore();

  const [step, setStep] = useState<Step>(0);
  const [name, setName] = useState("");
  const [selectedPreset, setSelectedPreset] = useState(0);
  const [loading, setLoading] = useState(false);

  async function handleFinish() {
    if (!name.trim()) return;
    setLoading(true);
    try {
      const goals = GOAL_PRESETS[selectedPreset].goals;
      const profile = await createProfile(name.trim(), goals);
      setProfile(profile.user_id, profile.name, profile.goals);
      router.replace("/(tabs)");
    } catch (err: any) {
      Alert.alert("Error", err.message ?? "Could not create profile.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={[styles.root, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
      {/* Progress dots */}
      <View style={styles.dots}>
        {[0, 1, 2].map((i) => (
          <View key={i} style={[styles.dot, step === i && styles.dotActive]} />
        ))}
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {step === 0 && (
          <View style={styles.step}>
            <Text style={styles.heading}>What should we call you?</Text>
            <Text style={styles.sub}>Your name helps personalize recommendations.</Text>
            <TextInput
              style={styles.input}
              placeholder="Enter your name"
              value={name}
              onChangeText={setName}
              autoFocus
              returnKeyType="next"
              onSubmitEditing={() => name.trim() && setStep(1)}
            />
          </View>
        )}

        {step === 1 && (
          <View style={styles.step}>
            <Text style={styles.heading}>Choose your nutrition goal</Text>
            <Text style={styles.sub}>You can adjust this anytime in Profile.</Text>
            <View style={styles.presetList}>
              {GOAL_PRESETS.map((preset, i) => (
                <Pressable
                  key={i}
                  style={[styles.presetCard, selectedPreset === i && styles.presetCardSelected]}
                  onPress={() => setSelectedPreset(i)}
                >
                  <Text style={styles.presetLabel}>{preset.label}</Text>
                  <Text style={styles.presetDesc}>{preset.description}</Text>
                  <Text style={styles.presetMacros}>
                    {preset.goals.calories} kcal · {preset.goals.protein}g protein
                  </Text>
                </Pressable>
              ))}
            </View>
          </View>
        )}

        {step === 2 && (
          <View style={styles.step}>
            <Text style={styles.heading}>You're all set, {name}!</Text>
            <Text style={styles.sub}>
              We'll recommend foods from UCI dining halls and beyond — ranked for your goals,
              not just calories.
            </Text>
          </View>
        )}
      </ScrollView>

      {/* CTA button */}
      <View style={styles.footer}>
        <Pressable
          style={[styles.cta, loading && styles.ctaDisabled]}
          onPress={() => {
            if (step < 2) setStep((step + 1) as Step);
            else handleFinish();
          }}
          disabled={loading || (step === 0 && !name.trim())}
        >
          <Text style={styles.ctaText}>
            {step < 2 ? "Continue" : loading ? "Setting up..." : "Get Recommendations"}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  dots: { flexDirection: "row", justifyContent: "center", gap: 6, paddingTop: Spacing.lg },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: Colors.border },
  dotActive: { backgroundColor: Colors.dining.primary, width: 20 },
  content: { padding: Spacing.lg, paddingBottom: Spacing.xl },
  step: {},
  heading: { ...Typography.heading, marginBottom: Spacing.sm, fontSize: 26 },
  sub: { ...Typography.body, color: Colors.textMuted, marginBottom: Spacing.lg, lineHeight: 22 },
  input: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Radius.input,
    padding: Spacing.md,
    fontSize: 16,
    backgroundColor: Colors.surface,
  },
  presetList: { gap: Spacing.sm },
  presetCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.card,
    padding: Spacing.md,
    borderWidth: 2,
    borderColor: Colors.border,
  },
  presetCardSelected: { borderColor: Colors.dining.primary },
  presetLabel: { ...Typography.subheading, marginBottom: 2 },
  presetDesc: { ...Typography.body, color: Colors.textMuted, marginBottom: 4 },
  presetMacros: { fontSize: 12, color: Colors.dining.primary, fontWeight: "600" },
  footer: { padding: Spacing.lg },
  cta: {
    backgroundColor: Colors.dining.primary,
    borderRadius: Radius.pill,
    padding: Spacing.md,
    alignItems: "center",
  },
  ctaDisabled: { opacity: 0.5 },
  ctaText: { color: Colors.textInverted, fontWeight: "600", fontSize: 16 },
});
