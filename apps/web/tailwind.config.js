/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        aegis: {
          orange: "#F97316",
          "orange-hover": "#EA580C",
          black: "#0A0A0A",
          panel: "#111827",
          border: "#1F2937",
          text: "#F9FAFB",
          soft: "#D1D5DB",
          muted: "#9CA3AF",
          danger: "#EF4444",
          success: "#22C55E",
          warning: "#F59E0B"
        }
      },
      boxShadow: {
        panel: "0 24px 60px rgba(0, 0, 0, 0.28)"
      }
    }
  },
  plugins: []
};

