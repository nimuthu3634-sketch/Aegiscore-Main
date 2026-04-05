import type { ReactNode } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/Card";

type EvidencePanelProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function EvidencePanel({
  eyebrow,
  title,
  description,
  actions,
  children
}: EvidencePanelProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          {eyebrow ? <p className="type-label-md">{eyebrow}</p> : null}
          <CardTitle className="mt-2">{title}</CardTitle>
          {description ? <CardDescription className="mt-2">{description}</CardDescription> : null}
        </div>
        {actions}
      </CardHeader>
      <CardContent className="pt-0">{children}</CardContent>
    </Card>
  );
}
