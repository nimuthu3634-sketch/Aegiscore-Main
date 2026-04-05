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
  warning: "border-status-warning/30",
  danger: "border-status-danger/30"
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
    <Card className={cn("h-full", toneClasses[tone], className)}>
      <CardHeader className="pb-4">
        <div className="space-y-3">
          <p className="type-label-md">{label}</p>
          <CardTitle className="type-display-md">{value}</CardTitle>
        </div>
        {trend}
      </CardHeader>
      <CardContent className="pt-0">
        <p className="type-body-sm">{detail}</p>
      </CardContent>
    </Card>
  );
}
