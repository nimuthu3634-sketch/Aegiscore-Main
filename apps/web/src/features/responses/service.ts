import { useAsyncResource } from "../../lib/data/useAsyncResource";
import { mockResponsesResponse } from "./mockData";
import type { ResponsesListResponse } from "./types";

async function listResponses(): Promise<ResponsesListResponse> {
  await new Promise((resolve) => window.setTimeout(resolve, 170));
  return mockResponsesResponse;
}

export function useResponsesList() {
  return useAsyncResource(listResponses);
}
