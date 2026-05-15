/*
 * Incident State Badge reusable UI component used by the React dashboard.
 */
import type { StatusTone } from "../../lib/theme/tokens";
import { StatusChip } from "./StatusChip";

// Defines the Incident State Badge Props data shape used by this frontend module.
type IncidentStateBadgeProps = {
  state: Exclude<StatusTone, "pending_response" | "disabled">;
};

// Renders the Incident State Badge UI section.
export function IncidentStateBadge({ state }: IncidentStateBadgeProps) {
  return <StatusChip status={state} />;
}
