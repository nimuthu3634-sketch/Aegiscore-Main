import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AnalystNotesPanel } from "../components/data-display/AnalystNotesPanel";
import { DetailHeader } from "../components/data-display/DetailHeader";
import { EvidencePanel } from "../components/data-display/EvidencePanel";
import { KeyValueGrid, type KeyValueItem } from "../components/data-display/KeyValueGrid";
import { RawPayloadViewer } from "../components/data-display/RawPayloadViewer";
import { RelatedResponsesPanel } from "../components/data-display/RelatedResponsesPanel";
import { ScoreExplanationCard } from "../components/data-display/ScoreExplanationCard";
import { EmptyState } from "../components/feedback/EmptyState";
import { AlertAiContextBanner } from "../components/data-display/AlertAiContextBanner";
import { AUTOMATED_BLOCK_SCOPE_NOTE, formatAiTierTitleCase } from "../lib/aiPrioritization";
import { formatTokenLabel } from "../lib/formatters";
import { ErrorState } from "../components/feedback/ErrorState";
import { LoadingCard, LoadingTable } from "../components/feedback/LoadingState";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { AiPriorityBadge } from "../components/ui/AiPriorityBadge";
import { SeverityChip } from "../components/ui/SeverityChip";
import { StatusChip } from "../components/ui/StatusChip";
import { LinkIncidentModal } from "../features/alerts/detail/LinkIncidentModal";
import {
  acknowledgeAlertDetail,
  closeAlertDetail,
  saveAlertNote,
  useAlertDetail
} from "../features/alerts/detail/service";

function fallbackValue(value: string | null | undefined) {
  return value ?? "n/a";
}

