import { getApiBaseUrl } from "@/lib/env";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function safeMessage(status: number): string {
  if (status === 404) {
    return "This student record could not be found.";
  }
  return "Unable to load your learning data.";
}

async function readErrorDetail(response: Response): Promise<string | null> {
  try {
    const body: unknown = await response.json();
    if (!body || typeof body !== "object" || !("detail" in body)) {
      return null;
    }
    const detail = body.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail.trim();
    }
    if (!Array.isArray(detail)) {
      return null;
    }
    const messages = detail.flatMap((item) => {
      if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string" && item.msg.trim()) {
        return [item.msg.trim()];
      }
      return [];
    });
    return messages.length > 0 ? messages.join(" ") : null;
  } catch {
    return null;
  }
}

async function request<T>(
  path: string,
  init: RequestInit,
  describeError?: (status: number, detail: string | null) => string,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...init.headers },
      cache: "no-store",
    });
  } catch {
    const message = describeError ? describeError(0, null) : "Unable to load your learning data.";
    throw new ApiError(message, 0);
  }

  if (!response.ok) {
    const detail = describeError ? await readErrorDetail(response) : null;
    const message = describeError ? describeError(response.status, detail) : safeMessage(response.status);
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export function apiGet<T>(
  path: string,
  describeError?: (status: number, detail: string | null) => string,
): Promise<T> {
  return request<T>(path, { method: "GET" }, describeError);
}

export function apiPost<T>(
  path: string,
  body: unknown,
  describeError?: (status: number, detail: string | null) => string,
): Promise<T> {
  return request<T>(
    path,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    describeError,
  );
}

export function apiPostForm<T>(
  path: string,
  body: FormData,
  describeError?: (status: number, detail: string | null) => string,
): Promise<T> {
  return request<T>(path, { method: "POST", body }, describeError);
}
