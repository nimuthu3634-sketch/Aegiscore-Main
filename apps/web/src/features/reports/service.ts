import { useCallback } from "react";
import { downloadApiFile, fetchApiJson, formatUtcDateTime } from "../../lib/api";
import { buildApiPath } from "../../lib/api/query";
import { useAsyncResource } from "../../lib/data/useAsyncResource";
import type {
  ReportDistributionPoint,
  ReportExportEntity,
  ReportExportFormat,
  ReportsOverviewResponse,
  ReportsQuery,
  ReportSummary,
  ReportSummaryApiResponse
} from "./types";

const detectionPalette = {
  brute_force: "#F97316",
  file_integrity_violation: "#EF4444",
  port_scan: "#F59E0B",
  unauthorized_user_creation: "#22C55E"
} as const;

const severityPalette = {
  critical: "#EF4444",
  high: "#F97316",
  medium: "#F59E0B",
  low: "#9CA3AF"
} as const;

const incidentStatePalette = {
  new: "#9CA3AF",
  triaged: "#F59E0B",
  investigating: "#F97316",
  contained: "#22C55E",
  resolved: "#22C55E",
  false_positive: "#9CA3AF"
} as const;

const responseStatusPalette = {
  succeeded: "#22C55E",
  warning: "#F59E0B",
  failed: "#EF4444",
  pending: "#9CA3AF"
} as const;

const fallbackPalette = ["#F97316", "#F59E0B", "#22C55E", "#9CA3AF", "#D1D5DB"];

function pickColor(label: string, index: number, paletteMap: Record<string, string>) {
  return paletteMap[label] ?? fallbackPalette[index % fallbackPalette.length];
}

function mapDistribution(
  items: Array<{ label: string; total: number }>,
  paletteMap: Record<string, string>
): ReportDistributionPoint[] {
  return items.map((item, index) => ({
    label: item.label,
    total: item.total,
    color: pickColor(item.label, index, paletteMap)
  }));
}

function mapReportSummary(payload: ReportSummaryApiResponse): ReportSummary {
  return {
    reportType: payload.report_type,
    generatedAt: formatUtcDateTime(payload.generated_at),
    windowStart: formatUtcDateTime(payload.window_start),
    windowEnd: formatUtcDateTime(payload.window_end),
    totalAlerts: payload.total_alerts,
    highRiskAlerts: payload.high_risk_alerts,
    openIncidents: payload.open_incidents,
    responseActions: payload.response_actions,
    activeAssets: payload.active_assets,
    averageRiskScore: Math.round(payload.average_risk_score),
    alertVolume: payload.alert_volume.map((item) => ({
      label: item.label,
      total: item.total
    })),
    alertsByDetection: mapDistribution(payload.alerts_by_detection, detectionPalette),
    severityDistribution: mapDistribution(
      payload.severity_distribution,
      severityPalette
    ),
    incidentStateDistribution: mapDistribution(
      payload.incident_state_distribution,
      incidentStatePalette
    ),
    responseStatusDistribution: mapDistribution(
      payload.response_status_distribution,
      responseStatusPalette
    ),
    topAssets: payload.top_assets.map((asset) => ({
      assetId: asset.asset_id,
      hostname: asset.hostname,
      ipAddress: asset.ip_address,
      alertCount: asset.alert_count,
      incidentCount: asset.incident_count
    }))
  };
}

function buildReportQuery(query: ReportsQuery) {
  return {
    date_from: query.dateFrom,
    date_to: query.dateTo,
    detection_type: query.detectionType,
    source_type: query.sourceType
  };
}

async function fetchReportsOverview(
  query: ReportsQuery
): Promise<ReportsOverviewResponse> {
  const params = buildReportQuery(query);
  const [daily, weekly] = await Promise.all([
    fetchApiJson<ReportSummaryApiResponse>(
      buildApiPath("/reports/daily-summary", params)
    ),
    fetchApiJson<ReportSummaryApiResponse>(
      buildApiPath("/reports/weekly-summary", params)
    )
  ]);

  return {
    fetchedAt: formatUtcDateTime(new Date().toISOString()),
    daily: mapReportSummary(daily),
    weekly: mapReportSummary(weekly)
  };
}

export async function exportReportDataset(
  entity: ReportExportEntity,
  format: ReportExportFormat,
  query: ReportsQuery
) {
  return downloadApiFile(
    buildApiPath(`/reports/${entity}/export`, {
      ...buildReportQuery(query),
      format
    }),
    `aegiscore-${entity}-export.${format}`
  );
}

export function useReportsOverview(query: ReportsQuery) {
  const loader = useCallback(() => fetchReportsOverview(query), [query]);
  return useAsyncResource(loader);
}
