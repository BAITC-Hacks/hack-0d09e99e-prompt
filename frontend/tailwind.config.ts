import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F5F7FA",
        card: "#FFFFFF",
        primary: {
          DEFAULT: "#004AC6",
          container: "#2563EB",
          fixed: "#DBE1FF",
        },
        secondary: {
          DEFAULT: "#4648D4",
          container: "#6063EE",
        },
        "ai-insight": {
          DEFAULT: "#6366F1",
          bg: "#EEF2FF",
          border: "#C7D2FE",
        },
        ink: {
          DEFAULT: "#0F172A",
          secondary: "#475569",
          muted: "#94A3B8",
        },
        line: {
          DEFAULT: "#E2E8F0",
          focus: "#2563EB",
        },
        surface: {
          low: "#EFF4FF",
          high: "#DCE9FF",
        },
        status: {
          safe: "#10B981",
          "safe-bg": "#ECFDF5",
          "safe-border": "#A7F3D0",
          warning: "#F59E0B",
          "warning-bg": "#FFFBEB",
          "warning-border": "#FDE68A",
          critical: "#EF4444",
          "critical-bg": "#FEF2F2",
          "critical-border": "#FECACA",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        card: "12px",
        control: "6px",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.02)",
        lift: "0 4px 6px -1px rgba(15, 23, 42, 0.06), 0 2px 4px -2px rgba(15, 23, 42, 0.04)",
        drawer: "0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.04)",
      },
    },
  },
  plugins: [],
};

export default config;
