import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MetricCard } from "../components/data-display/MetricCard";
import { SearchFilterToolbar } from "../components/data-display/SearchFilterToolbar";
import { TablePagination } from "../components/data-display/TablePagination";
import { EmptyState } from "../components/feedback/EmptyState";
import { ErrorState } from "../components/feedback/ErrorState";
import { LoadingCard, LoadingTable } from "../components/feedback/LoadingState";
import { QueryWarnings } from "../components/feedback/QueryWarnings";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { SearchInput } from "../components/ui/SearchInput";
import { Select } from "../components/ui/Select";
import { AlertsTable } from "../features/alerts/components/AlertsTable";
import { useAlertsList } from "../features/alerts/service";
import type { AlertsDateRange, AlertsListQuery, AlertsSortField } from "../features/alerts/types";
import { formatTokenLabel } from "../lib/formatters";
import { supportedDetectionSelectOptions } from "../lib/supportedDetections";
import { pageBlueprints } from "../lib/theme/tokens";

export function AlertsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState<AlertsListQuery["severity"]>("");
  const [status, setStatus] = useState<AlertsListQuery["status"]>("");
  const [detectionType, setDetectionType] = useState("");
  const [sourceType, setSourceType] = useState<AlertsListQuery["sourceType"]>("");
  const [asset, setAsset] = useState("");
  const [dateRange, setDateRange] = useState<AlertsDateRange>("24h");
  const [sortBy, setSortBy] = useState<AlertsSortField>("timestamp");
  const [sortDirection, setSortDirection] = useState<AlertsListQuery["sortDirection"]>("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const query = useMemo<AlertsListQuery>(
    () => ({
      search,
      severity,
      status,
      detectionType,
      sourceType,
      asset,
      dateRange,
      sortBy,
      sortDirection,
      page,
      pageSize
    }),
    [
      asset,
      dateRange,
      detectionType,
      page,
      pageSize,
      search,
      severity,
      sortBy,
      sortDirection,
      sourceType,
      status
    ]
  );

  const { data, isLoading, error, reload } = useAlertsList(query);
  const alerts = data?.items ?? [];
  const meta = data?.meta;

  if (error) {
    return (
      <ErrorState
        title="Alerts could not be loaded"
        description="The alerts surface is running against the backend query layer, but the current request failed."
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
            <Badge tone="outline">{data?.total ?? 0} alerts in feed</Badge>
            <Badge tone="brand">
              {alerts.filter((alert) => (alert.riskScore ?? 0) >= 70).length} high-risk on page
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
              label="Matching alerts"
              value={String(meta?.total ?? 0)}
              detail="Alerts matching filters in the four validated threat categories."
              tone="highlight"
            />
            <MetricCard
              label="Critical or high"
              value={String(
                alerts.filter(
                  (alert) => alert.severity === "critical" || alert.severity === "high"
                ).length
              )}
              detail="On this page: worst severity first when you sort by severity."
              tone="warning"
            />
            <MetricCard
              label="Pending response"
              value={String(
                alerts.filter((alert) => alert.status === "pending_response").length
              )}
              detail="On this page: automation queued or running—check response history for outcomes."
            />
          </>
        )}
      </section>

      <SearchFilterToolbar
        title="Alert triage filters"
        description="Search by ID, asset, IP, username, or event ID. Wazuh/Suricata raise detections; optional TensorFlow AI ranks them (Low/Medium/High). Filter by severity, status, validated threat categories, source, asset, and time window."
        search={
          <SearchInput
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        }
        filters={
          <>
            <Select
              aria-label="Filter alerts by severity"
              value={severity}
              onChange={(event) => {
                setSeverity(event.target.value as AlertsListQuery["severity"]);
                setPage(1);
              }}
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
              onChange={(event) => {
                setStatus(event.target.value as AlertsListQuery["status"]);
                setPage(1);
              }}
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
              onChange={(event) => {
                setDetectionType(event.target.value);
                setPage(1);
              }}
              placeholder="Detection"
              options={supportedDetectionSelectOptions()}
            />
            <Select
              aria-label="Filter alerts by source type"
              value={sourceType}
              onChange={(event) => {
                setSourceType(event.target.value as AlertsListQuery["sourceType"]);
                setPage(1);
              }}
              placeholder="Source"
              options={[
                { value: "wazuh", label: "Wazuh" },
                { value: "suricata", label: "Suricata" }
              ]}
            />
            <Select
              aria-label="Filter alerts by asset"
              value={asset}
              onChange={(event) => {
                setAsset(event.target.value);
                setPage(1);
              }}
              placeholder="Asset"
              options={[...new Set(alerts.map((alert) => alert.asset))].map((value) => ({
                value,
                label: value
              }))}
            />
            <Select
              aria-label="Filter alerts by date range"
              value={dateRange}
              onChange={(event) => {
                setDateRange(event.target.value as AlertsDateRange);
                setPage(1);
              }}
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
          <>
            <Select
              aria-label="Sort alerts by"
              value={sortBy}
              onChange={(event) => {
                setSortBy(event.target.value as AlertsSortField);
                setPage(1);
              }}
              options={[
                { value: "timestamp", label: "Newest activity" },
                { value: "severity", label: "Severity" },
                { value: "risk_score", label: "Risk score" }
              ]}
            />
            <Select
              aria-label="Alert sort direction"
              value={sortDirection}
              onChange={(event) => {
                setSortDirection(event.target.value as AlertsListQuery["sortDirection"]);
                setPage(1);
              }}
              options={[
                { value: "desc", label: "Descending" },
                { value: "asc", label: "Ascending" }
              ]}
            />
            <Select
              aria-label="Alerts page size"
              value={String(pageSize)}
              onChange={(event) => {
                setPageSize(Number(event.target.value));
                setPage(1);
              }}
              options={[
                { value: "10", label: "10 / page" },
                { value: "25", label: "25 / page" },
                { value: "50", label: "50 / page" }
              ]}
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSearch("");
                setSeverity("");
                setStatus("");
                setDetectionType("");
                setSourceType("");
                setAsset("");
                setDateRange("24h");
                setSortBy("timestamp");
                setSortDirection("desc");
                setPage(1);
                setPageSize(10);
              }}
            >
              Reset filters
            </Button>
          </>
        }
        activeFilters={[
          severity && `severity:${severity}`,
          status && `status:${status}`,
          detectionType && `detection:${formatTokenLabel(detectionType)}`,
          sourceType && `source:${sourceType}`,
          asset && `asset:${asset}`,
          dateRange !== "24h" && `range:${dateRange}`,
          sortBy !== "timestamp" && `sort:${sortBy}`,
          sortDirection !== "desc" && `dir:${sortDirection}`
        ].filter(Boolean) as string[]}
      />

      <QueryWarnings warnings={meta?.warnings ?? []} />

      {isLoading ? (
        <LoadingTable columns={9} rows={6} />
      ) : alerts.length ? (
        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="type-body-sm">
              Open a row for detection context, evidence, prioritization rationale, responses, and notifications.
            </p>
            <Badge tone="outline">risk 70+ = review soon</Badge>
          </div>
          <AlertsTable
            alerts={alerts}
            onRowClick={(alert) => navigate(`/alerts/${alert.id}`)}
            footer={
              meta ? (
                <TablePagination
                  page={meta.page}
                  pageSize={meta.pageSize}
                  total={meta.total}
                  totalPages={meta.totalPages}
                  itemLabel="alerts"
                  onPageChange={setPage}
                />
              ) : null
            }
          />
        </section>
      ) : (
        <EmptyState
          iconName="alerts"
          title="No alerts match the current filters"
          description="Broaden the time window or clear filters to see alerts again. "
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setSearch("");
                setSeverity("");
                setStatus("");
                setDetectionType("");
                setSourceType("");
                setAsset("");
                setDateRange("24h");
                setSortBy("timestamp");
                setSortDirection("desc");
                setPage(1);
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