import type { ReactNode } from "react";
import { Card, CardContent, CardHeader } from "../ui/Card";

type DetailHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  badges?: ReactNode;
  actions?: ReactNode;
  children?: ReactNode;
};

export function DetailHeader({
  eyebrow,
  title,
  description,
  badges,
  actions,
  children
}: DetailHeaderProps) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div className="space-y-4">
          {eyebrow ? <p className="type-label-md">{eyebrow}</p> : null}
          <div className="space-y-3">
            <h1 className="type-display-md">{title}</h1>
            {description ? <p className="max-w-3xl type-body-md">{description}</p> : null}
          </div>
          {badges ? <div className="flex flex-wrap gap-2">{badges}</div> : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
      </CardHeader>
      {children ? (
        <CardContent className="border-t border-border-subtle pt-5">
          {children}
        </CardContent>
      ) : null}
    </Card>
  );
}
