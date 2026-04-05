import type { ReactNode } from "react";
import { cn } from "../../lib/cn";
import { Card } from "../ui/Card";
import { Icon } from "../ui/Icon";

type ErrorStateTone = "danger" | "warning";

type ErrorStateProps = {
  title: string;
  description: string;
  details?: string;
  action?: ReactNode;
  tone?: ErrorStateTone;
};

const toneClasses: Record<ErrorStateTone, string> = {
  danger: "border-status-danger/30 bg-surface-dangerSoft/40",
  warning: "border-status-warning/30 bg-surface-warningSoft/40"
};

export function ErrorState({
  title,
  description,
  details,
  action,
  tone = "danger"
}: ErrorStateProps) {
  return (
    <Card className={cn("flex flex-col gap-4 p-panel", toneClasses[tone])}>
      <div className="flex items-start gap-4">
        <span
          className={cn(
            "inline-flex h-11 w-11 items-center justify-center rounded-2xl border",
            tone === "danger"
              ? "border-status-danger/35 text-status-danger"
              : "border-status-warning/35 text-status-warning"
          )}
        >
          <Icon name={tone === "danger" ? "x-circle" : "warning"} />
        </span>
        <div className="space-y-2">
          <h3 className="type-heading-sm">{title}</h3>
          <p className="type-body-sm">{description}</p>
          {details ? <p className="type-mono-sm">{details}</p> : null}
        </div>
      </div>
      {action}
    </Card>
  );
}
