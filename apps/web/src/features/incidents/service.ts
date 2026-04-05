import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { fetchApiJson } from "../../lib/api";
import { mapIncidentsListResponse } from "../../lib/api/listTransforms";
import type { IncidentsListApiResponse, IncidentsListResponse } from "./types";

async function listIncidents(): Promise<IncidentsListResponse> {
  const response = await fetchApiJson<IncidentsListApiResponse>("/incidents");
  return mapIncidentsListResponse(response);
}

export function useIncidentsList() {
  return useAsyncResource(listIncidents);
}
