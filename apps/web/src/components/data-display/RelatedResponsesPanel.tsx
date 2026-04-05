import { EvidencePanel } from "./EvidencePanel";
import { ModeBadge, ExecutionStatusBadge } from "../../features/responses/components/ResponseBadges";
import type { ResponseExecutionStatus, ResponseMode } from "../../features/responses/types";

export type RelatedResponseItem = {
  id: string;
  actionType: string;
  target: string;
  mode: ResponseMode;
  executionStatus: ResponseExecutionStatus;
  executedAt: string;
  resultSummary: string;
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
                    {response.actionType}
                  </p>
                  <p className="mt-1 type-mono-sm">{response.id}</p>
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
