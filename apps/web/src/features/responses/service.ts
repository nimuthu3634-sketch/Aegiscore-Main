import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { fetchApiJson } from "../../lib/api";
import { mapResponsesListResponse } from "../../lib/api/listTransforms";
import type { ResponsesListApiResponse, ResponsesListResponse } from "./types";

async function listResponses(): Promise<ResponsesListResponse> {
  const response = await fetchApiJson<ResponsesListApiResponse>("/responses");
  return mapResponsesListResponse(response);
}

export function useResponsesList() {
  return useAsyncResource(listResponses);
}
