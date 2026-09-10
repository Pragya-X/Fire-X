import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          DEFAULT: "var(--color-base)",
          panel: "var(--color-base-panel)",
          raised: "var(--color-base-raised)",
          border: "var(--color-base-border)",
        },
        primary: "var(--color-text-primary)",
        secondary: "var(--color-text-secondary)",
        muted: "var(--color-text-muted)",
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