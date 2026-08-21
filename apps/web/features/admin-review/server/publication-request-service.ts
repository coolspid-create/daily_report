import { createServiceClient } from "@/lib/database/service-client";

export async function requestPublicationBuild(publicationDate: string, rangeKey: "today" | "1d" | "7d") {
  const client = createServiceClient();
  const { data, error } = await client.from("daily_publications").upsert({
    publication_date: publicationDate,
    range_key: rangeKey,
    status: "BUILDING",
  }, { onConflict: "publication_date,range_key" }).select("id").single();
  if (error) throw new Error("공개 묶음 생성 요청에 실패했습니다.");
  return data;
}

export async function requestDigestBuild(publicationId: string, topicId: string) {
  if (!publicationId || !topicId) throw new Error("publicationId와 topicId가 필요합니다.");
  return { publicationId, topicId, status: "QUEUED" as const };
}
