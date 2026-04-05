import type { AnalystNote } from "../../../components/data-display/AnalystNotesPanel";
import type { LinkedAlertRow } from "../../../components/data-display/LinkedAlertsTable";
import type { TimelineItem } from "../../../components/data-display/ActivityTimeline";
import type { RelatedResponseItem } from "../../../components/data-display/RelatedResponsesPanel";
import type { AssetCriticality } from "../../assets/types";
import type { IncidentRecord } from "../types";

export type IncidentAssetSummary = {
  hostname: string;
  ipAddress: string;
  criticality: AssetCriticality;
  recentAlertsCount: number;
};

export type IncidentPriorityExplanation = {
  label: string;
  summary: string;
  rationale: string;
  factors: string[];
};

export type IncidentDetailRecord = IncidentRecord & {
  createdAt: string;
  updatedAt: string;
  linkedAlerts: LinkedAlertRow[];
  primaryAssetSummary: IncidentAssetSummary;
  affectedAssets: IncidentAssetSummary[];
  timeline: TimelineItem[];
  notes: AnalystNote[];
  relatedResponses: RelatedResponseItem[];
  correlationExplanation: string;
  groupedEvidence: string[];
  priorityExplanation: IncidentPriorityExplanation;
};

export type IncidentDetailResponse = {
  incident: IncidentDetailRecord;
  fetchedAt: string;
};
