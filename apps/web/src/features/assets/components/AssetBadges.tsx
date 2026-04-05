import { Badge } from "../../../components/ui/Badge";
import type { AssetAgentStatus, AssetCriticality } from "../types";

type AgentStatusBadgeProps = {
  status: AssetAgentStatus;
};

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

export function AgentStatusBadge({ status }: AgentStatusBadgeProps) {
  return <Badge tone={agentToneMap[status]}>{status}</Badge>;
}

export function CriticalityBadge({ criticality }: CriticalityBadgeProps) {
  return <Badge tone={criticalityToneMap[criticality]}>{criticality.split("_").join(" ")}</Badge>;
}
