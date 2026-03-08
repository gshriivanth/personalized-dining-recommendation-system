// app/(auth)/login.tsx
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
import { supabase } from "@/lib/supabase";
import * as Linking from "expo-linking";
import { Colors, Spacing, Radius, Typography } from "@/constants/theme";

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  async function handleLogin() {
    if (!email || !password) return;
    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) {
      Alert.alert("Sign in failed", error.message);
    } else {
      router.replace("/(tabs)");
    }
  }

  async function handleResendConfirmation() {
    if (!email) {
      Alert.alert("Enter your email", "Please enter the email you signed up with.");
      return;
    }
    setResending(true);
    const { error } = await supabase.auth.resend({
      type: "signup",
      email,
      options: { emailRedirectTo: Linking.createURL("/callback") },
    });
    setResending(false);
    if (error) {
      Alert.alert("Resend failed", error.message);
    } else {
      Alert.alert("Email sent", "Check your inbox for a new confirmation link.");
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.content}>
        <Text style={styles.title}>Welcome back</Text>
        <Text style={styles.sub}>Sign in to your UCI Dining account</Text>

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
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoComplete="password"
        />

        <Pressable
          style={[styles.btn, loading && styles.btnDisabled]}
          onPress={handleLogin}
          disabled={loading}
        >
          <Text style={styles.btnText}>{loading ? "Signing in..." : "Sign In"}</Text>
        </Pressable>

        <Pressable
          onPress={handleResendConfirmation}
          disabled={resending}
          style={styles.link}
        >
          <Text style={styles.linkText}>
            {resending ? "Sending confirmation..." : "Resend confirmation email"}
          </Text>
        </Pressable>

        <Pressable onPress={() => router.push("/(auth)/signup")} style={styles.link}>
          <Text style={styles.linkText}>Don't have an account? Sign up</Text>
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