export function AlertDetailPage() {
  const navigate = useNavigate();
  const { alertId } = useParams<{ alertId: string }>();
  const { data, isLoading, error, notFound, reload } = useAlertDetail(alertId);
  const [pendingAction, setPendingAction] = useState<"acknowledge" | "close" | null>(
    null
  );
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [workflowMessage, setWorkflowMessage] = useState<string | null>(null);
  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);
  const [noteDraft, setNoteDraft] = useState("");
  const [isSavingNote, setIsSavingNote] = useState(false);
  const [noteError, setNoteError] = useState<string | null>(null);
  const [noteMessage, setNoteMessage] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-section">
        <LoadingCard className="min-h-[220px]" />
        <section className="grid gap-4 2xl:grid-cols-[1.35fr_0.65fr]">
          <div className="space-y-4">
            <LoadingCard className="min-h-[240px]" />
            <LoadingCard className="min-h-[280px]" />
          </div>
          <div className="space-y-4">
            <LoadingCard className="min-h-[220px]" />
            <LoadingCard className="min-h-[220px]" />
          </div>
        </section>
        <LoadingTable columns={6} rows={4} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-section">
        <Button variant="ghost" size="sm" onClick={() => navigate("/alerts")}>
          Back to alerts
        </Button>
        <ErrorState
          title="Alert detail could not be loaded"
          description="The investigation detail surface is ready, but the current alert detail request failed."
          details={error}
          action={
            <div className="flex flex-wrap gap-3">
              <Button variant="secondary" size="sm" onClick={reload}>
                Retry detail
              </Button>
              <Button variant="ghost" size="sm" onClick={() => navigate("/alerts")}>
                Return to queue
              </Button>
            </div>
          }
        />
      </div>
    );
  }

  if (notFound || !data) {
    return (
      <div className="space-y-section">
        <Button variant="ghost" size="sm" onClick={() => navigate("/alerts")}>
          Back to alerts
        </Button>
        <EmptyState
          dataTestId="detail-record-not-found"
          iconName="alerts"
          title="Alert record was not found"
          description="The requested alert is not available in the current dataset. Return to the queue and select another alert."
          action={
            <Button variant="secondary" size="sm" onClick={() => navigate("/alerts")}>
              Open alerts queue
            </Button>
          }
        />
      </div>
    );
  }

  const { alert, fetchedAt } = data;
  const canAcknowledge = !["investigating", "resolved"].includes(alert.status);
  const canLinkIncident = !alert.linkedIncidentId && alert.status !== "resolved";
  const canClose = alert.status !== "resolved";

  const metadataItems: KeyValueItem[] = [
    { label: "Alert ID", value: alert.id, mono: true, emphasized: true },
    {
      label: "Detection type",
      value: formatTokenLabel(alert.detectionType),
      emphasized: true
    },
    { label: "Source IP", value: fallbackValue(alert.sourceIp), mono: true },
    { label: "Destination IP", value: fallbackValue(alert.destinationIp), mono: true },
    {
      label: "Destination port",
      value: fallbackValue(alert.destinationPort),
      mono: true
    },
    { label: "Asset / hostname", value: fallbackValue(alert.asset), emphasized: true },
    { label: "Username", value: fallbackValue(alert.username), mono: true },
    { label: "Timestamp", value: alert.timestamp, mono: true },
    {
      label: "Rule ID / source rule",
      value: [alert.ruleId, alert.sourceRule].filter(Boolean).join(" / ") || "n/a",
      mono: true
    }
  ];

  async function handleWorkflowAction(
    action: "acknowledge" | "close",
    runner: () => Promise<{ message: string }>
  ) {
    if (!alertId) {
      return;
    }

    setPendingAction(action);
    setWorkflowError(null);
    setWorkflowMessage(null);

    try {
      const response = await runner();
      setWorkflowMessage(response.message);
      reload();
    } catch (actionError: unknown) {
      setWorkflowError(
        actionError instanceof Error
          ? actionError.message
          : "Workflow action failed."
      );
    } finally {
      setPendingAction(null);
    }
  }

  async function handleSaveNote() {
    if (!alertId) {
      return;
    }

    if (!noteDraft.trim()) {
      setNoteError("Note content cannot be empty.");
      setNoteMessage(null);
      return;
    }

    setIsSavingNote(true);
    setNoteError(null);
    setNoteMessage(null);

    try {
      const response = await saveAlertNote(alertId, noteDraft);
      setNoteDraft("");
      setNoteMessage(response.message);
      reload();
    } catch (saveError: unknown) {
      setNoteError(
        saveError instanceof Error ? saveError.message : "Note save failed."
      );
    } finally {
      setIsSavingNote(false);
    }
  }

  return (
    <div className="space-y-section">
      {isLinkModalOpen ? (
        <LinkIncidentModal
          open={isLinkModalOpen}
          alertId={alert.id}
          alertTitle={alert.title ?? formatTokenLabel(alert.detectionType)}
          alertSummary={alert.normalizedSummary}
          onClose={() => setIsLinkModalOpen(false)}
          onSuccess={(message) => {
            setIsLinkModalOpen(false);
            setWorkflowError(null);
            setWorkflowMessage(message);
            reload();
          }}
        />
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate("/alerts")}>
          Back to alerts
        </Button>
        <Badge tone="outline">fetched {fetchedAt}</Badge>
      </div>

      <DetailHeader
        eyebrow="In-scope alert"
        title={formatTokenLabel(alert.detectionType)}
        description={alert.normalizedSummary}
        badges={
          <>
            <Badge tone="outline">{alert.id}</Badge>
            <Badge tone="outline">{alert.sourceType}</Badge>
            <SeverityChip severity={alert.severity} />
            {alert.scoreExplanation?.modelPriorityTier ? (
              <AiPriorityBadge tier={alert.scoreExplanation.modelPriorityTier} />
            ) : null}
            <StatusChip status={alert.status} />
            <Badge tone={(alert.riskScore ?? 0) >= 70 ? "warning" : "brand"}>
              risk {alert.riskScore ?? "n/a"}
            </Badge>
            {alert.linkedIncidentId ? (
              <Badge tone="outline">incident {alert.linkedIncidentId}</Badge>
            ) : (
              <Badge tone="neutral">no linked incident</Badge>
            )}
          </>
        }
        actions={
          <div className="flex flex-wrap gap-3">
            {alert.linkedIncidentId ? (
              <Button
                size="sm"
                onClick={() => navigate(`/incidents/${alert.linkedIncidentId}`)}
              >
                Open linked incident
              </Button>
            ) : null}
            <Button variant="secondary" size="sm">
              Export evidence
            </Button>
          </div>
        }
      >
        <KeyValueGrid items={metadataItems} columns={4} />
      </DetailHeader>

      <AlertAiContextBanner
        sourceType={alert.sourceType}
        detectionType={alert.detectionType}
        scoringMethodLabel={alert.scoreExplanation?.scoringMethod ?? null}
        rawScoringMethod={alert.scoreExplanation?.scoringMethodValue ?? null}
        aiTier={alert.scoreExplanation?.modelPriorityTier ?? null}
      />

      {alert.detectionType === "brute_force" ? (
        <EvidencePanel
          eyebrow="Automated response"
          title="Brute-force automation status"
          description="Only brute_force alerts may trigger the built-in ML IP block when TensorFlow prioritization is High and login-density gates pass. Review execution rows below."
        >
          {alert.relatedResponses.length ? (
            <ul className="space-y-2">
              {alert.relatedResponses.map((r) => (
                <li
                  key={r.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-panel border border-border-subtle bg-surface-subtle/50 px-3 py-2 type-body-sm"
                >
                  <span className="type-mono-sm">{r.actionType}</span>
                  <span className="text-content-muted">{r.executionStatus}</span>
                  <span className="type-mono-sm text-content-secondary">{r.mode}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="type-body-sm text-content-muted">
              No automated response executions are recorded for this alert yet.
            </p>
          )}
        </EvidencePanel>
      ) : null}

      <section className="grid gap-4 2xl:grid-cols-[1.35fr_0.65fr]">
        <div className="space-y-4">
          <EvidencePanel
            eyebrow="Evidence"
            title="Normalized details"
            description="Structured fields for triage (hosts, auth, paths, ports, users). Use with raw payload below for full fidelity."
          >
            <KeyValueGrid items={alert.normalizedDetails} columns={3} />
          </EvidencePanel>

          <RawPayloadViewer payload={alert.rawPayload} />

          <RelatedResponsesPanel
            responses={alert.relatedResponses}
            automationScopeFootnote={
              alert.detectionType === "brute_force"
                ? AUTOMATED_BLOCK_SCOPE_NOTE
                : "Built-in ML IP auto-blocking does not apply to this detection type; policy-driven actions may still appear below."
            }
          />

          <EvidencePanel
            dataTestId="alert-notifications-panel"
            eyebrow="Notifications"
            title="Administrator notifications"
            description="Delivery attempts for the linked incident from risk scoring, state transitions, response outcomes, or notify_admin actions."
          >
            {!alert.linkedIncidentId ? (
              <div
                className="rounded-panel border border-dashed border-border-subtle bg-surface-base/30 p-4"
                data-testid="alert-notification-link-required"
              >
                <p className="type-body-sm">
                  Notifications are scoped to incidents. Link this alert to an incident to see
                  administrator delivery history here.
                </p>
              </div>
            ) : alert.notifications.length ? (
              <div className="space-y-3">
                {alert.notifications.map((event) => (
                  <div
                    key={event.id}
                    className="rounded-panel border border-border-subtle bg-surface-subtle/65 p-4"
                    data-testid="notification-event-row"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="type-mono-sm">{event.subject}</p>
                      <Badge
                        tone={
                          event.status === "sent"
                            ? "success"
                            : event.status === "failed"
                              ? "danger"
                              : "outline"
                        }
                      >
                        {event.status}
                      </Badge>
                    </div>
                    <p className="mt-2 type-body-sm">
                      {event.channel} ({event.deliveryMode}) to {event.recipient}
                    </p>
                    <p className="mt-1 type-body-sm">
                      trigger: {event.triggerType} [{event.triggerValue}]
                    </p>
                    <p className="mt-1 type-body-sm">created: {event.createdAt}</p>
                    <p className="mt-1 type-body-sm">sent: {event.sentAt}</p>
                    {event.errorMessage ? (
                      <p className="mt-2 text-body-sm text-status-danger">{event.errorMessage}</p>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <div
                className="rounded-panel border border-dashed border-border-subtle bg-surface-base/30 p-4"
                data-testid="notification-empty-state"
              >
                <p className="type-body-sm">
                  No notification attempts have been recorded for this incident yet.
                </p>
              </div>
            )}
          </EvidencePanel>

          <AnalystNotesPanel
            notes={alert.notes}
            composerLabel="Add alert investigation note"
            draft={noteDraft}
            onDraftChange={(value) => {
              setNoteDraft(value);
              if (noteError) {
                setNoteError(null);
              }
              if (noteMessage) {
                setNoteMessage(null);
              }
            }}
            onSave={handleSaveNote}
            isSaving={isSavingNote}
            saveError={noteError}
            saveSuccess={noteMessage}
            saveDisabled={!alertId}
          />
        </div>

        <div className="space-y-4">
          {alert.scoreExplanation ? (
            <ScoreExplanationCard
              label={alert.scoreExplanation.label}
              summary={alert.scoreExplanation.summary}
              rationale={alert.scoreExplanation.rationale}
              reasoning={alert.scoreExplanation.reasoning}
              classProbabilitiesSummary={alert.scoreExplanation.classProbabilitiesSummary}
              scoreValue={<Badge tone="brand">risk {alert.scoreExplanation.score ?? "n/a"}</Badge>}
              factors={alert.scoreExplanation.factors}
              drivers={alert.scoreExplanation.drivers}
              metadata={[
                {
                  label: "Scoring method",
                  value: alert.scoreExplanation.scoringMethod ?? "n/a"
                },
                ...(alert.scoreExplanation.modelPriorityTier
                  ? [
                      {
                        label: "AI priority tier",
                        value: formatAiTierTitleCase(alert.scoreExplanation.modelPriorityTier)
                      }
                    ]
                  : []),
                ...(alert.scoreExplanation.version
                  ? [
                      {
                        label: "Version",
                        value: alert.scoreExplanation.version,
                        mono: true
                      }
                    ]
                  : []),
                {
                  label: "Confidence",
                  value:
                    alert.scoreExplanation.confidence != null
                      ? `${Math.round(alert.scoreExplanation.confidence * 100)}%`
                      : "n/a",
                  mono: true
                }
              ]}
            />
          ) : (
            <EvidencePanel
              eyebrow="Scoring"
              title="Score explanation unavailable"
              description="Risk is still shown in the header when present; a full factor breakdown was not returned for this alert."
            >
              <p className="type-body-sm">
                Refresh after scoring runs, or open the scoring docs if you are validating the
                pipeline in a lab environment.
              </p>
            </EvidencePanel>
          )}

          <EvidencePanel
            eyebrow="Workflow"
            title="Lifecycle actions"
            description="Acknowledge, link to an incident, or close. Each action is persisted and reflected on refresh."
          >
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <Button
                  variant="secondary"
                  size="sm"
                  data-testid="alert-acknowledge-btn"
                  onClick={() =>
                    handleWorkflowAction("acknowledge", () =>
                      acknowledgeAlertDetail(alert.id)
                    )
                  }
                  disabled={!canAcknowledge || pendingAction !== null}
                >
                  {pendingAction === "acknowledge" ? "Acknowledging..." : "Acknowledge"}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  data-testid="alert-link-incident-btn"
                  onClick={() => {
                    setWorkflowError(null);
                    setWorkflowMessage(null);
                    setIsLinkModalOpen(true);
                  }}
                  disabled={!canLinkIncident || pendingAction !== null}
                >
                  Link to incident
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  data-testid="alert-close-btn"
                  onClick={() =>
                    handleWorkflowAction("close", () => closeAlertDetail(alert.id))
                  }
                  disabled={!canClose || pendingAction !== null}
                >
                  {pendingAction === "close" ? "Closing..." : "Close"}
                </Button>
              </div>
              {workflowError || workflowMessage ? (
                <p
                  data-testid="alert-workflow-feedback"
                  className={
                    workflowError
                      ? "text-body-sm text-status-danger"
                      : "text-body-sm text-status-success"
                  }
                >
                  {workflowError ?? workflowMessage}
                </p>
              ) : (
                <p className="type-body-sm">
                  Choose an action above; success or errors appear here immediately after the
                  request completes.
                </p>
              )}
            </div>
          </EvidencePanel>

          <EvidencePanel
            eyebrow="Context"
            title="Incident linkage"
            description="Incident relationship status for this alert."
          >
            {alert.linkedIncidentId ? (
              <div className="space-y-3">
                <div className="space-y-2">
                  <p className="type-label-md">Current linked incident</p>
                  <p className="type-heading-sm">
                    {alert.linkedIncidentTitle ?? "Linked incident"}
                  </p>
                  <p className="type-body-sm">
                    This alert is already grouped into the incident below and no longer
                    needs a new linkage action.
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <Badge tone="brand">{alert.linkedIncidentId}</Badge>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => navigate(`/incidents/${alert.linkedIncidentId}`)}
                  >
                    Open incident detail
                  </Button>
                </div>
              </div>
            ) : (
              <div className="rounded-panel border border-dashed border-border-subtle bg-surface-base/30 p-4">
                <div className="space-y-3">
                  <p className="type-body-sm">
                    No incident linkage exists yet. Use the live link action above to
                    search existing incidents or intentionally create a new one.
                  </p>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setWorkflowError(null);
                      setWorkflowMessage(null);
                      setIsLinkModalOpen(true);
                    }}
                    disabled={!canLinkIncident}
                  >
                    Open incident linker
                  </Button>
                </div>
              </div>
            )}
          </EvidencePanel>
        </div>
      </section>
    </div>
  );
}
