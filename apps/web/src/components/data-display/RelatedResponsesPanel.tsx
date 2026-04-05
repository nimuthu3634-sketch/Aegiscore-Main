import { EvidencePanel } from "./EvidencePanel";
import { ModeBadge, ExecutionStatusBadge } from "../../features/responses/components/ResponseBadges";
import type { ResponseExecutionStatus, ResponseMode } from "../../features/responses/types";
import { Badge } from "../ui/Badge";
import { formatTokenLabel } from "../../lib/formatters";

export type RelatedResponseItem = {
  id: string;
  actionType: string;
  policyName?: string | null;
  target: string;
  mode: ResponseMode;
  executionStatus: ResponseExecutionStatus;
  executedAt: string;
  resultSummary: string;
  resultMessage?: string | null;
  attemptCount?: number;
  requestedBy?: string | null;
};

type RelatedResponsesPanelProps = {
  responses: RelatedResponseItem[];
  title?: string;
};

export function RelatedResponsesPanel({
  responses,
  title = "Related response actions"
}: RelatedResponsesPanelProps) {
  return (
    <EvidencePanel
      title={title}
      description="Related automated and analyst-triggered actions connected to this investigation context."
    >
      {responses.length ? (
        <div className="space-y-3">
          {responses.map((response) => (
            <div
              key={response.id}
              className="rounded-panel border border-border-subtle bg-surface-subtle/65 p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-body-sm font-medium text-content-primary">
                    {formatTokenLabel(response.actionType)}
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <p className="type-mono-sm">{response.id}</p>
                    {response.policyName ? <Badge tone="brand">{response.policyName}</Badge> : null}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <ModeBadge mode={response.mode} />
                  <ExecutionStatusBadge status={response.executionStatus} />
                </div>
              </div>
              <div className="mt-3 space-y-2">
                <p className="type-mono-sm">target: {response.target}</p>
                <p className="type-mono-sm">executed_at: {response.executedAt}</p>
                <p className="type-body-sm">{response.resultSummary}</p>
                {response.resultMessage && response.resultMessage !== response.resultSummary ? (
                  <p className="type-body-sm text-content-muted">{response.resultMessage}</p>
                ) : null}
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                  <p className="type-mono-sm">attempts: {response.attemptCount ?? 0}</p>
                  {response.requestedBy ? (
                    <p className="type-body-sm">
                      requested_by: <span className="type-mono-sm">{response.requestedBy}</span>
                    </p>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-panel border border-dashed border-border-subtle bg-surface-base/30 p-4">
          <p className="type-body-sm">
            No automated or analyst-triggered response actions are linked to this record yet.
          </p>
        </div>
      )}
    </EvidencePanel>
  );
}
