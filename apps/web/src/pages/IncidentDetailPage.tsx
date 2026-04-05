import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ActivityTimeline } from "../components/data-display/ActivityTimeline";
import { AnalystNotesPanel } from "../components/data-display/AnalystNotesPanel";
import { DetailHeader } from "../components/data-display/DetailHeader";
import { EvidencePanel } from "../components/data-display/EvidencePanel";
import { KeyValueGrid, type KeyValueItem } from "../components/data-display/KeyValueGrid";
import { LinkedAlertsTable } from "../components/data-display/LinkedAlertsTable";
import { RelatedResponsesPanel } from "../components/data-display/RelatedResponsesPanel";
import { ScoreExplanationCard } from "../components/data-display/ScoreExplanationCard";
import { EmptyState } from "../components/feedback/EmptyState";
import { ErrorState } from "../components/feedback/ErrorState";
import { LoadingCard, LoadingTable } from "../components/feedback/LoadingState";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { IncidentStateBadge } from "../components/ui/IncidentStateBadge";
import { PriorityChip } from "../components/ui/PriorityChip";
import { AgentStatusBadge, CriticalityBadge } from "../features/assets/components/AssetBadges";
import {
  saveIncidentNote,
  transitionIncident,
  useIncidentDetail
} from "../features/incidents/detail/service";

