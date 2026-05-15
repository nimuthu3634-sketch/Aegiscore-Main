/*
 * Priority Chip reusable UI component used by the React dashboard.
 */
import type { Severity } from "../../lib/theme/tokens";
import { SeverityChip } from "./SeverityChip";

// Defines the Priority Chip Props data shape used by this frontend module.
type PriorityChipProps = {
  priority: Severity;
};

// Renders the Priority Chip UI section.
export function PriorityChip({ priority }: PriorityChipProps) {
  return <SeverityChip severity={priority} />;
}
