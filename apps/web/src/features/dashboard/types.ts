/*
 * TypeScript types used by the dashboard feature area.
 */
import type { AssetRecord } from "../assets/types";
import type { IncidentRecord } from "../incidents/types";
import type { ResponseRecord } from "../responses/types";

// Defines the Dashboard Summary Api Response data shape used by this frontend module.
export type DashboardSummaryApiResponse = {
  asset_count: number;
  raw_alert_count: number;
  alert_count: number;
  open_incident_count: number;
  pending_response_count: number;
  average_risk_score: number;
  alerts_by_detection: Array<{
    detection_type: string;
    total: number;
  }>;
};

// Defines the Dashboard Trend Point data shape used by this frontend module.
export type DashboardTrendPoint = {
  label: string;
  total: number;
};

// Defines the Dashboard Distribution Point data shape used by this frontend module.
export type DashboardDistributionPoint = {
  label: string;
  total: number;
  color: string;
};

// Defines the Dashboard Detection Point data shape used by this frontend module.
export type DashboardDetectionPoint = {
  detectionType: string;
  total: number;
};

// Defines the Dashboard Overview Response data shape used by this frontend module.
export type DashboardOverviewResponse = {
  fetchedAt: string;
  summary: {
    totalAlerts: number;
    highRiskAlerts: number;
    openIncidents: number;
    activeAssets: number;
    recentResponses: number;
    pendingResponses: number;
    averageRiskScore: number;
  };
  alertVolume: DashboardTrendPoint[];
  severityDistribution: DashboardDistributionPoint[];
  riskDistribution: DashboardDistributionPoint[];
  incidentStateDistribution: DashboardDistributionPoint[];
  alertsByDetection: DashboardDetectionPoint[];
  latestIncidents: IncidentRecord[];
  topAffectedAssets: AssetRecord[];
  recentResponsesFeed: ResponseRecord[];
};