export function IncidentDetailPage() {
  const navigate = useNavigate();
  const { incidentId } = useParams<{ incidentId: string }>();
  const { data, isLoading, error, notFound, reload } = useIncidentDetail(incidentId);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [transitionMessage, setTransitionMessage] = useState<string | null>(null);
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
            <LoadingTable columns={7} rows={4} />
            <LoadingCard className="min-h-[260px]" />
            <LoadingCard className="min-h-[220px]" />
          </div>
          <div className="space-y-4">
            <LoadingCard className="min-h-[260px]" />
            <LoadingCard className="min-h-[260px]" />
          </div>
        </section>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-section">
        <Button variant="ghost" size="sm" onClick={() => navigate("/incidents")}>
          Back to incidents
        </Button>
        <ErrorState
          title="Incident detail could not be loaded"
          description="The incident investigation view is ready, but the current detail request failed."
          details={error}
          action={
            <div className="flex flex-wrap gap-3">
              <Button variant="secondary" size="sm" onClick={reload}>
                Retry incident detail
              </Button>
              <Button variant="ghost" size="sm" onClick={() => navigate("/incidents")}>
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
        <Button variant="ghost" size="sm" onClick={() => navigate("/incidents")}>
          Back to incidents
        </Button>
        <EmptyState
          iconName="incidents"
          title="Incident record was not found"
          description="The requested incident is not available in the current dataset. Return to the queue and choose another investigation."
          action={
            <Button variant="secondary" size="sm" onClick={() => navigate("/incidents")}>
              Open incidents queue
            </Button>
          }
        />
      </div>
    );
  }

  const { incident, fetchedAt } = data;

  const summaryItems: KeyValueItem[] = [
    { label: "Incident ID", value: incident.id, mono: true, emphasized: true },
    { label: "Assignee", value: incident.assignee, mono: true },
    { label: "Created at", value: incident.createdAt, mono: true },
    { label: "Updated at", value: incident.updatedAt, mono: true },
    { label: "Primary asset", value: incident.primaryAsset, emphasized: true },
    { label: "Detection type", value: incident.detectionType, mono: true },
    { label: "Linked alerts", value: String(incident.linkedAlertsCount), mono: true },
    { label: "Source type", value: incident.sourceType, emphasized: true }
  ];

  const affectedAssets = incident.affectedAssets.filter(
    (asset) =>
      asset.hostname !== incident.primaryAssetSummary.hostname ||
      asset.ipAddress !== incident.primaryAssetSummary.ipAddress
  );

  const actionVariants = {
    triage: incident.availableActions?.includes("triage") ? "primary" : "secondary",
    investigate: incident.availableActions?.includes("investigate")
      ? "primary"
      : "secondary",
    contain: incident.availableActions?.includes("contain") ? "primary" : "secondary",
    resolve: incident.availableActions?.includes("resolve") ? "primary" : "secondary",
    falsePositive: incident.availableActions?.includes("mark_false_positive")
      ? "ghost"
      : "secondary"
  } as const;

  async function handleTransition(
    action: "triage" | "investigate" | "contain" | "resolve" | "mark_false_positive"
  ) {
    if (!incidentId) {
      return;
    }

    setPendingAction(action);
    setTransitionError(null);
    setTransitionMessage(null);

    try {
      const response = await transitionIncident(incidentId, action);
      setTransitionMessage(response.message);
      reload();
    } catch (transitionActionError: unknown) {
      setTransitionError(
        transitionActionError instanceof Error
          ? transitionActionError.message
          : "Incident transition failed."
      );
    } finally {
      setPendingAction(null);
    }
  }

  async function handleSaveNote() {
    if (!incidentId) {
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
      const response = await saveIncidentNote(incidentId, noteDraft);
      setNoteDraft("");
      setNoteMessage(response.message);
      reload();
    } catch (saveError: unknown) {
      setNoteError(
        saveError instanceof Error ? saveError.message : "Incident note save failed."
      );
    } finally {
      setIsSavingNote(false);
    }
  }

  return (
    <div className="space-y-section">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate("/incidents")}>
          Back to incidents
        </Button>
        <Badge tone="outline">fetched {fetchedAt}</Badge>
      </div>

      <DetailHeader
        eyebrow="Incident investigation"
        title={incident.title}
        description={incident.summary}
        badges={
          <>
            <Badge tone="outline">{incident.id}</Badge>
            <Badge tone="outline">{incident.detectionType}</Badge>
            <PriorityChip priority={incident.priority} />
            <IncidentStateBadge state={incident.state} />
            <Badge tone="outline">{incident.assignee}</Badge>
            <Badge tone="brand">{incident.linkedAlertsCount} linked alerts</Badge>
          </>
        }
        actions={
          <div className="flex flex-wrap gap-3">
            <Button variant="secondary" size="sm">
              Export incident placeholder
            </Button>
            <Button variant="ghost" size="sm" onClick={() => navigate("/alerts")}>
              Open alerts queue
            </Button>
          </div>
        }
      >
        <KeyValueGrid items={summaryItems} columns={4} />
      </DetailHeader>

      <section className="grid gap-4 2xl:grid-cols-[1.35fr_0.65fr]">
        <div className="space-y-4">
          <EvidencePanel
            eyebrow="Evidence"
            title="Linked alerts"
            description="The linked alert set that produced or supports this incident."
          >
            <LinkedAlertsTable
              alerts={incident.linkedAlerts}
              onRowClick={(linkedAlert) => navigate(`/alerts/${linkedAlert.id}`)}
            />
          </EvidencePanel>

          <EvidencePanel
            eyebrow="Correlation"
            title="Grouped evidence summary"
            description={incident.correlationExplanation}
          >
            <div className="space-y-4">
              <p className="type-body-sm">{incident.correlationExplanation}</p>
              {incident.groupedEvidence.length ? (
                <ul className="space-y-2">
                  {incident.groupedEvidence.map((evidence) => (
                    <li
                      key={evidence}
                      className="rounded-panel border border-border-subtle bg-surface-subtle/65 px-4 py-3 text-body-sm text-content-secondary"
                    >
                      {evidence}
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="rounded-panel border border-dashed border-border-subtle bg-surface-base/30 p-4">
                  <p className="type-body-sm">
                    No additional grouped evidence items were returned by the backend.
                  </p>
                </div>
              )}
            </div>
          </EvidencePanel>

          <RelatedResponsesPanel
            responses={incident.relatedResponses}
            title="Response action history"
          />

          <AnalystNotesPanel
            notes={incident.notes}
            composerLabel="Add incident investigation note"
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
            saveDisabled={!incidentId}
          />
        </div>

        <div className="space-y-4">
          <EvidencePanel
            eyebrow="Assets"
            title="Primary and affected assets"
            description="Asset context grouped under this incident for triage and containment decisions."
          >
            <div className="space-y-3">
              <div className="rounded-panel border border-border-subtle bg-surface-subtle/65 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-body-sm font-medium text-content-primary">
                      {incident.primaryAssetSummary.hostname}
                    </p>
                    <p className="type-mono-sm">
                      {incident.primaryAssetSummary.ipAddress}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <CriticalityBadge
                      criticality={incident.primaryAssetSummary.criticality}
                    />
                    <AgentStatusBadge status="online" />
                  </div>
                </div>
                <p className="mt-3 type-body-sm">
                  Recent alerts on asset: {incident.primaryAssetSummary.recentAlertsCount}
                </p>
              </div>

              {affectedAssets.length ? (
                affectedAssets.map((asset) => (
                  <div
                    key={`${asset.hostname}-${asset.ipAddress}`}
                    className="rounded-panel border border-border-subtle bg-surface-base/35 p-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="space-y-1">
                        <p className="text-body-sm font-medium text-content-primary">
                          {asset.hostname}
                        </p>
                        <p className="type-mono-sm">{asset.ipAddress}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <CriticalityBadge criticality={asset.criticality} />
                      </div>
                    </div>
                    <p className="mt-3 type-body-sm">
                      Recent alerts on asset: {asset.recentAlertsCount}
                    </p>
                  </div>
                ))
              ) : (
                <div className="rounded-panel border border-dashed border-border-subtle bg-surface-base/30 p-4">
                  <p className="type-body-sm">
                    No additional affected assets are grouped into this incident yet.
                  </p>
                </div>
              )}
            </div>
          </EvidencePanel>

          <EvidencePanel
            eyebrow="Timeline"
            title="Investigation activity"
            description="Chronological investigation and response activity for this incident."
          >
            <ActivityTimeline items={incident.timeline} />
          </EvidencePanel>

          <ScoreExplanationCard
            label={incident.priorityExplanation.label}
            summary={incident.priorityExplanation.summary}
            rationale={incident.priorityExplanation.rationale}
            scoreValue={<PriorityChip priority={incident.priority} />}
            factors={incident.priorityExplanation.factors}
          />

          <EvidencePanel
            eyebrow="Workflow"
            title="State transitions"
            description="Validated incident state transitions with persisted timeline and audit updates."
          >
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-2">
                <Button
                  variant={actionVariants.triage}
                  size="sm"
                  onClick={() => handleTransition("triage")}
                  disabled={
                    pendingAction !== null ||
                    !incident.availableActions?.includes("triage")
                  }
                >
                  {pendingAction === "triage" ? "Triaging..." : "Triage"}
                </Button>
                <Button
                  variant={actionVariants.investigate}
                  size="sm"
                  onClick={() => handleTransition("investigate")}
                  disabled={
                    pendingAction !== null ||
                    !incident.availableActions?.includes("investigate")
                  }
                >
                  {pendingAction === "investigate" ? "Updating..." : "Investigate"}
                </Button>
                <Button
                  variant={actionVariants.contain}
                  size="sm"
                  onClick={() => handleTransition("contain")}
                  disabled={
                    pendingAction !== null ||
                    !incident.availableActions?.includes("contain")
                  }
                >
                  {pendingAction === "contain" ? "Containing..." : "Contain"}
                </Button>
                <Button
                  variant={actionVariants.resolve}
                  size="sm"
                  onClick={() => handleTransition("resolve")}
                  disabled={
                    pendingAction !== null ||
                    !incident.availableActions?.includes("resolve")
                  }
                >
                  {pendingAction === "resolve" ? "Resolving..." : "Resolve"}
                </Button>
              </div>
              <Button
                variant={actionVariants.falsePositive}
                size="sm"
                fullWidth
                onClick={() => handleTransition("mark_false_positive")}
                disabled={
                  pendingAction !== null ||
                  !incident.availableActions?.includes("mark_false_positive")
                }
              >
                {pendingAction === "mark_false_positive"
                  ? "Updating..."
                  : "Mark false positive"}
              </Button>
              {transitionError ? (
                <p className="text-body-sm text-status-danger">{transitionError}</p>
              ) : transitionMessage ? (
                <p className="text-body-sm text-status-success">{transitionMessage}</p>
              ) : null}
            </div>
          </EvidencePanel>
        </div>
      </section>
    </div>
  );
}
