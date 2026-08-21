import { createServiceClient } from "@/lib/database/service-client";
import type { SourceHealth } from "@/features/admin-review/types/admin-review";

export async function getSourceHealth(): Promise<SourceHealth[]> {
  const client = createServiceClient();
  const { data, error } = await client
    .from("sources")
    .select("id,name,status,active,last_success_at,consecutive_failures")
    .order("name");
  if (error) throw new Error("출처 상태를 불러오지 못했습니다.");
  return data.map((row) => ({
    id: row.id,
    name: row.name,
    status: row.status,
    active: row.active,
    lastSuccessAt: row.last_success_at,
    consecutiveFailures: row.consecutive_failures,
  })) as SourceHealth[];
}
