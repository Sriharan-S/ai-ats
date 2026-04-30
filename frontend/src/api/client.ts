/// <reference types="vite/client" />
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

type ApiErrorBody = {
  error?: string | { message?: string };
};

function getErrorMessage(data: unknown, status: number): string {
  if (typeof data === "object" && data !== null && "error" in data) {
    const { error } = data as ApiErrorBody;
    if (typeof error === "string") {
      return error;
    }
    if (error?.message) {
      return error.message;
    }
  }

  return `Request failed: ${status}`;
}

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  const contentType = response.headers.get("content-type") ?? "";
  const data: unknown = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw new Error(getErrorMessage(data, response.status));
  }

  return data as T;
}

/**
 * Like requestJson but returns the JSON body even when the HTTP status is
 * non-2xx. Useful for the platform track endpoints, which return 404 with
 * a populated `{fetch_status: "not_found", ...}` body that the UI wants to
 * render.
 */
export async function requestJsonAllowNonOk<T>(
  path: string,
  init?: RequestInit
): Promise<{ data: T; ok: boolean; status: number }> {
  const response = await fetch(`${API_BASE}${path}`, init);
  const contentType = response.headers.get("content-type") ?? "";
  const data: unknown = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  return { data: data as T, ok: response.ok, status: response.status };
}
