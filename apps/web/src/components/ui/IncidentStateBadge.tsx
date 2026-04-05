import type { StatusTone } from "../../lib/theme/tokens";
import { StatusChip } from "./StatusChip";

type IncidentStateBadgeProps = {
  state: Exclude<StatusTone, "pending_response" | "disabled">;
};

export function IncidentStateBadge({ state }: IncidentStateBadgeProps) {
  return <StatusChip status={state} />;
}
