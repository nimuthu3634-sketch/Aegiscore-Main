import type { AnalystNote } from "../../../components/data-display/AnalystNotesPanel";
import type { RelatedResponseItem } from "../../../components/data-display/RelatedResponsesPanel";
import type { KeyValueItem } from "../../../components/data-display/KeyValueGrid";
import type { AlertRecord } from "../types";

export type AlertScoreExplanation = {
  score: number;
  label: string;
  summary: string;
  rationale: string;
  factors: string[];
};

export type AlertDetailRecord = AlertRecord & {
  linkedIncidentId: string | null;
  destinationIp: string | null;
  ruleId: string | null;
  sourceRule: string | null;
  normalizedSummary: string;
  normalizedDetails: KeyValueItem[];
  rawPayload: Record<string, unknown>;
  scoreExplanation: AlertScoreExplanation;
  relatedResponses: RelatedResponseItem[];
  notes: AnalystNote[];
};

export type AlertDetailResponse = {
  alert: AlertDetailRecord;
  fetchedAt: string;
};
