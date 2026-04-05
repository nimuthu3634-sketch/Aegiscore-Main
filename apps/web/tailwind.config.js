import defaultTheme from "tailwindcss/defaultTheme";

function withOpacity(variableName) {
  return `rgb(var(${variableName}) / <alpha-value>)`;
}

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: withOpacity("--color-brand-primary"),
          hover: withOpacity("--color-brand-hover")
        },
        surface: {
          base: withOpacity("--color-bg-base"),
          panel: withOpacity("--color-bg-panel"),
          raised: withOpacity("--color-surface-raised"),
          subtle: withOpacity("--color-surface-subtle"),
          overlay: withOpacity("--color-surface-overlay"),
          accentSoft: withOpacity("--color-surface-accent-soft"),
          successSoft: withOpacity("--color-surface-success-soft"),
          warningSoft: withOpacity("--color-surface-warning-soft"),
          dangerSoft: withOpacity("--color-surface-danger-soft")
        },
        border: {
          subtle: withOpacity("--color-border-default")
        },
        content: {
          primary: withOpacity("--color-text-primary"),
          secondary: withOpacity("--color-text-secondary"),
          muted: withOpacity("--color-text-muted")
        },
        status: {
          danger: withOpacity("--color-status-danger"),
          success: withOpacity("--color-status-success"),
          warning: withOpacity("--color-status-warning")
        }
      },
      fontFamily: {
        sans: ["Inter", ...defaultTheme.fontFamily.sans],
        display: ["Space Grotesk", ...defaultTheme.fontFamily.sans],
        mono: ["JetBrains Mono", ...defaultTheme.fontFamily.mono]
      },
      fontSize: {
        "display-lg": [
          "2.5rem",
          { lineHeight: "3rem", letterSpacing: "-0.03em", fontWeight: "600" }
        ],
        "display-md": [
          "2rem",
          { lineHeight: "2.5rem", letterSpacing: "-0.03em", fontWeight: "600" }
        ],
        "heading-lg": ["1.5rem", { lineHeight: "2rem", fontWeight: "600" }],
        "heading-md": ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
        "heading-sm": ["1rem", { lineHeight: "1.5rem", fontWeight: "600" }],
        "body-md": ["0.875rem", { lineHeight: "1.375rem", fontWeight: "400" }],
        "body-sm": ["0.8125rem", { lineHeight: "1.25rem", fontWeight: "400" }],
        "label-md": [
          "0.75rem",
          { lineHeight: "1rem", letterSpacing: "0.16em", fontWeight: "600" }
        ],
        "label-sm": [
          "0.6875rem",
          { lineHeight: "1rem", letterSpacing: "0.16em", fontWeight: "600" }
        ],
        "mono-md": ["0.8125rem", { lineHeight: "1.25rem", fontWeight: "500" }],
        "mono-sm": ["0.75rem", { lineHeight: "1.125rem", fontWeight: "500" }]
      },
      spacing: {
        toolbar: "1rem",
        panel: "1.5rem",
        section: "2rem",
        "section-lg": "2.5rem",
        shell: "3rem",
        sidebar: "16.5rem",
        topnav: "4rem"
      },
      borderRadius: {
        chip: "0.375rem",
        field: "0.625rem",
        panel: "0.875rem",
        shell: "1.125rem"
      },
      boxShadow: {
        panel: "0 10px 30px rgba(0, 0, 0, 0.28)",
        float: "0 18px 40px rgba(0, 0, 0, 0.38)",
        modal: "0 24px 64px rgba(0, 0, 0, 0.46)",
        focus:
          "0 0 0 1px rgba(249, 115, 22, 0.65), 0 0 0 4px rgba(249, 115, 22, 0.16)"
      },
      backgroundImage: {
        shell:
          "radial-gradient(circle at top, rgba(249, 115, 22, 0.18), transparent 24%), linear-gradient(180deg, rgba(17, 24, 39, 0.92) 0%, #0A0A0A 46%, #050505 100%)",
        "panel-grid":
          "linear-gradient(rgba(156, 163, 175, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(156, 163, 175, 0.08) 1px, transparent 1px)"
      },
      backgroundSize: {
        grid: "22px 22px"
      },
      maxWidth: {
        shell: "90rem"
      },
      gridTemplateColumns: {
        shell: "minmax(240px, 264px) minmax(0, 1fr)"
      }
    }
  },
  plugins: []
};
