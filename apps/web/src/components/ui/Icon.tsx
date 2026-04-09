import type { ReactNode } from "react";
import type { IconName } from "../../lib/theme/tokens";
import { cn } from "../../lib/cn";

type IconProps = {
  name: IconName;
  className?: string;
};

const iconPaths: Record<IconName, ReactNode> = {
  dashboard: (
    <path d="M4 4h7v7H4zM13 4h7v4h-7zM13 10h7v10h-7zM4 13h7v7H4z" />
  ),
  alerts: (
    <path d="M12 3 2.8 19a1 1 0 0 0 .86 1.5h16.68A1 1 0 0 0 21.2 19L12 3Zm0 5.5v4.5m0 4h.01" />
  ),
  incidents: (
    <path d="M12 3a8.5 8.5 0 0 0-8.5 8.5c0 4.9 3.43 8.1 7.12 9.2.88.26 1.76-.45 1.76-1.36V17m0 0a2 2 0 1 1 0-4m0 4a2 2 0 1 0 0-4m0 0V8.5" />
  ),
  endpoints: (
    <path d="M4 6h16v9H4zM8 18h8M10 15v3m4-3v3" />
  ),
  responses: (
    <path d="M4 12a8 8 0 0 0 14.56 4M20 12A8 8 0 0 0 5.44 8M4 4v4h4M20 20v-4h-4" />
  ),
  rules: (
    <path d="M6 4h12l2 4-8 12L4 8l2-4Zm3 4h6" />
  ),
  reports: (
    <path d="M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6" />
  ),
  settings: (
    <path d="m12 3 1.7 2.3 2.8.6.2 2.9 2 2-1.2 2.7 1.2 2.7-2 2-.2 2.9-2.8.6L12 21l-1.7-2.3-2.8-.6-.2-2.9-2-2 1.2-2.7L5.3 8l2-2 .2-2.9 2.8-.6L12 3Zm0 5.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" />
  ),
  shield: (
    <path d="M12 3 5 6v5c0 5 3 8.5 7 10 4-1.5 7-5 7-10V6l-7-3Z" />
  ),
  search: <path d="m21 21-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Z" />,
  filter: <path d="M4 6h16M7 12h10M10 18h4" />,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  "chevron-right": <path d="m9 6 6 6-6 6" />,
  spark: <path d="m12 2 1.8 5.2L19 9l-5.2 1.8L12 16l-1.8-5.2L5 9l5.2-1.8L12 2Z" />,
  activity: <path d="M3 12h4l2.5-5 3 10 2.5-5H21" />,
  health: <path d="M12 21s-7-4.35-7-10a4 4 0 0 1 7-2.65A4 4 0 0 1 19 11c0 5.65-7 10-7 10Z" />,
  clock: (
    <path d="M12 3.5a8.5 8.5 0 1 0 8.5 8.5A8.5 8.5 0 0 0 12 3.5Zm0 4.25v4.5l3 1.75" />
  ),
  server: (
    <path d="M4 5h16v5H4zM4 14h16v5H4zM8 7.5h.01M8 16.5h.01M13 7.5h5M13 16.5h5" />
  ),
  "check-circle": (
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14M22 4 12 14.01l-3-3" />
  ),
  warning: (
    <path d="M12 3 2.8 19a1 1 0 0 0 .86 1.5h16.68A1 1 0 0 0 21.2 19L12 3Zm0 6v4m0 4h.01" />
  ),
  "x-circle": (
    <path d="M12 22a10 10 0 1 1 10-10 10 10 0 0 1-10 10Zm-3-13 6 6m0-6-6 6" />
  ),
  logout: (
    <>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="m16 17 5-5-5-5" />
      <path d="M21 12H9" />
    </>
  )
};

export function Icon({ name, className }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("h-5 w-5 shrink-0", className)}
      aria-hidden="true"
    >
      {iconPaths[name]}
    </svg>
  );
}
