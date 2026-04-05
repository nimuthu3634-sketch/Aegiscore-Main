import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { mockAlertsResponse } from "./mockData";
import type { AlertsListResponse } from "./types";

async function listAlerts(): Promise<AlertsListResponse> {
  await new Promise((resolve) => window.setTimeout(resolve, 140));
  return mockAlertsResponse;
}

export function useAlertsList() {
  return useAsyncResource(listAlerts);
}
