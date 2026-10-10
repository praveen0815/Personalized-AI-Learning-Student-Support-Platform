import { apiGet } from "@/lib/api/client";
import type { HealthStatus } from "@/types/learning";

export function getHealth(): Promise<HealthStatus> {
  return apiGet<HealthStatus>("/health");
}
