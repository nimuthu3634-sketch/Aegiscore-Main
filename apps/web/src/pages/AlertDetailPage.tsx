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
import { ErrorState } from "../components/feedback/ErrorState";
import { LoadingCard, LoadingTable } from "../components/feedback/LoadingState";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
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
          alertTitle={alert.title ?? alert.detectionType}
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
        eyebrow="Alert investigation"
        title={alert.detectionType}
        description={alert.normalizedSummary}
        badges={
          <>
            <Badge tone="outline">{alert.id}</Badge>
            <Badge tone="outline">{alert.sourceType}</Badge>
            <SeverityChip severity={alert.severity} />
            <StatusChip status={alert.status} />
            <Badge tone="brand">risk {alert.riskScore ?? "n/a"}</Badge>
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
              Export evidence placeholder
            </Button>
          </div>
        }
      >
        <KeyValueGrid items={metadataItems} columns={4} />
      </DetailHeader>

      <section className="grid gap-4 2xl:grid-cols-[1.35fr_0.65fr]">
        <div className="space-y-4">
          <EvidencePanel
            eyebrow="Common schema"
            title="Normalized details"
            description="AegisCore-normalized evidence aligned to the future backend detail response."
          >
            <KeyValueGrid items={alert.normalizedDetails} columns={3} />
          </EvidencePanel>

          <RawPayloadViewer payload={alert.rawPayload} />

          <RelatedResponsesPanel responses={alert.relatedResponses} />

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
              scoreValue={<Badge tone="brand">risk {alert.scoreExplanation.score ?? "n/a"}</Badge>}
              factors={alert.scoreExplanation.factors}
              drivers={alert.scoreExplanation.drivers}
              metadata={[
                {
                  label: "Scoring method",
                  value: alert.scoreExplanation.scoringMethod ?? "n/a"
                },
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
              description="The backend did not return a risk explanation for this alert yet."
            >
              <p className="type-body-sm">
                The detail flow remains connected to the backend, but this alert does not currently include a score rationale payload.
              </p>
            </EvidencePanel>
          )}

          <EvidencePanel
            eyebrow="Workflow"
            title="Lifecycle actions"
            description="Persisted alert lifecycle controls backed by audit logging and live detail refresh."
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
              {workflowError ? (
                <p className="text-body-sm text-status-danger">{workflowError}</p>
              ) : workflowMessage ? (
                <p className="text-body-sm text-status-success">{workflowMessage}</p>
              ) : (
                <p className="type-body-sm">
                  Acknowledge, incident linkage, and close actions now persist through the
                  backend workflow APIs.
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
