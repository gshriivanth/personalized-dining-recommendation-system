// components/layout/ScreenHeader.tsx
import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Colors, Spacing, Typography } from "@/constants/theme";

interface Props {
  title: string;
  subtitle?: string;
  backgroundColor?: string;
  textColor?: string;
  right?: React.ReactNode;
}

export function ScreenHeader({
  title,
  subtitle,
  backgroundColor = Colors.surface,
  textColor = Colors.text,
  right,
}: Props) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.header, { backgroundColor, paddingTop: insets.top + Spacing.sm }]}>
      <View style={styles.content}>
        <View style={styles.titleRow}>
          <View style={styles.textGroup}>
            <Text style={[styles.title, { color: textColor }]}>{title}</Text>
            {subtitle && (
              <Text style={[styles.subtitle, { color: textColor, opacity: 0.7 }]}>
                {subtitle}
              </Text>
            )}
          </View>
          {right && <View>{right}</View>}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingBottom: Spacing.md,
    paddingHorizontal: Spacing.md,
  },
  content: {},
  titleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
  },
  textGroup: { flex: 1 },
  title: {
    ...Typography.heading,
  },
  subtitle: {
    ...Typography.label,
    marginTop: 2,
  },
});
