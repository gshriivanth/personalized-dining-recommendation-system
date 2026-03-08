// app/_layout.tsx
// Root layout: sets up QueryClient, Supabase auth listener, safe area, and fonts.
// Unauthenticated users are redirected to (auth)/login.
// Authenticated users who haven't set goals go to (auth)/onboarding.
import "../global.css";
import { useCallback, useEffect, useState } from "react";
import { Stack, router } from "expo-router";
import { supabase } from "@/lib/supabase";
import type { Session } from "@supabase/supabase-js";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { useFonts } from "expo-font";
import * as SplashScreen from "expo-splash-screen";
import * as Linking from "expo-linking";
import { Alert } from "react-native";
import { useProfileStore } from "@/lib/store/profile";
import { getProfile } from "@/lib/api/profile";

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function RootLayout() {
  const { setProfile, reset } = useProfileStore();
  const [fontsLoaded] = useFonts({
    // Add custom fonts here when available.
    // "Inter-Regular": require("../assets/fonts/Inter-Regular.ttf"),
  });
  const [session, setSession] = useState<Session | null | undefined>(undefined);

  const handleAuthLink = useCallback(async (url: string | null) => {
    if (!url) return;

    const parseParams = (input: string) => {
      const params: Record<string, string> = {};
      if (!input) return params;
      for (const part of input.split("&")) {
        if (!part) continue;
        const [rawKey, rawValue] = part.split("=");
        const key = decodeURIComponent(rawKey ?? "");
        const value = decodeURIComponent(rawValue ?? "");
        if (key) params[key] = value;
      }
      return params;
    };

    const queryIndex = url.indexOf("?");
    const hashIndex = url.indexOf("#");
    const queryString =
      queryIndex >= 0 ? url.slice(queryIndex + 1, hashIndex >= 0 ? hashIndex : undefined) : "";
    const hashString = hashIndex >= 0 ? url.slice(hashIndex + 1) : "";
    const params = { ...parseParams(queryString), ...parseParams(hashString) };

    const errorMessage = params.error_description || params.error;
    if (errorMessage) {
      Alert.alert("Email confirmation failed", errorMessage.replace(/\+/g, " "));
      return;
    }

    const code = params.code;
    if (code) {
      const { error } = await supabase.auth.exchangeCodeForSession(code);
      if (error) {
        Alert.alert("Email confirmation failed", error.message);
      }
      return;
    }

    const accessToken = params.access_token;
    const refreshToken = params.refresh_token;
    if (accessToken && refreshToken) {
      const { error } = await supabase.auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken,
      });
      if (error) {
        Alert.alert("Email confirmation failed", error.message);
      }
    }
  }, []);

  async function syncProfileFromApi() {
    try {
      const profile = await getProfile();
      setProfile(profile.user_id, profile.name, profile.goals);
    } catch (error) {
      // If the profile isn't ready yet (e.g., unconfirmed user), don't block UI.
      console.warn("Profile sync skipped:", (error as Error).message);
    }
  }

  // Listen for Supabase auth state changes and redirect accordingly.
  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      if (data.session) {
        syncProfileFromApi();
      } else {
        reset();
      }
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, s) => {
      setSession(s);
      if (!s) {
        // Signed out — go to login
        reset();
        router.replace("/(auth)/login");
      } else {
        syncProfileFromApi();
      }
    });
    return () => listener.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    Linking.getInitialURL().then(handleAuthLink);
    const subscription = Linking.addEventListener("url", ({ url }) => handleAuthLink(url));
    return () => subscription.remove();
  }, [handleAuthLink]);

  useEffect(() => {
    if (fontsLoaded) SplashScreen.hideAsync();
  }, [fontsLoaded]);

  // Wait for both fonts and auth session to resolve before rendering
  if (!fontsLoaded || session === undefined) return null;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <StatusBar style="auto" />
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="(auth)" />
            <Stack.Screen name="(tabs)" />
          </Stack>
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
