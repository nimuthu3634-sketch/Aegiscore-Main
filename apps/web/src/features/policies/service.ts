import { useCallback } from "react";
import { fetchApiJson, formatUtcDateTime } from "../../lib/api";
import { useAsyncResource } from "../../lib/data/useAsyncResource";
import type {
  PoliciesApiResponse,
  PoliciesResponse,
  PolicyUpdateApiResponse
} from "./types";

function mapPoliciesResponse(payload: PoliciesApiResponse): PoliciesResponse {
  return {
    fetchedAt: formatUtcDateTime(new Date().toISOString()),
    items: payload.items.map((policy) => ({
      id: policy.id,
      name: policy.name,
      description: policy.description,
      enabled: policy.enabled,
      target: policy.target,
      detectionType: policy.detection_type,
      actionType: policy.action_type,
      minRiskScore: policy.min_risk_score,
      mode: policy.mode,
      lastUpdated: formatUtcDateTime(policy.updated_at)
    }))
  };
}

async function fetchPolicies(): Promise<PoliciesResponse> {
  const response = await fetchApiJson<PoliciesApiResponse>("/policies");
  return mapPoliciesResponse(response);
}

export async function updatePolicyEnabled(policyId: string, enabled: boolean) {
  return fetchApiJson<PolicyUpdateApiResponse>(`/policies/${policyId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ enabled })
  });
}

export function usePolicies() {
  const loader = useCallback(() => fetchPolicies(), []);
  return useAsyncResource(loader);
}
