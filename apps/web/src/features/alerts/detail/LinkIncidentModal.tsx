import {
  startTransition,
  useDeferredValue,
  useEffect,
  useMemo,
  useState
} from "react";
import { TablePagination } from "../../../components/data-display/TablePagination";
import { EmptyState } from "../../../components/feedback/EmptyState";
import { LoadingCard } from "../../../components/feedback/LoadingState";
import { Modal } from "../../../components/feedback/Modal";
import { Badge } from "../../../components/ui/Badge";
import { Button } from "../../../components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../components/ui/Card";
import { IncidentStateBadge } from "../../../components/ui/IncidentStateBadge";
import { Input } from "../../../components/ui/Input";
import { PriorityChip } from "../../../components/ui/PriorityChip";
import { SearchInput } from "../../../components/ui/SearchInput";
import { Textarea } from "../../../components/ui/Textarea";
import { cn } from "../../../lib/cn";
import { useIncidentsList } from "../../incidents/service";
import type { IncidentRecord, IncidentsListQuery } from "../../incidents/types";
import { linkAlertToIncident } from "./service";

type LinkMode = "existing" | "new";

type LinkIncidentModalProps = {
  open: boolean;
  alertId: string;
  alertTitle: string;
  alertSummary: string;
  onClose: () => void;
  onSuccess: (message: string) => void;
};

type IncidentCandidateListProps = {
  incidents: IncidentRecord[];
  selectedIncidentId: string | null;
  onSelect: (incident: IncidentRecord) => void;
};

type IncidentPreviewCardProps = {
  incident: IncidentRecord | null;
};

