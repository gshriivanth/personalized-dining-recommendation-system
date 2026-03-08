// app/(tabs)/profile.tsx — Profile and goals editor
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  ScrollView,
  Pressable,
  Alert,
} from "react-native";
import { router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { Colors, Spacing, Radius, Typography, Shadow } from "@/constants/theme";
import { useProfileStore } from "@/lib/store/profile";
import { updateGoals } from "@/lib/api/profile";
import { supabase } from "@/lib/supabase";
import type { NutritionGoals } from "@/lib/types/user";

const GOAL_FIELDS: { key: keyof NutritionGoals; label: string; unit: string }[] = [
  { key: "calories", label: "Calories", unit: "kcal" },
  { key: "protein", label: "Protein", unit: "g" },
  { key: "carbs", label: "Carbohydrates", unit: "g" },
  { key: "fat", label: "Fat", unit: "g" },
  { key: "fiber", label: "Fiber", unit: "g" },
];

export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const { name, goals, setGoals, reset } = useProfileStore();

  const [editedGoals, setEditedGoals] = useState<NutritionGoals>({ ...goals });
  const [saving, setSaving] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [memberSince, setMemberSince] = useState<string | null>(null);
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (data.user) {
        setEmail(data.user.email ?? null);
        if (data.user.created_at) {
          const d = new Date(data.user.created_at);
          setMemberSince(d.toLocaleDateString("en-US", { month: "long", year: "numeric" }));
        }
      }
    });
  }, []);

  async function handleLogout() {
    Alert.alert("Sign Out", "Are you sure you want to sign out?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Sign Out",
        style: "destructive",
        onPress: async () => {
          setLoggingOut(true);
          try {
            await supabase.auth.signOut();
            reset();
            router.replace("/(auth)/login");
          } catch (err: any) {
            Alert.alert("Error", err.message);
          } finally {
            setLoggingOut(false);
          }
        },
      },
    ]);
  }

  async function handleChangePassword() {
    if (!email) return;
    setChangingPassword(true);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email);
      if (error) throw error;
      Alert.alert(
        "Check your email",
        `A password reset link has been sent to ${email}.`
      );
    } catch (err: any) {
      Alert.alert("Error", err.message ?? "Could not send reset email.");
    } finally {
      setChangingPassword(false);
    }
  }

  function handleChange(key: keyof NutritionGoals, value: string) {
    const parsed = value === "" ? null : parseFloat(value);
    setEditedGoals((prev) => ({ ...prev, [key]: isNaN(parsed as number) ? null : parsed }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await updateGoals(editedGoals);
      setGoals(updated);
      Alert.alert("Saved", "Your goals have been updated.");
    } catch (err: any) {
      Alert.alert("Error", err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <ScrollView
      style={styles.root}
      contentContainerStyle={[styles.content, { paddingTop: insets.top + Spacing.md }]}
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.title}>Profile</Text>
      {name && <Text style={styles.name}>{name}</Text>}

      {/* Account Information */}
      <View style={[styles.section, styles.sectionSpacing]}>
        <Text style={styles.sectionTitle}>Account Information</Text>

        <View style={styles.infoRow}>
          <Ionicons name="mail-outline" size={16} color={Colors.textMuted} style={styles.infoIcon} />
          <View style={styles.infoTextGroup}>
            <Text style={styles.infoLabel}>Email</Text>
            <Text style={styles.infoValue}>{email ?? "—"}</Text>
          </View>
        </View>

        <View style={[styles.infoRow, { borderBottomWidth: 0 }]}>
          <Ionicons name="calendar-outline" size={16} color={Colors.textMuted} style={styles.infoIcon} />
          <View style={styles.infoTextGroup}>
            <Text style={styles.infoLabel}>Member since</Text>
            <Text style={styles.infoValue}>{memberSince ?? "—"}</Text>
          </View>
        </View>

        <Pressable
          style={[styles.changePasswordBtn, changingPassword && styles.saveBtnDisabled]}
          onPress={handleChangePassword}
          disabled={changingPassword || !email}
        >
          <Ionicons name="lock-closed-outline" size={15} color={Colors.explore.primary} />
          <Text style={styles.changePasswordText}>
            {changingPassword ? "Sending..." : "Send Password Reset Email"}
          </Text>
        </Pressable>
      </View>

      {/* Goals editor */}
      <View style={[styles.section, styles.sectionSpacing]}>
        <Text style={styles.sectionTitle}>Daily Nutrition Goals</Text>
        <Text style={styles.sectionHint}>
          Leave a field blank to exclude it from recommendations.
        </Text>

        {GOAL_FIELDS.map(({ key, label, unit }) => (
          <View key={key} style={styles.row}>
            <Text style={styles.label}>{label}</Text>
            <View style={styles.inputRow}>
              <TextInput
                style={styles.input}
                value={editedGoals[key] != null ? String(editedGoals[key]) : ""}
                onChangeText={(v) => handleChange(key, v)}
                keyboardType="decimal-pad"
                placeholder="—"
                placeholderTextColor={Colors.textMuted}
              />
              <Text style={styles.unit}>{unit}</Text>
            </View>
          </View>
        ))}

        <Pressable
          style={[styles.saveBtn, saving && styles.saveBtnDisabled]}
          onPress={handleSave}
          disabled={saving}
        >
          <Text style={styles.saveBtnText}>{saving ? "Saving..." : "Save Goals"}</Text>
        </Pressable>
      </View>

      <Pressable
        style={[styles.logoutBtn, loggingOut && styles.saveBtnDisabled]}
        onPress={handleLogout}
        disabled={loggingOut}
      >
        <Text style={styles.logoutBtnText}>{loggingOut ? "Signing out..." : "Sign Out"}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  content: { padding: Spacing.md, paddingBottom: Spacing.xl },
  title: { ...Typography.heading, marginBottom: 2 },
  name: { fontSize: 16, color: Colors.textMuted, marginBottom: Spacing.lg },
  section: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.card,
    padding: Spacing.md,
    ...Shadow.card,
  },
  sectionSpacing: { marginBottom: Spacing.md },
  sectionTitle: { ...Typography.subheading, marginBottom: 4 },
  sectionHint: { ...Typography.label, marginBottom: Spacing.md },
  // Account info rows
  infoRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    gap: Spacing.sm,
  },
  infoIcon: { width: 20 },
  infoTextGroup: { flex: 1 },
  infoLabel: { fontSize: 11, color: Colors.textMuted, marginBottom: 1 },
  infoValue: { fontSize: 14, color: Colors.text, fontWeight: "500" },
  changePasswordBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: Spacing.sm,
    paddingVertical: Spacing.xs,
  },
  changePasswordText: {
    fontSize: 13,
    color: Colors.explore.primary,
    fontWeight: "600",
  },
  // Goals rows
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  label: { fontSize: 14, color: Colors.text, flex: 1 },
  inputRow: { flexDirection: "row", alignItems: "center", gap: Spacing.xs },
  input: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Radius.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 6,
    fontSize: 14,
    width: 80,
    textAlign: "right",
    color: Colors.text,
  },
  unit: { fontSize: 12, color: Colors.textMuted, width: 32 },
  saveBtn: {
    marginTop: Spacing.md,
    backgroundColor: Colors.dining.primary,
    borderRadius: Radius.pill,
    padding: Spacing.sm,
    alignItems: "center",
  },
  saveBtnDisabled: { opacity: 0.5 },
  saveBtnText: { color: Colors.textInverted, fontWeight: "600" },
  logoutBtn: {
    marginTop: Spacing.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Radius.pill,
    padding: Spacing.sm,
    alignItems: "center",
  },
  logoutBtnText: { color: Colors.textMuted, fontWeight: "600" },
});
