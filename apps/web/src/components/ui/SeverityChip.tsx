import type { Severity } from "../../lib/theme/tokens";
import { Badge } from "./Badge";

type SeverityChipProps = {
  severity: Severity;
};

const severityToneMap: Record<
  Severity,
  "danger" | "warning" | "brand" | "neutral"
> = {
  critical: "danger",
  high: "warning",
  medium: "brand",
  low: "neutral"
};

export function SeverityChip({ severity }: SeverityChipProps) {
  return (
    <Badge tone={severityToneMap[severity]}>
      {severity === "critical" ? "Critical" : severity}
    </Badge>
  );
}