function IncidentCandidateList({
  incidents,
  selectedIncidentId,
  onSelect
}: IncidentCandidateListProps) {
  return (
    <div className="rounded-panel border border-border-subtle bg-surface-base/40">
      {incidents.map((incident, index) => {
        const isSelected = incident.id === selectedIncidentId;
        const isTerminal =
          incident.state === "resolved" || incident.state === "false_positive";

        return (
          <button
            key={incident.id}
            type="button"
            data-testid={`link-incident-candidate-${incident.id}`}
            className={cn(
              "w-full border-b border-border-subtle px-4 py-4 text-left transition last:border-b-0 hover:bg-surface-accentSoft/35",
              isSelected &&
                "bg-surface-accentSoft/60 shadow-[inset_2px_0_0_0_rgba(249,115,22,1)]"
            )}
            onClick={() => onSelect(incident)}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 flex-1 space-y-2">
                <div className="type-mono-sm text-content-secondary">{incident.id}</div>
                <div className="space-y-1">
                  <h3 className="text-body-sm font-medium text-content-primary">
                    {incident.title}
                  </h3>
                  <p className="text-body-sm text-content-muted">{incident.summary}</p>
                </div>
              </div>
              <div className="flex flex-wrap items-center justify-end gap-2">
                <PriorityChip priority={incident.priority} />
                <IncidentStateBadge state={incident.state} />
              </div>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Badge tone="brand">{incident.linkedAlertsCount} linked alerts</Badge>
              <Badge tone="outline">{incident.primaryAsset}</Badge>
              <Badge tone="outline">{incident.lastUpdated}</Badge>
              {isTerminal ? <Badge tone="danger">terminal</Badge> : null}
            </div>
            {index === 0 && !selectedIncidentId ? (
              <p className="mt-3 text-body-sm text-content-muted">
                Select a target incident to preview it before linking.
              </p>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

function IncidentPreviewCard({ incident }: IncidentPreviewCardProps) {
  if (!incident) {
    return (
      <Card className="h-full">
        <CardHeader className="block space-y-3">
          <div>
            <p className="type-label-md">Incident preview</p>
            <CardTitle>Select an incident</CardTitle>
            <CardDescription>
              Review the incident target before you confirm the link action.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <p className="type-body-sm">
            The selected incident preview will show the incident id, title, priority,
            state, and current linked-alert count here.
          </p>
        </CardContent>
      </Card>
    );
  }

  const isTerminal =
    incident.state === "resolved" || incident.state === "false_positive";

  return (
    <Card className="h-full">
      <CardHeader className="block space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <p className="type-label-md">Selected incident</p>
            <CardTitle>{incident.title}</CardTitle>
            <CardDescription className="type-mono-sm">
              {incident.id}
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <PriorityChip priority={incident.priority} />
            <IncidentStateBadge state={incident.state} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        <div className="flex flex-wrap gap-2">
          <Badge tone="brand">{incident.linkedAlertsCount} linked alerts</Badge>
          <Badge tone="outline">{incident.sourceType}</Badge>
          {isTerminal ? <Badge tone="danger">cannot accept new links</Badge> : null}
        </div>
        <p className="type-body-sm">{incident.summary}</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <p className="type-label-sm">Primary asset</p>
            <p className="type-mono-sm">{incident.primaryAsset}</p>
          </div>
          <div className="space-y-1">
            <p className="type-label-sm">Assignee</p>
            <p className="type-mono-sm">{incident.assignee}</p>
          </div>
          <div className="space-y-1">
            <p className="type-label-sm">Detection</p>
            <p className="type-mono-sm">{incident.detectionType}</p>
          </div>
          <div className="space-y-1">
            <p className="type-label-sm">Last updated</p>
            <p className="type-mono-sm">{incident.lastUpdated}</p>
          </div>
        </div>
        {isTerminal ? (
          <p className="text-body-sm text-status-danger">
            This incident is already terminal. Select an active incident or create a
            new one instead.
          </p>
        ) : (
          <p className="type-body-sm">
            Confirming this action will add the current alert into this incident's
            evidence set and refresh the investigation view.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function NewIncidentPreviewCard({
  title,
  summary
}: {
  title: string;
  summary: string;
}) {
  const resolvedTitle = title.trim() || "Use alert title";
  const resolvedSummary = summary.trim() || "Use alert summary and normalized context";

  return (
    <Card className="h-full">
      <CardHeader className="block space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <p className="type-label-md">New incident preview</p>
            <CardTitle>{resolvedTitle}</CardTitle>
            <CardDescription>
              The backend will create a new triaged incident and link this alert into it.
            </CardDescription>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge tone="brand">new incident</Badge>
            <IncidentStateBadge state="triaged" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 pt-0">
        <p className="type-body-sm">{resolvedSummary}</p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <p className="type-label-sm">Priority</p>
            <p className="type-body-sm">
              Derived server-side from the alert severity and risk score.
            </p>
          </div>
          <div className="space-y-1">
            <p className="type-label-sm">Initial state</p>
            <p className="type-mono-sm">triaged</p>
          </div>
        </div>
        <p className="type-body-sm">
          Use this path when the alert should start a new investigation instead of being
          grouped into an existing incident.
        </p>
      </CardContent>
    </Card>
  );
}

export function LinkIncidentModal({
  open,
  alertId,
  alertTitle,
  alertSummary,
  onClose,
  onSuccess
}: LinkIncidentModalProps) {
  const [mode, setMode] = useState<LinkMode>("existing");
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const [page, setPage] = useState(1);
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  const [newIncidentTitle, setNewIncidentTitle] = useState(alertTitle);
  const [newIncidentSummary, setNewIncidentSummary] = useState(alertSummary);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const query = useMemo<IncidentsListQuery>(
    () => ({
      search: deferredSearch,
      priority: "",
      state: "",
      detectionType: "",
      assignee: "",
      sortBy: "updated_at",
      sortDirection: "desc",
      page,
      pageSize: 6
    }),
    [deferredSearch, page]
  );

  const { data, isLoading, error, reload } = useIncidentsList(query);
  const incidents = useMemo(() => data?.items ?? [], [data?.items]);
  const selectedIncident =
    incidents.find((incident) => incident.id === selectedIncidentId) ?? null;
  const selectedIncidentIsTerminal =
    selectedIncident?.state === "resolved" ||
    selectedIncident?.state === "false_positive";

  useEffect(() => {
    if (!selectedIncidentId) {
      return;
    }

    const selectedStillVisible = incidents.some(
      (incident) => incident.id === selectedIncidentId
    );
    if (!selectedStillVisible) {
      setSelectedIncidentId(null);
    }
  }, [incidents, selectedIncidentId]);

  function handleModeChange(nextMode: LinkMode) {
    startTransition(() => {
      setMode(nextMode);
      setSubmitError(null);
      if (nextMode === "existing") {
        setPage(1);
      } else {
        setSelectedIncidentId(null);
      }
    });
  }

  async function handleConfirm() {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const response =
        mode === "existing"
          ? await linkAlertToIncident(alertId, {
              incident_id: selectedIncident?.id
            })
          : await linkAlertToIncident(alertId, {
              create_new: true,
              title: newIncidentTitle.trim() || undefined,
              summary: newIncidentSummary.trim() || undefined
            });

      onSuccess(response.message);
    } catch (linkError: unknown) {
      setSubmitError(
        linkError instanceof Error ? linkError.message : "Incident link failed."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const confirmDisabled =
    isSubmitting ||
    (mode === "existing"
      ? !selectedIncident || selectedIncidentIsTerminal
      : false);

  return (
    <Modal
      open={open}
      title="Link Alert To Incident"
      description="Choose whether this alert should join an existing investigation or create a new one."
      size="lg"
      onClose={onClose}
      footer={
        <div className="space-y-3">
          {submitError ? (
            <p className="text-body-sm text-status-danger">{submitError}</p>
          ) : (
            <p className="type-body-sm">
              {mode === "existing"
                ? "Select the target incident, review the preview, then confirm the link."
                : "Review the new incident preview, then confirm the creation and link action."}
            </p>
          )}
          <div className="flex flex-wrap items-center justify-end gap-3">
            <Button variant="ghost" size="sm" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              data-testid="link-incident-confirm-btn"
              onClick={handleConfirm}
              disabled={confirmDisabled}
            >
              {isSubmitting
                ? mode === "existing"
                  ? "Linking..."
                  : "Creating..."
                : mode === "existing"
                  ? "Link selected incident"
                  : "Create and link incident"}
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-5">
        <div className="inline-flex rounded-field border border-border-subtle bg-surface-subtle/60 p-1">
          <Button
            size="sm"
            variant={mode === "existing" ? "primary" : "ghost"}
            data-testid="link-incident-mode-existing-btn"
            onClick={() => handleModeChange("existing")}
          >
            Existing incident
          </Button>
          <Button
            size="sm"
            variant={mode === "new" ? "primary" : "ghost"}
            data-testid="link-incident-mode-new-btn"
            onClick={() => handleModeChange("new")}
          >
            Create new
          </Button>
        </div>

        {mode === "existing" ? (
          <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <SearchInput
                  data-testid="link-incident-search-input"
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                    setSubmitError(null);
                  }}
                  placeholder="Search incidents by id, title, asset, analyst, or detection type"
                />
                <Badge tone="outline">{data?.total ?? 0} matches</Badge>
              </div>

              {isLoading ? (
                <LoadingCard className="min-h-[260px]" />
              ) : error ? (
                <Card>
                  <CardContent className="space-y-4 pt-6">
                    <div className="space-y-2">
                      <p className="type-label-md">Incident search failed</p>
                      <p className="type-body-sm">{error}</p>
                    </div>
                    <Button variant="secondary" size="sm" onClick={reload}>
                      Retry incident search
                    </Button>
                  </CardContent>
                </Card>
              ) : incidents.length ? (
                <div className="space-y-4">
                  <IncidentCandidateList
                    incidents={incidents}
                    selectedIncidentId={selectedIncidentId}
                    onSelect={(incident) => {
                      setSelectedIncidentId(incident.id);
                      setSubmitError(null);
                    }}
                  />
                  {data?.meta ? (
                    <TablePagination
                      page={data.meta.page}
                      pageSize={data.meta.pageSize}
                      total={data.meta.total}
                      totalPages={data.meta.totalPages}
                      itemLabel="incidents"
                      onPageChange={setPage}
                    />
                  ) : null}
                </div>
              ) : (
                <EmptyState
                  iconName="incidents"
                  title="No incidents matched this search"
                  description="Broaden the incident search or switch to Create new if this alert should start a fresh investigation."
                  action={
                    search ? (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => {
                          setSearch("");
                          setPage(1);
                        }}
                      >
                        Clear search
                      </Button>
                    ) : undefined
                  }
                />
              )}
            </div>

            <IncidentPreviewCard incident={selectedIncident} />
          </div>
        ) : (
          <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <div className="space-y-4">
              <Input
                label="Incident title"
                value={newIncidentTitle}
                onChange={(event) => {
                  setNewIncidentTitle(event.target.value);
                  setSubmitError(null);
                }}
                placeholder={alertTitle}
              />
              <Textarea
                label="Incident summary"
                value={newIncidentSummary}
                onChange={(event) => {
                  setNewIncidentSummary(event.target.value);
                  setSubmitError(null);
                }}
                placeholder={alertSummary}
              />
              <Card tone="subtle">
                <CardContent className="space-y-3 pt-6">
                  <p className="type-label-md">Create-new guidance</p>
                  <p className="type-body-sm">
                    Use a new incident only when this alert should not be grouped into an
                    ongoing investigation. If you leave the fields unchanged, the backend
                    will still accept the alert-backed defaults cleanly.
                  </p>
                </CardContent>
              </Card>
            </div>

            <NewIncidentPreviewCard
              title={newIncidentTitle}
              summary={newIncidentSummary}
            />
          </div>
        )}
      </div>
    </Modal>
  );
}
