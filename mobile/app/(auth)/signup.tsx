// app/(auth)/signup.tsx
import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { router } from "expo-router";
import * as Linking from "expo-linking";
import { supabase } from "@/lib/supabase";
import { Colors, Spacing, Radius, Typography } from "@/constants/theme";

export default function SignupScreen() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSignup() {
    if (!email || !password || !name) return;
    setLoading(true);
    const redirectUrl = Linking.createURL("/callback");
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        // Passed to the new user's raw_user_meta_data so the DB trigger
        // can populate profiles.name automatically.
        data: { name },
        // Redirect back into the app after email confirmation.
        emailRedirectTo: redirectUrl,
      },
    });
    setLoading(false);
    if (error) {
      Alert.alert("Sign up failed", error.message);
    } else {
      if (!data.session) {
        Alert.alert(
          "Check your email",
          "We sent a confirmation link. Please confirm your email, then return to finish setup."
        );
      }
      // After sign-up, go to onboarding to set nutrition goals.
      router.replace("/(auth)/onboarding");
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.content}>
        <Text style={styles.title}>Create account</Text>
        <Text style={styles.sub}>Personalized nutrition recommendations await</Text>

        <TextInput
          style={styles.input}
          placeholder="Your name"
          value={name}
          onChangeText={setName}
          autoCapitalize="words"
        />
        <TextInput
          style={styles.input}
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          autoComplete="email"
        />
        <TextInput
          style={styles.input}
          placeholder="Password (min 6 characters)"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoComplete="new-password"
        />

        <Pressable
          style={[styles.btn, loading && styles.btnDisabled]}
          onPress={handleSignup}
          disabled={loading}
        >
          <Text style={styles.btnText}>{loading ? "Creating account..." : "Sign Up"}</Text>
        </Pressable>

        <Pressable onPress={() => router.push("/(auth)/login")} style={styles.link}>
          <Text style={styles.linkText}>Already have an account? Sign in</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  content: { flex: 1, justifyContent: "center", padding: Spacing.lg, gap: Spacing.md },
  title: { ...Typography.heading, fontSize: 28 },
  sub: { ...Typography.label, marginBottom: Spacing.sm },
  input: {
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Radius.input,
    padding: Spacing.md,
    fontSize: 16,
    backgroundColor: Colors.surface,
    color: Colors.text,
  },
  btn: {
    backgroundColor: Colors.dining.primary,
    borderRadius: Radius.pill,
    padding: Spacing.md,
    alignItems: "center",
    marginTop: Spacing.sm,
  },
  btnDisabled: { opacity: 0.5 },
  btnText: { color: Colors.textInverted, fontWeight: "600", fontSize: 16 },
  link: { alignItems: "center", marginTop: Spacing.sm },
  linkText: { color: Colors.dining.primary, fontSize: 14 },
});
