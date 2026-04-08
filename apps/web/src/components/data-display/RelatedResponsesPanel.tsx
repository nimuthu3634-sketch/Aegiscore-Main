import { EvidencePanel } from "./EvidencePanel";
import { ModeBadge, ExecutionStatusBadge } from "../../features/responses/components/ResponseBadges";
import type { ResponseExecutionStatus, ResponseMode } from "../../features/responses/types";
import { Badge } from "../ui/Badge";
import { formatTokenLabel } from "../../lib/formatters";

export type ResponseRelatedNotification = {
  id: string;
  recipient: string;
  status: string;
  triggerType: string;
  deliveryMode: string;
  subject: string;
};

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
  relatedNotifications?: ResponseRelatedNotification[];
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
      eyebrow="Response history"
      title={title}
      description="What ran against this alert or incident: policy name, target, dry-run vs live, outcome, and any linked notification deliveries."
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
                {response.relatedNotifications && response.relatedNotifications.length ? (
                  <div
                    className="mt-3 rounded-panel border border-border-subtle/80 bg-surface-base/40 p-3"
                    data-testid="response-linked-notification-deliveries"
                  >
                    <p className="type-body-sm font-medium text-content-primary">
                      Linked notification deliveries
                    </p>
                    <ul className="mt-2 space-y-2">
                      {response.relatedNotifications.map((event) => (
                        <li
                          key={event.id}
                          className="type-body-sm text-content-secondary"
                          data-testid="response-notification-delivery-item"
                        >
                          <span className="type-mono-sm">{event.status}</span>
                          {" · "}
                          {event.deliveryMode} to {event.recipient}
                          {" · "}
                          {event.triggerType}
                          {event.subject ? (
                            <>
                              {" · "}
                              <span className="text-content-muted">{event.subject}</span>
                            </>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-panel border border-dashed border-border-subtle bg-surface-base/30 p-4">
          <p className="type-body-sm">
            No policy executions recorded for this record yet. If automation is enabled, actions
            appear here after they run.
          </p>
        </div>
      )}
    </EvidencePanel>
  );
}
