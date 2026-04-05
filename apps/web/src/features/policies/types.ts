export type PolicyTarget = "alert" | "incident";
export type PolicyMode = "dry-run" | "live";

export type PolicyRecord = {
  id: string;
  name: string;
  description: string | null;
  enabled: boolean;
  target: PolicyTarget;
  detectionType: string;
  actionType: string;
  minRiskScore: number;
  mode: PolicyMode;
  lastUpdated: string;
};

export type PoliciesResponse = {
  items: PolicyRecord[];
  fetchedAt: string;
};

export type PoliciesApiResponse = {
  items: Array<{
    id: string;
    name: string;
    description: string | null;
    enabled: boolean;
    target: PolicyTarget;
    detection_type: string;
    min_risk_score: number;
    action_type: string;
    mode: PolicyMode;
    updated_at: string;
  }>;
};

export type PolicyUpdateApiResponse = {
  policy: PoliciesApiResponse["items"][number];
  message: string;
};
