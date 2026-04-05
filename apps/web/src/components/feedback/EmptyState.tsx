import type { ReactNode } from "react";
import { Card } from "../ui/Card";
import { Icon } from "../ui/Icon";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
  iconName?: "shield" | "reports" | "alerts" | "incidents" | "endpoints";
};

export function EmptyState({
  title,
  description,
  action,
  iconName = "shield"
}: EmptyStateProps) {
  return (
    <Card className="flex flex-col items-start gap-4 p-panel">
      <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl border border-brand-primary/20 bg-surface-accentSoft text-brand-primary">
        <Icon name={iconName} />
      </span>
      <div className="space-y-2">
        <h3 className="type-heading-sm">{title}</h3>
        <p className="type-body-sm max-w-xl">{description}</p>
      </div>
      {action}
    </Card>
  );
}
