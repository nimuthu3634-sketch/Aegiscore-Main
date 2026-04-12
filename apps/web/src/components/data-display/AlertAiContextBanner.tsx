import { Badge } from "../ui/Badge";
import { AiPriorityBadge } from "../ui/AiPriorityBadge";
import type { AiPriorityTier } from "../../lib/aiPrioritization";
import { isTensorFlowScoringMethod } from "../../lib/aiPrioritization";
import { AUTOMATED_BLOCK_SCOPE_NOTE } from "../../lib/aiPrioritization";

type AlertAiContextBannerProps = {
  sourceType: "Wazuh" | "Suricata";
  detectionType: string;
  scoringMethodLabel: string | null | undefined;
  rawScoringMethod?: string | null;
  aiTier: AiPriorityTier | null;
};

/**
 * Clarifies detect vs prioritize and shows the 3-class AI tier when TensorFlow scored the alert.
 */
export function AlertAiContextBanner({
  sourceType,
  detectionType,
  scoringMethodLabel,
  rawScoringMethod,
  aiTier
}: AlertAiContextBannerProps) {
  const tf = isTensorFlowScoringMethod(rawScoringMethod ?? undefined);
  const isBrute = detectionType === "brute_force";

  return (
    <div
      className="rounded-panel border border-border-subtle bg-surface-subtle/50 p-4 space-y-3"
      data-testid="alert-ai-context-banner"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="outline">Detection</Badge>
        <span className="type-body-sm text-content-secondary">
          <span className="font-medium text-content-primary">{sourceType}</span> reported this
          event ({detectionType.replace(/_/g, " ")}).
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="brand">Prioritization</Badge>
        {tf && aiTier ? (
          <span className="flex flex-wrap items-center gap-2 type-body-sm text-content-secondary">
            <span>TensorFlow model ranks urgency as</span>
            <AiPriorityBadge tier={aiTier} />
            <span className="text-content-muted">(AI uses Low / Medium / High only.)</span>
          </span>
        ) : (
          <span className="type-body-sm text-content-secondary">
            {scoringMethodLabel ? (
              <>
                Scored with <span className="font-medium text-content-primary">{scoringMethodLabel}</span>
                {tf ? " — tier not available in this payload." : " (deterministic rules, not the 3-class AI head)."}
              </>
            ) : (
              "No scoring method metadata was returned for this alert."
            )}
          </span>
        )}
      </div>
      {isBrute ? (
        <p className="type-body-sm text-content-muted border-t border-border-subtle pt-3">
          {AUTOMATED_BLOCK_SCOPE_NOTE}
        </p>
      ) : (
        <p className="type-body-sm text-content-muted border-t border-border-subtle pt-3">
          Automated IP blocking is limited to brute_force under strict AI + threshold gates. This
          detection type ({detectionType.replace(/_/g, " ")}) is not eligible for that built-in
          auto-block path.
        </p>
      )}
    </div>
  );
}
