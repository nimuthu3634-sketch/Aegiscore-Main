import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
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
import { ChartCard } from "../components/data-display/ChartCard";
import { MetricCard } from "../components/data-display/MetricCard";
import { SearchFilterToolbar } from "../components/data-display/SearchFilterToolbar";
import { EmptyState } from "../components/feedback/EmptyState";
import { ErrorState } from "../components/feedback/ErrorState";
import { LoadingCard } from "../components/feedback/LoadingState";
import { PageHeader } from "../components/layout/PageHeader";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/Card";
import { Icon } from "../components/ui/Icon";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { DistributionBars } from "../features/dashboard/components/DistributionBars";
import { TopAssetsReportPanel } from "../features/reports/components/TopAssetsReportPanel";
import {
  exportReportDataset,
  useReportsOverview
} from "../features/reports/service";
import type {
  ReportExportEntity,
  ReportExportFormat,
  ReportsQuery
} from "../features/reports/types";
import { formatTokenLabel } from "../lib/formatters";
import { supportedDetectionSelectOptions } from "../lib/supportedDetections";
import { pageBlueprints } from "../lib/theme/tokens";

const metricFormatter = new Intl.NumberFormat("en-US");
const tooltipContentStyle = {
  backgroundColor: "#111827",
  border: "1px solid #1F2937",
  borderRadius: "14px",
  boxShadow: "0 18px 40px rgba(0, 0, 0, 0.38)"
};
const tooltipLabelStyle = {
  color: "#D1D5DB",
  fontSize: "12px",
  letterSpacing: "0.12em",
  textTransform: "uppercase"
};
const tooltipItemStyle = {
  color: "#F9FAFB",
  fontSize: "12px",
  padding: 0
};

const detectionOptions = supportedDetectionSelectOptions();

type SourceFilter = "" | "wazuh" | "suricata";

