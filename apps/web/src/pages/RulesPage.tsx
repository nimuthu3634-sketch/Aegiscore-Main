import { useMemo, useState } from "react";
import { MetricCard } from "../components/data-display/MetricCard";
import { SearchFilterToolbar } from "../components/data-display/SearchFilterToolbar";
import { EmptyState } from "../components/feedback/EmptyState";
import { ErrorState } from "../components/feedback/ErrorState";
import { LoadingCard, LoadingTable } from "../components/feedback/LoadingState";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SearchInput } from "../components/ui/SearchInput";
import { Select } from "../components/ui/Select";
import { PoliciesTable } from "../features/policies/components/PoliciesTable";
import { updatePolicyEnabled, usePolicies } from "../features/policies/service";
import type { PolicyMode, PolicyRecord, PolicyTarget } from "../features/policies/types";
import { getStoredSessionRole } from "../lib/api";
import { formatTokenLabel } from "../lib/formatters";
import { supportedDetectionSelectOptions } from "../lib/supportedDetections";
import { pageBlueprints } from "../lib/theme/tokens";

type EnabledFilter = "" | "enabled" | "disabled";

export function RulesPage() {
  const [search, setSearch] = useState("");
  const [detectionType, setDetectionType] = useState("");
  const [mode, setMode] = useState<PolicyMode | "">("");
  const [target, setTarget] = useState<PolicyTarget | "">("");
  const [enabled, setEnabled] = useState<EnabledFilter>("");
  const [pendingPolicyId, setPendingPolicyId] = useState<string | null>(null);
  const [updateMessage, setUpdateMessage] = useState<string | null>(null);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const canTogglePolicies = getStoredSessionRole() === "admin";

  const { data, isLoading, error, reload } = usePolicies();
  const policies = useMemo(() => data?.items ?? [], [data]);

  const filteredPolicies = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return policies.filter((policy) => {
      const matchesSearch =
        !normalizedSearch ||
        [
          policy.name,
          policy.description ?? "",
          policy.detectionType,
          policy.actionType,
          policy.target
        ]
          .join(" ")
          .toLowerCase()
          .includes(normalizedSearch);

      const matchesDetection =
        !detectionType || policy.detectionType === detectionType;
      const matchesMode = !mode || policy.mode === mode;
      const matchesTarget = !target || policy.target === target;
      const matchesEnabled =
        !enabled ||
        (enabled === "enabled" ? policy.enabled : !policy.enabled);

      return (
        matchesSearch &&
        matchesDetection &&
        matchesMode &&
        matchesTarget &&
        matchesEnabled
      );
    });
  }, [detectionType, enabled, mode, policies, search, target]);

  const detectionOptions = supportedDetectionSelectOptions();

  const summary = useMemo(
    () => ({
      enabled: policies.filter((policy) => policy.enabled).length,
      dryRun: policies.filter((policy) => policy.mode === "dry-run").length,
      live: policies.filter((policy) => policy.mode === "live").length,
      incident: policies.filter((policy) => policy.target === "incident").length
    }),
    [policies]
  );

  async function handleToggle(policy: PolicyRecord) {
    if (!canTogglePolicies) {
      setUpdateError(
        "Policy enable/disable requires an admin session. Analyst sessions are read-only on this page."
      );
      setUpdateMessage(null);
      return;
    }

    setPendingPolicyId(policy.id);
    setUpdateMessage(null);
    setUpdateError(null);

    try {
      const response = await updatePolicyEnabled(policy.id, !policy.enabled);
      setUpdateMessage(response.message);
      reload();
    } catch (toggleError: unknown) {
      setUpdateError(
        toggleError instanceof Error
          ? toggleError.message
          : "Policy update failed."
      );
    } finally {
      setPendingPolicyId(null);
    }
  }

  if (error && !data) {
    return (
      <ErrorState
        title="Policies could not be loaded"
        description="The Rules / Policies page is connected to the backend policy system, but the current request failed."
        details={error}
        action={
          <Button variant="secondary" size="sm" onClick={reload}>
            Retry policies
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-section">
      <PageHeader
        eyebrow={pageBlueprints.rules.eyebrow}
        title={pageBlueprints.rules.title}
        description={pageBlueprints.rules.description}
        meta={
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="brand">real backend policies</Badge>
            {data ? <Badge tone="outline">fetched {data.fetchedAt}</Badge> : null}
          </div>
        }
      />

      {error && data ? (
        <ErrorState
          title="Policy data is stale"
          description="The last successful policy snapshot is still visible, but the latest refresh failed."
          details={error}
          action={
            <Button variant="secondary" size="sm" onClick={reload}>
              Retry refresh
            </Button>
          }
          tone="warning"
        />
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {isLoading && !data ? (
          <>
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
          </>
        ) : (
          <>
            <MetricCard
              label="Enabled policies"
              value={String(summary.enabled)}
              detail="Active automated response policies currently enforced by the backend."
              tone="highlight"
            />
            <MetricCard
              label="Dry-run policies"
              value={String(summary.dryRun)}
              detail="Policies simulating action outcomes without live external changes."
            />
            <MetricCard
              label="Live policies"
              value={String(summary.live)}
              detail="Policies allowed to record live outcomes through safe internal actions or adapters."
              tone="warning"
            />
            <MetricCard
              label="Incident-scoped"
              value={String(summary.incident)}
              detail="Policies evaluating incident rollups rather than individual alerts."
            />
          </>
        )}
      </section>

      <SearchFilterToolbar
        title="Policy filters"
        description={
          canTogglePolicies
            ? "Backend-owned policies can be enabled or disabled here. Threshold, action, and mode edits remain backend-managed in this build."
            : "Backend-owned policies are visible here in analyst read-only mode. Policy enable/disable requires an admin session."
        }
        search={
          <SearchInput
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        }
        filters={
          <>
            <Select
              aria-label="Filter policies by detection type"
              value={detectionType}
              onChange={(event) => setDetectionType(event.target.value)}
              placeholder="Detection type"
              options={detectionOptions}
            />
            <Select
              aria-label="Filter policies by mode"
              value={mode}
              onChange={(event) => setMode(event.target.value as PolicyMode | "")}
              placeholder="Mode"
              options={[
                { value: "dry-run", label: "Dry-run" },
                { value: "live", label: "Live" }
              ]}
            />
            <Select
              aria-label="Filter policies by target"
              value={target}
              onChange={(event) => setTarget(event.target.value as PolicyTarget | "")}
              placeholder="Target"
              options={[
                { value: "alert", label: "Alert" },
                { value: "incident", label: "Incident" }
              ]}
            />
            <Select
              aria-label="Filter policies by enabled state"
              value={enabled}
              onChange={(event) => setEnabled(event.target.value as EnabledFilter)}
              placeholder="Enabled state"
              options={[
                { value: "enabled", label: "Enabled" },
                { value: "disabled", label: "Disabled" }
              ]}
            />
          </>
        }
        actions={
          <>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearch("");
                setDetectionType("");
                setMode("");
                setTarget("");
                setEnabled("");
                setUpdateError(null);
                setUpdateMessage(null);
              }}
            >
              Reset filters
            </Button>
            <Button variant="secondary" size="sm" onClick={reload}>
              Refresh policies
            </Button>
          </>
        }
        activeFilters={[
          detectionType && `detection:${formatTokenLabel(detectionType)}`,
          mode && `mode:${mode}`,
          target && `target:${target}`,
          enabled && `state:${enabled}`
        ].filter(Boolean) as string[]}
      />

      {updateError ? (
        <p className="text-body-sm text-status-danger">{updateError}</p>
      ) : updateMessage ? (
        <p className="text-body-sm text-status-success">{updateMessage}</p>
      ) : !canTogglePolicies ? (
        <p className="type-body-sm" data-testid="policy-admin-only-hint">
          Admin role required: analysts can review policy state but cannot toggle enablement.
        </p>
      ) : null}

      {isLoading && !data ? (
        <LoadingTable columns={8} rows={6} />
      ) : filteredPolicies.length ? (
        <PoliciesTable
          policies={filteredPolicies}
          pendingPolicyId={pendingPolicyId}
          onToggle={handleToggle}
          canToggle={canTogglePolicies}
        />
      ) : (
        <EmptyState
          iconName="rules"
          title="No policies match the current filters"
          description="Clear the local policy filters to see the backend-managed automated response rules again."
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSearch("");
                setDetectionType("");
                setMode("");
                setTarget("");
                setEnabled("");
              }}
            >
              Clear filters
            </Button>
          }
        />
      )}
    </div>
  );
}
