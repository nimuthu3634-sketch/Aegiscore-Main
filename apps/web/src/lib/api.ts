export type HealthResponse = {
  status: string;
  service: string;
  database: string;
};

type AuthTokenResponse = {
  access_token: string;
};

type FetchApiJsonOptions = {
  auth?: boolean;
};

const accessTokenStorageKey = "aegiscore.access_token";
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
const devApiUsername =
  import.meta.env.VITE_DEV_API_USERNAME ??
  (import.meta.env.DEV ? "admin" : undefined);
const devApiPassword =
  import.meta.env.VITE_DEV_API_PASSWORD ??
  (import.meta.env.DEV ? "AegisCore123!" : undefined);
let devAccessTokenPromise: Promise<string | null> | null = null;

function buildUrl(path: string) {
  return `${apiBaseUrl.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
}

export class ApiRequestError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

function canUseWebStorage() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function getStoredAccessToken() {
  if (!canUseWebStorage()) {
    return null;
  }

  return window.localStorage.getItem(accessTokenStorageKey);
}

function setStoredAccessToken(token: string) {
  if (!canUseWebStorage()) {
    return;
  }

  window.localStorage.setItem(accessTokenStorageKey, token);
}

function clearStoredAccessToken() {
  if (!canUseWebStorage()) {
    return;
  }

  window.localStorage.removeItem(accessTokenStorageKey);
}

async function requestDevAccessToken(): Promise<string | null> {
  if (!devApiUsername || !devApiPassword) {
    return null;
  }

  const response = await fetch(buildUrl("/auth/login"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json"
    },
    body: JSON.stringify({
      username: devApiUsername,
      password: devApiPassword
    })
  });

  if (!response.ok) {
    throw new ApiRequestError(
      response.status,
      "Authentication required for backend detail endpoints. Configure VITE_DEV_API_USERNAME and VITE_DEV_API_PASSWORD or sign in through the future auth flow."
    );
  }

  const payload = (await response.json()) as AuthTokenResponse;
  setStoredAccessToken(payload.access_token);
  return payload.access_token;
}

async function ensureAccessToken(forceRefresh = false) {
  if (!forceRefresh) {
    const existingToken = getStoredAccessToken();
    if (existingToken) {
      return existingToken;
    }
  } else {
    clearStoredAccessToken();
  }

  if (!import.meta.env.DEV) {
    return null;
  }

  if (!devAccessTokenPromise || forceRefresh) {
    devAccessTokenPromise = requestDevAccessToken().finally(() => {
      devAccessTokenPromise = null;
    });
  }

  return devAccessTokenPromise;
}

async function extractApiError(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      return payload.detail;
    }
  } catch {
    // Fall through to generic message if the response is not JSON.
  }

  return `API request failed with status ${response.status}`;
}

export async function fetchApiResponse(
  path: string,
  init: RequestInit = {},
  options: FetchApiJsonOptions = {}
): Promise<Response> {
  const useAuth = options.auth ?? true;
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  const sendRequest = async (token: string | null) => {
    const requestHeaders = new Headers(headers);
    if (token) {
      requestHeaders.set("Authorization", `Bearer ${token}`);
    }

    return fetch(buildUrl(path), {
      ...init,
      headers: requestHeaders
    });
  };

  let token = useAuth ? await ensureAccessToken() : null;
  let response = await sendRequest(token);

  if (useAuth && response.status === 401) {
    token = await ensureAccessToken(true);
    response = await sendRequest(token);
  }

  if (!response.ok) {
    throw new ApiRequestError(response.status, await extractApiError(response));
  }

  return response;
}

export async function fetchApiJson<T>(
  path: string,
  init: RequestInit = {},
  options: FetchApiJsonOptions = {}
): Promise<T> {
  const response = await fetchApiResponse(path, init, options);
  return (await response.json()) as T;
}

function parseDownloadFilename(
  headerValue: string | null,
  fallbackFilename: string
) {
  if (!headerValue) {
    return fallbackFilename;
  }

  const matched = headerValue.match(/filename="?([^";]+)"?/i);
  return matched?.[1] ?? fallbackFilename;
}

export async function downloadApiFile(
  path: string,
  fallbackFilename: string,
  init: RequestInit = {},
  options: FetchApiJsonOptions = {}
) {
  const response = await fetchApiResponse(path, init, options);
  const blob = await response.blob();
  const filename = parseDownloadFilename(
    response.headers.get("Content-Disposition"),
    fallbackFilename
  );

  if (typeof window !== "undefined") {
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);
  }

  return filename;
}

export function formatUtcDateTime(value: string | null | undefined) {
  if (!value) {
    return "n/a";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");

  return `${year}-${month}-${day} ${hours}:${minutes} UTC`;
}

export async function fetchHealthResponse(): Promise<HealthResponse> {
  const response = await fetchApiJson<HealthResponse>("/health", {}, { auth: false });

  return response;
}
