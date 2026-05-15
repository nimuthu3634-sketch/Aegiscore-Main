/*
 * Ai Priority Badge reusable UI component used by the React dashboard.
 */
import { Badge } from "./Badge";
import type { AiPriorityTier } from "../../lib/aiPrioritization";
import { formatAiTierTitleCase } from "../../lib/aiPrioritization";

// Defines the Ai Priority Badge Props data shape used by this frontend module.
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
