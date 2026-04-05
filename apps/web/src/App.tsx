import { startTransition, useDeferredValue, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { ChartCard } from "./components/data-display/ChartCard";
import {
  DataTable,
  type TableColumn
} from "./components/data-display/DataTable";
import { MetricCard } from "./components/data-display/MetricCard";
import { SearchFilterToolbar } from "./components/data-display/SearchFilterToolbar";
import { EmptyState } from "./components/feedback/EmptyState";
import { ErrorState } from "./components/feedback/ErrorState";
import {
  LoadingCard,
  LoadingTable
} from "./components/feedback/LoadingState";
import { Modal } from "./components/feedback/Modal";
import { AppShell } from "./components/layout/AppShell";
import { PageHeader } from "./components/layout/PageHeader";
import { Badge } from "./components/ui/Badge";
import { Button } from "./components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "./components/ui/Card";
import { Icon } from "./components/ui/Icon";
import { Input } from "./components/ui/Input";
import { SearchInput } from "./components/ui/SearchInput";
import { Select } from "./components/ui/Select";
import { SeverityChip } from "./components/ui/SeverityChip";
import { StatusChip } from "./components/ui/StatusChip";
import { Textarea } from "./components/ui/Textarea";
import { fetchHealthResponse, type HealthResponse } from "./lib/api";
import {
  pageBlueprints,
  primaryNavigation,
  type HealthTone,
  type NavKey,
  type Severity,
  type StatusTone
} from "./lib/theme/tokens";

type AlertRow = {
  id: string;
  timestamp: string;
  source: "Wazuh" | "Suricata";
  detection: string;
  severity: Severity;
  risk: string;
  asset: string;
  endpoint: string;
  status: StatusTone;
  analyst: string;
  port: string;
  eventId: string;
};

const alertActivity = [
  { window: "06:00", alerts: 7 },
  { window: "08:00", alerts: 11 },
  { window: "10:00", alerts: 16 },
  { window: "12:00", alerts: 13 },
  { window: "14:00", alerts: 19 },
  { window: "16:00", alerts: 14 },
  { window: "18:00", alerts: 12 }
];

const severityDistribution = [
  { detection: "brute_force", critical: 2, high: 6, medium: 8, low: 1 },
  {
    detection: "file_integrity_violation",
    critical: 1,
    high: 3,
    medium: 4,
    low: 1
  },
  { detection: "port_scan", critical: 1, high: 4, medium: 5, low: 2 },
  {
    detection: "unauthorized_user_creation",
    critical: 2,
    high: 2,
    medium: 2,
    low: 0
  }
];

const alertRows: AlertRow[] = [
  {
    id: "ALRT-1084",
    timestamp: "2026-04-05 08:14:09 UTC",
    source: "Wazuh",
    detection: "brute_force",
    severity: "high",
    risk: "87 High",
    asset: "edge-auth-01",
    endpoint: "10.42.0.21",
    status: "investigating",
    analyst: "N. Silva",
    port: "22",
    eventId: "evt-54fd8c"
  },
  {
    id: "ALRT-1085",
    timestamp: "2026-04-05 08:18:44 UTC",
    source: "Suricata",
    detection: "port_scan",
    severity: "medium",
    risk: "61 Medium",
    asset: "branch-fw-02",
    endpoint: "172.16.4.8",
    status: "triaged",
    analyst: "SOC Queue",
    port: "3389",
    eventId: "evt-7bc310"
  },
  {
    id: "ALRT-1086",
    timestamp: "2026-04-05 08:24:17 UTC",
    source: "Wazuh",
    detection: "unauthorized_user_creation",
    severity: "critical",
    risk: "95 Critical",
    asset: "finance-dc-01",
    endpoint: "10.42.11.9",
    status: "pending_response",
    analyst: "R. Perera",
    port: "389",
    eventId: "evt-a190d2"
  },
  {
    id: "ALRT-1087",
    timestamp: "2026-04-05 08:32:51 UTC",
    source: "Wazuh",
    detection: "file_integrity_violation",
    severity: "high",
    risk: "79 High",
    asset: "ops-files-03",
    endpoint: "10.42.7.54",
    status: "contained",
    analyst: "J. Fernando",
    port: "445",
    eventId: "evt-c8ae24"
  }
];

const pageReadiness: Record<
  Exclude<NavKey, "overview">,
  { surface: string; readyComponents: string[] }
> = {
  alerts: {
    surface: "High-density alert triage surface",
    readyComponents: [
      "Page header",
      "Search and filter toolbar",
      "Dense alert table",
      "Severity chips",
      "Status chips"
    ]
  },
  incidents: {
    surface: "Investigation queue management",
    readyComponents: [
      "Page header",
      "Queue table",
      "Side summary card",
      "Workflow chips",
      "Modal actions"
    ]
  },
  assets: {
    surface: "Endpoint inventory and health surface",
    readyComponents: [
      "Page header",
      "Inventory table",
      "SOC monospace metadata",
      "Metric cards",
      "Filter toolbar"
    ]
  },
  responses: {
    surface: "Response audit and execution timeline",
    readyComponents: [
      "History table",
      "Status chips",
      "Result cards",
      "Error states",
      "Modal confirmation shell"
    ]
  },
  rules: {
    surface: "Policy editing and scope control",
    readyComponents: [
      "Split-panel shell",
      "Form controls",
      "Textareas",
      "Danger and warning states",
      "Buttons"
    ]
  },
  reports: {
    surface: "Operational reports and exports",
    readyComponents: [
      "Chart cards",
      "Metric summaries",
      "Toolbar actions",
      "Empty states",
      "Generate-report modal"
    ]
  },
  settings: {
    surface: "Configuration management panels",
    readyComponents: [
      "Page header",
      "Section cards",
      "Inputs and selects",
      "Error states",
      "Form actions"
    ]
  }
};

export default function App() {
  const [activePage, setActivePage] = useState<NavKey>("overview");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [searchValue, setSearchValue] = useState("");
  const [selectedAlertId, setSelectedAlertId] = useState(alertRows[0].id);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const deferredSearchValue = useDeferredValue(searchValue);

  useEffect(() => {
    let isMounted = true;

    void fetchHealthResponse()
      .then((response) => {
        if (!isMounted) {
          return;
        }

        startTransition(() => {
          setHealth(response);
          setHealthError(null);
        });
      })
      .catch((error: Error) => {
        if (!isMounted) {
          return;
        }

        startTransition(() => {
          setHealth(null);
          setHealthError(error.message);
        });
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const filteredAlerts = alertRows.filter((row) => {
    const query = deferredSearchValue.trim().toLowerCase();

    if (!query) {
      return true;
    }

    return [
      row.id,
      row.detection,
      row.asset,
      row.endpoint,
      row.source,
      row.eventId
    ].some((value) => value.toLowerCase().includes(query));
  });

  const selectedAlert =
    filteredAlerts.find((row) => row.id === selectedAlertId) ??
    filteredAlerts[0] ??
    alertRows[0];

  const healthTone: HealthTone = healthError
    ? "down"
    : health?.database === "up"
      ? "healthy"
      : "degraded";

  const healthLabel = healthError
    ? "API connectivity issue"
    : health
      ? `API ${health.status} · database ${health.database}`
      : "Checking API health";

  const alertColumns: TableColumn<AlertRow>[] = [
    {
      id: "timestamp",
      header: "Observed",
      cell: (row) => <span className="type-mono-sm">{row.timestamp}</span>
    },
    {
      id: "source",
      header: "Source",
      cell: (row) => <Badge tone="outline">{row.source}</Badge>
    },
    {
      id: "detection",
      header: "Detection",
      cell: (row) => (
        <span className="text-body-sm font-medium text-content-primary">
          {row.detection}
        </span>
      )
    },
    {
      id: "severity",
      header: "Severity",
      cell: (row) => <SeverityChip severity={row.severity} />
    },
    {
      id: "risk",
      header: "Risk",
      cell: (row) => (
        <span className="text-body-sm font-medium text-content-primary">
          {row.risk}
        </span>
      ),
      align: "right"
    },
    {
      id: "asset",
      header: "Asset / IP",
      cell: (row) => (
        <div className="space-y-1">
          <div className="text-body-sm font-medium text-content-primary">
            {row.asset}
          </div>
          <div className="type-mono-sm">{row.endpoint}</div>
        </div>
      )
    },
    {
      id: "status",
      header: "Status",
      cell: (row) => <StatusChip status={row.status} />
    },
    {
      id: "analyst",
      header: "Assignee",
      cell: (row) => (
        <span className="text-body-sm font-medium text-content-primary">
          {row.analyst}
        </span>
      )
    }
  ];

  return (
    <>
      <AppShell
        items={primaryNavigation}
        activeId={activePage}
        onNavigate={setActivePage}
        pageTitle={pageBlueprints[activePage].title}
        pageDescription={pageBlueprints[activePage].description}
        healthTone={healthTone}
        healthLabel={healthLabel}
        searchValue={searchValue}
        onSearchChange={(event) => setSearchValue(event.target.value)}
      >
        <div className="space-y-section">
          {healthError ? (
            <ErrorState
              title="Backend health degraded"
              description="The API foundation is still reachable through the frontend shell, but the latest health request did not complete."
              details={healthError}
              action={
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => window.location.reload()}
                  leadingIcon={<Icon name="activity" className="h-4 w-4" />}
                >
                  Retry health check
                </Button>
              }
            />
          ) : null}

          {activePage === "overview" ? (
            <>
              <PageHeader
                eyebrow={pageBlueprints.overview.eyebrow}
                title={pageBlueprints.overview.title}
                description={pageBlueprints.overview.description}
                meta={
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="brand">Single tenant</Badge>
                    <Badge tone="outline">Wazuh + Suricata</Badge>
                    <Badge tone="outline">AI scoring enabled</Badge>
                  </div>
                }
                actions={
                  <>
                    <Button
                      variant="ghost"
                      leadingIcon={<Icon name="spark" className="h-4 w-4" />}
                    >
                      Launch investigation
                    </Button>
                    <Button
                      variant="primary"
                      leadingIcon={<Icon name="reports" className="h-4 w-4" />}
                      onClick={() => setReportModalOpen(true)}
                    >
                      Generate report
                    </Button>
                  </>
                }
              />

              <section className="grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
                <ChartCard
                  eyebrow="Detection focus"
                  title="In-Scope Security Activity"
                  description="Alert pressure across the approved AegisCore detection types."
                  footer={
                    <div className="flex flex-wrap items-center gap-3">
                      <Badge tone="brand">Primary signal: brute_force</Badge>
                      <span className="text-body-sm text-content-secondary">
                        Orange remains reserved for the most important trend on
                        the screen.
                      </span>
                    </div>
                  }
                >
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={alertActivity}>
                        <defs>
                          <linearGradient
                            id="alert-activity-fill"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >
                            <stop
                              offset="5%"
                              stopColor="#F97316"
                              stopOpacity={0.55}
                            />
                            <stop
                              offset="95%"
                              stopColor="#F97316"
                              stopOpacity={0.04}
                            />
                          </linearGradient>
                        </defs>
                        <CartesianGrid
                          stroke="rgba(31, 41, 55, 0.9)"
                          strokeDasharray="4 4"
                        />
                        <XAxis
                          dataKey="window"
                          stroke="#9CA3AF"
                          tickLine={false}
                          axisLine={false}
                        />
                        <YAxis
                          stroke="#9CA3AF"
                          tickLine={false}
                          axisLine={false}
                        />
                        <Tooltip
                          cursor={{ fill: "rgba(249, 115, 22, 0.08)" }}
                          contentStyle={{
                            backgroundColor: "rgba(17, 24, 39, 0.96)",
                            borderColor: "#1F2937",
                            borderRadius: "14px",
                            color: "#F9FAFB"
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="alerts"
                          stroke="#F97316"
                          strokeWidth={3}
                          fill="url(#alert-activity-fill)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                <div className="grid gap-4">
                  <MetricCard
                    label="Normalized alerts"
                    value="37"
                    detail="Common-schema alert flow built for Wazuh and Suricata ingestion."
                    tone="highlight"
                    trend={<Badge tone="brand">+8 today</Badge>}
                  />
                  <MetricCard
                    label="Open incidents"
                    value="4"
                    detail="Investigation queue aligned to analyst workflows and single-tenant ownership."
                    trend={<Badge tone="warning">2 pending response</Badge>}
                  />
                  {health ? (
                    <MetricCard
                      label="Platform health"
                      value={health.database === "up" ? "Healthy" : "Degraded"}
                      detail="Frontend talks only to backend APIs, with database health surfaced through the API boundary."
                      tone={health.database === "up" ? "neutral" : "warning"}
                      trend={
                        <Badge
                          tone={
                            health.database === "up" ? "success" : "warning"
                          }
                          icon={<Icon name="health" className="h-3.5 w-3.5" />}
                        >
                          {health.service}
                        </Badge>
                      }
                    />
                  ) : (
                    <LoadingCard />
                  )}
                </div>
              </section>

              <section className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
                <ChartCard
                  eyebrow="Priority mix"
                  title="Severity by detection"
                  description="The dashboard uses compact stacked bars for comparison-heavy security summaries."
                >
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={severityDistribution}>
                        <CartesianGrid
                          stroke="rgba(31, 41, 55, 0.9)"
                          strokeDasharray="4 4"
                        />
                        <XAxis
                          dataKey="detection"
                          stroke="#9CA3AF"
                          tickLine={false}
                          axisLine={false}
                          interval={0}
                          height={70}
                          angle={-18}
                          textAnchor="end"
                        />
                        <YAxis
                          stroke="#9CA3AF"
                          tickLine={false}
                          axisLine={false}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "rgba(17, 24, 39, 0.96)",
                            borderColor: "#1F2937",
                            borderRadius: "14px",
                            color: "#F9FAFB"
                          }}
                        />
                        <Bar
                          dataKey="critical"
                          stackId="severity"
                          fill="#EF4444"
                          radius={[4, 4, 0, 0]}
                        />
                        <Bar
                          dataKey="high"
                          stackId="severity"
                          fill="#F59E0B"
                        />
                        <Bar
                          dataKey="medium"
                          stackId="severity"
                          fill="#F97316"
                        />
                        <Bar
                          dataKey="low"
                          stackId="severity"
                          fill="#9CA3AF"
                          radius={[0, 0, 4, 4]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </ChartCard>

                <Card>
                  <CardHeader>
                    <div>
                      <p className="type-label-md">Selected alert</p>
                      <CardTitle>{selectedAlert.id}</CardTitle>
                      <CardDescription>
                        Investigation context, raw identifiers, and response
                        posture remain visible without leaving the page.
                      </CardDescription>
                    </div>
                    <StatusChip status={selectedAlert.status} />
                  </CardHeader>
                  <CardContent className="grid gap-4 pt-0 md:grid-cols-2">
                    <div className="space-y-4">
                      <div>
                        <p className="type-label-sm">Affected asset</p>
                        <p className="mt-2 text-heading-sm text-content-primary">
                          {selectedAlert.asset}
                        </p>
                        <p className="mt-1 type-mono-sm">
                          {selectedAlert.endpoint}
                        </p>
                      </div>
                      <div>
                        <p className="type-label-sm">Detection</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          <Badge tone="outline">{selectedAlert.source}</Badge>
                          <SeverityChip severity={selectedAlert.severity} />
                          <Badge tone="brand">{selectedAlert.risk}</Badge>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div>
                        <p className="type-label-sm">Event metadata</p>
                        <div className="mt-2 space-y-2">
                          <p className="type-mono-sm">
                            event_id: {selectedAlert.eventId}
                          </p>
                          <p className="type-mono-sm">
                            timestamp: {selectedAlert.timestamp}
                          </p>
                          <p className="type-mono-sm">
                            port: {selectedAlert.port}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="secondary"
                        fullWidth
                        leadingIcon={<Icon name="spark" className="h-4 w-4" />}
                      >
                        Open incident detail
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </section>

              <section className="space-y-4">
                <SearchFilterToolbar
                  title="Alert triage toolbar"
                  description="Shared search and filter surface for alerts, incidents, assets, and response history."
                  search={
                    <SearchInput
                      value={searchValue}
                      onChange={(event) => setSearchValue(event.target.value)}
                    />
                  }
                  filters={
                    <>
                      <Select
                        aria-label="Filter by source"
                        defaultValue=""
                        options={[
                          { value: "wazuh", label: "Wazuh" },
                          { value: "suricata", label: "Suricata" }
                        ]}
                        placeholder="Source"
                      />
                      <Select
                        aria-label="Filter by severity"
                        defaultValue=""
                        options={[
                          { value: "critical", label: "Critical" },
                          { value: "high", label: "High" },
                          { value: "medium", label: "Medium" },
                          { value: "low", label: "Low" }
                        ]}
                        placeholder="Severity"
                      />
                      <Select
                        aria-label="Filter by status"
                        defaultValue=""
                        options={[
                          { value: "new", label: "New" },
                          { value: "investigating", label: "Investigating" },
                          { value: "contained", label: "Contained" },
                          { value: "resolved", label: "Resolved" }
                        ]}
                        placeholder="Status"
                      />
                    </>
                  }
                  actions={
                    <>
                      <Button variant="ghost" size="sm">
                        Reset
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        leadingIcon={<Icon name="filter" className="h-4 w-4" />}
                      >
                        Save filter
                      </Button>
                    </>
                  }
                  activeFilters={[
                    "source: Wazuh + Suricata",
                    "scope: approved detections",
                    "tenant: single"
                  ]}
                />

                <DataTable
                  ariaLabel="AegisCore alert triage table"
                  columns={alertColumns}
                  data={filteredAlerts}
                  rowKey={(row) => row.id}
                  selectedRowKey={selectedAlert.id}
                  onRowClick={(row) => setSelectedAlertId(row.id)}
                  footer={
                    <div className="flex flex-col gap-2 text-body-sm text-content-muted md:flex-row md:items-center md:justify-between">
                      <span>
                        Showing {filteredAlerts.length} of {alertRows.length}{" "}
                        normalized alerts
                      </span>
                      <Button variant="ghost" size="sm">
                        View full alert queue
                      </Button>
                    </div>
                  }
                />
              </section>

              <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr_0.9fr]">
                <EmptyState
                  iconName="reports"
                  title="Reports workspace is ready"
                  description="The design system now includes chart cards, metric summaries, and modal scaffolding for SME-friendly operational reports."
                  action={
                    <Button
                      variant="secondary"
                      size="sm"
                      leadingIcon={<Icon name="reports" className="h-4 w-4" />}
                      onClick={() => setActivePage("reports")}
                    >
                      Open reports blueprint
                    </Button>
                  }
                />

                <Card>
                  <CardHeader>
                    <div>
                      <p className="type-label-md">Response policy preview</p>
                      <CardTitle>Safe SME automation controls</CardTitle>
                      <CardDescription>
                        Shared form primitives for policy editing, confirmation,
                        and audit-safe actions.
                      </CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4 pt-0">
                    <Input
                      label="Policy name"
                      defaultValue="Brute force containment"
                    />
                    <Select
                      label="Detection scope"
                      defaultValue="brute_force"
                      options={[
                        { value: "brute_force", label: "brute_force" },
                        {
                          value: "file_integrity_violation",
                          label: "file_integrity_violation"
                        },
                        { value: "port_scan", label: "port_scan" },
                        {
                          value: "unauthorized_user_creation",
                          label: "unauthorized_user_creation"
                        }
                      ]}
                    />
                    <Textarea
                      label="Analyst guidance"
                      defaultValue="Contain only after confirming repeated failed logins on the same monitored endpoint."
                    />
                  </CardContent>
                </Card>

                <Card tone="subtle">
                  <CardHeader>
                    <div>
                      <p className="type-label-md">SOC data formatting</p>
                      <CardTitle>Monospace evidence rules</CardTitle>
                      <CardDescription>
                        IPs, ports, hashes, timestamps, and event IDs retain
                        monospace treatment for scanability.
                      </CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3 pt-0">
                    <p className="type-mono-sm">ip: 10.42.11.9</p>
                    <p className="type-mono-sm">port: 389</p>
                    <p className="type-mono-sm">
                      sha256:
                      3e9af1bf8c77f4d14d0f679c7efdfeca8db3b48b3fd6134f
                    </p>
                    <p className="type-mono-sm">event_id: evt-a190d2</p>
                  </CardContent>
                </Card>
              </section>
            </>
          ) : (
            <>
              <PageHeader
                eyebrow={pageBlueprints[activePage].eyebrow}
                title={pageBlueprints[activePage].title}
                description={pageBlueprints[activePage].description}
                actions={
                  <Button
                    variant="secondary"
                    leadingIcon={
                      <Icon name="dashboard" className="h-4 w-4" />
                    }
                    onClick={() => setActivePage("overview")}
                  >
                    Return to overview
                  </Button>
                }
              />

              <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
                <Card>
                  <CardHeader>
                    <div>
                      <p className="type-label-md">Foundation ready</p>
                      <CardTitle>{pageReadiness[activePage].surface}</CardTitle>
                      <CardDescription>
                        Shared UI primitives are now available to implement this
                        page directly from the repo design spec.
                      </CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="grid gap-3 md:grid-cols-2">
                      {pageReadiness[activePage].readyComponents.map((item) => (
                        <div
                          key={item}
                          className="rounded-panel border border-border-subtle bg-surface-subtle/65 p-4"
                        >
                          <div className="flex items-center gap-3">
                            <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-brand-primary/25 bg-surface-accentSoft text-brand-primary">
                              <Icon
                                name="check-circle"
                                className="h-4 w-4"
                              />
                            </span>
                            <span className="text-body-sm font-medium text-content-primary">
                              {item}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <EmptyState
                  iconName="shield"
                  title={`${pageBlueprints[activePage].title} is ready for page implementation`}
                  description="The shell, cards, table surface, filters, states, and modal patterns are already in place. The next step is building the page-specific data flows and layout composition."
                  action={
                    <Button
                      variant="primary"
                      size="sm"
                      leadingIcon={<Icon name="spark" className="h-4 w-4" />}
                      onClick={() => setActivePage("overview")}
                    >
                      Review the foundation
                    </Button>
                  }
                />
              </section>

              <LoadingTable columns={5} rows={5} />
            </>
          )}
        </div>
      </AppShell>

      <Modal
        open={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        title="Generate operational report"
        description="Use the shared modal and form primitives to drive reports, response previews, and audited analyst workflows."
        footer={
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <Button variant="ghost" onClick={() => setReportModalOpen(false)}>
              Cancel
            </Button>
            <div className="flex gap-3">
              <Button variant="secondary">Preview</Button>
              <Button variant="primary">Generate report</Button>
            </div>
          </div>
        }
      >
        <div className="grid gap-4 md:grid-cols-2">
          <Input label="Report name" defaultValue="Daily security posture summary" />
          <Select
            label="Time range"
            defaultValue="24h"
            options={[
              { value: "24h", label: "Last 24 hours" },
              { value: "7d", label: "Last 7 days" },
              { value: "30d", label: "Last 30 days" }
            ]}
          />
          <Select
            label="Primary focus"
            defaultValue="alerts"
            options={[
              { value: "alerts", label: "Alert trends" },
              { value: "incidents", label: "Incident summary" },
              { value: "assets", label: "Asset exposure" },
              { value: "responses", label: "Response execution" }
            ]}
          />
          <Input
            label="Recipient"
            type="email"
            defaultValue="security-lead@aegiscore.local"
          />
          <div className="md:col-span-2">
            <Textarea
              label="Analyst note"
              defaultValue="Focus on the unauthorized_user_creation detection and any pending response actions before circulation."
            />
          </div>
        </div>
      </Modal>
    </>
  );
}
