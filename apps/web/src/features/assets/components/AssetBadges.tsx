/*
 * Asset Badges reusable UI component used by the React dashboard.
 */
import { Badge } from "../../../components/ui/Badge";
import type { AssetAgentStatus, AssetCriticality } from "../types";

// Defines the Agent Status Badge Props data shape used by this frontend module.
type AgentStatusBadgeProps = {
  status: AssetAgentStatus;
};

// Defines the Criticality Badge Props data shape used by this frontend module.
type CriticalityBadgeProps = {
  criticality: AssetCriticality;
};

const agentToneMap: Record<AssetAgentStatus, "success" | "warning" | "danger"> = {
  online: "success",
  degraded: "warning",
  offline: "danger"
};

const criticalityToneMap: Record<
  AssetCriticality,
  "danger" | "warning" | "brand" | "neutral"
> = {
  mission_critical: "danger",
  high: "warning",
  standard: "brand",
  low: "neutral"
};

// Renders the Agent Status Badge UI section.
export function AgentStatusBadge({ status }: AgentStatusBadgeProps) {
  return <Badge tone={agentToneMap[status]}>{status}</Badge>;
}

// Renders the Criticality Badge UI section.
export function CriticalityBadge({ criticality }: CriticalityBadgeProps) {
  return <Badge tone={criticalityToneMap[criticality]}>{criticality.split("_").join(" ")}</Badge>;
}
