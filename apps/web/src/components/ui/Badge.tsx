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
  neutral: "border-border-subtle bg-surface-subtle text-content-secondary",
  brand: "border-brand-primary/35 bg-brand-primary/10 text-brand-hover",
  success: "border-status-success/35 bg-status-success/10 text-status-success",
  warning: "border-status-warning/35 bg-status-warning/12 text-status-warning",
  danger: "border-status-danger/35 bg-status-danger/12 text-status-danger",
  outline: "border-border-subtle bg-white text-content-secondary"
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
