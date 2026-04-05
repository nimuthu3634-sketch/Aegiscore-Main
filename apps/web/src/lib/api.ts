export type HealthResponse = {
  status: string;
  service: string;
  database: string;
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

function buildUrl(path: string) {
  return `${apiBaseUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
}

export async function fetchHealthResponse(): Promise<HealthResponse> {
  const response = await fetch(buildUrl("/health"));

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return (await response.json()) as HealthResponse;
}

