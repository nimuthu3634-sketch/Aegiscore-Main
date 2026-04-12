import { Badge } from "./Badge";
import type { AiPriorityTier } from "../../lib/aiPrioritization";
import { formatAiTierTitleCase } from "../../lib/aiPrioritization";

type AiPriorityBadgeProps = {
  tier: AiPriorityTier;
};

const toneMap: Record<AiPriorityTier, "neutral" | "brand" | "warning"> = {
  low: "neutral",
  medium: "brand",
  high: "warning"
};

/** TensorFlow alert prioritization tier only (Low / Medium / High — never Critical). */
export function AiPriorityBadge({ tier }: AiPriorityBadgeProps) {
  return <Badge tone={toneMap[tier]}>AI: {formatAiTierTitleCase(tier)}</Badge>;
}
