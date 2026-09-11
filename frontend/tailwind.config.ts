import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          DEFAULT: "rgb(var(--rgb-base) / <alpha-value>)",
          panel: "rgb(var(--rgb-base-panel) / <alpha-value>)",
          raised: "rgb(var(--rgb-base-raised) / <alpha-value>)",
          border: "rgb(var(--rgb-base-border) / <alpha-value>)",
        },
        primary: "rgb(var(--rgb-primary) / <alpha-value>)",
        secondary: "rgb(var(--rgb-secondary) / <alpha-value>)",
        muted: "rgb(var(--rgb-muted) / <alpha-value>)",
        critical: "#dc2626",
        high: "#ea580c",
        moderate: "#d97706",
        low: "#16a34a",
        info: "#2563eb",
        accent: "#0284c7",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      boxShadow: {
        sm: "0 1px 2px rgba(15, 23, 42, 0.06)",
        md: "0 4px 6px rgba(15, 23, 42, 0.08)",
        panel: "0 8px 30px rgba(2, 8, 23, 0.25)",
      },
      animation: {
        fadeIn: "fadeIn 0.25s ease-out",
        pulseSlow: "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;