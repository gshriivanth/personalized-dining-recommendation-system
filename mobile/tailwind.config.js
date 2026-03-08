/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        background: "#F8F9FA",
        surface: "#FFFFFF",
        border: "#E9ECEF",
        text: {
          DEFAULT: "#212529",
          muted: "#6C757D",
          inverted: "#FFFFFF",
        },
        dining: {
          primary: "#1B4332",
          accent: "#E9C46A",
          light: "#D8F3DC",
          surface: "#2D6A4F",
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
      },
      fontFamily: {
        sans: ["Inter", "system-ui"],
        mono: ["DM Mono", "monospace"],
      },
      borderRadius: {
        card: "16px",
        pill: "9999px",
      },
    },
  },
  plugins: [],
};
