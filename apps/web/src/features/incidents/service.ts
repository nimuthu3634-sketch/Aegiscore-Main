import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { mockIncidentsResponse } from "./mockData";
import type { IncidentsListResponse } from "./types";

async function listIncidents(): Promise<IncidentsListResponse> {
  await new Promise((resolve) => window.setTimeout(resolve, 150));
  return mockIncidentsResponse;
}

export function useIncidentsList() {
  return useAsyncResource(listIncidents);
}
