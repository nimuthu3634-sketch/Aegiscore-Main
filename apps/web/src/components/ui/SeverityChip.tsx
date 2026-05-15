/*
 * Severity Chip reusable UI component used by the React dashboard.
 */
import type { Severity } from "../../lib/theme/tokens";
import { Badge } from "./Badge";

// Defines the Severity Chip Props data shape used by this frontend module.
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

// Renders the Severity Chip UI section.
export function SeverityChip({ severity }: SeverityChipProps) {
  return (
    <Badge tone={severityToneMap[severity]}>
      {severity === "critical" ? "Critical" : severity}
    </Badge>
  );
}
