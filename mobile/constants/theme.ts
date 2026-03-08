// constants/theme.ts
// Single source of truth for design tokens.
// These mirror tailwind.config.js for use in StyleSheet and dynamic styles.

export const Colors = {
  background: "#F8F9FA",
  surface: "#FFFFFF",
  border: "#E9ECEF",
  text: "#212529",
  textMuted: "#6C757D",
  textInverted: "#FFFFFF",

  dining: {
    primary: "#023E8A",
    accent: "#74C69D",
    light: "#E0F0FF",
    surface: "#0353A4",
  },

  explore: {
    primary: "#023E8A",
    accent: "#74C69D",
    light: "#E0F0FF",
    surface: "#0353A4",
  },

  macro: {
    calorie: "#F4A261",
    protein: "#2D6A4F",
    carbs: "#457B9D",
    fat: "#E07A5F",
    fiber: "#8D99AE",
  },
} as const;

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

export const Radius = {
  card: 16,
  pill: 100,
  input: 10,
  sm: 8,
} as const;

export const Shadow = {
  card: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
} as const;

export const Typography = {
  heading: { fontSize: 22, fontWeight: "600" as const, color: Colors.text },
  subheading: { fontSize: 16, fontWeight: "600" as const, color: Colors.text },
  body: { fontSize: 14, fontWeight: "400" as const, color: Colors.text },
  label: { fontSize: 12, fontWeight: "500" as const, color: Colors.textMuted },
  macro: { fontSize: 13, fontWeight: "600" as const },
} as const;
