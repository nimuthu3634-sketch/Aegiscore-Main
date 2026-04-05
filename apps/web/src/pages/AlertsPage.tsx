import { useState } from "react";
import { useNavigate } from "react-router-dom";
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
import { AlertsTable } from "../features/alerts/components/AlertsTable";
import { useAlertsList } from "../features/alerts/service";
import { pageBlueprints } from "../lib/theme/tokens";

type AlertsDateRange = "4h" | "12h" | "24h" | "all";

const dateRangeThresholds: Record<Exclude<AlertsDateRange, "all">, number> = {
  "4h": 4 * 60 * 60 * 1000,
  "12h": 12 * 60 * 60 * 1000,
  "24h": 24 * 60 * 60 * 1000
};

function toUtcDate(value: string) {
  return new Date(value.replace(" UTC", "Z").replace(" ", "T"));
}

export function AlertsPage() {
  const navigate = useNavigate();
  const { data, isLoading, error, reload } = useAlertsList();
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [detectionType, setDetectionType] = useState("");
  const [sourceType, setSourceType] = useState("");
  const [asset, setAsset] = useState("");
  const [dateRange, setDateRange] = useState<AlertsDateRange>("24h");

  const alerts = data?.items ?? [];
  const generatedAt = data?.generatedAt ? new Date(data.generatedAt) : null;

  const filteredAlerts = alerts.filter((alert) => {
    const normalizedQuery = query.trim().toLowerCase();
    const matchesQuery =
      !normalizedQuery ||
      [
        alert.id,
        alert.detectionType,
        alert.asset,
        alert.sourceIp,
        alert.destinationPort ?? "",
        alert.username,
        alert.eventId
      ].some((value) => value.toLowerCase().includes(normalizedQuery));

    const matchesSeverity = !severity || alert.severity === severity;
    const matchesStatus = !status || alert.status === status;
    const matchesDetection = !detectionType || alert.detectionType === detectionType;
    const matchesSource = !sourceType || alert.sourceType === sourceType;
    const matchesAsset = !asset || alert.asset === asset;

    const matchesDateRange =
      !generatedAt ||
      dateRange === "all" ||
      generatedAt.getTime() - toUtcDate(alert.timestamp).getTime() <=
        dateRangeThresholds[dateRange];

    return (
      matchesQuery &&
      matchesSeverity &&
      matchesStatus &&
      matchesDetection &&
      matchesSource &&
      matchesAsset &&
      matchesDateRange
    );
  });

  if (error) {
    return (
      <ErrorState
        title="Alerts could not be loaded"
        description="The alerts surface is ready for API integration, but the current dataset request failed."
        details={error}
        action={
          <Button variant="secondary" size="sm" onClick={reload}>
            Retry alerts
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-section">
      <PageHeader
        eyebrow={pageBlueprints.alerts.eyebrow}
        title={pageBlueprints.alerts.title}
        description={pageBlueprints.alerts.description}
        meta={
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="outline">{alerts.length} seeded alerts</Badge>
            <Badge tone="brand">
              {alerts.filter((alert) => alert.riskScore >= 80).length} high-risk
            </Badge>
          </div>
        }
        actions={
          <Button variant="secondary" size="sm">
            Export queue
          </Button>
        }
      />

      <section className="grid gap-4 md:grid-cols-3">
        {isLoading ? (
          <>
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
          </>
        ) : (
          <>
            <MetricCard
              label="Visible alerts"
              value={String(filteredAlerts.length)}
              detail="Current triage set after search and filter conditions."
              tone="highlight"
            />
            <MetricCard
              label="Critical or high"
              value={String(
                filteredAlerts.filter(
                  (alert) =>
                    alert.severity === "critical" || alert.severity === "high"
                ).length
              )}
              detail="Highest priority analyst work stays visible first."
              tone="warning"
            />
            <MetricCard
              label="Pending response"
              value={String(
                filteredAlerts.filter(
                  (alert) => alert.status === "pending_response"
                ).length
              )}
              detail="Alerts already close to an automated or analyst action."
            />
          </>
        )}
      </section>

      <SearchFilterToolbar
        title="Alert triage filters"
        description="Search by alert ID, asset, IP, username, or event ID and refine by the most operationally relevant dimensions."
        search={<SearchInput value={query} onChange={(event) => setQuery(event.target.value)} />}
        filters={
          <>
            <Select
              aria-label="Filter alerts by severity"
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
              placeholder="Severity"
              options={[
                { value: "critical", label: "Critical" },
                { value: "high", label: "High" },
                { value: "medium", label: "Medium" },
                { value: "low", label: "Low" }
              ]}
            />
            <Select
              aria-label="Filter alerts by status"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
              placeholder="Status"
              options={[
                { value: "new", label: "New" },
                { value: "triaged", label: "Triaged" },
                { value: "investigating", label: "Investigating" },
                { value: "contained", label: "Contained" },
                { value: "resolved", label: "Resolved" },
                { value: "pending_response", label: "Pending response" }
              ]}
            />
            <Select
              aria-label="Filter alerts by detection type"
              value={detectionType}
              onChange={(event) => setDetectionType(event.target.value)}
              placeholder="Detection"
              options={[...new Set(alerts.map((alert) => alert.detectionType))].map(
                (value) => ({ value, label: value })
              )}
            />
            <Select
              aria-label="Filter alerts by source type"
              value={sourceType}
              onChange={(event) => setSourceType(event.target.value)}
              placeholder="Source"
              options={[...new Set(alerts.map((alert) => alert.sourceType))].map(
                (value) => ({ value, label: value })
              )}
            />
            <Select
              aria-label="Filter alerts by asset"
              value={asset}
              onChange={(event) => setAsset(event.target.value)}
              placeholder="Asset"
              options={[...new Set(alerts.map((alert) => alert.asset))].map(
                (value) => ({ value, label: value })
              )}
            />
            <Select
              aria-label="Filter alerts by date range"
              value={dateRange}
              onChange={(event) =>
                setDateRange(event.target.value as AlertsDateRange)
              }
              placeholder="Date range"
              options={[
                { value: "4h", label: "Last 4 hours" },
                { value: "12h", label: "Last 12 hours" },
                { value: "24h", label: "Last 24 hours" },
                { value: "all", label: "All available" }
              ]}
            />
          </>
        }
        actions={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setQuery("");
              setSeverity("");
              setStatus("");
              setDetectionType("");
              setSourceType("");
              setAsset("");
              setDateRange("24h");
            }}
          >
            Reset filters
          </Button>
        }
        activeFilters={[
          severity && `severity:${severity}`,
          status && `status:${status}`,
          detectionType && `detection:${detectionType}`,
          sourceType && `source:${sourceType}`,
          asset && `asset:${asset}`,
          dateRange !== "24h" && `range:${dateRange}`
        ].filter(Boolean) as string[]}
      />

      {isLoading ? (
        <LoadingTable columns={9} rows={6} />
      ) : filteredAlerts.length ? (
        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="type-body-sm">
              Select a row to open the detailed investigation surface for that alert.
            </p>
            <Badge tone="outline">detail route enabled</Badge>
          </div>
          <AlertsTable
            alerts={filteredAlerts}
            onRowClick={(alert) => navigate(`/alerts/${alert.id}`)}
          />
        </section>
      ) : (
        <EmptyState
          iconName="alerts"
          title="No alerts match the current filters"
          description="Adjust the severity, status, source, or date range filters to bring matching alerts back into the queue."
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setQuery("");
                setSeverity("");
                setStatus("");
                setDetectionType("");
                setSourceType("");
                setAsset("");
                setDateRange("24h");
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
