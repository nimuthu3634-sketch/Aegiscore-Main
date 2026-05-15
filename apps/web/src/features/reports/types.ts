/*
 * TypeScript types used by the reports feature area.
 */
export type ReportPeriod = "daily" | "weekly";
// Defines the Report Source Type data shape used by this frontend module.
export type ReportSourceType = "" | "wazuh" | "suricata";
// Defines the Report Export Format data shape used by this frontend module.
export type ReportExportFormat = "csv" | "json";
// Defines the Report Export Entity data shape used by this frontend module.
export type ReportExportEntity = "alerts" | "incidents" | "responses";

// Defines the Reports Query data shape used by this frontend module.
export type ReportsQuery = {
  dateFrom: string;
  dateTo: string;
  detectionType: string;
  sourceType: ReportSourceType;
};

// Defines the Report Distribution Point data shape used by this frontend module.
export type ReportDistributionPoint = {
  label: string;
  total: number;
  color: string;
};

// Defines the Report Trend Point data shape used by this frontend module.
export type ReportTrendPoint = {
  label: string;
  total: number;
};

// Defines the Report Top Asset data shape used by this frontend module.
export type ReportTopAsset = {
  assetId: string;
  hostname: string;
  ipAddress: string;
  alertCount: number;
  incidentCount: number;
};

// Defines the Report Summary data shape used by this frontend module.
export type ReportSummary = {
  reportType: ReportPeriod;
  generatedAt: string;
  windowStart: string;
  windowEnd: string;
  totalAlerts: number;
  highRiskAlerts: number;
  openIncidents: number;
  responseActions: number;
  activeAssets: number;
  averageRiskScore: number;
  alertVolume: ReportTrendPoint[];
  alertsByDetection: ReportDistributionPoint[];
  severityDistribution: ReportDistributionPoint[];
  incidentStateDistribution: ReportDistributionPoint[];
  responseStatusDistribution: ReportDistributionPoint[];
  topAssets: ReportTopAsset[];
};

export type ReportsOverviewResponse = {
  fetchedAt: string;
  daily: ReportSummary;
  weekly: ReportSummary;
};

export type ReportSummaryApiResponse = {
  report_type: ReportPeriod;
  generated_at: string;
  window_start: string;
  window_end: string;
  total_alerts: number;
  high_risk_alerts: number;
  open_incidents: number;
  response_actions: number;
  active_assets: number;
  average_risk_score: number;
  alert_volume: Array<{
    label: string;
    total: number;
  }>;
  alerts_by_detection: Array<{
    label: string;
    total: number;
  }>;
  severity_distribution: Array<{
    label: string;
    total: number;
  }>;
  incident_state_distribution: Array<{
    label: string;
    total: number;
  }>;
  response_status_distribution: Array<{
    label: string;
    total: number;
  }>;
  top_assets: Array<{
    asset_id: string;
    hostname: string;
    ip_address: string;
    alert_count: number;
    incident_count: number;
  }>;
};
