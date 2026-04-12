export type NavKey =
  | "overview"
  | "alerts"
  | "incidents"
  | "assets"
  | "responses"
  | "rules"
  | "reports"
  | "settings";

export type IconName =
  | "dashboard"
  | "alerts"
  | "incidents"
  | "endpoints"
  | "responses"
  | "rules"
  | "reports"
  | "settings"
  | "shield"
  | "search"
  | "filter"
  | "menu"
  | "close"
  | "chevron-right"
  | "spark"
  | "activity"
  | "health"
  | "clock"
  | "server"
  | "check-circle"
  | "warning"
  | "x-circle"
  | "logout";

export type Severity = "critical" | "high" | "medium" | "low";
export type StatusTone =
  | "new"
  | "triaged"
  | "investigating"
  | "contained"
  | "resolved"
  | "false_positive"
  | "pending_response"
  | "failed"
  | "disabled";

export type HealthTone = "healthy" | "degraded" | "down";

export type NavigationItem = {
  id: NavKey;
  label: string;
  shortLabel: string;
  icon: IconName;
  path: string;
  badgeCount?: number;
};

export const themeTokens = {
  colors: {
    brandPrimary: "#F97316",
    brandHover: "#EA580C",
    brandInk: "#F9FAFB",
    brandDivider: "#4B5563",
    brandGlow: "#FB923C",
    bgBase: "#0A0A0A",
    bgPanel: "#111827",
    borderDefault: "#1F2937",
    textPrimary: "#F9FAFB",
    textSecondary: "#D1D5DB",
    textMuted: "#9CA3AF",
    danger: "#EF4444",
    success: "#22C55E",
    warning: "#F59E0B"
  },
  spacing: {
    toolbar: "1rem",
    panel: "1.5rem",
    section: "2rem",
    sectionLg: "2.5rem",
    shell: "3rem"
  },
  radius: {
    chip: "0.375rem",
    field: "0.625rem",
    panel: "0.875rem",
    shell: "1.125rem"
  }
} as const;

export const primaryNavigation: NavigationItem[] = [
  {
    id: "overview",
    label: "Overview Dashboard",
    shortLabel: "Overview",
    icon: "dashboard",
    path: "/overview"
  },
  {
    id: "alerts",
    label: "Alerts",
    shortLabel: "Alerts",
    icon: "alerts",
    path: "/alerts"
  },
  {
    id: "incidents",
    label: "Incidents Queue",
    shortLabel: "Incidents",
    icon: "incidents",
    path: "/incidents"
  },
  {
    id: "assets",
    label: "Assets / Endpoints",
    shortLabel: "Assets",
    icon: "endpoints",
    path: "/assets"
  },
  {
    id: "responses",
    label: "Response History",
    shortLabel: "Responses",
    icon: "responses",
    path: "/responses"
  },
  {
    id: "rules",
    label: "Rules / Policies",
    shortLabel: "Rules",
    icon: "rules",
    path: "/rules"
  },
  {
    id: "reports",
    label: "Reports",
    shortLabel: "Reports",
    icon: "reports",
    path: "/reports"
  },
  {
    id: "settings",
    label: "Settings",
    shortLabel: "Settings",
    icon: "settings",
    path: "/settings"
  }
];

export const analystNavigation = primaryNavigation.filter((item) =>
  ["overview", "alerts", "incidents", "assets", "responses", "rules", "reports"].includes(item.id)
);

export const navPathById = primaryNavigation.reduce<Record<NavKey, string>>(
  (paths, item) => {
    paths[item.id] = item.path;
    return paths;
  },
  {
    overview: "/overview",
    alerts: "/alerts",
    incidents: "/incidents",
    assets: "/assets",
    responses: "/responses",
    rules: "/rules",
    reports: "/reports",
    settings: "/settings"
  }
);

export const pageBlueprints: Record<
  NavKey,
  { eyebrow: string; title: string; description: string }
> = {
  overview: {
    eyebrow: "SOC overview",
    title: "Overview Dashboard",
    description:
      "At-a-glance posture for the academic MVP threat scope (four core categories): volume, risk, incidents, responses, and affected assets—built for a centralized SOC platform MVP console."
  },
  alerts: {
    eyebrow: "Normalized alerts",
    title: "Alerts",
    description:
      "Wazuh and Suricata detect in-scope threats; optional AI prioritizes (Low/Medium/High). Triage brute force, FIM, port scan, and unauthorized user creation—sort by risk when the queue is busy."
  },
  incidents: {
    eyebrow: "Investigation queue",
    title: "Incidents Queue",
    description:
      "Grouped investigations with state, priority, and linked alerts—drive each case from triage to resolution."
  },
  assets: {
    eyebrow: "Asset inventory",
    title: "Assets / Endpoints",
    description:
      "Endpoints carrying alert load for the four validated threat categories. Use this to see which hosts need attention alongside incidents."
  },
  responses: {
    eyebrow: "Action history",
    title: "Response History",
    description:
      "What the platform already did: policy-driven dry-run or live actions with outcomes you can audit."
  },
  rules: {
    eyebrow: "Detection scope",
    title: "Rules / Policies",
    description:
      "Automation rules for the academic MVP four-category scope only—tune enablement and modes; broader detections are roadmap-only."
  },
  reports: {
    eyebrow: "Operational reporting",
    title: "Reports",
    description:
      "Summaries and exports for the same four-category activity you see in the queues—ideal for demos and handoffs."
  },
  settings: {
    eyebrow: "Platform configuration",
    title: "Settings",
    description:
      "Single-tenant integration, auth, notification, and retention settings owned by the backend platform."
  }
};
