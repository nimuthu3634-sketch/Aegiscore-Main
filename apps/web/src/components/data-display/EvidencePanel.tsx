import type { ReactNode } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/Card";

type EvidencePanelProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  dataTestId?: string;
};

export function EvidencePanel({
  eyebrow,
  title,
  description,
  actions,
  children,
  dataTestId
}: EvidencePanelProps) {
  return (
    <Card className="h-full" data-testid={dataTestId}>
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
