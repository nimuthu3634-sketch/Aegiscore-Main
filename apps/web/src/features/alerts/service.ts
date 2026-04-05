import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { fetchApiJson } from "../../lib/api";
import { mapAlertsListResponse } from "../../lib/api/listTransforms";
import type { AlertsListApiResponse, AlertsListResponse } from "./types";

async function listAlerts(): Promise<AlertsListResponse> {
  const response = await fetchApiJson<AlertsListApiResponse>("/alerts");
  return mapAlertsListResponse(response);
}

export function useAlertsList() {
  return useAsyncResource(listAlerts);
}
