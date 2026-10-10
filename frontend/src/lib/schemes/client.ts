import { ApiError } from "@/lib/api/client";
import type { SchemeProfile } from "@/lib/schemes/profile";
import type { RecommendResponse } from "@/types/schemes";

function schemeError(status: number, detail: string | null): string {
  if (detail) {
    return detail;
  }
  if (status === 422) {
    return "The scheme predictor rejected this profile.";
  }
  if (status === 503) {
    return "The government scheme predictor is unavailable.";
  }
  return "The government scheme predictor could not check this profile.";
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
        const location =
          "loc" in item && Array.isArray(item.loc)
            ? item.loc.filter((part: unknown) => typeof part === "string").join(".")
            : "";
        return [location ? `${location}: ${item.msg.trim()}` : item.msg.trim()];
      }
      return [];
    });
    return messages.length > 0 ? messages.join(" ") : null;
  } catch {
    return null;
  }
}

function isRecommendResponse(value: unknown): value is RecommendResponse {
  if (!value || typeof value !== "object") {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    typeof record.eligible_scheme_count === "number" &&
    typeof record.total_schemes_evaluated === "number" &&
    typeof record.disclaimer === "string" &&
    Array.isArray(record.recommendations) &&
    Array.isArray(record.evaluated_schemes)
  );
}

export async function recommendSchemes(profile: SchemeProfile): Promise<RecommendResponse> {
  let response: Response;
  try {
    response = await fetch("/api/support/schemes", {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify(profile),
      cache: "no-store",
    });
  } catch {
    throw new ApiError("The government scheme predictor could not be reached.", 0);
  }

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new ApiError(schemeError(response.status, detail), response.status);
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new ApiError("The government scheme predictor returned an unreadable response.", response.status);
  }
  if (!isRecommendResponse(body)) {
    throw new ApiError("The government scheme predictor returned an unexpected response.", response.status);
  }
  return body;
}
