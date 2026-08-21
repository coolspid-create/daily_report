import { createServiceClient } from "@/lib/database/service-client";

export async function setSourceActive(sourceId: string, active: boolean) {
  const client = createServiceClient();
  const { error } = await client.from("sources").update({
    active,
    status: active ? "HEALTHY" : "DISABLED",
  }).eq("id", sourceId);
  if (error) throw new Error("출처 상태 변경에 실패했습니다.");
}
