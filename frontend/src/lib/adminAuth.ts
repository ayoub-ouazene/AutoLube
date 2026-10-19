// Admin authentication helpers.
// Token lives in an httpOnly cookie set by POST /admin/login — JS cannot
// read it. All requests use credentials: "include" so the browser
// attaches the cookie automatically.

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function getAdminApiUrl(): string {
  if (typeof window === "undefined") return API_URL;

  const url = new URL(API_URL);
  const frontendHost = window.location.hostname;
  const loopbackHosts = new Set(["localhost", "127.0.0.1"]);

  // Cookies are host-only. Keep local frontend/backend requests on the same
  // loopback hostname so a cookie set by login is sent to /admin/me.
  if (
    loopbackHosts.has(frontendHost) &&
    loopbackHosts.has(url.hostname) &&
    url.hostname !== frontendHost
  ) {
    url.hostname = frontendHost;
  }

  return url.toString().replace(/\/$/, "");
}

export type AdminMe = { username: string };

export class AdminAuthError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "AdminAuthError";
    this.status = status;
  }
}

export async function apiAdminFetch<T = unknown>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const baseUrl = getAdminApiUrl();
  const url = path.startsWith("http")
    ? path
    : `${baseUrl}${path.startsWith("/") ? "" : "/"}${path}`;

  const res = await fetch(url, {
    ...init,
    credentials: "include",
    headers: {
      ...(init.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...(init.headers ?? {}),
    },
  });

  if (res.status === 401) {
    throw new AdminAuthError("Non authentifié.", 401);
  }

  if (!res.ok) {
    let detail = `Erreur ${res.status}`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") detail = body.detail;
    } catch {
      // non-JSON error body — keep the generic message
    }
    throw new AdminAuthError(detail, res.status);
  }

  if (res.status === 204) return undefined as T;

  return (await res.json()) as T;
}

export async function login(
  username: string,
  password: string
): Promise<void> {
  await apiAdminFetch<{
    access_token: string;
    token_type: string;
    expires_in: number;
  }>("/admin/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  // The token remains only in the httpOnly cookie. The JSON token is discarded.
}

export async function logout(): Promise<void> {
  try {
    await apiAdminFetch<{ ok: boolean }>("/admin/logout", {
      method: "POST",
    });
  } catch {
    // Best effort: local auth state is still cleared by the provider.
  }
}

export async function getMe(): Promise<AdminMe> {
  return apiAdminFetch<AdminMe>("/admin/me");
}
