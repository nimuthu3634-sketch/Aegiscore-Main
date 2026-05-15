/*
 * TypeScript types used by the policies feature area.
 */
export type PolicyTarget = "alert" | "incident";
// Defines the Policy Mode data shape used by this frontend module.
export type PolicyMode = "dry-run" | "live";

// Defines the Policy Record data shape used by this frontend module.
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

// Defines the Policies Response data shape used by this frontend module.
export type PoliciesResponse = {
  items: PolicyRecord[];
  fetchedAt: string;
};

// Defines the Policies Api Response data shape used by this frontend module.
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

// Defines the Policy Update Api Response data shape used by this frontend module.
export type PolicyUpdateApiResponse = {
  policy: PoliciesApiResponse["items"][number];
  message: string;
};
