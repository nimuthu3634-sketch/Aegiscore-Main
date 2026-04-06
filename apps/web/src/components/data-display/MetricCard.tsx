import type { ReactNode } from "react";
import { cn } from "../../lib/cn";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";

type MetricCardProps = {
  label: string;
  value: string;
  detail: string;
  trend?: ReactNode;
  tone?: "neutral" | "highlight" | "warning" | "danger";
  className?: string;
};

const toneClasses = {
  neutral: "border-border-subtle",
  highlight: "border-brand-primary/35",
  warning: "border-status-warning/35",
  danger: "border-status-danger/35"
} as const;

const toneIndicatorClasses = {
  neutral: "bg-slate-500",
  highlight: "bg-brand-primary",
  warning: "bg-status-warning",
  danger: "bg-status-danger"
} as const;

export function MetricCard({
  label,
  value,
  detail,
  trend,
  tone = "neutral",
  className
}: MetricCardProps) {
  return (
    <Card className={cn("h-full bg-white", toneClasses[tone], className)}>
      <CardHeader className="pb-4">
        <div className="space-y-2.5">
          <p className="type-label-md">{label}</p>
          <CardTitle className="text-[1.625rem] font-semibold leading-none text-content-primary">
            {value}
          </CardTitle>
        </div>
        <span
          className={cn(
            "mt-1 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
            toneIndicatorClasses[tone],
            tone === "neutral" ? "text-white/80" : "text-white"
          )}
          aria-hidden="true"
        >
          <span className="h-2 w-2 rounded-full bg-current" />
        </span>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="type-body-sm">{detail}</p>
        {trend ? <div className="mt-3">{trend}</div> : null}
      </CardContent>
    </Card>
  );
}
