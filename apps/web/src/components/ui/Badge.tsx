import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

type BadgeTone =
  | "neutral"
  | "brand"
  | "success"
  | "warning"
  | "danger"
  | "outline";

type BadgeProps = {
  tone?: BadgeTone;
  icon?: ReactNode;
  className?: string;
  children: ReactNode;
};

const toneClasses: Record<BadgeTone, string> = {
  neutral: "border-border-subtle bg-surface-subtle/70 text-content-secondary",
  brand: "border-brand-primary/35 bg-surface-accentSoft text-brand-primary",
  success: "border-status-success/35 bg-surface-successSoft text-status-success",
  warning: "border-status-warning/35 bg-surface-warningSoft text-status-warning",
  danger: "border-status-danger/35 bg-surface-dangerSoft text-status-danger",
  outline: "border-border-subtle bg-transparent text-content-secondary"
};

export function Badge({
  tone = "neutral",
  icon,
  className,
  children
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-chip border px-2.5 py-1 font-semibold uppercase tracking-[0.18em]",
        "text-[0.6875rem] leading-4",
        toneClasses[tone],
        className
      )}
    >
      {icon}
      {children}
    </span>
  );
}
