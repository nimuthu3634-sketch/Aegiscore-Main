import { Badge } from "../ui/Badge";
import { formatTokenLabel } from "../../lib/formatters";
import { SUPPORTED_DETECTION_TYPES } from "../../lib/supportedDetections";

/**
 * Compact reminder of the four approved detections and the analyst workflow this console supports.
 */
export function DetectionScopeCallout() {
  return (
    <div className="rounded-panel border border-brand-primary/30 bg-surface-subtle/50 px-4 py-4 md:px-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between lg:gap-6">
        <div className="min-w-0 space-y-2">
          <p className="type-label-md text-brand-primary">v1 threat scope — four detections</p>
          <p className="max-w-3xl type-body-sm text-content-secondary">
            <span className="font-medium text-content-primary">Review in order: </span>
            what happened (alerts and evidence), how serious it is (severity and risk score), what
            automated response executed (responses), then close the loop in incidents and
            notifications.
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {SUPPORTED_DETECTION_TYPES.map((detection) => (
            <Badge key={detection} tone="outline" className="border-border-subtle/90">
              {formatTokenLabel(detection)}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}
