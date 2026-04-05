import type { ReactNode } from "react";
import { cn } from "../../lib/cn";
import { Card, CardContent } from "../ui/Card";

type ChartCardProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
};

export function ChartCard({
  eyebrow,
  title,
  description,
  actions,
  footer,
  children,
  className,
  bodyClassName
}: ChartCardProps) {
  return (
    <Card className={cn("h-full", className)}>
      <div className="flex flex-wrap items-start justify-between gap-4 p-panel">
        <div className="space-y-2">
          {eyebrow ? <p className="type-label-md">{eyebrow}</p> : null}
          <h3 className="type-heading-md">{title}</h3>
          {description ? <p className="type-body-sm">{description}</p> : null}
        </div>
        {actions}
      </div>
      <CardContent className={cn("pt-0", bodyClassName)}>{children}</CardContent>
      {footer ? (
        <div className="border-t border-border-subtle px-panel py-4">{footer}</div>
      ) : null}
    </Card>
  );
}
