import type { Severity } from "../../lib/theme/tokens";
import { SeverityChip } from "./SeverityChip";

type PriorityChipProps = {
  priority: Severity;
};

export function PriorityChip({ priority }: PriorityChipProps) {
  return <SeverityChip severity={priority} />;
}