export function ReportsPage() {
  const navigate = useNavigate();
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [detectionType, setDetectionType] = useState("");
  const [sourceType, setSourceType] = useState<SourceFilter>("");
  const [exportFormat, setExportFormat] = useState<ReportExportFormat>("csv");
  const [pendingExport, setPendingExport] = useState<ReportExportEntity | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const query = useMemo<ReportsQuery>(
    () => ({
      dateFrom,
      dateTo,
      detectionType,
      sourceType
    }),
    [dateFrom, dateTo, detectionType, sourceType]
  );

  const { data, isLoading, error, reload } = useReportsOverview(query);

  const summaryCards = useMemo(() => {
    if (!data) {
      return [];
    }

    return [
      {
        label: "Daily alerts",
        value: metricFormatter.format(data.daily.totalAlerts),
        detail: "In-scope volume for the day (Wazuh and Suricata normalized alerts).",
        tone: "highlight" as const,
        trend: <Badge tone="outline">weekly {data.weekly.totalAlerts}</Badge>
      },
      {
        label: "High-risk alerts",
        value: metricFormatter.format(data.daily.highRiskAlerts),
        detail: "Score 70+ for the day—same threshold as triage badges elsewhere.",
        tone: "warning" as const,
        trend: <Badge tone="warning">avg risk {data.daily.averageRiskScore}</Badge>
      },
      {
        label: "Open incidents",
        value: metricFormatter.format(data.daily.openIncidents),
        detail: "Investigations not yet resolved in the daily slice.",
        tone: "danger" as const,
        trend: <Badge tone="outline">weekly {data.weekly.openIncidents}</Badge>
      },
      {
        label: "Response actions",
        value: metricFormatter.format(data.daily.responseActions),
        detail: "What automation or analysts executed—pairs with the response history page.",
        tone: "neutral" as const,
        trend: <Badge tone="outline">weekly {data.weekly.responseActions}</Badge>
      },
      {
        label: "Active assets",
        value: metricFormatter.format(data.daily.activeAssets),
        detail: "Hosts that saw alert activity in the reporting window.",
        tone: "neutral" as const,
        trend: <Badge tone="brand">weekly {data.weekly.activeAssets}</Badge>
      }
    ];
  }, [data]);

  async function handleExport(entity: ReportExportEntity) {
    setPendingExport(entity);
    setExportMessage(null);
    setExportError(null);

    try {
      const filename = await exportReportDataset(entity, exportFormat, query);
      setExportMessage(`${formatTokenLabel(entity)} exported as ${filename}.`);
    } catch (downloadError: unknown) {
      setExportError(
        downloadError instanceof Error
          ? downloadError.message
          : "Report export failed."
      );
    } finally {
      setPendingExport(null);
    }
  }

  if (error && !data) {
    return (
      <ErrorState
        title="Reports could not be loaded"
        description="The reports workspace depends on real backend summary endpoints, and the current request failed."
        details={error}
        action={
          <Button variant="secondary" size="sm" onClick={reload}>
            Retry reports
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-section">
      <PageHeader
        eyebrow={pageBlueprints.reports.eyebrow}
        title={pageBlueprints.reports.title}
        description={pageBlueprints.reports.description}
        meta={
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="outline">MVP threat-scope summaries</Badge>
            {data ? <Badge tone="brand">fetched {data.fetchedAt}</Badge> : null}
          </div>
        }
        actions={
          <Button
            variant="secondary"
            size="sm"
            leadingIcon={<Icon name="activity" className="h-4 w-4" />}
            onClick={reload}
          >
            {isLoading && data ? "Refreshing" : "Refresh reports"}
          </Button>
        }
      />

      {error && data ? (
        <ErrorState
          title="Report data is stale"
          description="The last successful report snapshot is still visible, but the latest refresh failed."
          details={error}
          action={
            <Button variant="secondary" size="sm" onClick={reload}>
              Retry refresh
            </Button>
          }
          tone="warning"
        />
      ) : null}

      {isLoading && !data ? (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <LoadingCard />
          <LoadingCard />
          <LoadingCard />
          <LoadingCard />
          <LoadingCard />
        </section>
      ) : (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {summaryCards.map((card) => (
            <MetricCard
              key={card.label}
              label={card.label}
              value={card.value}
              detail={card.detail}
              tone={card.tone}
              trend={card.trend}
            />
          ))}
        </section>
      )}

      <SearchFilterToolbar
        title="Report scope"
        description="Daily and weekly summaries use the same date, detection, and source filters. Export actions reuse this scope."
        search={
          <div className="grid gap-3 md:grid-cols-2">
            <Input
              label="Date from"
              type="date"
              value={dateFrom}
              onChange={(event) => setDateFrom(event.target.value)}
            />
            <Input
              label="Date to"
              type="date"
              value={dateTo}
              onChange={(event) => setDateTo(event.target.value)}
            />
          </div>
        }
        filters={
          <>
            <Select
              label="Detection type"
              aria-label="Filter reports by detection type"
              value={detectionType}
              onChange={(event) => setDetectionType(event.target.value)}
              placeholder="All detections"
              options={detectionOptions}
            />
            <Select
              label="Source type"
              aria-label="Filter reports by source type"
              value={sourceType}
              onChange={(event) => setSourceType(event.target.value as SourceFilter)}
              placeholder="All sources"
              options={[
                { value: "wazuh", label: "Wazuh" },
                { value: "suricata", label: "Suricata" }
              ]}
            />
          </>
        }
        actions={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setDateFrom("");
              setDateTo("");
              setDetectionType("");
              setSourceType("");
              setExportMessage(null);
              setExportError(null);
            }}
          >
            Reset filters
          </Button>
        }
        activeFilters={[
          dateFrom && `from:${dateFrom}`,
          dateTo && `to:${dateTo}`,
          detectionType && `detection:${formatTokenLabel(detectionType)}`,
          sourceType && `source:${formatTokenLabel(sourceType)}`
        ].filter(Boolean) as string[]}
      />

      <Card tone="subtle">
        <CardHeader className="gap-4">
          <div className="space-y-2">
            <p className="type-label-md">Exports</p>
            <CardTitle>Operational data exports</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 pt-0">
          <div className="grid gap-3 md:grid-cols-[16rem_repeat(3,minmax(0,1fr))]">
            <Select
              label="Export format"
              aria-label="Select export format"
              value={exportFormat}
              onChange={(event) =>
                setExportFormat(event.target.value as ReportExportFormat)
              }
              options={[
                { value: "csv", label: "CSV" },
                { value: "json", label: "JSON" }
              ]}
            />
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleExport("alerts")}
              disabled={pendingExport !== null}
            >
              {pendingExport === "alerts" ? "Exporting alerts" : "Export alerts"}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleExport("incidents")}
              disabled={pendingExport !== null}
            >
              {pendingExport === "incidents"
                ? "Exporting incidents"
                : "Export incidents"}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleExport("responses")}
              disabled={pendingExport !== null}
            >
              {pendingExport === "responses"
                ? "Exporting responses"
                : "Export responses"}
            </Button>
          </div>

          {exportError ? (
            <p className="text-body-sm text-status-danger">{exportError}</p>
          ) : exportMessage ? (
            <p className="text-body-sm text-status-success">{exportMessage}</p>
          ) : (
            <p className="type-body-sm">
              Exports are generated from the current backend report scope and recorded
              in audit history.
            </p>
          )}
        </CardContent>
      </Card>

      {isLoading && !data ? (
        <>
          <section className="grid gap-4 xl:grid-cols-2">
            <LoadingCard className="min-h-[22rem]" />
            <LoadingCard className="min-h-[22rem]" />
          </section>
          <section className="grid gap-4 xl:grid-cols-2">
            <LoadingCard className="min-h-[22rem]" />
            <LoadingCard className="min-h-[22rem]" />
          </section>
          <LoadingCard className="min-h-[18rem]" />
        </>
      ) : data ? (
        <>
          <section className="grid gap-4 xl:grid-cols-2">
            <ChartCard
              eyebrow="Daily alert flow"
              title="Hourly normalized alert volume"
              description={`Current window ${data.daily.windowStart} to ${data.daily.windowEnd}.`}
              className="min-h-[23rem]"
              actions={<Badge tone="outline">{data.daily.totalAlerts} alerts</Badge>}
            >
              <div className="surface-grid rounded-panel border border-border-subtle/80 p-4">
                {data.daily.alertVolume.some((item) => item.total > 0) ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <AreaChart
                      data={data.daily.alertVolume}
                      margin={{ top: 10, right: 8, left: -24, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient
                          id="aegiscoreReportsDailyVolume"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop offset="5%" stopColor="#F97316" stopOpacity={0.45} />
                          <stop offset="95%" stopColor="#F97316" stopOpacity={0.05} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="rgba(156, 163, 175, 0.12)" vertical={false} />
                      <XAxis
                        dataKey="label"
                        tick={{ fill: "#9CA3AF", fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        allowDecimals={false}
                        tick={{ fill: "#9CA3AF", fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={tooltipContentStyle}
                        labelStyle={tooltipLabelStyle}
                        itemStyle={tooltipItemStyle}
                      />
                      <Area
                        type="monotone"
                        dataKey="total"
                        stroke="#F97316"
                        strokeWidth={2.5}
                        fill="url(#aegiscoreReportsDailyVolume)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    iconName="reports"
                    title="No daily alert activity"
                    description="The backend returned no alert volume for the current daily report window."
                  />
                )}
              </div>
            </ChartCard>

            <ChartCard
              eyebrow="Weekly alert flow"
              title="Daily normalized alert volume"
              description={`Current window ${data.weekly.windowStart} to ${data.weekly.windowEnd}.`}
              className="min-h-[23rem]"
              actions={
                <Badge tone="warning">
                  avg risk {metricFormatter.format(data.weekly.averageRiskScore)}
                </Badge>
              }
            >
              <div className="surface-grid rounded-panel border border-border-subtle/80 p-4">
                {data.weekly.alertVolume.some((item) => item.total > 0) ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart
                      data={data.weekly.alertVolume}
                      margin={{ top: 8, right: 12, left: -24, bottom: 0 }}
                    >
                      <CartesianGrid stroke="rgba(156, 163, 175, 0.12)" vertical={false} />
                      <XAxis
                        dataKey="label"
                        tick={{ fill: "#9CA3AF", fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        allowDecimals={false}
                        tick={{ fill: "#9CA3AF", fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={tooltipContentStyle}
                        labelStyle={tooltipLabelStyle}
                        itemStyle={tooltipItemStyle}
                      />
                      <Bar dataKey="total" radius={[8, 8, 0, 0]} fill="#F97316" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    iconName="reports"
                    title="No weekly alert activity"
                    description="The backend returned no alert volume for the current weekly report window."
                  />
                )}
              </div>
            </ChartCard>
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            <ChartCard
              eyebrow="Daily distributions"
              title="Detection and severity mix"
              description="Daily breakdown of the four validated threat categories and normalized severity bands."
              className="min-h-[23rem]"
            >
              <div className="grid gap-4 lg:grid-cols-2">
                <DistributionBars
                  title="Detections"
                  items={data.daily.alertsByDetection}
                />
                <DistributionBars
                  title="Severity"
                  items={data.daily.severityDistribution}
                />
              </div>
            </ChartCard>

            <ChartCard
              eyebrow="Weekly workflow"
              title="Incident and response posture"
              description="Weekly view of investigation state mix and response execution outcomes."
              className="min-h-[23rem]"
              actions={
                <Badge tone="outline">
                  {metricFormatter.format(data.weekly.responseActions)} responses
                </Badge>
              }
            >
              <div className="grid gap-4 lg:grid-cols-2">
                <DistributionBars
                  title="Incident states"
                  items={data.weekly.incidentStateDistribution}
                />
                <DistributionBars
                  title="Response status"
                  items={data.weekly.responseStatusDistribution}
                />
              </div>
            </ChartCard>
          </section>

          <section className="grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
            <TopAssetsReportPanel
              assets={data.weekly.topAssets}
              onViewAssets={() => navigate("/assets")}
            />

            <ChartCard
              eyebrow="Operational routing"
              title="Follow-up surfaces"
              description="Jump from the report snapshot into the active operational pages."
            >
              <div className="grid gap-3">
                {[
                  {
                    id: "alerts",
                    label: "Review alerts",
                    description: `${data.daily.highRiskAlerts} high-risk daily alerts`,
                    value: data.daily.totalAlerts,
                    onClick: () => navigate("/alerts")
                  },
                  {
                    id: "incidents",
                    label: "Review incidents",
                    description: `${data.weekly.openIncidents} open investigations`,
                    value: data.weekly.openIncidents,
                    onClick: () => navigate("/incidents")
                  },
                  {
                    id: "responses",
                    label: "Review response history",
                    description: `${data.weekly.responseActions} weekly execution records`,
                    value: data.weekly.responseActions,
                    onClick: () => navigate("/responses")
                  }
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={item.onClick}
                    className="focus-ring flex items-center justify-between rounded-panel border border-border-subtle bg-surface-subtle/40 px-4 py-3 text-left transition hover:border-brand-primary/30 hover:bg-surface-subtle/70"
                  >
                    <div className="space-y-1">
                      <p className="type-heading-sm">{item.label}</p>
                      <p className="type-body-sm">{item.description}</p>
                    </div>
                    <span className="type-mono-sm">{item.value}</span>
                  </button>
                ))}
              </div>
            </ChartCard>
          </section>
        </>
      ) : (
        <EmptyState
          iconName="reports"
          title="No report data is available"
          description="Adjust date or detection filters, or retry once the reporting API has data for the four validated threat categories."
          action={
            <Button variant="secondary" size="sm" onClick={reload}>
              Retry reports
            </Button>
          }
        />
      )}
    </div>
  );
}
