import { EvidencePanel } from "./EvidencePanel";
import { ModeBadge, ExecutionStatusBadge } from "../../features/responses/components/ResponseBadges";
import type { ResponseExecutionStatus, ResponseMode } from "../../features/responses/types";
import { Badge } from "../ui/Badge";
import { formatTokenLabel } from "../../lib/formatters";
import { summarizeMlBruteForceBlock } from "../../lib/aiPrioritization";

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
  /** Raw execution details from the API (used for built-in ML brute-force block copy). */
  details?: Record<string, unknown>;
};

type RelatedResponsesPanelProps = {
  responses: RelatedResponseItem[];
  title?: string;
  /** Optional scope note (e.g. brute_force-only built-in block) shown once above the list. */
  automationScopeFootnote?: string | null;
};

export function RelatedResponsesPanel({
  responses,
  title = "Related response actions",
  automationScopeFootnote
}: RelatedResponsesPanelProps) {
  return (
    <EvidencePanel
      eyebrow="Response history"
      title={title}
      description="What ran against this alert or incident: policy name, target, dry-run vs live, outcome, and any linked notification deliveries."
    >
      {automationScopeFootnote ? (
        <p className="type-body-sm text-content-muted mb-3 rounded-panel border border-dashed border-border-subtle bg-surface-base/30 px-4 py-3">
          {automationScopeFootnote}
        </p>
      ) : null}
      {responses.length ? (
        <div className="space-y-3">
          {responses.map((response) => {
            const mlBlockWhy = summarizeMlBruteForceBlock(response.details);
            return (
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
                    {!response.policyName && response.actionType === "block_ip" ? (
                      <Badge tone="outline">built-in automation</Badge>
                    ) : null}
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
                {mlBlockWhy ? (
                  <div
                    className="rounded-panel border border-brand-primary/30 bg-surface-accentSoft/40 px-4 py-3"
                    data-testid="ml-brute-block-why"
                  >
                    <p className="type-label-sm">Why this IP was blocked</p>
                    <p className="type-body-sm mt-2 text-content-secondary">{mlBlockWhy}</p>
                  </div>
                ) : null}
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
            );
          })}
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
