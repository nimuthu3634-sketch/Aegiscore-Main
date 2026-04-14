export type HealthResponse = {
  status: string;
  service: string;
  database: string;
};

export type AuthUserResponse = {
  id: string;
  username: string;
  full_name: string;
  is_active: boolean;
  role: {
    id: string;
    name: "admin" | "analyst";
  };
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUserResponse;
};

export const AUTH_REQUIRED_EVENT = "aegiscore:auth-required";

type FetchApiJsonOptions = {
  auth?: boolean;
};

const accessTokenStorageKey = "aegiscore.access_token";
const sessionRoleStorageKey = "aegiscore.session_role";
const sessionUsernameStorageKey = "aegiscore.session_username";
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
const devAuthBootstrapEnabled =
  import.meta.env.DEV &&
  import.meta.env.VITE_ENABLE_DEV_AUTH_BOOTSTRAP === "true";
const devApiUsername =
  devAuthBootstrapEnabled
    ? import.meta.env.VITE_DEV_API_USERNAME ?? "admin"
    : undefined;
const devApiPassword =
  devAuthBootstrapEnabled
    ? import.meta.env.VITE_DEV_API_PASSWORD ?? "AegisCore123!"
    : undefined;
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

export function getStoredAccessToken() {
  if (!canUseWebStorage()) {
    return null;
  }

  return window.localStorage.getItem(accessTokenStorageKey);
}

export function setStoredAccessToken(token: string) {
  if (!canUseWebStorage()) {
    return;
  }

  window.localStorage.setItem(accessTokenStorageKey, token);
}

export function clearStoredAccessToken() {
  if (!canUseWebStorage()) {
    return;
  }

  window.localStorage.removeItem(accessTokenStorageKey);
  window.localStorage.removeItem(sessionRoleStorageKey);
  window.localStorage.removeItem(sessionUsernameStorageKey);
}

/**
 * Ends the operator browser session: clears persisted JWT and role, and drops any
 * in-flight dev-bootstrap token fetch so the next request does not reuse a stale promise.
 *
 * Storage keys removed: `aegiscore.access_token`, `aegiscore.session_role`.
 * (Dev credentials live in env vars only; there is no separate localStorage key for them.)
 */
export function logoutOperator() {
  clearStoredAccessToken();
  devAccessTokenPromise = null;
}

export function hasStoredAccessToken() {
  return Boolean(getStoredAccessToken());
}

export function getStoredSessionRole() {
  if (!canUseWebStorage()) {
    return null;
  }
  return window.localStorage.getItem(sessionRoleStorageKey);
}

export function getStoredUsername() {
  if (!canUseWebStorage()) {
    return null;
  }
  return window.localStorage.getItem(sessionUsernameStorageKey);
}

export function isDevAuthBootstrapEnabled() {
  return devAuthBootstrapEnabled;
}

export async function loginWithPassword(
  username: string,
  password: string,
  options: {
    persist?: boolean;
  } = {}
): Promise<AuthTokenResponse> {
  const response = await fetch(buildUrl("/auth/login"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json"
    },
    body: JSON.stringify({
      username,
      password
    })
  });

  if (!response.ok) {
    throw new ApiRequestError(response.status, await extractApiError(response));
  }

  const payload = (await response.json()) as AuthTokenResponse;

  if (options.persist ?? true) {
    setStoredAccessToken(payload.access_token);
    window.localStorage.setItem(sessionRoleStorageKey, payload.user.role.name);
    window.localStorage.setItem(sessionUsernameStorageKey, payload.user.username);
  }

  return payload;
}

async function requestDevAccessToken(): Promise<string | null> {
  if (!devApiUsername || !devApiPassword) {
    return null;
  }

  try {
    const payload = await loginWithPassword(devApiUsername, devApiPassword);
    return payload.access_token;
  } catch (error) {
    if (error instanceof ApiRequestError) {
      throw new ApiRequestError(
        error.status,
        "Authentication required. Sign in through the AegisCore login flow or explicitly enable local dev bootstrap with VITE_ENABLE_DEV_AUTH_BOOTSTRAP=true."
      );
    }

    throw error;
  }
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

function notifyAuthRequired() {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new Event(AUTH_REQUIRED_EVENT));
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

  if (useAuth && response.status === 401) {
    clearStoredAccessToken();
    notifyAuthRequired();
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